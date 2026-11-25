# Copyright (C) 2021-2022, Xilinx, Inc.
# Copyright (C) 2022-2026, Advanced Micro Devices, Inc.
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

import threading
from typing import List

from chipscopy import dm
from chipscopy.client.core_property_client import CorePropertyClient
from chipscopy.tcf import protocol
from chipscopy.tcf.services import DoneHWCommand
from chipscopy.utils.logger import get_logger

PCIE_NODE_TYPE = "cpm6_pcie_core"
PCIE_SERVICE_NAME = "PCIe"

logger = get_logger("client_pcie")


class PCIeCoreClient(CorePropertyClient):
    @staticmethod
    def is_compatible(node: dm.Node) -> bool:
        return node.type and node.type == PCIE_NODE_TYPE

    def get_service_proxy(self):
        return self.manager.channel.getRemoteService(PCIE_SERVICE_NAME)

    def initialize(self, done: DoneHWCommand = None):
        service, done_cb = self.make_done(done)
        logger.info(f"Initializing {PCIE_SERVICE_NAME} service")
        token = service.initialize(self.ctx, done_cb)
        return self.add_pending(token)

    def _send_merging_result(self, command_name, send, done, timeout_s=30):
        """Send a command and merge the property dict it returns into this node.

        When called without a *done* callback (the common case from the
        HardenedDebugPCIe wrapper) this blocks until the server responds, so a
        caller that reads properties immediately afterwards sees post-command
        values rather than the previous cache.

        When an external *done* callback is supplied the call is asynchronous
        and result handling is delegated to that callback; props are merged
        either way.

        Blocking is only safe from a thread other than the TCF dispatch thread,
        since the response callback is itself delivered on that thread. Waiting
        there would deadlock the very callback that must fire to release the
        wait, so in that case the call stays asynchronous and props are merged
        once the response arrives.
        """
        node = self
        on_dispatch_thread = protocol.isDispatchThread()
        done_event = threading.Event() if (done is None and not on_dispatch_thread) else None

        service, inner_done_cb = self.make_done(done)

        def updating_done_cb(token, error, results):
            try:
                # Go through Node.update() (not node.props.update()) so that
                # listeners/managers are notified of the changed properties.
                if not error and isinstance(results, dict):
                    node.update(results)
                inner_done_cb(token, error, results)
            finally:
                if done_event is not None:
                    done_event.set()

        token = send(service, updating_done_cb)
        self.add_pending(token)

        if done is None and on_dispatch_thread:
            logger.warning(
                f"{command_name}: called from the TCF dispatch thread for "
                f"ctx={self.ctx}; skipping synchronous wait to avoid a deadlock. "
                f"Props will be updated asynchronously once the server responds."
            )
        elif done_event is not None and not done_event.wait(timeout=timeout_s):
            logger.warning(
                f"{command_name}: cs_server did not respond within {timeout_s}s; "
                f"returning with stale/partial props for ctx={self.ctx}. The "
                f"server may be unresponsive or the request may still be pending."
            )

        return token

    def read_ltssm_trace(self, done: DoneHWCommand = None):
        """Send readLtssmTrace to cs_server and refresh cached trace props."""
        return self._send_merging_result(
            "read_ltssm_trace",
            lambda service, done_cb: service.read_ltssm_trace(self.ctx, done_cb),
            done,
        )

    def reset_core(self, done: DoneHWCommand = None):
        """Send resetCore to cs_server and refresh cached props.

        The server clears the cached state/edge/trace properties as part of the
        reset and returns the resulting property dict, so this has to merge that
        response for callers to observe the cleared values.
        """
        return self._send_merging_result(
            "reset_core",
            lambda service, done_cb: service.reset_core(self.ctx, done_cb),
            done,
        )

    def refresh_property_group(self, groups: List[str], done: DoneHWCommand = None):
        service, done_cb = self.make_done(done)
        token = service.refresh_property_group(self.ctx, groups, done_cb)
        return self.add_pending(token)
