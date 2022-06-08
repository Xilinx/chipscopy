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

from typing import List, Set, Dict
from dataclasses import dataclass

from chipscopy.api import CoreType
from chipscopy.api._detail.debug_core import DebugCore

# TODO: PerfMonTrafficQOSClass should have an alias on the top level
from chipscopy.dm.harden.noc_perfmon.traffic_classes import PerfMonTrafficQOSClass
from chipscopy.tcf.services import DoneHWCommand
from chipscopy.client.noc_perfmon_core_client import NoCPerfMonCoreClient
from chipscopy.utils import printer


@dataclass
class NocPerfmon(DebugCore["NoCPerfMonCoreClient"]):
    """NocPerfMon is the top level API for accessing NocPerfmon.
    It wraps the old client noc_perfmon_core_client.NoCPerfMonCoreClient(CoreClient) class
    and simplifies the use model by hiding tcf and node lower level details.
    """

    def __init__(self, noc_tcf_node):
        super(NocPerfmon, self).__init__(CoreType.NOC_ROOT, noc_tcf_node)

        self.name = noc_tcf_node.props["Name"]

        # This is used by the filter_by method in QueryList
        self.filter_by = {"name": self.name}

    def __str__(self):
        return self.name

    def initialize(self, done: DoneHWCommand = None):  # pragma: no cover
        """
        This method collects the clocking information for client use later in the configuration of this service. It
        also refreshes the client's view of specific properties for the root node *ONLY*.

        This call must be invoked before clocking information is requested from the device

        Args:
            done: Optional command callback that will be invoked when the response is received.

        Returns:
            No data is returned directly from this method.

        """
        self.core_tcf_node.initialize(done)

    def discover_noc_elements(self, done: DoneHWCommand = None) -> List[str]:
        """

        WARNING - This function is deprecated and will be removed in the future

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
        element_list = self.core_tcf_node.discover_noc_elements(done)
        return element_list

    def configure_monitors(
        self,
        monitors: Set[str],
        sampling_intervals: dict,
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
            monitors (List[str]):
                List of NoC elements to enable to stream performance data.
                For Example -
                ``['NOC_NMU128_X0Y0', 'DDRMC_X0Y0', ...]``
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

            extended_monitor_config:
                Optional argument that is a dictionary of additional monitor configuration. The keys must correspond to
                the monitors. "tslide" is the only supported key at this time. Tslide will change the meaning of the
                latency counters for the specified monitor (read and write channel). The meaning of the counter values
                can be represented by 2^(tslide) clocks. Default tslide is 0, corresponding to 1 clock per count. In
                practice this is a tradeoff between precision and range. When the counters overflow error flags will be
                set in the associated metrics. If overflow is observed, the tslide should be increased to avoid that
                condition. Otherwise there will be a "clipping" in the data. Note, only NMU and NSU's support the tslide
                extended configuraiton option. DDRMC does not, and will ignore the value, if supplied by the client.

        Returns:
            No data is returned from this call.

        """
        self.core_tcf_node.configure_monitors(
            monitors=monitors,
            sampling_intervals=sampling_intervals,
            traffic_class=traffic_class,
            sample_count=sample_count,
            done=done,
            extended_monitor_config=extended_monitor_config,
        )

    def get_supported_sampling_periods(
        self,
        ref_clk_feq_mhz=33.3333,
        pl_alt_ref_clk_freq_mhz=33.3333,
        ddrmc_freq_mhz={"ddrmc_main_0": 800.0},
        done: DoneHWCommand = None,
    ) -> Dict[str, List[float]]:
        """
        Get the supported sampling periods (ms) for various clock domains based on input clocks and design parameters.
        This function queries the PLLs of the device to determine actual clock speeds of locked PLLs.

        Args:
            done: Optional command callback that will be invoked when the response is received.
            ddrmc_freq_mhz (dict[str,float]): dictionary of DDRMC instance names as the keys and the value is the MC clock in MHz float.
            ref_clk_feq_mhz (float): ref_clk input frequency in MHz, value can be attained from .csa or .hwh files. Default is 33.333MHz
            pl_alt_ref_clk_freq_mhz (float): pl_alt_ref_clk input frequency in MHz, value can be attained from .csa or .hwh files. Default is 33.333MHz

        Returns:
            Dictionary with two top level keys ``NoC``, ``NPI``, and memory subsystem components whose values are lists
            of supported sampling periods measured in milliseconds (float).

        """
        sampling_dict = self.core_tcf_node.get_supported_sampling_periods(
            ref_clk_feq_mhz, pl_alt_ref_clk_freq_mhz, ddrmc_freq_mhz, done
        )
        return sampling_dict

    def get_clk_info(self, done: DoneHWCommand = None) -> dict:  # pragma: no cover
        """
        DEPRECATED will remove in 2022.1

        Reports NPI and NoC clock information from the running design. These are parameters set by the designer in
        Vivado.

        Args:
            done: Optional command callback that will be invoked when the response is received.

        Returns:
            A dictionary with two top level keys ``NoC`` and ``NPI`` whose values are dictionaries that
            detail the ``freq_mhz``, frequency in MHz (float) and the ``period_ms``, period in milliseconds (float).

        """
        frequency_dict = self.core_tcf_node.get_clk_info(done)
        return frequency_dict

    def enumerate_noc_elements(
        self, scan_nodes, done: DoneHWCommand = None, raw_mode=False
    ) -> List[str]:
        results = self.core_tcf_node.enumerate_noc_elements(scan_nodes, done)
        disabled = results["disabled"]
        invalid = results["invalid"]
        if len(disabled) != 0:
            printer(
                "Warning: These nodes were requested but are disabled in the hardware, verify the design:"
            )
            for d in disabled:
                printer(f"  {d}")
        if len(invalid) != 0:
            printer(
                "Warning: These nodes were requested but are not valid for "
                "this hardware, double check the device and the site names in "
                "the design:"
            )
            for i in invalid:
                printer(f"  {i}")
        if raw_mode:
            return results
        else:
            return results["enabled"]
