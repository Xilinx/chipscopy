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





# file: ibert_vcu128_q131_q132.xdc
####################################################################################

##**************************************************************************
##
## Icon Constraints
##





create_clock -name D_CLK -period 10.0 [get_ports gty_sysclkp_i]
set_clock_groups -group [get_clocks D_CLK -include_generated_clocks] -asynchronous

set_property C_CLK_INPUT_FREQ_HZ 100000000 [get_debug_cores dbg_hub]
set_property C_ENABLE_CLK_DIVIDER true [get_debug_cores dbg_hub]
##
##gtrefclk lock constraints
##






 
set_property PACKAGE_PIN AB42 [get_ports gty_refclk0p_i[0]]
set_property PACKAGE_PIN AB43 [get_ports gty_refclk0n_i[0]]
set_property PACKAGE_PIN AA40 [get_ports gty_refclk1p_i[0]]
set_property PACKAGE_PIN AA41 [get_ports gty_refclk1n_i[0]]

 
set_property PACKAGE_PIN Y42 [get_ports gty_refclk0p_i[1]]
set_property PACKAGE_PIN Y43 [get_ports gty_refclk0n_i[1]]
set_property PACKAGE_PIN W40 [get_ports gty_refclk1p_i[1]]
set_property PACKAGE_PIN W41 [get_ports gty_refclk1n_i[1]]


set_property PACKAGE_PIN T42 [get_ports gty_refclk0p_i[2]]
set_property PACKAGE_PIN T43 [get_ports gty_refclk0n_i[2]]
set_property PACKAGE_PIN R40 [get_ports gty_refclk1p_i[2]]
set_property PACKAGE_PIN R41 [get_ports gty_refclk1n_i[2]]

 
set_property PACKAGE_PIN P42 [get_ports gty_refclk0p_i[3]]
set_property PACKAGE_PIN P43 [get_ports gty_refclk0n_i[3]]
set_property PACKAGE_PIN M42 [get_ports gty_refclk1p_i[3]]
set_property PACKAGE_PIN M43 [get_ports gty_refclk1n_i[3]]

##
## Refclk constraints
##





 
create_clock -name gtrefclk0_7 -period 6.4 [get_ports gty_refclk0p_i[0]]
create_clock -name gtrefclk1_7 -period 6.4 [get_ports gty_refclk1p_i[0]]
set_clock_groups -group [get_clocks gtrefclk0_7 -include_generated_clocks] -asynchronous
set_clock_groups -group [get_clocks gtrefclk1_7 -include_generated_clocks] -asynchronous
 
create_clock -name gtrefclk0_8 -period 6.4 [get_ports gty_refclk0p_i[1]]
create_clock -name gtrefclk1_8 -period 6.4 [get_ports gty_refclk1p_i[1]]
set_clock_groups -group [get_clocks gtrefclk0_8 -include_generated_clocks] -asynchronous
set_clock_groups -group [get_clocks gtrefclk1_8 -include_generated_clocks] -asynchronous

create_clock -name gtrefclk0_10 -period 6.4 [get_ports gty_refclk0p_i[2]]
create_clock -name gtrefclk1_10 -period 6.4 [get_ports gty_refclk1p_i[2]]
set_clock_groups -group [get_clocks gtrefclk0_10 -include_generated_clocks] -asynchronous
set_clock_groups -group [get_clocks gtrefclk1_10 -include_generated_clocks] -asynchronous
 
create_clock -name gtrefclk0_11 -period 6.4 [get_ports gty_refclk0p_i[3]]
create_clock -name gtrefclk1_11 -period 6.4 [get_ports gty_refclk1p_i[3]]
set_clock_groups -group [get_clocks gtrefclk0_11 -include_generated_clocks] -asynchronous
set_clock_groups -group [get_clocks gtrefclk1_11 -include_generated_clocks] -asynchronous

##
## System clock pin locs and timing constraints
##
set_property PACKAGE_PIN BH51 [get_ports gty_sysclkp_i]
set_property IOSTANDARD LVDS [get_ports gty_sysclkp_i]
