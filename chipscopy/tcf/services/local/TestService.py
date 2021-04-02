# *****************************************************************************
# * Copyright (c) 2020 Xilinx, Inc.
# * All rights reserved. This program and the accompanying materials
# * are made available under the terms of the Eclipse Public License 2.0
# * which accompanies this distribution, and is available at
# * https://www.eclipse.org/legal/epl-2.0/
# *
# * Contributors:
# *     Xilinx
# *****************************************************************************

from .. import Service, ServiceProvider, add_service_provider
from . import CommandServer
from ..test import NAME, TestListener
from .. import from_xargs
from chipscopy.dm.request import CsRequest, DoneRequest
from chipscopy import dm
from chipscopy.dm import debugcore
from chipscopy.tcf import protocol

MANAGER_TEST_NAME = "test_manager"

listeners = set()


class CsDoneHw(DoneRequest):
    def __init__(self, req):
        self.req = req

    def done_request(self, token, error, args):
        if error:
            self.req.sendError(error)
        else:
            if not args:
                args = ()
            self.req.sendXicomResult(*args)


class TestService(Service):
    def __init__(self):
        pass

    def getName(self):
        return NAME

    def addManagerCmd(self, req):
        args = from_xargs(req.args)
        name = args[0]
        manager = debugcore.DebugCoreManager(name)

        if manager:
            dm.add_manager(manager)
            req.sendXicomResult()
        else:
            req.sendError(f"Could not create manager {name}")

    def removeManagerCmd(self, req):
        args = from_xargs(req.args)

        name = args[0]

        manager = dm.get_manager(name)

        if not manager:
            req.SendError(f"Could not find manager {name}")

        dm.remove_manager(manager)
        req.sendXicomResult()

    def addNodeCmd(self, req):
        args = from_xargs(req.args)

        manager_name = args[0]
        ctx = args[1]
        props = args[2]

        manager = dm.get_manager(manager_name)

        if not manager:
            req.sendError(f"Invalid manager name {manager_name}")
            return

        class AddTestNodeRequest(CsRequest):
            def run(self):
                parent_ctx = props.get("ParentID")
                if not parent_ctx:
                    parent_ctx = ""
                node = manager.add_node(ctx, parent_ctx)

                if node:
                    if props:
                        node.update(props)
                    protocol.invokeLater(req.sendXicomResult)
                else:
                    req.sendError("Could not create node {ctx}, parent {parent_ctx}")
                return True

        cs_req = AddTestNodeRequest(manager)
        cs_req()

    def removeNodeCmd(self, req):
        args = from_xargs(req.args)

        manager_name = args[0]
        ctx = args[1]

        manager = dm.get_manager(manager_name)

        if not manager:
            req.sendError(f"Invalid manager name {manager_name}")
            return

        class RemoveTestNodeRequest(CsRequest):
            def run(self):
                manager.remove_node(ctx)
                protocol.invokeLater(self.done_run)

        cs_req = RemoveTestNodeRequest(manager, done=CsDoneHw(req))
        cs_req()

    def updateNodeCmd(self, req):
        args = from_xargs(req.args)

        manager_name = args[0]
        ctx = args[1]
        props = args[2]

        manager = dm.get_manager(manager_name)

        if not manager:
            req.sendError(f"Invalid manager name {manager_name}")
            return

        class UpdateNodeRequest(CsRequest):
            def run(self):
                self.node.update(props)
                protocol.invokeLater(self.done_run)

        cs_req = UpdateNodeRequest(manager, ctx, done=CsDoneHw(req))
        cs_req()

    def exitCmd(self, req):
        req.sendXicomResult()
        for listener in listeners:
            protocol.invokeLater(listener.exiting)


class TestServiceProvider(ServiceProvider):
    def get_local_service(self, _channel):
        _channel.addCommandServer(
            TestService.service,
            CommandServer(TestService.service, _channel)
        )
        return TestService.service,


# creating singleton
TestService.service = TestService()
add_service_provider(TestServiceProvider())
