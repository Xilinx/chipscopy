#------------------------------------------------------------------------------
#  (c) Copyright 2013-2015 Xilinx, Inc. All rights reserved.
#
#  This file contains confidential and proprietary information
#  of Xilinx, Inc. and is protected under U.S. and
#  international copyright and other intellectual property
#  laws.
#
#  DISCLAIMER
#  This disclaimer is not a license and does not grant any
#  rights to the materials distributed herewith. Except as
#  otherwise provided in a valid license issued to you by
#  Xilinx, and to the maximum extent permitted by applicable
#  law: (1) THESE MATERIALS ARE MADE AVAILABLE "AS IS" AND
#  WITH ALL FAULTS, AND XILINX HEREBY DISCLAIMS ALL WARRANTIES
#  AND CONDITIONS, EXPRESS, IMPLIED, OR STATUTORY, INCLUDING
#  BUT NOT LIMITED TO WARRANTIES OF MERCHANTABILITY, NON-
#  INFRINGEMENT, OR FITNESS FOR ANY PARTICULAR PURPOSE; and
#  (2) Xilinx shall not be liable (whether in contract or tort,
#  including negligence, or under any other theory of
#  liability) for any loss or damage of any kind or nature
#  related to, arising under or in connection with these
#  materials, including for any direct, or any indirect,
#  special, incidental, or consequential loss or damage
#  (including loss of data, profits, goodwill, or any type of
#  loss or damage suffered as a result of any action brought
#  by a third party) even if such damage or loss was
#  reasonably foreseeable or Xilinx had been advised of the
#  possibility of the same.
#
#  CRITICAL APPLICATIONS
#  Xilinx products are not designed or intended to be fail-
#  safe, or for use in any application requiring fail-safe
#  performance, such as life-support or safety devices or
#  systems, Class III medical devices, nuclear facilities,
#  applications related to the deployment of airbags, or any
#  other applications that could lead to death, personal
#  injury, or severe property or environmental damage
#  (individually and collectively, "Critical
#  Applications"). Customer assumes the sole risk and
#  liability of any use of Xilinx products in Critical
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
set_property package_pin R34 [get_ports mgtrefclk1_x0y3_n]
set_property package_pin R33 [get_ports mgtrefclk1_x0y3_p]

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
set_property package_pin AR9 [get_ports hb_gtwiz_reset_clk_freerun_in_p]
set_property package_pin AR8 [get_ports hb_gtwiz_reset_clk_freerun_in_n]
set_property package_pin H22 [get_ports hb_gtwiz_reset_all_in]
set_property package_pin H21 [get_ports link_down_latched_reset_in]
set_property package_pin L19 [get_ports link_status_out]
set_property package_pin N21 [get_ports link_down_latched_out]

set_property iostandard DIFF_SSTL15 [get_ports hb_gtwiz_reset_clk_freerun_in_p]
set_property iostandard DIFF_SSTL15 [get_ports hb_gtwiz_reset_clk_freerun_in_n]
set_property iostandard LVCMOS18       [get_ports hb_gtwiz_reset_all_in]
set_property iostandard LVCMOS18       [get_ports link_down_latched_reset_in]
set_property iostandard LVCMOS18       [get_ports link_status_out]
set_property iostandard LVCMOS18       [get_ports link_down_latched_out]
# Clock constraints for clocks provided as inputs to the core
# Note: the IP core-level XDC constrains clocks produced by the core, which drive user clocks via helper blocks
# ----------------------------------------------------------------------------------------------------------------------
#create_clock -name clk_freerun -period 3.333 [get_ports hb_gtwiz_reset_clk_freerun_in_p]
create_clock -name clk_mgtrefclk1_x0y3_p -period 6.4 [get_ports mgtrefclk1_x0y3_p]

# False path constraints
# ----------------------------------------------------------------------------------------------------------------------
set_false_path -to [get_cells -hierarchical -filter {NAME =~ *bit_synchronizer*inst/i_in_meta_reg}]
set_false_path -to [get_cells -hierarchical -filter {NAME =~ *reset_synchronizer*inst/rst_in_*_reg}]
set_false_path -to [get_cells -hierarchical -filter {NAME =~ *gtwiz_userclk_tx_inst/*gtwiz_userclk_tx_active_*_reg}]
set_false_path -to [get_cells -hierarchical -filter {NAME =~ *gtwiz_userclk_rx_inst/*gtwiz_userclk_rx_active_*_reg}]

