# Copyright (C) 2024, Advanced Micro Devices, Inc.
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
#
from typing import Dict, Callable

from chipscopy.client.jtagdevice import JtagRegister
from chipscopy.shared.ehnanced_program_log import ProgramLogStrategy


class ClientProgramLogStrategy(ProgramLogStrategy):
    """
    ChipScoPy client side implement of the Program report strategy.
    This looks up registers and log in the chipscopy client.

    This class lives on the chipscopy client side.
    """

    def __init__(self, regs: Dict[str, JtagRegister], plm_log_fn: Callable[[int], str]):
        self._slr_count = regs.get("reg.slr_count", 1)
        self._regs = {
            "jtag_status": regs.get("jtag_status"),
            "error_status": regs.get("error_status"),
        }
        self._plm_log_fn = plm_log_fn

    def get_slr_count(self) -> int:
        return self._slr_count

    def get_reg_hex_val(self, reg_name: str, slr_index: int) -> str:
        try:
            data = self._regs[reg_name].data[slr_index]
            return "0x" + data[::-1].hex()
        except KeyError:
            return f"Register {reg_name} not found"
        except IndexError:
            return f"SLR index {slr_index} out of range"

    def get_reg_bitfield(self, reg_name: str, slr_index: int) -> str:
        try:
            report_lines = []
            reg = self._regs[reg_name]
            fields: Dict = reg.fields[slr_index]
            for _, val in fields.items():
                name = val.get("name", "")
                bit_range = val.get("bit_range", "")
                int_val: int = val.get("value", 0)
                hex_value = format(int_val, "x")
                report_lines.append(f"{name} (Bits [{bit_range}]): {hex_value}")
            return "\n".join(str(e) for e in report_lines)
        except KeyError:
            return f"Register {reg_name} not found"
        except IndexError:
            return f"SLR index {slr_index} out of range"

    def get_plm_log(self, slr_index: int) -> str:
        try:
            return self._plm_log_fn(slr_index)
        except Exception as e:
            return f"Error retrieving PLM log: {str(e)}"
