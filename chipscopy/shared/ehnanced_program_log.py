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
class ProgramLogStrategy:
    """
    Interface for the PDI Report.

    The client and server must implement the 4 empty functions.
    When implemented, the generate_report() method will generate
    an enhanced program log for use in the pdi_debug_util.

    This class lives in a common area to both cs_server and chipscopy.
    """

    def get_slr_count(self) -> int:
        """
        Return the number of SLRs in the device
        """
        ...

    def get_reg_hex_val(self, reg_name: str, slr_index: int) -> str:
        """
        Return the hex value of the named register.
        Supported registers: jtag_status, error_status.

        Example::
            get_reg_hex_val("jtag_status")
            0x042e810f0d
        """
        ...

    def get_reg_bitfield(self, reg_name: str, slr_index: int) -> str:
        """
        Return a string with lines representing the bitfield of the registers.
        Supported registers: jtag_status, error_status.

        Example::
            get_reg_bitfield("jtag_status")
            RESERVED_35 (Bits [35]): 0
            DONE (Bits [34]): 1
            JRDBK_ERROR (Bits [33]): 0
            JCONFIG_ERROR (Bits [32]): 0
            PMC_VERSION (Bits [31:28]): 2
            RESERVED_27_24 (Bits [27:24]): e
            ...

        """
        ...

    def get_plm_log(self, slr_index: int) -> str:
        """
        Return text of the PLM log.

        Example::
            get_plm_log(0)
            [0.016]****************************************
            [0.049]Xilinx Versal Platform Loader and Manager
            [0.083]Release 2024.1   Jun 13 2024  -  21:21:34
            [0.118]Platform Version: v2.0 PMC: v2.0, PS: v2.0
            [0.159]BOOTMODE: 0x0, MULTIBOOT: 0x0
            [0.188]****************************************
            ...
        """
        ...

    def generate_program_log(self) -> str:
        """
        Generate a string with an enhanced program log.
        This contains jtag_status, error_status, and the PLM log for each SLR.
        """
        report_lines = []
        for slr_index in range(self.get_slr_count()):
            report_lines.append("Enhanced PDI Log Version 1.0")
            if self.get_slr_count() > 1:
                # special case for multi-slr device
                report_lines.append(f"#################### SLR {slr_index} ####################")
            report_lines.append("JTAG Status")
            reg_val = self.get_reg_hex_val("jtag_status", slr_index)
            report_lines.append(f"JTAG STATUS: {reg_val}")
            reg_bits = self.get_reg_bitfield("jtag_status", slr_index)
            report_lines.append(reg_bits)
            report_lines.append("Error Status")
            reg_val = self.get_reg_hex_val("error_status", slr_index)
            report_lines.append(f"ERROR STATUS: {reg_val}")
            reg_bits = self.get_reg_bitfield("error_status", slr_index)
            report_lines.append(reg_bits)
            report_lines.append("PLM Log")
            plm_log = self.get_plm_log(slr_index)
            report_lines.append(plm_log)
        return "\n".join(str(e) for e in report_lines)
