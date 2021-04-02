# Copyright 2021 Xilinx, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import inspect
from abc import abstractmethod
from typing import List, Tuple

from chipscopy.tcf.services import from_xargs
from .server_info import ServerInfo
from .view_info import ViewInfo
from chipscopy import dm
from chipscopy.dm import chipscope, request


def get_cs_view(server: ServerInfo) -> ViewInfo:
    """
    Gets the Chipscope view for handling debug cores

    :param server: Active Chipscope server for which to get the CS View
    :return: Chipscope View
    """
    if not server or not isinstance(server, ServerInfo):
        raise Exception("Attempted to get view for inactive server info object")
    return server.get_view(chipscope)


class CoreParent(dm.Node):
    @staticmethod
    def is_compatible(node: dm.Node) -> bool:
        return node.type

    def setup_cores(self, debug_hub_addrs: List[int] = (), done: request.DoneCallback = None):
        """
        Sets up cores on a given context

        :param debug_hub_addrs: List of address offsets for Debug Hubs
        :param done: DoneRequest callback
        :return: Token of request
        """
        proc = self.manager.channel.getRemoteService("ChipScope")
        done = request._make_callback(done)

        def done_setup(token, error, results):
            self.remove_pending(token)
            if done:
                done.done_request(token, error, results)

        # add pending to indicate that this node is being changed
        return self.add_pending(proc.setup_debug_cores(self.ctx, debug_hub_addrs, done_setup))

    def remove_cores(self, done: request.DoneCallback = None):
        """
        Removes child cores on a given context

        :param done: DoneRequest callback
        :return: Token of request
        """
        proc = self.manager.channel.getRemoteService("ChipScope")
        done = request._make_callback(done)

        def done_remove(token, error, results):
            self.remove_pending(token)
            if done:
                done.done_request(token, error, results)

        # add pending to indicate that this node is being changed
        return self.add_pending(proc.remove_debug_cores(self.ctx, done_remove))


class CoreClient(dm.Node):
    def post_init(self):
        def done_post_init(token, error, results):
            self.remove_pending(token)
            if error:
                # Detect and bypass disabled DDRMC found error to be thrown
                disabled_mc = "DDRMC get_initialize: DDRMC is not enabled"
                if isinstance(error, dict) and (disabled_mc in error["Format"]):
                    pass
                else:
                    raise Exception(error)

        service = self.get_service_proxy()
        if service:
            self.add_pending(service.initialize(self.ctx, done_post_init))

    @abstractmethod
    def get_service_proxy(self):
        pass

    def make_done(self, done, restore_tuple=False) -> Tuple:
        service = self.get_service_proxy()
        done = request._make_callback(done)

        def done_core_command(token, error, results):
            self.remove_pending(token)
            if done:
                # results = from_xargs(results)
                if isinstance(results, list) and len(results) == 1:
                    results = results[0]
                if restore_tuple and isinstance(results, list):
                    results = [None if not item else tuple(item) for item in results]

                done.done_request(token, error, results)

        return service, done_core_command


def progress_callback(func):
    """
    Simple decorator to pass on the progress result and suppress the token and error.
    In case of progress TCF messages, the value of error is same as token.
    """

    def actual_decorator(*args):
        progress_result = args[2]
        func(progress_result)

    return actual_decorator
