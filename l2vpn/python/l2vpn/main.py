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
        self.log.info('Service create new(service=', service._path, ')')
        self.log.debug("Service ", service)

        # our template vars
        tvars = ncs.template.Variables()

        # get ID from YANG model and add to template vars
        tvars.add('ID', service.name)

        # get our policer, one policer for every UNI
        tvars.add('POLICER', service.policer)

        # Our list with endpoints from our l2vpn yang model
        # endpoint is always device/interface combination
        endpoints = service.device_if
        number = 0

        for endpoint in endpoints:
           node = 'NODE' + str(number)
           tvars.add(node, endpoint.device)

           interface = 'INTERFACE' +  str(number)
           tvars.add(interface, endpoint.interface)
 
           # let's lookup lo0 from cdb
           # /devices/device[name='mx01']/config/junos:configuration/interfaces/interface[name='lo0']/unit[name='0']/family/inet/address[name='2.2.2.2/32']
           # .address will return a list with only keys
           loopback_list = root.devices.device[endpoint.device].config.configuration.interfaces.interface["lo0"].unit["0"].family.inet.address
           #self.log.debug("loopback", loopback_address)
          
           # now get loopback address. We're using the value from hash key 0 to get loopback addres 
           loopback_address = loopback_list[loopback_list.keys()[0]].name
           loopback = 'LOOPBACK' + str(number) 
           tvars.add(loopback, loopback_address.split("/")[0])

           # let's show our generated vars
           self.log.debug("tvars", tvars)

           number += 1

        template = ncs.template.Template(service)
        template.apply('l2vpn-template', tvars)

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
        self.register_service('l2vpn-servicepoint', ServiceCallbacks)

        # If we registered any callback(s) above, the Application class
        # took care of creating a daemon (related to the service/action point).

        # When this setup method is finished, all registrations are
        # considered done and the application is 'started'.

    def teardown(self):
        # When the application is finished (which would happen if NCS went
        # down, packages were reloaded or some error occurred) this teardown
        # method will be called.

        self.log.info('Main FINISHED')
