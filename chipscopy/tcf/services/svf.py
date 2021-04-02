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

from chipscopy.tcf.services import Service, DoneHWCommand

NAME = "svf"
"""SVF service name."""


class SVFService(Service):
    """TCF SVF service interface."""
    def getName(self) -> str:
        """
        Get this service name.

        :returns: The value of string :const:`NAME`
        """
        return NAME

    def add_target(self, name: str, done: DoneHWCommand) -> None:
        """
        Create an SVF target.

        :param name: Name of target
        :param done: Callback with result and any error.
        """
        raise NotImplementedError("Abstract method")

    def add_device(self, target_ctx: str, name: str, done: DoneHWCommand) -> str:
        """
        Adds SVF device from database using the given name to the target chain.

        :param target_ctx: Context id of the target chain
        :param name: Name of the device to add (must be a known device)
        :param done: Callback with result and any error
        :return: Name of added device
        """
        raise NotImplementedError("Abstract method")

    def remove_target(self, target_ctx: str, done: DoneHWCommand) -> None:
        """
        Deletes the target and any associated devices.

        :param target_ctx: Context id of the target chain
        :param done: Callback with the result and any error
        """
        raise NotImplementedError("Abstract method")
