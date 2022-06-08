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

noc_nmu_typedef = "noc_nmu"
noc_nsu_typedef = "noc_nsu"
ddrmc_noc_typedef = "ddrmc_noc"
ddrmc_main_typedef = "ddrmc_main"
hbmmc_typedef = "hbmmc"
noc_node_types = [
    noc_nmu_typedef,
    noc_nsu_typedef,
    ddrmc_noc_typedef,
    ddrmc_main_typedef,
    hbmmc_typedef,
]
noc_bw_lat_types = [noc_nmu_typedef, noc_nsu_typedef, ddrmc_noc_typedef]
