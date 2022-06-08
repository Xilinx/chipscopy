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

import dataclasses
from dataclasses import dataclass, asdict
import json
import re
from typing import Union, List, Dict, TYPE_CHECKING
from collections import defaultdict

from chipscopy.api import CoreType
from chipscopy.api._detail.ltx import Ltx, LtxCore, LtxProbe
from chipscopy.api._detail.debug_core import DebugCore

if TYPE_CHECKING:
    from chipscopy.client.axis_vio_core_client import AxisVIOCoreClient


@dataclass
class VIOProbe:
    """VIOProbe represents a single VIO probe connected to a VIO port.
    A VIO Port may be connected to many probes. Each probe is a slice
    of the port as shown below.

    ::

                            --------
          ----------------- VIO Port ------------------------
                            --------
        msb                                                lsb
        N-1                        47          16 15        0
         -----------------------------------------------------
        | boo[]   | ... | baz[]   | bar[31:0]    | foo[15:0] |
        -----------------------------------------------------
                                   ^            ^
                                   |          port_bit_
                                   |          offset
                                   |            16
                                   |            |
                                 bus_left      bus_right
                                  _index       _index
                                  31           0

    Normally the left index is the most significant probe index, and the right
    index is the least significant. They match the HDL index of what was probed
    in the design.

    """

    probe_name: str
    """Represents the HDL net or bus name. It does not contain the brackets
    of the bus name [x:y]."""
    direction: str
    """in or out. IN is a monitor connected to something in the design. Out is
    a virtual button the VIO drives."""
    is_bus: bool
    """True if this probe is a vector, False if this probe is a scalar."""
    bus_left_index: int
    """``probe_name[bus_left_index::bus_right_index]`` - When **is_bus == True**, this is the left index of the probe.
    When **is_bus == False**, this unused."""
    bus_right_index: int
    """``probe_name[bus_left_index::bus_right_index]`` - When **is_bus == True**, this is the right index of the probe.
    When **is_bus == False**, this unused."""
    port_index: int
    """VIO port number of the input or output port."""
    port_bit_offset: int
    """Bit offset into the probe port that indicates where the probe data begins in the port."""

    def __init__(self, ltx_probe: LtxProbe):
        """Build a Probe based on the ltx probe information"""
        self.probe_name = ltx_probe.name
        self.direction = ltx_probe.direction.lower()
        self.is_bus = ltx_probe.is_bus
        self.bus_left_index = ltx_probe.bus_left_index
        self.bus_right_index = ltx_probe.bus_right_index
        self.port_index = ltx_probe.port_index
        self.port_bit_offset = 0

    def __str__(self) -> str:
        return self.probe_name

    def __repr__(self) -> str:
        return self.to_json()

    def to_dict(self) -> Dict:
        return dataclasses.asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=4)

    @property
    def port_name(self):
        """Represents the VIO port name in the IP (like probe_in0, probe_out1, etc)"""
        return f"probe_{self.direction}{self.port_index}"


class VIO(DebugCore["AxisVIOCoreClient"]):
    """This class contains the main API to use the VIO (Virtual Input/Output)
    debug core. VIO monitors elements of a running design in hardware with
    probe inputs and drives elements in the design with probe outputs.

    This API has methods for querying and controlling VIO ports directly.
    This is useful for lower level control, or direct VIO control when no LTX
    file is available.

    If an LTX file is available, the higher level read_probes and write_probes
    methods are available to debug at the higher level HDL context. HDL nets and
    bus names from Vivado are automatically converted to the correct VIO probe
    port when reading or writing.
    """

    def __init__(self, vio_tcf_node, *, ltx: Ltx = None):
        super(VIO, self).__init__(core_type=CoreType.AXIS_VIO, core_tcf_node=vio_tcf_node)

        self.name = vio_tcf_node.props["Name"]
        self.instance_name = None
        self.ltx_core = None
        self.uuid = self.core_info.uuid
        (
            self.port_in_widths,
            self.port_out_widths,
            self.has_activity,
        ) = self._read_port_info_from_hardware()
        self._setup_vio_from_ltx(ltx)

        # This is used by the filter_by method in QueryList
        self.filter_by = {"name": self.name, "uuid": self.uuid, "instance_name": self.instance_name}

    def __repr__(self) -> str:
        return self.to_json()

    def __str__(self) -> str:
        return self.name

    def to_dict(self) -> Dict:
        input_ports = {}
        for idx, val in enumerate(self.port_in_widths):
            input_ports[f"probe_in{idx}"] = val
        output_ports = {}
        for idx, val in enumerate(self.port_out_widths):
            output_ports[f"probe_out{idx}"] = val
        probes = [asdict(probe) for probe in self.probes]
        # super().to_dict() holds the standard core_info
        d = super().to_dict()
        d.update(
            {
                "name": self.name,
                "type": str(self.core_type),
                "instance": self.instance_name,
                "input_ports": input_ports,
                "output_ports": output_ports,
                "probes": probes,
            }
        )
        return d

    def to_json(self) -> str:
        return json.dumps(dict(sorted(self.to_dict().items())), indent=4, default=lambda o: str(o))

    ###########################################################################
    # VIO CORE AND PORT CONTROL
    ###########################################################################
    @property
    def is_activity_supported(self) -> bool:
        """True if this vio core supports activity detection"""
        return self.has_activity

    @property
    def port_in_count(self) -> int:
        """Number of VIO input ports in the debug core. Input ports monitor
        activity in the design.
        """
        return len(self.port_in_widths)

    @property
    def port_out_count(self) -> int:
        """Number of VIO output ports in debug core. Output ports are virtual
        buttons.
        """
        return len(self.port_out_widths)

    @property
    def port_names(self) -> List[str]:
        """List of all VIO port names (input and output) for this VIO core.

        VIO cores name ports as ``probe_in#`` for input ports, and
        ``probe_out#`` for output ports. '#' represents the port index and
        begins at 0.
        """
        port_names = []
        for idx in range(self.port_in_count):
            port_names.append(f"probe_in{idx}")
        for idx in range(self.port_out_count):
            port_names.append(f"probe_out{idx}")
        return port_names

    def reset_vio(self):
        """
        Resets the VIO core by resetting all probe outputs to their initial
        values.
        """
        self.core_tcf_node.reset_core()

    def read_ports(self, port_names: Union[str, List[str]] = None) -> Dict[str, Dict]:
        """Read VIO port values from hardware. Gets the current values from
        hardware for selected input_ports and output_ports.

        Args:
            port_names: **(optional)** List of port names (see
                ``vio_port_names``). The default is all ports.

        Returns:
            dict:
                dict: (port_name, {'value': value, 'activity': activity}).

                'value' is always returned as an integer for each port.

                'activity' is only included for vio input ports when the
                activity detection is turned on. Activity does not exist
                for vio output ports. Activity is returned as one character per
                bit of the probe. 'R', 'F', 'N', 'B' represent edges -  Rising,
                Falling, None, Both.

                port_data returned as a dictionary in the following format:

                ::

                    port_data = {
                                   probe_in0: {'value': 3, 'activity': 'RR'},
                                   ... ,
                                   probe_out0: {'value': 456},
                                   ...
                                }

        """
        # TODO: Document the order of 'activity' bits in the return string
        if isinstance(port_names, str):
            port_names = [port_names]
        if port_names is None:
            port_names = self.port_names
        port_in_data = self.core_tcf_node.refresh_port_in_data()
        port_out_data = self.core_tcf_node.refresh_port_out_data()
        port_data = {}
        for port_name in port_names:
            port_name_split = re.split("^probe_(in|out)(\\d+)$", port_name)
            assert len(port_name_split) == 4
            _, port_direction, port_index_str, _ = port_name_split  # ['', 'in|out', idx, '']
            port_index = int(port_index_str)
            if port_direction == "in":
                assert port_index < self.port_in_count
                val = port_in_data["In"][port_index]
                if "Activity" in port_in_data:
                    activity = port_in_data["Activity"][port_index]
                    port_data[port_name] = {"value": val, "activity": activity}
            elif port_direction == "out":
                assert port_index < self.port_out_count
                val = port_out_data["Out"][port_index]
                port_data[port_name] = {"value": val}
            else:
                raise ValueError(f"Invalid port name - {port_name}")
        return port_data

    def write_ports(self, port_values: Dict[str, int]):
        """Write values to VIO port outputs in hardware. Port names follow
        the VIO convention port in and port out naming.
        See ``vio_port_names``.

        Args:
            port_values: dict. key=port_name, value=port_value.
                port_name is a VIO output port. port_value is a python int
                value.

                ::

                      write_ports({'probe_out0': 1000,
                                   'probe_out1': 0x100})

        Returns:
            Nothing
        """
        assert isinstance(port_values, dict)
        port_data = {}
        for port_name, port_value in port_values.items():
            port_name_split = re.split("^probe_out(\\d+)$", port_name)
            if len(port_name_split) != 3:
                raise KeyError(f"Invalid port name {port_name}")
            _, port_index_str, _ = port_name_split  # ['', idx, '']
            port_index = int(port_index_str)
            port_data[port_index] = port_value
        assert len(port_data) > 0
        self.core_tcf_node.commit_port_out_data(port_data)

    ###########################################################################
    # VIO PROBE ACCESS
    ###########################################################################
    @property
    def probes(self) -> List[VIOProbe]:
        """
        Get probes attached to the VIO core and associated port information.

        Returns:
            List of VIOProbes
        """
        probe_list = []
        if self.ltx_core:
            ltx_probe_dict = self._get_probe_to_port_map(self.ltx_core.probes)
            for port_name, ltx_probe_list in ltx_probe_dict.items():
                for ltx_probe in ltx_probe_list:
                    probe_list.append(VIOProbe(ltx_probe))
        return probe_list

    @property
    def probe_names(self) -> List[str]:
        """
        Returns:
             List of probe names from the LTX file
        """
        probe_names = []
        if self.ltx_core:
            for probe in self.ltx_core.probes:
                probe_names.append(probe.name)
        return probe_names

    def clear_activity(self):
        """Clear any stale activity indicator data. This really just does a
        dummy read of all probes.

        Returns:
            Nothing
        """
        self.read_probes()

    def read_probe_activity(self, probe_names: List[str] or str = None) -> Dict[str, str]:
        """Read probe activity values from hardware.  Reading activity has the
        side effect of clearing activity registers in the VIO IP in hardware.

        Activity tracking is only available on input ports, and must be enabled
        when generating the VIO IP.

        Activity is returned as a string of characters representing activity
        for each bit.

        ::

            'R' = rising edge detected
            'F' = falling edge detected
            'B' = both edges detected
            'N' = no edge detected
            'X' = activity not supported on port (ex: vio output port)

        Args:
            probe_names: Optional list of probe names (see ``vio_probe_names``). Empty returns all probe activity.

        Returns:
            dict:
                dict: {probe_name: activity_string, ...}.
        """
        probe_dict = self.read_probes(probe_names)
        retval = {}
        for k, v in probe_dict.items():
            retval[k] = v["activity"]
        return retval

    def read_probe_values(self, probe_names: List[str] or str = None) -> Dict[str, int]:
        """Read probe values from hardware. Reading probes has a side effect of
        clearing activity. If you need both values and activity, call read_probes().

        Args:
            probe_names: Optional list of probe names (see ``vio_probe_names``). Empty returns all probe values.

        Returns:
            dict:
                dict: {probe_name:  value, ...}.
                'value' is always returned as an integer for each port.
        """
        probe_dict = self.read_probes(probe_names)
        retval = {}
        for k, v in probe_dict.items():
            retval[k] = v["value"]
        return retval

    def read_probes(self, probe_names: List[str] or str = None) -> Dict[str, Dict]:
        """Read probe values from hardware. Gets the current integer and activity values from
        hardware for selected probes. Output probes to not support activity and will return
        'X' for all activity values.

        Args:
            probe_names: Optional list of probe names (see ``vio_probe_names``). Empty returns all probe values.

        Returns:
            dict:
                dict: (probe_name, {'value': value, 'activity': activity}).

                'value' is always returned as an integer for each port.

                'activity' is only included for vio input probes when the
                activity detection is turned on. Activity does not exist
                for vio output probes. Activity is returned as one character per
                bit of the probe. 'R', 'F', 'N', 'B' represent edges -  Rising,
                Falling, None, Both.
                'X' returned for activity indicates it is not supported on that probe.

                ::

                    port_data = {
                                   foo_probe: {'value': 3, 'activity': 'RR'},
                                   ... ,
                                   bar_probe: {'value': 456},
                                   ...
                                }
        """
        self.core_tcf_node.refresh_probe()
        report_results: Dict = self.core_tcf_node.report_probe()
        retval: Dict = {}
        if isinstance(probe_names, str):
            probe_names = [probe_names]
        elif probe_names is None:
            # None defaults to all probes
            probe_names = report_results.keys()
        for probe_name in probe_names:
            probe_value = report_results[probe_name]["value"]
            probe_activity = report_results[probe_name]["activity"]
            retval[probe_name] = {"value": probe_value, "activity": probe_activity}
        return retval

    def write_probes(self, probe_values: Dict[str, int] = None):
        """Write values to VIO probe outputs in hardware. See
        ``vio_probe_names``.

        Args:
            probe_values: dict. key=probe_name, value=probe_value.
                probe_name is a VIO output probe. probe_value is a python int
                value.

                ::

                      write_probes({'foo': 1000,
                                    'bar': 0x100})

        Returns:
            Nothing
        """
        assert isinstance(probe_values, dict)
        self.core_tcf_node.commit_probe(probe_values)

    def _read_port_info_from_hardware(self):
        ports_info_dict = self.core_tcf_node.get_ports_info()
        port_in_widths: List[int] = []
        port_in_count = ports_info_dict["port_in_count"]
        if port_in_count > 0:
            port_in_widths = ports_info_dict["port_in_widths"]
        port_out_widths: List[int] = []
        port_out_count = ports_info_dict["port_out_count"]
        if port_out_count > 0:
            port_out_widths = ports_info_dict["port_out_widths"]
        has_activity: bool = ports_info_dict["has_activity_detector"]
        return port_in_widths, port_out_widths, has_activity

    @staticmethod
    def _get_probe_to_port_map(ltx_probes: List[LtxProbe]) -> Dict[str, List[LtxProbe]]:
        # Build the probe to port mapping. Associates the logical
        # LTX port data to the physical VIO hardware port configuration.
        # Group probes by port index and order probes from smallest to largest
        # offset { port_index : [probe, ..., probe] ... }
        # There may be multiple logical probes for each physical port.

        probes_by_port = defaultdict(list)
        for ltx_probe in ltx_probes:
            # TODO: Need to handle probe slices... That means sort by bit index
            #       and handle multiple probes for a single port
            direction = ltx_probe.direction.lower()
            port_key = f"probe_{direction}{ltx_probe.port_index}"
            probes_by_port[port_key].append(ltx_probe)
        return probes_by_port

    def _create_probes(self, probe_to_port_map: Dict[str, List[LtxProbe]]):
        for port_index in sorted(probe_to_port_map.keys()):
            probes_for_port = probe_to_port_map[port_index]
            for ltx_probe in probes_for_port:
                probe = VIOProbe(ltx_probe)
                # print("_create_probes - CREATED PROBE: ", probe)
                port_name = f"{probe.direction}{probe.port_index}"
                probe_to_create = {
                    "name": probe.probe_name,
                    "net": probe.probe_name,
                    "map": port_name,
                }
                self.core_tcf_node.define_probe([probe_to_create])

    def _setup_vio_from_ltx(self, ltx: Ltx):
        # Clear out any old LTX leftovers
        self.instance_name = None
        self.core_tcf_node.undefine_probe(probe_name="All")
        self.ltx_core = None
        if ltx:
            ltx_core: LtxCore = ltx.get_core(core_type=self.core_type, uuid=self.uuid)
            self.ltx_core = ltx_core
            assert ltx_core is not None
            self.instance_name = ltx_core.cell_name
            self.name = ltx_core.cell_name
            probe_to_port_map = self._get_probe_to_port_map(ltx_core.probes)
            self._create_probes(probe_to_port_map)
