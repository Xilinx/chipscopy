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

from zipfile import ZipFile
import os
import tempfile
import xml.etree.ElementTree as ET


class HardwareHandoff:
    noc_mod_type = "axi_noc"
    cips_mod_type = "versal_cips"
    axi_tg_type = "sim_trig"
    mc_period_parameter_name = "mc_memory_timeperiod"
    cips_ref_clk_names = [
        "pmc_ref_clk_freqmhz",
        "pmc_alt_ref_clk_freqmhz",
        "pmc_pl_alt_ref_clk_freqmhz",
    ]

    def __init__(self, filename):
        self.supported_sampling_T_to_tap = {}
        self.filename = filename
        self.tree = None
        self.root = None
        self.ddrmc_periods_ps = {}  # tabulated during parse
        self.cips_clk_info = {}
        for clk in HardwareHandoff.cips_ref_clk_names:
            self.cips_clk_info[clk] = 33.33333
        self.axi_tgs = {}
        self.parse_handoff_file()

    def parse_handoff_file(self):
        self.tree = ET.parse(self.filename)
        self.root = self.tree.getroot()
        self.parse_ddrmc_clocking_info()
        self.parse_cips_clocking_info()
        self.parse_tg_info()

    def parse_ddrmc_clocking_info(self):
        # Assumption is that there is one NoC
        found_noc = False
        # use XPath expression to find
        for module in self.root.findall("./MODULES/MODULE"):
            if module.get("MODTYPE") != HardwareHandoff.noc_mod_type:
                continue
            # use XPATH to get all the pertinent MC period
            for param in module.findall("PARAMETERS/PARAMETER"):
                if HardwareHandoff.mc_period_parameter_name in param.get("NAME").lower():
                    name = param.get("NAME").lower()
                    inst = int(name.split(HardwareHandoff.mc_period_parameter_name)[-1])
                    # per Jon Jasper MC clock is 2x memory speed
                    self.ddrmc_periods_ps[inst] = 2 * int(param.get("VALUE"))

    def parse_cips_clocking_info(self):
        for module in self.root.findall("./MODULES/MODULE"):
            if module.get("MODTYPE") != HardwareHandoff.cips_mod_type:
                continue
            for param in module.findall("PARAMETERS/PARAMETER"):
                if param.get("NAME").lower() in HardwareHandoff.cips_ref_clk_names:
                    self.cips_clk_info[param.get("NAME").lower()] = float(param.get("VALUE"))

    def get_ref_clk_freqs(self):
        return (
            self.cips_clk_info["pmc_ref_clk_freqmhz"],
            self.cips_clk_info["pmc_pl_alt_ref_clk_freqmhz"],
        )

    def get_ddrmc_freq_mhz(self):
        freqs = {}
        for instance, time_period_ps in self.ddrmc_periods_ps.items():
            freqs[f"DDRMC_MAIN_{instance}"] = (1 / time_period_ps) * 1000000
        return freqs

    def parse_tg_info(self):
        for module in self.root.findall("./MODULES/MODULE"):
            if module.get("MODTYPE") != HardwareHandoff.axi_tg_type:
                continue
            # found axi_tg
            inst_name = module.get("INSTANCE")
            self.axi_tgs[inst_name] = {}
            for param in module.findall("PARAMETERS/PARAMETER"):
                if param.get("NAME").lower() == "c_baseaddr":
                    self.axi_tgs[inst_name][param.get("NAME").lower()] = int(param.get("VALUE"), 16)


class XSA:
    """
    Given an xsa attempt to extract he design related info files into a temp_directory
    :param xsa_filename:
    """

    def __init__(self, xsa_filename: str):
        self.xsa_filename = xsa_filename
        # if design_name is None:
        #     temp = os.path.splitext(os.path.split(xsa_filename)[-1])[0]
        #     parts = temp.split('_')
        #     if parts[-1] == 'wrapper':
        #         self.design_name = '_'.join(parts[0:-1])
        #     else:
        #         self.design_name = temp
        # else:
        #     self.design_name = design_name
        self.hardware_handoff = None
        # extract into storage location
        self.tempdir = None
        # dict of the _extracted_ design filenames
        self.design_fileset = {".pdi": None, ".hwh": None}
        self.extract_xsa()

    def extract_xsa(self):
        # create temp working area
        self.tempdir = (
            tempfile.TemporaryDirectory()
        )  # automatic filesystem management when this is done
        with ZipFile(self.xsa_filename, "r") as zip_object:
            manifest = zip_object.namelist()
            for filename in manifest:
                if filename == "sysdef.xml":
                    zip_object.extract(filename, self.tempdir.name)
                    root = ET.parse(self.tempdir.name + os.sep + filename).getroot()
                    for file in root.findall("./File"):
                        if file.get("Type").lower() == "pdi":
                            pdi_filename = file.get("Name")
                            extracted_pdi = self.tempdir.name + os.sep + pdi_filename
                            self.design_fileset[".pdi"] = extracted_pdi
                            zip_object.extract(pdi_filename, self.tempdir.name)
                        if (
                            file.get("Type").lower() == "hw_handoff"
                            and file.get("BD_TYPE").lower() == "default_bd"
                        ):
                            handoff_filename = file.get("Name")
                            extracted_hw = self.tempdir.name + os.sep + handoff_filename
                            self.design_fileset[".hwh"] = extracted_hw
                            zip_object.extract(handoff_filename, self.tempdir.name)

        if self.design_fileset[".hwh"] is not None:
            # This will parse pertinent file info
            self.hardware_handoff = HardwareHandoff(self.design_fileset[".hwh"])
        else:
            raise FileNotFoundError("Unable to find the hardware handoff file, verify xsa")
            pass

        if self.design_fileset[".pdi"] is None:
            raise FileNotFoundError("Unable to find the pdi file, verify xsa")

    def close(self):
        self.tempdir.cleanup()
