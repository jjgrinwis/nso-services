# -*- mode: python; python-indent: 4 -*-
import ncs
from ncs.application import Service


# ------------------------
# SERVICE CALLBACK EXAMPLE
# ------------------------
class ServiceCallbacks(Service):

    # The create() callback is invoked inside NCS FASTMAP and
    # must always exist.
    @Service.create
    def cb_create(self, tctx, root, service, proplist):
        self.log.info('Service create(service=', service._path, ')')
        self.log.info('starting to configure internet-id:', service.internet_id)
  
        # our internet routers
        ir = ['mx01','mx02']
           
        for link in service.link:
           tvars = ncs.template.Variables()
           template = ncs.template.Template(service)
 
           # unique AS per service 
           tvars.add("AS", service.as_number) 

           self.log.info('starting to configure link-id:', link.link_id)
           self.log.info('starting to configure interface:', link.interface)

           link_id = link.link_id

           # Calculate IP address from unique site ID: 172.x.y.z
           pe_ip_o2 = 31 - (link_id * 4) % 4096 # Second octet
           pe_ip_o3 = ((link_id * 4) % 4096) / 64 # Third octet
           pe_ip_o4 = ((link_id * 4) % 4096) % 64 + 1 # Fourth octet
           ce_ip_o4 = pe_ip_o4 + 1 # Fourth octet for CE side
   
           link_ip = '172.{}.{}.{}'.format(pe_ip_o2, pe_ip_o3, pe_ip_o4)
           peer_ip = '172.{}.{}.{}'.format(pe_ip_o2, pe_ip_o3, ce_ip_o4)

           self.log.info('starting to configure link_ip:', link_ip)
           self.log.info('starting to configure peer_id:', peer_ip)

           # let's lookup lo0 from cdb
           # /devices/device[name='mx01']/config/junos:configuration/interfaces/interface[name='lo0']/unit[name='0']/family/inet/address[name='2.2.2.2/32']
           # .address will return a list with only keys
           loopback_list = root.devices.device[link.device].config.configuration.interfaces.interface["lo0"].unit["0"].family.inet.address
           loopback_list_ir = root.devices.device[ir[link_id]].config.configuration.interfaces.interface["lo0"].unit["0"].family.inet.address

           # now get loopback address. We're using the value from hash key 0 to get loopback addres
           loopback_address = loopback_list[loopback_list.keys()[0]].name
           loopback_address_ir = loopback_list_ir[loopback_list_ir.keys()[0]].name

           # Now create unique vlan_id based on internet_id + link+id
           vlan_id = str(service.internet_id) + str(link_id)

           tvars.add('NODE', link.device)
           tvars.add('INTERFACE', link.interface)
           tvars.add('LIP', link_ip)
           tvars.add('PIP', peer_ip)
           tvars.add('INTERNET_ID', service.internet_id)
           tvars.add('LID', link_id)
           tvars.add('VLAN', vlan_id)
           tvars.add("LOOPBACK", loopback_address.split("/")[0])
           tvars.add("LOOPBACK_IR", loopback_address_ir.split("/")[0])
           tvars.add("PESI", loopback_address.split(".")[0])
           tvars.add("IRSI", loopback_address_ir.split(".")[0])
           tvars.add("IR", ir[link_id]) 
            
           self.log.info('vars', tvars)
           template = ncs.template.Template(service)
           template.apply('ir-template', tvars)
           template.apply('pe-template', tvars)

    # The pre_modification() and post_modification() callbacks are optional,
    # and are invoked outside FASTMAP. pre_modification() is invoked before
    # create, update, or delete of the service, as indicated by the enum
    # ncs_service_operation op parameter. Conversely
    # post_modification() is invoked after create, update, or delete
    # of the service. These functions can be useful e.g. for
    # allocations that should be stored and existing also when the
    # service instance is removed.

    # @Service.pre_lock_create
    # def cb_pre_lock_create(self, tctx, root, service, proplist):
    #     self.log.info('Service plcreate(service=', service._path, ')')

    # @Service.pre_modification
    # def cb_pre_modification(self, tctx, op, kp, root, proplist):
    #     self.log.info('Service premod(service=', kp, ')')

    # @Service.post_modification
    # def cb_post_modification(self, tctx, op, kp, root, proplist):
    #     self.log.info('Service premod(service=', kp, ')')


# ---------------------------------------------
# COMPONENT THREAD THAT WILL BE STARTED BY NCS.
# ---------------------------------------------
class Main(ncs.application.Application):
    def setup(self):
        # The application class sets up logging for us. It is accessible
        # through 'self.log' and is a ncs.log.Log instance.
        self.log.info('Main RUNNING')

        # Service callbacks require a registration for a 'service point',
        # as specified in the corresponding data model.
        #
        self.register_service('internet-servicepoint', ServiceCallbacks)

        # If we registered any callback(s) above, the Application class
        # took care of creating a daemon (related to the service/action point).

        # When this setup method is finished, all registrations are
        # considered done and the application is 'started'.

    def teardown(self):
        # When the application is finished (which would happen if NCS went
        # down, packages were reloaded or some error occurred) this teardown
        # method will be called.

        self.log.info('Main FINISHED')
