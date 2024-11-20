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
## TX/RX out clock clock constraints
##





# GT X0Y28
set_clock_groups -asynchronous -group [get_clocks -of_objects [get_pins {u_ibert_gty_core_a/inst/QUAD0.u_q/CH[0].u_ch/u_gtye4_channel/RXOUTCLK}] -include_generated_clocks]
set_clock_groups -asynchronous -group [get_clocks -of_objects [get_pins {u_ibert_gty_core_a/inst/QUAD0.u_q/CH[0].u_ch/u_gtye4_channel/TXOUTCLK}] -include_generated_clocks]
# GT X0Y29
set_clock_groups -asynchronous -group [get_clocks -of_objects [get_pins {u_ibert_gty_core_a/inst/QUAD0.u_q/CH[1].u_ch/u_gtye4_channel/RXOUTCLK}] -include_generated_clocks]
set_clock_groups -asynchronous -group [get_clocks -of_objects [get_pins {u_ibert_gty_core_a/inst/QUAD0.u_q/CH[1].u_ch/u_gtye4_channel/TXOUTCLK}] -include_generated_clocks]
# GT X0Y30
set_clock_groups -asynchronous -group [get_clocks -of_objects [get_pins {u_ibert_gty_core_a/inst/QUAD0.u_q/CH[2].u_ch/u_gtye4_channel/RXOUTCLK}] -include_generated_clocks]
set_clock_groups -asynchronous -group [get_clocks -of_objects [get_pins {u_ibert_gty_core_a/inst/QUAD0.u_q/CH[2].u_ch/u_gtye4_channel/TXOUTCLK}] -include_generated_clocks]
# GT X0Y31
set_clock_groups -asynchronous -group [get_clocks -of_objects [get_pins {u_ibert_gty_core_a/inst/QUAD0.u_q/CH[3].u_ch/u_gtye4_channel/RXOUTCLK}] -include_generated_clocks]
set_clock_groups -asynchronous -group [get_clocks -of_objects [get_pins {u_ibert_gty_core_a/inst/QUAD0.u_q/CH[3].u_ch/u_gtye4_channel/TXOUTCLK}] -include_generated_clocks]
# GT X0Y32
set_clock_groups -asynchronous -group [get_clocks -of_objects [get_pins {u_ibert_gty_core_a/inst/QUAD1.u_q/CH[0].u_ch/u_gtye4_channel/RXOUTCLK}] -include_generated_clocks]
set_clock_groups -asynchronous -group [get_clocks -of_objects [get_pins {u_ibert_gty_core_a/inst/QUAD1.u_q/CH[0].u_ch/u_gtye4_channel/TXOUTCLK}] -include_generated_clocks]
# GT X0Y33
set_clock_groups -asynchronous -group [get_clocks -of_objects [get_pins {u_ibert_gty_core_a/inst/QUAD1.u_q/CH[1].u_ch/u_gtye4_channel/RXOUTCLK}] -include_generated_clocks]
set_clock_groups -asynchronous -group [get_clocks -of_objects [get_pins {u_ibert_gty_core_a/inst/QUAD1.u_q/CH[1].u_ch/u_gtye4_channel/TXOUTCLK}] -include_generated_clocks]
# GT X0Y34
set_clock_groups -asynchronous -group [get_clocks -of_objects [get_pins {u_ibert_gty_core_a/inst/QUAD1.u_q/CH[2].u_ch/u_gtye4_channel/RXOUTCLK}] -include_generated_clocks]
set_clock_groups -asynchronous -group [get_clocks -of_objects [get_pins {u_ibert_gty_core_a/inst/QUAD1.u_q/CH[2].u_ch/u_gtye4_channel/TXOUTCLK}] -include_generated_clocks]
# GT X0Y35
set_clock_groups -asynchronous -group [get_clocks -of_objects [get_pins {u_ibert_gty_core_a/inst/QUAD1.u_q/CH[3].u_ch/u_gtye4_channel/RXOUTCLK}] -include_generated_clocks]
set_clock_groups -asynchronous -group [get_clocks -of_objects [get_pins {u_ibert_gty_core_a/inst/QUAD1.u_q/CH[3].u_ch/u_gtye4_channel/TXOUTCLK}] -include_generated_clocks]

# GT X0Y40
set_clock_groups -asynchronous -group [get_clocks -of_objects [get_pins {u_ibert_gty_core_b/inst/QUAD0.u_q/CH[0].u_ch/u_gtye4_channel/RXOUTCLK}] -include_generated_clocks]
set_clock_groups -asynchronous -group [get_clocks -of_objects [get_pins {u_ibert_gty_core_b/inst/QUAD0.u_q/CH[0].u_ch/u_gtye4_channel/TXOUTCLK}] -include_generated_clocks]
# GT X0Y41
set_clock_groups -asynchronous -group [get_clocks -of_objects [get_pins {u_ibert_gty_core_b/inst/QUAD0.u_q/CH[1].u_ch/u_gtye4_channel/RXOUTCLK}] -include_generated_clocks]
set_clock_groups -asynchronous -group [get_clocks -of_objects [get_pins {u_ibert_gty_core_b/inst/QUAD0.u_q/CH[1].u_ch/u_gtye4_channel/TXOUTCLK}] -include_generated_clocks]
# GT X0Y42
set_clock_groups -asynchronous -group [get_clocks -of_objects [get_pins {u_ibert_gty_core_b/inst/QUAD0.u_q/CH[2].u_ch/u_gtye4_channel/RXOUTCLK}] -include_generated_clocks]
set_clock_groups -asynchronous -group [get_clocks -of_objects [get_pins {u_ibert_gty_core_b/inst/QUAD0.u_q/CH[2].u_ch/u_gtye4_channel/TXOUTCLK}] -include_generated_clocks]
# GT X0Y43
set_clock_groups -asynchronous -group [get_clocks -of_objects [get_pins {u_ibert_gty_core_b/inst/QUAD0.u_q/CH[3].u_ch/u_gtye4_channel/RXOUTCLK}] -include_generated_clocks]
set_clock_groups -asynchronous -group [get_clocks -of_objects [get_pins {u_ibert_gty_core_b/inst/QUAD0.u_q/CH[3].u_ch/u_gtye4_channel/TXOUTCLK}] -include_generated_clocks]
# GT X0Y44
set_clock_groups -asynchronous -group [get_clocks -of_objects [get_pins {u_ibert_gty_core_b/inst/QUAD1.u_q/CH[0].u_ch/u_gtye4_channel/RXOUTCLK}] -include_generated_clocks]
set_clock_groups -asynchronous -group [get_clocks -of_objects [get_pins {u_ibert_gty_core_b/inst/QUAD1.u_q/CH[0].u_ch/u_gtye4_channel/TXOUTCLK}] -include_generated_clocks]
# GT X0Y45
set_clock_groups -asynchronous -group [get_clocks -of_objects [get_pins {u_ibert_gty_core_b/inst/QUAD1.u_q/CH[1].u_ch/u_gtye4_channel/RXOUTCLK}] -include_generated_clocks]
set_clock_groups -asynchronous -group [get_clocks -of_objects [get_pins {u_ibert_gty_core_b/inst/QUAD1.u_q/CH[1].u_ch/u_gtye4_channel/TXOUTCLK}] -include_generated_clocks]
# GT X0Y46
set_clock_groups -asynchronous -group [get_clocks -of_objects [get_pins {u_ibert_gty_core_b/inst/QUAD1.u_q/CH[2].u_ch/u_gtye4_channel/RXOUTCLK}] -include_generated_clocks]
set_clock_groups -asynchronous -group [get_clocks -of_objects [get_pins {u_ibert_gty_core_b/inst/QUAD1.u_q/CH[2].u_ch/u_gtye4_channel/TXOUTCLK}] -include_generated_clocks]
# GT X0Y47
set_clock_groups -asynchronous -group [get_clocks -of_objects [get_pins {u_ibert_gty_core_b/inst/QUAD1.u_q/CH[3].u_ch/u_gtye4_channel/RXOUTCLK}] -include_generated_clocks]
set_clock_groups -asynchronous -group [get_clocks -of_objects [get_pins {u_ibert_gty_core_b/inst/QUAD1.u_q/CH[3].u_ch/u_gtye4_channel/TXOUTCLK}] -include_generated_clocks]
