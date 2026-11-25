#------------------------------------------------------------------------------
#  (c) Copyright 2023 Advanced Micro Devices, Inc. All rights reserved.
#
#  This file contains confidential and proprietary information
#  of AMD, Inc. and is protected under U.S. and
#  international copyright and other intellectual property
#  laws.
#
#  DISCLAIMER
#  This disclaimer is not a license and does not grant any
#  rights to the materials distributed herewith. Except as
#  otherwise provided in a valid license issued to you by
#  AMD, and to the maximum extent permitted by applicable
#  law: (1) THESE MATERIALS ARE MADE AVAILABLE "AS IS" AND
#  WITH ALL FAULTS, AND AMD HEREBY DISCLAIMS ALL WARRANTIES
#  AND CONDITIONS, EXPRESS, IMPLIED, OR STATUTORY, INCLUDING
#  BUT NOT LIMITED TO WARRANTIES OF MERCHANTABILITY, NON-
#  INFRINGEMENT, OR FITNESS FOR ANY PARTICULAR PURPOSE; and
#  (2) AMD shall not be liable (whether in contract or tort,
#  including negligence, or under any other theory of
#  liability) for any loss or damage of any kind or nature
#  related to, arising under or in connection with these
#  materials, including for any direct, or any indirect,
#  special, incidental, or consequential loss or damage
#  (including loss of data, profits, goodwill, or any type of
#  loss or damage suffered as a result of any action brought
#  by a third party) even if such damage or loss was
#  reasonably foreseeable or AMD had been advised of the
#  possibility of the same.
#
#  CRITICAL APPLICATIONS
#  AMD products are not designed or intended to be fail-
#  safe, or for use in any application requiring fail-safe
#  performance, such as life-support or safety devices or
#  systems, Class III medical devices, nuclear facilities,
#  applications related to the deployment of airbags, or any
#  other applications that could lead to death, personal
#  injury, or severe property or environmental damage
#  (individually and collectively, "Critical
#  Applications"). Customer assumes the sole risk and
#  liability of any use of AMD products in Critical
#  Applications, subject only to applicable laws and
#  regulations governing limitations on product liability.
#
#  THIS COPYRIGHT NOTICE AND DISCLAIMER MUST BE RETAINED AS
#  PART OF THIS FILE AT ALL TIMES.
#------------------------------------------------------------------------------


# UltraScale FPGAs Transceivers Wizard IP example design-level XDC file
# ----------------------------------------------------------------------------------------------------------------------

# Location constraints for differential reference clock buffers
# Note: the IP core-level XDC constrains the transceiver channel data pin locations
# ----------------------------------------------------------------------------------------------------------------------
set_property package_pin L28 [get_ports mgtrefclk0_x0y2_n]
set_property package_pin L27 [get_ports mgtrefclk0_x0y2_p]
set_property package_pin C7 [get_ports mgtrefclk0_x1y3_n]
set_property package_pin C8 [get_ports mgtrefclk0_x1y3_p]

# Location constraints for other example design top-level ports
# Note: uncomment the following set_property constraints and replace "<>" with appropriate pin locations for your board
# ----------------------------------------------------------------------------------------------------------------------
#set_property package_pin <> [get_ports hb_gtwiz_reset_clk_freerun_in]
#set_property iostandard  <> [get_ports hb_gtwiz_reset_clk_freerun_in]

#set_property package_pin <> [get_ports hb_gtwiz_reset_all_in]
#set_property iostandard  <> [get_ports hb_gtwiz_reset_all_in]

#set_property package_pin <> [get_ports link_down_latched_reset_in]
#set_property iostandard  <> [get_ports link_down_latched_reset_in]

#set_property package_pin <> [get_ports link_status_out]
#set_property iostandard  <> [get_ports link_status_out]

#set_property package_pin <> [get_ports link_down_latched_out]
#set_property iostandard  <> [get_ports link_down_latched_out]

# Clock constraints for clocks provided as inputs to the core
# Note: the IP core-level XDC constrains clocks produced by the core, which drive user clocks via helper blocks
# ----------------------------------------------------------------------------------------------------------------------
create_clock -name clk_freerun -period 8.0 [get_ports hb_gtwiz_reset_clk_freerun_in]
create_clock -name clk_mgtrefclk0_x0y2_p -period 6.4 [get_ports mgtrefclk0_x0y2_p]
create_clock -name clk_mgtrefclk0_x1y3_p -period 6.4 [get_ports mgtrefclk0_x1y3_p]

# False path constraints
# ----------------------------------------------------------------------------------------------------------------------
set_false_path -to [get_cells -hierarchical -filter {NAME =~ *bit_synchronizer*inst/i_in_meta_reg}] -quiet
##set_false_path -to [get_cells -hierarchical -filter {NAME =~ *reset_synchronizer*inst/rst_in_*_reg}] -quiet
set_false_path -to [get_pins -filter {REF_PIN_NAME=~*D} -of_objects [get_cells -hierarchical -filter {NAME =~ *reset_synchronizer*inst/rst_in_meta*}]] -quiet
set_false_path -to [get_pins -filter {REF_PIN_NAME=~*PRE} -of_objects [get_cells -hierarchical -filter {NAME =~ *reset_synchronizer*inst/rst_in_meta*}]] -quiet
set_false_path -to [get_pins -filter {REF_PIN_NAME=~*PRE} -of_objects [get_cells -hierarchical -filter {NAME =~ *reset_synchronizer*inst/rst_in_sync1*}]] -quiet
set_false_path -to [get_pins -filter {REF_PIN_NAME=~*PRE} -of_objects [get_cells -hierarchical -filter {NAME =~ *reset_synchronizer*inst/rst_in_sync2*}]] -quiet
set_false_path -to [get_pins -filter {REF_PIN_NAME=~*PRE} -of_objects [get_cells -hierarchical -filter {NAME =~ *reset_synchronizer*inst/rst_in_sync3*}]] -quiet
set_false_path -to [get_pins -filter {REF_PIN_NAME=~*PRE} -of_objects [get_cells -hierarchical -filter {NAME =~ *reset_synchronizer*inst/rst_in_out*}]] -quiet


set_false_path -to [get_cells -hierarchical -filter {NAME =~ *gtwiz_userclk_tx_inst/*gtwiz_userclk_tx_active_*_reg}] -quiet
set_false_path -to [get_cells -hierarchical -filter {NAME =~ *gtwiz_userclk_rx_inst/*gtwiz_userclk_rx_active_*_reg}] -quiet

###  for exdes




create_waiver -internal -type CDC -id {CDC-10} -user gtwizard_ultrascale -tags "1165536" -description "CDC-10 Paths between support blocks like vio and exdes inst" \
                        -scope -from [get_pins -quiet -filter {REF_PIN_NAME=~*C} -of_objects [get_cells -hierarchical -filter {SCOPED_NAME=~example_checking_inst*/prbs_match_out_reg*}]] \
						-to [get_pins -quiet -filter {REF_PIN_NAME=~*PRE} -of_objects [get_cells -hierarchical -filter {SCOPED_NAME =~*rst_in_meta_reg}]]
  
create_waiver -internal -type CDC -id {CDC-12} -user gtwizard_ultrascale -tags "1165536" -description "CDC-12 Paths between support blocks like vio and exdes inst" \
                        -scope -from [get_pins -quiet -filter {REF_PIN_NAME=~*C} -of_objects [get_cells -hierarchical -filter {SCOPED_NAME=~example_checking_inst*/prbs_match_out_reg*}]] \
						-to [get_pins -quiet -filter {REF_PIN_NAME=~*PRE} -of_objects [get_cells -hierarchical -filter {SCOPED_NAME =~*rst_in_meta_reg}]]








create_waiver -internal -type CDC -id {CDC-10} -user gtwizard_ultrascale -tags "1165536" -description "CDC-10 In exdes and vio path" -scope -from [get_pins -quiet -filter {REF_PIN_NAME=~*C} -of_objects [get_cells -hierarchical -filter {SCOPED_NAME=~*/reset_synchronizer_rx_done_inst/rst_in_out_reg}]] -to [get_pins -quiet -filter {REF_PIN_NAME=~*D} -of_objects [get_cells -hierarchical -filter {SCOPED_NAME =~*/bit_synchronizer_rx_init_done_inst/i_in_meta_reg}]]

          
create_waiver -internal -type CDC -id {CDC-10} -user gtwizard_ultrascale -tags "1165536" -description "CDC-10 In exdes and vio path" -scope -from [get_pins -quiet -filter {REF_PIN_NAME=~*C} -of_objects [get_cells -hierarchical -filter {SCOPED_NAME=~*/reset_synchronizer_rx_done_inst/rst_in_out_reg}]] -to [get_pins -quiet -filter {REF_PIN_NAME=~*PRE} -of_objects [get_cells -hierarchical -filter {SCOPED_NAME =~*/example_*_reset_synchronizer_inst/rst_in_meta_reg}]]

create_waiver -internal -type CDC -id {CDC-12} -user gtwizard_ultrascale -tags "1165536" -description "CDC-12 In exdes and vio path" -scope -from [get_pins -quiet -filter {REF_PIN_NAME=~*C} -of_objects [get_cells -hierarchical -filter {SCOPED_NAME=~*/reset_synchronizer_rx_done_inst/rst_in_out_reg}]] -to [get_pins -quiet -filter {REF_PIN_NAME=~*PRE} -of_objects [get_cells -hierarchical -filter {SCOPED_NAME =~*/example_*_reset_synchronizer_inst/rst_in_meta_reg}]]



create_waiver -internal -type CDC -id {CDC-10} -user gtwizard_ultrascale -tags "1165536" -description "CDC-10 Paths between support blocks like vio and exdes inst" \
                        -scope -to [get_pins -quiet -filter {REF_PIN_NAME=~*PRE} -of_objects [get_cells -hierarchical -filter {SCOPED_NAME =~*/example_*_reset_synchronizer_inst/rst_in_meta_reg}]]
  
create_waiver -internal -type CDC -id {CDC-11} -user gtwizard_ultrascale -tags "1165536" -description "CDC-11 Paths between support blocks like vio and exdes inst" \
                        -scope -to [get_pins -quiet -filter {REF_PIN_NAME=~*PRE} -of_objects [get_cells -hierarchical -filter {SCOPED_NAME =~*/example_*_reset_synchronizer_inst/rst_in_meta_reg}]]

create_waiver -internal -type CDC -id {CDC-12} -user gtwizard_ultrascale -tags "1165536" -description "CDC-12 Paths between support blocks like vio and exdes inst" \
                        -scope -to [get_pins -quiet -filter {REF_PIN_NAME=~*PRE} -of_objects [get_cells -hierarchical -filter {SCOPED_NAME =~*/example_*_reset_synchronizer_inst/rst_in_meta_reg}]]



create_waiver -internal -type CDC -id {CDC-10} -user gtwizard_ultrascale -tags "1165536" -description "CDC-10 In exdes and vio path" -scope -from [get_pins -quiet -filter {REF_PIN_NAME=~*C} -of_objects [get_cells -hierarchical -filter {SCOPED_NAME=~*/reset_synchronizer_*x_done_inst/rst_in_out_reg}]] -to [get_pins -quiet -filter {REF_PIN_NAME=~*D} -of_objects [get_cells -hierarchical -filter {SCOPED_NAME =~*/bit_synchronizer_*x_init_done_inst/i_in_meta_reg}]]

create_waiver -internal -type CDC -id {CDC-11} -user gtwizard_ultrascale -tags "1165536" -description "CDC-11 In exdes and vio path" -scope -from [get_pins -quiet -filter {REF_PIN_NAME=~*C} -of_objects [get_cells -hierarchical -filter {SCOPED_NAME=~example_init_inst/reset_all_out_reg}]] -to [get_pins -quiet -filter {REF_PIN_NAME=~*PRE} -of_objects [get_cells -hierarchical -filter {SCOPED_NAME =~*/example_checking_reset_synchronizer_inst/rst_in_meta_reg}]]

create_waiver -internal -type CDC -id {CDC-12} -user gtwizard_ultrascale -tags "1165536" -description "CDC-12 In exdes and vio path" -scope -from [get_pins -quiet -filter {REF_PIN_NAME=~*C} -of_objects [get_cells -hierarchical -filter {SCOPED_NAME=~example_init_inst/reset_all_out_reg}]] -to [get_pins -quiet -filter {REF_PIN_NAME=~*PRE} -of_objects [get_cells -hierarchical -filter {SCOPED_NAME =~*/example_checking_reset_synchronizer_inst/rst_in_meta_reg}]]

create_waiver -internal -type CDC -id {CDC-11} -user gtwizard_ultrascale -tags "1165536" -description "CDC-11 In exdes and vio path" -scope -from [get_pins -quiet -filter {REF_PIN_NAME=~*C} -of_objects [get_cells -hierarchical -filter {SCOPED_NAME=~*/reset_synchronizer_*x_done_inst/rst_in_out_reg}]] -to [get_pins -quiet -filter {REF_PIN_NAME=~*D} -of_objects [get_cells -hierarchical -filter {SCOPED_NAME =~bit_synchronizer_vio_gtwiz_reset_*x_done_*_inst/i_in_meta_reg}]]

create_waiver -internal -type CDC -id {CDC-11} -user gtwizard_ultrascale -tags "1165536" -description "CDC-11 In exdes and vio path" -scope -from [get_pins -quiet -filter {REF_PIN_NAME=~*C} -of_objects [get_cells -hierarchical -filter {SCOPED_NAME=~*/reset_synchronizer_*x_done_inst/rst_in_out_reg}]] -to [get_pins -quiet -filter {REF_PIN_NAME=~*D} -of_objects [get_cells -hierarchical -filter {SCOPED_NAME =~*/bit_synchronizer_*x_init_done_inst/i_in_meta_reg}]]

create_waiver -internal -type CDC -id {CDC-12} -user gtwizard_ultrascale -tags "1165536" -description "CDC-12 In exdes and vio path" -scope -from [get_pins -quiet -filter {REF_PIN_NAME=~*C} -of_objects [get_cells -hierarchical -filter {SCOPED_NAME=~*/reset_synchronizer_*x_done_inst/rst_in_out_reg}]] -to [get_pins -quiet -filter {REF_PIN_NAME=~*D} -of_objects [get_cells -hierarchical -filter {SCOPED_NAME =~*/bit_synchronizer_*x_init_done_inst/i_in_meta_reg}]]

