# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'MachineExport.export_name'
        db.add_column('machine_export', 'export_name',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=256),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'MachineExport.export_name'
        db.delete_column('machine_export', 'export_name')


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
        'core.credential': {
            'Meta': {'object_name': 'Credential', 'db_table': "'credential'"},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identity': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Identity']"}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '256'})
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
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identity': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Identity']"}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Group']"}),
            'quota': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Quota']"})
        },
        'core.instance': {
            'Meta': {'object_name': 'Instance', 'db_table': "'instance'"},
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
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
        'core.machine': {
            'Meta': {'object_name': 'Machine', 'db_table': "'machine'"},
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'end_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'featured': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'icon': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'init_package': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Package']", 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'private': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'providers': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Provider']", 'symmetrical': 'False', 'through': "orm['core.ProviderMachine']", 'blank': 'True'}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 6, 27, 0, 0)'}),
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
            'start_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 6, 27, 0, 0)'}),
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
            'start_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 6, 27, 0, 0)'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '256'})
        },
        'core.maintenancerecord': {
            'Meta': {'object_name': 'MaintenanceRecord', 'db_table': "'maintenance_record'"},
            'disable_login': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'end_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {}),
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
            'start_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 6, 27, 0, 0)'})
        },
        'core.package': {
            'Meta': {'object_name': 'Package', 'db_table': "'package'"},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'scripts': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Script']", 'symmetrical': 'False'}),
            'sha1sum': ('django.db.models.fields.CharField', [], {'max_length': '50'})
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
        'core.providermachine': {
            'Meta': {'object_name': 'ProviderMachine', 'db_table': "'provider_machine'"},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '256'}),
            'machine': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Machine']"}),
            'provider': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Provider']"})
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
            'start_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 6, 27, 0, 0)'})
        },
        'core.quota': {
            'Meta': {'object_name': 'Quota', 'db_table': "'quota'"},
            'cpu': ('django.db.models.fields.IntegerField', [], {'default': '2', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'memory': ('django.db.models.fields.IntegerField', [], {'default': '4', 'null': 'True', 'blank': 'True'}),
            'storage': ('django.db.models.fields.IntegerField', [], {'default': '50', 'null': 'True', 'blank': 'True'}),
            'storage_count': ('django.db.models.fields.IntegerField', [], {'default': '1', 'null': 'True', 'blank': 'True'})
        },
        'core.script': {
            'Meta': {'object_name': 'Script', 'db_table': "'script'"},
            'description': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'version': ('django.db.models.fields.IntegerField', [], {})
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
            'start_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 6, 27, 0, 0)'})
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
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'end_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'provider': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Provider']"}),
            'size': ('django.db.models.fields.IntegerField', [], {}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 6, 27, 0, 0)'})
        }
    }

    complete_apps = ['core']