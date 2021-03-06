"""
  Machine models for atmosphere.
"""
import json
import re
import os

from django.db import models
from django.utils import timezone
from core.models.user import AtmosphereUser as User


from core.application import save_app_data
from core.fields import VersionNumberField, VersionNumber
from core.models.application import get_application, create_application
from core.models.provider import Provider, AccountProvider
from core.models.machine import create_provider_machine
from core.models.node import NodeController

from atmosphere.settings import secrets
from threepio import logger

class MachineRequest(models.Model):
    """
    Storage container for the MachineRequestThread to start/restart the Queue
    Provides a Parent-Child relationship between the new image and ancestor(s)
    """
    # The instance to image.
    instance = models.ForeignKey("Instance")

    # Machine imaging Metadata
    status = models.TextField(default='', blank=True)
    parent_machine = models.ForeignKey("ProviderMachine",
                                       related_name="ancestor_machine")
    # Specifics for machine imaging.
    iplant_sys_files = models.TextField(default='', blank=True)
    installed_software = models.TextField(default='', blank=True)
    exclude_files = models.TextField(default='', blank=True)
    access_list = models.TextField(default='', blank=True)

    # Data for the new machine.
    new_machine_provider = models.ForeignKey(Provider)
    new_machine_name = models.CharField(max_length=256)
    new_machine_owner = models.ForeignKey(User)
    new_machine_visibility = models.CharField(max_length=256)
    new_machine_description = models.TextField(default='', blank=True)
    new_machine_tags = models.TextField(default='', blank=True)
    new_machine_version = VersionNumberField(default=int(VersionNumber(1,)))
    new_machine_forked = models.BooleanField(default=False)
    #Date time stamps
    start_date = models.DateTimeField(default=timezone.now())
    end_date = models.DateTimeField(null=True, blank=True)

    # Filled in when completed.
    new_machine = models.ForeignKey("ProviderMachine",
                                    null=True, blank=True,
                                    related_name="created_machine")


    def _get_meta_name(self):
        """
        admin_<username>_<name_under_scored>_<mmddyyyy_hhmmss>
        """
        meta_name = '%s_%s_%s_%s' %\
            ('admin', self.new_machine_owner.username,
            self.new_machine_name.replace(' ','_').replace('/','-'),
            self.start_date.strftime('%m%d%Y_%H%M%S'))
        return meta_name

    def new_machine_id(self):
        return 'zzz%s' % self.new_machine.identifier if self.new_machine else None

    def is_public(self):
        return "public" in self.new_machine_visibility.lower()

    def get_access_list(self):
        if '[' not in self.access_list:
            #Format = "test1, test2, test3"
            json_loads_list = str(raw_access_list.split(", "))
            #New Format = "[u'test1', u'test2', u'test3']"
        else:
            #Format = "[u'test1', u'test2', u'test3']"
            json_loads_list = self.access_list
        json_loads_list = json_loads_list.replace("'",'"').replace('u"', '"')
        user_list = json.loads(json_loads_list)
        return user_list

    def parse_access_list(self):
        user_list=re.split(', | |\n', self.access_list)
        return user_list

    def get_exclude_files(self):
        exclude=re.split(", | |\n", self.exclude_files)
        return exclude

    def get_credentials(self):
        old_provider = self.parent_machine.provider
        old_creds = old_provider.get_credentials()
        old_admin = old_provider.get_admin_identity().get_credentials()
        old_creds.update(old_admin)

        new_provider = self.new_machine_provider
        if old_provider.id == new_provider.id:
            new_creds = old_creds.copy()
        else:
            new_creds = new_provider.get_credentials()
            new_admin = new_provider.get_admin_identity().get_credentials()
            new_creds.update(new_admin)
        return (old_creds, new_creds)

    def prepare_manager(self):
        """
        Prepares, but does not initialize, manager(s)
        This allows the manager and required credentials to be passed to celery
        without causing serialization errors
        """
        from chromogenic.drivers.openstack import ImageManager as OSImageManager
        from chromogenic.drivers.eucalyptus import ImageManager as EucaImageManager

        orig_provider = self.parent_machine.provider
        dest_provider = self.new_machine_provider
        orig_type = orig_provider.get_type_name().lower()
        dest_type = dest_provider.get_type_name().lower()

        origCls = destCls = None
        if orig_type == 'eucalyptus':
            origCls = EucaImageManager
        elif orig_type == 'openstack':
            origCls = OSImageManager

        if dest_type == orig_type:
            destCls = origCls
        elif dest_type == 'eucalyptus':
            destCls = EucaImageManager
        elif dest_type == 'openstack':
            destCls = OSImageManager

        orig_creds, dest_creds = self.get_credentials()
        orig_creds = origCls._build_image_creds(orig_creds)
        dest_creds = destCls._build_image_creds(dest_creds)

        return (origCls, orig_creds, destCls, dest_creds)

    def get_imaging_args(self):
        """
        Prepares the entire machine request for serialization to celery

        TODO: Add things like description and tags to export and migration drivers
        """
        from chromogenic.drivers.openstack import ImageManager as OSImageManager
        from chromogenic.drivers.eucalyptus import ImageManager as EucaImageManager

        (orig_managerCls, orig_creds,
         dest_managerCls, dest_creds) = self.prepare_manager()
    
        download_dir = secrets.LOCAL_STORAGE
    
        imaging_args = {
            "instance_id": self.instance.provider_alias,
            "image_name": self.new_machine_name,
            "download_dir" : download_dir}
        if issubclass(orig_managerCls, OSImageManager):
            id_owner = self.instance.created_by_identity
            tenant_cred = id_owner.credential_set.filter(
                    key='ex_tenant_name')
            if not tenant_cred:
                tenant_cred = id_owner.credential_set.filter(
                        key='ex_project_name')
            if not tenant_cred:
                raise Exception("You should not be here! Update the key "
                        "used for openstack tenant names!")
            tenant_cred = tenant_cred[0]
            download_location = os.path.join(
                    download_dir, tenant_cred.value)
            download_location = os.path.join(
                    download_location, '%s.qcow2' % self.new_machine_name)
            imaging_args['download_location'] = download_location 
        elif issubclass(orig_managerCls, EucaImageManager):
            meta_name = self._get_meta_name()
            public_image = self.is_public()
            #Splits the string by ", " OR " " OR "\n" to create the list
            private_users = self.parse_access_list()
            exclude = self.get_exclude_files()
            #Create image on image manager
            node_scp_info = self.get_euca_node_info(orig_managerCls, orig_creds)
            imaging_args.update({
                "public" : public_image,
                "private_user_list" : private_users,
                "exclude" : exclude,
                "meta_name" : meta_name,
                "node_scp_info" : node_scp_info,
            })
        orig_provider = self.parent_machine.provider
        dest_provider = self.new_machine_provider
        orig_platform = orig_provider.get_platform_name().lower()
        dest_platform = dest_provider.get_platform_name().lower()
        if orig_platform != dest_platform:
            if orig_platform == 'kvm' and dest_platform == 'xen':
                imaging_args['kvm_to_xen'] = True
            elif orig_platform == 'xen' and dest_platform == 'kvm':
                imaging_args['xen_to_kvm'] = True
        return imaging_args

    def get_euca_node_info(self, euca_managerCls, euca_creds):
        node_dict = {
                'hostname':'',
                'port':'',
                'private_key':''
        }
        instance_id = self.instance.provider_alias
        #Prepare and use the manager
        euca_manager = euca_managerCls(**euca_creds)
        node_ip = euca_manager.get_instance_node(instance_id)

        #Find the matching node
        try:
            core_node = NodeController.objects.get(alias=node_ip)
            node_dict['hostname'] = core_node.hostname
            node_dict['port'] = core_node.port
            node_dict['private_key'] = core_node.private_ssh_key
        except NodeController.DoesNotExist:
            logger.error("Must create a nodecontroller for IP: %s" % node_ip)
        #Return a dict containing information on how to SCP to the node
        return node_dict

    def __unicode__(self):
        return '%s Instance: %s Name: %s Status: %s'\
                % (self.new_machine_owner, self.instance.provider_alias,
                   self.new_machine_name, self.status)

    class Meta:
        db_table = "machine_request"
        app_label = "core"

def process_machine_request(machine_request, new_image_id):
    from core.models.machine import add_to_cache
    from core.models.tag import Tag
    from core.models import Identity, ProviderMachine
    #Get all the data you can from the machine request
    new_provider = machine_request.new_machine_provider
    owner_ident = Identity.objects.get(created_by=machine_request.new_machine_owner, provider=new_provider)
    parent_mach = machine_request.instance.provider_machine
    parent_app = machine_request.instance.provider_machine.application
    if machine_request.new_machine_tags:
        tags = [Tag.objects.get(name__iexact=tag) for tag in
                machine_request.new_machine_tags.split(',')]
    else:
        tags = []

    #if machine_request.new_machine_forked:
    #NOTE: Swap these lines when application forking/versioning is supported in the UI
    if True:
        # This is a brand new app and a brand new providermachine
        new_app = create_application(
                new_image_id,
                new_provider.id,
                machine_request.new_machine_name, 
                owner_ident,
                #new_app.Private = False when machine_request.is_public = True
                not machine_request.is_public(),
                machine_request.new_machine_version,
                machine_request.new_machine_description,
                tags)
        app_to_use = new_app
        description = machine_request.new_machine_description
    else:
        #This is NOT a fork, the application to be used is that of your
        # ancestor, and the app owner should not be changed.
        app_to_use = parent_app
        #Include your ancestors tags, description if necessary
        tags.extend(parent_app.tags.all())
        if not machine_request.new_machine_description:
            description = parent_app.description
        else:
            description = machine_request.new_machine_description
        app.private = not machine_request.is_public()

        app.tags = tags
        app.description = description
        app.save()
    #Set application data to an existing/new providermachine
    try:
        new_machine = ProviderMachine.objects.get(identifier=new_image_id)
        new_machine.application = app_to_use
        new_machine.version = machine_request.new_machine_version
        new_machine.created_by = machine_request.new_machine_owner
        new_machine.created_by_identity = owner_ident
        new_machine.save()
    except ProviderMachine.DoesNotExist:
        new_machine = create_provider_machine(
            machine_request.new_machine_name, new_image_id,
            machine_request.new_machine_provider_id, app_to_use,
            {'version' : machine_request.new_machine_version})

    #Be sure to write all this data to openstack metadata
    #So that it can continue to be the 'authoritative source'
    if not machine_request.is_public():
        upload_privacy_data(machine_request, new_machine)
    save_app_data(new_machine.application)
    add_to_cache(new_machine)
    machine_request.new_machine = new_machine
    machine_request.end_date = timezone.now()
    machine_request.status = 'completed'
    machine_request.save()
    return machine_request

def upload_privacy_data(machine_request, new_machine):
    from service.accounts.openstack import AccountDriver as OSAccounts
    from service.driver import get_admin_driver
    prov = new_machine.provider
    accounts = OSAccounts(prov)
    if not accounts:
        print "Aborting import: Could not retrieve OSAccounts driver "\
                "for Provider %s" % prov
        return
    admin_driver = get_admin_driver(prov)
    if not admin_driver:
        print "Aborting import: Could not retrieve admin_driver "\
                "for Provider %s" % prov
        return
    img = accounts.image_manager.get_image(new_machine.identifier)
    tenant_list = machine_request.get_access_list()
    #All in the list will be added as 'sharing' the OStack img
    #All tenants already sharing the OStack img will be added to this list
    tenant_list = sync_image_access_list(accounts, img, names=tenant_list)
    #Make private on the DB level
    make_private(accounts.image_manager, img, new_machine, tenant_list)



def share_with_admins(private_userlist, provider_id):
    """
    NOTE: This will always work, but the userlist could get long some day.
    Another option would be to create an 'admin' tenant that all of core
    services and the admin are members of, and add only that tenant to the
    list.
    """
    if type(private_userlist) != list:
        raise Exception("Expected private_userlist to be list, got %s: %s"
                        % (type(private_userlist), private_userlist))

    from authentication.protocol.ldap import get_core_services
    core_services = get_core_services()
    admin_users = [ap.identity.created_by.username for ap in
            AccountProvider.objects.filter(provider__id=provider_id)]
    private_userlist.extend(core_services)
    private_userlist.extend(admin_users)
    return private_userlist

def share_with_self(private_userlist, username):
    if type(private_userlist) != list:
        raise Exception("Expected type(private_userlist) to be list, got %s: %s"
                        % (type(private_userlist), private_userlist))

    #TODO: Optionally, Lookup username and get the Projectname
    private_userlist.append(str(username))
    return private_userlist

def sync_image_access_list(accounts, img, names=None):
    projects = []
    shared_with = accounts.image_manager.shared_images_for(
            image_id=img.id)
    #if not shared_with:
    #    return tenant_names
    #Find tenants who are marked as 'sharing' on openstack but not on DB
    #Or just in One-line..
    projects = [accounts.get_project_by_id(member.member_id) for member in shared_with]
    #Any names who aren't already on the image should be added
    #Find names who are marekd as 'sharing' on DB but not on OpenStack
    for name in names:
        project = accounts.get_project(name)
        if project and project not in projects:
            print "Sharing image %s with project named %s" \
                    % (img.id, name)
            accounts.image_manager.share_image(img, name)
            projects.append(project)
    return projects

def make_private(image_manager, image, provider_machine, tenant_list=[]):
    #Circ.Dep. DO NOT MOVE UP!!
    from core.models import Group, ProviderMachineMembership

    if image.is_public == True:
        print "Marking image %s private" % image.id
        image_manager.update_image(image, is_public=False)
    if provider_machine.application.private == False:
        print "Marking application %s private" % provider_machine.application
        provider_machine.application.private = True
        provider_machine.application.save()
    #Add all these people by default..
    owner = provider_machine.application.created_by
    group_list = owner.group_set.all()
    if tenant_list:
        for tenant in tenant_list:
            name = tenant.name
            group = Group.objects.get(name=name)
            obj, created = ProviderMachineMembership.objects.get_or_create(
                    group=group, 
                    provider_machine=provider_machine)
            if created:
                print "Created new ProviderMachineMembership: %s" \
                    % (obj,)
