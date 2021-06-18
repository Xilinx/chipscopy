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

import typing
from chipscopy.utils.logger import log
from chipscopy import dm
from chipscopy.client import core_property_client
from chipscopy.tcf.services import DoneHWCommand
from chipscopy.proxies.AxisVIOProxy import AXIS_VIO_SERVICE_NAME, AXIS_VIO_NODE_NAME

# NOTE: PLEASE USE THIS DOMAIN NAME IN ALL LOG MESSAGES FROM THIS FILE.
DOMAIN_NAME = "client_axis_vio"


class AxisVIOCoreClient(core_property_client.CorePropertyClient):
    # ===========================================
    # Abstract methods redefined here
    # ===========================================
    def get_service_proxy(self):
        return self.manager.channel.getRemoteService(AXIS_VIO_SERVICE_NAME)

    # ===========================================
    # Static methods defined here
    # ===========================================
    @staticmethod
    def is_compatible(node: dm.Node) -> bool:
        return_val = node.type and node.type == AXIS_VIO_NODE_NAME
        return return_val

    def initialize(self, done: DoneHWCommand = None):
        service, done_cb = self.make_done(done)
        log[DOMAIN_NAME].info(f"Initializing {AXIS_VIO_SERVICE_NAME} service")
        token = service.initialize(self.ctx, done_cb)
        return self.add_pending(token)

    # ===========================================
    # Core control
    # ===========================================

    def reset_core(self, done: DoneHWCommand = None):
        """
        Resets the VIO core and sets the probe out(s) to their initial value.

        Args:
            done: **(Optional)** If callback is desired once operation is complete,
                then function/method should be provided.
        """
        service, done_cb = self.make_done(done)
        log[DOMAIN_NAME].info(f"Initiating AXIS VIO core reset")
        options = {"node_id": self.ctx}
        token = service.reset_core(options, done_cb)
        return self.add_pending(token)

    def get_core_info(self, done: DoneHWCommand = None):
        """
        Gets the core information properties associated with the VIO.

        Args:
            done: **(Optional)** If callback is desired once operation is complete,
                then function/method should be provided.

        Returns:
            dict:
                (Key, Value) - (Property name, Property value).
                Shown below are the keys that will be present in the return data along with
                example values

                ::

                    {
                     'core_type': 2, # int
                     'drv_ver': 0, # int
                     'tool_major_ver': 19, # int
                     'tool_minor_ver': 1, # int
                     'core_major_ver': 1, # int
                     'core_minor_ver': 0, # int
                     'uuid': "53E5F1C310B952D3BB10986C3375587A", # str
                    }

        """
        service, done_cb = self.make_done(done)
        log[DOMAIN_NAME].info(f"Initiating core info fetch")
        token = service.get_property_group(self.ctx, "core_info", done_cb)
        return self.add_pending(token)

    def get_ports_info(self, done: DoneHWCommand = None):
        """
        Gets static information like port counts, associated with the VIO core.

        Args:
            done: **(Optional)** If callback is desired once operation is complete,
                then function/method should be provided.

        Returns:
            dict:
                (Key, Value) - (Property name, Property value).
                Shown below are the keys that will be present in the return data along with
                example values

                ::

                    {
                        'port_in_count': 2, # int
                        'port_out_count': 3, # int

                         # Value at index 'X' is the width of port_in'X'
                         'port_in': [32, 64],

                         # Value at index 'X' is the width of port_out'X'
                         'port_out': [32, 64, 128]
                    }

        """
        service, done_cb = self.make_done(done)
        log[DOMAIN_NAME].info(f"Initiating ports info fetch")
        token = service.get_property_group(self.ctx, "static_info", done_cb)
        return self.add_pending(token)

    def get_control_signals(self, done: DoneHWCommand = None):
        """
        Gets the value of the control signals.

        Args:
            done: **(Optional)** If callback is desired once operation is complete,
                then function/method should be provided.

        Returns:
            dict(str, bool):
                (Key, Value) - (Property name, Property value).
                Shown below are signals in the control group and example values for them.

                ::

                    {
                     'reset': False,
                     'commit': False,
                    }

        """
        service, done_cb = self.make_done(done)
        log[DOMAIN_NAME].info(f"Initiating control signal fetch")
        token = service.get_property_group(self.ctx, "control", done_cb)
        return self.add_pending(token)

    # ===========================================
    # Port related
    # ===========================================

    def commit_port_out_data(
        self, port_data: typing.Dict[int, typing.Union[str, int]], done: DoneHWCommand = None
    ):
        """
        Commit new value to port out(s).

        Args:
            port_data (dict): (Key, Value) - (Port out number, new data for the port).
                Default input format for port data is :class:`int`. However, data can be
                provided as **binary**, **hex** or **octal** using the prefixes
                ``0b``, ``0x`` and ``0o`` before the data.
                For example, to write a value of ``0x1122334455`` to 32-bit wide port out's,
                the arguments to the function can be

                ::

                    commit_port_out_data({
                                            0: 0x11223344,

                                            # Int equivalent of 0x11223344
                                            1: 287454020,

                                            # Binary equivalent of 0x11223344
                                            2: 0b10001001000100011001101000100,

                                            # Octal equivalent of 0x11223344
                                            3: 0o2110431504
                                        })

            done: **(Optional)** If callback is desired once operation is complete,
                then function/method should be provided.

        Returns:
            bool:
                ``True`` if data was written to the core, ``False`` otherwise

        """
        service, done_cb = self.make_done(done)
        log[DOMAIN_NAME].info(f"Initiating port out commit")
        options = {"port_data": port_data}
        token = service.commit_port_out_data(self.ctx, options, done_cb)
        return self.add_pending(token)

    def refresh_port_in_data(self, done: DoneHWCommand = None):
        """
        Refresh port in(s) and activity(if available) in the core object
        with value(s) from the core.

        Args:
            done: **(Optional)** If callback is desired once operation is complete,
                then function/method should be provided.

        Returns:
            dict(str, list(int)):
                (Key, Value) - (Port type, Value for all available ports).
                For example, if the VIO design has 1 x Port in with activity,
                the return data would be

                ::

                    {
                     'In': [15],
                     'Activity': ['UDNB']
                    }

                     Interpreting activity
                     ---------------------
                     "B" signifies 1 to 0 + 0 to 1 transition for the bit
                     "R" signifies 0 to 1 transition for the bit
                     "F" signifies 1 to 0 transition for the bit
                     "N" signifies no change


                In this example, the value of ``Port in 0`` is the value at
                index ``0`` for key ``In``.

        """
        service, done_cb = self.make_done(done)
        log[DOMAIN_NAME].info(f"Initiating port in refresh")

        options = {"node_id": self.ctx}
        token = service.refresh_port_in_data(options, done_cb)
        return self.add_pending(token)

    def refresh_port_out_data(
        self, port_out_numbers: typing.Union[typing.List[int], int] = "", done: DoneHWCommand = None
    ):
        """
        Refresh port out(s) in the core object with value(s) from the core.

        Args:
            port_out_numbers (int, list(int)): The port out numbers

            done: **(Optional)** If callback is desired once operation is complete,
                then function/method should be provided.

        Returns:
            dict(str, list(int)):
                (Key, Value) - (Port type, Value for all available ports).
                For example, if the VIO design has 2 x Port out's, the return data would be

                ::

                    # If command was vio.refresh_port_out_data()
                    # or vio.refresh_port_out_data([0, 1])
                    {
                     'Out': [15, 16],
                    }

                    # If command was vio.refresh_port_out_data(1)
                    {
                     'Out': [None, 16],
                    }

                    # If command was vio.refresh_port_out_data(0)
                    {
                     'Out': [15, None],
                    }

                     Interpreting activity
                     ---------------------
                     "B" signifies 1 to 0 + 0 to 1 transition for the bit
                     "R" signifies 0 to 1 transition for the bit
                     "F" signifies 1 to 0 transition for the bit
                     "N" signifies no change


                In this example, the value of ``Port out 0`` is the value at
                index ``0`` for key ``Out``.

        """
        service, done_cb = self.make_done(done)
        log[DOMAIN_NAME].info(f"Initiating port out commit")

        options = {"node_id": self.ctx, "port_out_numbers": port_out_numbers}
        token = service.refresh_port_out_data(options, done_cb)
        return self.add_pending(token)

    def get_port_data(self, done: DoneHWCommand = None):
        """
        Get current port value from the VIO properties.

        Args:
            done: **(Optional)** If callback is desired once operation is complete,
                then function/method should be provided.

        Returns:
            dict(str, list(int)):
                (Key, Value) - (Port type, Value for all available ports).
                For example, if the VIO design has 1 x Port in with activity and
                2 x Port out, the return data would be

                ::

                    {
                     'In': [15],
                     'Out': [287454020, 1432778632],
                     'Activity': ['UDNB']
                    }

                     Interpreting activity
                     ---------------------
                     "B" signifies 1 to 0 + 0 to 1 transition for the bit
                     "R" signifies 0 to 1 transition for the bit
                     "F" signifies 1 to 0 transition for the bit
                     "N" signifies no change


                In this example, the value of ``Port out 1`` is the value at
                index ``1`` for key ``Out``.

        """
        service, done_cb = self.make_done(done)
        log[DOMAIN_NAME].info(f"Initiating port data fetch")
        options = {"node_id": self.ctx}
        token = service.get_port_data(options, done_cb)
        return self.add_pending(token)

    # ===========================================
    # Probe related
    # ===========================================

    def define_probe(
        self,
        probe_options: typing.Union[typing.Dict[str, str], typing.List[typing.Dict[str, str]]],
        done: DoneHWCommand = None,
    ):
        """
        Create a new probe.

        Args:
            probe_options (list(dict(str, str))):

                Its recommended to create a batch of probes. However, in case only one probe
                needs to be created, the probe_options can be provided as a ``dict(str, str]``.

                Each of the probe options need to have the following keys in the dictionary

                - ``name`` - Name of the new probe; This has to be **unique** for every probe
                - ``net`` - Name of the net the probe is mapped to
                - ``map`` - A white space separated list of port slices and constants in any order


                Following types of probes are currently supported

                    - Constant only
                    - Port in(s)
                    - Port in(s) + constant
                    - Port out(s)

                The below snippet, illustrates options supported by ``map``

                ::

                    "0101_1101"
                        Specifies a binary constant value. '_' may be used in between the constant
                        for readability purposes.

                    "port_out0[31:0]"
                        Specifies a 32-bit slice of a port. In the slice X:Y, X can be > or < Y.

                    "port_in0"
                        No explicit range means all bits of the physical port.
                        "port_in0" means same as "port_in0[31:0]", if the port is 32 bits wide.

                    "port_out0[4]"
                        Shorter notation for "port_out0[4:4]"

                    "0101 port_in0[31:0] 1101"
                        Specifies a constant and port slice. The constants need not be at the
                        beginning or end of the map.


            done: **(Optional)** If callback is desired once operation is complete,
                then function/method should be provided.

        """
        service, done_cb = self.make_done(done)
        log[DOMAIN_NAME].info("Initiating probe creation")
        options = {"node_id": self.ctx, "probe_options": probe_options}
        token = service.define_probe(options, done_cb)
        return self.add_pending(token)

    def report_probe(self, probe_name: str = "", done: DoneHWCommand = None):
        """
        Report information for given probe name.

        Args:
            probe_name (str): (**Optional**) Name of the probe.
                If not provided, information about all available probe(s) is returned.

            done: **(Optional)** If callback is desired once operation is complete,
                then function/method should be provided.

        Returns:
            dict(str, dict):
                (Key, Value) - (Probe name, probe information).
                The probe information dictionary has the following keys

                ::

                    {
                     'name': 'probeA',

                     'category': 'Out',

                     'net': 'dummy',

                     # Entry at index 'X', specifies the mapping for bit 'X' of the probe
                     'bits': ['port_out0_data[0]',
                              'port_out0_data[1]',
                              'port_out1_data[30]',
                              'port_out1_data[31]'],

                     # Bit length of the probe
                     'length': 4,

                     # If the probe has constants, this is True
                     'has_constants': False,

                     # The ports that have at least a bit mapped to the probe
                     'ports_part_of_probe': ['port_out0_data', 'port_out1_data'],

                     # Current value of probe as int
                     'value': 12,

                     # False if this probe is read only, True otherwise
                     'is_write_allowed': True
                    }

        """
        service, done_cb = self.make_done(done)
        log[DOMAIN_NAME].info("Initiating probe info fetch")
        options = {"node_id": self.ctx, "probe_name": probe_name}
        token = service.report_probe(options, done_cb)
        return self.add_pending(token)

    def undefine_probe(
        self, probe_name: typing.Union[typing.List[str], str] = "All", done: DoneHWCommand = None
    ):
        """
        Remove a previously defined probe.

        Args:
            probe_name (list(str]): (**Optional**) Name of the probe as a :obj:`list` of :obj:`str`.
                 If removing a single probe, then the probe name can be provided as an :obj:`str`.
                 If not provided, all available probes are deleted.

            done: **(Optional)** If callback is desired once operation is complete,
                then function/method should be provided.

        """
        service, done_cb = self.make_done(done)
        log[DOMAIN_NAME].info("Initiating probe removal destruction")
        options = {"node_id": self.ctx, "probe_name": probe_name}
        token = service.undefine_probe(options, done_cb)
        return self.add_pending(token)

    def refresh_probe(self, probe_name: str = "All", done: DoneHWCommand = None):
        """
        Refresh the value of the probe.

        Note:
            Refresh probe also refreshes the values of the ports.

        Args:
            probe_name (str): (**Optional**) Name of the probe.
                If not provided, all probes are refreshed.

            done: **(Optional)** If callback is desired once operation is complete,
                then function/method should be provided.

        """
        service, done_cb = self.make_done(done)
        log[DOMAIN_NAME].info("Initiating probe refresh")
        options = {"node_id": self.ctx, "probe_name": probe_name}
        token = service.refresh_probe(options, done_cb)
        return self.add_pending(token)

    def commit_probe(self, probe_options: typing.Dict[str, str], done: DoneHWCommand = None):
        """
        Commit new value to supported probe(s).

        Note:
            Currently commit is supported only for probe category of "Out" i.e.
            probe that has only port outs mapped to the probe bits.

        Args:
            probe_options (dict(str, str)): (Key, Value) - (Probe name, new value)
                Default input format for port data is :class:`int`. However, data can be
                provided as **binary**, **hex** or **octal** using the prefixes
                ``0b``, ``0x`` and ``0o`` before the data.

                For example, to write a value of ``0x1122334455`` to 32-bit wide probes,
                the arguments to the function can be

                ::

                    commit_probe({
                                    'probeA': 0x11223344,

                                    # Int equivalent of 0x11223344
                                    'probeB': 287454020,

                                    # Binary equivalent of 0x11223344
                                    'probeC': 0b10001001000100011001101000100,

                                    # Octal equivalent of 0x11223344
                                    'probeD': 0o2110431504,
                                 })

            done: **(Optional)** If callback is desired once operation is complete,
                then function/method should be provided.

        """
        service, done_cb = self.make_done(done)
        log[DOMAIN_NAME].info("Initiating probe addition")
        options = {"node_id": self.ctx, "probe_data": probe_options}
        token = service.commit_probe(options, done_cb)
        return self.add_pending(token)
