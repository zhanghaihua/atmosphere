# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

from atmosphere.settings import secrets
from threepio import logger

class Migration(DataMigration):

    def forwards(self, orm):
        "Write your forwards methods here."
        # Note: Remember to use orm['appname.ModelName'] rather than "from appname.models..."
        print '> core - data: Updating AccountProvider'
        self.build_account_admins(orm)

    def backwards(self, orm):
        "Write your backwards methods here."

    def build_account_admins(self, orm):
        print '> core - data - accountprovider: Openstack'
        self.build_os_admin(orm)
        print '> core - data - accountprovider: Eucalyptus'
        self.build_euca_admin(orm)
        print '> core - data - accountprovider: Atmosphere'
        self.build_atmo_admin(orm)

    def create_usergroup(self, orm, username):
        user = orm['auth.User'].objects.get_or_create(username=username)[0]
        group = orm.Group.objects.get_or_create(name=username)[0]
        user.groups.add(group)
        user.save()
        group.leaders.add(user)
        group.save()
        return (user, group)

    def build_atmo_admin(self, orm):
        if not hasattr(secrets, 'ATMOSPHERE_SUPERUSER'):
            print """Atmosphere Administrator could not be created from settings.
To create an Administrator account for Atmosphere via the REPL:
>>> Identity.make_account_admin(ATMOSPHERE_SUPERUSER_NAME)"""
            return
        user, group = self.create_usergroup(orm,username=secrets.ATMOSPHERE_SUPERUSER)
        quota = orm.Quota.objects.get_or_create(
                cpu = orm.Quota._meta.get_field('cpu').default,
                memory = orm.Quota._meta.get_field('memory').default,
                storage = orm.Quota._meta.get_field('storage').default,
                suspended_count = orm.Quota._meta.get_field('suspended_count').default,
                storage_count = orm.Quota._meta.get_field('storage_count').default)[0]
        #Prepare to update profile
        prof = orm.UserProfile.objects.get_or_create(user=user)[0]

        account_providers = orm.AccountProvider.objects.distinct('provider')
        for account_provider in account_providers:
            identity = account_provider.identity
            provider = account_provider.provider
            if not orm.ProviderMembership.objects.filter(
                                provider=provider, member=group):
                p_membership = orm.ProviderMembership.objects.get_or_create(
                    provider=provider, member=group)[0]
                id_membership = orm.IdentityMembership.objects.get_or_create(
                    identity=identity, member=group, quota=quota)[0]
                prof.selected_identity = identity

        #5. Save the profile to prepare user for first-time use
        prof.save()
        user.save()

    def create_identity(self, orm, username, provider_location,
                        max_quota=False, account_admin=False, **kwarg_creds):

        credentials = {}
        for (c_key,c_value) in kwarg_creds.items():
            if 'cred_' not in c_key.lower():
                continue
            c_key = c_key.replace('cred_','')
            credentials[c_key] = c_value

        provider = orm.Provider.objects.get(location__iexact=provider_location)
        #Create user-group
        user, group = self.create_usergroup(orm, username)



        #NOTE: This specific query will need to be modified if we want
        # 2+ Identities on a single provider

        id_membership = orm.IdentityMembership.objects.filter(
            member__name= user.username,
            identity__provider=provider,
            identity__created_by__username=user.username)
        if not id_membership:
            #1. Create a Provider Membership
            p_membership = orm.ProviderMembership.objects.get_or_create(
                provider=provider, member=group)[0]

            #2. Create an Identity Membership
            identity = orm.Identity.objects.get_or_create(
                created_by=user, provider=provider)[0]
            #Two-tuple, (Object, created)
            quota = orm.Quota.objects.get_or_create(
                cpu = orm.Quota._meta.get_field('cpu').default,
                memory = orm.Quota._meta.get_field('memory').default,
                storage = orm.Quota._meta.get_field('storage').default,
                suspended_count = orm.Quota._meta.get_field('suspended_count').default,
                storage_count = orm.Quota._meta.get_field('storage_count').default)[0]
            id_membership = orm.IdentityMembership.objects.get_or_create(
                identity=identity, member=group, quota=quota)
        #Either first in list OR object from two-tuple.. Its what we need.
        id_membership = id_membership[0] 

        #ID_Membership exists.

        #3. Make sure that all kwargs exist as credentials
        # NOTE: Because we assume only one identity per provider
        #       We can add new credentials to 
        #       existing identities if missing..
        # In the future it will be hard to determine when we want to 
        # update values on an identity Vs. create a second, new identity.
        for (c_key,c_value) in credentials.items():
            test_key_exists = orm.Credential.objects.filter(
                    identity=id_membership.identity,
                    key=c_key)
            if test_key_exists:
                logger.info("Conflicting Key Errror: Key:%s Value:%s "
                "Replacement:%s" % (c_key, c_value, test_key_exists[0].value))
                #No Dupes... But should we really throw an Exception here?
                continue
            orm.Credential.objects.get_or_create(
                identity=id_membership.identity,
                key=c_key,
                value=c_value)[0]
        if account_admin:
            admin = orm.AccountProvider.objects.get_or_create(
                        provider=id_membership.identity.provider,
                        identity=id_membership.identity)[0]

        #5. Save the user to activate profile on first-time use
        user.save()
        #Return the identity
        return id_membership.identity

    def build_os_admin(self, orm):
        if not hasattr(secrets, 'OPENSTACK_ARGS'):
            print """AccountProvider could not be created from secrets.
To create an AccountProvider for the 'OPENSTACK' location: via the REPL:
>>> Identity.create_identity(ADMIN_USERNAME, 'OPENSTACK', account_admin=True,
                             cred_key=username, cred_secret=password,
                             cred_ex_tenant_name=project_name,
                             cred_ex_project_name=project_name)"""
            return

        identity = self.create_identity(orm, 
            secrets.OPENSTACK_ARGS['username'],
            'OPENSTACK', account_admin=True,
            cred_key=secrets.OPENSTACK_ADMIN_KEY,
            cred_secret=secrets.OPENSTACK_ADMIN_SECRET,
            cred_ex_tenant_name=secrets.OPENSTACK_ADMIN_TENANT,
            cred_ex_project_name=secrets.OPENSTACK_ADMIN_TENANT)

    def build_euca_admin(self, orm):
        if not hasattr(secrets, 'EUCALYPTUS_ARGS'):
            print """AccountProvider could not be created from secrets.
To create a Eucalyptus AccountProvider via the REPL:
>>> Identity.create_identity(admin_username, 'EUCALYPTUS', account_admin=True,
                             cred_key=_key, cred_secret=secret)"""
            return
        identity = self.create_identity(orm,
            'admin', 'EUCALYPTUS',
            account_admin=True,
            cred_key=secrets.EUCA_ADMIN_KEY,
            cred_secret=secrets.EUCA_ADMIN_SECRET)

    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'core.accountprovider': {
            'Meta': {'object_name': 'AccountProvider', 'db_table': "'provider_admin'"},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identity': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Identity']"}),
            'provider': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Provider']"})
        },
        'core.allocation': {
            'Meta': {'object_name': 'Allocation', 'db_table': "'allocation'"},
            'delta': ('django.db.models.fields.IntegerField', [], {'default': '20160', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'threshold': ('django.db.models.fields.IntegerField', [], {'default': '10080', 'null': 'True', 'blank': 'True'})
        },
        'core.credential': {
            'Meta': {'object_name': 'Credential', 'db_table': "'credential'"},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identity': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Identity']"}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '256'})
        },
        'core.flow': {
            'Meta': {'object_name': 'Flow', 'db_table': "'flow'"},
            'alias': ('django.db.models.fields.CharField', [], {'max_length': '36'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'created_by_identity': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Identity']", 'null': 'True'}),
            'end_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instance': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Instance']", 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'blank': 'True'}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 10, 11, 0, 0)'}),
            'status': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.FlowType']"})
        },
        'core.flowtype': {
            'Meta': {'object_name': 'FlowType', 'db_table': "'flowtype'"},
            'end_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 10, 11, 0, 0)'})
        },
        'core.group': {
            'Meta': {'object_name': 'Group', 'db_table': "'group'", '_ormbases': [u'auth.Group']},
            u'group_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['auth.Group']", 'unique': 'True', 'primary_key': 'True'}),
            'identities': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Identity']", 'symmetrical': 'False', 'through': "orm['core.IdentityMembership']", 'blank': 'True'}),
            'instances': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Instance']", 'symmetrical': 'False', 'through': "orm['core.InstanceMembership']", 'blank': 'True'}),
            'leaders': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.User']", 'symmetrical': 'False'}),
            'machines': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Machine']", 'symmetrical': 'False', 'through': "orm['core.MachineMembership']", 'blank': 'True'}),
            'providers': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Provider']", 'symmetrical': 'False', 'through': "orm['core.ProviderMembership']", 'blank': 'True'})
        },
        'core.identity': {
            'Meta': {'object_name': 'Identity', 'db_table': "'identity'"},
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'provider': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Provider']"})
        },
        'core.identitymembership': {
            'Meta': {'object_name': 'IdentityMembership', 'db_table': "'identity_membership'"},
            'allocation': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Allocation']", 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identity': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Identity']"}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Group']"}),
            'quota': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Quota']"})
        },
        'core.instance': {
            'Meta': {'object_name': 'Instance', 'db_table': "'instance'"},
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'created_by_identity': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Identity']", 'null': 'True'}),
            'end_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip_address': ('django.db.models.fields.GenericIPAddressField', [], {'max_length': '39', 'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'provider_alias': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '256'}),
            'provider_machine': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ProviderMachine']"}),
            'shell': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Tag']", 'symmetrical': 'False', 'blank': 'True'}),
            'token': ('django.db.models.fields.CharField', [], {'max_length': '36', 'null': 'True', 'blank': 'True'}),
            'vnc': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'core.instancemembership': {
            'Meta': {'object_name': 'InstanceMembership', 'db_table': "'instance_membership'"},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instance': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Instance']"}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Group']"})
        },
        'core.instancestatus': {
            'Meta': {'object_name': 'InstanceStatus', 'db_table': "'instance_status'"},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        'core.instancestatushistory': {
            'Meta': {'object_name': 'InstanceStatusHistory', 'db_table': "'instance_status_history'"},
            'end_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instance': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Instance']"}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 10, 11, 0, 0)'}),
            'status': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.InstanceStatus']"})
        },
        'core.machine': {
            'Meta': {'object_name': 'Machine', 'db_table': "'machine'"},
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'created_by_identity': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Identity']", 'null': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'end_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'featured': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'icon': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'private': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'providers': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Provider']", 'symmetrical': 'False', 'through': "orm['core.ProviderMachine']", 'blank': 'True'}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 10, 11, 0, 0)'}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Tag']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'core.machineexport': {
            'Meta': {'object_name': 'MachineExport', 'db_table': "'machine_export'"},
            'end_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'export_file': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'export_format': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'export_name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'export_owner': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instance': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Instance']"}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 10, 11, 0, 0)'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '256'})
        },
        'core.machinemembership': {
            'Meta': {'object_name': 'MachineMembership', 'db_table': "'machine_membership'"},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'machine': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Machine']"}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Group']"})
        },
        'core.machinerequest': {
            'Meta': {'object_name': 'MachineRequest', 'db_table': "'machine_request'"},
            'access_list': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'end_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'exclude_files': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'installed_software': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'instance': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Instance']"}),
            'iplant_sys_files': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'new_machine': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'created_machine'", 'null': 'True', 'to': "orm['core.ProviderMachine']"}),
            'new_machine_description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'new_machine_name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'new_machine_owner': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'new_machine_provider': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Provider']"}),
            'new_machine_tags': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'new_machine_visibility': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'parent_machine': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'ancestor_machine'", 'to': "orm['core.ProviderMachine']"}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 10, 11, 0, 0)'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '256'})
        },
        'core.maintenancerecord': {
            'Meta': {'object_name': 'MaintenanceRecord', 'db_table': "'maintenance_record'"},
            'disable_login': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'end_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {}),
            'provider': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Provider']", 'null': 'True', 'blank': 'True'}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '256'})
        },
        'core.nodecontroller': {
            'Meta': {'object_name': 'NodeController', 'db_table': "'node_controller'"},
            'alias': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'end_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'hostname': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'private_ssh_key': ('django.db.models.fields.TextField', [], {}),
            'provider': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Provider']"}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 10, 11, 0, 0)'})
        },
        'core.provider': {
            'Meta': {'object_name': 'Provider', 'db_table': "'provider'"},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'end_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ProviderType']"})
        },
        'core.providercredential': {
            'Meta': {'object_name': 'ProviderCredential', 'db_table': "'provider_credential'"},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'provider': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Provider']"}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '256'})
        },
        'core.providermachine': {
            'Meta': {'object_name': 'ProviderMachine', 'db_table': "'provider_machine'"},
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True'}),
            'created_by_identity': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Identity']", 'null': 'True'}),
            'end_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '256'}),
            'machine': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Machine']"}),
            'provider': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Provider']"}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 10, 11, 0, 0)'})
        },
        'core.providermembership': {
            'Meta': {'object_name': 'ProviderMembership', 'db_table': "'provider_membership'"},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Group']"}),
            'provider': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Provider']"})
        },
        'core.providersize': {
            'Meta': {'object_name': 'ProviderSize', 'db_table': "'provider_size'"},
            'alias': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'cpu': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'disk': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'end_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'ram': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        'core.providertype': {
            'Meta': {'object_name': 'ProviderType', 'db_table': "'provider_type'"},
            'end_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 10, 11, 0, 0)'})
        },
        'core.quota': {
            'Meta': {'object_name': 'Quota', 'db_table': "'quota'"},
            'cpu': ('django.db.models.fields.IntegerField', [], {'default': '2', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'memory': ('django.db.models.fields.IntegerField', [], {'default': '4', 'null': 'True', 'blank': 'True'}),
            'storage': ('django.db.models.fields.IntegerField', [], {'default': '50', 'null': 'True', 'blank': 'True'}),
            'storage_count': ('django.db.models.fields.IntegerField', [], {'default': '1', 'null': 'True', 'blank': 'True'}),
            'suspended_count': ('django.db.models.fields.IntegerField', [], {'default': '2', 'null': 'True', 'blank': 'True'})
        },
        'core.size': {
            'Meta': {'object_name': 'Size', 'db_table': "'size'"},
            'alias': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'cpu': ('django.db.models.fields.IntegerField', [], {}),
            'disk': ('django.db.models.fields.IntegerField', [], {}),
            'end_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mem': ('django.db.models.fields.IntegerField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'provider': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Provider']"}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 10, 11, 0, 0)'})
        },
        'core.step': {
            'Meta': {'object_name': 'Step', 'db_table': "'step'"},
            'alias': ('django.db.models.fields.CharField', [], {'max_length': '36'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'created_by_identity': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Identity']", 'null': 'True'}),
            'end_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'exit_code': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'flow': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Flow']", 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instance': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Instance']", 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'blank': 'True'}),
            'script': ('django.db.models.fields.TextField', [], {}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 10, 11, 0, 0)'})
        },
        'core.tag': {
            'Meta': {'object_name': 'Tag', 'db_table': "'tag'"},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.SlugField', [], {'max_length': '128'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True', 'blank': 'True'})
        },
        'core.userprofile': {
            'Meta': {'object_name': 'UserProfile', 'db_table': "'user_profile'"},
            'background': ('django.db.models.fields.CharField', [], {'default': "'default'", 'max_length': '255'}),
            'default_size': ('django.db.models.fields.CharField', [], {'default': "'m1.small'", 'max_length': '255'}),
            'icon_set': ('django.db.models.fields.CharField', [], {'default': "'default'", 'max_length': '255'}),
            'quick_launch': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'selected_identity': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Identity']", 'null': 'True', 'blank': 'True'}),
            'send_emails': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['auth.User']", 'unique': 'True', 'primary_key': 'True'}),
            'vnc_resolution': ('django.db.models.fields.CharField', [], {'default': "'800x600'", 'max_length': '255'})
        },
        'core.volume': {
            'Meta': {'object_name': 'Volume', 'db_table': "'volume'"},
            'alias': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True'}),
            'created_by_identity': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Identity']", 'null': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'end_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'provider': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Provider']"}),
            'size': ('django.db.models.fields.IntegerField', [], {}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 10, 11, 0, 0)'})
        }
    }

    complete_apps = ['core']
    symmetrical = True
