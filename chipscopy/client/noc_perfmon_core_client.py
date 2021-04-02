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

from typing import List

from chipscopy import dm
from chipscopy.client.core import CoreClient
from chipscopy.dm.harden.noc_perfmon.traffic_classes import PerfMonTrafficQOSClass
from chipscopy.tcf.services import DoneHWCommand
from chipscopy.proxies.NoCPerfMonProxy import NOC_PERFMON_SERVICE_NAME


class NoCPerfMonCoreClient(CoreClient):
    @staticmethod
    def is_compatible(node: dm.Node) -> bool:
        return node.type and node.type == "npi_nir"

    def get_service_proxy(self):
        return self.manager.channel.getRemoteService(NOC_PERFMON_SERVICE_NAME)

    def refresh_property_group(self, groups: List[str], done: DoneHWCommand = None) -> List[str]:
        """

        Args:
            groups (List[str]): list of property group names. For NoC PerfMon the groups are ``control``, ``status``,
                and ``perfmon``.
            done: Optional command callback that will be invoked when the response is received.

        Returns:
            Property name/value pairs from the requested group(s).

        """
        service, done_cb = self.make_done(done)
        token = service.refresh_property_group(self.ctx, groups, done_cb)
        return self.add_pending(token)

    def initialize(self, done: DoneHWCommand = None):
        """
        This method collects the clocking information for client use later in the configuration of this service. It
        also refreshes the client's view of specific properties for the root node *ONLY*.

        This call must be invoked before clocking information is requested from the device

        Args:
            done: Optional command callback that will be invoked when the response is received.

        Returns:
            No data is returned directly from this method.

        """
        service, done_cb = self.make_done(done)
        return self.add_pending(service.initialize(self.ctx, done_cb))

    #
    # discover the NoC elements in the device
    #
    def discover_noc_elements(self, done: DoneHWCommand = None) -> List[str]:
        """
        This method dynamically scans the NoC to determine the active nodes in the programmed design. If no
        nodes are programmed or the NPI domain is inaccessible this will return an empty list.

        This list will serve as the set from which elements may be chosen for runtime performance analysis.

        Unrouted, disabled NoC elements cannot be configured for measurement. It may be assumed their counters would
        always produce zero count values.

        Args:
            done: Optional command callback that will be invoked when the response is received.

        Returns:
            Returns a list of active NMU, NSU/DDRMC_NOC, and NPS elements. Unrouted, disabled elements are not returned
            and cannot be monitored.

        """
        service, done_cb = self.make_done(done)
        return self.add_pending(service.discover_noc_elements(self.ctx, done_cb))

    def configure_monitors(
        self,
        monitors: {str},
        sampling_intervals: {dict},
        traffic_class: PerfMonTrafficQOSClass,
        sample_count: int,
        done: DoneHWCommand = None,
        extended_monitor_config: dict = None,
    ):

        """
        This method configures and enables the performance monitoring on the parameter set of elements. Upon completion
        of the configuration, data will start to be emitted asynchronously from ChipScope Server back to the requesting
        client. The client must implement an Event Listener to properly receive the data.

        Each element will be configured to monitor both read and write traffic independently. QOS classes of a
        particular direction of traffic will be applied to the monitor responsible for that type of traffic
        ``read|write``.

        Args:
            monitors (set[str]):
                Set of NoC elements to enable to stream performance data.
                For Example -
                ``('NOC_NMU128_X0Y0', 'DDRMC_X0Y0', 'NOC_NPS5555_X11Y2')``
            sampling_intervals (dict):
                The requested ``period_ms`` for sampling. The client must ensure this is a supported period.
                **NOTE**: this structure needs to contain information for NPI, NoC and each DDRMC controller clk
                NPI, NoC are sampling periods (ms) (floats) and DDRMC controller clk domain is a tap (int)
                -- for reference see the XSA class in the utilities to understand how the ctrl clk works.
            traffic_class (PerfMonTrafficQOSClass):
                The traffic classes bitwise-or'd that shall be monitored.
            sample_count (int):
                *OPTIONAL* The number of intervals or windows to capture. 1 - will configure supporting hardware for
                single shot. 2-int_max will configure all hardware for continuous mode and will stop streaming data when
                the requested number of samples have been sent to the client. -1 is the default and means the streaming
                will run indefinitely.
            filter_spec (dict[int]):
                Will move! hold off on using this for now.
                *OPTIONAL* Dictionary defining the AXI filtering to use. If this parameter is not supplied then no
                filtering will occur and all transactions will be counted by the samplers. No validation is done on
                these fields, they will be masked and shifted, as they are received. For convenience any fields not
                specified will retain the default value of zero, except max fields (AxSIZE, AxQoS, AxLEN) which have the
                largest supported values). The supported fields include

                ``AxPROT[3]``, ``AxBURST[2]``, ``AxSIZE_MIN[3]``, ``AxLEN_MIN[8]``, ``AxID[16]``
                ``TDEST[10]`` (AXIS only), ``DST_ID[12]``, ``AxLOCK[1]``, ``AxQoS_MIN[4]``, ``AxCACHE[4]``,
                ``AxSIZE_MAX[3]``, ``AxQoS_MAX[4]``, ``AxLEN_MAX[8]``

            done:
                Optional command callback that will be invoked when the response is received.

        Returns:
            No data is returned from this call.

        """
        params = {
            "node_id": self.ctx,
            "monitors": monitors,
            "intervals": sampling_intervals,
            "traffic_class": traffic_class,
            "sample_count": sample_count,
            "extended_monitor_config": extended_monitor_config,
        }
        service, done_cb = self.make_done(done)
        return self.add_pending(service.configure_monitors(params, done_cb))

    def get_supported_sampling_periods(
        self,
        ref_clk_freq_mhz: float = None,
        pl_alt_ref_clk_freq_mhz: float = None,
        ddrmc_freq_mhz: dict = {},
        done: DoneHWCommand = None,
    ) -> dict:
        """

        Args:
            done: Optional command callback that will be invoked when the response is received.

        Returns:
            Dictionary with two top level keys ``NoC`` and ``NPI`` whose values are lists of supported sampling
            periods measured in milliseconds (float).
            :param ddrmc_freq_mhz:
            :param done:
            :param pl_alt_ref_clk_freq_mhz:
            :param ref_clk_freq_mhz:


        """
        params = {"node_id": self.ctx}
        if ref_clk_freq_mhz is not None:
            params.update({"ref_clk_freq_mhz": ref_clk_freq_mhz})
        if pl_alt_ref_clk_freq_mhz is not None:
            params.update({"pl_alt_ref_clk_freq_mhz": pl_alt_ref_clk_freq_mhz})
        params.update(ddrmc_freq_mhz)
        service, done_cb = self.make_done(done)
        return self.add_pending(service.get_supported_sampling_periods(params, done_cb))

    def get_clk_info(self, done: DoneHWCommand = None) -> dict:
        """
        Reports NPI and NoC clock information from the running design. These are parameters set by the designer in
        Vivado.

        Args:
            done: Optional command callback that will be invoked when the response is received.

        Returns:
            A dictionary with two top level keys ``NoC`` and ``NPI`` whose values are dictionaries that
            detail the ``freq_mhz``, frequency in MHz (float) and the ``period_ms``, period in milliseconds (float).

        """
        service, done_cb = self.make_done(done)
        return self.add_pending(service.get_clk_info(self.ctx, done_cb))

    def enumerate_noc_elements(self, nodes, done: DoneHWCommand = None) -> List[str]:
        params = {
            "node_id": self.ctx,
            "scan_nodes": nodes,
        }
        service, done_cb = self.make_done(done)
        return self.add_pending(service.enumerate_noc_elements(params, done_cb))
