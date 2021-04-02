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


from typing import Dict, Any, List
from chipscopy.tcf import channel
from chipscopy.tcf.services import Service, DoneHWCommand
from chipscopy.tcf.services.arguments import from_xargs
from chipscopy.utils.logger import log
from chipscopy.utils import words_from_bytes


NAME = "DebugCore"
"""DebugCore service name."""


class DebugNodeListener(object):
    """Debug node event listener is notified when debug node hierarchy changes,
    and when node is modified by DebugCore service commands.
    """

    def node_added(self, node_ctx: str, props: Dict[str, Any]):
        """
        Called when a new Debug Node was added
        :param node_ctx: Debug node context id
        :param props: Debug node properties added
        """
        pass

    def node_changed(self, node_ctx: str, props: Dict[str, Any]):
        """
        Called when a new Debug Node was changed
        :param node_ctx: Debug node context id
        :param props: Debug node properties changed
        """
        pass

    def node_removed(self, node_ctx: str):
        """
        Called when a new Debug Node was removed
        :param node_ctx: Debug node context id
        """
        pass


class DebugCoreProxy(Service):
    def __init__(self, channel):
        super().__init__(channel)
        self.listeners = {}

    """TCF DebugCore service interface."""

    def getName(self):
        """Get this service name.

        :returns: The value of string :const:`NAME`
        """
        return NAME

    def detect_hubs(self, ctx: str, hub_addresses: List[int], done: DoneHWCommand):
        """Detects cores given a parent context and expected core offsets

        :param ctx: Parent context handle
        :param hub_addresses: List of offsets for each Debug Hub
        :param done: Callback with result and any error
        :returns: Token of command request
        """
        if not hub_addresses:
            hub_addresses = []
        return self.send_xicom_command("detectHubs", (ctx, hub_addresses), done)

    def setup_cores(self, ctx: str, done: DoneHWCommand):
        """
        Sets up hardened debug nodes from a context
        :param ctx: Context underwhich to setup debug nodes
        :param done: Callback with result and any error
        :returns: Token of command request
        """
        return self.send_xicom_command("setupCores", (ctx,), done)

    def remove_cores(self, ctx: str, done: DoneHWCommand):
        """
        Removes child cores from a Debug node context
        :param ctx: Context underwhich to remove debug nodes
        :param done: Callback with result and any error
        :returns: Token of command request
        """
        return self.send_xicom_command("removeCores", (ctx,), done)

    def get_children(self, ctx: str, done: DoneHWCommand):
        """Retrieves list of children given a parent context.
        If no parent context given it returns the available list of parent core contexts.

        :param ctx: Parent context handle (defaults None)
        :param done: Callback with result and any error
        :returns: Token of command request
        :results: children - list of children
        """
        if not ctx:
            ctx = ""
        return self.send_xicom_command("getChildren", (ctx,), done)

    def get_context(self, ctx: str, done: DoneHWCommand):
        """Retrieves list of context given a debug core context.

        :param ctx: Debug core context
        :param done: Callback with result and any error
        :returns: Token of command request
        :results: |Dict| of available context properties
        """
        return self.send_xicom_command("getContext", (ctx,), done)

    def run_sequence(self, ctx: str, seq, done: DoneHWCommand):
        """
        Runs a sequence of memory transactions.

        :param ctx: Debug core context
        :param seq: List of transactions to run in the given sequence.
            Each transaction is a dict of transaction properties.
        :param done: Callback with result and any error
        :returns: Token of command request
        :results: seq - list of read transactions with resulting values in the order ran.
        """
        if log.is_domain_enabled("debugcore", "DEBUG"):
            log.debugcore.debug(f"Running sequence {len(seq)}:")
            for op in seq:
                log.debugcore.debug(f"\t{op}")
                if "data" in op:
                    words = words_from_bytes(op["data"])
                    hexstr = " ".join(f"{word:08X}" for word in words)
                    log.debugcore.debug(f"\t\t{hexstr}")
        return self.send_xicom_command("sequence", (ctx, seq), done)

    def lock(self, ctx: str, done: DoneHWCommand):
        """Locks a targeted debug core so that only this channel can access.
        Debug cores automatically unlock during a channel disconnect.

        :param ctx: Debug core context to lock
        :param done: Callback with result and any error
        :returns: Token of command request
        :results: success - true if locked
        """
        raise NotImplementedError("Abstract method")

    def unlock(self, ctx: str, done: DoneHWCommand):
        """Unlocks a targeted debug core. See `lock`

        :param ctx: Debug core context to unlock
        :param done: Callback with result and any error
        :returns: Token of command request
        :results: success - true if unlocked.  Also considered successful if already unlocked.
        """
        raise NotImplementedError("Abstract method")

    def perf_test(self, ctx: str, props: Dict[str, Any] = {}, done: DoneHWCommand = None):
        return self.send_xicom_command("perfTest", (ctx, props), done)

    def add_listener(self, listener: DebugNodeListener):
        """Add DebugCore service event listener.
        :param listener: Event listener implementation.
        """
        l = ChannelEventListener(self, listener)
        self.channel.addEventListener(self, l)
        self.listeners[listener] = l

    def remove_listener(self, listener: DebugNodeListener):
        """Remove DebugCore service event listener.
        :param listener: Event listener implementation.
        """
        l = self.listeners.get(listener)
        if l:
            del self.listeners[listener]
            self.channel.removeEventListener(self, l)


class ChannelEventListener(channel.EventListener):
    def __init__(self, service, listener):
        self.service = service
        self.listener = listener

    def event(self, name, data):
        try:
            args = channel.fromJSONSequence(data)
            if name == "nodeAdded":
                args = from_xargs(args)
                assert len(args) >= 2
                self.listener.node_added(args[0], args[1])
            elif name == "nodeChanged":
                args = from_xargs(args)
                assert len(args) >= 2
                self.listener.node_changed(args[0], args[1])
            elif name == "nodeRemoved":
                args = from_xargs(args)
                assert len(args) == 1
                self.listener.node_removed(args[0])
            else:
                raise IOError("Memory service: unknown event: " + name)
        except Exception as x:
            import sys

            x.tb = sys.exc_info()[2]
            self.service.channel.terminate(x)


DebugCoreService = DebugCoreProxy
