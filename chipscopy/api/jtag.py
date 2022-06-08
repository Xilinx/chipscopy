# Copyright 2022 Xilinx, Inc.
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
import sys
from collections import namedtuple
from typing import List
from chipscopy.client.jtagdevice import JtagNode
from enum import Enum

JtagPadding = namedtuple("JtagPadding", ["size", "value"])


class JtagState(Enum):
    RESET = "RESET"
    IDLE = "IDLE"
    DRSELECT = "DRSELECT"
    DRCAPTURE = "DRCAPTURE"
    DRSHIFT = "DRSHIFT"
    DREXIT1 = "DREXIT1"
    DRPAUSE = "DRPAUSE"
    DREXIT2 = "DREXIT2"
    DRUPDATE = "DRUPDATE"
    IRSELECT = "IRSELECT"
    IRCAPTURE = "IRCAPTURE"
    IRSHIFT = "IRSHIFT"
    IREXIT1 = "IREXIT1"
    IRPAUSE = "IRPAUSE"
    IREXIT2 = "IREXIT2"
    IRUPDATE = "IRUPDATE"


class JtagSequence:
    _jtag_node: JtagNode = None
    _commands: list = None
    _data: bytes = None
    _ir_prefix = JtagPadding(size=0, value=0)
    _ir_postfix = JtagPadding(size=0, value=0)
    _dr_prefix = JtagPadding(size=0, value=0)
    _dr_postfix = JtagPadding(size=0, value=0)

    def __init__(self, jtag_node: JtagNode):
        self._jtag_node = jtag_node
        self._commands = list()
        self._data = bytearray()

    def __str__(self):
        return "Sequence commands = " + str(self._commands) + "\n" + "Data = " + str(self._data)

    def __repr__(self):
        return "Sequence commands = " + str(self._commands) + "\n" + "Data = " + str(self._data)

    def clear(self):
        """Remove all commands from JTAG sequence

        Args:
            None
        """
        self._commands.clear()
        self._data = bytearray()

    def set_ir_prefix(self, *, size: int, value: int):
        self._ir_prefix = JtagPadding(size=size, value=value)

    def set_ir_postfix(self, *, size: int, value: int):
        self._ir_postfix = JtagPadding(size=size, value=value)

    def set_dr_prefix(self, *, size: int, value: int):
        self._dr_prefix = JtagPadding(size=size, value=value)

    def set_dr_postfix(self, *, size: int, value: int):
        self._dr_postfix = JtagPadding(size=size, value=value)

    def shift(
        self,
        *,
        shift_type: str = "dr",
        data: int or bytearray = None,
        tdi: int = None,
        size,
        capture: bool = True,
        end_state: JtagState = JtagState.RESET,
    ):
        """Add JTAG sequence command to shift data in IR/DR SHIFT state

        Args:
            shift_type: JTAG state in which data to shift. Valid options: "dr" or "ir"
            data: Integer or bytearray data to shift
            tdi: TDI value to use for all clocks in shift state
            size: Size of data to be shifted in bits
            capture: Capture TDO data during shift and return from sequence run command
            end_state: JTAG state to enter after shift is complete. The default is RESET.

        TODO: Mask and compare options
        """

        # Check arguments
        if data is not None and tdi is not None:
            raise ValueError("Cannot use data and tdi shift arguments simultaneously.")

        if shift_type != "dr" and shift_type != "ir":
            raise ValueError('Valid shift_type values are "ir" and "dr".')

        # Create list with shift command arguments
        shift_command = ["shift", shift_type[0], capture, size]

        shift_options = dict()
        if end_state is not None:
            shift_options["state"] = end_state.name

        if data is not None:
            if isinstance(data, (bytes, bytearray)) is True:
                # Append data to object's member variable. Size should be ceil of size in bits / 8.
                self._data += data[: -(size // -8)]
            else:
                # If data is not in bytearray format convert it to bytes and append to object's member variable
                truncated_data = data & ((1 << size) - 1)
                self._data += truncated_data.to_bytes(-(size // -8), sys.byteorder)
        else:
            shift_options["value"] = tdi

        shift_command.append(shift_options)

        # Add command to list of commands
        self._commands.append(shift_command)

    def ir_shift(
        self,
        *,
        data=None,
        tdi: int = None,
        size,
        capture: bool = True,
        end_state: JtagState = JtagState.RESET,
    ):
        """Add JTAG sequence command to shift data in IR SHIFT state

        Args:
            data: Integer or bytearray data to shift
            tdi: TDI value to use for all clocks in shift state
            size: Size of data to be shifted in bits
            capture: Capture TDO data during shift and return from sequence run command
            end_state: JTAG state to enter after shift is complete. The default is RESET.
        """
        if self._ir_prefix.size != 0:
            self.shift(
                shift_type="ir",
                data=self._ir_prefix.value,
                size=self._ir_prefix.size,
                capture=False,
                end_state=JtagState.IRSHIFT,
            )

        self.shift(
            shift_type="ir",
            data=data,
            tdi=tdi,
            size=size,
            capture=capture,
            end_state=JtagState.IRSHIFT if self._ir_postfix.size != 0 else end_state,
        )

        if self._ir_postfix.size != 0:
            self.shift(
                shift_type="ir",
                data=self._ir_postfix.value,
                size=self._ir_postfix.size,
                capture=False,
                end_state=end_state,
            )

    def dr_shift(
        self,
        *,
        data=None,
        tdi: int = None,
        size,
        capture: bool = True,
        end_state: JtagState = JtagState.RESET,
    ):
        """Add JTAG sequence command to shift data in DR SHIFT state

        Args:
            data: Integer or bytearray data to shift
            tdi: TDI value to use for all clocks in shift state
            size: Size of data to be shifted in bits
            capture: Capture TDO data during shift and return from sequence run command
            end_state: JTAG state to enter after shift is complete. The default is RESET.
        """

        if self._dr_prefix.size != 0:
            self.shift(
                shift_type="dr",
                data=self._dr_prefix.value,
                size=self._dr_prefix.size,
                capture=False,
                end_state=JtagState.DRSHIFT,
            )

        self.shift(
            shift_type="dr",
            data=data,
            tdi=tdi,
            size=size,
            capture=capture,
            end_state=JtagState.DRSHIFT if self._dr_postfix.size != 0 else end_state,
        )

        if self._dr_postfix.size != 0:
            self.shift(
                shift_type="dr",
                data=self._dr_postfix.value,
                size=self._dr_postfix.size,
                capture=False,
                end_state=end_state,
            )

    def set_state(self, state: JtagState, count: int = 0):
        """Add JTAG sequence command to move JTAG state machine to a new state and then generate certain number of JTAG
        clocks

        Args:
            state: Move JTAG state machine to this state
            count: Number of JTAG clocks to generate after moving to specified JTAG state
        """
        state_command = ["state", state.name, count]
        self._commands.append(state_command)

    def run(self) -> List[bytearray]:
        """Run JTAG operations in sequence for target JTAG node. This method will return the result from IR/DR shift
        commands for which capture is true.

        Args:
            None

        TODO: Option to mask and compare data returned after running sequence
        """
        # Execute commands in JTAG sequence
        seq_result = self._jtag_node.sequence(self._commands, self._data)

        result = list()
        index = 0
        for command in self._commands:
            # Split combined sequence run result into a list of bytearrays based on length of shift commands in
            # JTAG sequence
            if command[0] == "shift" and command[2] is True:
                size_in_bytes = -(command[3] // -8)
                result.append(seq_result[index : index + size_in_bytes])
                index += size_in_bytes
        return result
