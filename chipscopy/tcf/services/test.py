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

from typing import List, Dict, Any
from chipscopy.tcf.services import Service, DoneHWCommand

NAME = "Test"
"""Test service name."""


class TestListener(object):
    """Test event listener is notified when test service needs to send an internal event
    """

    def exiting(self):
        """Called when an exit command is received.  Used to gracefully shuttdown during testing when a client is done.
        """
        pass


class TestService(Service):
    """TCF Test service interface."""
    def getName(self):
        """Get this service name.

        :returns: The value of string :const:`NAME`
        """
        return NAME

    def add_manager(self, manager_name: str, done: DoneHWCommand):
        """
        Adds manager of a given name to server
        :param manager_name: Name to add
        :param done: Callback when command is complete
        """
        raise NotImplementedError("Abstract method")

    def remove_manager(self, manager_name: str, done: DoneHWCommand):
        """
        Removes manager of a given name from server
        :param manager_name: Name to remove
        :param done: Callback when command is complete
        """
        raise NotImplementedError("Abstract method")

    def add_node(self, manager_name: str, ctx: str, props: Dict, done: DoneHWCommand):
        """
        Adds node to manager with given props.  If property, ParentID, is set the node will be added as a child of
        node with that context id.

        :param manager_name: Name of manager to which to add the node
        :param ctx: Node context handle to use
        :param props: Properties to set in the node
        :param done: Callback when command is complete
        """
        raise NotImplementedError("Abstract method")

    def remove_node(self, manager_name: str, ctx: str, done: DoneHWCommand):
        """
        Removes node from manager.

        :param manager_name: Name of manager from which to remove
        :param ctx: Node context handle to use
        :param done: Callback when command is complete
        """
        raise NotImplementedError("Abstract method")

    def update_node(self, manager_name: str, ctx: str, props: Dict, done: DoneHWCommand):
        """
        Updates node with given props.

        :param manager_name: Name of manager
        :param ctx: Node context handle to use
        :param props: Properties to set in the node
        :param done: Callback when command is complete
        """
        raise NotImplementedError("Abstract method")

    def exit(self, done: DoneHWCommand):
        """
        Tells the server to exit.

        :param done: Callback when command is complete
        """
        raise NotImplementedError("Abstract method")

