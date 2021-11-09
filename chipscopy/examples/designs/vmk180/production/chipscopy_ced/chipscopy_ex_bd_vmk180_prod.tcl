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


################################################################
# This is a generated script based on design: chipscopy_ex
#
# Though there are limitations about the generated script,
# the main purpose of this utility is to make learning
# IP Integrator Tcl commands easier.
################################################################

namespace eval _tcl {
proc get_script_folder {} {
   set script_path [file normalize [info script]]
   set script_folder [file dirname $script_path]
   return $script_folder
}
}
variable script_folder
set script_folder [_tcl::get_script_folder]

################################################################
# Check if script is running in correct Vivado version.
################################################################
set scripts_vivado_version 2021.1
set current_vivado_version [version -short]

if { [string first $scripts_vivado_version $current_vivado_version] == -1 } {
   puts ""
   catch {common::send_gid_msg -ssname BD::TCL -id 2041 -severity "ERROR" "This script was generated using Vivado <$scripts_vivado_version> and is being run in <$current_vivado_version> of Vivado. Please run the script in Vivado <$scripts_vivado_version> then open the design in Vivado <$current_vivado_version>. Upgrade the design by running \"Tools => Report => Report IP Status...\", then run write_bd_tcl to create an updated script."}

   return 1
}

################################################################
# START
################################################################

# To test this script, run the following commands from Vivado Tcl console:
# source chipscopy_ex_script.tcl

# If there is no project opened, this script will create a
# project, but make sure you do not have an existing project
# <./myproj/project_1.xpr> in the current working folder.

set list_projs [get_projects -quiet]
if { $list_projs eq "" } {
   create_project project_1 myproj -part xcvm1802-vsva2197-2MP-e-S
   set_property BOARD_PART xilinx.com:vmk180:part0:2.2 [current_project]
}


# CHANGE DESIGN NAME HERE
variable design_name
set design_name chipscopy_ex

# If you do not already have an existing IP Integrator design open,
# you can create a design using the following command:
#    create_bd_design $design_name

# Creating design if needed
set errMsg ""
set nRet 0

set cur_design [current_bd_design -quiet]
set list_cells [get_bd_cells -quiet]

if { ${design_name} eq "" } {
   # USE CASES:
   #    1) Design_name not set

   set errMsg "Please set the variable <design_name> to a non-empty value."
   set nRet 1

} elseif { ${cur_design} ne "" && ${list_cells} eq "" } {
   # USE CASES:
   #    2): Current design opened AND is empty AND names same.
   #    3): Current design opened AND is empty AND names diff; design_name NOT in project.
   #    4): Current design opened AND is empty AND names diff; design_name exists in project.

   if { $cur_design ne $design_name } {
      common::send_gid_msg -ssname BD::TCL -id 2001 -severity "INFO" "Changing value of <design_name> from <$design_name> to <$cur_design> since current design is empty."
      set design_name [get_property NAME $cur_design]
   }
   common::send_gid_msg -ssname BD::TCL -id 2002 -severity "INFO" "Constructing design in IPI design <$cur_design>..."

} elseif { ${cur_design} ne "" && $list_cells ne "" && $cur_design eq $design_name } {
   # USE CASES:
   #    5) Current design opened AND has components AND same names.

   set errMsg "Design <$design_name> already exists in your project, please set the variable <design_name> to another value."
   set nRet 1
} elseif { [get_files -quiet ${design_name}.bd] ne "" } {
   # USE CASES: 
   #    6) Current opened design, has components, but diff names, design_name exists in project.
   #    7) No opened design, design_name exists in project.

   set errMsg "Design <$design_name> already exists in your project, please set the variable <design_name> to another value."
   set nRet 2

} else {
   # USE CASES:
   #    8) No opened design, design_name not in project.
   #    9) Current opened design, has components, but diff names, design_name not in project.

   common::send_gid_msg -ssname BD::TCL -id 2003 -severity "INFO" "Currently there is no design <$design_name> in project, so creating one..."

   create_bd_design $design_name

   common::send_gid_msg -ssname BD::TCL -id 2004 -severity "INFO" "Making design <$design_name> as current_bd_design."
   current_bd_design $design_name

}

  # Add USER_COMMENTS on $design_name
  set_property USER_COMMENTS.comment_0 "ChipScoPy Configurable Example Design (CED)
-----------------------------------------------------------------
This CED targets the vmk180 evaluation board and is designed 
to be used with the ChipScoPy API examples found at 
https://github.com/Xilinx/chipscopy

This design includes support for the following API examples:
- GTY transceivers for IBERT API examples
- DDR4 memory controller for DDRMC API examples
- SysMon voltage and temp sensors for SysMon API examples
- NoC, traffic generator, and BRAM controller for 
  NoC Perfmon API examples
- Binary counters and DDS cores for ILA and VIO API examples" [get_bd_designs $design_name]

common::send_gid_msg -ssname BD::TCL -id 2005 -severity "INFO" "Currently the variable <design_name> is equal to \"$design_name\"."

if { $nRet != 0 } {
   catch {common::send_gid_msg -ssname BD::TCL -id 2006 -severity "ERROR" $errMsg}
   return $nRet
}

set bCheckIPsPassed 1
##################################################################
# CHECK IPs
##################################################################
set bCheckIPs 1
if { $bCheckIPs == 1 } {
   set list_check_ips "\ 
xilinx.com:ip:axi_noc:1.0\
xilinx.com:ip:clk_wizard:1.0\
xilinx.com:ip:proc_sys_reset:5.0\
xilinx.com:ip:versal_cips:3.0\
xilinx.com:ip:xlconstant:1.1\
xilinx.com:ip:xlslice:1.0\
xilinx.com:ip:c_counter_binary:12.0\
xilinx.com:ip:dds_compiler:6.0\
xilinx.com:ip:axis_ila:1.1\
xilinx.com:ip:axis_vio:1.0\
xilinx.com:ip:gt_bridge_ip:1.1\
xilinx.com:ip:bufg_gt:1.0\
xilinx.com:ip:gt_quad_base:1.1\
xilinx.com:ip:util_reduced_logic:2.0\
xilinx.com:ip:util_ds_buf:2.2\
xilinx.com:ip:xlconcat:2.1\
xilinx.com:ip:axi_bram_ctrl:4.1\
xilinx.com:ip:emb_mem_gen:1.0\
xilinx.com:ip:sim_trig:1.0\
xilinx.com:ip:perf_axi_tg:1.0\
xilinx.com:ip:smartconnect:1.0\
"

   set list_ips_missing ""
   common::send_gid_msg -ssname BD::TCL -id 2011 -severity "INFO" "Checking if the following IPs exist in the project's IP catalog: $list_check_ips ."

   foreach ip_vlnv $list_check_ips {
      set ip_obj [get_ipdefs -all $ip_vlnv]
      if { $ip_obj eq "" } {
         lappend list_ips_missing $ip_vlnv
      }
   }

   if { $list_ips_missing ne "" } {
      catch {common::send_gid_msg -ssname BD::TCL -id 2012 -severity "ERROR" "The following IPs are not found in the IP Catalog:\n  $list_ips_missing\n\nResolution: Please add the repository containing the IP(s) to the project." }
      set bCheckIPsPassed 0
   }

}

if { $bCheckIPsPassed != 1 } {
  common::send_gid_msg -ssname BD::TCL -id 2023 -severity "WARNING" "Will not continue with creation of design due to the error(s) above."
  return 3
}

##################################################################
# DESIGN PROCs
##################################################################


# Hierarchical cell: noc_tg_bc
proc create_hier_cell_noc_tg_bc { parentCell nameHier } {

  variable script_folder

  if { $parentCell eq "" || $nameHier eq "" } {
     catch {common::send_gid_msg -ssname BD::TCL -id 2092 -severity "ERROR" "create_hier_cell_noc_tg_bc() - Empty argument(s)!"}
     return
  }

  # Get object for parentCell
  set parentObj [get_bd_cells $parentCell]
  if { $parentObj == "" } {
     catch {common::send_gid_msg -ssname BD::TCL -id 2090 -severity "ERROR" "Unable to find parent cell <$parentCell>!"}
     return
  }

  # Make sure parentObj is hier blk
  set parentType [get_property TYPE $parentObj]
  if { $parentType ne "hier" } {
     catch {common::send_gid_msg -ssname BD::TCL -id 2091 -severity "ERROR" "Parent <$parentObj> has TYPE = <$parentType>. Expected to be <hier>."}
     return
  }

  # Save current instance; Restore later
  set oldCurInst [current_bd_instance .]

  # Set parent object as current
  current_bd_instance $parentObj

  # Create cell and set as current instance
  set hier_obj [create_bd_cell -type hier $nameHier]
  current_bd_instance $hier_obj

  # Create interface pins
  create_bd_intf_pin -mode Master -vlnv xilinx.com:interface:aximm_rtl:1.0 M_AXI

  create_bd_intf_pin -mode Slave -vlnv xilinx.com:interface:aximm_rtl:1.0 S00_AXI

  create_bd_intf_pin -mode Slave -vlnv xilinx.com:interface:aximm_rtl:1.0 SLOT_0_AXI


  # Create pins
  create_bd_pin -dir I -type rst aresetn
  create_bd_pin -dir I -type clk clk
  create_bd_pin -dir I -type clk pclk
  create_bd_pin -dir I -type rst rst_n

  # Create instance: axis_vio_0, and set properties
  set axis_vio_0 [ create_bd_cell -type ip -vlnv xilinx.com:ip:axis_vio:1.0 axis_vio_0 ]
  set_property -dict [ list \
   CONFIG.C_NUM_PROBE_IN {2} \
   CONFIG.C_NUM_PROBE_OUT {2} \
 ] $axis_vio_0

  # Create instance: noc_bc, and set properties
  set noc_bc [ create_bd_cell -type ip -vlnv xilinx.com:ip:axi_bram_ctrl:4.1 noc_bc ]

  # Create instance: noc_bc_axis_ila_0, and set properties
  set noc_bc_axis_ila_0 [ create_bd_cell -type ip -vlnv xilinx.com:ip:axis_ila:1.1 noc_bc_axis_ila_0 ]
  set_property -dict [ list \
   CONFIG.C_ADV_TRIGGER {true} \
   CONFIG.C_BRAM_CNT {0} \
   CONFIG.C_INPUT_PIPE_STAGES {2} \
   CONFIG.C_MON_TYPE {Interface_Monitor} \
   CONFIG.C_SLOT_0_APC_EN {0} \
   CONFIG.C_SLOT_0_AXI_AR_SEL_DATA {1} \
   CONFIG.C_SLOT_0_AXI_AR_SEL_TRIG {1} \
   CONFIG.C_SLOT_0_AXI_AW_SEL_DATA {1} \
   CONFIG.C_SLOT_0_AXI_AW_SEL_TRIG {1} \
   CONFIG.C_SLOT_0_AXI_B_SEL_DATA {1} \
   CONFIG.C_SLOT_0_AXI_B_SEL_TRIG {1} \
   CONFIG.C_SLOT_0_AXI_R_SEL_DATA {1} \
   CONFIG.C_SLOT_0_AXI_R_SEL_TRIG {1} \
   CONFIG.C_SLOT_0_AXI_W_SEL_DATA {1} \
   CONFIG.C_SLOT_0_AXI_W_SEL_TRIG {1} \
   CONFIG.C_SLOT_0_TXN_CNTR_EN {0} \
 ] $noc_bc_axis_ila_0

  # Create instance: noc_bc_bram, and set properties
  set noc_bc_bram [ create_bd_cell -type ip -vlnv xilinx.com:ip:emb_mem_gen:1.0 noc_bc_bram ]
  set_property -dict [ list \
   CONFIG.MEMORY_TYPE {True_Dual_Port_RAM} \
 ] $noc_bc_bram

  # Create instance: noc_sim_trig, and set properties
  set noc_sim_trig [ create_bd_cell -type ip -vlnv xilinx.com:ip:sim_trig:1.0 noc_sim_trig ]
  set_property -dict [ list \
   CONFIG.USER_DEBUG_INTF {EXTERNAL_AXI4_LITE} \
   CONFIG.USER_TRAFFIC_SHAPING_EN {FALSE} \
 ] $noc_sim_trig

  # Create instance: noc_tg, and set properties
  set noc_tg [ create_bd_cell -type ip -vlnv xilinx.com:ip:perf_axi_tg:1.0 noc_tg ]
  set_property -dict [ list \
   CONFIG.USER_C_AXI_RDATA_WIDTH {512} \
   CONFIG.USER_C_AXI_READ_SIZE {1} \
   CONFIG.USER_C_AXI_WDATA_VALUE {0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000}\
   CONFIG.USER_C_AXI_WDATA_WIDTH {512} \
   CONFIG.USER_C_AXI_WRITE_SIZE {1} \
   CONFIG.USER_DEBUG_INTF {TRUE} \
   CONFIG.USER_PERF_TG {SYNTHESIZABLE} \
   CONFIG.USER_SYNTH_DEFINED_PATTERN_CSV ${script_folder}/empty_traffic_spec.csv \
   CONFIG.USER_TRAFFIC_SHAPING_EN {FALSE} \
 ] $noc_tg

  # Create instance: smartconnect_0, and set properties
  set smartconnect_0 [ create_bd_cell -type ip -vlnv xilinx.com:ip:smartconnect:1.0 smartconnect_0 ]
  set_property -dict [ list \
   CONFIG.NUM_MI {1} \
   CONFIG.NUM_SI {1} \
 ] $smartconnect_0

  # Create interface connections
  connect_bd_intf_net -intf_net Conn1 [get_bd_intf_pins S00_AXI] [get_bd_intf_pins smartconnect_0/S00_AXI]
  connect_bd_intf_net -intf_net SLOT_0_AXI_1 [get_bd_intf_pins SLOT_0_AXI] [get_bd_intf_pins noc_bc/S_AXI]
  connect_bd_intf_net -intf_net [get_bd_intf_nets SLOT_0_AXI_1] [get_bd_intf_pins SLOT_0_AXI] [get_bd_intf_pins noc_bc_axis_ila_0/SLOT_0_AXI]
  connect_bd_intf_net -intf_net noc_bc_BRAM_PORTA [get_bd_intf_pins noc_bc/BRAM_PORTA] [get_bd_intf_pins noc_bc_bram/BRAM_PORTA]
  connect_bd_intf_net -intf_net noc_bc_BRAM_PORTB [get_bd_intf_pins noc_bc/BRAM_PORTB] [get_bd_intf_pins noc_bc_bram/BRAM_PORTB]
  connect_bd_intf_net -intf_net noc_sim_trig_MCSIO_OUT_00 [get_bd_intf_pins noc_sim_trig/MCSIO_OUT_00] [get_bd_intf_pins noc_tg/MCSIO_IN]
  connect_bd_intf_net -intf_net noc_tg_M_AXI [get_bd_intf_pins M_AXI] [get_bd_intf_pins noc_tg/M_AXI]
  connect_bd_intf_net -intf_net smartconnect_0_M00_AXI [get_bd_intf_pins noc_sim_trig/AXI4_LITE] [get_bd_intf_pins smartconnect_0/M00_AXI]

  # Create port connections
  connect_bd_net -net aresetn_1 [get_bd_pins aresetn] [get_bd_pins smartconnect_0/aresetn]
  connect_bd_net -net noc_sim_trig_rst_n [get_bd_pins axis_vio_0/probe_out0] [get_bd_pins noc_sim_trig/rst_n]
  connect_bd_net -net noc_tg_tg_rst_n [get_bd_pins axis_vio_0/probe_out1] [get_bd_pins noc_tg/tg_rst_n]
  connect_bd_net -net clk_1 [get_bd_pins clk] [get_bd_pins noc_tg/clk]
  connect_bd_net -net noc_sim_trig_trig_00 [get_bd_pins noc_sim_trig/trig_00] [get_bd_pins noc_tg/axi_tg_start]
  connect_bd_net -net noc_tg_axi_tg_done [get_bd_pins axis_vio_0/probe_in0] [get_bd_pins noc_sim_trig/all_done_00] [get_bd_pins noc_tg/axi_tg_done]
  connect_bd_net -net noc_tg_axi_tg_error [get_bd_pins axis_vio_0/probe_in1] [get_bd_pins noc_tg/axi_tg_error]
  connect_bd_net -net proc_sys_reset_0_peripheral_aresetn [get_bd_pins rst_n] [get_bd_pins noc_bc/s_axi_aresetn] [get_bd_pins noc_bc_axis_ila_0/resetn]
  connect_bd_net -net versal_cips_0_pl0_ref_clk [get_bd_pins pclk] [get_bd_pins axis_vio_0/clk] [get_bd_pins noc_bc/s_axi_aclk] [get_bd_pins noc_bc_axis_ila_0/clk] [get_bd_pins noc_sim_trig/pclk] [get_bd_pins noc_tg/pclk] [get_bd_pins smartconnect_0/aclk]

  # Restore current instance
  current_bd_instance $oldCurInst
}

# Hierarchical cell: gty_quad_205
proc create_hier_cell_gty_quad_205 { parentCell nameHier } {

  variable script_folder

  if { $parentCell eq "" || $nameHier eq "" } {
     catch {common::send_gid_msg -ssname BD::TCL -id 2092 -severity "ERROR" "create_hier_cell_gty_quad_205() - Empty argument(s)!"}
     return
  }

  # Get object for parentCell
  set parentObj [get_bd_cells $parentCell]
  if { $parentObj == "" } {
     catch {common::send_gid_msg -ssname BD::TCL -id 2090 -severity "ERROR" "Unable to find parent cell <$parentCell>!"}
     return
  }

  # Make sure parentObj is hier blk
  set parentType [get_property TYPE $parentObj]
  if { $parentType ne "hier" } {
     catch {common::send_gid_msg -ssname BD::TCL -id 2091 -severity "ERROR" "Parent <$parentObj> has TYPE = <$parentType>. Expected to be <hier>."}
     return
  }

  # Save current instance; Restore later
  set oldCurInst [current_bd_instance .]

  # Set parent object as current
  current_bd_instance $parentObj

  # Create cell and set as current instance
  set hier_obj [create_bd_cell -type hier $nameHier]
  current_bd_instance $hier_obj

  # Create interface pins
  create_bd_intf_pin -mode Master -vlnv xilinx.com:interface:gt_rtl:1.0 GT_Serial_3

  create_bd_intf_pin -mode Slave -vlnv xilinx.com:interface:diff_clock_rtl:1.0 bridge_refclkX1Y10_diff_gt_ref_clock


  # Create pins
  create_bd_pin -dir I -type clk apb3clk

  # Create instance: bridge_refclkX1Y10, and set properties
  set bridge_refclkX1Y10 [ create_bd_cell -type ip -vlnv xilinx.com:ip:gt_bridge_ip:1.1 bridge_refclkX1Y10 ]
  set_property -dict [ list \
   CONFIG.IP_LR0_SETTINGS {GT_DIRECTION DUPLEX  GT_TYPE GTY  INS_LOSS_NYQ 20  INTERNAL_PRESET None \
OOB_ENABLE false  PCIE_ENABLE false  PCIE_USERCLK2_FREQ 250  PCIE_USERCLK_FREQ\
250  PRESET None  RESET_SEQUENCE_INTERVAL 0  RXPROGDIV_FREQ_ENABLE false \
RXPROGDIV_FREQ_SOURCE LCPLL  RXPROGDIV_FREQ_VAL 322.265625  RX_64B66B_CRC false\
RX_64B66B_DECODER false  RX_64B66B_DESCRAMBLER false \
RX_ACTUAL_REFCLK_FREQUENCY 100.000000000000  RX_BUFFER_BYPASS_MODE Fast_Sync \
RX_BUFFER_BYPASS_MODE_LANE MULTI  RX_BUFFER_MODE 1 \
RX_BUFFER_RESET_ON_CB_CHANGE ENABLE  RX_BUFFER_RESET_ON_COMMAALIGN DISABLE \
RX_BUFFER_RESET_ON_RATE_CHANGE ENABLE  RX_CB_DISP_0_0 false  RX_CB_DISP_0_1\
false  RX_CB_DISP_0_2 false  RX_CB_DISP_0_3 false  RX_CB_DISP_1_0 false \
RX_CB_DISP_1_1 false  RX_CB_DISP_1_2 false  RX_CB_DISP_1_3 false  RX_CB_K_0_0\
false  RX_CB_K_0_1 false  RX_CB_K_0_2 false  RX_CB_K_0_3 false  RX_CB_K_1_0\
false  RX_CB_K_1_1 false  RX_CB_K_1_2 false  RX_CB_K_1_3 false  RX_CB_LEN_SEQ 1\
RX_CB_MASK_0_0 false  RX_CB_MASK_0_1 false  RX_CB_MASK_0_2 false \
RX_CB_MASK_0_3 false  RX_CB_MASK_1_0 false  RX_CB_MASK_1_1 false \
RX_CB_MASK_1_2 false  RX_CB_MASK_1_3 false  RX_CB_MAX_LEVEL 1  RX_CB_MAX_SKEW 1\
RX_CB_NUM_SEQ 0  RX_CB_VAL_0_0 00000000  RX_CB_VAL_0_1 00000000  RX_CB_VAL_0_2\
00000000  RX_CB_VAL_0_3 00000000  RX_CB_VAL_1_0 00000000  RX_CB_VAL_1_1\
00000000  RX_CB_VAL_1_2 00000000  RX_CB_VAL_1_3 00000000  RX_CC_DISP_0_0 false \
RX_CC_DISP_0_1 false  RX_CC_DISP_0_2 false  RX_CC_DISP_0_3 false \
RX_CC_DISP_1_0 false  RX_CC_DISP_1_1 false  RX_CC_DISP_1_2 false \
RX_CC_DISP_1_3 false  RX_CC_KEEP_IDLE DISABLE  RX_CC_K_0_0 false  RX_CC_K_0_1\
false  RX_CC_K_0_2 false  RX_CC_K_0_3 false  RX_CC_K_1_0 false  RX_CC_K_1_1\
false  RX_CC_K_1_2 false  RX_CC_K_1_3 false  RX_CC_LEN_SEQ 1  RX_CC_MASK_0_0\
false  RX_CC_MASK_0_1 false  RX_CC_MASK_0_2 false  RX_CC_MASK_0_3 false \
RX_CC_MASK_1_0 false  RX_CC_MASK_1_1 false  RX_CC_MASK_1_2 false \
RX_CC_MASK_1_3 false  RX_CC_NUM_SEQ 0  RX_CC_PERIODICITY 5000  RX_CC_PRECEDENCE\
ENABLE  RX_CC_REPEAT_WAIT 0  RX_CC_VAL\
00000000000000000000000000000000000000000000000000000000000000000000000000000000\
RX_CC_VAL_0_0 00000000  RX_CC_VAL_0_1 00000000  RX_CC_VAL_0_2 00000000 \
RX_CC_VAL_0_3 00000000  RX_CC_VAL_1_0 00000000  RX_CC_VAL_1_1 00000000 \
RX_CC_VAL_1_2 00000000  RX_CC_VAL_1_3 00000000  RX_COMMA_ALIGN_WORD 1 \
RX_COMMA_DOUBLE_ENABLE false  RX_COMMA_MASK 0000000000  RX_COMMA_M_ENABLE false\
RX_COMMA_M_VAL 1010000011  RX_COMMA_PRESET NONE  RX_COMMA_P_ENABLE false \
RX_COMMA_P_VAL 0101111100  RX_COMMA_SHOW_REALIGN_ENABLE true \
RX_COMMA_VALID_ONLY 0  RX_COUPLING AC  RX_DATA_DECODING RAW  RX_EQ_MODE AUTO \
RX_FRACN_ENABLED false  RX_FRACN_NUMERATOR 0  RX_GRAY_BYP true \
RX_GRAY_LITTLEENDIAN true  RX_INT_DATA_WIDTH 64  RX_JTOL_FC 10 \
RX_JTOL_LF_SLOPE -20  RX_LINE_RATE 25  RX_OUTCLK_SOURCE RXOUTCLKPMA  RX_PAM_SEL\
NRZ  RX_PLL_TYPE LCPLL  RX_PPM_OFFSET 0  RX_PRECODE_BYP true \
RX_PRECODE_LITTLEENDIAN false  RX_RATE_GROUP A  RX_REFCLK_FREQUENCY 100 \
RX_REFCLK_SOURCE R0  RX_SLIDE_MODE OFF  RX_SSC_PPM 0  RX_TERMINATION\
PROGRAMMABLE  RX_TERMINATION_PROG_VALUE 800  RX_USER_DATA_WIDTH 64 \
TXPROGDIV_FREQ_ENABLE false  TXPROGDIV_FREQ_SOURCE LCPLL  TXPROGDIV_FREQ_VAL\
322.265625  TX_64B66B_CRC false  TX_64B66B_ENCODER false  TX_64B66B_SCRAMBLER\
false  TX_ACTUAL_REFCLK_FREQUENCY 100.000000000000  TX_BUFFER_BYPASS_MODE\
Fast_Sync  TX_BUFFER_MODE 1  TX_BUFFER_RESET_ON_RATE_CHANGE ENABLE \
TX_DATA_ENCODING RAW  TX_DIFF_SWING_EMPH_MODE CUSTOM  TX_FRACN_ENABLED false \
TX_FRACN_NUMERATOR 0  TX_GRAY_BYP true  TX_GRAY_LITTLEENDIAN true \
TX_INT_DATA_WIDTH 64  TX_LINE_RATE 25  TX_OUTCLK_SOURCE TXOUTCLKPMA  TX_PAM_SEL\
NRZ  TX_PIPM_ENABLE false  TX_PLL_TYPE LCPLL  TX_PRECODE_BYP true \
TX_PRECODE_LITTLEENDIAN false  TX_RATE_GROUP A  TX_REFCLK_FREQUENCY 100 \
TX_REFCLK_SOURCE R0  TX_USER_DATA_WIDTH 64}\
   CONFIG.IP_NO_OF_LANES {4} \
 ] $bridge_refclkX1Y10

  # Create instance: bufg_gt_6, and set properties
  set bufg_gt_6 [ create_bd_cell -type ip -vlnv xilinx.com:ip:bufg_gt:1.0 bufg_gt_6 ]

  # Create instance: bufg_gt_7, and set properties
  set bufg_gt_7 [ create_bd_cell -type ip -vlnv xilinx.com:ip:bufg_gt:1.0 bufg_gt_7 ]

  # Create instance: gt_quad_base_3, and set properties
  set gt_quad_base_3 [ create_bd_cell -type ip -vlnv xilinx.com:ip:gt_quad_base:1.1 gt_quad_base_3 ]
  set_property -dict [ list \
   CONFIG.PORTS_INFO_DICT {LANE_SEL_DICT {PROT0 {RX0 RX1 RX2 RX3 TX0 TX1 TX2 TX3}} GT_TYPE GTY\
REG_CONF_INTF APB3_INTF BOARD_INTERFACE false}\
   CONFIG.PROT1_LR0_SETTINGS {GT_TYPE GTY GT_DIRECTION DUPLEX INS_LOSS_NYQ 20 INTERNAL_PRESET None OOB_ENABLE\
false PCIE_ENABLE false PCIE_USERCLK2_FREQ 250 PCIE_USERCLK_FREQ 250 PRESET\
None RESET_SEQUENCE_INTERVAL 0 RXPROGDIV_FREQ_ENABLE false\
RXPROGDIV_FREQ_SOURCE LCPLL RXPROGDIV_FREQ_VAL 322.265625 RX_64B66B_CRC false\
RX_RATE_GROUP A RX_64B66B_DECODER false RX_64B66B_DESCRAMBLER false\
RX_ACTUAL_REFCLK_FREQUENCY 156.25 RX_BUFFER_BYPASS_MODE Fast_Sync\
RX_BUFFER_BYPASS_MODE_LANE MULTI RX_BUFFER_MODE 1 RX_BUFFER_RESET_ON_CB_CHANGE\
ENABLE RX_BUFFER_RESET_ON_COMMAALIGN DISABLE RX_BUFFER_RESET_ON_RATE_CHANGE\
ENABLE RX_CB_DISP_0_0 false RX_CB_DISP_0_1 false RX_CB_DISP_0_2 false\
RX_CB_DISP_0_3 false RX_CB_DISP_1_0 false RX_CB_DISP_1_1 false RX_CB_DISP_1_2\
false RX_CB_DISP_1_3 false RX_CB_K_0_0 false RX_CB_K_0_1 false RX_CB_K_0_2\
false RX_CB_K_0_3 false RX_CB_K_1_0 false RX_CB_K_1_1 false RX_CB_K_1_2 false\
RX_CB_K_1_3 false RX_CB_LEN_SEQ 1 RX_CB_MASK_0_0 false RX_CB_MASK_0_1 false\
RX_CB_MASK_0_2 false RX_CB_MASK_0_3 false RX_CB_MASK_1_0 false RX_CB_MASK_1_1\
false RX_CB_MASK_1_2 false RX_CB_MASK_1_3 false RX_CB_MAX_LEVEL 1\
RX_CB_MAX_SKEW 1 RX_CB_NUM_SEQ 0 RX_CB_VAL_0_0 00000000 RX_CB_VAL_0_1 00000000\
RX_CB_VAL_0_2 00000000 RX_CB_VAL_0_3 00000000 RX_CB_VAL_1_0 00000000\
RX_CB_VAL_1_1 00000000 RX_CB_VAL_1_2 00000000 RX_CB_VAL_1_3 00000000\
RX_CC_DISP_0_0 false RX_CC_DISP_0_1 false RX_CC_DISP_0_2 false RX_CC_DISP_0_3\
false RX_CC_DISP_1_0 false RX_CC_DISP_1_1 false RX_CC_DISP_1_2 false\
RX_CC_DISP_1_3 false RX_CC_KEEP_IDLE DISABLE RX_CC_K_0_0 false RX_CC_K_0_1\
false RX_CC_K_0_2 false RX_CC_K_0_3 false RX_CC_K_1_0 false RX_CC_K_1_1 false\
RX_CC_K_1_2 false RX_CC_K_1_3 false RX_CC_LEN_SEQ 1 RX_CC_MASK_0_0 false\
RX_CC_MASK_0_1 false RX_CC_MASK_0_2 false RX_CC_MASK_0_3 false RX_CC_MASK_1_0\
false RX_CC_MASK_1_1 false RX_CC_MASK_1_2 false RX_CC_MASK_1_3 false\
RX_CC_NUM_SEQ 0 RX_CC_PERIODICITY 5000 RX_CC_PRECEDENCE ENABLE\
RX_CC_REPEAT_WAIT 0 RX_CC_VAL\
00000000000000000000000000000000000000000000000000000000000000000000000000000000\
RX_CC_VAL_0_0 0000000000 RX_CC_VAL_0_1 0000000000 RX_CC_VAL_0_2 0000000000\
RX_CC_VAL_0_3 0000000000 RX_CC_VAL_1_0 0000000000 RX_CC_VAL_1_1 0000000000\
RX_CC_VAL_1_2 0000000000 RX_CC_VAL_1_3 0000000000 RX_COMMA_ALIGN_WORD 1\
RX_COMMA_DOUBLE_ENABLE false RX_COMMA_MASK 1111111111 RX_COMMA_M_ENABLE false\
RX_COMMA_M_VAL 1010000011 RX_COMMA_PRESET NONE RX_COMMA_P_ENABLE false\
RX_COMMA_P_VAL 0101111100 RX_COMMA_SHOW_REALIGN_ENABLE true RX_COMMA_VALID_ONLY\
0 RX_COUPLING AC RX_DATA_DECODING RAW RX_EQ_MODE AUTO RX_FRACN_ENABLED false\
RX_FRACN_NUMERATOR 0 RX_INT_DATA_WIDTH 32 RX_JTOL_FC 0 RX_JTOL_LF_SLOPE -20\
RX_LINE_RATE 10.3125 RX_OUTCLK_SOURCE RXOUTCLKPMA RX_PLL_TYPE LCPLL\
RX_PPM_OFFSET 0 RX_REFCLK_FREQUENCY 156.25 RX_REFCLK_SOURCE R0 RX_SLIDE_MODE\
OFF RX_SSC_PPM 0 RX_TERMINATION PROGRAMMABLE RX_TERMINATION_PROG_VALUE 800\
RX_USER_DATA_WIDTH 32 TXPROGDIV_FREQ_ENABLE false TXPROGDIV_FREQ_SOURCE LCPLL\
TXPROGDIV_FREQ_VAL 322.265625 TX_64B66B_CRC false TX_RATE_GROUP A\
TX_64B66B_ENCODER false TX_64B66B_SCRAMBLER false TX_ACTUAL_REFCLK_FREQUENCY\
156.25 TX_BUFFER_BYPASS_MODE Fast_Sync TX_BUFFER_MODE 1\
TX_BUFFER_RESET_ON_RATE_CHANGE ENABLE TX_DATA_ENCODING RAW\
TX_DIFF_SWING_EMPH_MODE CUSTOM TX_FRACN_ENABLED false TX_FRACN_NUMERATOR 0\
TX_INT_DATA_WIDTH 32 TX_LINE_RATE 10.3125 TX_OUTCLK_SOURCE TXOUTCLKPMA\
TX_PIPM_ENABLE false TX_PLL_TYPE LCPLL TX_REFCLK_FREQUENCY 156.25\
TX_REFCLK_SOURCE R0 TX_USER_DATA_WIDTH 32}\
   CONFIG.PROT2_LR0_SETTINGS {GT_TYPE GTY GT_DIRECTION DUPLEX INS_LOSS_NYQ 20 INTERNAL_PRESET None OOB_ENABLE\
false PCIE_ENABLE false PCIE_USERCLK2_FREQ 250 PCIE_USERCLK_FREQ 250 PRESET\
None RESET_SEQUENCE_INTERVAL 0 RXPROGDIV_FREQ_ENABLE false\
RXPROGDIV_FREQ_SOURCE LCPLL RXPROGDIV_FREQ_VAL 322.265625 RX_64B66B_CRC false\
RX_RATE_GROUP A RX_64B66B_DECODER false RX_64B66B_DESCRAMBLER false\
RX_ACTUAL_REFCLK_FREQUENCY 156.25 RX_BUFFER_BYPASS_MODE Fast_Sync\
RX_BUFFER_BYPASS_MODE_LANE MULTI RX_BUFFER_MODE 1 RX_BUFFER_RESET_ON_CB_CHANGE\
ENABLE RX_BUFFER_RESET_ON_COMMAALIGN DISABLE RX_BUFFER_RESET_ON_RATE_CHANGE\
ENABLE RX_CB_DISP_0_0 false RX_CB_DISP_0_1 false RX_CB_DISP_0_2 false\
RX_CB_DISP_0_3 false RX_CB_DISP_1_0 false RX_CB_DISP_1_1 false RX_CB_DISP_1_2\
false RX_CB_DISP_1_3 false RX_CB_K_0_0 false RX_CB_K_0_1 false RX_CB_K_0_2\
false RX_CB_K_0_3 false RX_CB_K_1_0 false RX_CB_K_1_1 false RX_CB_K_1_2 false\
RX_CB_K_1_3 false RX_CB_LEN_SEQ 1 RX_CB_MASK_0_0 false RX_CB_MASK_0_1 false\
RX_CB_MASK_0_2 false RX_CB_MASK_0_3 false RX_CB_MASK_1_0 false RX_CB_MASK_1_1\
false RX_CB_MASK_1_2 false RX_CB_MASK_1_3 false RX_CB_MAX_LEVEL 1\
RX_CB_MAX_SKEW 1 RX_CB_NUM_SEQ 0 RX_CB_VAL_0_0 00000000 RX_CB_VAL_0_1 00000000\
RX_CB_VAL_0_2 00000000 RX_CB_VAL_0_3 00000000 RX_CB_VAL_1_0 00000000\
RX_CB_VAL_1_1 00000000 RX_CB_VAL_1_2 00000000 RX_CB_VAL_1_3 00000000\
RX_CC_DISP_0_0 false RX_CC_DISP_0_1 false RX_CC_DISP_0_2 false RX_CC_DISP_0_3\
false RX_CC_DISP_1_0 false RX_CC_DISP_1_1 false RX_CC_DISP_1_2 false\
RX_CC_DISP_1_3 false RX_CC_KEEP_IDLE DISABLE RX_CC_K_0_0 false RX_CC_K_0_1\
false RX_CC_K_0_2 false RX_CC_K_0_3 false RX_CC_K_1_0 false RX_CC_K_1_1 false\
RX_CC_K_1_2 false RX_CC_K_1_3 false RX_CC_LEN_SEQ 1 RX_CC_MASK_0_0 false\
RX_CC_MASK_0_1 false RX_CC_MASK_0_2 false RX_CC_MASK_0_3 false RX_CC_MASK_1_0\
false RX_CC_MASK_1_1 false RX_CC_MASK_1_2 false RX_CC_MASK_1_3 false\
RX_CC_NUM_SEQ 0 RX_CC_PERIODICITY 5000 RX_CC_PRECEDENCE ENABLE\
RX_CC_REPEAT_WAIT 0 RX_CC_VAL\
00000000000000000000000000000000000000000000000000000000000000000000000000000000\
RX_CC_VAL_0_0 0000000000 RX_CC_VAL_0_1 0000000000 RX_CC_VAL_0_2 0000000000\
RX_CC_VAL_0_3 0000000000 RX_CC_VAL_1_0 0000000000 RX_CC_VAL_1_1 0000000000\
RX_CC_VAL_1_2 0000000000 RX_CC_VAL_1_3 0000000000 RX_COMMA_ALIGN_WORD 1\
RX_COMMA_DOUBLE_ENABLE false RX_COMMA_MASK 1111111111 RX_COMMA_M_ENABLE false\
RX_COMMA_M_VAL 1010000011 RX_COMMA_PRESET NONE RX_COMMA_P_ENABLE false\
RX_COMMA_P_VAL 0101111100 RX_COMMA_SHOW_REALIGN_ENABLE true RX_COMMA_VALID_ONLY\
0 RX_COUPLING AC RX_DATA_DECODING RAW RX_EQ_MODE AUTO RX_FRACN_ENABLED false\
RX_FRACN_NUMERATOR 0 RX_INT_DATA_WIDTH 32 RX_JTOL_FC 0 RX_JTOL_LF_SLOPE -20\
RX_LINE_RATE 10.3125 RX_OUTCLK_SOURCE RXOUTCLKPMA RX_PLL_TYPE LCPLL\
RX_PPM_OFFSET 0 RX_REFCLK_FREQUENCY 156.25 RX_REFCLK_SOURCE R0 RX_SLIDE_MODE\
OFF RX_SSC_PPM 0 RX_TERMINATION PROGRAMMABLE RX_TERMINATION_PROG_VALUE 800\
RX_USER_DATA_WIDTH 32 TXPROGDIV_FREQ_ENABLE false TXPROGDIV_FREQ_SOURCE LCPLL\
TXPROGDIV_FREQ_VAL 322.265625 TX_64B66B_CRC false TX_RATE_GROUP A\
TX_64B66B_ENCODER false TX_64B66B_SCRAMBLER false TX_ACTUAL_REFCLK_FREQUENCY\
156.25 TX_BUFFER_BYPASS_MODE Fast_Sync TX_BUFFER_MODE 1\
TX_BUFFER_RESET_ON_RATE_CHANGE ENABLE TX_DATA_ENCODING RAW\
TX_DIFF_SWING_EMPH_MODE CUSTOM TX_FRACN_ENABLED false TX_FRACN_NUMERATOR 0\
TX_INT_DATA_WIDTH 32 TX_LINE_RATE 10.3125 TX_OUTCLK_SOURCE TXOUTCLKPMA\
TX_PIPM_ENABLE false TX_PLL_TYPE LCPLL TX_REFCLK_FREQUENCY 156.25\
TX_REFCLK_SOURCE R0 TX_USER_DATA_WIDTH 32}\
   CONFIG.PROT3_LR0_SETTINGS {GT_TYPE GTY GT_DIRECTION DUPLEX INS_LOSS_NYQ 20 INTERNAL_PRESET None OOB_ENABLE\
false PCIE_ENABLE false PCIE_USERCLK2_FREQ 250 PCIE_USERCLK_FREQ 250 PRESET\
None RESET_SEQUENCE_INTERVAL 0 RXPROGDIV_FREQ_ENABLE false\
RXPROGDIV_FREQ_SOURCE LCPLL RXPROGDIV_FREQ_VAL 322.265625 RX_64B66B_CRC false\
RX_RATE_GROUP A RX_64B66B_DECODER false RX_64B66B_DESCRAMBLER false\
RX_ACTUAL_REFCLK_FREQUENCY 156.25 RX_BUFFER_BYPASS_MODE Fast_Sync\
RX_BUFFER_BYPASS_MODE_LANE MULTI RX_BUFFER_MODE 1 RX_BUFFER_RESET_ON_CB_CHANGE\
ENABLE RX_BUFFER_RESET_ON_COMMAALIGN DISABLE RX_BUFFER_RESET_ON_RATE_CHANGE\
ENABLE RX_CB_DISP_0_0 false RX_CB_DISP_0_1 false RX_CB_DISP_0_2 false\
RX_CB_DISP_0_3 false RX_CB_DISP_1_0 false RX_CB_DISP_1_1 false RX_CB_DISP_1_2\
false RX_CB_DISP_1_3 false RX_CB_K_0_0 false RX_CB_K_0_1 false RX_CB_K_0_2\
false RX_CB_K_0_3 false RX_CB_K_1_0 false RX_CB_K_1_1 false RX_CB_K_1_2 false\
RX_CB_K_1_3 false RX_CB_LEN_SEQ 1 RX_CB_MASK_0_0 false RX_CB_MASK_0_1 false\
RX_CB_MASK_0_2 false RX_CB_MASK_0_3 false RX_CB_MASK_1_0 false RX_CB_MASK_1_1\
false RX_CB_MASK_1_2 false RX_CB_MASK_1_3 false RX_CB_MAX_LEVEL 1\
RX_CB_MAX_SKEW 1 RX_CB_NUM_SEQ 0 RX_CB_VAL_0_0 00000000 RX_CB_VAL_0_1 00000000\
RX_CB_VAL_0_2 00000000 RX_CB_VAL_0_3 00000000 RX_CB_VAL_1_0 00000000\
RX_CB_VAL_1_1 00000000 RX_CB_VAL_1_2 00000000 RX_CB_VAL_1_3 00000000\
RX_CC_DISP_0_0 false RX_CC_DISP_0_1 false RX_CC_DISP_0_2 false RX_CC_DISP_0_3\
false RX_CC_DISP_1_0 false RX_CC_DISP_1_1 false RX_CC_DISP_1_2 false\
RX_CC_DISP_1_3 false RX_CC_KEEP_IDLE DISABLE RX_CC_K_0_0 false RX_CC_K_0_1\
false RX_CC_K_0_2 false RX_CC_K_0_3 false RX_CC_K_1_0 false RX_CC_K_1_1 false\
RX_CC_K_1_2 false RX_CC_K_1_3 false RX_CC_LEN_SEQ 1 RX_CC_MASK_0_0 false\
RX_CC_MASK_0_1 false RX_CC_MASK_0_2 false RX_CC_MASK_0_3 false RX_CC_MASK_1_0\
false RX_CC_MASK_1_1 false RX_CC_MASK_1_2 false RX_CC_MASK_1_3 false\
RX_CC_NUM_SEQ 0 RX_CC_PERIODICITY 5000 RX_CC_PRECEDENCE ENABLE\
RX_CC_REPEAT_WAIT 0 RX_CC_VAL\
00000000000000000000000000000000000000000000000000000000000000000000000000000000\
RX_CC_VAL_0_0 0000000000 RX_CC_VAL_0_1 0000000000 RX_CC_VAL_0_2 0000000000\
RX_CC_VAL_0_3 0000000000 RX_CC_VAL_1_0 0000000000 RX_CC_VAL_1_1 0000000000\
RX_CC_VAL_1_2 0000000000 RX_CC_VAL_1_3 0000000000 RX_COMMA_ALIGN_WORD 1\
RX_COMMA_DOUBLE_ENABLE false RX_COMMA_MASK 1111111111 RX_COMMA_M_ENABLE false\
RX_COMMA_M_VAL 1010000011 RX_COMMA_PRESET NONE RX_COMMA_P_ENABLE false\
RX_COMMA_P_VAL 0101111100 RX_COMMA_SHOW_REALIGN_ENABLE true RX_COMMA_VALID_ONLY\
0 RX_COUPLING AC RX_DATA_DECODING RAW RX_EQ_MODE AUTO RX_FRACN_ENABLED false\
RX_FRACN_NUMERATOR 0 RX_INT_DATA_WIDTH 32 RX_JTOL_FC 0 RX_JTOL_LF_SLOPE -20\
RX_LINE_RATE 10.3125 RX_OUTCLK_SOURCE RXOUTCLKPMA RX_PLL_TYPE LCPLL\
RX_PPM_OFFSET 0 RX_REFCLK_FREQUENCY 156.25 RX_REFCLK_SOURCE R0 RX_SLIDE_MODE\
OFF RX_SSC_PPM 0 RX_TERMINATION PROGRAMMABLE RX_TERMINATION_PROG_VALUE 800\
RX_USER_DATA_WIDTH 32 TXPROGDIV_FREQ_ENABLE false TXPROGDIV_FREQ_SOURCE LCPLL\
TXPROGDIV_FREQ_VAL 322.265625 TX_64B66B_CRC false TX_RATE_GROUP A\
TX_64B66B_ENCODER false TX_64B66B_SCRAMBLER false TX_ACTUAL_REFCLK_FREQUENCY\
156.25 TX_BUFFER_BYPASS_MODE Fast_Sync TX_BUFFER_MODE 1\
TX_BUFFER_RESET_ON_RATE_CHANGE ENABLE TX_DATA_ENCODING RAW\
TX_DIFF_SWING_EMPH_MODE CUSTOM TX_FRACN_ENABLED false TX_FRACN_NUMERATOR 0\
TX_INT_DATA_WIDTH 32 TX_LINE_RATE 10.3125 TX_OUTCLK_SOURCE TXOUTCLKPMA\
TX_PIPM_ENABLE false TX_PLL_TYPE LCPLL TX_REFCLK_FREQUENCY 156.25\
TX_REFCLK_SOURCE R0 TX_USER_DATA_WIDTH 32}\
   CONFIG.PROT4_LR0_SETTINGS {GT_TYPE GTY GT_DIRECTION DUPLEX INS_LOSS_NYQ 20 INTERNAL_PRESET None OOB_ENABLE\
false PCIE_ENABLE false PCIE_USERCLK2_FREQ 250 PCIE_USERCLK_FREQ 250 PRESET\
None RESET_SEQUENCE_INTERVAL 0 RXPROGDIV_FREQ_ENABLE false\
RXPROGDIV_FREQ_SOURCE LCPLL RXPROGDIV_FREQ_VAL 322.265625 RX_64B66B_CRC false\
RX_RATE_GROUP A RX_64B66B_DECODER false RX_64B66B_DESCRAMBLER false\
RX_ACTUAL_REFCLK_FREQUENCY 156.25 RX_BUFFER_BYPASS_MODE Fast_Sync\
RX_BUFFER_BYPASS_MODE_LANE MULTI RX_BUFFER_MODE 1 RX_BUFFER_RESET_ON_CB_CHANGE\
ENABLE RX_BUFFER_RESET_ON_COMMAALIGN DISABLE RX_BUFFER_RESET_ON_RATE_CHANGE\
ENABLE RX_CB_DISP_0_0 false RX_CB_DISP_0_1 false RX_CB_DISP_0_2 false\
RX_CB_DISP_0_3 false RX_CB_DISP_1_0 false RX_CB_DISP_1_1 false RX_CB_DISP_1_2\
false RX_CB_DISP_1_3 false RX_CB_K_0_0 false RX_CB_K_0_1 false RX_CB_K_0_2\
false RX_CB_K_0_3 false RX_CB_K_1_0 false RX_CB_K_1_1 false RX_CB_K_1_2 false\
RX_CB_K_1_3 false RX_CB_LEN_SEQ 1 RX_CB_MASK_0_0 false RX_CB_MASK_0_1 false\
RX_CB_MASK_0_2 false RX_CB_MASK_0_3 false RX_CB_MASK_1_0 false RX_CB_MASK_1_1\
false RX_CB_MASK_1_2 false RX_CB_MASK_1_3 false RX_CB_MAX_LEVEL 1\
RX_CB_MAX_SKEW 1 RX_CB_NUM_SEQ 0 RX_CB_VAL_0_0 00000000 RX_CB_VAL_0_1 00000000\
RX_CB_VAL_0_2 00000000 RX_CB_VAL_0_3 00000000 RX_CB_VAL_1_0 00000000\
RX_CB_VAL_1_1 00000000 RX_CB_VAL_1_2 00000000 RX_CB_VAL_1_3 00000000\
RX_CC_DISP_0_0 false RX_CC_DISP_0_1 false RX_CC_DISP_0_2 false RX_CC_DISP_0_3\
false RX_CC_DISP_1_0 false RX_CC_DISP_1_1 false RX_CC_DISP_1_2 false\
RX_CC_DISP_1_3 false RX_CC_KEEP_IDLE DISABLE RX_CC_K_0_0 false RX_CC_K_0_1\
false RX_CC_K_0_2 false RX_CC_K_0_3 false RX_CC_K_1_0 false RX_CC_K_1_1 false\
RX_CC_K_1_2 false RX_CC_K_1_3 false RX_CC_LEN_SEQ 1 RX_CC_MASK_0_0 false\
RX_CC_MASK_0_1 false RX_CC_MASK_0_2 false RX_CC_MASK_0_3 false RX_CC_MASK_1_0\
false RX_CC_MASK_1_1 false RX_CC_MASK_1_2 false RX_CC_MASK_1_3 false\
RX_CC_NUM_SEQ 0 RX_CC_PERIODICITY 5000 RX_CC_PRECEDENCE ENABLE\
RX_CC_REPEAT_WAIT 0 RX_CC_VAL\
00000000000000000000000000000000000000000000000000000000000000000000000000000000\
RX_CC_VAL_0_0 0000000000 RX_CC_VAL_0_1 0000000000 RX_CC_VAL_0_2 0000000000\
RX_CC_VAL_0_3 0000000000 RX_CC_VAL_1_0 0000000000 RX_CC_VAL_1_1 0000000000\
RX_CC_VAL_1_2 0000000000 RX_CC_VAL_1_3 0000000000 RX_COMMA_ALIGN_WORD 1\
RX_COMMA_DOUBLE_ENABLE false RX_COMMA_MASK 1111111111 RX_COMMA_M_ENABLE false\
RX_COMMA_M_VAL 1010000011 RX_COMMA_PRESET NONE RX_COMMA_P_ENABLE false\
RX_COMMA_P_VAL 0101111100 RX_COMMA_SHOW_REALIGN_ENABLE true RX_COMMA_VALID_ONLY\
0 RX_COUPLING AC RX_DATA_DECODING RAW RX_EQ_MODE AUTO RX_FRACN_ENABLED false\
RX_FRACN_NUMERATOR 0 RX_INT_DATA_WIDTH 32 RX_JTOL_FC 0 RX_JTOL_LF_SLOPE -20\
RX_LINE_RATE 10.3125 RX_OUTCLK_SOURCE RXOUTCLKPMA RX_PLL_TYPE LCPLL\
RX_PPM_OFFSET 0 RX_REFCLK_FREQUENCY 156.25 RX_REFCLK_SOURCE R0 RX_SLIDE_MODE\
OFF RX_SSC_PPM 0 RX_TERMINATION PROGRAMMABLE RX_TERMINATION_PROG_VALUE 800\
RX_USER_DATA_WIDTH 32 TXPROGDIV_FREQ_ENABLE false TXPROGDIV_FREQ_SOURCE LCPLL\
TXPROGDIV_FREQ_VAL 322.265625 TX_64B66B_CRC false TX_RATE_GROUP A\
TX_64B66B_ENCODER false TX_64B66B_SCRAMBLER false TX_ACTUAL_REFCLK_FREQUENCY\
156.25 TX_BUFFER_BYPASS_MODE Fast_Sync TX_BUFFER_MODE 1\
TX_BUFFER_RESET_ON_RATE_CHANGE ENABLE TX_DATA_ENCODING RAW\
TX_DIFF_SWING_EMPH_MODE CUSTOM TX_FRACN_ENABLED false TX_FRACN_NUMERATOR 0\
TX_INT_DATA_WIDTH 32 TX_LINE_RATE 10.3125 TX_OUTCLK_SOURCE TXOUTCLKPMA\
TX_PIPM_ENABLE false TX_PLL_TYPE LCPLL TX_REFCLK_FREQUENCY 156.25\
TX_REFCLK_SOURCE R0 TX_USER_DATA_WIDTH 32}\
   CONFIG.PROT5_LR0_SETTINGS {GT_TYPE GTY GT_DIRECTION DUPLEX INS_LOSS_NYQ 20 INTERNAL_PRESET None OOB_ENABLE\
false PCIE_ENABLE false PCIE_USERCLK2_FREQ 250 PCIE_USERCLK_FREQ 250 PRESET\
None RESET_SEQUENCE_INTERVAL 0 RXPROGDIV_FREQ_ENABLE false\
RXPROGDIV_FREQ_SOURCE LCPLL RXPROGDIV_FREQ_VAL 322.265625 RX_64B66B_CRC false\
RX_RATE_GROUP A RX_64B66B_DECODER false RX_64B66B_DESCRAMBLER false\
RX_ACTUAL_REFCLK_FREQUENCY 156.25 RX_BUFFER_BYPASS_MODE Fast_Sync\
RX_BUFFER_BYPASS_MODE_LANE MULTI RX_BUFFER_MODE 1 RX_BUFFER_RESET_ON_CB_CHANGE\
ENABLE RX_BUFFER_RESET_ON_COMMAALIGN DISABLE RX_BUFFER_RESET_ON_RATE_CHANGE\
ENABLE RX_CB_DISP_0_0 false RX_CB_DISP_0_1 false RX_CB_DISP_0_2 false\
RX_CB_DISP_0_3 false RX_CB_DISP_1_0 false RX_CB_DISP_1_1 false RX_CB_DISP_1_2\
false RX_CB_DISP_1_3 false RX_CB_K_0_0 false RX_CB_K_0_1 false RX_CB_K_0_2\
false RX_CB_K_0_3 false RX_CB_K_1_0 false RX_CB_K_1_1 false RX_CB_K_1_2 false\
RX_CB_K_1_3 false RX_CB_LEN_SEQ 1 RX_CB_MASK_0_0 false RX_CB_MASK_0_1 false\
RX_CB_MASK_0_2 false RX_CB_MASK_0_3 false RX_CB_MASK_1_0 false RX_CB_MASK_1_1\
false RX_CB_MASK_1_2 false RX_CB_MASK_1_3 false RX_CB_MAX_LEVEL 1\
RX_CB_MAX_SKEW 1 RX_CB_NUM_SEQ 0 RX_CB_VAL_0_0 00000000 RX_CB_VAL_0_1 00000000\
RX_CB_VAL_0_2 00000000 RX_CB_VAL_0_3 00000000 RX_CB_VAL_1_0 00000000\
RX_CB_VAL_1_1 00000000 RX_CB_VAL_1_2 00000000 RX_CB_VAL_1_3 00000000\
RX_CC_DISP_0_0 false RX_CC_DISP_0_1 false RX_CC_DISP_0_2 false RX_CC_DISP_0_3\
false RX_CC_DISP_1_0 false RX_CC_DISP_1_1 false RX_CC_DISP_1_2 false\
RX_CC_DISP_1_3 false RX_CC_KEEP_IDLE DISABLE RX_CC_K_0_0 false RX_CC_K_0_1\
false RX_CC_K_0_2 false RX_CC_K_0_3 false RX_CC_K_1_0 false RX_CC_K_1_1 false\
RX_CC_K_1_2 false RX_CC_K_1_3 false RX_CC_LEN_SEQ 1 RX_CC_MASK_0_0 false\
RX_CC_MASK_0_1 false RX_CC_MASK_0_2 false RX_CC_MASK_0_3 false RX_CC_MASK_1_0\
false RX_CC_MASK_1_1 false RX_CC_MASK_1_2 false RX_CC_MASK_1_3 false\
RX_CC_NUM_SEQ 0 RX_CC_PERIODICITY 5000 RX_CC_PRECEDENCE ENABLE\
RX_CC_REPEAT_WAIT 0 RX_CC_VAL\
00000000000000000000000000000000000000000000000000000000000000000000000000000000\
RX_CC_VAL_0_0 0000000000 RX_CC_VAL_0_1 0000000000 RX_CC_VAL_0_2 0000000000\
RX_CC_VAL_0_3 0000000000 RX_CC_VAL_1_0 0000000000 RX_CC_VAL_1_1 0000000000\
RX_CC_VAL_1_2 0000000000 RX_CC_VAL_1_3 0000000000 RX_COMMA_ALIGN_WORD 1\
RX_COMMA_DOUBLE_ENABLE false RX_COMMA_MASK 1111111111 RX_COMMA_M_ENABLE false\
RX_COMMA_M_VAL 1010000011 RX_COMMA_PRESET NONE RX_COMMA_P_ENABLE false\
RX_COMMA_P_VAL 0101111100 RX_COMMA_SHOW_REALIGN_ENABLE true RX_COMMA_VALID_ONLY\
0 RX_COUPLING AC RX_DATA_DECODING RAW RX_EQ_MODE AUTO RX_FRACN_ENABLED false\
RX_FRACN_NUMERATOR 0 RX_INT_DATA_WIDTH 32 RX_JTOL_FC 0 RX_JTOL_LF_SLOPE -20\
RX_LINE_RATE 10.3125 RX_OUTCLK_SOURCE RXOUTCLKPMA RX_PLL_TYPE LCPLL\
RX_PPM_OFFSET 0 RX_REFCLK_FREQUENCY 156.25 RX_REFCLK_SOURCE R0 RX_SLIDE_MODE\
OFF RX_SSC_PPM 0 RX_TERMINATION PROGRAMMABLE RX_TERMINATION_PROG_VALUE 800\
RX_USER_DATA_WIDTH 32 TXPROGDIV_FREQ_ENABLE false TXPROGDIV_FREQ_SOURCE LCPLL\
TXPROGDIV_FREQ_VAL 322.265625 TX_64B66B_CRC false TX_RATE_GROUP A\
TX_64B66B_ENCODER false TX_64B66B_SCRAMBLER false TX_ACTUAL_REFCLK_FREQUENCY\
156.25 TX_BUFFER_BYPASS_MODE Fast_Sync TX_BUFFER_MODE 1\
TX_BUFFER_RESET_ON_RATE_CHANGE ENABLE TX_DATA_ENCODING RAW\
TX_DIFF_SWING_EMPH_MODE CUSTOM TX_FRACN_ENABLED false TX_FRACN_NUMERATOR 0\
TX_INT_DATA_WIDTH 32 TX_LINE_RATE 10.3125 TX_OUTCLK_SOURCE TXOUTCLKPMA\
TX_PIPM_ENABLE false TX_PLL_TYPE LCPLL TX_REFCLK_FREQUENCY 156.25\
TX_REFCLK_SOURCE R0 TX_USER_DATA_WIDTH 32}\
   CONFIG.PROT6_LR0_SETTINGS {GT_TYPE GTY GT_DIRECTION DUPLEX INS_LOSS_NYQ 20 INTERNAL_PRESET None OOB_ENABLE\
false PCIE_ENABLE false PCIE_USERCLK2_FREQ 250 PCIE_USERCLK_FREQ 250 PRESET\
None RESET_SEQUENCE_INTERVAL 0 RXPROGDIV_FREQ_ENABLE false\
RXPROGDIV_FREQ_SOURCE LCPLL RXPROGDIV_FREQ_VAL 322.265625 RX_64B66B_CRC false\
RX_RATE_GROUP A RX_64B66B_DECODER false RX_64B66B_DESCRAMBLER false\
RX_ACTUAL_REFCLK_FREQUENCY 156.25 RX_BUFFER_BYPASS_MODE Fast_Sync\
RX_BUFFER_BYPASS_MODE_LANE MULTI RX_BUFFER_MODE 1 RX_BUFFER_RESET_ON_CB_CHANGE\
ENABLE RX_BUFFER_RESET_ON_COMMAALIGN DISABLE RX_BUFFER_RESET_ON_RATE_CHANGE\
ENABLE RX_CB_DISP_0_0 false RX_CB_DISP_0_1 false RX_CB_DISP_0_2 false\
RX_CB_DISP_0_3 false RX_CB_DISP_1_0 false RX_CB_DISP_1_1 false RX_CB_DISP_1_2\
false RX_CB_DISP_1_3 false RX_CB_K_0_0 false RX_CB_K_0_1 false RX_CB_K_0_2\
false RX_CB_K_0_3 false RX_CB_K_1_0 false RX_CB_K_1_1 false RX_CB_K_1_2 false\
RX_CB_K_1_3 false RX_CB_LEN_SEQ 1 RX_CB_MASK_0_0 false RX_CB_MASK_0_1 false\
RX_CB_MASK_0_2 false RX_CB_MASK_0_3 false RX_CB_MASK_1_0 false RX_CB_MASK_1_1\
false RX_CB_MASK_1_2 false RX_CB_MASK_1_3 false RX_CB_MAX_LEVEL 1\
RX_CB_MAX_SKEW 1 RX_CB_NUM_SEQ 0 RX_CB_VAL_0_0 00000000 RX_CB_VAL_0_1 00000000\
RX_CB_VAL_0_2 00000000 RX_CB_VAL_0_3 00000000 RX_CB_VAL_1_0 00000000\
RX_CB_VAL_1_1 00000000 RX_CB_VAL_1_2 00000000 RX_CB_VAL_1_3 00000000\
RX_CC_DISP_0_0 false RX_CC_DISP_0_1 false RX_CC_DISP_0_2 false RX_CC_DISP_0_3\
false RX_CC_DISP_1_0 false RX_CC_DISP_1_1 false RX_CC_DISP_1_2 false\
RX_CC_DISP_1_3 false RX_CC_KEEP_IDLE DISABLE RX_CC_K_0_0 false RX_CC_K_0_1\
false RX_CC_K_0_2 false RX_CC_K_0_3 false RX_CC_K_1_0 false RX_CC_K_1_1 false\
RX_CC_K_1_2 false RX_CC_K_1_3 false RX_CC_LEN_SEQ 1 RX_CC_MASK_0_0 false\
RX_CC_MASK_0_1 false RX_CC_MASK_0_2 false RX_CC_MASK_0_3 false RX_CC_MASK_1_0\
false RX_CC_MASK_1_1 false RX_CC_MASK_1_2 false RX_CC_MASK_1_3 false\
RX_CC_NUM_SEQ 0 RX_CC_PERIODICITY 5000 RX_CC_PRECEDENCE ENABLE\
RX_CC_REPEAT_WAIT 0 RX_CC_VAL\
00000000000000000000000000000000000000000000000000000000000000000000000000000000\
RX_CC_VAL_0_0 0000000000 RX_CC_VAL_0_1 0000000000 RX_CC_VAL_0_2 0000000000\
RX_CC_VAL_0_3 0000000000 RX_CC_VAL_1_0 0000000000 RX_CC_VAL_1_1 0000000000\
RX_CC_VAL_1_2 0000000000 RX_CC_VAL_1_3 0000000000 RX_COMMA_ALIGN_WORD 1\
RX_COMMA_DOUBLE_ENABLE false RX_COMMA_MASK 1111111111 RX_COMMA_M_ENABLE false\
RX_COMMA_M_VAL 1010000011 RX_COMMA_PRESET NONE RX_COMMA_P_ENABLE false\
RX_COMMA_P_VAL 0101111100 RX_COMMA_SHOW_REALIGN_ENABLE true RX_COMMA_VALID_ONLY\
0 RX_COUPLING AC RX_DATA_DECODING RAW RX_EQ_MODE AUTO RX_FRACN_ENABLED false\
RX_FRACN_NUMERATOR 0 RX_INT_DATA_WIDTH 32 RX_JTOL_FC 0 RX_JTOL_LF_SLOPE -20\
RX_LINE_RATE 10.3125 RX_OUTCLK_SOURCE RXOUTCLKPMA RX_PLL_TYPE LCPLL\
RX_PPM_OFFSET 0 RX_REFCLK_FREQUENCY 156.25 RX_REFCLK_SOURCE R0 RX_SLIDE_MODE\
OFF RX_SSC_PPM 0 RX_TERMINATION PROGRAMMABLE RX_TERMINATION_PROG_VALUE 800\
RX_USER_DATA_WIDTH 32 TXPROGDIV_FREQ_ENABLE false TXPROGDIV_FREQ_SOURCE LCPLL\
TXPROGDIV_FREQ_VAL 322.265625 TX_64B66B_CRC false TX_RATE_GROUP A\
TX_64B66B_ENCODER false TX_64B66B_SCRAMBLER false TX_ACTUAL_REFCLK_FREQUENCY\
156.25 TX_BUFFER_BYPASS_MODE Fast_Sync TX_BUFFER_MODE 1\
TX_BUFFER_RESET_ON_RATE_CHANGE ENABLE TX_DATA_ENCODING RAW\
TX_DIFF_SWING_EMPH_MODE CUSTOM TX_FRACN_ENABLED false TX_FRACN_NUMERATOR 0\
TX_INT_DATA_WIDTH 32 TX_LINE_RATE 10.3125 TX_OUTCLK_SOURCE TXOUTCLKPMA\
TX_PIPM_ENABLE false TX_PLL_TYPE LCPLL TX_REFCLK_FREQUENCY 156.25\
TX_REFCLK_SOURCE R0 TX_USER_DATA_WIDTH 32}\
   CONFIG.PROT7_LR0_SETTINGS {GT_TYPE GTY GT_DIRECTION DUPLEX INS_LOSS_NYQ 20 INTERNAL_PRESET None OOB_ENABLE\
false PCIE_ENABLE false PCIE_USERCLK2_FREQ 250 PCIE_USERCLK_FREQ 250 PRESET\
None RESET_SEQUENCE_INTERVAL 0 RXPROGDIV_FREQ_ENABLE false\
RXPROGDIV_FREQ_SOURCE LCPLL RXPROGDIV_FREQ_VAL 322.265625 RX_64B66B_CRC false\
RX_RATE_GROUP A RX_64B66B_DECODER false RX_64B66B_DESCRAMBLER false\
RX_ACTUAL_REFCLK_FREQUENCY 156.25 RX_BUFFER_BYPASS_MODE Fast_Sync\
RX_BUFFER_BYPASS_MODE_LANE MULTI RX_BUFFER_MODE 1 RX_BUFFER_RESET_ON_CB_CHANGE\
ENABLE RX_BUFFER_RESET_ON_COMMAALIGN DISABLE RX_BUFFER_RESET_ON_RATE_CHANGE\
ENABLE RX_CB_DISP_0_0 false RX_CB_DISP_0_1 false RX_CB_DISP_0_2 false\
RX_CB_DISP_0_3 false RX_CB_DISP_1_0 false RX_CB_DISP_1_1 false RX_CB_DISP_1_2\
false RX_CB_DISP_1_3 false RX_CB_K_0_0 false RX_CB_K_0_1 false RX_CB_K_0_2\
false RX_CB_K_0_3 false RX_CB_K_1_0 false RX_CB_K_1_1 false RX_CB_K_1_2 false\
RX_CB_K_1_3 false RX_CB_LEN_SEQ 1 RX_CB_MASK_0_0 false RX_CB_MASK_0_1 false\
RX_CB_MASK_0_2 false RX_CB_MASK_0_3 false RX_CB_MASK_1_0 false RX_CB_MASK_1_1\
false RX_CB_MASK_1_2 false RX_CB_MASK_1_3 false RX_CB_MAX_LEVEL 1\
RX_CB_MAX_SKEW 1 RX_CB_NUM_SEQ 0 RX_CB_VAL_0_0 00000000 RX_CB_VAL_0_1 00000000\
RX_CB_VAL_0_2 00000000 RX_CB_VAL_0_3 00000000 RX_CB_VAL_1_0 00000000\
RX_CB_VAL_1_1 00000000 RX_CB_VAL_1_2 00000000 RX_CB_VAL_1_3 00000000\
RX_CC_DISP_0_0 false RX_CC_DISP_0_1 false RX_CC_DISP_0_2 false RX_CC_DISP_0_3\
false RX_CC_DISP_1_0 false RX_CC_DISP_1_1 false RX_CC_DISP_1_2 false\
RX_CC_DISP_1_3 false RX_CC_KEEP_IDLE DISABLE RX_CC_K_0_0 false RX_CC_K_0_1\
false RX_CC_K_0_2 false RX_CC_K_0_3 false RX_CC_K_1_0 false RX_CC_K_1_1 false\
RX_CC_K_1_2 false RX_CC_K_1_3 false RX_CC_LEN_SEQ 1 RX_CC_MASK_0_0 false\
RX_CC_MASK_0_1 false RX_CC_MASK_0_2 false RX_CC_MASK_0_3 false RX_CC_MASK_1_0\
false RX_CC_MASK_1_1 false RX_CC_MASK_1_2 false RX_CC_MASK_1_3 false\
RX_CC_NUM_SEQ 0 RX_CC_PERIODICITY 5000 RX_CC_PRECEDENCE ENABLE\
RX_CC_REPEAT_WAIT 0 RX_CC_VAL\
00000000000000000000000000000000000000000000000000000000000000000000000000000000\
RX_CC_VAL_0_0 0000000000 RX_CC_VAL_0_1 0000000000 RX_CC_VAL_0_2 0000000000\
RX_CC_VAL_0_3 0000000000 RX_CC_VAL_1_0 0000000000 RX_CC_VAL_1_1 0000000000\
RX_CC_VAL_1_2 0000000000 RX_CC_VAL_1_3 0000000000 RX_COMMA_ALIGN_WORD 1\
RX_COMMA_DOUBLE_ENABLE false RX_COMMA_MASK 1111111111 RX_COMMA_M_ENABLE false\
RX_COMMA_M_VAL 1010000011 RX_COMMA_PRESET NONE RX_COMMA_P_ENABLE false\
RX_COMMA_P_VAL 0101111100 RX_COMMA_SHOW_REALIGN_ENABLE true RX_COMMA_VALID_ONLY\
0 RX_COUPLING AC RX_DATA_DECODING RAW RX_EQ_MODE AUTO RX_FRACN_ENABLED false\
RX_FRACN_NUMERATOR 0 RX_INT_DATA_WIDTH 32 RX_JTOL_FC 0 RX_JTOL_LF_SLOPE -20\
RX_LINE_RATE 10.3125 RX_OUTCLK_SOURCE RXOUTCLKPMA RX_PLL_TYPE LCPLL\
RX_PPM_OFFSET 0 RX_REFCLK_FREQUENCY 156.25 RX_REFCLK_SOURCE R0 RX_SLIDE_MODE\
OFF RX_SSC_PPM 0 RX_TERMINATION PROGRAMMABLE RX_TERMINATION_PROG_VALUE 800\
RX_USER_DATA_WIDTH 32 TXPROGDIV_FREQ_ENABLE false TXPROGDIV_FREQ_SOURCE LCPLL\
TXPROGDIV_FREQ_VAL 322.265625 TX_64B66B_CRC false TX_RATE_GROUP A\
TX_64B66B_ENCODER false TX_64B66B_SCRAMBLER false TX_ACTUAL_REFCLK_FREQUENCY\
156.25 TX_BUFFER_BYPASS_MODE Fast_Sync TX_BUFFER_MODE 1\
TX_BUFFER_RESET_ON_RATE_CHANGE ENABLE TX_DATA_ENCODING RAW\
TX_DIFF_SWING_EMPH_MODE CUSTOM TX_FRACN_ENABLED false TX_FRACN_NUMERATOR 0\
TX_INT_DATA_WIDTH 32 TX_LINE_RATE 10.3125 TX_OUTCLK_SOURCE TXOUTCLKPMA\
TX_PIPM_ENABLE false TX_PLL_TYPE LCPLL TX_REFCLK_FREQUENCY 156.25\
TX_REFCLK_SOURCE R0 TX_USER_DATA_WIDTH 32}\
   CONFIG.PROT_OUTCLK_VALUES {CH0_RXOUTCLK 390.625 CH0_TXOUTCLK 390.625 CH1_RXOUTCLK 390.625 CH1_TXOUTCLK\
390.625 CH2_RXOUTCLK 390.625 CH2_TXOUTCLK 390.625 CH3_RXOUTCLK 390.625\
CH3_TXOUTCLK 390.625}\
   CONFIG.REFCLK_STRING {HSCLK0_LCPLLGTREFCLK0 refclk_PROT0_R0_100_MHz_unique1 HSCLK1_LCPLLGTREFCLK0\
refclk_PROT0_R0_100_MHz_unique1}\
 ] $gt_quad_base_3

  # Create instance: urlp_3, and set properties
  set urlp_3 [ create_bd_cell -type ip -vlnv xilinx.com:ip:util_reduced_logic:2.0 urlp_3 ]
  set_property -dict [ list \
   CONFIG.C_SIZE {1} \
 ] $urlp_3

  # Create instance: util_ds_buf_3, and set properties
  set util_ds_buf_3 [ create_bd_cell -type ip -vlnv xilinx.com:ip:util_ds_buf:2.2 util_ds_buf_3 ]
  set_property -dict [ list \
   CONFIG.C_BUF_TYPE {IBUFDSGTE} \
 ] $util_ds_buf_3

  # Create instance: xlcp_3, and set properties
  set xlcp_3 [ create_bd_cell -type ip -vlnv xilinx.com:ip:xlconcat:2.1 xlcp_3 ]
  set_property -dict [ list \
   CONFIG.NUM_PORTS {1} \
 ] $xlcp_3

  # Create interface connections
  connect_bd_intf_net -intf_net bridge_refclkX1Y10_GT_RX0 [get_bd_intf_pins bridge_refclkX1Y10/GT_RX0] [get_bd_intf_pins gt_quad_base_3/RX0_GT_IP_Interface]
  connect_bd_intf_net -intf_net bridge_refclkX1Y10_GT_RX1 [get_bd_intf_pins bridge_refclkX1Y10/GT_RX1] [get_bd_intf_pins gt_quad_base_3/RX1_GT_IP_Interface]
  connect_bd_intf_net -intf_net bridge_refclkX1Y10_GT_RX2 [get_bd_intf_pins bridge_refclkX1Y10/GT_RX2] [get_bd_intf_pins gt_quad_base_3/RX2_GT_IP_Interface]
  connect_bd_intf_net -intf_net bridge_refclkX1Y10_GT_RX3 [get_bd_intf_pins bridge_refclkX1Y10/GT_RX3] [get_bd_intf_pins gt_quad_base_3/RX3_GT_IP_Interface]
  connect_bd_intf_net -intf_net bridge_refclkX1Y10_GT_TX0 [get_bd_intf_pins bridge_refclkX1Y10/GT_TX0] [get_bd_intf_pins gt_quad_base_3/TX0_GT_IP_Interface]
  connect_bd_intf_net -intf_net bridge_refclkX1Y10_GT_TX1 [get_bd_intf_pins bridge_refclkX1Y10/GT_TX1] [get_bd_intf_pins gt_quad_base_3/TX1_GT_IP_Interface]
  connect_bd_intf_net -intf_net bridge_refclkX1Y10_GT_TX2 [get_bd_intf_pins bridge_refclkX1Y10/GT_TX2] [get_bd_intf_pins gt_quad_base_3/TX2_GT_IP_Interface]
  connect_bd_intf_net -intf_net bridge_refclkX1Y10_GT_TX3 [get_bd_intf_pins bridge_refclkX1Y10/GT_TX3] [get_bd_intf_pins gt_quad_base_3/TX3_GT_IP_Interface]
  connect_bd_intf_net -intf_net bridge_refclkX1Y10_diff_gt_ref_clock_1 [get_bd_intf_pins bridge_refclkX1Y10_diff_gt_ref_clock] [get_bd_intf_pins util_ds_buf_3/CLK_IN_D]
  connect_bd_intf_net -intf_net gt_quad_base_3_GT_Serial [get_bd_intf_pins GT_Serial_3] [get_bd_intf_pins gt_quad_base_3/GT_Serial]

  # Create port connections
  connect_bd_net -net bufg_gt_6_usrclk [get_bd_pins bridge_refclkX1Y10/gt_rxusrclk] [get_bd_pins bufg_gt_6/usrclk] [get_bd_pins gt_quad_base_3/ch0_rxusrclk] [get_bd_pins gt_quad_base_3/ch1_rxusrclk] [get_bd_pins gt_quad_base_3/ch2_rxusrclk] [get_bd_pins gt_quad_base_3/ch3_rxusrclk]
  connect_bd_net -net bufg_gt_7_usrclk [get_bd_pins bridge_refclkX1Y10/gt_txusrclk] [get_bd_pins bufg_gt_7/usrclk] [get_bd_pins gt_quad_base_3/ch0_txusrclk] [get_bd_pins gt_quad_base_3/ch1_txusrclk] [get_bd_pins gt_quad_base_3/ch2_txusrclk] [get_bd_pins gt_quad_base_3/ch3_txusrclk]
  connect_bd_net -net gt_quad_base_3_ch0_rxoutclk [get_bd_pins bufg_gt_6/outclk] [get_bd_pins gt_quad_base_3/ch0_rxoutclk]
  connect_bd_net -net gt_quad_base_3_ch0_txoutclk [get_bd_pins bufg_gt_7/outclk] [get_bd_pins gt_quad_base_3/ch0_txoutclk]
  connect_bd_net -net gt_quad_base_3_gtpowergood [get_bd_pins gt_quad_base_3/gtpowergood] [get_bd_pins xlcp_3/In0]
  connect_bd_net -net urlp_3_Res [get_bd_pins bridge_refclkX1Y10/gtpowergood] [get_bd_pins urlp_3/Res]
  connect_bd_net -net util_ds_buf_3_IBUF_OUT [get_bd_pins gt_quad_base_3/GT_REFCLK0] [get_bd_pins util_ds_buf_3/IBUF_OUT]
  connect_bd_net -net versal_cips_0_pl0_ref_clk [get_bd_pins apb3clk] [get_bd_pins bridge_refclkX1Y10/apb3clk] [get_bd_pins gt_quad_base_3/apb3clk]
  connect_bd_net -net xlcp_3_dout [get_bd_pins urlp_3/Op1] [get_bd_pins xlcp_3/dout]

  # Restore current instance
  current_bd_instance $oldCurInst
}

# Hierarchical cell: gty_quad_204
proc create_hier_cell_gty_quad_204 { parentCell nameHier } {

  variable script_folder

  if { $parentCell eq "" || $nameHier eq "" } {
     catch {common::send_gid_msg -ssname BD::TCL -id 2092 -severity "ERROR" "create_hier_cell_gty_quad_204() - Empty argument(s)!"}
     return
  }

  # Get object for parentCell
  set parentObj [get_bd_cells $parentCell]
  if { $parentObj == "" } {
     catch {common::send_gid_msg -ssname BD::TCL -id 2090 -severity "ERROR" "Unable to find parent cell <$parentCell>!"}
     return
  }

  # Make sure parentObj is hier blk
  set parentType [get_property TYPE $parentObj]
  if { $parentType ne "hier" } {
     catch {common::send_gid_msg -ssname BD::TCL -id 2091 -severity "ERROR" "Parent <$parentObj> has TYPE = <$parentType>. Expected to be <hier>."}
     return
  }

  # Save current instance; Restore later
  set oldCurInst [current_bd_instance .]

  # Set parent object as current
  current_bd_instance $parentObj

  # Create cell and set as current instance
  set hier_obj [create_bd_cell -type hier $nameHier]
  current_bd_instance $hier_obj

  # Create interface pins
  create_bd_intf_pin -mode Master -vlnv xilinx.com:interface:gt_rtl:1.0 GT_Serial_2

  create_bd_intf_pin -mode Slave -vlnv xilinx.com:interface:diff_clock_rtl:1.0 bridge_refclkX1Y8_diff_gt_ref_clock


  # Create pins
  create_bd_pin -dir I -type clk apb3clk

  # Create instance: bridge_refclkX1Y8, and set properties
  set bridge_refclkX1Y8 [ create_bd_cell -type ip -vlnv xilinx.com:ip:gt_bridge_ip:1.1 bridge_refclkX1Y8 ]
  set_property -dict [ list \
   CONFIG.IP_LR0_SETTINGS {GT_DIRECTION DUPLEX  GT_TYPE GTY  INS_LOSS_NYQ 20  INTERNAL_PRESET None \
OOB_ENABLE false  PCIE_ENABLE false  PCIE_USERCLK2_FREQ 250  PCIE_USERCLK_FREQ\
250  PRESET None  RESET_SEQUENCE_INTERVAL 0  RXPROGDIV_FREQ_ENABLE false \
RXPROGDIV_FREQ_SOURCE LCPLL  RXPROGDIV_FREQ_VAL 322.265625  RX_64B66B_CRC false\
RX_64B66B_DECODER false  RX_64B66B_DESCRAMBLER false \
RX_ACTUAL_REFCLK_FREQUENCY 100.000000000000  RX_BUFFER_BYPASS_MODE Fast_Sync \
RX_BUFFER_BYPASS_MODE_LANE MULTI  RX_BUFFER_MODE 1 \
RX_BUFFER_RESET_ON_CB_CHANGE ENABLE  RX_BUFFER_RESET_ON_COMMAALIGN DISABLE \
RX_BUFFER_RESET_ON_RATE_CHANGE ENABLE  RX_CB_DISP_0_0 false  RX_CB_DISP_0_1\
false  RX_CB_DISP_0_2 false  RX_CB_DISP_0_3 false  RX_CB_DISP_1_0 false \
RX_CB_DISP_1_1 false  RX_CB_DISP_1_2 false  RX_CB_DISP_1_3 false  RX_CB_K_0_0\
false  RX_CB_K_0_1 false  RX_CB_K_0_2 false  RX_CB_K_0_3 false  RX_CB_K_1_0\
false  RX_CB_K_1_1 false  RX_CB_K_1_2 false  RX_CB_K_1_3 false  RX_CB_LEN_SEQ 1\
RX_CB_MASK_0_0 false  RX_CB_MASK_0_1 false  RX_CB_MASK_0_2 false \
RX_CB_MASK_0_3 false  RX_CB_MASK_1_0 false  RX_CB_MASK_1_1 false \
RX_CB_MASK_1_2 false  RX_CB_MASK_1_3 false  RX_CB_MAX_LEVEL 1  RX_CB_MAX_SKEW 1\
RX_CB_NUM_SEQ 0  RX_CB_VAL_0_0 00000000  RX_CB_VAL_0_1 00000000  RX_CB_VAL_0_2\
00000000  RX_CB_VAL_0_3 00000000  RX_CB_VAL_1_0 00000000  RX_CB_VAL_1_1\
00000000  RX_CB_VAL_1_2 00000000  RX_CB_VAL_1_3 00000000  RX_CC_DISP_0_0 false \
RX_CC_DISP_0_1 false  RX_CC_DISP_0_2 false  RX_CC_DISP_0_3 false \
RX_CC_DISP_1_0 false  RX_CC_DISP_1_1 false  RX_CC_DISP_1_2 false \
RX_CC_DISP_1_3 false  RX_CC_KEEP_IDLE DISABLE  RX_CC_K_0_0 false  RX_CC_K_0_1\
false  RX_CC_K_0_2 false  RX_CC_K_0_3 false  RX_CC_K_1_0 false  RX_CC_K_1_1\
false  RX_CC_K_1_2 false  RX_CC_K_1_3 false  RX_CC_LEN_SEQ 1  RX_CC_MASK_0_0\
false  RX_CC_MASK_0_1 false  RX_CC_MASK_0_2 false  RX_CC_MASK_0_3 false \
RX_CC_MASK_1_0 false  RX_CC_MASK_1_1 false  RX_CC_MASK_1_2 false \
RX_CC_MASK_1_3 false  RX_CC_NUM_SEQ 0  RX_CC_PERIODICITY 5000  RX_CC_PRECEDENCE\
ENABLE  RX_CC_REPEAT_WAIT 0  RX_CC_VAL\
00000000000000000000000000000000000000000000000000000000000000000000000000000000\
RX_CC_VAL_0_0 00000000  RX_CC_VAL_0_1 00000000  RX_CC_VAL_0_2 00000000 \
RX_CC_VAL_0_3 00000000  RX_CC_VAL_1_0 00000000  RX_CC_VAL_1_1 00000000 \
RX_CC_VAL_1_2 00000000  RX_CC_VAL_1_3 00000000  RX_COMMA_ALIGN_WORD 1 \
RX_COMMA_DOUBLE_ENABLE false  RX_COMMA_MASK 0000000000  RX_COMMA_M_ENABLE false\
RX_COMMA_M_VAL 1010000011  RX_COMMA_PRESET NONE  RX_COMMA_P_ENABLE false \
RX_COMMA_P_VAL 0101111100  RX_COMMA_SHOW_REALIGN_ENABLE true \
RX_COMMA_VALID_ONLY 0  RX_COUPLING AC  RX_DATA_DECODING RAW  RX_EQ_MODE AUTO \
RX_FRACN_ENABLED false  RX_FRACN_NUMERATOR 0  RX_GRAY_BYP true \
RX_GRAY_LITTLEENDIAN true  RX_INT_DATA_WIDTH 32  RX_JTOL_FC 9.5980804 \
RX_JTOL_LF_SLOPE -20  RX_LINE_RATE 16  RX_OUTCLK_SOURCE RXOUTCLKPMA  RX_PAM_SEL\
NRZ  RX_PLL_TYPE LCPLL  RX_PPM_OFFSET 0  RX_PRECODE_BYP true \
RX_PRECODE_LITTLEENDIAN false  RX_RATE_GROUP A  RX_REFCLK_FREQUENCY 100 \
RX_REFCLK_SOURCE R0  RX_SLIDE_MODE OFF  RX_SSC_PPM 0  RX_TERMINATION\
PROGRAMMABLE  RX_TERMINATION_PROG_VALUE 800  RX_USER_DATA_WIDTH 32 \
TXPROGDIV_FREQ_ENABLE false  TXPROGDIV_FREQ_SOURCE LCPLL  TXPROGDIV_FREQ_VAL\
322.265625  TX_64B66B_CRC false  TX_64B66B_ENCODER false  TX_64B66B_SCRAMBLER\
false  TX_ACTUAL_REFCLK_FREQUENCY 100.000000000000  TX_BUFFER_BYPASS_MODE\
Fast_Sync  TX_BUFFER_MODE 1  TX_BUFFER_RESET_ON_RATE_CHANGE ENABLE \
TX_DATA_ENCODING RAW  TX_DIFF_SWING_EMPH_MODE CUSTOM  TX_FRACN_ENABLED false \
TX_FRACN_NUMERATOR 0  TX_GRAY_BYP true  TX_GRAY_LITTLEENDIAN true \
TX_INT_DATA_WIDTH 32  TX_LINE_RATE 16  TX_OUTCLK_SOURCE TXOUTCLKPMA  TX_PAM_SEL\
NRZ  TX_PIPM_ENABLE false  TX_PLL_TYPE LCPLL  TX_PRECODE_BYP true \
TX_PRECODE_LITTLEENDIAN false  TX_RATE_GROUP A  TX_REFCLK_FREQUENCY 100 \
TX_REFCLK_SOURCE R0  TX_USER_DATA_WIDTH 32}\
   CONFIG.IP_NO_OF_LANES {4} \
 ] $bridge_refclkX1Y8

  # Create instance: bufg_gt_4, and set properties
  set bufg_gt_4 [ create_bd_cell -type ip -vlnv xilinx.com:ip:bufg_gt:1.0 bufg_gt_4 ]

  # Create instance: bufg_gt_5, and set properties
  set bufg_gt_5 [ create_bd_cell -type ip -vlnv xilinx.com:ip:bufg_gt:1.0 bufg_gt_5 ]

  # Create instance: gt_quad_base_2, and set properties
  set gt_quad_base_2 [ create_bd_cell -type ip -vlnv xilinx.com:ip:gt_quad_base:1.1 gt_quad_base_2 ]
  set_property -dict [ list \
   CONFIG.PORTS_INFO_DICT {LANE_SEL_DICT {PROT0 {RX0 RX1 RX2 RX3 TX0 TX1 TX2 TX3}} GT_TYPE GTY\
REG_CONF_INTF APB3_INTF BOARD_INTERFACE false}\
   CONFIG.PROT1_LR0_SETTINGS {GT_TYPE GTY GT_DIRECTION DUPLEX INS_LOSS_NYQ 20 INTERNAL_PRESET None OOB_ENABLE\
false PCIE_ENABLE false PCIE_USERCLK2_FREQ 250 PCIE_USERCLK_FREQ 250 PRESET\
None RESET_SEQUENCE_INTERVAL 0 RXPROGDIV_FREQ_ENABLE false\
RXPROGDIV_FREQ_SOURCE LCPLL RXPROGDIV_FREQ_VAL 322.265625 RX_64B66B_CRC false\
RX_RATE_GROUP A RX_64B66B_DECODER false RX_64B66B_DESCRAMBLER false\
RX_ACTUAL_REFCLK_FREQUENCY 156.25 RX_BUFFER_BYPASS_MODE Fast_Sync\
RX_BUFFER_BYPASS_MODE_LANE MULTI RX_BUFFER_MODE 1 RX_BUFFER_RESET_ON_CB_CHANGE\
ENABLE RX_BUFFER_RESET_ON_COMMAALIGN DISABLE RX_BUFFER_RESET_ON_RATE_CHANGE\
ENABLE RX_CB_DISP_0_0 false RX_CB_DISP_0_1 false RX_CB_DISP_0_2 false\
RX_CB_DISP_0_3 false RX_CB_DISP_1_0 false RX_CB_DISP_1_1 false RX_CB_DISP_1_2\
false RX_CB_DISP_1_3 false RX_CB_K_0_0 false RX_CB_K_0_1 false RX_CB_K_0_2\
false RX_CB_K_0_3 false RX_CB_K_1_0 false RX_CB_K_1_1 false RX_CB_K_1_2 false\
RX_CB_K_1_3 false RX_CB_LEN_SEQ 1 RX_CB_MASK_0_0 false RX_CB_MASK_0_1 false\
RX_CB_MASK_0_2 false RX_CB_MASK_0_3 false RX_CB_MASK_1_0 false RX_CB_MASK_1_1\
false RX_CB_MASK_1_2 false RX_CB_MASK_1_3 false RX_CB_MAX_LEVEL 1\
RX_CB_MAX_SKEW 1 RX_CB_NUM_SEQ 0 RX_CB_VAL_0_0 00000000 RX_CB_VAL_0_1 00000000\
RX_CB_VAL_0_2 00000000 RX_CB_VAL_0_3 00000000 RX_CB_VAL_1_0 00000000\
RX_CB_VAL_1_1 00000000 RX_CB_VAL_1_2 00000000 RX_CB_VAL_1_3 00000000\
RX_CC_DISP_0_0 false RX_CC_DISP_0_1 false RX_CC_DISP_0_2 false RX_CC_DISP_0_3\
false RX_CC_DISP_1_0 false RX_CC_DISP_1_1 false RX_CC_DISP_1_2 false\
RX_CC_DISP_1_3 false RX_CC_KEEP_IDLE DISABLE RX_CC_K_0_0 false RX_CC_K_0_1\
false RX_CC_K_0_2 false RX_CC_K_0_3 false RX_CC_K_1_0 false RX_CC_K_1_1 false\
RX_CC_K_1_2 false RX_CC_K_1_3 false RX_CC_LEN_SEQ 1 RX_CC_MASK_0_0 false\
RX_CC_MASK_0_1 false RX_CC_MASK_0_2 false RX_CC_MASK_0_3 false RX_CC_MASK_1_0\
false RX_CC_MASK_1_1 false RX_CC_MASK_1_2 false RX_CC_MASK_1_3 false\
RX_CC_NUM_SEQ 0 RX_CC_PERIODICITY 5000 RX_CC_PRECEDENCE ENABLE\
RX_CC_REPEAT_WAIT 0 RX_CC_VAL\
00000000000000000000000000000000000000000000000000000000000000000000000000000000\
RX_CC_VAL_0_0 0000000000 RX_CC_VAL_0_1 0000000000 RX_CC_VAL_0_2 0000000000\
RX_CC_VAL_0_3 0000000000 RX_CC_VAL_1_0 0000000000 RX_CC_VAL_1_1 0000000000\
RX_CC_VAL_1_2 0000000000 RX_CC_VAL_1_3 0000000000 RX_COMMA_ALIGN_WORD 1\
RX_COMMA_DOUBLE_ENABLE false RX_COMMA_MASK 1111111111 RX_COMMA_M_ENABLE false\
RX_COMMA_M_VAL 1010000011 RX_COMMA_PRESET NONE RX_COMMA_P_ENABLE false\
RX_COMMA_P_VAL 0101111100 RX_COMMA_SHOW_REALIGN_ENABLE true RX_COMMA_VALID_ONLY\
0 RX_COUPLING AC RX_DATA_DECODING RAW RX_EQ_MODE AUTO RX_FRACN_ENABLED false\
RX_FRACN_NUMERATOR 0 RX_INT_DATA_WIDTH 32 RX_JTOL_FC 0 RX_JTOL_LF_SLOPE -20\
RX_LINE_RATE 10.3125 RX_OUTCLK_SOURCE RXOUTCLKPMA RX_PLL_TYPE LCPLL\
RX_PPM_OFFSET 0 RX_REFCLK_FREQUENCY 156.25 RX_REFCLK_SOURCE R0 RX_SLIDE_MODE\
OFF RX_SSC_PPM 0 RX_TERMINATION PROGRAMMABLE RX_TERMINATION_PROG_VALUE 800\
RX_USER_DATA_WIDTH 32 TXPROGDIV_FREQ_ENABLE false TXPROGDIV_FREQ_SOURCE LCPLL\
TXPROGDIV_FREQ_VAL 322.265625 TX_64B66B_CRC false TX_RATE_GROUP A\
TX_64B66B_ENCODER false TX_64B66B_SCRAMBLER false TX_ACTUAL_REFCLK_FREQUENCY\
156.25 TX_BUFFER_BYPASS_MODE Fast_Sync TX_BUFFER_MODE 1\
TX_BUFFER_RESET_ON_RATE_CHANGE ENABLE TX_DATA_ENCODING RAW\
TX_DIFF_SWING_EMPH_MODE CUSTOM TX_FRACN_ENABLED false TX_FRACN_NUMERATOR 0\
TX_INT_DATA_WIDTH 32 TX_LINE_RATE 10.3125 TX_OUTCLK_SOURCE TXOUTCLKPMA\
TX_PIPM_ENABLE false TX_PLL_TYPE LCPLL TX_REFCLK_FREQUENCY 156.25\
TX_REFCLK_SOURCE R0 TX_USER_DATA_WIDTH 32}\
   CONFIG.PROT2_LR0_SETTINGS {GT_TYPE GTY GT_DIRECTION DUPLEX INS_LOSS_NYQ 20 INTERNAL_PRESET None OOB_ENABLE\
false PCIE_ENABLE false PCIE_USERCLK2_FREQ 250 PCIE_USERCLK_FREQ 250 PRESET\
None RESET_SEQUENCE_INTERVAL 0 RXPROGDIV_FREQ_ENABLE false\
RXPROGDIV_FREQ_SOURCE LCPLL RXPROGDIV_FREQ_VAL 322.265625 RX_64B66B_CRC false\
RX_RATE_GROUP A RX_64B66B_DECODER false RX_64B66B_DESCRAMBLER false\
RX_ACTUAL_REFCLK_FREQUENCY 156.25 RX_BUFFER_BYPASS_MODE Fast_Sync\
RX_BUFFER_BYPASS_MODE_LANE MULTI RX_BUFFER_MODE 1 RX_BUFFER_RESET_ON_CB_CHANGE\
ENABLE RX_BUFFER_RESET_ON_COMMAALIGN DISABLE RX_BUFFER_RESET_ON_RATE_CHANGE\
ENABLE RX_CB_DISP_0_0 false RX_CB_DISP_0_1 false RX_CB_DISP_0_2 false\
RX_CB_DISP_0_3 false RX_CB_DISP_1_0 false RX_CB_DISP_1_1 false RX_CB_DISP_1_2\
false RX_CB_DISP_1_3 false RX_CB_K_0_0 false RX_CB_K_0_1 false RX_CB_K_0_2\
false RX_CB_K_0_3 false RX_CB_K_1_0 false RX_CB_K_1_1 false RX_CB_K_1_2 false\
RX_CB_K_1_3 false RX_CB_LEN_SEQ 1 RX_CB_MASK_0_0 false RX_CB_MASK_0_1 false\
RX_CB_MASK_0_2 false RX_CB_MASK_0_3 false RX_CB_MASK_1_0 false RX_CB_MASK_1_1\
false RX_CB_MASK_1_2 false RX_CB_MASK_1_3 false RX_CB_MAX_LEVEL 1\
RX_CB_MAX_SKEW 1 RX_CB_NUM_SEQ 0 RX_CB_VAL_0_0 00000000 RX_CB_VAL_0_1 00000000\
RX_CB_VAL_0_2 00000000 RX_CB_VAL_0_3 00000000 RX_CB_VAL_1_0 00000000\
RX_CB_VAL_1_1 00000000 RX_CB_VAL_1_2 00000000 RX_CB_VAL_1_3 00000000\
RX_CC_DISP_0_0 false RX_CC_DISP_0_1 false RX_CC_DISP_0_2 false RX_CC_DISP_0_3\
false RX_CC_DISP_1_0 false RX_CC_DISP_1_1 false RX_CC_DISP_1_2 false\
RX_CC_DISP_1_3 false RX_CC_KEEP_IDLE DISABLE RX_CC_K_0_0 false RX_CC_K_0_1\
false RX_CC_K_0_2 false RX_CC_K_0_3 false RX_CC_K_1_0 false RX_CC_K_1_1 false\
RX_CC_K_1_2 false RX_CC_K_1_3 false RX_CC_LEN_SEQ 1 RX_CC_MASK_0_0 false\
RX_CC_MASK_0_1 false RX_CC_MASK_0_2 false RX_CC_MASK_0_3 false RX_CC_MASK_1_0\
false RX_CC_MASK_1_1 false RX_CC_MASK_1_2 false RX_CC_MASK_1_3 false\
RX_CC_NUM_SEQ 0 RX_CC_PERIODICITY 5000 RX_CC_PRECEDENCE ENABLE\
RX_CC_REPEAT_WAIT 0 RX_CC_VAL\
00000000000000000000000000000000000000000000000000000000000000000000000000000000\
RX_CC_VAL_0_0 0000000000 RX_CC_VAL_0_1 0000000000 RX_CC_VAL_0_2 0000000000\
RX_CC_VAL_0_3 0000000000 RX_CC_VAL_1_0 0000000000 RX_CC_VAL_1_1 0000000000\
RX_CC_VAL_1_2 0000000000 RX_CC_VAL_1_3 0000000000 RX_COMMA_ALIGN_WORD 1\
RX_COMMA_DOUBLE_ENABLE false RX_COMMA_MASK 1111111111 RX_COMMA_M_ENABLE false\
RX_COMMA_M_VAL 1010000011 RX_COMMA_PRESET NONE RX_COMMA_P_ENABLE false\
RX_COMMA_P_VAL 0101111100 RX_COMMA_SHOW_REALIGN_ENABLE true RX_COMMA_VALID_ONLY\
0 RX_COUPLING AC RX_DATA_DECODING RAW RX_EQ_MODE AUTO RX_FRACN_ENABLED false\
RX_FRACN_NUMERATOR 0 RX_INT_DATA_WIDTH 32 RX_JTOL_FC 0 RX_JTOL_LF_SLOPE -20\
RX_LINE_RATE 10.3125 RX_OUTCLK_SOURCE RXOUTCLKPMA RX_PLL_TYPE LCPLL\
RX_PPM_OFFSET 0 RX_REFCLK_FREQUENCY 156.25 RX_REFCLK_SOURCE R0 RX_SLIDE_MODE\
OFF RX_SSC_PPM 0 RX_TERMINATION PROGRAMMABLE RX_TERMINATION_PROG_VALUE 800\
RX_USER_DATA_WIDTH 32 TXPROGDIV_FREQ_ENABLE false TXPROGDIV_FREQ_SOURCE LCPLL\
TXPROGDIV_FREQ_VAL 322.265625 TX_64B66B_CRC false TX_RATE_GROUP A\
TX_64B66B_ENCODER false TX_64B66B_SCRAMBLER false TX_ACTUAL_REFCLK_FREQUENCY\
156.25 TX_BUFFER_BYPASS_MODE Fast_Sync TX_BUFFER_MODE 1\
TX_BUFFER_RESET_ON_RATE_CHANGE ENABLE TX_DATA_ENCODING RAW\
TX_DIFF_SWING_EMPH_MODE CUSTOM TX_FRACN_ENABLED false TX_FRACN_NUMERATOR 0\
TX_INT_DATA_WIDTH 32 TX_LINE_RATE 10.3125 TX_OUTCLK_SOURCE TXOUTCLKPMA\
TX_PIPM_ENABLE false TX_PLL_TYPE LCPLL TX_REFCLK_FREQUENCY 156.25\
TX_REFCLK_SOURCE R0 TX_USER_DATA_WIDTH 32}\
   CONFIG.PROT3_LR0_SETTINGS {GT_TYPE GTY GT_DIRECTION DUPLEX INS_LOSS_NYQ 20 INTERNAL_PRESET None OOB_ENABLE\
false PCIE_ENABLE false PCIE_USERCLK2_FREQ 250 PCIE_USERCLK_FREQ 250 PRESET\
None RESET_SEQUENCE_INTERVAL 0 RXPROGDIV_FREQ_ENABLE false\
RXPROGDIV_FREQ_SOURCE LCPLL RXPROGDIV_FREQ_VAL 322.265625 RX_64B66B_CRC false\
RX_RATE_GROUP A RX_64B66B_DECODER false RX_64B66B_DESCRAMBLER false\
RX_ACTUAL_REFCLK_FREQUENCY 156.25 RX_BUFFER_BYPASS_MODE Fast_Sync\
RX_BUFFER_BYPASS_MODE_LANE MULTI RX_BUFFER_MODE 1 RX_BUFFER_RESET_ON_CB_CHANGE\
ENABLE RX_BUFFER_RESET_ON_COMMAALIGN DISABLE RX_BUFFER_RESET_ON_RATE_CHANGE\
ENABLE RX_CB_DISP_0_0 false RX_CB_DISP_0_1 false RX_CB_DISP_0_2 false\
RX_CB_DISP_0_3 false RX_CB_DISP_1_0 false RX_CB_DISP_1_1 false RX_CB_DISP_1_2\
false RX_CB_DISP_1_3 false RX_CB_K_0_0 false RX_CB_K_0_1 false RX_CB_K_0_2\
false RX_CB_K_0_3 false RX_CB_K_1_0 false RX_CB_K_1_1 false RX_CB_K_1_2 false\
RX_CB_K_1_3 false RX_CB_LEN_SEQ 1 RX_CB_MASK_0_0 false RX_CB_MASK_0_1 false\
RX_CB_MASK_0_2 false RX_CB_MASK_0_3 false RX_CB_MASK_1_0 false RX_CB_MASK_1_1\
false RX_CB_MASK_1_2 false RX_CB_MASK_1_3 false RX_CB_MAX_LEVEL 1\
RX_CB_MAX_SKEW 1 RX_CB_NUM_SEQ 0 RX_CB_VAL_0_0 00000000 RX_CB_VAL_0_1 00000000\
RX_CB_VAL_0_2 00000000 RX_CB_VAL_0_3 00000000 RX_CB_VAL_1_0 00000000\
RX_CB_VAL_1_1 00000000 RX_CB_VAL_1_2 00000000 RX_CB_VAL_1_3 00000000\
RX_CC_DISP_0_0 false RX_CC_DISP_0_1 false RX_CC_DISP_0_2 false RX_CC_DISP_0_3\
false RX_CC_DISP_1_0 false RX_CC_DISP_1_1 false RX_CC_DISP_1_2 false\
RX_CC_DISP_1_3 false RX_CC_KEEP_IDLE DISABLE RX_CC_K_0_0 false RX_CC_K_0_1\
false RX_CC_K_0_2 false RX_CC_K_0_3 false RX_CC_K_1_0 false RX_CC_K_1_1 false\
RX_CC_K_1_2 false RX_CC_K_1_3 false RX_CC_LEN_SEQ 1 RX_CC_MASK_0_0 false\
RX_CC_MASK_0_1 false RX_CC_MASK_0_2 false RX_CC_MASK_0_3 false RX_CC_MASK_1_0\
false RX_CC_MASK_1_1 false RX_CC_MASK_1_2 false RX_CC_MASK_1_3 false\
RX_CC_NUM_SEQ 0 RX_CC_PERIODICITY 5000 RX_CC_PRECEDENCE ENABLE\
RX_CC_REPEAT_WAIT 0 RX_CC_VAL\
00000000000000000000000000000000000000000000000000000000000000000000000000000000\
RX_CC_VAL_0_0 0000000000 RX_CC_VAL_0_1 0000000000 RX_CC_VAL_0_2 0000000000\
RX_CC_VAL_0_3 0000000000 RX_CC_VAL_1_0 0000000000 RX_CC_VAL_1_1 0000000000\
RX_CC_VAL_1_2 0000000000 RX_CC_VAL_1_3 0000000000 RX_COMMA_ALIGN_WORD 1\
RX_COMMA_DOUBLE_ENABLE false RX_COMMA_MASK 1111111111 RX_COMMA_M_ENABLE false\
RX_COMMA_M_VAL 1010000011 RX_COMMA_PRESET NONE RX_COMMA_P_ENABLE false\
RX_COMMA_P_VAL 0101111100 RX_COMMA_SHOW_REALIGN_ENABLE true RX_COMMA_VALID_ONLY\
0 RX_COUPLING AC RX_DATA_DECODING RAW RX_EQ_MODE AUTO RX_FRACN_ENABLED false\
RX_FRACN_NUMERATOR 0 RX_INT_DATA_WIDTH 32 RX_JTOL_FC 0 RX_JTOL_LF_SLOPE -20\
RX_LINE_RATE 10.3125 RX_OUTCLK_SOURCE RXOUTCLKPMA RX_PLL_TYPE LCPLL\
RX_PPM_OFFSET 0 RX_REFCLK_FREQUENCY 156.25 RX_REFCLK_SOURCE R0 RX_SLIDE_MODE\
OFF RX_SSC_PPM 0 RX_TERMINATION PROGRAMMABLE RX_TERMINATION_PROG_VALUE 800\
RX_USER_DATA_WIDTH 32 TXPROGDIV_FREQ_ENABLE false TXPROGDIV_FREQ_SOURCE LCPLL\
TXPROGDIV_FREQ_VAL 322.265625 TX_64B66B_CRC false TX_RATE_GROUP A\
TX_64B66B_ENCODER false TX_64B66B_SCRAMBLER false TX_ACTUAL_REFCLK_FREQUENCY\
156.25 TX_BUFFER_BYPASS_MODE Fast_Sync TX_BUFFER_MODE 1\
TX_BUFFER_RESET_ON_RATE_CHANGE ENABLE TX_DATA_ENCODING RAW\
TX_DIFF_SWING_EMPH_MODE CUSTOM TX_FRACN_ENABLED false TX_FRACN_NUMERATOR 0\
TX_INT_DATA_WIDTH 32 TX_LINE_RATE 10.3125 TX_OUTCLK_SOURCE TXOUTCLKPMA\
TX_PIPM_ENABLE false TX_PLL_TYPE LCPLL TX_REFCLK_FREQUENCY 156.25\
TX_REFCLK_SOURCE R0 TX_USER_DATA_WIDTH 32}\
   CONFIG.PROT4_LR0_SETTINGS {GT_TYPE GTY GT_DIRECTION DUPLEX INS_LOSS_NYQ 20 INTERNAL_PRESET None OOB_ENABLE\
false PCIE_ENABLE false PCIE_USERCLK2_FREQ 250 PCIE_USERCLK_FREQ 250 PRESET\
None RESET_SEQUENCE_INTERVAL 0 RXPROGDIV_FREQ_ENABLE false\
RXPROGDIV_FREQ_SOURCE LCPLL RXPROGDIV_FREQ_VAL 322.265625 RX_64B66B_CRC false\
RX_RATE_GROUP A RX_64B66B_DECODER false RX_64B66B_DESCRAMBLER false\
RX_ACTUAL_REFCLK_FREQUENCY 156.25 RX_BUFFER_BYPASS_MODE Fast_Sync\
RX_BUFFER_BYPASS_MODE_LANE MULTI RX_BUFFER_MODE 1 RX_BUFFER_RESET_ON_CB_CHANGE\
ENABLE RX_BUFFER_RESET_ON_COMMAALIGN DISABLE RX_BUFFER_RESET_ON_RATE_CHANGE\
ENABLE RX_CB_DISP_0_0 false RX_CB_DISP_0_1 false RX_CB_DISP_0_2 false\
RX_CB_DISP_0_3 false RX_CB_DISP_1_0 false RX_CB_DISP_1_1 false RX_CB_DISP_1_2\
false RX_CB_DISP_1_3 false RX_CB_K_0_0 false RX_CB_K_0_1 false RX_CB_K_0_2\
false RX_CB_K_0_3 false RX_CB_K_1_0 false RX_CB_K_1_1 false RX_CB_K_1_2 false\
RX_CB_K_1_3 false RX_CB_LEN_SEQ 1 RX_CB_MASK_0_0 false RX_CB_MASK_0_1 false\
RX_CB_MASK_0_2 false RX_CB_MASK_0_3 false RX_CB_MASK_1_0 false RX_CB_MASK_1_1\
false RX_CB_MASK_1_2 false RX_CB_MASK_1_3 false RX_CB_MAX_LEVEL 1\
RX_CB_MAX_SKEW 1 RX_CB_NUM_SEQ 0 RX_CB_VAL_0_0 00000000 RX_CB_VAL_0_1 00000000\
RX_CB_VAL_0_2 00000000 RX_CB_VAL_0_3 00000000 RX_CB_VAL_1_0 00000000\
RX_CB_VAL_1_1 00000000 RX_CB_VAL_1_2 00000000 RX_CB_VAL_1_3 00000000\
RX_CC_DISP_0_0 false RX_CC_DISP_0_1 false RX_CC_DISP_0_2 false RX_CC_DISP_0_3\
false RX_CC_DISP_1_0 false RX_CC_DISP_1_1 false RX_CC_DISP_1_2 false\
RX_CC_DISP_1_3 false RX_CC_KEEP_IDLE DISABLE RX_CC_K_0_0 false RX_CC_K_0_1\
false RX_CC_K_0_2 false RX_CC_K_0_3 false RX_CC_K_1_0 false RX_CC_K_1_1 false\
RX_CC_K_1_2 false RX_CC_K_1_3 false RX_CC_LEN_SEQ 1 RX_CC_MASK_0_0 false\
RX_CC_MASK_0_1 false RX_CC_MASK_0_2 false RX_CC_MASK_0_3 false RX_CC_MASK_1_0\
false RX_CC_MASK_1_1 false RX_CC_MASK_1_2 false RX_CC_MASK_1_3 false\
RX_CC_NUM_SEQ 0 RX_CC_PERIODICITY 5000 RX_CC_PRECEDENCE ENABLE\
RX_CC_REPEAT_WAIT 0 RX_CC_VAL\
00000000000000000000000000000000000000000000000000000000000000000000000000000000\
RX_CC_VAL_0_0 0000000000 RX_CC_VAL_0_1 0000000000 RX_CC_VAL_0_2 0000000000\
RX_CC_VAL_0_3 0000000000 RX_CC_VAL_1_0 0000000000 RX_CC_VAL_1_1 0000000000\
RX_CC_VAL_1_2 0000000000 RX_CC_VAL_1_3 0000000000 RX_COMMA_ALIGN_WORD 1\
RX_COMMA_DOUBLE_ENABLE false RX_COMMA_MASK 1111111111 RX_COMMA_M_ENABLE false\
RX_COMMA_M_VAL 1010000011 RX_COMMA_PRESET NONE RX_COMMA_P_ENABLE false\
RX_COMMA_P_VAL 0101111100 RX_COMMA_SHOW_REALIGN_ENABLE true RX_COMMA_VALID_ONLY\
0 RX_COUPLING AC RX_DATA_DECODING RAW RX_EQ_MODE AUTO RX_FRACN_ENABLED false\
RX_FRACN_NUMERATOR 0 RX_INT_DATA_WIDTH 32 RX_JTOL_FC 0 RX_JTOL_LF_SLOPE -20\
RX_LINE_RATE 10.3125 RX_OUTCLK_SOURCE RXOUTCLKPMA RX_PLL_TYPE LCPLL\
RX_PPM_OFFSET 0 RX_REFCLK_FREQUENCY 156.25 RX_REFCLK_SOURCE R0 RX_SLIDE_MODE\
OFF RX_SSC_PPM 0 RX_TERMINATION PROGRAMMABLE RX_TERMINATION_PROG_VALUE 800\
RX_USER_DATA_WIDTH 32 TXPROGDIV_FREQ_ENABLE false TXPROGDIV_FREQ_SOURCE LCPLL\
TXPROGDIV_FREQ_VAL 322.265625 TX_64B66B_CRC false TX_RATE_GROUP A\
TX_64B66B_ENCODER false TX_64B66B_SCRAMBLER false TX_ACTUAL_REFCLK_FREQUENCY\
156.25 TX_BUFFER_BYPASS_MODE Fast_Sync TX_BUFFER_MODE 1\
TX_BUFFER_RESET_ON_RATE_CHANGE ENABLE TX_DATA_ENCODING RAW\
TX_DIFF_SWING_EMPH_MODE CUSTOM TX_FRACN_ENABLED false TX_FRACN_NUMERATOR 0\
TX_INT_DATA_WIDTH 32 TX_LINE_RATE 10.3125 TX_OUTCLK_SOURCE TXOUTCLKPMA\
TX_PIPM_ENABLE false TX_PLL_TYPE LCPLL TX_REFCLK_FREQUENCY 156.25\
TX_REFCLK_SOURCE R0 TX_USER_DATA_WIDTH 32}\
   CONFIG.PROT5_LR0_SETTINGS {GT_TYPE GTY GT_DIRECTION DUPLEX INS_LOSS_NYQ 20 INTERNAL_PRESET None OOB_ENABLE\
false PCIE_ENABLE false PCIE_USERCLK2_FREQ 250 PCIE_USERCLK_FREQ 250 PRESET\
None RESET_SEQUENCE_INTERVAL 0 RXPROGDIV_FREQ_ENABLE false\
RXPROGDIV_FREQ_SOURCE LCPLL RXPROGDIV_FREQ_VAL 322.265625 RX_64B66B_CRC false\
RX_RATE_GROUP A RX_64B66B_DECODER false RX_64B66B_DESCRAMBLER false\
RX_ACTUAL_REFCLK_FREQUENCY 156.25 RX_BUFFER_BYPASS_MODE Fast_Sync\
RX_BUFFER_BYPASS_MODE_LANE MULTI RX_BUFFER_MODE 1 RX_BUFFER_RESET_ON_CB_CHANGE\
ENABLE RX_BUFFER_RESET_ON_COMMAALIGN DISABLE RX_BUFFER_RESET_ON_RATE_CHANGE\
ENABLE RX_CB_DISP_0_0 false RX_CB_DISP_0_1 false RX_CB_DISP_0_2 false\
RX_CB_DISP_0_3 false RX_CB_DISP_1_0 false RX_CB_DISP_1_1 false RX_CB_DISP_1_2\
false RX_CB_DISP_1_3 false RX_CB_K_0_0 false RX_CB_K_0_1 false RX_CB_K_0_2\
false RX_CB_K_0_3 false RX_CB_K_1_0 false RX_CB_K_1_1 false RX_CB_K_1_2 false\
RX_CB_K_1_3 false RX_CB_LEN_SEQ 1 RX_CB_MASK_0_0 false RX_CB_MASK_0_1 false\
RX_CB_MASK_0_2 false RX_CB_MASK_0_3 false RX_CB_MASK_1_0 false RX_CB_MASK_1_1\
false RX_CB_MASK_1_2 false RX_CB_MASK_1_3 false RX_CB_MAX_LEVEL 1\
RX_CB_MAX_SKEW 1 RX_CB_NUM_SEQ 0 RX_CB_VAL_0_0 00000000 RX_CB_VAL_0_1 00000000\
RX_CB_VAL_0_2 00000000 RX_CB_VAL_0_3 00000000 RX_CB_VAL_1_0 00000000\
RX_CB_VAL_1_1 00000000 RX_CB_VAL_1_2 00000000 RX_CB_VAL_1_3 00000000\
RX_CC_DISP_0_0 false RX_CC_DISP_0_1 false RX_CC_DISP_0_2 false RX_CC_DISP_0_3\
false RX_CC_DISP_1_0 false RX_CC_DISP_1_1 false RX_CC_DISP_1_2 false\
RX_CC_DISP_1_3 false RX_CC_KEEP_IDLE DISABLE RX_CC_K_0_0 false RX_CC_K_0_1\
false RX_CC_K_0_2 false RX_CC_K_0_3 false RX_CC_K_1_0 false RX_CC_K_1_1 false\
RX_CC_K_1_2 false RX_CC_K_1_3 false RX_CC_LEN_SEQ 1 RX_CC_MASK_0_0 false\
RX_CC_MASK_0_1 false RX_CC_MASK_0_2 false RX_CC_MASK_0_3 false RX_CC_MASK_1_0\
false RX_CC_MASK_1_1 false RX_CC_MASK_1_2 false RX_CC_MASK_1_3 false\
RX_CC_NUM_SEQ 0 RX_CC_PERIODICITY 5000 RX_CC_PRECEDENCE ENABLE\
RX_CC_REPEAT_WAIT 0 RX_CC_VAL\
00000000000000000000000000000000000000000000000000000000000000000000000000000000\
RX_CC_VAL_0_0 0000000000 RX_CC_VAL_0_1 0000000000 RX_CC_VAL_0_2 0000000000\
RX_CC_VAL_0_3 0000000000 RX_CC_VAL_1_0 0000000000 RX_CC_VAL_1_1 0000000000\
RX_CC_VAL_1_2 0000000000 RX_CC_VAL_1_3 0000000000 RX_COMMA_ALIGN_WORD 1\
RX_COMMA_DOUBLE_ENABLE false RX_COMMA_MASK 1111111111 RX_COMMA_M_ENABLE false\
RX_COMMA_M_VAL 1010000011 RX_COMMA_PRESET NONE RX_COMMA_P_ENABLE false\
RX_COMMA_P_VAL 0101111100 RX_COMMA_SHOW_REALIGN_ENABLE true RX_COMMA_VALID_ONLY\
0 RX_COUPLING AC RX_DATA_DECODING RAW RX_EQ_MODE AUTO RX_FRACN_ENABLED false\
RX_FRACN_NUMERATOR 0 RX_INT_DATA_WIDTH 32 RX_JTOL_FC 0 RX_JTOL_LF_SLOPE -20\
RX_LINE_RATE 10.3125 RX_OUTCLK_SOURCE RXOUTCLKPMA RX_PLL_TYPE LCPLL\
RX_PPM_OFFSET 0 RX_REFCLK_FREQUENCY 156.25 RX_REFCLK_SOURCE R0 RX_SLIDE_MODE\
OFF RX_SSC_PPM 0 RX_TERMINATION PROGRAMMABLE RX_TERMINATION_PROG_VALUE 800\
RX_USER_DATA_WIDTH 32 TXPROGDIV_FREQ_ENABLE false TXPROGDIV_FREQ_SOURCE LCPLL\
TXPROGDIV_FREQ_VAL 322.265625 TX_64B66B_CRC false TX_RATE_GROUP A\
TX_64B66B_ENCODER false TX_64B66B_SCRAMBLER false TX_ACTUAL_REFCLK_FREQUENCY\
156.25 TX_BUFFER_BYPASS_MODE Fast_Sync TX_BUFFER_MODE 1\
TX_BUFFER_RESET_ON_RATE_CHANGE ENABLE TX_DATA_ENCODING RAW\
TX_DIFF_SWING_EMPH_MODE CUSTOM TX_FRACN_ENABLED false TX_FRACN_NUMERATOR 0\
TX_INT_DATA_WIDTH 32 TX_LINE_RATE 10.3125 TX_OUTCLK_SOURCE TXOUTCLKPMA\
TX_PIPM_ENABLE false TX_PLL_TYPE LCPLL TX_REFCLK_FREQUENCY 156.25\
TX_REFCLK_SOURCE R0 TX_USER_DATA_WIDTH 32}\
   CONFIG.PROT6_LR0_SETTINGS {GT_TYPE GTY GT_DIRECTION DUPLEX INS_LOSS_NYQ 20 INTERNAL_PRESET None OOB_ENABLE\
false PCIE_ENABLE false PCIE_USERCLK2_FREQ 250 PCIE_USERCLK_FREQ 250 PRESET\
None RESET_SEQUENCE_INTERVAL 0 RXPROGDIV_FREQ_ENABLE false\
RXPROGDIV_FREQ_SOURCE LCPLL RXPROGDIV_FREQ_VAL 322.265625 RX_64B66B_CRC false\
RX_RATE_GROUP A RX_64B66B_DECODER false RX_64B66B_DESCRAMBLER false\
RX_ACTUAL_REFCLK_FREQUENCY 156.25 RX_BUFFER_BYPASS_MODE Fast_Sync\
RX_BUFFER_BYPASS_MODE_LANE MULTI RX_BUFFER_MODE 1 RX_BUFFER_RESET_ON_CB_CHANGE\
ENABLE RX_BUFFER_RESET_ON_COMMAALIGN DISABLE RX_BUFFER_RESET_ON_RATE_CHANGE\
ENABLE RX_CB_DISP_0_0 false RX_CB_DISP_0_1 false RX_CB_DISP_0_2 false\
RX_CB_DISP_0_3 false RX_CB_DISP_1_0 false RX_CB_DISP_1_1 false RX_CB_DISP_1_2\
false RX_CB_DISP_1_3 false RX_CB_K_0_0 false RX_CB_K_0_1 false RX_CB_K_0_2\
false RX_CB_K_0_3 false RX_CB_K_1_0 false RX_CB_K_1_1 false RX_CB_K_1_2 false\
RX_CB_K_1_3 false RX_CB_LEN_SEQ 1 RX_CB_MASK_0_0 false RX_CB_MASK_0_1 false\
RX_CB_MASK_0_2 false RX_CB_MASK_0_3 false RX_CB_MASK_1_0 false RX_CB_MASK_1_1\
false RX_CB_MASK_1_2 false RX_CB_MASK_1_3 false RX_CB_MAX_LEVEL 1\
RX_CB_MAX_SKEW 1 RX_CB_NUM_SEQ 0 RX_CB_VAL_0_0 00000000 RX_CB_VAL_0_1 00000000\
RX_CB_VAL_0_2 00000000 RX_CB_VAL_0_3 00000000 RX_CB_VAL_1_0 00000000\
RX_CB_VAL_1_1 00000000 RX_CB_VAL_1_2 00000000 RX_CB_VAL_1_3 00000000\
RX_CC_DISP_0_0 false RX_CC_DISP_0_1 false RX_CC_DISP_0_2 false RX_CC_DISP_0_3\
false RX_CC_DISP_1_0 false RX_CC_DISP_1_1 false RX_CC_DISP_1_2 false\
RX_CC_DISP_1_3 false RX_CC_KEEP_IDLE DISABLE RX_CC_K_0_0 false RX_CC_K_0_1\
false RX_CC_K_0_2 false RX_CC_K_0_3 false RX_CC_K_1_0 false RX_CC_K_1_1 false\
RX_CC_K_1_2 false RX_CC_K_1_3 false RX_CC_LEN_SEQ 1 RX_CC_MASK_0_0 false\
RX_CC_MASK_0_1 false RX_CC_MASK_0_2 false RX_CC_MASK_0_3 false RX_CC_MASK_1_0\
false RX_CC_MASK_1_1 false RX_CC_MASK_1_2 false RX_CC_MASK_1_3 false\
RX_CC_NUM_SEQ 0 RX_CC_PERIODICITY 5000 RX_CC_PRECEDENCE ENABLE\
RX_CC_REPEAT_WAIT 0 RX_CC_VAL\
00000000000000000000000000000000000000000000000000000000000000000000000000000000\
RX_CC_VAL_0_0 0000000000 RX_CC_VAL_0_1 0000000000 RX_CC_VAL_0_2 0000000000\
RX_CC_VAL_0_3 0000000000 RX_CC_VAL_1_0 0000000000 RX_CC_VAL_1_1 0000000000\
RX_CC_VAL_1_2 0000000000 RX_CC_VAL_1_3 0000000000 RX_COMMA_ALIGN_WORD 1\
RX_COMMA_DOUBLE_ENABLE false RX_COMMA_MASK 1111111111 RX_COMMA_M_ENABLE false\
RX_COMMA_M_VAL 1010000011 RX_COMMA_PRESET NONE RX_COMMA_P_ENABLE false\
RX_COMMA_P_VAL 0101111100 RX_COMMA_SHOW_REALIGN_ENABLE true RX_COMMA_VALID_ONLY\
0 RX_COUPLING AC RX_DATA_DECODING RAW RX_EQ_MODE AUTO RX_FRACN_ENABLED false\
RX_FRACN_NUMERATOR 0 RX_INT_DATA_WIDTH 32 RX_JTOL_FC 0 RX_JTOL_LF_SLOPE -20\
RX_LINE_RATE 10.3125 RX_OUTCLK_SOURCE RXOUTCLKPMA RX_PLL_TYPE LCPLL\
RX_PPM_OFFSET 0 RX_REFCLK_FREQUENCY 156.25 RX_REFCLK_SOURCE R0 RX_SLIDE_MODE\
OFF RX_SSC_PPM 0 RX_TERMINATION PROGRAMMABLE RX_TERMINATION_PROG_VALUE 800\
RX_USER_DATA_WIDTH 32 TXPROGDIV_FREQ_ENABLE false TXPROGDIV_FREQ_SOURCE LCPLL\
TXPROGDIV_FREQ_VAL 322.265625 TX_64B66B_CRC false TX_RATE_GROUP A\
TX_64B66B_ENCODER false TX_64B66B_SCRAMBLER false TX_ACTUAL_REFCLK_FREQUENCY\
156.25 TX_BUFFER_BYPASS_MODE Fast_Sync TX_BUFFER_MODE 1\
TX_BUFFER_RESET_ON_RATE_CHANGE ENABLE TX_DATA_ENCODING RAW\
TX_DIFF_SWING_EMPH_MODE CUSTOM TX_FRACN_ENABLED false TX_FRACN_NUMERATOR 0\
TX_INT_DATA_WIDTH 32 TX_LINE_RATE 10.3125 TX_OUTCLK_SOURCE TXOUTCLKPMA\
TX_PIPM_ENABLE false TX_PLL_TYPE LCPLL TX_REFCLK_FREQUENCY 156.25\
TX_REFCLK_SOURCE R0 TX_USER_DATA_WIDTH 32}\
   CONFIG.PROT7_LR0_SETTINGS {GT_TYPE GTY GT_DIRECTION DUPLEX INS_LOSS_NYQ 20 INTERNAL_PRESET None OOB_ENABLE\
false PCIE_ENABLE false PCIE_USERCLK2_FREQ 250 PCIE_USERCLK_FREQ 250 PRESET\
None RESET_SEQUENCE_INTERVAL 0 RXPROGDIV_FREQ_ENABLE false\
RXPROGDIV_FREQ_SOURCE LCPLL RXPROGDIV_FREQ_VAL 322.265625 RX_64B66B_CRC false\
RX_RATE_GROUP A RX_64B66B_DECODER false RX_64B66B_DESCRAMBLER false\
RX_ACTUAL_REFCLK_FREQUENCY 156.25 RX_BUFFER_BYPASS_MODE Fast_Sync\
RX_BUFFER_BYPASS_MODE_LANE MULTI RX_BUFFER_MODE 1 RX_BUFFER_RESET_ON_CB_CHANGE\
ENABLE RX_BUFFER_RESET_ON_COMMAALIGN DISABLE RX_BUFFER_RESET_ON_RATE_CHANGE\
ENABLE RX_CB_DISP_0_0 false RX_CB_DISP_0_1 false RX_CB_DISP_0_2 false\
RX_CB_DISP_0_3 false RX_CB_DISP_1_0 false RX_CB_DISP_1_1 false RX_CB_DISP_1_2\
false RX_CB_DISP_1_3 false RX_CB_K_0_0 false RX_CB_K_0_1 false RX_CB_K_0_2\
false RX_CB_K_0_3 false RX_CB_K_1_0 false RX_CB_K_1_1 false RX_CB_K_1_2 false\
RX_CB_K_1_3 false RX_CB_LEN_SEQ 1 RX_CB_MASK_0_0 false RX_CB_MASK_0_1 false\
RX_CB_MASK_0_2 false RX_CB_MASK_0_3 false RX_CB_MASK_1_0 false RX_CB_MASK_1_1\
false RX_CB_MASK_1_2 false RX_CB_MASK_1_3 false RX_CB_MAX_LEVEL 1\
RX_CB_MAX_SKEW 1 RX_CB_NUM_SEQ 0 RX_CB_VAL_0_0 00000000 RX_CB_VAL_0_1 00000000\
RX_CB_VAL_0_2 00000000 RX_CB_VAL_0_3 00000000 RX_CB_VAL_1_0 00000000\
RX_CB_VAL_1_1 00000000 RX_CB_VAL_1_2 00000000 RX_CB_VAL_1_3 00000000\
RX_CC_DISP_0_0 false RX_CC_DISP_0_1 false RX_CC_DISP_0_2 false RX_CC_DISP_0_3\
false RX_CC_DISP_1_0 false RX_CC_DISP_1_1 false RX_CC_DISP_1_2 false\
RX_CC_DISP_1_3 false RX_CC_KEEP_IDLE DISABLE RX_CC_K_0_0 false RX_CC_K_0_1\
false RX_CC_K_0_2 false RX_CC_K_0_3 false RX_CC_K_1_0 false RX_CC_K_1_1 false\
RX_CC_K_1_2 false RX_CC_K_1_3 false RX_CC_LEN_SEQ 1 RX_CC_MASK_0_0 false\
RX_CC_MASK_0_1 false RX_CC_MASK_0_2 false RX_CC_MASK_0_3 false RX_CC_MASK_1_0\
false RX_CC_MASK_1_1 false RX_CC_MASK_1_2 false RX_CC_MASK_1_3 false\
RX_CC_NUM_SEQ 0 RX_CC_PERIODICITY 5000 RX_CC_PRECEDENCE ENABLE\
RX_CC_REPEAT_WAIT 0 RX_CC_VAL\
00000000000000000000000000000000000000000000000000000000000000000000000000000000\
RX_CC_VAL_0_0 0000000000 RX_CC_VAL_0_1 0000000000 RX_CC_VAL_0_2 0000000000\
RX_CC_VAL_0_3 0000000000 RX_CC_VAL_1_0 0000000000 RX_CC_VAL_1_1 0000000000\
RX_CC_VAL_1_2 0000000000 RX_CC_VAL_1_3 0000000000 RX_COMMA_ALIGN_WORD 1\
RX_COMMA_DOUBLE_ENABLE false RX_COMMA_MASK 1111111111 RX_COMMA_M_ENABLE false\
RX_COMMA_M_VAL 1010000011 RX_COMMA_PRESET NONE RX_COMMA_P_ENABLE false\
RX_COMMA_P_VAL 0101111100 RX_COMMA_SHOW_REALIGN_ENABLE true RX_COMMA_VALID_ONLY\
0 RX_COUPLING AC RX_DATA_DECODING RAW RX_EQ_MODE AUTO RX_FRACN_ENABLED false\
RX_FRACN_NUMERATOR 0 RX_INT_DATA_WIDTH 32 RX_JTOL_FC 0 RX_JTOL_LF_SLOPE -20\
RX_LINE_RATE 10.3125 RX_OUTCLK_SOURCE RXOUTCLKPMA RX_PLL_TYPE LCPLL\
RX_PPM_OFFSET 0 RX_REFCLK_FREQUENCY 156.25 RX_REFCLK_SOURCE R0 RX_SLIDE_MODE\
OFF RX_SSC_PPM 0 RX_TERMINATION PROGRAMMABLE RX_TERMINATION_PROG_VALUE 800\
RX_USER_DATA_WIDTH 32 TXPROGDIV_FREQ_ENABLE false TXPROGDIV_FREQ_SOURCE LCPLL\
TXPROGDIV_FREQ_VAL 322.265625 TX_64B66B_CRC false TX_RATE_GROUP A\
TX_64B66B_ENCODER false TX_64B66B_SCRAMBLER false TX_ACTUAL_REFCLK_FREQUENCY\
156.25 TX_BUFFER_BYPASS_MODE Fast_Sync TX_BUFFER_MODE 1\
TX_BUFFER_RESET_ON_RATE_CHANGE ENABLE TX_DATA_ENCODING RAW\
TX_DIFF_SWING_EMPH_MODE CUSTOM TX_FRACN_ENABLED false TX_FRACN_NUMERATOR 0\
TX_INT_DATA_WIDTH 32 TX_LINE_RATE 10.3125 TX_OUTCLK_SOURCE TXOUTCLKPMA\
TX_PIPM_ENABLE false TX_PLL_TYPE LCPLL TX_REFCLK_FREQUENCY 156.25\
TX_REFCLK_SOURCE R0 TX_USER_DATA_WIDTH 32}\
   CONFIG.PROT_OUTCLK_VALUES {CH0_RXOUTCLK 500 CH0_TXOUTCLK 500 CH1_RXOUTCLK 500 CH1_TXOUTCLK 500\
CH2_RXOUTCLK 500 CH2_TXOUTCLK 500 CH3_RXOUTCLK 500 CH3_TXOUTCLK 500}\
   CONFIG.REFCLK_STRING {HSCLK0_LCPLLGTREFCLK0 refclk_PROT0_R0_100_MHz_unique1 HSCLK1_LCPLLGTREFCLK0\
refclk_PROT0_R0_100_MHz_unique1}\
 ] $gt_quad_base_2

  # Create instance: urlp_2, and set properties
  set urlp_2 [ create_bd_cell -type ip -vlnv xilinx.com:ip:util_reduced_logic:2.0 urlp_2 ]
  set_property -dict [ list \
   CONFIG.C_SIZE {1} \
 ] $urlp_2

  # Create instance: util_ds_buf_2, and set properties
  set util_ds_buf_2 [ create_bd_cell -type ip -vlnv xilinx.com:ip:util_ds_buf:2.2 util_ds_buf_2 ]
  set_property -dict [ list \
   CONFIG.C_BUF_TYPE {IBUFDSGTE} \
 ] $util_ds_buf_2

  # Create instance: xlcp_2, and set properties
  set xlcp_2 [ create_bd_cell -type ip -vlnv xilinx.com:ip:xlconcat:2.1 xlcp_2 ]
  set_property -dict [ list \
   CONFIG.NUM_PORTS {1} \
 ] $xlcp_2

  # Create interface connections
  connect_bd_intf_net -intf_net bridge_refclkX1Y8_GT_RX0 [get_bd_intf_pins bridge_refclkX1Y8/GT_RX0] [get_bd_intf_pins gt_quad_base_2/RX0_GT_IP_Interface]
  connect_bd_intf_net -intf_net bridge_refclkX1Y8_GT_RX1 [get_bd_intf_pins bridge_refclkX1Y8/GT_RX1] [get_bd_intf_pins gt_quad_base_2/RX1_GT_IP_Interface]
  connect_bd_intf_net -intf_net bridge_refclkX1Y8_GT_RX2 [get_bd_intf_pins bridge_refclkX1Y8/GT_RX2] [get_bd_intf_pins gt_quad_base_2/RX2_GT_IP_Interface]
  connect_bd_intf_net -intf_net bridge_refclkX1Y8_GT_RX3 [get_bd_intf_pins bridge_refclkX1Y8/GT_RX3] [get_bd_intf_pins gt_quad_base_2/RX3_GT_IP_Interface]
  connect_bd_intf_net -intf_net bridge_refclkX1Y8_GT_TX0 [get_bd_intf_pins bridge_refclkX1Y8/GT_TX0] [get_bd_intf_pins gt_quad_base_2/TX0_GT_IP_Interface]
  connect_bd_intf_net -intf_net bridge_refclkX1Y8_GT_TX1 [get_bd_intf_pins bridge_refclkX1Y8/GT_TX1] [get_bd_intf_pins gt_quad_base_2/TX1_GT_IP_Interface]
  connect_bd_intf_net -intf_net bridge_refclkX1Y8_GT_TX2 [get_bd_intf_pins bridge_refclkX1Y8/GT_TX2] [get_bd_intf_pins gt_quad_base_2/TX2_GT_IP_Interface]
  connect_bd_intf_net -intf_net bridge_refclkX1Y8_GT_TX3 [get_bd_intf_pins bridge_refclkX1Y8/GT_TX3] [get_bd_intf_pins gt_quad_base_2/TX3_GT_IP_Interface]
  connect_bd_intf_net -intf_net bridge_refclkX1Y8_diff_gt_ref_clock_1 [get_bd_intf_pins bridge_refclkX1Y8_diff_gt_ref_clock] [get_bd_intf_pins util_ds_buf_2/CLK_IN_D]
  connect_bd_intf_net -intf_net gt_quad_base_2_GT_Serial [get_bd_intf_pins GT_Serial_2] [get_bd_intf_pins gt_quad_base_2/GT_Serial]

  # Create port connections
  connect_bd_net -net bufg_gt_4_usrclk [get_bd_pins bridge_refclkX1Y8/gt_rxusrclk] [get_bd_pins bufg_gt_4/usrclk] [get_bd_pins gt_quad_base_2/ch0_rxusrclk] [get_bd_pins gt_quad_base_2/ch1_rxusrclk] [get_bd_pins gt_quad_base_2/ch2_rxusrclk] [get_bd_pins gt_quad_base_2/ch3_rxusrclk]
  connect_bd_net -net bufg_gt_5_usrclk [get_bd_pins bridge_refclkX1Y8/gt_txusrclk] [get_bd_pins bufg_gt_5/usrclk] [get_bd_pins gt_quad_base_2/ch0_txusrclk] [get_bd_pins gt_quad_base_2/ch1_txusrclk] [get_bd_pins gt_quad_base_2/ch2_txusrclk] [get_bd_pins gt_quad_base_2/ch3_txusrclk]
  connect_bd_net -net gt_quad_base_2_ch0_rxoutclk [get_bd_pins bufg_gt_4/outclk] [get_bd_pins gt_quad_base_2/ch0_rxoutclk]
  connect_bd_net -net gt_quad_base_2_ch0_txoutclk [get_bd_pins bufg_gt_5/outclk] [get_bd_pins gt_quad_base_2/ch0_txoutclk]
  connect_bd_net -net gt_quad_base_2_gtpowergood [get_bd_pins gt_quad_base_2/gtpowergood] [get_bd_pins xlcp_2/In0]
  connect_bd_net -net urlp_2_Res [get_bd_pins bridge_refclkX1Y8/gtpowergood] [get_bd_pins urlp_2/Res]
  connect_bd_net -net util_ds_buf_2_IBUF_OUT [get_bd_pins gt_quad_base_2/GT_REFCLK0] [get_bd_pins util_ds_buf_2/IBUF_OUT]
  connect_bd_net -net versal_cips_0_pl0_ref_clk [get_bd_pins apb3clk] [get_bd_pins bridge_refclkX1Y8/apb3clk] [get_bd_pins gt_quad_base_2/apb3clk]
  connect_bd_net -net xlcp_2_dout [get_bd_pins urlp_2/Op1] [get_bd_pins xlcp_2/dout]

  # Restore current instance
  current_bd_instance $oldCurInst
}

# Hierarchical cell: gty_quad_201
proc create_hier_cell_gty_quad_201 { parentCell nameHier } {

  variable script_folder

  if { $parentCell eq "" || $nameHier eq "" } {
     catch {common::send_gid_msg -ssname BD::TCL -id 2092 -severity "ERROR" "create_hier_cell_gty_quad_201() - Empty argument(s)!"}
     return
  }

  # Get object for parentCell
  set parentObj [get_bd_cells $parentCell]
  if { $parentObj == "" } {
     catch {common::send_gid_msg -ssname BD::TCL -id 2090 -severity "ERROR" "Unable to find parent cell <$parentCell>!"}
     return
  }

  # Make sure parentObj is hier blk
  set parentType [get_property TYPE $parentObj]
  if { $parentType ne "hier" } {
     catch {common::send_gid_msg -ssname BD::TCL -id 2091 -severity "ERROR" "Parent <$parentObj> has TYPE = <$parentType>. Expected to be <hier>."}
     return
  }

  # Save current instance; Restore later
  set oldCurInst [current_bd_instance .]

  # Set parent object as current
  current_bd_instance $parentObj

  # Create cell and set as current instance
  set hier_obj [create_bd_cell -type hier $nameHier]
  current_bd_instance $hier_obj

  # Create interface pins
  create_bd_intf_pin -mode Master -vlnv xilinx.com:interface:gt_rtl:1.0 GT_Serial_1

  create_bd_intf_pin -mode Slave -vlnv xilinx.com:interface:diff_clock_rtl:1.0 bridge_refclkX1Y2_diff_gt_ref_clock


  # Create pins
  create_bd_pin -dir I -type clk apb3clk

  # Create instance: bridge_refclkX1Y2, and set properties
  set bridge_refclkX1Y2 [ create_bd_cell -type ip -vlnv xilinx.com:ip:gt_bridge_ip:1.1 bridge_refclkX1Y2 ]
  set_property -dict [ list \
   CONFIG.IP_LR0_SETTINGS {GT_DIRECTION DUPLEX  GT_TYPE GTY  INS_LOSS_NYQ 20  INTERNAL_PRESET None \
OOB_ENABLE false  PCIE_ENABLE false  PCIE_USERCLK2_FREQ 250  PCIE_USERCLK_FREQ\
250  PRESET None  RESET_SEQUENCE_INTERVAL 0  RXPROGDIV_FREQ_ENABLE false \
RXPROGDIV_FREQ_SOURCE LCPLL  RXPROGDIV_FREQ_VAL 322.265625  RX_64B66B_CRC false\
RX_64B66B_DECODER false  RX_64B66B_DESCRAMBLER false \
RX_ACTUAL_REFCLK_FREQUENCY 100.000000000000  RX_BUFFER_BYPASS_MODE Fast_Sync \
RX_BUFFER_BYPASS_MODE_LANE MULTI  RX_BUFFER_MODE 1 \
RX_BUFFER_RESET_ON_CB_CHANGE ENABLE  RX_BUFFER_RESET_ON_COMMAALIGN DISABLE \
RX_BUFFER_RESET_ON_RATE_CHANGE ENABLE  RX_CB_DISP_0_0 false  RX_CB_DISP_0_1\
false  RX_CB_DISP_0_2 false  RX_CB_DISP_0_3 false  RX_CB_DISP_1_0 false \
RX_CB_DISP_1_1 false  RX_CB_DISP_1_2 false  RX_CB_DISP_1_3 false  RX_CB_K_0_0\
false  RX_CB_K_0_1 false  RX_CB_K_0_2 false  RX_CB_K_0_3 false  RX_CB_K_1_0\
false  RX_CB_K_1_1 false  RX_CB_K_1_2 false  RX_CB_K_1_3 false  RX_CB_LEN_SEQ 1\
RX_CB_MASK_0_0 false  RX_CB_MASK_0_1 false  RX_CB_MASK_0_2 false \
RX_CB_MASK_0_3 false  RX_CB_MASK_1_0 false  RX_CB_MASK_1_1 false \
RX_CB_MASK_1_2 false  RX_CB_MASK_1_3 false  RX_CB_MAX_LEVEL 1  RX_CB_MAX_SKEW 1\
RX_CB_NUM_SEQ 0  RX_CB_VAL_0_0 00000000  RX_CB_VAL_0_1 00000000  RX_CB_VAL_0_2\
00000000  RX_CB_VAL_0_3 00000000  RX_CB_VAL_1_0 00000000  RX_CB_VAL_1_1\
00000000  RX_CB_VAL_1_2 00000000  RX_CB_VAL_1_3 00000000  RX_CC_DISP_0_0 false \
RX_CC_DISP_0_1 false  RX_CC_DISP_0_2 false  RX_CC_DISP_0_3 false \
RX_CC_DISP_1_0 false  RX_CC_DISP_1_1 false  RX_CC_DISP_1_2 false \
RX_CC_DISP_1_3 false  RX_CC_KEEP_IDLE DISABLE  RX_CC_K_0_0 false  RX_CC_K_0_1\
false  RX_CC_K_0_2 false  RX_CC_K_0_3 false  RX_CC_K_1_0 false  RX_CC_K_1_1\
false  RX_CC_K_1_2 false  RX_CC_K_1_3 false  RX_CC_LEN_SEQ 1  RX_CC_MASK_0_0\
false  RX_CC_MASK_0_1 false  RX_CC_MASK_0_2 false  RX_CC_MASK_0_3 false \
RX_CC_MASK_1_0 false  RX_CC_MASK_1_1 false  RX_CC_MASK_1_2 false \
RX_CC_MASK_1_3 false  RX_CC_NUM_SEQ 0  RX_CC_PERIODICITY 5000  RX_CC_PRECEDENCE\
ENABLE  RX_CC_REPEAT_WAIT 0  RX_CC_VAL\
00000000000000000000000000000000000000000000000000000000000000000000000000000000\
RX_CC_VAL_0_0 00000000  RX_CC_VAL_0_1 00000000  RX_CC_VAL_0_2 00000000 \
RX_CC_VAL_0_3 00000000  RX_CC_VAL_1_0 00000000  RX_CC_VAL_1_1 00000000 \
RX_CC_VAL_1_2 00000000  RX_CC_VAL_1_3 00000000  RX_COMMA_ALIGN_WORD 1 \
RX_COMMA_DOUBLE_ENABLE false  RX_COMMA_MASK 0000000000  RX_COMMA_M_ENABLE false\
RX_COMMA_M_VAL 1010000011  RX_COMMA_PRESET NONE  RX_COMMA_P_ENABLE false \
RX_COMMA_P_VAL 0101111100  RX_COMMA_SHOW_REALIGN_ENABLE true \
RX_COMMA_VALID_ONLY 0  RX_COUPLING AC  RX_DATA_DECODING RAW  RX_EQ_MODE AUTO \
RX_FRACN_ENABLED true  RX_FRACN_NUMERATOR 0  RX_GRAY_BYP true \
RX_GRAY_LITTLEENDIAN true  RX_INT_DATA_WIDTH 32  RX_JTOL_FC 6.1862627 \
RX_JTOL_LF_SLOPE -20  RX_LINE_RATE 10.3125  RX_OUTCLK_SOURCE RXOUTCLKPMA \
RX_PAM_SEL NRZ  RX_PLL_TYPE LCPLL  RX_PPM_OFFSET 0  RX_PRECODE_BYP true \
RX_PRECODE_LITTLEENDIAN false  RX_RATE_GROUP A  RX_REFCLK_FREQUENCY 100 \
RX_REFCLK_SOURCE R0  RX_SLIDE_MODE OFF  RX_SSC_PPM 0  RX_TERMINATION\
PROGRAMMABLE  RX_TERMINATION_PROG_VALUE 800  RX_USER_DATA_WIDTH 32 \
TXPROGDIV_FREQ_ENABLE false  TXPROGDIV_FREQ_SOURCE LCPLL  TXPROGDIV_FREQ_VAL\
322.265625  TX_64B66B_CRC false  TX_64B66B_ENCODER false  TX_64B66B_SCRAMBLER\
false  TX_ACTUAL_REFCLK_FREQUENCY 100.000000000000  TX_BUFFER_BYPASS_MODE\
Fast_Sync  TX_BUFFER_MODE 1  TX_BUFFER_RESET_ON_RATE_CHANGE ENABLE \
TX_DATA_ENCODING RAW  TX_DIFF_SWING_EMPH_MODE CUSTOM  TX_FRACN_ENABLED true \
TX_FRACN_NUMERATOR 0  TX_GRAY_BYP true  TX_GRAY_LITTLEENDIAN true \
TX_INT_DATA_WIDTH 32  TX_LINE_RATE 10.3125  TX_OUTCLK_SOURCE TXOUTCLKPMA \
TX_PAM_SEL NRZ  TX_PIPM_ENABLE false  TX_PLL_TYPE LCPLL  TX_PRECODE_BYP true \
TX_PRECODE_LITTLEENDIAN false  TX_RATE_GROUP A  TX_REFCLK_FREQUENCY 100 \
TX_REFCLK_SOURCE R0  TX_USER_DATA_WIDTH 32}\
   CONFIG.IP_NO_OF_LANES {4} \
 ] $bridge_refclkX1Y2

  # Create instance: bufg_gt_2, and set properties
  set bufg_gt_2 [ create_bd_cell -type ip -vlnv xilinx.com:ip:bufg_gt:1.0 bufg_gt_2 ]

  # Create instance: bufg_gt_3, and set properties
  set bufg_gt_3 [ create_bd_cell -type ip -vlnv xilinx.com:ip:bufg_gt:1.0 bufg_gt_3 ]

  # Create instance: gt_quad_base_1, and set properties
  set gt_quad_base_1 [ create_bd_cell -type ip -vlnv xilinx.com:ip:gt_quad_base:1.1 gt_quad_base_1 ]
  set_property -dict [ list \
   CONFIG.PORTS_INFO_DICT {LANE_SEL_DICT {PROT0 {RX0 RX1 RX2 RX3 TX0 TX1 TX2 TX3}} GT_TYPE GTY\
REG_CONF_INTF APB3_INTF BOARD_INTERFACE false}\
   CONFIG.PROT1_LR0_SETTINGS {GT_TYPE GTY GT_DIRECTION DUPLEX INS_LOSS_NYQ 20 INTERNAL_PRESET None OOB_ENABLE\
false PCIE_ENABLE false PCIE_USERCLK2_FREQ 250 PCIE_USERCLK_FREQ 250 PRESET\
None RESET_SEQUENCE_INTERVAL 0 RXPROGDIV_FREQ_ENABLE false\
RXPROGDIV_FREQ_SOURCE LCPLL RXPROGDIV_FREQ_VAL 322.265625 RX_64B66B_CRC false\
RX_RATE_GROUP A RX_64B66B_DECODER false RX_64B66B_DESCRAMBLER false\
RX_ACTUAL_REFCLK_FREQUENCY 156.25 RX_BUFFER_BYPASS_MODE Fast_Sync\
RX_BUFFER_BYPASS_MODE_LANE MULTI RX_BUFFER_MODE 1 RX_BUFFER_RESET_ON_CB_CHANGE\
ENABLE RX_BUFFER_RESET_ON_COMMAALIGN DISABLE RX_BUFFER_RESET_ON_RATE_CHANGE\
ENABLE RX_CB_DISP_0_0 false RX_CB_DISP_0_1 false RX_CB_DISP_0_2 false\
RX_CB_DISP_0_3 false RX_CB_DISP_1_0 false RX_CB_DISP_1_1 false RX_CB_DISP_1_2\
false RX_CB_DISP_1_3 false RX_CB_K_0_0 false RX_CB_K_0_1 false RX_CB_K_0_2\
false RX_CB_K_0_3 false RX_CB_K_1_0 false RX_CB_K_1_1 false RX_CB_K_1_2 false\
RX_CB_K_1_3 false RX_CB_LEN_SEQ 1 RX_CB_MASK_0_0 false RX_CB_MASK_0_1 false\
RX_CB_MASK_0_2 false RX_CB_MASK_0_3 false RX_CB_MASK_1_0 false RX_CB_MASK_1_1\
false RX_CB_MASK_1_2 false RX_CB_MASK_1_3 false RX_CB_MAX_LEVEL 1\
RX_CB_MAX_SKEW 1 RX_CB_NUM_SEQ 0 RX_CB_VAL_0_0 00000000 RX_CB_VAL_0_1 00000000\
RX_CB_VAL_0_2 00000000 RX_CB_VAL_0_3 00000000 RX_CB_VAL_1_0 00000000\
RX_CB_VAL_1_1 00000000 RX_CB_VAL_1_2 00000000 RX_CB_VAL_1_3 00000000\
RX_CC_DISP_0_0 false RX_CC_DISP_0_1 false RX_CC_DISP_0_2 false RX_CC_DISP_0_3\
false RX_CC_DISP_1_0 false RX_CC_DISP_1_1 false RX_CC_DISP_1_2 false\
RX_CC_DISP_1_3 false RX_CC_KEEP_IDLE DISABLE RX_CC_K_0_0 false RX_CC_K_0_1\
false RX_CC_K_0_2 false RX_CC_K_0_3 false RX_CC_K_1_0 false RX_CC_K_1_1 false\
RX_CC_K_1_2 false RX_CC_K_1_3 false RX_CC_LEN_SEQ 1 RX_CC_MASK_0_0 false\
RX_CC_MASK_0_1 false RX_CC_MASK_0_2 false RX_CC_MASK_0_3 false RX_CC_MASK_1_0\
false RX_CC_MASK_1_1 false RX_CC_MASK_1_2 false RX_CC_MASK_1_3 false\
RX_CC_NUM_SEQ 0 RX_CC_PERIODICITY 5000 RX_CC_PRECEDENCE ENABLE\
RX_CC_REPEAT_WAIT 0 RX_CC_VAL\
00000000000000000000000000000000000000000000000000000000000000000000000000000000\
RX_CC_VAL_0_0 0000000000 RX_CC_VAL_0_1 0000000000 RX_CC_VAL_0_2 0000000000\
RX_CC_VAL_0_3 0000000000 RX_CC_VAL_1_0 0000000000 RX_CC_VAL_1_1 0000000000\
RX_CC_VAL_1_2 0000000000 RX_CC_VAL_1_3 0000000000 RX_COMMA_ALIGN_WORD 1\
RX_COMMA_DOUBLE_ENABLE false RX_COMMA_MASK 1111111111 RX_COMMA_M_ENABLE false\
RX_COMMA_M_VAL 1010000011 RX_COMMA_PRESET NONE RX_COMMA_P_ENABLE false\
RX_COMMA_P_VAL 0101111100 RX_COMMA_SHOW_REALIGN_ENABLE true RX_COMMA_VALID_ONLY\
0 RX_COUPLING AC RX_DATA_DECODING RAW RX_EQ_MODE AUTO RX_FRACN_ENABLED false\
RX_FRACN_NUMERATOR 0 RX_INT_DATA_WIDTH 32 RX_JTOL_FC 0 RX_JTOL_LF_SLOPE -20\
RX_LINE_RATE 10.3125 RX_OUTCLK_SOURCE RXOUTCLKPMA RX_PLL_TYPE LCPLL\
RX_PPM_OFFSET 0 RX_REFCLK_FREQUENCY 156.25 RX_REFCLK_SOURCE R0 RX_SLIDE_MODE\
OFF RX_SSC_PPM 0 RX_TERMINATION PROGRAMMABLE RX_TERMINATION_PROG_VALUE 800\
RX_USER_DATA_WIDTH 32 TXPROGDIV_FREQ_ENABLE false TXPROGDIV_FREQ_SOURCE LCPLL\
TXPROGDIV_FREQ_VAL 322.265625 TX_64B66B_CRC false TX_RATE_GROUP A\
TX_64B66B_ENCODER false TX_64B66B_SCRAMBLER false TX_ACTUAL_REFCLK_FREQUENCY\
156.25 TX_BUFFER_BYPASS_MODE Fast_Sync TX_BUFFER_MODE 1\
TX_BUFFER_RESET_ON_RATE_CHANGE ENABLE TX_DATA_ENCODING RAW\
TX_DIFF_SWING_EMPH_MODE CUSTOM TX_FRACN_ENABLED false TX_FRACN_NUMERATOR 0\
TX_INT_DATA_WIDTH 32 TX_LINE_RATE 10.3125 TX_OUTCLK_SOURCE TXOUTCLKPMA\
TX_PIPM_ENABLE false TX_PLL_TYPE LCPLL TX_REFCLK_FREQUENCY 156.25\
TX_REFCLK_SOURCE R0 TX_USER_DATA_WIDTH 32}\
   CONFIG.PROT2_LR0_SETTINGS {GT_TYPE GTY GT_DIRECTION DUPLEX INS_LOSS_NYQ 20 INTERNAL_PRESET None OOB_ENABLE\
false PCIE_ENABLE false PCIE_USERCLK2_FREQ 250 PCIE_USERCLK_FREQ 250 PRESET\
None RESET_SEQUENCE_INTERVAL 0 RXPROGDIV_FREQ_ENABLE false\
RXPROGDIV_FREQ_SOURCE LCPLL RXPROGDIV_FREQ_VAL 322.265625 RX_64B66B_CRC false\
RX_RATE_GROUP A RX_64B66B_DECODER false RX_64B66B_DESCRAMBLER false\
RX_ACTUAL_REFCLK_FREQUENCY 156.25 RX_BUFFER_BYPASS_MODE Fast_Sync\
RX_BUFFER_BYPASS_MODE_LANE MULTI RX_BUFFER_MODE 1 RX_BUFFER_RESET_ON_CB_CHANGE\
ENABLE RX_BUFFER_RESET_ON_COMMAALIGN DISABLE RX_BUFFER_RESET_ON_RATE_CHANGE\
ENABLE RX_CB_DISP_0_0 false RX_CB_DISP_0_1 false RX_CB_DISP_0_2 false\
RX_CB_DISP_0_3 false RX_CB_DISP_1_0 false RX_CB_DISP_1_1 false RX_CB_DISP_1_2\
false RX_CB_DISP_1_3 false RX_CB_K_0_0 false RX_CB_K_0_1 false RX_CB_K_0_2\
false RX_CB_K_0_3 false RX_CB_K_1_0 false RX_CB_K_1_1 false RX_CB_K_1_2 false\
RX_CB_K_1_3 false RX_CB_LEN_SEQ 1 RX_CB_MASK_0_0 false RX_CB_MASK_0_1 false\
RX_CB_MASK_0_2 false RX_CB_MASK_0_3 false RX_CB_MASK_1_0 false RX_CB_MASK_1_1\
false RX_CB_MASK_1_2 false RX_CB_MASK_1_3 false RX_CB_MAX_LEVEL 1\
RX_CB_MAX_SKEW 1 RX_CB_NUM_SEQ 0 RX_CB_VAL_0_0 00000000 RX_CB_VAL_0_1 00000000\
RX_CB_VAL_0_2 00000000 RX_CB_VAL_0_3 00000000 RX_CB_VAL_1_0 00000000\
RX_CB_VAL_1_1 00000000 RX_CB_VAL_1_2 00000000 RX_CB_VAL_1_3 00000000\
RX_CC_DISP_0_0 false RX_CC_DISP_0_1 false RX_CC_DISP_0_2 false RX_CC_DISP_0_3\
false RX_CC_DISP_1_0 false RX_CC_DISP_1_1 false RX_CC_DISP_1_2 false\
RX_CC_DISP_1_3 false RX_CC_KEEP_IDLE DISABLE RX_CC_K_0_0 false RX_CC_K_0_1\
false RX_CC_K_0_2 false RX_CC_K_0_3 false RX_CC_K_1_0 false RX_CC_K_1_1 false\
RX_CC_K_1_2 false RX_CC_K_1_3 false RX_CC_LEN_SEQ 1 RX_CC_MASK_0_0 false\
RX_CC_MASK_0_1 false RX_CC_MASK_0_2 false RX_CC_MASK_0_3 false RX_CC_MASK_1_0\
false RX_CC_MASK_1_1 false RX_CC_MASK_1_2 false RX_CC_MASK_1_3 false\
RX_CC_NUM_SEQ 0 RX_CC_PERIODICITY 5000 RX_CC_PRECEDENCE ENABLE\
RX_CC_REPEAT_WAIT 0 RX_CC_VAL\
00000000000000000000000000000000000000000000000000000000000000000000000000000000\
RX_CC_VAL_0_0 0000000000 RX_CC_VAL_0_1 0000000000 RX_CC_VAL_0_2 0000000000\
RX_CC_VAL_0_3 0000000000 RX_CC_VAL_1_0 0000000000 RX_CC_VAL_1_1 0000000000\
RX_CC_VAL_1_2 0000000000 RX_CC_VAL_1_3 0000000000 RX_COMMA_ALIGN_WORD 1\
RX_COMMA_DOUBLE_ENABLE false RX_COMMA_MASK 1111111111 RX_COMMA_M_ENABLE false\
RX_COMMA_M_VAL 1010000011 RX_COMMA_PRESET NONE RX_COMMA_P_ENABLE false\
RX_COMMA_P_VAL 0101111100 RX_COMMA_SHOW_REALIGN_ENABLE true RX_COMMA_VALID_ONLY\
0 RX_COUPLING AC RX_DATA_DECODING RAW RX_EQ_MODE AUTO RX_FRACN_ENABLED false\
RX_FRACN_NUMERATOR 0 RX_INT_DATA_WIDTH 32 RX_JTOL_FC 0 RX_JTOL_LF_SLOPE -20\
RX_LINE_RATE 10.3125 RX_OUTCLK_SOURCE RXOUTCLKPMA RX_PLL_TYPE LCPLL\
RX_PPM_OFFSET 0 RX_REFCLK_FREQUENCY 156.25 RX_REFCLK_SOURCE R0 RX_SLIDE_MODE\
OFF RX_SSC_PPM 0 RX_TERMINATION PROGRAMMABLE RX_TERMINATION_PROG_VALUE 800\
RX_USER_DATA_WIDTH 32 TXPROGDIV_FREQ_ENABLE false TXPROGDIV_FREQ_SOURCE LCPLL\
TXPROGDIV_FREQ_VAL 322.265625 TX_64B66B_CRC false TX_RATE_GROUP A\
TX_64B66B_ENCODER false TX_64B66B_SCRAMBLER false TX_ACTUAL_REFCLK_FREQUENCY\
156.25 TX_BUFFER_BYPASS_MODE Fast_Sync TX_BUFFER_MODE 1\
TX_BUFFER_RESET_ON_RATE_CHANGE ENABLE TX_DATA_ENCODING RAW\
TX_DIFF_SWING_EMPH_MODE CUSTOM TX_FRACN_ENABLED false TX_FRACN_NUMERATOR 0\
TX_INT_DATA_WIDTH 32 TX_LINE_RATE 10.3125 TX_OUTCLK_SOURCE TXOUTCLKPMA\
TX_PIPM_ENABLE false TX_PLL_TYPE LCPLL TX_REFCLK_FREQUENCY 156.25\
TX_REFCLK_SOURCE R0 TX_USER_DATA_WIDTH 32}\
   CONFIG.PROT3_LR0_SETTINGS {GT_TYPE GTY GT_DIRECTION DUPLEX INS_LOSS_NYQ 20 INTERNAL_PRESET None OOB_ENABLE\
false PCIE_ENABLE false PCIE_USERCLK2_FREQ 250 PCIE_USERCLK_FREQ 250 PRESET\
None RESET_SEQUENCE_INTERVAL 0 RXPROGDIV_FREQ_ENABLE false\
RXPROGDIV_FREQ_SOURCE LCPLL RXPROGDIV_FREQ_VAL 322.265625 RX_64B66B_CRC false\
RX_RATE_GROUP A RX_64B66B_DECODER false RX_64B66B_DESCRAMBLER false\
RX_ACTUAL_REFCLK_FREQUENCY 156.25 RX_BUFFER_BYPASS_MODE Fast_Sync\
RX_BUFFER_BYPASS_MODE_LANE MULTI RX_BUFFER_MODE 1 RX_BUFFER_RESET_ON_CB_CHANGE\
ENABLE RX_BUFFER_RESET_ON_COMMAALIGN DISABLE RX_BUFFER_RESET_ON_RATE_CHANGE\
ENABLE RX_CB_DISP_0_0 false RX_CB_DISP_0_1 false RX_CB_DISP_0_2 false\
RX_CB_DISP_0_3 false RX_CB_DISP_1_0 false RX_CB_DISP_1_1 false RX_CB_DISP_1_2\
false RX_CB_DISP_1_3 false RX_CB_K_0_0 false RX_CB_K_0_1 false RX_CB_K_0_2\
false RX_CB_K_0_3 false RX_CB_K_1_0 false RX_CB_K_1_1 false RX_CB_K_1_2 false\
RX_CB_K_1_3 false RX_CB_LEN_SEQ 1 RX_CB_MASK_0_0 false RX_CB_MASK_0_1 false\
RX_CB_MASK_0_2 false RX_CB_MASK_0_3 false RX_CB_MASK_1_0 false RX_CB_MASK_1_1\
false RX_CB_MASK_1_2 false RX_CB_MASK_1_3 false RX_CB_MAX_LEVEL 1\
RX_CB_MAX_SKEW 1 RX_CB_NUM_SEQ 0 RX_CB_VAL_0_0 00000000 RX_CB_VAL_0_1 00000000\
RX_CB_VAL_0_2 00000000 RX_CB_VAL_0_3 00000000 RX_CB_VAL_1_0 00000000\
RX_CB_VAL_1_1 00000000 RX_CB_VAL_1_2 00000000 RX_CB_VAL_1_3 00000000\
RX_CC_DISP_0_0 false RX_CC_DISP_0_1 false RX_CC_DISP_0_2 false RX_CC_DISP_0_3\
false RX_CC_DISP_1_0 false RX_CC_DISP_1_1 false RX_CC_DISP_1_2 false\
RX_CC_DISP_1_3 false RX_CC_KEEP_IDLE DISABLE RX_CC_K_0_0 false RX_CC_K_0_1\
false RX_CC_K_0_2 false RX_CC_K_0_3 false RX_CC_K_1_0 false RX_CC_K_1_1 false\
RX_CC_K_1_2 false RX_CC_K_1_3 false RX_CC_LEN_SEQ 1 RX_CC_MASK_0_0 false\
RX_CC_MASK_0_1 false RX_CC_MASK_0_2 false RX_CC_MASK_0_3 false RX_CC_MASK_1_0\
false RX_CC_MASK_1_1 false RX_CC_MASK_1_2 false RX_CC_MASK_1_3 false\
RX_CC_NUM_SEQ 0 RX_CC_PERIODICITY 5000 RX_CC_PRECEDENCE ENABLE\
RX_CC_REPEAT_WAIT 0 RX_CC_VAL\
00000000000000000000000000000000000000000000000000000000000000000000000000000000\
RX_CC_VAL_0_0 0000000000 RX_CC_VAL_0_1 0000000000 RX_CC_VAL_0_2 0000000000\
RX_CC_VAL_0_3 0000000000 RX_CC_VAL_1_0 0000000000 RX_CC_VAL_1_1 0000000000\
RX_CC_VAL_1_2 0000000000 RX_CC_VAL_1_3 0000000000 RX_COMMA_ALIGN_WORD 1\
RX_COMMA_DOUBLE_ENABLE false RX_COMMA_MASK 1111111111 RX_COMMA_M_ENABLE false\
RX_COMMA_M_VAL 1010000011 RX_COMMA_PRESET NONE RX_COMMA_P_ENABLE false\
RX_COMMA_P_VAL 0101111100 RX_COMMA_SHOW_REALIGN_ENABLE true RX_COMMA_VALID_ONLY\
0 RX_COUPLING AC RX_DATA_DECODING RAW RX_EQ_MODE AUTO RX_FRACN_ENABLED false\
RX_FRACN_NUMERATOR 0 RX_INT_DATA_WIDTH 32 RX_JTOL_FC 0 RX_JTOL_LF_SLOPE -20\
RX_LINE_RATE 10.3125 RX_OUTCLK_SOURCE RXOUTCLKPMA RX_PLL_TYPE LCPLL\
RX_PPM_OFFSET 0 RX_REFCLK_FREQUENCY 156.25 RX_REFCLK_SOURCE R0 RX_SLIDE_MODE\
OFF RX_SSC_PPM 0 RX_TERMINATION PROGRAMMABLE RX_TERMINATION_PROG_VALUE 800\
RX_USER_DATA_WIDTH 32 TXPROGDIV_FREQ_ENABLE false TXPROGDIV_FREQ_SOURCE LCPLL\
TXPROGDIV_FREQ_VAL 322.265625 TX_64B66B_CRC false TX_RATE_GROUP A\
TX_64B66B_ENCODER false TX_64B66B_SCRAMBLER false TX_ACTUAL_REFCLK_FREQUENCY\
156.25 TX_BUFFER_BYPASS_MODE Fast_Sync TX_BUFFER_MODE 1\
TX_BUFFER_RESET_ON_RATE_CHANGE ENABLE TX_DATA_ENCODING RAW\
TX_DIFF_SWING_EMPH_MODE CUSTOM TX_FRACN_ENABLED false TX_FRACN_NUMERATOR 0\
TX_INT_DATA_WIDTH 32 TX_LINE_RATE 10.3125 TX_OUTCLK_SOURCE TXOUTCLKPMA\
TX_PIPM_ENABLE false TX_PLL_TYPE LCPLL TX_REFCLK_FREQUENCY 156.25\
TX_REFCLK_SOURCE R0 TX_USER_DATA_WIDTH 32}\
   CONFIG.PROT4_LR0_SETTINGS {GT_TYPE GTY GT_DIRECTION DUPLEX INS_LOSS_NYQ 20 INTERNAL_PRESET None OOB_ENABLE\
false PCIE_ENABLE false PCIE_USERCLK2_FREQ 250 PCIE_USERCLK_FREQ 250 PRESET\
None RESET_SEQUENCE_INTERVAL 0 RXPROGDIV_FREQ_ENABLE false\
RXPROGDIV_FREQ_SOURCE LCPLL RXPROGDIV_FREQ_VAL 322.265625 RX_64B66B_CRC false\
RX_RATE_GROUP A RX_64B66B_DECODER false RX_64B66B_DESCRAMBLER false\
RX_ACTUAL_REFCLK_FREQUENCY 156.25 RX_BUFFER_BYPASS_MODE Fast_Sync\
RX_BUFFER_BYPASS_MODE_LANE MULTI RX_BUFFER_MODE 1 RX_BUFFER_RESET_ON_CB_CHANGE\
ENABLE RX_BUFFER_RESET_ON_COMMAALIGN DISABLE RX_BUFFER_RESET_ON_RATE_CHANGE\
ENABLE RX_CB_DISP_0_0 false RX_CB_DISP_0_1 false RX_CB_DISP_0_2 false\
RX_CB_DISP_0_3 false RX_CB_DISP_1_0 false RX_CB_DISP_1_1 false RX_CB_DISP_1_2\
false RX_CB_DISP_1_3 false RX_CB_K_0_0 false RX_CB_K_0_1 false RX_CB_K_0_2\
false RX_CB_K_0_3 false RX_CB_K_1_0 false RX_CB_K_1_1 false RX_CB_K_1_2 false\
RX_CB_K_1_3 false RX_CB_LEN_SEQ 1 RX_CB_MASK_0_0 false RX_CB_MASK_0_1 false\
RX_CB_MASK_0_2 false RX_CB_MASK_0_3 false RX_CB_MASK_1_0 false RX_CB_MASK_1_1\
false RX_CB_MASK_1_2 false RX_CB_MASK_1_3 false RX_CB_MAX_LEVEL 1\
RX_CB_MAX_SKEW 1 RX_CB_NUM_SEQ 0 RX_CB_VAL_0_0 00000000 RX_CB_VAL_0_1 00000000\
RX_CB_VAL_0_2 00000000 RX_CB_VAL_0_3 00000000 RX_CB_VAL_1_0 00000000\
RX_CB_VAL_1_1 00000000 RX_CB_VAL_1_2 00000000 RX_CB_VAL_1_3 00000000\
RX_CC_DISP_0_0 false RX_CC_DISP_0_1 false RX_CC_DISP_0_2 false RX_CC_DISP_0_3\
false RX_CC_DISP_1_0 false RX_CC_DISP_1_1 false RX_CC_DISP_1_2 false\
RX_CC_DISP_1_3 false RX_CC_KEEP_IDLE DISABLE RX_CC_K_0_0 false RX_CC_K_0_1\
false RX_CC_K_0_2 false RX_CC_K_0_3 false RX_CC_K_1_0 false RX_CC_K_1_1 false\
RX_CC_K_1_2 false RX_CC_K_1_3 false RX_CC_LEN_SEQ 1 RX_CC_MASK_0_0 false\
RX_CC_MASK_0_1 false RX_CC_MASK_0_2 false RX_CC_MASK_0_3 false RX_CC_MASK_1_0\
false RX_CC_MASK_1_1 false RX_CC_MASK_1_2 false RX_CC_MASK_1_3 false\
RX_CC_NUM_SEQ 0 RX_CC_PERIODICITY 5000 RX_CC_PRECEDENCE ENABLE\
RX_CC_REPEAT_WAIT 0 RX_CC_VAL\
00000000000000000000000000000000000000000000000000000000000000000000000000000000\
RX_CC_VAL_0_0 0000000000 RX_CC_VAL_0_1 0000000000 RX_CC_VAL_0_2 0000000000\
RX_CC_VAL_0_3 0000000000 RX_CC_VAL_1_0 0000000000 RX_CC_VAL_1_1 0000000000\
RX_CC_VAL_1_2 0000000000 RX_CC_VAL_1_3 0000000000 RX_COMMA_ALIGN_WORD 1\
RX_COMMA_DOUBLE_ENABLE false RX_COMMA_MASK 1111111111 RX_COMMA_M_ENABLE false\
RX_COMMA_M_VAL 1010000011 RX_COMMA_PRESET NONE RX_COMMA_P_ENABLE false\
RX_COMMA_P_VAL 0101111100 RX_COMMA_SHOW_REALIGN_ENABLE true RX_COMMA_VALID_ONLY\
0 RX_COUPLING AC RX_DATA_DECODING RAW RX_EQ_MODE AUTO RX_FRACN_ENABLED false\
RX_FRACN_NUMERATOR 0 RX_INT_DATA_WIDTH 32 RX_JTOL_FC 0 RX_JTOL_LF_SLOPE -20\
RX_LINE_RATE 10.3125 RX_OUTCLK_SOURCE RXOUTCLKPMA RX_PLL_TYPE LCPLL\
RX_PPM_OFFSET 0 RX_REFCLK_FREQUENCY 156.25 RX_REFCLK_SOURCE R0 RX_SLIDE_MODE\
OFF RX_SSC_PPM 0 RX_TERMINATION PROGRAMMABLE RX_TERMINATION_PROG_VALUE 800\
RX_USER_DATA_WIDTH 32 TXPROGDIV_FREQ_ENABLE false TXPROGDIV_FREQ_SOURCE LCPLL\
TXPROGDIV_FREQ_VAL 322.265625 TX_64B66B_CRC false TX_RATE_GROUP A\
TX_64B66B_ENCODER false TX_64B66B_SCRAMBLER false TX_ACTUAL_REFCLK_FREQUENCY\
156.25 TX_BUFFER_BYPASS_MODE Fast_Sync TX_BUFFER_MODE 1\
TX_BUFFER_RESET_ON_RATE_CHANGE ENABLE TX_DATA_ENCODING RAW\
TX_DIFF_SWING_EMPH_MODE CUSTOM TX_FRACN_ENABLED false TX_FRACN_NUMERATOR 0\
TX_INT_DATA_WIDTH 32 TX_LINE_RATE 10.3125 TX_OUTCLK_SOURCE TXOUTCLKPMA\
TX_PIPM_ENABLE false TX_PLL_TYPE LCPLL TX_REFCLK_FREQUENCY 156.25\
TX_REFCLK_SOURCE R0 TX_USER_DATA_WIDTH 32}\
   CONFIG.PROT5_LR0_SETTINGS {GT_TYPE GTY GT_DIRECTION DUPLEX INS_LOSS_NYQ 20 INTERNAL_PRESET None OOB_ENABLE\
false PCIE_ENABLE false PCIE_USERCLK2_FREQ 250 PCIE_USERCLK_FREQ 250 PRESET\
None RESET_SEQUENCE_INTERVAL 0 RXPROGDIV_FREQ_ENABLE false\
RXPROGDIV_FREQ_SOURCE LCPLL RXPROGDIV_FREQ_VAL 322.265625 RX_64B66B_CRC false\
RX_RATE_GROUP A RX_64B66B_DECODER false RX_64B66B_DESCRAMBLER false\
RX_ACTUAL_REFCLK_FREQUENCY 156.25 RX_BUFFER_BYPASS_MODE Fast_Sync\
RX_BUFFER_BYPASS_MODE_LANE MULTI RX_BUFFER_MODE 1 RX_BUFFER_RESET_ON_CB_CHANGE\
ENABLE RX_BUFFER_RESET_ON_COMMAALIGN DISABLE RX_BUFFER_RESET_ON_RATE_CHANGE\
ENABLE RX_CB_DISP_0_0 false RX_CB_DISP_0_1 false RX_CB_DISP_0_2 false\
RX_CB_DISP_0_3 false RX_CB_DISP_1_0 false RX_CB_DISP_1_1 false RX_CB_DISP_1_2\
false RX_CB_DISP_1_3 false RX_CB_K_0_0 false RX_CB_K_0_1 false RX_CB_K_0_2\
false RX_CB_K_0_3 false RX_CB_K_1_0 false RX_CB_K_1_1 false RX_CB_K_1_2 false\
RX_CB_K_1_3 false RX_CB_LEN_SEQ 1 RX_CB_MASK_0_0 false RX_CB_MASK_0_1 false\
RX_CB_MASK_0_2 false RX_CB_MASK_0_3 false RX_CB_MASK_1_0 false RX_CB_MASK_1_1\
false RX_CB_MASK_1_2 false RX_CB_MASK_1_3 false RX_CB_MAX_LEVEL 1\
RX_CB_MAX_SKEW 1 RX_CB_NUM_SEQ 0 RX_CB_VAL_0_0 00000000 RX_CB_VAL_0_1 00000000\
RX_CB_VAL_0_2 00000000 RX_CB_VAL_0_3 00000000 RX_CB_VAL_1_0 00000000\
RX_CB_VAL_1_1 00000000 RX_CB_VAL_1_2 00000000 RX_CB_VAL_1_3 00000000\
RX_CC_DISP_0_0 false RX_CC_DISP_0_1 false RX_CC_DISP_0_2 false RX_CC_DISP_0_3\
false RX_CC_DISP_1_0 false RX_CC_DISP_1_1 false RX_CC_DISP_1_2 false\
RX_CC_DISP_1_3 false RX_CC_KEEP_IDLE DISABLE RX_CC_K_0_0 false RX_CC_K_0_1\
false RX_CC_K_0_2 false RX_CC_K_0_3 false RX_CC_K_1_0 false RX_CC_K_1_1 false\
RX_CC_K_1_2 false RX_CC_K_1_3 false RX_CC_LEN_SEQ 1 RX_CC_MASK_0_0 false\
RX_CC_MASK_0_1 false RX_CC_MASK_0_2 false RX_CC_MASK_0_3 false RX_CC_MASK_1_0\
false RX_CC_MASK_1_1 false RX_CC_MASK_1_2 false RX_CC_MASK_1_3 false\
RX_CC_NUM_SEQ 0 RX_CC_PERIODICITY 5000 RX_CC_PRECEDENCE ENABLE\
RX_CC_REPEAT_WAIT 0 RX_CC_VAL\
00000000000000000000000000000000000000000000000000000000000000000000000000000000\
RX_CC_VAL_0_0 0000000000 RX_CC_VAL_0_1 0000000000 RX_CC_VAL_0_2 0000000000\
RX_CC_VAL_0_3 0000000000 RX_CC_VAL_1_0 0000000000 RX_CC_VAL_1_1 0000000000\
RX_CC_VAL_1_2 0000000000 RX_CC_VAL_1_3 0000000000 RX_COMMA_ALIGN_WORD 1\
RX_COMMA_DOUBLE_ENABLE false RX_COMMA_MASK 1111111111 RX_COMMA_M_ENABLE false\
RX_COMMA_M_VAL 1010000011 RX_COMMA_PRESET NONE RX_COMMA_P_ENABLE false\
RX_COMMA_P_VAL 0101111100 RX_COMMA_SHOW_REALIGN_ENABLE true RX_COMMA_VALID_ONLY\
0 RX_COUPLING AC RX_DATA_DECODING RAW RX_EQ_MODE AUTO RX_FRACN_ENABLED false\
RX_FRACN_NUMERATOR 0 RX_INT_DATA_WIDTH 32 RX_JTOL_FC 0 RX_JTOL_LF_SLOPE -20\
RX_LINE_RATE 10.3125 RX_OUTCLK_SOURCE RXOUTCLKPMA RX_PLL_TYPE LCPLL\
RX_PPM_OFFSET 0 RX_REFCLK_FREQUENCY 156.25 RX_REFCLK_SOURCE R0 RX_SLIDE_MODE\
OFF RX_SSC_PPM 0 RX_TERMINATION PROGRAMMABLE RX_TERMINATION_PROG_VALUE 800\
RX_USER_DATA_WIDTH 32 TXPROGDIV_FREQ_ENABLE false TXPROGDIV_FREQ_SOURCE LCPLL\
TXPROGDIV_FREQ_VAL 322.265625 TX_64B66B_CRC false TX_RATE_GROUP A\
TX_64B66B_ENCODER false TX_64B66B_SCRAMBLER false TX_ACTUAL_REFCLK_FREQUENCY\
156.25 TX_BUFFER_BYPASS_MODE Fast_Sync TX_BUFFER_MODE 1\
TX_BUFFER_RESET_ON_RATE_CHANGE ENABLE TX_DATA_ENCODING RAW\
TX_DIFF_SWING_EMPH_MODE CUSTOM TX_FRACN_ENABLED false TX_FRACN_NUMERATOR 0\
TX_INT_DATA_WIDTH 32 TX_LINE_RATE 10.3125 TX_OUTCLK_SOURCE TXOUTCLKPMA\
TX_PIPM_ENABLE false TX_PLL_TYPE LCPLL TX_REFCLK_FREQUENCY 156.25\
TX_REFCLK_SOURCE R0 TX_USER_DATA_WIDTH 32}\
   CONFIG.PROT6_LR0_SETTINGS {GT_TYPE GTY GT_DIRECTION DUPLEX INS_LOSS_NYQ 20 INTERNAL_PRESET None OOB_ENABLE\
false PCIE_ENABLE false PCIE_USERCLK2_FREQ 250 PCIE_USERCLK_FREQ 250 PRESET\
None RESET_SEQUENCE_INTERVAL 0 RXPROGDIV_FREQ_ENABLE false\
RXPROGDIV_FREQ_SOURCE LCPLL RXPROGDIV_FREQ_VAL 322.265625 RX_64B66B_CRC false\
RX_RATE_GROUP A RX_64B66B_DECODER false RX_64B66B_DESCRAMBLER false\
RX_ACTUAL_REFCLK_FREQUENCY 156.25 RX_BUFFER_BYPASS_MODE Fast_Sync\
RX_BUFFER_BYPASS_MODE_LANE MULTI RX_BUFFER_MODE 1 RX_BUFFER_RESET_ON_CB_CHANGE\
ENABLE RX_BUFFER_RESET_ON_COMMAALIGN DISABLE RX_BUFFER_RESET_ON_RATE_CHANGE\
ENABLE RX_CB_DISP_0_0 false RX_CB_DISP_0_1 false RX_CB_DISP_0_2 false\
RX_CB_DISP_0_3 false RX_CB_DISP_1_0 false RX_CB_DISP_1_1 false RX_CB_DISP_1_2\
false RX_CB_DISP_1_3 false RX_CB_K_0_0 false RX_CB_K_0_1 false RX_CB_K_0_2\
false RX_CB_K_0_3 false RX_CB_K_1_0 false RX_CB_K_1_1 false RX_CB_K_1_2 false\
RX_CB_K_1_3 false RX_CB_LEN_SEQ 1 RX_CB_MASK_0_0 false RX_CB_MASK_0_1 false\
RX_CB_MASK_0_2 false RX_CB_MASK_0_3 false RX_CB_MASK_1_0 false RX_CB_MASK_1_1\
false RX_CB_MASK_1_2 false RX_CB_MASK_1_3 false RX_CB_MAX_LEVEL 1\
RX_CB_MAX_SKEW 1 RX_CB_NUM_SEQ 0 RX_CB_VAL_0_0 00000000 RX_CB_VAL_0_1 00000000\
RX_CB_VAL_0_2 00000000 RX_CB_VAL_0_3 00000000 RX_CB_VAL_1_0 00000000\
RX_CB_VAL_1_1 00000000 RX_CB_VAL_1_2 00000000 RX_CB_VAL_1_3 00000000\
RX_CC_DISP_0_0 false RX_CC_DISP_0_1 false RX_CC_DISP_0_2 false RX_CC_DISP_0_3\
false RX_CC_DISP_1_0 false RX_CC_DISP_1_1 false RX_CC_DISP_1_2 false\
RX_CC_DISP_1_3 false RX_CC_KEEP_IDLE DISABLE RX_CC_K_0_0 false RX_CC_K_0_1\
false RX_CC_K_0_2 false RX_CC_K_0_3 false RX_CC_K_1_0 false RX_CC_K_1_1 false\
RX_CC_K_1_2 false RX_CC_K_1_3 false RX_CC_LEN_SEQ 1 RX_CC_MASK_0_0 false\
RX_CC_MASK_0_1 false RX_CC_MASK_0_2 false RX_CC_MASK_0_3 false RX_CC_MASK_1_0\
false RX_CC_MASK_1_1 false RX_CC_MASK_1_2 false RX_CC_MASK_1_3 false\
RX_CC_NUM_SEQ 0 RX_CC_PERIODICITY 5000 RX_CC_PRECEDENCE ENABLE\
RX_CC_REPEAT_WAIT 0 RX_CC_VAL\
00000000000000000000000000000000000000000000000000000000000000000000000000000000\
RX_CC_VAL_0_0 0000000000 RX_CC_VAL_0_1 0000000000 RX_CC_VAL_0_2 0000000000\
RX_CC_VAL_0_3 0000000000 RX_CC_VAL_1_0 0000000000 RX_CC_VAL_1_1 0000000000\
RX_CC_VAL_1_2 0000000000 RX_CC_VAL_1_3 0000000000 RX_COMMA_ALIGN_WORD 1\
RX_COMMA_DOUBLE_ENABLE false RX_COMMA_MASK 1111111111 RX_COMMA_M_ENABLE false\
RX_COMMA_M_VAL 1010000011 RX_COMMA_PRESET NONE RX_COMMA_P_ENABLE false\
RX_COMMA_P_VAL 0101111100 RX_COMMA_SHOW_REALIGN_ENABLE true RX_COMMA_VALID_ONLY\
0 RX_COUPLING AC RX_DATA_DECODING RAW RX_EQ_MODE AUTO RX_FRACN_ENABLED false\
RX_FRACN_NUMERATOR 0 RX_INT_DATA_WIDTH 32 RX_JTOL_FC 0 RX_JTOL_LF_SLOPE -20\
RX_LINE_RATE 10.3125 RX_OUTCLK_SOURCE RXOUTCLKPMA RX_PLL_TYPE LCPLL\
RX_PPM_OFFSET 0 RX_REFCLK_FREQUENCY 156.25 RX_REFCLK_SOURCE R0 RX_SLIDE_MODE\
OFF RX_SSC_PPM 0 RX_TERMINATION PROGRAMMABLE RX_TERMINATION_PROG_VALUE 800\
RX_USER_DATA_WIDTH 32 TXPROGDIV_FREQ_ENABLE false TXPROGDIV_FREQ_SOURCE LCPLL\
TXPROGDIV_FREQ_VAL 322.265625 TX_64B66B_CRC false TX_RATE_GROUP A\
TX_64B66B_ENCODER false TX_64B66B_SCRAMBLER false TX_ACTUAL_REFCLK_FREQUENCY\
156.25 TX_BUFFER_BYPASS_MODE Fast_Sync TX_BUFFER_MODE 1\
TX_BUFFER_RESET_ON_RATE_CHANGE ENABLE TX_DATA_ENCODING RAW\
TX_DIFF_SWING_EMPH_MODE CUSTOM TX_FRACN_ENABLED false TX_FRACN_NUMERATOR 0\
TX_INT_DATA_WIDTH 32 TX_LINE_RATE 10.3125 TX_OUTCLK_SOURCE TXOUTCLKPMA\
TX_PIPM_ENABLE false TX_PLL_TYPE LCPLL TX_REFCLK_FREQUENCY 156.25\
TX_REFCLK_SOURCE R0 TX_USER_DATA_WIDTH 32}\
   CONFIG.PROT7_LR0_SETTINGS {GT_TYPE GTY GT_DIRECTION DUPLEX INS_LOSS_NYQ 20 INTERNAL_PRESET None OOB_ENABLE\
false PCIE_ENABLE false PCIE_USERCLK2_FREQ 250 PCIE_USERCLK_FREQ 250 PRESET\
None RESET_SEQUENCE_INTERVAL 0 RXPROGDIV_FREQ_ENABLE false\
RXPROGDIV_FREQ_SOURCE LCPLL RXPROGDIV_FREQ_VAL 322.265625 RX_64B66B_CRC false\
RX_RATE_GROUP A RX_64B66B_DECODER false RX_64B66B_DESCRAMBLER false\
RX_ACTUAL_REFCLK_FREQUENCY 156.25 RX_BUFFER_BYPASS_MODE Fast_Sync\
RX_BUFFER_BYPASS_MODE_LANE MULTI RX_BUFFER_MODE 1 RX_BUFFER_RESET_ON_CB_CHANGE\
ENABLE RX_BUFFER_RESET_ON_COMMAALIGN DISABLE RX_BUFFER_RESET_ON_RATE_CHANGE\
ENABLE RX_CB_DISP_0_0 false RX_CB_DISP_0_1 false RX_CB_DISP_0_2 false\
RX_CB_DISP_0_3 false RX_CB_DISP_1_0 false RX_CB_DISP_1_1 false RX_CB_DISP_1_2\
false RX_CB_DISP_1_3 false RX_CB_K_0_0 false RX_CB_K_0_1 false RX_CB_K_0_2\
false RX_CB_K_0_3 false RX_CB_K_1_0 false RX_CB_K_1_1 false RX_CB_K_1_2 false\
RX_CB_K_1_3 false RX_CB_LEN_SEQ 1 RX_CB_MASK_0_0 false RX_CB_MASK_0_1 false\
RX_CB_MASK_0_2 false RX_CB_MASK_0_3 false RX_CB_MASK_1_0 false RX_CB_MASK_1_1\
false RX_CB_MASK_1_2 false RX_CB_MASK_1_3 false RX_CB_MAX_LEVEL 1\
RX_CB_MAX_SKEW 1 RX_CB_NUM_SEQ 0 RX_CB_VAL_0_0 00000000 RX_CB_VAL_0_1 00000000\
RX_CB_VAL_0_2 00000000 RX_CB_VAL_0_3 00000000 RX_CB_VAL_1_0 00000000\
RX_CB_VAL_1_1 00000000 RX_CB_VAL_1_2 00000000 RX_CB_VAL_1_3 00000000\
RX_CC_DISP_0_0 false RX_CC_DISP_0_1 false RX_CC_DISP_0_2 false RX_CC_DISP_0_3\
false RX_CC_DISP_1_0 false RX_CC_DISP_1_1 false RX_CC_DISP_1_2 false\
RX_CC_DISP_1_3 false RX_CC_KEEP_IDLE DISABLE RX_CC_K_0_0 false RX_CC_K_0_1\
false RX_CC_K_0_2 false RX_CC_K_0_3 false RX_CC_K_1_0 false RX_CC_K_1_1 false\
RX_CC_K_1_2 false RX_CC_K_1_3 false RX_CC_LEN_SEQ 1 RX_CC_MASK_0_0 false\
RX_CC_MASK_0_1 false RX_CC_MASK_0_2 false RX_CC_MASK_0_3 false RX_CC_MASK_1_0\
false RX_CC_MASK_1_1 false RX_CC_MASK_1_2 false RX_CC_MASK_1_3 false\
RX_CC_NUM_SEQ 0 RX_CC_PERIODICITY 5000 RX_CC_PRECEDENCE ENABLE\
RX_CC_REPEAT_WAIT 0 RX_CC_VAL\
00000000000000000000000000000000000000000000000000000000000000000000000000000000\
RX_CC_VAL_0_0 0000000000 RX_CC_VAL_0_1 0000000000 RX_CC_VAL_0_2 0000000000\
RX_CC_VAL_0_3 0000000000 RX_CC_VAL_1_0 0000000000 RX_CC_VAL_1_1 0000000000\
RX_CC_VAL_1_2 0000000000 RX_CC_VAL_1_3 0000000000 RX_COMMA_ALIGN_WORD 1\
RX_COMMA_DOUBLE_ENABLE false RX_COMMA_MASK 1111111111 RX_COMMA_M_ENABLE false\
RX_COMMA_M_VAL 1010000011 RX_COMMA_PRESET NONE RX_COMMA_P_ENABLE false\
RX_COMMA_P_VAL 0101111100 RX_COMMA_SHOW_REALIGN_ENABLE true RX_COMMA_VALID_ONLY\
0 RX_COUPLING AC RX_DATA_DECODING RAW RX_EQ_MODE AUTO RX_FRACN_ENABLED false\
RX_FRACN_NUMERATOR 0 RX_INT_DATA_WIDTH 32 RX_JTOL_FC 0 RX_JTOL_LF_SLOPE -20\
RX_LINE_RATE 10.3125 RX_OUTCLK_SOURCE RXOUTCLKPMA RX_PLL_TYPE LCPLL\
RX_PPM_OFFSET 0 RX_REFCLK_FREQUENCY 156.25 RX_REFCLK_SOURCE R0 RX_SLIDE_MODE\
OFF RX_SSC_PPM 0 RX_TERMINATION PROGRAMMABLE RX_TERMINATION_PROG_VALUE 800\
RX_USER_DATA_WIDTH 32 TXPROGDIV_FREQ_ENABLE false TXPROGDIV_FREQ_SOURCE LCPLL\
TXPROGDIV_FREQ_VAL 322.265625 TX_64B66B_CRC false TX_RATE_GROUP A\
TX_64B66B_ENCODER false TX_64B66B_SCRAMBLER false TX_ACTUAL_REFCLK_FREQUENCY\
156.25 TX_BUFFER_BYPASS_MODE Fast_Sync TX_BUFFER_MODE 1\
TX_BUFFER_RESET_ON_RATE_CHANGE ENABLE TX_DATA_ENCODING RAW\
TX_DIFF_SWING_EMPH_MODE CUSTOM TX_FRACN_ENABLED false TX_FRACN_NUMERATOR 0\
TX_INT_DATA_WIDTH 32 TX_LINE_RATE 10.3125 TX_OUTCLK_SOURCE TXOUTCLKPMA\
TX_PIPM_ENABLE false TX_PLL_TYPE LCPLL TX_REFCLK_FREQUENCY 156.25\
TX_REFCLK_SOURCE R0 TX_USER_DATA_WIDTH 32}\
   CONFIG.REFCLK_STRING {HSCLK0_LCPLLGTREFCLK0 refclk_PROT0_R0_100_MHz_unique1 HSCLK1_LCPLLGTREFCLK0\
refclk_PROT0_R0_100_MHz_unique1}\
 ] $gt_quad_base_1

  # Create instance: urlp_1, and set properties
  set urlp_1 [ create_bd_cell -type ip -vlnv xilinx.com:ip:util_reduced_logic:2.0 urlp_1 ]
  set_property -dict [ list \
   CONFIG.C_SIZE {1} \
 ] $urlp_1

  # Create instance: util_ds_buf_1, and set properties
  set util_ds_buf_1 [ create_bd_cell -type ip -vlnv xilinx.com:ip:util_ds_buf:2.2 util_ds_buf_1 ]
  set_property -dict [ list \
   CONFIG.C_BUF_TYPE {IBUFDSGTE} \
 ] $util_ds_buf_1

  # Create instance: xlcp_1, and set properties
  set xlcp_1 [ create_bd_cell -type ip -vlnv xilinx.com:ip:xlconcat:2.1 xlcp_1 ]
  set_property -dict [ list \
   CONFIG.NUM_PORTS {1} \
 ] $xlcp_1

  # Create interface connections
  connect_bd_intf_net -intf_net bridge_refclkX1Y2_GT_RX0 [get_bd_intf_pins bridge_refclkX1Y2/GT_RX0] [get_bd_intf_pins gt_quad_base_1/RX0_GT_IP_Interface]
  connect_bd_intf_net -intf_net bridge_refclkX1Y2_GT_RX1 [get_bd_intf_pins bridge_refclkX1Y2/GT_RX1] [get_bd_intf_pins gt_quad_base_1/RX1_GT_IP_Interface]
  connect_bd_intf_net -intf_net bridge_refclkX1Y2_GT_RX2 [get_bd_intf_pins bridge_refclkX1Y2/GT_RX2] [get_bd_intf_pins gt_quad_base_1/RX2_GT_IP_Interface]
  connect_bd_intf_net -intf_net bridge_refclkX1Y2_GT_RX3 [get_bd_intf_pins bridge_refclkX1Y2/GT_RX3] [get_bd_intf_pins gt_quad_base_1/RX3_GT_IP_Interface]
  connect_bd_intf_net -intf_net bridge_refclkX1Y2_GT_TX0 [get_bd_intf_pins bridge_refclkX1Y2/GT_TX0] [get_bd_intf_pins gt_quad_base_1/TX0_GT_IP_Interface]
  connect_bd_intf_net -intf_net bridge_refclkX1Y2_GT_TX1 [get_bd_intf_pins bridge_refclkX1Y2/GT_TX1] [get_bd_intf_pins gt_quad_base_1/TX1_GT_IP_Interface]
  connect_bd_intf_net -intf_net bridge_refclkX1Y2_GT_TX2 [get_bd_intf_pins bridge_refclkX1Y2/GT_TX2] [get_bd_intf_pins gt_quad_base_1/TX2_GT_IP_Interface]
  connect_bd_intf_net -intf_net bridge_refclkX1Y2_GT_TX3 [get_bd_intf_pins bridge_refclkX1Y2/GT_TX3] [get_bd_intf_pins gt_quad_base_1/TX3_GT_IP_Interface]
  connect_bd_intf_net -intf_net bridge_refclkX1Y2_diff_gt_ref_clock_1 [get_bd_intf_pins bridge_refclkX1Y2_diff_gt_ref_clock] [get_bd_intf_pins util_ds_buf_1/CLK_IN_D]
  connect_bd_intf_net -intf_net gt_quad_base_1_GT_Serial [get_bd_intf_pins GT_Serial_1] [get_bd_intf_pins gt_quad_base_1/GT_Serial]

  # Create port connections
  connect_bd_net -net bufg_gt_2_usrclk [get_bd_pins bridge_refclkX1Y2/gt_rxusrclk] [get_bd_pins bufg_gt_2/usrclk] [get_bd_pins gt_quad_base_1/ch0_rxusrclk] [get_bd_pins gt_quad_base_1/ch1_rxusrclk] [get_bd_pins gt_quad_base_1/ch2_rxusrclk] [get_bd_pins gt_quad_base_1/ch3_rxusrclk]
  connect_bd_net -net bufg_gt_3_usrclk [get_bd_pins bridge_refclkX1Y2/gt_txusrclk] [get_bd_pins bufg_gt_3/usrclk] [get_bd_pins gt_quad_base_1/ch0_txusrclk] [get_bd_pins gt_quad_base_1/ch1_txusrclk] [get_bd_pins gt_quad_base_1/ch2_txusrclk] [get_bd_pins gt_quad_base_1/ch3_txusrclk]
  connect_bd_net -net gt_quad_base_1_ch0_rxoutclk [get_bd_pins bufg_gt_2/outclk] [get_bd_pins gt_quad_base_1/ch0_rxoutclk]
  connect_bd_net -net gt_quad_base_1_ch0_txoutclk [get_bd_pins bufg_gt_3/outclk] [get_bd_pins gt_quad_base_1/ch0_txoutclk]
  connect_bd_net -net gt_quad_base_1_gtpowergood [get_bd_pins gt_quad_base_1/gtpowergood] [get_bd_pins xlcp_1/In0]
  connect_bd_net -net urlp_1_Res [get_bd_pins bridge_refclkX1Y2/gtpowergood] [get_bd_pins urlp_1/Res]
  connect_bd_net -net util_ds_buf_1_IBUF_OUT [get_bd_pins gt_quad_base_1/GT_REFCLK0] [get_bd_pins util_ds_buf_1/IBUF_OUT]
  connect_bd_net -net versal_cips_0_pl0_ref_clk [get_bd_pins apb3clk] [get_bd_pins bridge_refclkX1Y2/apb3clk] [get_bd_pins gt_quad_base_1/apb3clk]
  connect_bd_net -net xlcp_1_dout [get_bd_pins urlp_1/Op1] [get_bd_pins xlcp_1/dout]

  # Restore current instance
  current_bd_instance $oldCurInst
}

# Hierarchical cell: gty_quad_105
proc create_hier_cell_gty_quad_105 { parentCell nameHier } {

  variable script_folder

  if { $parentCell eq "" || $nameHier eq "" } {
     catch {common::send_gid_msg -ssname BD::TCL -id 2092 -severity "ERROR" "create_hier_cell_gty_quad_105() - Empty argument(s)!"}
     return
  }

  # Get object for parentCell
  set parentObj [get_bd_cells $parentCell]
  if { $parentObj == "" } {
     catch {common::send_gid_msg -ssname BD::TCL -id 2090 -severity "ERROR" "Unable to find parent cell <$parentCell>!"}
     return
  }

  # Make sure parentObj is hier blk
  set parentType [get_property TYPE $parentObj]
  if { $parentType ne "hier" } {
     catch {common::send_gid_msg -ssname BD::TCL -id 2091 -severity "ERROR" "Parent <$parentObj> has TYPE = <$parentType>. Expected to be <hier>."}
     return
  }

  # Save current instance; Restore later
  set oldCurInst [current_bd_instance .]

  # Set parent object as current
  current_bd_instance $parentObj

  # Create cell and set as current instance
  set hier_obj [create_bd_cell -type hier $nameHier]
  current_bd_instance $hier_obj

  # Create interface pins
  create_bd_intf_pin -mode Master -vlnv xilinx.com:interface:gt_rtl:1.0 GT_Serial

  create_bd_intf_pin -mode Slave -vlnv xilinx.com:interface:diff_clock_rtl:1.0 bridge_refclkX0Y10_diff_gt_ref_clock


  # Create pins
  create_bd_pin -dir I -type clk apb3clk

  # Create instance: bridge_refclkX0Y10, and set properties
  set bridge_refclkX0Y10 [ create_bd_cell -type ip -vlnv xilinx.com:ip:gt_bridge_ip:1.1 bridge_refclkX0Y10 ]
  set_property -dict [ list \
   CONFIG.IP_LR0_SETTINGS {GT_DIRECTION DUPLEX  GT_TYPE GTY  INS_LOSS_NYQ 20  INTERNAL_PRESET None \
OOB_ENABLE false  PCIE_ENABLE false  PCIE_USERCLK2_FREQ 250  PCIE_USERCLK_FREQ\
250  PRESET None  RESET_SEQUENCE_INTERVAL 0  RXPROGDIV_FREQ_ENABLE false \
RXPROGDIV_FREQ_SOURCE LCPLL  RXPROGDIV_FREQ_VAL 322.265625  RX_64B66B_CRC false\
RX_64B66B_DECODER false  RX_64B66B_DESCRAMBLER false \
RX_ACTUAL_REFCLK_FREQUENCY 156.250000000000  RX_BUFFER_BYPASS_MODE Fast_Sync \
RX_BUFFER_BYPASS_MODE_LANE MULTI  RX_BUFFER_MODE 1 \
RX_BUFFER_RESET_ON_CB_CHANGE ENABLE  RX_BUFFER_RESET_ON_COMMAALIGN DISABLE \
RX_BUFFER_RESET_ON_RATE_CHANGE ENABLE  RX_CB_DISP 00000000  RX_CB_DISP_0_0\
false  RX_CB_DISP_0_1 false  RX_CB_DISP_0_2 false  RX_CB_DISP_0_3 false \
RX_CB_DISP_1_0 false  RX_CB_DISP_1_1 false  RX_CB_DISP_1_2 false \
RX_CB_DISP_1_3 false  RX_CB_K 00000000  RX_CB_K_0_0 false  RX_CB_K_0_1 false \
RX_CB_K_0_2 false  RX_CB_K_0_3 false  RX_CB_K_1_0 false  RX_CB_K_1_1 false \
RX_CB_K_1_2 false  RX_CB_K_1_3 false  RX_CB_LEN_SEQ 1  RX_CB_MASK 00000000 \
RX_CB_MASK_0_0 false  RX_CB_MASK_0_1 false  RX_CB_MASK_0_2 false \
RX_CB_MASK_0_3 false  RX_CB_MASK_1_0 false  RX_CB_MASK_1_1 false \
RX_CB_MASK_1_2 false  RX_CB_MASK_1_3 false  RX_CB_MAX_LEVEL 1  RX_CB_MAX_SKEW 1\
RX_CB_NUM_SEQ 0  RX_CB_VAL\
00000000000000000000000000000000000000000000000000000000000000000000000000000000\
RX_CB_VAL_0_0 00000000  RX_CB_VAL_0_1 00000000  RX_CB_VAL_0_2 00000000 \
RX_CB_VAL_0_3 00000000  RX_CB_VAL_1_0 00000000  RX_CB_VAL_1_1 00000000 \
RX_CB_VAL_1_2 00000000  RX_CB_VAL_1_3 00000000  RX_CC_DISP 00000000 \
RX_CC_DISP_0_0 false  RX_CC_DISP_0_1 false  RX_CC_DISP_0_2 false \
RX_CC_DISP_0_3 false  RX_CC_DISP_1_0 false  RX_CC_DISP_1_1 false \
RX_CC_DISP_1_2 false  RX_CC_DISP_1_3 false  RX_CC_K 00000000  RX_CC_KEEP_IDLE\
DISABLE  RX_CC_K_0_0 false  RX_CC_K_0_1 false  RX_CC_K_0_2 false  RX_CC_K_0_3\
false  RX_CC_K_1_0 false  RX_CC_K_1_1 false  RX_CC_K_1_2 false  RX_CC_K_1_3\
false  RX_CC_LEN_SEQ 1  RX_CC_MASK 00000000  RX_CC_MASK_0_0 false \
RX_CC_MASK_0_1 false  RX_CC_MASK_0_2 false  RX_CC_MASK_0_3 false \
RX_CC_MASK_1_0 false  RX_CC_MASK_1_1 false  RX_CC_MASK_1_2 false \
RX_CC_MASK_1_3 false  RX_CC_NUM_SEQ 0  RX_CC_PERIODICITY 5000  RX_CC_PRECEDENCE\
ENABLE  RX_CC_REPEAT_WAIT 0  RX_CC_VAL\
00000000000000000000000000000000000000000000000000000000000000000000000000000000\
RX_CC_VAL_0_0 00000000  RX_CC_VAL_0_1 00000000  RX_CC_VAL_0_2 00000000 \
RX_CC_VAL_0_3 00000000  RX_CC_VAL_1_0 00000000  RX_CC_VAL_1_1 00000000 \
RX_CC_VAL_1_2 00000000  RX_CC_VAL_1_3 00000000  RX_COMMA_ALIGN_WORD 1 \
RX_COMMA_DOUBLE_ENABLE false  RX_COMMA_MASK 0000000000  RX_COMMA_M_ENABLE false\
RX_COMMA_M_VAL 1010000011  RX_COMMA_PRESET NONE  RX_COMMA_P_ENABLE false \
RX_COMMA_P_VAL 0101111100  RX_COMMA_SHOW_REALIGN_ENABLE true \
RX_COMMA_VALID_ONLY 0  RX_COUPLING AC  RX_DATA_DECODING RAW  RX_EQ_MODE AUTO \
RX_FRACN_ENABLED false  RX_FRACN_NUMERATOR 0  RX_INT_DATA_WIDTH 32  RX_JTOL_FC\
6.1862627  RX_JTOL_LF_SLOPE -20  RX_LINE_RATE 10.3125  RX_OUTCLK_SOURCE\
RXOUTCLKPMA  RX_PLL_TYPE LCPLL  RX_PPM_OFFSET 0  RX_RATE_GROUP A \
RX_REFCLK_FREQUENCY 156.25  RX_REFCLK_SOURCE R0  RX_SLIDE_MODE OFF  RX_SSC_PPM\
0  RX_TERMINATION PROGRAMMABLE  RX_TERMINATION_PROG_VALUE 800 \
RX_USER_DATA_WIDTH 32  TXPROGDIV_FREQ_ENABLE false  TXPROGDIV_FREQ_SOURCE LCPLL\
TXPROGDIV_FREQ_VAL 322.265625  TX_64B66B_CRC false  TX_64B66B_ENCODER false \
TX_64B66B_SCRAMBLER false  TX_ACTUAL_REFCLK_FREQUENCY 156.250000000000 \
TX_BUFFER_BYPASS_MODE Fast_Sync  TX_BUFFER_MODE 1 \
TX_BUFFER_RESET_ON_RATE_CHANGE ENABLE  TX_DATA_ENCODING RAW \
TX_DIFF_SWING_EMPH_MODE CUSTOM  TX_FRACN_ENABLED false  TX_FRACN_NUMERATOR 0 \
TX_INT_DATA_WIDTH 32  TX_LINE_RATE 10.3125  TX_OUTCLK_SOURCE TXOUTCLKPMA \
TX_PIPM_ENABLE false  TX_PLL_TYPE LCPLL  TX_RATE_GROUP A  TX_REFCLK_FREQUENCY\
156.25  TX_REFCLK_SOURCE R0  TX_USER_DATA_WIDTH 32}\
   CONFIG.IP_NO_OF_LANES {4} \
 ] $bridge_refclkX0Y10

  # Create instance: bufg_gt, and set properties
  set bufg_gt [ create_bd_cell -type ip -vlnv xilinx.com:ip:bufg_gt:1.0 bufg_gt ]

  # Create instance: bufg_gt_1, and set properties
  set bufg_gt_1 [ create_bd_cell -type ip -vlnv xilinx.com:ip:bufg_gt:1.0 bufg_gt_1 ]

  # Create instance: gt_quad_base, and set properties
  set gt_quad_base [ create_bd_cell -type ip -vlnv xilinx.com:ip:gt_quad_base:1.1 gt_quad_base ]
  set_property -dict [ list \
   CONFIG.PORTS_INFO_DICT {LANE_SEL_DICT {PROT0 {RX0 RX1 RX2 RX3 TX0 TX1 TX2 TX3}} GT_TYPE GTY\
REG_CONF_INTF APB3_INTF BOARD_INTERFACE false}\
   CONFIG.PROT1_LR0_SETTINGS {GT_TYPE GTY GT_DIRECTION DUPLEX INS_LOSS_NYQ 20 INTERNAL_PRESET None OOB_ENABLE\
false PCIE_ENABLE false PCIE_USERCLK2_FREQ 250 PCIE_USERCLK_FREQ 250 PRESET\
None RESET_SEQUENCE_INTERVAL 0 RXPROGDIV_FREQ_ENABLE false\
RXPROGDIV_FREQ_SOURCE LCPLL RXPROGDIV_FREQ_VAL 322.265625 RX_64B66B_CRC false\
RX_RATE_GROUP A RX_64B66B_DECODER false RX_64B66B_DESCRAMBLER false\
RX_ACTUAL_REFCLK_FREQUENCY 156.25 RX_BUFFER_BYPASS_MODE Fast_Sync\
RX_BUFFER_BYPASS_MODE_LANE MULTI RX_BUFFER_MODE 1 RX_BUFFER_RESET_ON_CB_CHANGE\
ENABLE RX_BUFFER_RESET_ON_COMMAALIGN DISABLE RX_BUFFER_RESET_ON_RATE_CHANGE\
ENABLE RX_CB_DISP_0_0 false RX_CB_DISP_0_1 false RX_CB_DISP_0_2 false\
RX_CB_DISP_0_3 false RX_CB_DISP_1_0 false RX_CB_DISP_1_1 false RX_CB_DISP_1_2\
false RX_CB_DISP_1_3 false RX_CB_K_0_0 false RX_CB_K_0_1 false RX_CB_K_0_2\
false RX_CB_K_0_3 false RX_CB_K_1_0 false RX_CB_K_1_1 false RX_CB_K_1_2 false\
RX_CB_K_1_3 false RX_CB_LEN_SEQ 1 RX_CB_MASK_0_0 false RX_CB_MASK_0_1 false\
RX_CB_MASK_0_2 false RX_CB_MASK_0_3 false RX_CB_MASK_1_0 false RX_CB_MASK_1_1\
false RX_CB_MASK_1_2 false RX_CB_MASK_1_3 false RX_CB_MAX_LEVEL 1\
RX_CB_MAX_SKEW 1 RX_CB_NUM_SEQ 0 RX_CB_VAL_0_0 00000000 RX_CB_VAL_0_1 00000000\
RX_CB_VAL_0_2 00000000 RX_CB_VAL_0_3 00000000 RX_CB_VAL_1_0 00000000\
RX_CB_VAL_1_1 00000000 RX_CB_VAL_1_2 00000000 RX_CB_VAL_1_3 00000000\
RX_CC_DISP_0_0 false RX_CC_DISP_0_1 false RX_CC_DISP_0_2 false RX_CC_DISP_0_3\
false RX_CC_DISP_1_0 false RX_CC_DISP_1_1 false RX_CC_DISP_1_2 false\
RX_CC_DISP_1_3 false RX_CC_KEEP_IDLE DISABLE RX_CC_K_0_0 false RX_CC_K_0_1\
false RX_CC_K_0_2 false RX_CC_K_0_3 false RX_CC_K_1_0 false RX_CC_K_1_1 false\
RX_CC_K_1_2 false RX_CC_K_1_3 false RX_CC_LEN_SEQ 1 RX_CC_MASK_0_0 false\
RX_CC_MASK_0_1 false RX_CC_MASK_0_2 false RX_CC_MASK_0_3 false RX_CC_MASK_1_0\
false RX_CC_MASK_1_1 false RX_CC_MASK_1_2 false RX_CC_MASK_1_3 false\
RX_CC_NUM_SEQ 0 RX_CC_PERIODICITY 5000 RX_CC_PRECEDENCE ENABLE\
RX_CC_REPEAT_WAIT 0 RX_CC_VAL\
00000000000000000000000000000000000000000000000000000000000000000000000000000000\
RX_CC_VAL_0_0 0000000000 RX_CC_VAL_0_1 0000000000 RX_CC_VAL_0_2 0000000000\
RX_CC_VAL_0_3 0000000000 RX_CC_VAL_1_0 0000000000 RX_CC_VAL_1_1 0000000000\
RX_CC_VAL_1_2 0000000000 RX_CC_VAL_1_3 0000000000 RX_COMMA_ALIGN_WORD 1\
RX_COMMA_DOUBLE_ENABLE false RX_COMMA_MASK 1111111111 RX_COMMA_M_ENABLE false\
RX_COMMA_M_VAL 1010000011 RX_COMMA_PRESET NONE RX_COMMA_P_ENABLE false\
RX_COMMA_P_VAL 0101111100 RX_COMMA_SHOW_REALIGN_ENABLE true RX_COMMA_VALID_ONLY\
0 RX_COUPLING AC RX_DATA_DECODING RAW RX_EQ_MODE AUTO RX_FRACN_ENABLED false\
RX_FRACN_NUMERATOR 0 RX_INT_DATA_WIDTH 32 RX_JTOL_FC 0 RX_JTOL_LF_SLOPE -20\
RX_LINE_RATE 10.3125 RX_OUTCLK_SOURCE RXOUTCLKPMA RX_PLL_TYPE LCPLL\
RX_PPM_OFFSET 0 RX_REFCLK_FREQUENCY 156.25 RX_REFCLK_SOURCE R0 RX_SLIDE_MODE\
OFF RX_SSC_PPM 0 RX_TERMINATION PROGRAMMABLE RX_TERMINATION_PROG_VALUE 800\
RX_USER_DATA_WIDTH 32 TXPROGDIV_FREQ_ENABLE false TXPROGDIV_FREQ_SOURCE LCPLL\
TXPROGDIV_FREQ_VAL 322.265625 TX_64B66B_CRC false TX_RATE_GROUP A\
TX_64B66B_ENCODER false TX_64B66B_SCRAMBLER false TX_ACTUAL_REFCLK_FREQUENCY\
156.25 TX_BUFFER_BYPASS_MODE Fast_Sync TX_BUFFER_MODE 1\
TX_BUFFER_RESET_ON_RATE_CHANGE ENABLE TX_DATA_ENCODING RAW\
TX_DIFF_SWING_EMPH_MODE CUSTOM TX_FRACN_ENABLED false TX_FRACN_NUMERATOR 0\
TX_INT_DATA_WIDTH 32 TX_LINE_RATE 10.3125 TX_OUTCLK_SOURCE TXOUTCLKPMA\
TX_PIPM_ENABLE false TX_PLL_TYPE LCPLL TX_REFCLK_FREQUENCY 156.25\
TX_REFCLK_SOURCE R0 TX_USER_DATA_WIDTH 32}\
   CONFIG.PROT2_LR0_SETTINGS {GT_TYPE GTY GT_DIRECTION DUPLEX INS_LOSS_NYQ 20 INTERNAL_PRESET None OOB_ENABLE\
false PCIE_ENABLE false PCIE_USERCLK2_FREQ 250 PCIE_USERCLK_FREQ 250 PRESET\
None RESET_SEQUENCE_INTERVAL 0 RXPROGDIV_FREQ_ENABLE false\
RXPROGDIV_FREQ_SOURCE LCPLL RXPROGDIV_FREQ_VAL 322.265625 RX_64B66B_CRC false\
RX_RATE_GROUP A RX_64B66B_DECODER false RX_64B66B_DESCRAMBLER false\
RX_ACTUAL_REFCLK_FREQUENCY 156.25 RX_BUFFER_BYPASS_MODE Fast_Sync\
RX_BUFFER_BYPASS_MODE_LANE MULTI RX_BUFFER_MODE 1 RX_BUFFER_RESET_ON_CB_CHANGE\
ENABLE RX_BUFFER_RESET_ON_COMMAALIGN DISABLE RX_BUFFER_RESET_ON_RATE_CHANGE\
ENABLE RX_CB_DISP_0_0 false RX_CB_DISP_0_1 false RX_CB_DISP_0_2 false\
RX_CB_DISP_0_3 false RX_CB_DISP_1_0 false RX_CB_DISP_1_1 false RX_CB_DISP_1_2\
false RX_CB_DISP_1_3 false RX_CB_K_0_0 false RX_CB_K_0_1 false RX_CB_K_0_2\
false RX_CB_K_0_3 false RX_CB_K_1_0 false RX_CB_K_1_1 false RX_CB_K_1_2 false\
RX_CB_K_1_3 false RX_CB_LEN_SEQ 1 RX_CB_MASK_0_0 false RX_CB_MASK_0_1 false\
RX_CB_MASK_0_2 false RX_CB_MASK_0_3 false RX_CB_MASK_1_0 false RX_CB_MASK_1_1\
false RX_CB_MASK_1_2 false RX_CB_MASK_1_3 false RX_CB_MAX_LEVEL 1\
RX_CB_MAX_SKEW 1 RX_CB_NUM_SEQ 0 RX_CB_VAL_0_0 00000000 RX_CB_VAL_0_1 00000000\
RX_CB_VAL_0_2 00000000 RX_CB_VAL_0_3 00000000 RX_CB_VAL_1_0 00000000\
RX_CB_VAL_1_1 00000000 RX_CB_VAL_1_2 00000000 RX_CB_VAL_1_3 00000000\
RX_CC_DISP_0_0 false RX_CC_DISP_0_1 false RX_CC_DISP_0_2 false RX_CC_DISP_0_3\
false RX_CC_DISP_1_0 false RX_CC_DISP_1_1 false RX_CC_DISP_1_2 false\
RX_CC_DISP_1_3 false RX_CC_KEEP_IDLE DISABLE RX_CC_K_0_0 false RX_CC_K_0_1\
false RX_CC_K_0_2 false RX_CC_K_0_3 false RX_CC_K_1_0 false RX_CC_K_1_1 false\
RX_CC_K_1_2 false RX_CC_K_1_3 false RX_CC_LEN_SEQ 1 RX_CC_MASK_0_0 false\
RX_CC_MASK_0_1 false RX_CC_MASK_0_2 false RX_CC_MASK_0_3 false RX_CC_MASK_1_0\
false RX_CC_MASK_1_1 false RX_CC_MASK_1_2 false RX_CC_MASK_1_3 false\
RX_CC_NUM_SEQ 0 RX_CC_PERIODICITY 5000 RX_CC_PRECEDENCE ENABLE\
RX_CC_REPEAT_WAIT 0 RX_CC_VAL\
00000000000000000000000000000000000000000000000000000000000000000000000000000000\
RX_CC_VAL_0_0 0000000000 RX_CC_VAL_0_1 0000000000 RX_CC_VAL_0_2 0000000000\
RX_CC_VAL_0_3 0000000000 RX_CC_VAL_1_0 0000000000 RX_CC_VAL_1_1 0000000000\
RX_CC_VAL_1_2 0000000000 RX_CC_VAL_1_3 0000000000 RX_COMMA_ALIGN_WORD 1\
RX_COMMA_DOUBLE_ENABLE false RX_COMMA_MASK 1111111111 RX_COMMA_M_ENABLE false\
RX_COMMA_M_VAL 1010000011 RX_COMMA_PRESET NONE RX_COMMA_P_ENABLE false\
RX_COMMA_P_VAL 0101111100 RX_COMMA_SHOW_REALIGN_ENABLE true RX_COMMA_VALID_ONLY\
0 RX_COUPLING AC RX_DATA_DECODING RAW RX_EQ_MODE AUTO RX_FRACN_ENABLED false\
RX_FRACN_NUMERATOR 0 RX_INT_DATA_WIDTH 32 RX_JTOL_FC 0 RX_JTOL_LF_SLOPE -20\
RX_LINE_RATE 10.3125 RX_OUTCLK_SOURCE RXOUTCLKPMA RX_PLL_TYPE LCPLL\
RX_PPM_OFFSET 0 RX_REFCLK_FREQUENCY 156.25 RX_REFCLK_SOURCE R0 RX_SLIDE_MODE\
OFF RX_SSC_PPM 0 RX_TERMINATION PROGRAMMABLE RX_TERMINATION_PROG_VALUE 800\
RX_USER_DATA_WIDTH 32 TXPROGDIV_FREQ_ENABLE false TXPROGDIV_FREQ_SOURCE LCPLL\
TXPROGDIV_FREQ_VAL 322.265625 TX_64B66B_CRC false TX_RATE_GROUP A\
TX_64B66B_ENCODER false TX_64B66B_SCRAMBLER false TX_ACTUAL_REFCLK_FREQUENCY\
156.25 TX_BUFFER_BYPASS_MODE Fast_Sync TX_BUFFER_MODE 1\
TX_BUFFER_RESET_ON_RATE_CHANGE ENABLE TX_DATA_ENCODING RAW\
TX_DIFF_SWING_EMPH_MODE CUSTOM TX_FRACN_ENABLED false TX_FRACN_NUMERATOR 0\
TX_INT_DATA_WIDTH 32 TX_LINE_RATE 10.3125 TX_OUTCLK_SOURCE TXOUTCLKPMA\
TX_PIPM_ENABLE false TX_PLL_TYPE LCPLL TX_REFCLK_FREQUENCY 156.25\
TX_REFCLK_SOURCE R0 TX_USER_DATA_WIDTH 32}\
   CONFIG.PROT3_LR0_SETTINGS {GT_TYPE GTY GT_DIRECTION DUPLEX INS_LOSS_NYQ 20 INTERNAL_PRESET None OOB_ENABLE\
false PCIE_ENABLE false PCIE_USERCLK2_FREQ 250 PCIE_USERCLK_FREQ 250 PRESET\
None RESET_SEQUENCE_INTERVAL 0 RXPROGDIV_FREQ_ENABLE false\
RXPROGDIV_FREQ_SOURCE LCPLL RXPROGDIV_FREQ_VAL 322.265625 RX_64B66B_CRC false\
RX_RATE_GROUP A RX_64B66B_DECODER false RX_64B66B_DESCRAMBLER false\
RX_ACTUAL_REFCLK_FREQUENCY 156.25 RX_BUFFER_BYPASS_MODE Fast_Sync\
RX_BUFFER_BYPASS_MODE_LANE MULTI RX_BUFFER_MODE 1 RX_BUFFER_RESET_ON_CB_CHANGE\
ENABLE RX_BUFFER_RESET_ON_COMMAALIGN DISABLE RX_BUFFER_RESET_ON_RATE_CHANGE\
ENABLE RX_CB_DISP_0_0 false RX_CB_DISP_0_1 false RX_CB_DISP_0_2 false\
RX_CB_DISP_0_3 false RX_CB_DISP_1_0 false RX_CB_DISP_1_1 false RX_CB_DISP_1_2\
false RX_CB_DISP_1_3 false RX_CB_K_0_0 false RX_CB_K_0_1 false RX_CB_K_0_2\
false RX_CB_K_0_3 false RX_CB_K_1_0 false RX_CB_K_1_1 false RX_CB_K_1_2 false\
RX_CB_K_1_3 false RX_CB_LEN_SEQ 1 RX_CB_MASK_0_0 false RX_CB_MASK_0_1 false\
RX_CB_MASK_0_2 false RX_CB_MASK_0_3 false RX_CB_MASK_1_0 false RX_CB_MASK_1_1\
false RX_CB_MASK_1_2 false RX_CB_MASK_1_3 false RX_CB_MAX_LEVEL 1\
RX_CB_MAX_SKEW 1 RX_CB_NUM_SEQ 0 RX_CB_VAL_0_0 00000000 RX_CB_VAL_0_1 00000000\
RX_CB_VAL_0_2 00000000 RX_CB_VAL_0_3 00000000 RX_CB_VAL_1_0 00000000\
RX_CB_VAL_1_1 00000000 RX_CB_VAL_1_2 00000000 RX_CB_VAL_1_3 00000000\
RX_CC_DISP_0_0 false RX_CC_DISP_0_1 false RX_CC_DISP_0_2 false RX_CC_DISP_0_3\
false RX_CC_DISP_1_0 false RX_CC_DISP_1_1 false RX_CC_DISP_1_2 false\
RX_CC_DISP_1_3 false RX_CC_KEEP_IDLE DISABLE RX_CC_K_0_0 false RX_CC_K_0_1\
false RX_CC_K_0_2 false RX_CC_K_0_3 false RX_CC_K_1_0 false RX_CC_K_1_1 false\
RX_CC_K_1_2 false RX_CC_K_1_3 false RX_CC_LEN_SEQ 1 RX_CC_MASK_0_0 false\
RX_CC_MASK_0_1 false RX_CC_MASK_0_2 false RX_CC_MASK_0_3 false RX_CC_MASK_1_0\
false RX_CC_MASK_1_1 false RX_CC_MASK_1_2 false RX_CC_MASK_1_3 false\
RX_CC_NUM_SEQ 0 RX_CC_PERIODICITY 5000 RX_CC_PRECEDENCE ENABLE\
RX_CC_REPEAT_WAIT 0 RX_CC_VAL\
00000000000000000000000000000000000000000000000000000000000000000000000000000000\
RX_CC_VAL_0_0 0000000000 RX_CC_VAL_0_1 0000000000 RX_CC_VAL_0_2 0000000000\
RX_CC_VAL_0_3 0000000000 RX_CC_VAL_1_0 0000000000 RX_CC_VAL_1_1 0000000000\
RX_CC_VAL_1_2 0000000000 RX_CC_VAL_1_3 0000000000 RX_COMMA_ALIGN_WORD 1\
RX_COMMA_DOUBLE_ENABLE false RX_COMMA_MASK 1111111111 RX_COMMA_M_ENABLE false\
RX_COMMA_M_VAL 1010000011 RX_COMMA_PRESET NONE RX_COMMA_P_ENABLE false\
RX_COMMA_P_VAL 0101111100 RX_COMMA_SHOW_REALIGN_ENABLE true RX_COMMA_VALID_ONLY\
0 RX_COUPLING AC RX_DATA_DECODING RAW RX_EQ_MODE AUTO RX_FRACN_ENABLED false\
RX_FRACN_NUMERATOR 0 RX_INT_DATA_WIDTH 32 RX_JTOL_FC 0 RX_JTOL_LF_SLOPE -20\
RX_LINE_RATE 10.3125 RX_OUTCLK_SOURCE RXOUTCLKPMA RX_PLL_TYPE LCPLL\
RX_PPM_OFFSET 0 RX_REFCLK_FREQUENCY 156.25 RX_REFCLK_SOURCE R0 RX_SLIDE_MODE\
OFF RX_SSC_PPM 0 RX_TERMINATION PROGRAMMABLE RX_TERMINATION_PROG_VALUE 800\
RX_USER_DATA_WIDTH 32 TXPROGDIV_FREQ_ENABLE false TXPROGDIV_FREQ_SOURCE LCPLL\
TXPROGDIV_FREQ_VAL 322.265625 TX_64B66B_CRC false TX_RATE_GROUP A\
TX_64B66B_ENCODER false TX_64B66B_SCRAMBLER false TX_ACTUAL_REFCLK_FREQUENCY\
156.25 TX_BUFFER_BYPASS_MODE Fast_Sync TX_BUFFER_MODE 1\
TX_BUFFER_RESET_ON_RATE_CHANGE ENABLE TX_DATA_ENCODING RAW\
TX_DIFF_SWING_EMPH_MODE CUSTOM TX_FRACN_ENABLED false TX_FRACN_NUMERATOR 0\
TX_INT_DATA_WIDTH 32 TX_LINE_RATE 10.3125 TX_OUTCLK_SOURCE TXOUTCLKPMA\
TX_PIPM_ENABLE false TX_PLL_TYPE LCPLL TX_REFCLK_FREQUENCY 156.25\
TX_REFCLK_SOURCE R0 TX_USER_DATA_WIDTH 32}\
   CONFIG.PROT4_LR0_SETTINGS {GT_TYPE GTY GT_DIRECTION DUPLEX INS_LOSS_NYQ 20 INTERNAL_PRESET None OOB_ENABLE\
false PCIE_ENABLE false PCIE_USERCLK2_FREQ 250 PCIE_USERCLK_FREQ 250 PRESET\
None RESET_SEQUENCE_INTERVAL 0 RXPROGDIV_FREQ_ENABLE false\
RXPROGDIV_FREQ_SOURCE LCPLL RXPROGDIV_FREQ_VAL 322.265625 RX_64B66B_CRC false\
RX_RATE_GROUP A RX_64B66B_DECODER false RX_64B66B_DESCRAMBLER false\
RX_ACTUAL_REFCLK_FREQUENCY 156.25 RX_BUFFER_BYPASS_MODE Fast_Sync\
RX_BUFFER_BYPASS_MODE_LANE MULTI RX_BUFFER_MODE 1 RX_BUFFER_RESET_ON_CB_CHANGE\
ENABLE RX_BUFFER_RESET_ON_COMMAALIGN DISABLE RX_BUFFER_RESET_ON_RATE_CHANGE\
ENABLE RX_CB_DISP_0_0 false RX_CB_DISP_0_1 false RX_CB_DISP_0_2 false\
RX_CB_DISP_0_3 false RX_CB_DISP_1_0 false RX_CB_DISP_1_1 false RX_CB_DISP_1_2\
false RX_CB_DISP_1_3 false RX_CB_K_0_0 false RX_CB_K_0_1 false RX_CB_K_0_2\
false RX_CB_K_0_3 false RX_CB_K_1_0 false RX_CB_K_1_1 false RX_CB_K_1_2 false\
RX_CB_K_1_3 false RX_CB_LEN_SEQ 1 RX_CB_MASK_0_0 false RX_CB_MASK_0_1 false\
RX_CB_MASK_0_2 false RX_CB_MASK_0_3 false RX_CB_MASK_1_0 false RX_CB_MASK_1_1\
false RX_CB_MASK_1_2 false RX_CB_MASK_1_3 false RX_CB_MAX_LEVEL 1\
RX_CB_MAX_SKEW 1 RX_CB_NUM_SEQ 0 RX_CB_VAL_0_0 00000000 RX_CB_VAL_0_1 00000000\
RX_CB_VAL_0_2 00000000 RX_CB_VAL_0_3 00000000 RX_CB_VAL_1_0 00000000\
RX_CB_VAL_1_1 00000000 RX_CB_VAL_1_2 00000000 RX_CB_VAL_1_3 00000000\
RX_CC_DISP_0_0 false RX_CC_DISP_0_1 false RX_CC_DISP_0_2 false RX_CC_DISP_0_3\
false RX_CC_DISP_1_0 false RX_CC_DISP_1_1 false RX_CC_DISP_1_2 false\
RX_CC_DISP_1_3 false RX_CC_KEEP_IDLE DISABLE RX_CC_K_0_0 false RX_CC_K_0_1\
false RX_CC_K_0_2 false RX_CC_K_0_3 false RX_CC_K_1_0 false RX_CC_K_1_1 false\
RX_CC_K_1_2 false RX_CC_K_1_3 false RX_CC_LEN_SEQ 1 RX_CC_MASK_0_0 false\
RX_CC_MASK_0_1 false RX_CC_MASK_0_2 false RX_CC_MASK_0_3 false RX_CC_MASK_1_0\
false RX_CC_MASK_1_1 false RX_CC_MASK_1_2 false RX_CC_MASK_1_3 false\
RX_CC_NUM_SEQ 0 RX_CC_PERIODICITY 5000 RX_CC_PRECEDENCE ENABLE\
RX_CC_REPEAT_WAIT 0 RX_CC_VAL\
00000000000000000000000000000000000000000000000000000000000000000000000000000000\
RX_CC_VAL_0_0 0000000000 RX_CC_VAL_0_1 0000000000 RX_CC_VAL_0_2 0000000000\
RX_CC_VAL_0_3 0000000000 RX_CC_VAL_1_0 0000000000 RX_CC_VAL_1_1 0000000000\
RX_CC_VAL_1_2 0000000000 RX_CC_VAL_1_3 0000000000 RX_COMMA_ALIGN_WORD 1\
RX_COMMA_DOUBLE_ENABLE false RX_COMMA_MASK 1111111111 RX_COMMA_M_ENABLE false\
RX_COMMA_M_VAL 1010000011 RX_COMMA_PRESET NONE RX_COMMA_P_ENABLE false\
RX_COMMA_P_VAL 0101111100 RX_COMMA_SHOW_REALIGN_ENABLE true RX_COMMA_VALID_ONLY\
0 RX_COUPLING AC RX_DATA_DECODING RAW RX_EQ_MODE AUTO RX_FRACN_ENABLED false\
RX_FRACN_NUMERATOR 0 RX_INT_DATA_WIDTH 32 RX_JTOL_FC 0 RX_JTOL_LF_SLOPE -20\
RX_LINE_RATE 10.3125 RX_OUTCLK_SOURCE RXOUTCLKPMA RX_PLL_TYPE LCPLL\
RX_PPM_OFFSET 0 RX_REFCLK_FREQUENCY 156.25 RX_REFCLK_SOURCE R0 RX_SLIDE_MODE\
OFF RX_SSC_PPM 0 RX_TERMINATION PROGRAMMABLE RX_TERMINATION_PROG_VALUE 800\
RX_USER_DATA_WIDTH 32 TXPROGDIV_FREQ_ENABLE false TXPROGDIV_FREQ_SOURCE LCPLL\
TXPROGDIV_FREQ_VAL 322.265625 TX_64B66B_CRC false TX_RATE_GROUP A\
TX_64B66B_ENCODER false TX_64B66B_SCRAMBLER false TX_ACTUAL_REFCLK_FREQUENCY\
156.25 TX_BUFFER_BYPASS_MODE Fast_Sync TX_BUFFER_MODE 1\
TX_BUFFER_RESET_ON_RATE_CHANGE ENABLE TX_DATA_ENCODING RAW\
TX_DIFF_SWING_EMPH_MODE CUSTOM TX_FRACN_ENABLED false TX_FRACN_NUMERATOR 0\
TX_INT_DATA_WIDTH 32 TX_LINE_RATE 10.3125 TX_OUTCLK_SOURCE TXOUTCLKPMA\
TX_PIPM_ENABLE false TX_PLL_TYPE LCPLL TX_REFCLK_FREQUENCY 156.25\
TX_REFCLK_SOURCE R0 TX_USER_DATA_WIDTH 32}\
   CONFIG.PROT5_LR0_SETTINGS {GT_TYPE GTY GT_DIRECTION DUPLEX INS_LOSS_NYQ 20 INTERNAL_PRESET None OOB_ENABLE\
false PCIE_ENABLE false PCIE_USERCLK2_FREQ 250 PCIE_USERCLK_FREQ 250 PRESET\
None RESET_SEQUENCE_INTERVAL 0 RXPROGDIV_FREQ_ENABLE false\
RXPROGDIV_FREQ_SOURCE LCPLL RXPROGDIV_FREQ_VAL 322.265625 RX_64B66B_CRC false\
RX_RATE_GROUP A RX_64B66B_DECODER false RX_64B66B_DESCRAMBLER false\
RX_ACTUAL_REFCLK_FREQUENCY 156.25 RX_BUFFER_BYPASS_MODE Fast_Sync\
RX_BUFFER_BYPASS_MODE_LANE MULTI RX_BUFFER_MODE 1 RX_BUFFER_RESET_ON_CB_CHANGE\
ENABLE RX_BUFFER_RESET_ON_COMMAALIGN DISABLE RX_BUFFER_RESET_ON_RATE_CHANGE\
ENABLE RX_CB_DISP_0_0 false RX_CB_DISP_0_1 false RX_CB_DISP_0_2 false\
RX_CB_DISP_0_3 false RX_CB_DISP_1_0 false RX_CB_DISP_1_1 false RX_CB_DISP_1_2\
false RX_CB_DISP_1_3 false RX_CB_K_0_0 false RX_CB_K_0_1 false RX_CB_K_0_2\
false RX_CB_K_0_3 false RX_CB_K_1_0 false RX_CB_K_1_1 false RX_CB_K_1_2 false\
RX_CB_K_1_3 false RX_CB_LEN_SEQ 1 RX_CB_MASK_0_0 false RX_CB_MASK_0_1 false\
RX_CB_MASK_0_2 false RX_CB_MASK_0_3 false RX_CB_MASK_1_0 false RX_CB_MASK_1_1\
false RX_CB_MASK_1_2 false RX_CB_MASK_1_3 false RX_CB_MAX_LEVEL 1\
RX_CB_MAX_SKEW 1 RX_CB_NUM_SEQ 0 RX_CB_VAL_0_0 00000000 RX_CB_VAL_0_1 00000000\
RX_CB_VAL_0_2 00000000 RX_CB_VAL_0_3 00000000 RX_CB_VAL_1_0 00000000\
RX_CB_VAL_1_1 00000000 RX_CB_VAL_1_2 00000000 RX_CB_VAL_1_3 00000000\
RX_CC_DISP_0_0 false RX_CC_DISP_0_1 false RX_CC_DISP_0_2 false RX_CC_DISP_0_3\
false RX_CC_DISP_1_0 false RX_CC_DISP_1_1 false RX_CC_DISP_1_2 false\
RX_CC_DISP_1_3 false RX_CC_KEEP_IDLE DISABLE RX_CC_K_0_0 false RX_CC_K_0_1\
false RX_CC_K_0_2 false RX_CC_K_0_3 false RX_CC_K_1_0 false RX_CC_K_1_1 false\
RX_CC_K_1_2 false RX_CC_K_1_3 false RX_CC_LEN_SEQ 1 RX_CC_MASK_0_0 false\
RX_CC_MASK_0_1 false RX_CC_MASK_0_2 false RX_CC_MASK_0_3 false RX_CC_MASK_1_0\
false RX_CC_MASK_1_1 false RX_CC_MASK_1_2 false RX_CC_MASK_1_3 false\
RX_CC_NUM_SEQ 0 RX_CC_PERIODICITY 5000 RX_CC_PRECEDENCE ENABLE\
RX_CC_REPEAT_WAIT 0 RX_CC_VAL\
00000000000000000000000000000000000000000000000000000000000000000000000000000000\
RX_CC_VAL_0_0 0000000000 RX_CC_VAL_0_1 0000000000 RX_CC_VAL_0_2 0000000000\
RX_CC_VAL_0_3 0000000000 RX_CC_VAL_1_0 0000000000 RX_CC_VAL_1_1 0000000000\
RX_CC_VAL_1_2 0000000000 RX_CC_VAL_1_3 0000000000 RX_COMMA_ALIGN_WORD 1\
RX_COMMA_DOUBLE_ENABLE false RX_COMMA_MASK 1111111111 RX_COMMA_M_ENABLE false\
RX_COMMA_M_VAL 1010000011 RX_COMMA_PRESET NONE RX_COMMA_P_ENABLE false\
RX_COMMA_P_VAL 0101111100 RX_COMMA_SHOW_REALIGN_ENABLE true RX_COMMA_VALID_ONLY\
0 RX_COUPLING AC RX_DATA_DECODING RAW RX_EQ_MODE AUTO RX_FRACN_ENABLED false\
RX_FRACN_NUMERATOR 0 RX_INT_DATA_WIDTH 32 RX_JTOL_FC 0 RX_JTOL_LF_SLOPE -20\
RX_LINE_RATE 10.3125 RX_OUTCLK_SOURCE RXOUTCLKPMA RX_PLL_TYPE LCPLL\
RX_PPM_OFFSET 0 RX_REFCLK_FREQUENCY 156.25 RX_REFCLK_SOURCE R0 RX_SLIDE_MODE\
OFF RX_SSC_PPM 0 RX_TERMINATION PROGRAMMABLE RX_TERMINATION_PROG_VALUE 800\
RX_USER_DATA_WIDTH 32 TXPROGDIV_FREQ_ENABLE false TXPROGDIV_FREQ_SOURCE LCPLL\
TXPROGDIV_FREQ_VAL 322.265625 TX_64B66B_CRC false TX_RATE_GROUP A\
TX_64B66B_ENCODER false TX_64B66B_SCRAMBLER false TX_ACTUAL_REFCLK_FREQUENCY\
156.25 TX_BUFFER_BYPASS_MODE Fast_Sync TX_BUFFER_MODE 1\
TX_BUFFER_RESET_ON_RATE_CHANGE ENABLE TX_DATA_ENCODING RAW\
TX_DIFF_SWING_EMPH_MODE CUSTOM TX_FRACN_ENABLED false TX_FRACN_NUMERATOR 0\
TX_INT_DATA_WIDTH 32 TX_LINE_RATE 10.3125 TX_OUTCLK_SOURCE TXOUTCLKPMA\
TX_PIPM_ENABLE false TX_PLL_TYPE LCPLL TX_REFCLK_FREQUENCY 156.25\
TX_REFCLK_SOURCE R0 TX_USER_DATA_WIDTH 32}\
   CONFIG.PROT6_LR0_SETTINGS {GT_TYPE GTY GT_DIRECTION DUPLEX INS_LOSS_NYQ 20 INTERNAL_PRESET None OOB_ENABLE\
false PCIE_ENABLE false PCIE_USERCLK2_FREQ 250 PCIE_USERCLK_FREQ 250 PRESET\
None RESET_SEQUENCE_INTERVAL 0 RXPROGDIV_FREQ_ENABLE false\
RXPROGDIV_FREQ_SOURCE LCPLL RXPROGDIV_FREQ_VAL 322.265625 RX_64B66B_CRC false\
RX_RATE_GROUP A RX_64B66B_DECODER false RX_64B66B_DESCRAMBLER false\
RX_ACTUAL_REFCLK_FREQUENCY 156.25 RX_BUFFER_BYPASS_MODE Fast_Sync\
RX_BUFFER_BYPASS_MODE_LANE MULTI RX_BUFFER_MODE 1 RX_BUFFER_RESET_ON_CB_CHANGE\
ENABLE RX_BUFFER_RESET_ON_COMMAALIGN DISABLE RX_BUFFER_RESET_ON_RATE_CHANGE\
ENABLE RX_CB_DISP_0_0 false RX_CB_DISP_0_1 false RX_CB_DISP_0_2 false\
RX_CB_DISP_0_3 false RX_CB_DISP_1_0 false RX_CB_DISP_1_1 false RX_CB_DISP_1_2\
false RX_CB_DISP_1_3 false RX_CB_K_0_0 false RX_CB_K_0_1 false RX_CB_K_0_2\
false RX_CB_K_0_3 false RX_CB_K_1_0 false RX_CB_K_1_1 false RX_CB_K_1_2 false\
RX_CB_K_1_3 false RX_CB_LEN_SEQ 1 RX_CB_MASK_0_0 false RX_CB_MASK_0_1 false\
RX_CB_MASK_0_2 false RX_CB_MASK_0_3 false RX_CB_MASK_1_0 false RX_CB_MASK_1_1\
false RX_CB_MASK_1_2 false RX_CB_MASK_1_3 false RX_CB_MAX_LEVEL 1\
RX_CB_MAX_SKEW 1 RX_CB_NUM_SEQ 0 RX_CB_VAL_0_0 00000000 RX_CB_VAL_0_1 00000000\
RX_CB_VAL_0_2 00000000 RX_CB_VAL_0_3 00000000 RX_CB_VAL_1_0 00000000\
RX_CB_VAL_1_1 00000000 RX_CB_VAL_1_2 00000000 RX_CB_VAL_1_3 00000000\
RX_CC_DISP_0_0 false RX_CC_DISP_0_1 false RX_CC_DISP_0_2 false RX_CC_DISP_0_3\
false RX_CC_DISP_1_0 false RX_CC_DISP_1_1 false RX_CC_DISP_1_2 false\
RX_CC_DISP_1_3 false RX_CC_KEEP_IDLE DISABLE RX_CC_K_0_0 false RX_CC_K_0_1\
false RX_CC_K_0_2 false RX_CC_K_0_3 false RX_CC_K_1_0 false RX_CC_K_1_1 false\
RX_CC_K_1_2 false RX_CC_K_1_3 false RX_CC_LEN_SEQ 1 RX_CC_MASK_0_0 false\
RX_CC_MASK_0_1 false RX_CC_MASK_0_2 false RX_CC_MASK_0_3 false RX_CC_MASK_1_0\
false RX_CC_MASK_1_1 false RX_CC_MASK_1_2 false RX_CC_MASK_1_3 false\
RX_CC_NUM_SEQ 0 RX_CC_PERIODICITY 5000 RX_CC_PRECEDENCE ENABLE\
RX_CC_REPEAT_WAIT 0 RX_CC_VAL\
00000000000000000000000000000000000000000000000000000000000000000000000000000000\
RX_CC_VAL_0_0 0000000000 RX_CC_VAL_0_1 0000000000 RX_CC_VAL_0_2 0000000000\
RX_CC_VAL_0_3 0000000000 RX_CC_VAL_1_0 0000000000 RX_CC_VAL_1_1 0000000000\
RX_CC_VAL_1_2 0000000000 RX_CC_VAL_1_3 0000000000 RX_COMMA_ALIGN_WORD 1\
RX_COMMA_DOUBLE_ENABLE false RX_COMMA_MASK 1111111111 RX_COMMA_M_ENABLE false\
RX_COMMA_M_VAL 1010000011 RX_COMMA_PRESET NONE RX_COMMA_P_ENABLE false\
RX_COMMA_P_VAL 0101111100 RX_COMMA_SHOW_REALIGN_ENABLE true RX_COMMA_VALID_ONLY\
0 RX_COUPLING AC RX_DATA_DECODING RAW RX_EQ_MODE AUTO RX_FRACN_ENABLED false\
RX_FRACN_NUMERATOR 0 RX_INT_DATA_WIDTH 32 RX_JTOL_FC 0 RX_JTOL_LF_SLOPE -20\
RX_LINE_RATE 10.3125 RX_OUTCLK_SOURCE RXOUTCLKPMA RX_PLL_TYPE LCPLL\
RX_PPM_OFFSET 0 RX_REFCLK_FREQUENCY 156.25 RX_REFCLK_SOURCE R0 RX_SLIDE_MODE\
OFF RX_SSC_PPM 0 RX_TERMINATION PROGRAMMABLE RX_TERMINATION_PROG_VALUE 800\
RX_USER_DATA_WIDTH 32 TXPROGDIV_FREQ_ENABLE false TXPROGDIV_FREQ_SOURCE LCPLL\
TXPROGDIV_FREQ_VAL 322.265625 TX_64B66B_CRC false TX_RATE_GROUP A\
TX_64B66B_ENCODER false TX_64B66B_SCRAMBLER false TX_ACTUAL_REFCLK_FREQUENCY\
156.25 TX_BUFFER_BYPASS_MODE Fast_Sync TX_BUFFER_MODE 1\
TX_BUFFER_RESET_ON_RATE_CHANGE ENABLE TX_DATA_ENCODING RAW\
TX_DIFF_SWING_EMPH_MODE CUSTOM TX_FRACN_ENABLED false TX_FRACN_NUMERATOR 0\
TX_INT_DATA_WIDTH 32 TX_LINE_RATE 10.3125 TX_OUTCLK_SOURCE TXOUTCLKPMA\
TX_PIPM_ENABLE false TX_PLL_TYPE LCPLL TX_REFCLK_FREQUENCY 156.25\
TX_REFCLK_SOURCE R0 TX_USER_DATA_WIDTH 32}\
   CONFIG.PROT7_LR0_SETTINGS {GT_TYPE GTY GT_DIRECTION DUPLEX INS_LOSS_NYQ 20 INTERNAL_PRESET None OOB_ENABLE\
false PCIE_ENABLE false PCIE_USERCLK2_FREQ 250 PCIE_USERCLK_FREQ 250 PRESET\
None RESET_SEQUENCE_INTERVAL 0 RXPROGDIV_FREQ_ENABLE false\
RXPROGDIV_FREQ_SOURCE LCPLL RXPROGDIV_FREQ_VAL 322.265625 RX_64B66B_CRC false\
RX_RATE_GROUP A RX_64B66B_DECODER false RX_64B66B_DESCRAMBLER false\
RX_ACTUAL_REFCLK_FREQUENCY 156.25 RX_BUFFER_BYPASS_MODE Fast_Sync\
RX_BUFFER_BYPASS_MODE_LANE MULTI RX_BUFFER_MODE 1 RX_BUFFER_RESET_ON_CB_CHANGE\
ENABLE RX_BUFFER_RESET_ON_COMMAALIGN DISABLE RX_BUFFER_RESET_ON_RATE_CHANGE\
ENABLE RX_CB_DISP_0_0 false RX_CB_DISP_0_1 false RX_CB_DISP_0_2 false\
RX_CB_DISP_0_3 false RX_CB_DISP_1_0 false RX_CB_DISP_1_1 false RX_CB_DISP_1_2\
false RX_CB_DISP_1_3 false RX_CB_K_0_0 false RX_CB_K_0_1 false RX_CB_K_0_2\
false RX_CB_K_0_3 false RX_CB_K_1_0 false RX_CB_K_1_1 false RX_CB_K_1_2 false\
RX_CB_K_1_3 false RX_CB_LEN_SEQ 1 RX_CB_MASK_0_0 false RX_CB_MASK_0_1 false\
RX_CB_MASK_0_2 false RX_CB_MASK_0_3 false RX_CB_MASK_1_0 false RX_CB_MASK_1_1\
false RX_CB_MASK_1_2 false RX_CB_MASK_1_3 false RX_CB_MAX_LEVEL 1\
RX_CB_MAX_SKEW 1 RX_CB_NUM_SEQ 0 RX_CB_VAL_0_0 00000000 RX_CB_VAL_0_1 00000000\
RX_CB_VAL_0_2 00000000 RX_CB_VAL_0_3 00000000 RX_CB_VAL_1_0 00000000\
RX_CB_VAL_1_1 00000000 RX_CB_VAL_1_2 00000000 RX_CB_VAL_1_3 00000000\
RX_CC_DISP_0_0 false RX_CC_DISP_0_1 false RX_CC_DISP_0_2 false RX_CC_DISP_0_3\
false RX_CC_DISP_1_0 false RX_CC_DISP_1_1 false RX_CC_DISP_1_2 false\
RX_CC_DISP_1_3 false RX_CC_KEEP_IDLE DISABLE RX_CC_K_0_0 false RX_CC_K_0_1\
false RX_CC_K_0_2 false RX_CC_K_0_3 false RX_CC_K_1_0 false RX_CC_K_1_1 false\
RX_CC_K_1_2 false RX_CC_K_1_3 false RX_CC_LEN_SEQ 1 RX_CC_MASK_0_0 false\
RX_CC_MASK_0_1 false RX_CC_MASK_0_2 false RX_CC_MASK_0_3 false RX_CC_MASK_1_0\
false RX_CC_MASK_1_1 false RX_CC_MASK_1_2 false RX_CC_MASK_1_3 false\
RX_CC_NUM_SEQ 0 RX_CC_PERIODICITY 5000 RX_CC_PRECEDENCE ENABLE\
RX_CC_REPEAT_WAIT 0 RX_CC_VAL\
00000000000000000000000000000000000000000000000000000000000000000000000000000000\
RX_CC_VAL_0_0 0000000000 RX_CC_VAL_0_1 0000000000 RX_CC_VAL_0_2 0000000000\
RX_CC_VAL_0_3 0000000000 RX_CC_VAL_1_0 0000000000 RX_CC_VAL_1_1 0000000000\
RX_CC_VAL_1_2 0000000000 RX_CC_VAL_1_3 0000000000 RX_COMMA_ALIGN_WORD 1\
RX_COMMA_DOUBLE_ENABLE false RX_COMMA_MASK 1111111111 RX_COMMA_M_ENABLE false\
RX_COMMA_M_VAL 1010000011 RX_COMMA_PRESET NONE RX_COMMA_P_ENABLE false\
RX_COMMA_P_VAL 0101111100 RX_COMMA_SHOW_REALIGN_ENABLE true RX_COMMA_VALID_ONLY\
0 RX_COUPLING AC RX_DATA_DECODING RAW RX_EQ_MODE AUTO RX_FRACN_ENABLED false\
RX_FRACN_NUMERATOR 0 RX_INT_DATA_WIDTH 32 RX_JTOL_FC 0 RX_JTOL_LF_SLOPE -20\
RX_LINE_RATE 10.3125 RX_OUTCLK_SOURCE RXOUTCLKPMA RX_PLL_TYPE LCPLL\
RX_PPM_OFFSET 0 RX_REFCLK_FREQUENCY 156.25 RX_REFCLK_SOURCE R0 RX_SLIDE_MODE\
OFF RX_SSC_PPM 0 RX_TERMINATION PROGRAMMABLE RX_TERMINATION_PROG_VALUE 800\
RX_USER_DATA_WIDTH 32 TXPROGDIV_FREQ_ENABLE false TXPROGDIV_FREQ_SOURCE LCPLL\
TXPROGDIV_FREQ_VAL 322.265625 TX_64B66B_CRC false TX_RATE_GROUP A\
TX_64B66B_ENCODER false TX_64B66B_SCRAMBLER false TX_ACTUAL_REFCLK_FREQUENCY\
156.25 TX_BUFFER_BYPASS_MODE Fast_Sync TX_BUFFER_MODE 1\
TX_BUFFER_RESET_ON_RATE_CHANGE ENABLE TX_DATA_ENCODING RAW\
TX_DIFF_SWING_EMPH_MODE CUSTOM TX_FRACN_ENABLED false TX_FRACN_NUMERATOR 0\
TX_INT_DATA_WIDTH 32 TX_LINE_RATE 10.3125 TX_OUTCLK_SOURCE TXOUTCLKPMA\
TX_PIPM_ENABLE false TX_PLL_TYPE LCPLL TX_REFCLK_FREQUENCY 156.25\
TX_REFCLK_SOURCE R0 TX_USER_DATA_WIDTH 32}\
   CONFIG.REFCLK_STRING {HSCLK0_LCPLLGTREFCLK0 refclk_PROT0_R0_156.25_MHz_unique1 HSCLK1_LCPLLGTREFCLK0\
refclk_PROT0_R0_156.25_MHz_unique1}\
 ] $gt_quad_base

  # Create instance: urlp, and set properties
  set urlp [ create_bd_cell -type ip -vlnv xilinx.com:ip:util_reduced_logic:2.0 urlp ]
  set_property -dict [ list \
   CONFIG.C_SIZE {1} \
 ] $urlp

  # Create instance: util_ds_buf, and set properties
  set util_ds_buf [ create_bd_cell -type ip -vlnv xilinx.com:ip:util_ds_buf:2.2 util_ds_buf ]
  set_property -dict [ list \
   CONFIG.C_BUF_TYPE {IBUFDSGTE} \
 ] $util_ds_buf

  # Create instance: xlcp, and set properties
  set xlcp [ create_bd_cell -type ip -vlnv xilinx.com:ip:xlconcat:2.1 xlcp ]
  set_property -dict [ list \
   CONFIG.NUM_PORTS {1} \
 ] $xlcp

  # Create interface connections
  connect_bd_intf_net -intf_net bridge_refclkX0Y10_GT_RX0 [get_bd_intf_pins bridge_refclkX0Y10/GT_RX0] [get_bd_intf_pins gt_quad_base/RX0_GT_IP_Interface]
  connect_bd_intf_net -intf_net bridge_refclkX0Y10_GT_RX1 [get_bd_intf_pins bridge_refclkX0Y10/GT_RX1] [get_bd_intf_pins gt_quad_base/RX1_GT_IP_Interface]
  connect_bd_intf_net -intf_net bridge_refclkX0Y10_GT_RX2 [get_bd_intf_pins bridge_refclkX0Y10/GT_RX2] [get_bd_intf_pins gt_quad_base/RX2_GT_IP_Interface]
  connect_bd_intf_net -intf_net bridge_refclkX0Y10_GT_RX3 [get_bd_intf_pins bridge_refclkX0Y10/GT_RX3] [get_bd_intf_pins gt_quad_base/RX3_GT_IP_Interface]
  connect_bd_intf_net -intf_net bridge_refclkX0Y10_GT_TX0 [get_bd_intf_pins bridge_refclkX0Y10/GT_TX0] [get_bd_intf_pins gt_quad_base/TX0_GT_IP_Interface]
  connect_bd_intf_net -intf_net bridge_refclkX0Y10_GT_TX1 [get_bd_intf_pins bridge_refclkX0Y10/GT_TX1] [get_bd_intf_pins gt_quad_base/TX1_GT_IP_Interface]
  connect_bd_intf_net -intf_net bridge_refclkX0Y10_GT_TX2 [get_bd_intf_pins bridge_refclkX0Y10/GT_TX2] [get_bd_intf_pins gt_quad_base/TX2_GT_IP_Interface]
  connect_bd_intf_net -intf_net bridge_refclkX0Y10_GT_TX3 [get_bd_intf_pins bridge_refclkX0Y10/GT_TX3] [get_bd_intf_pins gt_quad_base/TX3_GT_IP_Interface]
  connect_bd_intf_net -intf_net bridge_refclkX0Y10_diff_gt_ref_clock_1 [get_bd_intf_pins bridge_refclkX0Y10_diff_gt_ref_clock] [get_bd_intf_pins util_ds_buf/CLK_IN_D]
  connect_bd_intf_net -intf_net gt_quad_base_GT_Serial [get_bd_intf_pins GT_Serial] [get_bd_intf_pins gt_quad_base/GT_Serial]

  # Create port connections
  connect_bd_net -net bufg_gt_1_usrclk [get_bd_pins bridge_refclkX0Y10/gt_txusrclk] [get_bd_pins bufg_gt_1/usrclk] [get_bd_pins gt_quad_base/ch0_txusrclk] [get_bd_pins gt_quad_base/ch1_txusrclk] [get_bd_pins gt_quad_base/ch2_txusrclk] [get_bd_pins gt_quad_base/ch3_txusrclk]
  connect_bd_net -net bufg_gt_usrclk [get_bd_pins bridge_refclkX0Y10/gt_rxusrclk] [get_bd_pins bufg_gt/usrclk] [get_bd_pins gt_quad_base/ch0_rxusrclk] [get_bd_pins gt_quad_base/ch1_rxusrclk] [get_bd_pins gt_quad_base/ch2_rxusrclk] [get_bd_pins gt_quad_base/ch3_rxusrclk]
  connect_bd_net -net gt_quad_base_ch0_rxoutclk [get_bd_pins bufg_gt/outclk] [get_bd_pins gt_quad_base/ch0_rxoutclk]
  connect_bd_net -net gt_quad_base_ch0_txoutclk [get_bd_pins bufg_gt_1/outclk] [get_bd_pins gt_quad_base/ch0_txoutclk]
  connect_bd_net -net gt_quad_base_gtpowergood [get_bd_pins gt_quad_base/gtpowergood] [get_bd_pins xlcp/In0]
  connect_bd_net -net urlp_Res [get_bd_pins bridge_refclkX0Y10/gtpowergood] [get_bd_pins urlp/Res]
  connect_bd_net -net util_ds_buf_IBUF_OUT [get_bd_pins gt_quad_base/GT_REFCLK0] [get_bd_pins util_ds_buf/IBUF_OUT]
  connect_bd_net -net versal_cips_0_pl0_ref_clk [get_bd_pins apb3clk] [get_bd_pins bridge_refclkX0Y10/apb3clk] [get_bd_pins gt_quad_base/apb3clk]
  connect_bd_net -net xlcp_dout [get_bd_pins urlp/Op1] [get_bd_pins xlcp/dout]

  # Restore current instance
  current_bd_instance $oldCurInst
}

# Hierarchical cell: counters
proc create_hier_cell_counters { parentCell nameHier } {

  variable script_folder

  if { $parentCell eq "" || $nameHier eq "" } {
     catch {common::send_gid_msg -ssname BD::TCL -id 2092 -severity "ERROR" "create_hier_cell_counters() - Empty argument(s)!"}
     return
  }

  # Get object for parentCell
  set parentObj [get_bd_cells $parentCell]
  if { $parentObj == "" } {
     catch {common::send_gid_msg -ssname BD::TCL -id 2090 -severity "ERROR" "Unable to find parent cell <$parentCell>!"}
     return
  }

  # Make sure parentObj is hier blk
  set parentType [get_property TYPE $parentObj]
  if { $parentType ne "hier" } {
     catch {common::send_gid_msg -ssname BD::TCL -id 2091 -severity "ERROR" "Parent <$parentObj> has TYPE = <$parentType>. Expected to be <hier>."}
     return
  }

  # Save current instance; Restore later
  set oldCurInst [current_bd_instance .]

  # Set parent object as current
  current_bd_instance $parentObj

  # Create cell and set as current instance
  set hier_obj [create_bd_cell -type hier $nameHier]
  current_bd_instance $hier_obj

  # Create interface pins

  # Create pins
  create_bd_pin -dir I -type clk clk100
  create_bd_pin -dir I -type clk clk200

  # Create instance: const1, and set properties
  set const1 [ create_bd_cell -type ip -vlnv xilinx.com:ip:xlconstant:1.1 const1 ]

  # Create instance: fast_cosine, and set properties
  set fast_cosine [ create_bd_cell -type ip -vlnv xilinx.com:ip:xlslice:1.0 fast_cosine ]
  set_property -dict [ list \
   CONFIG.DIN_FROM {15} \
   CONFIG.DIN_TO {0} \
   CONFIG.DOUT_WIDTH {16} \
 ] $fast_cosine

  # Create instance: fast_counter_0, and set properties
  set fast_counter_0 [ create_bd_cell -type ip -vlnv xilinx.com:ip:c_counter_binary:12.0 fast_counter_0 ]
  set_property -dict [ list \
   CONFIG.CE {true} \
   CONFIG.Count_Mode {UPDOWN} \
   CONFIG.Load {true} \
   CONFIG.Output_Width {32} \
   CONFIG.SCLR {true} \
 ] $fast_counter_0

  # Create instance: fast_dds_compiler_0, and set properties
  set fast_dds_compiler_0 [ create_bd_cell -type ip -vlnv xilinx.com:ip:dds_compiler:6.0 fast_dds_compiler_0 ]
  set_property -dict [ list \
   CONFIG.DATA_Has_TLAST {Not_Required} \
   CONFIG.Has_Phase_Out {false} \
   CONFIG.Latency {2} \
   CONFIG.M_DATA_Has_TUSER {Not_Required} \
   CONFIG.Noise_Shaping {None} \
   CONFIG.Output_Frequency1 {0} \
   CONFIG.Output_Selection {Sine_and_Cosine} \
   CONFIG.Output_Width {16} \
   CONFIG.PINC1 {0} \
   CONFIG.Parameter_Entry {Hardware_Parameters} \
   CONFIG.PartsPresent {SIN_COS_LUT_only} \
   CONFIG.Phase_Width {10} \
   CONFIG.S_PHASE_Has_TUSER {Not_Required} \
 ] $fast_dds_compiler_0

  # Create instance: fast_phase, and set properties
  set fast_phase [ create_bd_cell -type ip -vlnv xilinx.com:ip:xlslice:1.0 fast_phase ]
  set_property -dict [ list \
   CONFIG.DIN_FROM {15} \
   CONFIG.DIN_TO {0} \
   CONFIG.DOUT_WIDTH {16} \
 ] $fast_phase

  # Create instance: fast_sine, and set properties
  set fast_sine [ create_bd_cell -type ip -vlnv xilinx.com:ip:xlslice:1.0 fast_sine ]
  set_property -dict [ list \
   CONFIG.DIN_FROM {31} \
   CONFIG.DIN_TO {16} \
   CONFIG.DOUT_WIDTH {16} \
 ] $fast_sine

  # Create instance: ila_fast_counter_0, and set properties
  set ila_fast_counter_0 [ create_bd_cell -type ip -vlnv xilinx.com:ip:axis_ila:1.1 ila_fast_counter_0 ]
  set_property -dict [ list \
   CONFIG.ALL_PROBE_SAME_MU_CNT {4} \
   CONFIG.C_ADV_TRIGGER {true} \
   CONFIG.C_BRAM_CNT {12} \
   CONFIG.C_DATA_DEPTH {4096} \
   CONFIG.C_INPUT_PIPE_STAGES {2} \
   CONFIG.C_NUM_OF_PROBES {12} \
   CONFIG.C_PROBE0_MU_CNT {4} \
   CONFIG.C_PROBE10_MU_CNT {4} \
   CONFIG.C_PROBE10_WIDTH {16} \
   CONFIG.C_PROBE11_MU_CNT {4} \
   CONFIG.C_PROBE11_WIDTH {16} \
   CONFIG.C_PROBE1_MU_CNT {4} \
   CONFIG.C_PROBE2_MU_CNT {4} \
   CONFIG.C_PROBE3_MU_CNT {4} \
   CONFIG.C_PROBE4_MU_CNT {4} \
   CONFIG.C_PROBE4_WIDTH {32} \
   CONFIG.C_PROBE5_MU_CNT {4} \
   CONFIG.C_PROBE5_WIDTH {32} \
   CONFIG.C_PROBE6_MU_CNT {4} \
   CONFIG.C_PROBE7_MU_CNT {4} \
   CONFIG.C_PROBE8_MU_CNT {4} \
   CONFIG.C_PROBE9_MU_CNT {4} \
   CONFIG.C_TRIGIN_EN {true} \
   CONFIG.C_TRIGOUT_EN {true} \
 ] $ila_fast_counter_0

  # Create instance: ila_slow_counter_0, and set properties
  set ila_slow_counter_0 [ create_bd_cell -type ip -vlnv xilinx.com:ip:axis_ila:1.1 ila_slow_counter_0 ]
  set_property -dict [ list \
   CONFIG.ALL_PROBE_SAME_MU_CNT {4} \
   CONFIG.C_ADV_TRIGGER {true} \
   CONFIG.C_BRAM_CNT {12} \
   CONFIG.C_DATA_DEPTH {4096} \
   CONFIG.C_INPUT_PIPE_STAGES {2} \
   CONFIG.C_NUM_OF_PROBES {12} \
   CONFIG.C_PROBE0_MU_CNT {4} \
   CONFIG.C_PROBE10_MU_CNT {4} \
   CONFIG.C_PROBE10_WIDTH {16} \
   CONFIG.C_PROBE11_MU_CNT {4} \
   CONFIG.C_PROBE11_WIDTH {16} \
   CONFIG.C_PROBE1_MU_CNT {4} \
   CONFIG.C_PROBE2_MU_CNT {4} \
   CONFIG.C_PROBE3_MU_CNT {4} \
   CONFIG.C_PROBE4_MU_CNT {4} \
   CONFIG.C_PROBE4_WIDTH {32} \
   CONFIG.C_PROBE5_MU_CNT {4} \
   CONFIG.C_PROBE5_WIDTH {32} \
   CONFIG.C_PROBE6_MU_CNT {4} \
   CONFIG.C_PROBE7_MU_CNT {4} \
   CONFIG.C_PROBE8_MU_CNT {4} \
   CONFIG.C_PROBE9_MU_CNT {4} \
   CONFIG.C_TRIGIN_EN {true} \
   CONFIG.C_TRIGOUT_EN {true} \
 ] $ila_slow_counter_0

  # Create instance: slow_cosine, and set properties
  set slow_cosine [ create_bd_cell -type ip -vlnv xilinx.com:ip:xlslice:1.0 slow_cosine ]
  set_property -dict [ list \
   CONFIG.DIN_FROM {15} \
   CONFIG.DIN_TO {0} \
   CONFIG.DOUT_WIDTH {16} \
 ] $slow_cosine

  # Create instance: slow_counter_0, and set properties
  set slow_counter_0 [ create_bd_cell -type ip -vlnv xilinx.com:ip:c_counter_binary:12.0 slow_counter_0 ]
  set_property -dict [ list \
   CONFIG.CE {true} \
   CONFIG.Count_Mode {UPDOWN} \
   CONFIG.Load {true} \
   CONFIG.Output_Width {32} \
   CONFIG.SCLR {true} \
 ] $slow_counter_0

  # Create instance: slow_dds_compiler_0, and set properties
  set slow_dds_compiler_0 [ create_bd_cell -type ip -vlnv xilinx.com:ip:dds_compiler:6.0 slow_dds_compiler_0 ]
  set_property -dict [ list \
   CONFIG.DATA_Has_TLAST {Not_Required} \
   CONFIG.Has_Phase_Out {false} \
   CONFIG.Latency {2} \
   CONFIG.M_DATA_Has_TUSER {Not_Required} \
   CONFIG.Noise_Shaping {None} \
   CONFIG.Output_Frequency1 {0} \
   CONFIG.Output_Selection {Sine_and_Cosine} \
   CONFIG.Output_Width {16} \
   CONFIG.PINC1 {0} \
   CONFIG.Parameter_Entry {Hardware_Parameters} \
   CONFIG.PartsPresent {SIN_COS_LUT_only} \
   CONFIG.Phase_Width {10} \
   CONFIG.S_PHASE_Has_TUSER {Not_Required} \
 ] $slow_dds_compiler_0

  # Create instance: slow_phase, and set properties
  set slow_phase [ create_bd_cell -type ip -vlnv xilinx.com:ip:xlslice:1.0 slow_phase ]
  set_property -dict [ list \
   CONFIG.DIN_FROM {15} \
   CONFIG.DIN_TO {0} \
   CONFIG.DOUT_WIDTH {16} \
 ] $slow_phase

  # Create instance: slow_sine, and set properties
  set slow_sine [ create_bd_cell -type ip -vlnv xilinx.com:ip:xlslice:1.0 slow_sine ]
  set_property -dict [ list \
   CONFIG.DIN_FROM {31} \
   CONFIG.DIN_TO {16} \
   CONFIG.DOUT_WIDTH {16} \
 ] $slow_sine

  # Create instance: vio_fast_counter_0, and set properties
  set vio_fast_counter_0 [ create_bd_cell -type ip -vlnv xilinx.com:ip:axis_vio:1.0 vio_fast_counter_0 ]
  set_property -dict [ list \
   CONFIG.C_NUM_PROBE_OUT {5} \
   CONFIG.C_PROBE_IN0_WIDTH {32} \
   CONFIG.C_PROBE_OUT0_INIT_VAL {0x1} \
   CONFIG.C_PROBE_OUT2_INIT_VAL {0x1} \
   CONFIG.C_PROBE_OUT4_WIDTH {32} \
 ] $vio_fast_counter_0

  # Create instance: vio_slow_counter_0, and set properties
  set vio_slow_counter_0 [ create_bd_cell -type ip -vlnv xilinx.com:ip:axis_vio:1.0 vio_slow_counter_0 ]
  set_property -dict [ list \
   CONFIG.C_NUM_PROBE_OUT {5} \
   CONFIG.C_PROBE_IN0_WIDTH {32} \
   CONFIG.C_PROBE_OUT0_INIT_VAL {0x1} \
   CONFIG.C_PROBE_OUT2_INIT_VAL {0x1} \
   CONFIG.C_PROBE_OUT4_WIDTH {32} \
 ] $vio_slow_counter_0

  # Create port connections
  connect_bd_net -net clk100 [get_bd_pins clk100] [get_bd_pins ila_slow_counter_0/clk] [get_bd_pins slow_counter_0/CLK] [get_bd_pins slow_dds_compiler_0/aclk] [get_bd_pins vio_slow_counter_0/clk]
  connect_bd_net -net clk200 [get_bd_pins clk200] [get_bd_pins fast_counter_0/CLK] [get_bd_pins fast_dds_compiler_0/aclk] [get_bd_pins ila_fast_counter_0/clk] [get_bd_pins vio_fast_counter_0/clk]
  connect_bd_net -net const1_dout [get_bd_pins const1/dout] [get_bd_pins fast_dds_compiler_0/s_axis_phase_tvalid] [get_bd_pins slow_dds_compiler_0/s_axis_phase_tvalid]
  connect_bd_net -net fast_cosine_Dout [get_bd_pins fast_cosine/Dout] [get_bd_pins ila_fast_counter_0/probe11]
  connect_bd_net -net fast_counter_0_CE [get_bd_pins fast_counter_0/CE] [get_bd_pins ila_fast_counter_0/probe0] [get_bd_pins vio_fast_counter_0/probe_out0]
  connect_bd_net -net fast_counter_0_L [get_bd_pins fast_counter_0/L] [get_bd_pins ila_fast_counter_0/probe4] [get_bd_pins vio_fast_counter_0/probe_out4]
  connect_bd_net -net fast_counter_0_LOAD [get_bd_pins fast_counter_0/LOAD] [get_bd_pins ila_fast_counter_0/probe3] [get_bd_pins vio_fast_counter_0/probe_out3]
  connect_bd_net -net fast_counter_0_Q [get_bd_pins fast_counter_0/Q] [get_bd_pins fast_phase/Din] [get_bd_pins ila_fast_counter_0/probe5] [get_bd_pins vio_fast_counter_0/probe_in0]
  connect_bd_net -net fast_counter_0_SCLR [get_bd_pins fast_counter_0/SCLR] [get_bd_pins ila_fast_counter_0/probe1] [get_bd_pins vio_fast_counter_0/probe_out1]
  connect_bd_net -net fast_counter_0_UP [get_bd_pins fast_counter_0/UP] [get_bd_pins ila_fast_counter_0/probe2] [get_bd_pins vio_fast_counter_0/probe_out2]
  connect_bd_net -net fast_dds_compiler_0_m_axis_data_tdata [get_bd_pins fast_cosine/Din] [get_bd_pins fast_dds_compiler_0/m_axis_data_tdata] [get_bd_pins fast_sine/Din]
  connect_bd_net -net fast_phase_Dout [get_bd_pins fast_dds_compiler_0/s_axis_phase_tdata] [get_bd_pins fast_phase/Dout]
  connect_bd_net -net fast_sine_Dout [get_bd_pins fast_sine/Dout] [get_bd_pins ila_fast_counter_0/probe10]
  connect_bd_net -net ila_fast_counter_0_TRIG_IN_ack [get_bd_pins ila_fast_counter_0/TRIG_IN_ack] [get_bd_pins ila_fast_counter_0/probe9] [get_bd_pins ila_slow_counter_0/TRIG_OUT_ack] [get_bd_pins ila_slow_counter_0/probe7]
  connect_bd_net -net ila_fast_counter_0_TRIG_OUT_trig [get_bd_pins ila_fast_counter_0/TRIG_OUT_trig] [get_bd_pins ila_fast_counter_0/probe6] [get_bd_pins ila_slow_counter_0/TRIG_IN_trig] [get_bd_pins ila_slow_counter_0/probe8]
  connect_bd_net -net ila_slow_counter_0_TRIG_IN_ack [get_bd_pins ila_fast_counter_0/TRIG_OUT_ack] [get_bd_pins ila_fast_counter_0/probe7] [get_bd_pins ila_slow_counter_0/TRIG_IN_ack] [get_bd_pins ila_slow_counter_0/probe9]
  connect_bd_net -net ila_slow_counter_0_TRIG_OUT_trig [get_bd_pins ila_fast_counter_0/TRIG_IN_trig] [get_bd_pins ila_fast_counter_0/probe8] [get_bd_pins ila_slow_counter_0/TRIG_OUT_trig] [get_bd_pins ila_slow_counter_0/probe6]
  connect_bd_net -net slow_cosine_Dout [get_bd_pins ila_slow_counter_0/probe11] [get_bd_pins slow_cosine/Dout]
  connect_bd_net -net slow_counter_0_CE [get_bd_pins ila_slow_counter_0/probe0] [get_bd_pins slow_counter_0/CE] [get_bd_pins vio_slow_counter_0/probe_out0]
  connect_bd_net -net slow_counter_0_L [get_bd_pins ila_slow_counter_0/probe4] [get_bd_pins slow_counter_0/L] [get_bd_pins vio_slow_counter_0/probe_out4]
  connect_bd_net -net slow_counter_0_LOAD [get_bd_pins ila_slow_counter_0/probe3] [get_bd_pins slow_counter_0/LOAD] [get_bd_pins vio_slow_counter_0/probe_out3]
  connect_bd_net -net slow_counter_0_Q [get_bd_pins ila_slow_counter_0/probe5] [get_bd_pins slow_counter_0/Q] [get_bd_pins slow_phase/Din] [get_bd_pins vio_slow_counter_0/probe_in0]
  connect_bd_net -net slow_counter_0_SCLR [get_bd_pins ila_slow_counter_0/probe1] [get_bd_pins slow_counter_0/SCLR] [get_bd_pins vio_slow_counter_0/probe_out1]
  connect_bd_net -net slow_counter_0_UP [get_bd_pins ila_slow_counter_0/probe2] [get_bd_pins slow_counter_0/UP] [get_bd_pins vio_slow_counter_0/probe_out2]
  connect_bd_net -net slow_dds_compiler_0_m_axis_data_tdata [get_bd_pins slow_cosine/Din] [get_bd_pins slow_dds_compiler_0/m_axis_data_tdata] [get_bd_pins slow_sine/Din]
  connect_bd_net -net slow_phase_0 [get_bd_pins slow_dds_compiler_0/s_axis_phase_tdata] [get_bd_pins slow_phase/Dout]
  connect_bd_net -net slow_sine_Dout [get_bd_pins ila_slow_counter_0/probe10] [get_bd_pins slow_sine/Dout]

  # Restore current instance
  current_bd_instance $oldCurInst
}


# Procedure to create entire design; Provide argument to make
# procedure reusable. If parentCell is "", will use root.
proc create_root_design { parentCell } {

  variable script_folder
  variable design_name

  if { $parentCell eq "" } {
     set parentCell [get_bd_cells /]
  }

  # Get object for parentCell
  set parentObj [get_bd_cells $parentCell]
  if { $parentObj == "" } {
     catch {common::send_gid_msg -ssname BD::TCL -id 2090 -severity "ERROR" "Unable to find parent cell <$parentCell>!"}
     return
  }

  # Make sure parentObj is hier blk
  set parentType [get_property TYPE $parentObj]
  if { $parentType ne "hier" } {
     catch {common::send_gid_msg -ssname BD::TCL -id 2091 -severity "ERROR" "Parent <$parentObj> has TYPE = <$parentType>. Expected to be <hier>."}
     return
  }

  # Save current instance; Restore later
  set oldCurInst [current_bd_instance .]

  # Set parent object as current
  current_bd_instance $parentObj


  # Create interface ports
  set GT_Serial [ create_bd_intf_port -mode Master -vlnv xilinx.com:interface:gt_rtl:1.0 GT_Serial ]

  set GT_Serial_1 [ create_bd_intf_port -mode Master -vlnv xilinx.com:interface:gt_rtl:1.0 GT_Serial_1 ]

  set GT_Serial_2 [ create_bd_intf_port -mode Master -vlnv xilinx.com:interface:gt_rtl:1.0 GT_Serial_2 ]

  set GT_Serial_3 [ create_bd_intf_port -mode Master -vlnv xilinx.com:interface:gt_rtl:1.0 GT_Serial_3 ]

  set bridge_refclkX0Y10_diff_gt_ref_clock [ create_bd_intf_port -mode Slave -vlnv xilinx.com:interface:diff_clock_rtl:1.0 bridge_refclkX0Y10_diff_gt_ref_clock ]
  set_property -dict [ list \
   CONFIG.FREQ_HZ {156250000} \
   ] $bridge_refclkX0Y10_diff_gt_ref_clock

  set bridge_refclkX1Y10_diff_gt_ref_clock [ create_bd_intf_port -mode Slave -vlnv xilinx.com:interface:diff_clock_rtl:1.0 bridge_refclkX1Y10_diff_gt_ref_clock ]
  set_property -dict [ list \
   CONFIG.FREQ_HZ {156250000} \
   ] $bridge_refclkX1Y10_diff_gt_ref_clock

  set bridge_refclkX1Y2_diff_gt_ref_clock [ create_bd_intf_port -mode Slave -vlnv xilinx.com:interface:diff_clock_rtl:1.0 bridge_refclkX1Y2_diff_gt_ref_clock ]
  set_property -dict [ list \
   CONFIG.FREQ_HZ {156250000} \
   ] $bridge_refclkX1Y2_diff_gt_ref_clock

  set bridge_refclkX1Y8_diff_gt_ref_clock [ create_bd_intf_port -mode Slave -vlnv xilinx.com:interface:diff_clock_rtl:1.0 bridge_refclkX1Y8_diff_gt_ref_clock ]
  set_property -dict [ list \
   CONFIG.FREQ_HZ {156250000} \
   ] $bridge_refclkX1Y8_diff_gt_ref_clock

  set ddr4_dimm1 [ create_bd_intf_port -mode Master -vlnv xilinx.com:interface:ddr4_rtl:1.0 ddr4_dimm1 ]

  set ddr4_dimm1_sma_clk [ create_bd_intf_port -mode Slave -vlnv xilinx.com:interface:diff_clock_rtl:1.0 ddr4_dimm1_sma_clk ]
  set_property -dict [ list \
   CONFIG.FREQ_HZ {200000000} \
   ] $ddr4_dimm1_sma_clk


  # Create ports

  # Create instance: axi_noc_0, and set properties
  set axi_noc_0 [ create_bd_cell -type ip -vlnv xilinx.com:ip:axi_noc:1.0 axi_noc_0 ]
  set_property -dict [ list \
   CONFIG.CH0_DDR4_0_BOARD_INTERFACE {ddr4_dimm1} \
   CONFIG.CONTROLLERTYPE {DDR4_SDRAM} \
   CONFIG.HBM_MEMORY_FREQ0 {900} \
   CONFIG.HBM_MEMORY_FREQ1 {900} \
   CONFIG.LOGO_FILE {data/noc_mc.png} \
   CONFIG.MC0_CONFIG_NUM {config17} \
   CONFIG.MC1_CONFIG_NUM {config17} \
   CONFIG.MC2_CONFIG_NUM {config17} \
   CONFIG.MC3_CONFIG_NUM {config17} \
   CONFIG.MC_BOARD_INTRF_EN {true} \
   CONFIG.MC_CASLATENCY {22} \
   CONFIG.MC_CHAN_REGION1 {DDR_LOW1} \
   CONFIG.MC_COMPONENT_WIDTH {x8} \
   CONFIG.MC_CONFIG_NUM {config17} \
   CONFIG.MC_DATAWIDTH {64} \
   CONFIG.MC_DDR4_2T {Disable} \
   CONFIG.MC_EN_INTR_RESP {TRUE} \
   CONFIG.MC_F1_TRCD {13750} \
   CONFIG.MC_F1_TRCDMIN {13750} \
   CONFIG.MC_INPUTCLK0_PERIOD {5000} \
   CONFIG.MC_INPUT_FREQUENCY0 {200.000} \
   CONFIG.MC_INTERLEAVE_SIZE {128} \
   CONFIG.MC_MEMORY_DEVICETYPE {UDIMMs} \
   CONFIG.MC_MEMORY_SPEEDGRADE {DDR4-3200AA(22-22-22)} \
   CONFIG.MC_NETLIST_SIMULATION {true} \
   CONFIG.MC_NO_CHANNELS {Single} \
   CONFIG.MC_RANK {1} \
   CONFIG.MC_READ_BANDWIDTH {6400.0} \
   CONFIG.MC_ROWADDRESSWIDTH {16} \
   CONFIG.MC_STACKHEIGHT {1} \
   CONFIG.MC_SYSTEM_CLOCK {Differential} \
   CONFIG.MC_TRC {45750} \
   CONFIG.MC_TRCD {13750} \
   CONFIG.MC_TRCDMIN {13750} \
   CONFIG.MC_TRCMIN {45750} \
   CONFIG.MC_TRP {13750} \
   CONFIG.MC_TRPMIN {13750} \
   CONFIG.MC_WRITE_BANDWIDTH {6400.0} \
   CONFIG.MC_XPLL_CLKOUT1_PHASE {238.176} \
   CONFIG.NUM_CLKS {8} \
   CONFIG.NUM_MC {1} \
   CONFIG.NUM_MCP {4} \
   CONFIG.NUM_MI {2} \
   CONFIG.NUM_SI {7} \
   CONFIG.sys_clk0_BOARD_INTERFACE {ddr4_dimm1_sma_clk} \
 ] $axi_noc_0

  set_property -dict [ list \
   CONFIG.DATA_WIDTH {32} \
   CONFIG.APERTURES {{0x201_0000_0000 1G}} \
   CONFIG.CATEGORY {pl} \
 ] [get_bd_intf_pins /axi_noc_0/M00_AXI]

  set_property -dict [ list \
   CONFIG.DATA_WIDTH {32} \
   CONFIG.APERTURES {{0x201_8000_0000 1G}} \
   CONFIG.CATEGORY {pl} \
 ] [get_bd_intf_pins /axi_noc_0/M01_AXI]

  set_property -dict [ list \
   CONFIG.DATA_WIDTH {512} \
   CONFIG.CONNECTIONS {MC_0 { read_bw {1720} write_bw {1720} read_avg_burst {4} write_avg_burst {4}} } \
   CONFIG.DEST_IDS {M00_AXI:0x40} \
   CONFIG.CATEGORY {pl} \
 ] [get_bd_intf_pins /axi_noc_0/S00_AXI]

  set_property -dict [ list \
   CONFIG.DATA_WIDTH {128} \
   CONFIG.REGION {0} \
   CONFIG.CONNECTIONS {MC_0 { read_bw {100} write_bw {100} read_avg_burst {4} write_avg_burst {4}} M01_AXI { read_bw {1720} write_bw {1720} read_avg_burst {4} write_avg_burst {4}} } \
   CONFIG.DEST_IDS {M01_AXI:0x80} \
   CONFIG.CATEGORY {ps_cci} \
 ] [get_bd_intf_pins /axi_noc_0/S01_AXI]

  set_property -dict [ list \
   CONFIG.DATA_WIDTH {128} \
   CONFIG.REGION {0} \
   CONFIG.CONNECTIONS {MC_1 {read_bw {100} write_bw {100} read_avg_burst {4} write_avg_burst {4}}} \
   CONFIG.CATEGORY {ps_cci} \
 ] [get_bd_intf_pins /axi_noc_0/S02_AXI]

  set_property -dict [ list \
   CONFIG.DATA_WIDTH {128} \
   CONFIG.REGION {0} \
   CONFIG.CONNECTIONS {MC_2 {read_bw {100} write_bw {100} read_avg_burst {4} write_avg_burst {4}}} \
   CONFIG.CATEGORY {ps_cci} \
 ] [get_bd_intf_pins /axi_noc_0/S03_AXI]

  set_property -dict [ list \
   CONFIG.DATA_WIDTH {128} \
   CONFIG.REGION {0} \
   CONFIG.CONNECTIONS {MC_3 {read_bw {100} write_bw {100} read_avg_burst {4} write_avg_burst {4}}} \
   CONFIG.CATEGORY {ps_cci} \
 ] [get_bd_intf_pins /axi_noc_0/S04_AXI]

  set_property -dict [ list \
   CONFIG.DATA_WIDTH {128} \
   CONFIG.REGION {0} \
   CONFIG.CONNECTIONS {MC_0 {read_bw {100} write_bw {100} read_avg_burst {4} write_avg_burst {4}}} \
   CONFIG.CATEGORY {ps_rpu} \
 ] [get_bd_intf_pins /axi_noc_0/S05_AXI]

  set_property -dict [ list \
   CONFIG.DATA_WIDTH {128} \
   CONFIG.REGION {0} \
   CONFIG.CONNECTIONS {MC_0 { read_bw {100} write_bw {100} read_avg_burst {4} write_avg_burst {4}} M01_AXI { read_bw {1720} write_bw {1720} read_avg_burst {4} write_avg_burst {4}} M00_AXI { read_bw {1720} write_bw {1720} read_avg_burst {4} write_avg_burst {4}} } \
   CONFIG.DEST_IDS {M01_AXI:0x80:M00_AXI:0x0} \
   CONFIG.CATEGORY {ps_pmc} \
 ] [get_bd_intf_pins /axi_noc_0/S06_AXI]

  set_property -dict [ list \
   CONFIG.ASSOCIATED_BUSIF {S01_AXI} \
 ] [get_bd_pins /axi_noc_0/aclk0]

  set_property -dict [ list \
   CONFIG.ASSOCIATED_BUSIF {S02_AXI} \
 ] [get_bd_pins /axi_noc_0/aclk1]

  set_property -dict [ list \
   CONFIG.ASSOCIATED_BUSIF {S03_AXI} \
 ] [get_bd_pins /axi_noc_0/aclk2]

  set_property -dict [ list \
   CONFIG.ASSOCIATED_BUSIF {S04_AXI} \
 ] [get_bd_pins /axi_noc_0/aclk3]

  set_property -dict [ list \
   CONFIG.ASSOCIATED_BUSIF {S05_AXI} \
 ] [get_bd_pins /axi_noc_0/aclk4]

  set_property -dict [ list \
   CONFIG.ASSOCIATED_BUSIF {S06_AXI} \
 ] [get_bd_pins /axi_noc_0/aclk5]

  set_property -dict [ list \
   CONFIG.ASSOCIATED_BUSIF {M00_AXI:M01_AXI} \
 ] [get_bd_pins /axi_noc_0/aclk6]

  set_property -dict [ list \
   CONFIG.ASSOCIATED_BUSIF {S00_AXI} \
 ] [get_bd_pins /axi_noc_0/aclk7]

  # Create instance: clk_wizard_0, and set properties
  set clk_wizard_0 [ create_bd_cell -type ip -vlnv xilinx.com:ip:clk_wizard:1.0 clk_wizard_0 ]
  set_property -dict [ list \
   CONFIG.BANDWIDTH {OPTIMIZED} \
   CONFIG.CLKFBOUT_MULT {27.000000} \
   CONFIG.CLKOUT1_DIVIDE {24.000000} \
   CONFIG.CLKOUT2_DIVIDE {30.000000} \
   CONFIG.CLKOUT3_DIVIDE {15.000000} \
   CONFIG.CLKOUT4_DIVIDE {9.000000} \
   CONFIG.CLKOUT_DRIVES {BUFG,BUFG,BUFG,BUFG,BUFG,BUFG,BUFG} \
   CONFIG.CLKOUT_DYN_PS {None,None,None,None,None,None,None} \
   CONFIG.CLKOUT_GROUPING {Auto,Auto,Auto,Auto,Auto,Auto,Auto} \
   CONFIG.CLKOUT_MATCHED_ROUTING {false,false,false,false,false,false,false} \
   CONFIG.CLKOUT_PORT {clk_out1,clk_out2,clk_out3,clk_out4,clk_out5,clk_out6,clk_out7} \
   CONFIG.CLKOUT_REQUESTED_DUTY_CYCLE {50.000,50.000,50.000,50.000,50.000,50.000,50.000} \
   CONFIG.CLKOUT_REQUESTED_OUT_FREQUENCY {125.000,100.000,200.000,333.000,100.000,100.000,100.000} \
   CONFIG.CLKOUT_REQUESTED_PHASE {0.000,0.000,0.000,0.000,0.000,0.000,0.000} \
   CONFIG.CLKOUT_USED {true,true,true,true,false,false,false} \
   CONFIG.DIVCLK_DIVIDE {3} \
 ] $clk_wizard_0

  # Create instance: counters
  create_hier_cell_counters [current_bd_instance .] counters

  # Create instance: gty_quad_105
  create_hier_cell_gty_quad_105 [current_bd_instance .] gty_quad_105

  # Create instance: gty_quad_201
  create_hier_cell_gty_quad_201 [current_bd_instance .] gty_quad_201

  # Create instance: gty_quad_204
  create_hier_cell_gty_quad_204 [current_bd_instance .] gty_quad_204

  # Create instance: gty_quad_205
  create_hier_cell_gty_quad_205 [current_bd_instance .] gty_quad_205

  # Create instance: noc_tg_bc
  create_hier_cell_noc_tg_bc [current_bd_instance .] noc_tg_bc

  # Create instance: proc_sys_reset_0, and set properties
  set proc_sys_reset_0 [ create_bd_cell -type ip -vlnv xilinx.com:ip:proc_sys_reset:5.0 proc_sys_reset_0 ]

  # Create instance: versal_cips_0, and set properties
  set versal_cips_0 [ create_bd_cell -type ip -vlnv xilinx.com:ip:versal_cips:3.0 versal_cips_0 ]
  set_property -dict [ list \
   CONFIG.CLOCK_MODE {Custom} \
   CONFIG.CPM_CONFIG {AURORA_LINE_RATE_GPBS 10.0 BOOT_SECONDARY_PCIE_ENABLE 0 CPM_A0_REFCLK 0\
CPM_A1_REFCLK 0 CPM_AUX0_REF_CTRL_ACT_FREQMHZ 899.991028\
CPM_AUX0_REF_CTRL_DIVISOR0 2 CPM_AUX0_REF_CTRL_FREQMHZ 900\
CPM_AUX1_REF_CTRL_ACT_FREQMHZ 899.991028 CPM_AUX1_REF_CTRL_DIVISOR0 2\
CPM_AUX1_REF_CTRL_FREQMHZ 900 CPM_AXI_SLV_BRIDGE_BASE_ADDRR_H 0x00000006\
CPM_AXI_SLV_BRIDGE_BASE_ADDRR_L 0x00000000 CPM_AXI_SLV_MULTQ_BASE_ADDRR_H\
0x00000006 CPM_AXI_SLV_MULTQ_BASE_ADDRR_L 0x10000000\
CPM_AXI_SLV_XDMA_BASE_ADDRR_H 0x00000006 CPM_AXI_SLV_XDMA_BASE_ADDRR_L\
0x11000000 CPM_CCIX_IS_MM_ONLY 0 CPM_CCIX_PARTIAL_CACHELINE_SUPPORT 0\
CPM_CCIX_PORT_AGGREGATION_ENABLE 0 CPM_CCIX_RSVRD_MEMORY_AGENT_TYPE_0 HA0\
CPM_CCIX_RSVRD_MEMORY_AGENT_TYPE_1 HA0 CPM_CCIX_RSVRD_MEMORY_AGENT_TYPE_2 HA0\
CPM_CCIX_RSVRD_MEMORY_AGENT_TYPE_3 HA0 CPM_CCIX_RSVRD_MEMORY_AGENT_TYPE_4 HA0\
CPM_CCIX_RSVRD_MEMORY_AGENT_TYPE_5 HA0 CPM_CCIX_RSVRD_MEMORY_AGENT_TYPE_6 HA0\
CPM_CCIX_RSVRD_MEMORY_AGENT_TYPE_7 HA0 CPM_CCIX_RSVRD_MEMORY_ATTRIB_0\
Normal_Non_Cacheable_Memory CPM_CCIX_RSVRD_MEMORY_ATTRIB_1\
Normal_Non_Cacheable_Memory CPM_CCIX_RSVRD_MEMORY_ATTRIB_2\
Normal_Non_Cacheable_Memory CPM_CCIX_RSVRD_MEMORY_ATTRIB_3\
Normal_Non_Cacheable_Memory CPM_CCIX_RSVRD_MEMORY_ATTRIB_4\
Normal_Non_Cacheable_Memory CPM_CCIX_RSVRD_MEMORY_ATTRIB_5\
Normal_Non_Cacheable_Memory CPM_CCIX_RSVRD_MEMORY_ATTRIB_6\
Normal_Non_Cacheable_Memory CPM_CCIX_RSVRD_MEMORY_ATTRIB_7\
Normal_Non_Cacheable_Memory CPM_CCIX_RSVRD_MEMORY_BASEADDRESS_0 0x00000000\
CPM_CCIX_RSVRD_MEMORY_BASEADDRESS_1 0x00000000\
CPM_CCIX_RSVRD_MEMORY_BASEADDRESS_2 0x00000000\
CPM_CCIX_RSVRD_MEMORY_BASEADDRESS_3 0x00000000\
CPM_CCIX_RSVRD_MEMORY_BASEADDRESS_4 0x00000000\
CPM_CCIX_RSVRD_MEMORY_BASEADDRESS_5 0x00000000\
CPM_CCIX_RSVRD_MEMORY_BASEADDRESS_6 0x00000000\
CPM_CCIX_RSVRD_MEMORY_BASEADDRESS_7 0x00000000 CPM_CCIX_RSVRD_MEMORY_REGION_0 0\
CPM_CCIX_RSVRD_MEMORY_REGION_1 0 CPM_CCIX_RSVRD_MEMORY_REGION_2 0\
CPM_CCIX_RSVRD_MEMORY_REGION_3 0 CPM_CCIX_RSVRD_MEMORY_REGION_4 0\
CPM_CCIX_RSVRD_MEMORY_REGION_5 0 CPM_CCIX_RSVRD_MEMORY_REGION_6 0\
CPM_CCIX_RSVRD_MEMORY_REGION_7 0 CPM_CCIX_RSVRD_MEMORY_SIZE_0 4GB\
CPM_CCIX_RSVRD_MEMORY_SIZE_1 4GB CPM_CCIX_RSVRD_MEMORY_SIZE_2 4GB\
CPM_CCIX_RSVRD_MEMORY_SIZE_3 4GB CPM_CCIX_RSVRD_MEMORY_SIZE_4 4GB\
CPM_CCIX_RSVRD_MEMORY_SIZE_5 4GB CPM_CCIX_RSVRD_MEMORY_SIZE_6 4GB\
CPM_CCIX_RSVRD_MEMORY_SIZE_7 4GB CPM_CCIX_RSVRD_MEMORY_TYPE_0\
Other_or_Non_Specified_Memory_Type CPM_CCIX_RSVRD_MEMORY_TYPE_1\
Other_or_Non_Specified_Memory_Type CPM_CCIX_RSVRD_MEMORY_TYPE_2\
Other_or_Non_Specified_Memory_Type CPM_CCIX_RSVRD_MEMORY_TYPE_3\
Other_or_Non_Specified_Memory_Type CPM_CCIX_RSVRD_MEMORY_TYPE_4\
Other_or_Non_Specified_Memory_Type CPM_CCIX_RSVRD_MEMORY_TYPE_5\
Other_or_Non_Specified_Memory_Type CPM_CCIX_RSVRD_MEMORY_TYPE_6\
Other_or_Non_Specified_Memory_Type CPM_CCIX_RSVRD_MEMORY_TYPE_7\
Other_or_Non_Specified_Memory_Type CPM_CCIX_SELECT_AGENT None CPM_CDO_EN 0\
CPM_CLRERR_LANE_MARGIN 0 CPM_CORE_REF_CTRL_ACT_FREQMHZ 899.991028\
CPM_CORE_REF_CTRL_DIVISOR0 2 CPM_CORE_REF_CTRL_FREQMHZ 900 CPM_CPLL_CTRL_FBDIV\
108 CPM_CPLL_CTRL_SRCSEL REF_CLK CPM_DBG_REF_CTRL_ACT_FREQMHZ 299.997009\
CPM_DBG_REF_CTRL_DIVISOR0 6 CPM_DBG_REF_CTRL_FREQMHZ 300 CPM_DESIGN_USE_MODE 0\
CPM_DMA_CREDIT_INIT_DEMUX 1 CPM_DMA_IS_MM_ONLY 0 CPM_LSBUS_REF_CTRL_ACT_FREQMHZ\
149.998505 CPM_LSBUS_REF_CTRL_DIVISOR0 12 CPM_LSBUS_REF_CTRL_FREQMHZ 150\
CPM_NUM_CCIX_CREDIT_LINKS 0 CPM_NUM_HNF_AGENTS 0 CPM_NUM_HOME_OR_SLAVE_AGENTS 0\
CPM_NUM_REQ_AGENTS 0 CPM_NUM_SLAVE_AGENTS 0 CPM_PCIE0_AER_CAP_ENABLED 1\
CPM_PCIE0_ARI_CAP_ENABLED 1 CPM_PCIE0_ASYNC_MODE SRNS CPM_PCIE0_ATS_PRI_CAP_ON\
0 CPM_PCIE0_AXIBAR_NUM 1 CPM_PCIE0_AXISTEN_IF_CC_ALIGNMENT_MODE DWORD_Aligned\
CPM_PCIE0_AXISTEN_IF_COMPL_TIMEOUT_REG0 BEBC20\
CPM_PCIE0_AXISTEN_IF_COMPL_TIMEOUT_REG1 2FAF080\
CPM_PCIE0_AXISTEN_IF_CQ_ALIGNMENT_MODE DWORD_Aligned\
CPM_PCIE0_AXISTEN_IF_ENABLE_256_TAGS 0 CPM_PCIE0_AXISTEN_IF_ENABLE_CLIENT_TAG 0\
CPM_PCIE0_AXISTEN_IF_ENABLE_INTERNAL_MSIX_TABLE 0\
CPM_PCIE0_AXISTEN_IF_ENABLE_MESSAGE_RID_CHECK 1\
CPM_PCIE0_AXISTEN_IF_ENABLE_MSG_ROUTE 0\
CPM_PCIE0_AXISTEN_IF_ENABLE_RX_MSG_INTFC 0\
CPM_PCIE0_AXISTEN_IF_ENABLE_RX_TAG_SCALING 0\
CPM_PCIE0_AXISTEN_IF_ENABLE_TX_TAG_SCALING 0\
CPM_PCIE0_AXISTEN_IF_EXTEND_CPL_TIMEOUT 16ms_to_1s CPM_PCIE0_AXISTEN_IF_EXT_512\
0 CPM_PCIE0_AXISTEN_IF_EXT_512_CC_STRADDLE 0\
CPM_PCIE0_AXISTEN_IF_EXT_512_CQ_STRADDLE 0\
CPM_PCIE0_AXISTEN_IF_EXT_512_RC_4TLP_STRADDLE 1\
CPM_PCIE0_AXISTEN_IF_EXT_512_RC_STRADDLE 1\
CPM_PCIE0_AXISTEN_IF_EXT_512_RQ_STRADDLE 1\
CPM_PCIE0_AXISTEN_IF_RC_ALIGNMENT_MODE DWORD_Aligned\
CPM_PCIE0_AXISTEN_IF_RC_STRADDLE 0 CPM_PCIE0_AXISTEN_IF_RQ_ALIGNMENT_MODE\
DWORD_Aligned CPM_PCIE0_AXISTEN_IF_RX_PARITY_EN 1\
CPM_PCIE0_AXISTEN_IF_SIM_SHORT_CPL_TIMEOUT 0 CPM_PCIE0_AXISTEN_IF_TX_PARITY_EN\
0 CPM_PCIE0_AXISTEN_IF_WIDTH 64 CPM_PCIE0_AXISTEN_MSIX_VECTORS_PER_FUNCTION 8\
CPM_PCIE0_AXISTEN_USER_SPARE 0 CPM_PCIE0_BRIDGE_AXI_SLAVE_IF 0\
CPM_PCIE0_CCIX_EN 0 CPM_PCIE0_CCIX_OPT_TLP_GEN_AND_RECEPT_EN_CONTROL_INTERNAL 0\
CPM_PCIE0_CCIX_VENDOR_ID 0 CPM_PCIE0_CFG_CTL_IF 0 CPM_PCIE0_CFG_EXT_IF 0\
CPM_PCIE0_CFG_FC_IF 0 CPM_PCIE0_CFG_MGMT_IF 0 CPM_PCIE0_CFG_SPEC_4_0 0\
CPM_PCIE0_CFG_STS_IF 0 CPM_PCIE0_CFG_VEND_ID 10EE CPM_PCIE0_CONTROLLER_ENABLE 0\
CPM_PCIE0_COPY_PF0_ENABLED 0 CPM_PCIE0_COPY_PF0_QDMA_ENABLED 1\
CPM_PCIE0_COPY_PF0_SRIOV_QDMA_ENABLED 1 CPM_PCIE0_COPY_SRIOV_PF0_ENABLED 1\
CPM_PCIE0_COPY_XDMA_PF0_ENABLED 0 CPM_PCIE0_CORE_CLK_FREQ 500\
CPM_PCIE0_CORE_EDR_CLK_FREQ 625 CPM_PCIE0_DMA_DATA_WIDTH 256bits\
CPM_PCIE0_DMA_ENABLE_SECURE 0 CPM_PCIE0_DMA_INTF AXI4 CPM_PCIE0_DMA_MASK\
256bits CPM_PCIE0_DMA_METERING_ENABLE 1 CPM_PCIE0_DMA_MSI_RX_PIN_ENABLED FALSE\
CPM_PCIE0_DMA_ROOT_PORT 0 CPM_PCIE0_DSC_BYPASS_RD 0 CPM_PCIE0_DSC_BYPASS_WR 0\
CPM_PCIE0_EDR_IF 0 CPM_PCIE0_EDR_LINK_SPEED None CPM_PCIE0_EN_PARITY 0\
CPM_PCIE0_EXT_PCIE_CFG_SPACE_ENABLED None CPM_PCIE0_FUNCTIONAL_MODE None\
CPM_PCIE0_LANE_REVERSAL_EN 1 CPM_PCIE0_LEGACY_EXT_PCIE_CFG_SPACE_ENABLED 0\
CPM_PCIE0_LINK_DEBUG_AXIST_EN 0 CPM_PCIE0_LINK_DEBUG_EN 0\
CPM_PCIE0_LINK_SPEED0_FOR_POWER GEN1 CPM_PCIE0_LINK_WIDTH0_FOR_POWER 0\
CPM_PCIE0_MAILBOX_ENABLE 0 CPM_PCIE0_MAX_LINK_SPEED 2.5_GT/s\
CPM_PCIE0_MCAP_CAP_NEXTPTR 0 CPM_PCIE0_MCAP_ENABLE 0 CPM_PCIE0_MESG_RSVD_IF 0\
CPM_PCIE0_MESG_TRANSMIT_IF 0 CPM_PCIE0_MODE0_FOR_POWER NONE CPM_PCIE0_MODES\
None CPM_PCIE0_MODE_SELECTION Basic CPM_PCIE0_MSIX_RP_ENABLED 1\
CPM_PCIE0_MSI_X_OPTIONS None CPM_PCIE0_NUM_USR_IRQ 1 CPM_PCIE0_PASID_IF 0\
CPM_PCIE0_PF0_AER_CAP_ECRC_GEN_AND_CHECK_CAPABLE 0\
CPM_PCIE0_PF0_AER_CAP_NEXTPTR 0 CPM_PCIE0_PF0_ARI_CAP_NEXTPTR 0\
CPM_PCIE0_PF0_ARI_CAP_NEXT_FUNC 0 CPM_PCIE0_PF0_ARI_CAP_VER 1\
CPM_PCIE0_PF0_ATS_CAP_NEXTPTR 0 CPM_PCIE0_PF0_ATS_CAP_ON 0\
CPM_PCIE0_PF0_AXIBAR2PCIE_BASEADDR_0 0x0000000000000000\
CPM_PCIE0_PF0_AXIBAR2PCIE_BASEADDR_1 0x0000000000000000\
CPM_PCIE0_PF0_AXIBAR2PCIE_BASEADDR_2 0x0000000000000000\
CPM_PCIE0_PF0_AXIBAR2PCIE_BASEADDR_3 0x0000000000000000\
CPM_PCIE0_PF0_AXIBAR2PCIE_BASEADDR_4 0x0000000000000000\
CPM_PCIE0_PF0_AXIBAR2PCIE_BASEADDR_5 0x0000000000000000\
CPM_PCIE0_PF0_AXIBAR2PCIE_BRIDGE_0 0x0000000000000000\
CPM_PCIE0_PF0_AXIBAR2PCIE_BRIDGE_1 0x0000000000000000\
CPM_PCIE0_PF0_AXIBAR2PCIE_BRIDGE_2 0x0000000000000000\
CPM_PCIE0_PF0_AXIBAR2PCIE_BRIDGE_3 0x0000000000000000\
CPM_PCIE0_PF0_AXIBAR2PCIE_BRIDGE_4 0x0000000000000000\
CPM_PCIE0_PF0_AXIBAR2PCIE_BRIDGE_5 0x0000000000000000\
CPM_PCIE0_PF0_AXIBAR2PCIE_HIGHADDR_0 0x0000000000000000\
CPM_PCIE0_PF0_AXIBAR2PCIE_HIGHADDR_1 0x0000000000000000\
CPM_PCIE0_PF0_AXIBAR2PCIE_HIGHADDR_2 0x0000000000000000\
CPM_PCIE0_PF0_AXIBAR2PCIE_HIGHADDR_3 0x0000000000000000\
CPM_PCIE0_PF0_AXIBAR2PCIE_HIGHADDR_4 0x0000000000000000\
CPM_PCIE0_PF0_AXIBAR2PCIE_HIGHADDR_5 0x0000000000000000\
CPM_PCIE0_PF0_AXILITE_MASTER_64BIT 0 CPM_PCIE0_PF0_AXILITE_MASTER_ENABLED 0\
CPM_PCIE0_PF0_AXILITE_MASTER_PREFETCHABLE 0 CPM_PCIE0_PF0_AXILITE_MASTER_SCALE\
Kilobytes CPM_PCIE0_PF0_AXILITE_MASTER_SIZE 128\
CPM_PCIE0_PF0_AXIST_BYPASS_64BIT 0 CPM_PCIE0_PF0_AXIST_BYPASS_ENABLED 0\
CPM_PCIE0_PF0_AXIST_BYPASS_PREFETCHABLE 0 CPM_PCIE0_PF0_AXIST_BYPASS_SCALE\
Kilobytes CPM_PCIE0_PF0_AXIST_BYPASS_SIZE 128 CPM_PCIE0_PF0_BAR0_64BIT 0\
CPM_PCIE0_PF0_BAR0_BRIDGE_64BIT 0 CPM_PCIE0_PF0_BAR0_BRIDGE_ENABLED 0\
CPM_PCIE0_PF0_BAR0_BRIDGE_PREFETCHABLE 0 CPM_PCIE0_PF0_BAR0_BRIDGE_SCALE Bytes\
CPM_PCIE0_PF0_BAR0_BRIDGE_SIZE 128 CPM_PCIE0_PF0_BAR0_BRIDGE_TYPE Memory\
CPM_PCIE0_PF0_BAR0_CONTROL 0 CPM_PCIE0_PF0_BAR0_ENABLED 1\
CPM_PCIE0_PF0_BAR0_PREFETCHABLE 0 CPM_PCIE0_PF0_BAR0_QDMA_64BIT 1\
CPM_PCIE0_PF0_BAR0_QDMA_AXCACHE 0 CPM_PCIE0_PF0_BAR0_QDMA_CONTROL 0\
CPM_PCIE0_PF0_BAR0_QDMA_ENABLED 1 CPM_PCIE0_PF0_BAR0_QDMA_PREFETCHABLE 1\
CPM_PCIE0_PF0_BAR0_QDMA_SCALE Kilobytes CPM_PCIE0_PF0_BAR0_QDMA_SIZE 256\
CPM_PCIE0_PF0_BAR0_QDMA_TYPE DMA CPM_PCIE0_PF0_BAR0_SCALE Kilobytes\
CPM_PCIE0_PF0_BAR0_SIZE 128 CPM_PCIE0_PF0_BAR0_SRIOV_QDMA_64BIT 1\
CPM_PCIE0_PF0_BAR0_SRIOV_QDMA_CONTROL 0 CPM_PCIE0_PF0_BAR0_SRIOV_QDMA_ENABLED 1\
CPM_PCIE0_PF0_BAR0_SRIOV_QDMA_PREFETCHABLE 1\
CPM_PCIE0_PF0_BAR0_SRIOV_QDMA_SCALE Kilobytes\
CPM_PCIE0_PF0_BAR0_SRIOV_QDMA_SIZE 16 CPM_PCIE0_PF0_BAR0_SRIOV_QDMA_TYPE DMA\
CPM_PCIE0_PF0_BAR0_TYPE Memory CPM_PCIE0_PF0_BAR0_XDMA_64BIT 1\
CPM_PCIE0_PF0_BAR0_XDMA_AXCACHE 0 CPM_PCIE0_PF0_BAR0_XDMA_CONTROL 0\
CPM_PCIE0_PF0_BAR0_XDMA_ENABLED 1 CPM_PCIE0_PF0_BAR0_XDMA_PREFETCHABLE 1\
CPM_PCIE0_PF0_BAR0_XDMA_SCALE Kilobytes CPM_PCIE0_PF0_BAR0_XDMA_SIZE 64\
CPM_PCIE0_PF0_BAR0_XDMA_TYPE DMA CPM_PCIE0_PF0_BAR1_64BIT 0\
CPM_PCIE0_PF0_BAR1_BRIDGE_ENABLED 0 CPM_PCIE0_PF0_BAR1_BRIDGE_SCALE Bytes\
CPM_PCIE0_PF0_BAR1_BRIDGE_SIZE 128 CPM_PCIE0_PF0_BAR1_BRIDGE_TYPE Memory\
CPM_PCIE0_PF0_BAR1_CONTROL 0 CPM_PCIE0_PF0_BAR1_ENABLED 0\
CPM_PCIE0_PF0_BAR1_PREFETCHABLE 0 CPM_PCIE0_PF0_BAR1_QDMA_64BIT 0\
CPM_PCIE0_PF0_BAR1_QDMA_AXCACHE 0 CPM_PCIE0_PF0_BAR1_QDMA_CONTROL 0\
CPM_PCIE0_PF0_BAR1_QDMA_ENABLED 0 CPM_PCIE0_PF0_BAR1_QDMA_PREFETCHABLE 0\
CPM_PCIE0_PF0_BAR1_QDMA_SCALE Bytes CPM_PCIE0_PF0_BAR1_QDMA_SIZE 128\
CPM_PCIE0_PF0_BAR1_QDMA_TYPE AXI_Bridge_Master CPM_PCIE0_PF0_BAR1_SCALE Bytes\
CPM_PCIE0_PF0_BAR1_SIZE 128 CPM_PCIE0_PF0_BAR1_SRIOV_QDMA_64BIT 0\
CPM_PCIE0_PF0_BAR1_SRIOV_QDMA_CONTROL 0 CPM_PCIE0_PF0_BAR1_SRIOV_QDMA_ENABLED 0\
CPM_PCIE0_PF0_BAR1_SRIOV_QDMA_PREFETCHABLE 0\
CPM_PCIE0_PF0_BAR1_SRIOV_QDMA_SCALE Bytes CPM_PCIE0_PF0_BAR1_SRIOV_QDMA_SIZE 1\
CPM_PCIE0_PF0_BAR1_SRIOV_QDMA_TYPE AXI_Bridge_Master CPM_PCIE0_PF0_BAR1_TYPE\
Memory CPM_PCIE0_PF0_BAR1_XDMA_64BIT 0 CPM_PCIE0_PF0_BAR1_XDMA_AXCACHE 0\
CPM_PCIE0_PF0_BAR1_XDMA_CONTROL 0 CPM_PCIE0_PF0_BAR1_XDMA_ENABLED 0\
CPM_PCIE0_PF0_BAR1_XDMA_PREFETCHABLE 0 CPM_PCIE0_PF0_BAR1_XDMA_SCALE Bytes\
CPM_PCIE0_PF0_BAR1_XDMA_SIZE 128 CPM_PCIE0_PF0_BAR1_XDMA_TYPE AXI_Bridge_Master\
CPM_PCIE0_PF0_BAR2_64BIT 0 CPM_PCIE0_PF0_BAR2_BRIDGE_64BIT 0\
CPM_PCIE0_PF0_BAR2_BRIDGE_ENABLED 0 CPM_PCIE0_PF0_BAR2_BRIDGE_PREFETCHABLE 0\
CPM_PCIE0_PF0_BAR2_BRIDGE_SCALE Bytes CPM_PCIE0_PF0_BAR2_BRIDGE_SIZE 128\
CPM_PCIE0_PF0_BAR2_BRIDGE_TYPE Memory CPM_PCIE0_PF0_BAR2_CONTROL 0\
CPM_PCIE0_PF0_BAR2_ENABLED 0 CPM_PCIE0_PF0_BAR2_PREFETCHABLE 0\
CPM_PCIE0_PF0_BAR2_QDMA_64BIT 0 CPM_PCIE0_PF0_BAR2_QDMA_AXCACHE 0\
CPM_PCIE0_PF0_BAR2_QDMA_CONTROL 0 CPM_PCIE0_PF0_BAR2_QDMA_ENABLED 0\
CPM_PCIE0_PF0_BAR2_QDMA_PREFETCHABLE 0 CPM_PCIE0_PF0_BAR2_QDMA_SCALE Bytes\
CPM_PCIE0_PF0_BAR2_QDMA_SIZE 128 CPM_PCIE0_PF0_BAR2_QDMA_TYPE AXI_Bridge_Master\
CPM_PCIE0_PF0_BAR2_SCALE Bytes CPM_PCIE0_PF0_BAR2_SIZE 128\
CPM_PCIE0_PF0_BAR2_SRIOV_QDMA_64BIT 0 CPM_PCIE0_PF0_BAR2_SRIOV_QDMA_CONTROL 0\
CPM_PCIE0_PF0_BAR2_SRIOV_QDMA_ENABLED 0\
CPM_PCIE0_PF0_BAR2_SRIOV_QDMA_PREFETCHABLE 0\
CPM_PCIE0_PF0_BAR2_SRIOV_QDMA_SCALE Bytes CPM_PCIE0_PF0_BAR2_SRIOV_QDMA_SIZE 1\
CPM_PCIE0_PF0_BAR2_SRIOV_QDMA_TYPE AXI_Bridge_Master CPM_PCIE0_PF0_BAR2_TYPE\
Memory CPM_PCIE0_PF0_BAR2_XDMA_64BIT 0 CPM_PCIE0_PF0_BAR2_XDMA_AXCACHE 0\
CPM_PCIE0_PF0_BAR2_XDMA_CONTROL 0 CPM_PCIE0_PF0_BAR2_XDMA_ENABLED 0\
CPM_PCIE0_PF0_BAR2_XDMA_PREFETCHABLE 0 CPM_PCIE0_PF0_BAR2_XDMA_SCALE Bytes\
CPM_PCIE0_PF0_BAR2_XDMA_SIZE 128 CPM_PCIE0_PF0_BAR2_XDMA_TYPE AXI_Bridge_Master\
CPM_PCIE0_PF0_BAR3_64BIT 0 CPM_PCIE0_PF0_BAR3_BRIDGE_ENABLED 0\
CPM_PCIE0_PF0_BAR3_BRIDGE_SCALE Bytes CPM_PCIE0_PF0_BAR3_BRIDGE_SIZE 128\
CPM_PCIE0_PF0_BAR3_BRIDGE_TYPE Memory CPM_PCIE0_PF0_BAR3_CONTROL 0\
CPM_PCIE0_PF0_BAR3_ENABLED 0 CPM_PCIE0_PF0_BAR3_PREFETCHABLE 0\
CPM_PCIE0_PF0_BAR3_QDMA_64BIT 0 CPM_PCIE0_PF0_BAR3_QDMA_AXCACHE 0\
CPM_PCIE0_PF0_BAR3_QDMA_CONTROL 0 CPM_PCIE0_PF0_BAR3_QDMA_ENABLED 0\
CPM_PCIE0_PF0_BAR3_QDMA_PREFETCHABLE 0 CPM_PCIE0_PF0_BAR3_QDMA_SCALE Bytes\
CPM_PCIE0_PF0_BAR3_QDMA_SIZE 128 CPM_PCIE0_PF0_BAR3_QDMA_TYPE AXI_Bridge_Master\
CPM_PCIE0_PF0_BAR3_SCALE Bytes CPM_PCIE0_PF0_BAR3_SIZE 128\
CPM_PCIE0_PF0_BAR3_SRIOV_QDMA_64BIT 0 CPM_PCIE0_PF0_BAR3_SRIOV_QDMA_CONTROL 0\
CPM_PCIE0_PF0_BAR3_SRIOV_QDMA_ENABLED 0\
CPM_PCIE0_PF0_BAR3_SRIOV_QDMA_PREFETCHABLE 0\
CPM_PCIE0_PF0_BAR3_SRIOV_QDMA_SCALE Bytes CPM_PCIE0_PF0_BAR3_SRIOV_QDMA_SIZE 1\
CPM_PCIE0_PF0_BAR3_SRIOV_QDMA_TYPE AXI_Bridge_Master CPM_PCIE0_PF0_BAR3_TYPE\
Memory CPM_PCIE0_PF0_BAR3_XDMA_64BIT 0 CPM_PCIE0_PF0_BAR3_XDMA_AXCACHE 0\
CPM_PCIE0_PF0_BAR3_XDMA_CONTROL 0 CPM_PCIE0_PF0_BAR3_XDMA_ENABLED 0\
CPM_PCIE0_PF0_BAR3_XDMA_PREFETCHABLE 0 CPM_PCIE0_PF0_BAR3_XDMA_SCALE Bytes\
CPM_PCIE0_PF0_BAR3_XDMA_SIZE 128 CPM_PCIE0_PF0_BAR3_XDMA_TYPE AXI_Bridge_Master\
CPM_PCIE0_PF0_BAR4_64BIT 0 CPM_PCIE0_PF0_BAR4_BRIDGE_64BIT 0\
CPM_PCIE0_PF0_BAR4_BRIDGE_ENABLED 0 CPM_PCIE0_PF0_BAR4_BRIDGE_PREFETCHABLE 0\
CPM_PCIE0_PF0_BAR4_BRIDGE_SCALE Bytes CPM_PCIE0_PF0_BAR4_BRIDGE_SIZE 128\
CPM_PCIE0_PF0_BAR4_BRIDGE_TYPE Memory CPM_PCIE0_PF0_BAR4_CONTROL 0\
CPM_PCIE0_PF0_BAR4_ENABLED 0 CPM_PCIE0_PF0_BAR4_PREFETCHABLE 0\
CPM_PCIE0_PF0_BAR4_QDMA_64BIT 0 CPM_PCIE0_PF0_BAR4_QDMA_AXCACHE 0\
CPM_PCIE0_PF0_BAR4_QDMA_CONTROL 0 CPM_PCIE0_PF0_BAR4_QDMA_ENABLED 0\
CPM_PCIE0_PF0_BAR4_QDMA_PREFETCHABLE 0 CPM_PCIE0_PF0_BAR4_QDMA_SCALE Bytes\
CPM_PCIE0_PF0_BAR4_QDMA_SIZE 128 CPM_PCIE0_PF0_BAR4_QDMA_TYPE AXI_Bridge_Master\
CPM_PCIE0_PF0_BAR4_SCALE Bytes CPM_PCIE0_PF0_BAR4_SIZE 128\
CPM_PCIE0_PF0_BAR4_SRIOV_QDMA_64BIT 0 CPM_PCIE0_PF0_BAR4_SRIOV_QDMA_CONTROL 0\
CPM_PCIE0_PF0_BAR4_SRIOV_QDMA_ENABLED 0\
CPM_PCIE0_PF0_BAR4_SRIOV_QDMA_PREFETCHABLE 0\
CPM_PCIE0_PF0_BAR4_SRIOV_QDMA_SCALE Bytes CPM_PCIE0_PF0_BAR4_SRIOV_QDMA_SIZE 1\
CPM_PCIE0_PF0_BAR4_SRIOV_QDMA_TYPE AXI_Bridge_Master CPM_PCIE0_PF0_BAR4_TYPE\
Memory CPM_PCIE0_PF0_BAR4_XDMA_64BIT 0 CPM_PCIE0_PF0_BAR4_XDMA_AXCACHE 0\
CPM_PCIE0_PF0_BAR4_XDMA_CONTROL 0 CPM_PCIE0_PF0_BAR4_XDMA_ENABLED 0\
CPM_PCIE0_PF0_BAR4_XDMA_PREFETCHABLE 0 CPM_PCIE0_PF0_BAR4_XDMA_SCALE Bytes\
CPM_PCIE0_PF0_BAR4_XDMA_SIZE 128 CPM_PCIE0_PF0_BAR4_XDMA_TYPE AXI_Bridge_Master\
CPM_PCIE0_PF0_BAR5_64BIT 0 CPM_PCIE0_PF0_BAR5_BRIDGE_ENABLED 0\
CPM_PCIE0_PF0_BAR5_BRIDGE_SCALE Bytes CPM_PCIE0_PF0_BAR5_BRIDGE_SIZE 128\
CPM_PCIE0_PF0_BAR5_BRIDGE_TYPE Memory CPM_PCIE0_PF0_BAR5_CONTROL 0\
CPM_PCIE0_PF0_BAR5_ENABLED 0 CPM_PCIE0_PF0_BAR5_PREFETCHABLE 0\
CPM_PCIE0_PF0_BAR5_QDMA_64BIT 0 CPM_PCIE0_PF0_BAR5_QDMA_AXCACHE 0\
CPM_PCIE0_PF0_BAR5_QDMA_CONTROL 0 CPM_PCIE0_PF0_BAR5_QDMA_ENABLED 0\
CPM_PCIE0_PF0_BAR5_QDMA_PREFETCHABLE 0 CPM_PCIE0_PF0_BAR5_QDMA_SCALE Bytes\
CPM_PCIE0_PF0_BAR5_QDMA_SIZE 128 CPM_PCIE0_PF0_BAR5_QDMA_TYPE AXI_Bridge_Master\
CPM_PCIE0_PF0_BAR5_SCALE Bytes CPM_PCIE0_PF0_BAR5_SIZE 128\
CPM_PCIE0_PF0_BAR5_SRIOV_QDMA_64BIT 0 CPM_PCIE0_PF0_BAR5_SRIOV_QDMA_CONTROL 0\
CPM_PCIE0_PF0_BAR5_SRIOV_QDMA_ENABLED 0\
CPM_PCIE0_PF0_BAR5_SRIOV_QDMA_PREFETCHABLE 0\
CPM_PCIE0_PF0_BAR5_SRIOV_QDMA_SCALE Bytes CPM_PCIE0_PF0_BAR5_SRIOV_QDMA_SIZE 1\
CPM_PCIE0_PF0_BAR5_SRIOV_QDMA_TYPE AXI_Bridge_Master CPM_PCIE0_PF0_BAR5_TYPE\
Memory CPM_PCIE0_PF0_BAR5_XDMA_64BIT 0 CPM_PCIE0_PF0_BAR5_XDMA_AXCACHE 0\
CPM_PCIE0_PF0_BAR5_XDMA_CONTROL 0 CPM_PCIE0_PF0_BAR5_XDMA_ENABLED 0\
CPM_PCIE0_PF0_BAR5_XDMA_PREFETCHABLE 0 CPM_PCIE0_PF0_BAR5_XDMA_SCALE Bytes\
CPM_PCIE0_PF0_BAR5_XDMA_SIZE 128 CPM_PCIE0_PF0_BAR5_XDMA_TYPE AXI_Bridge_Master\
CPM_PCIE0_PF0_BASE_CLASS_MENU Memory_controller CPM_PCIE0_PF0_BASE_CLASS_VALUE\
05 CPM_PCIE0_PF0_CAPABILITY_POINTER 80 CPM_PCIE0_PF0_CAP_NEXTPTR 0\
CPM_PCIE0_PF0_CFG_DEV_ID B03F CPM_PCIE0_PF0_CFG_REV_ID 0\
CPM_PCIE0_PF0_CFG_SUBSYS_ID 7 CPM_PCIE0_PF0_CFG_SUBSYS_VEND_ID 10EE\
CPM_PCIE0_PF0_CLASS_CODE 0 CPM_PCIE0_PF0_DEV_CAP_10B_TAG_EN 0\
CPM_PCIE0_PF0_DEV_CAP_ENDPOINT_L0S_LATENCY less_than_64ns\
CPM_PCIE0_PF0_DEV_CAP_ENDPOINT_L1S_LATENCY less_than_1us\
CPM_PCIE0_PF0_DEV_CAP_EXT_TAG_EN 0\
CPM_PCIE0_PF0_DEV_CAP_FUNCTION_LEVEL_RESET_CAPABLE 0\
CPM_PCIE0_PF0_DEV_CAP_MAX_PAYLOAD 1024_bytes CPM_PCIE0_PF0_DLL_FEATURE_CAP_ID 0\
CPM_PCIE0_PF0_DLL_FEATURE_CAP_NEXTPTR 0 CPM_PCIE0_PF0_DLL_FEATURE_CAP_ON 1\
CPM_PCIE0_PF0_DLL_FEATURE_CAP_VER 1 CPM_PCIE0_PF0_DSN_CAP_ENABLE 0\
CPM_PCIE0_PF0_DSN_CAP_NEXTPTR 10C CPM_PCIE0_PF0_EXPANSION_ROM_ENABLED 0\
CPM_PCIE0_PF0_EXPANSION_ROM_QDMA_ENABLED 0\
CPM_PCIE0_PF0_EXPANSION_ROM_QDMA_SCALE Kilobytes\
CPM_PCIE0_PF0_EXPANSION_ROM_QDMA_SIZE 2 CPM_PCIE0_PF0_EXPANSION_ROM_SCALE\
Kilobytes CPM_PCIE0_PF0_EXPANSION_ROM_SIZE 2 CPM_PCIE0_PF0_INTERFACE_VALUE 0\
CPM_PCIE0_PF0_INTERRUPT_PIN NONE CPM_PCIE0_PF0_LINK_CAP_ASPM_SUPPORT No_ASPM\
CPM_PCIE0_PF0_LINK_STATUS_SLOT_CLOCK_CONFIG 1 CPM_PCIE0_PF0_MARGINING_CAP_ID 0\
CPM_PCIE0_PF0_MARGINING_CAP_NEXTPTR 0 CPM_PCIE0_PF0_MARGINING_CAP_ON 0\
CPM_PCIE0_PF0_MARGINING_CAP_VER 1 CPM_PCIE0_PF0_MSIX_CAP_NEXTPTR 0\
CPM_PCIE0_PF0_MSIX_CAP_PBA_BIR BAR_0 CPM_PCIE0_PF0_MSIX_CAP_PBA_OFFSET 50\
CPM_PCIE0_PF0_MSIX_CAP_TABLE_BIR BAR_0 CPM_PCIE0_PF0_MSIX_CAP_TABLE_OFFSET 40\
CPM_PCIE0_PF0_MSIX_CAP_TABLE_SIZE 007 CPM_PCIE0_PF0_MSIX_ENABLED 1\
CPM_PCIE0_PF0_MSI_CAP_MULTIMSGCAP 1_vector CPM_PCIE0_PF0_MSI_CAP_NEXTPTR 0\
CPM_PCIE0_PF0_MSI_CAP_PERVECMASKCAP 0 CPM_PCIE0_PF0_MSI_ENABLED 1\
CPM_PCIE0_PF0_PASID_CAP_MAX_PASID_WIDTH 1 CPM_PCIE0_PF0_PASID_CAP_NEXTPTR 0\
CPM_PCIE0_PF0_PASID_CAP_ON 0 CPM_PCIE0_PF0_PCIEBAR2AXIBAR_AXIL_MASTER 0\
CPM_PCIE0_PF0_PCIEBAR2AXIBAR_AXIST_BYPASS 0\
CPM_PCIE0_PF0_PCIEBAR2AXIBAR_BRIDGE_0 0x0000000000000000\
CPM_PCIE0_PF0_PCIEBAR2AXIBAR_BRIDGE_1 0x0000000000000000\
CPM_PCIE0_PF0_PCIEBAR2AXIBAR_BRIDGE_2 0x0000000000000000\
CPM_PCIE0_PF0_PCIEBAR2AXIBAR_BRIDGE_3 0x0000000000000000\
CPM_PCIE0_PF0_PCIEBAR2AXIBAR_BRIDGE_4 0x0000000000000000\
CPM_PCIE0_PF0_PCIEBAR2AXIBAR_BRIDGE_5 0x0000000000000000\
CPM_PCIE0_PF0_PCIEBAR2AXIBAR_QDMA_0 0x0000000000000000\
CPM_PCIE0_PF0_PCIEBAR2AXIBAR_QDMA_1 0x0000000000000000\
CPM_PCIE0_PF0_PCIEBAR2AXIBAR_QDMA_2 0x0000000000000000\
CPM_PCIE0_PF0_PCIEBAR2AXIBAR_QDMA_3 0x0000000000000000\
CPM_PCIE0_PF0_PCIEBAR2AXIBAR_QDMA_4 0x0000000000000000\
CPM_PCIE0_PF0_PCIEBAR2AXIBAR_QDMA_5 0x0000000000000000\
CPM_PCIE0_PF0_PCIEBAR2AXIBAR_SRIOV_QDMA_0 0x0000000000000000\
CPM_PCIE0_PF0_PCIEBAR2AXIBAR_SRIOV_QDMA_1 0x0000000000000000\
CPM_PCIE0_PF0_PCIEBAR2AXIBAR_SRIOV_QDMA_2 0x0000000000000000\
CPM_PCIE0_PF0_PCIEBAR2AXIBAR_SRIOV_QDMA_3 0x0000000000000000\
CPM_PCIE0_PF0_PCIEBAR2AXIBAR_SRIOV_QDMA_4 0x0000000000000000\
CPM_PCIE0_PF0_PCIEBAR2AXIBAR_SRIOV_QDMA_5 0x0000000000000000\
CPM_PCIE0_PF0_PCIEBAR2AXIBAR_XDMA_0 0 CPM_PCIE0_PF0_PCIEBAR2AXIBAR_XDMA_1 0\
CPM_PCIE0_PF0_PCIEBAR2AXIBAR_XDMA_2 0 CPM_PCIE0_PF0_PCIEBAR2AXIBAR_XDMA_3 0\
CPM_PCIE0_PF0_PCIEBAR2AXIBAR_XDMA_4 0 CPM_PCIE0_PF0_PCIEBAR2AXIBAR_XDMA_5 0\
CPM_PCIE0_PF0_PL16_CAP_ID 0 CPM_PCIE0_PF0_PL16_CAP_NEXTPTR 0\
CPM_PCIE0_PF0_PL16_CAP_ON 0 CPM_PCIE0_PF0_PL16_CAP_VER 1\
CPM_PCIE0_PF0_PM_CAP_ID 0 CPM_PCIE0_PF0_PM_CAP_NEXTPTR 0\
CPM_PCIE0_PF0_PM_CAP_PMESUPPORT_D0 1 CPM_PCIE0_PF0_PM_CAP_PMESUPPORT_D1 1\
CPM_PCIE0_PF0_PM_CAP_PMESUPPORT_D3COLD 1 CPM_PCIE0_PF0_PM_CAP_PMESUPPORT_D3HOT\
1 CPM_PCIE0_PF0_PM_CAP_SUPP_D1_STATE 1 CPM_PCIE0_PF0_PM_CAP_VER_ID 3\
CPM_PCIE0_PF0_PM_CSR_NOSOFTRESET 1 CPM_PCIE0_PF0_PRI_CAP_NEXTPTR 0\
CPM_PCIE0_PF0_PRI_CAP_ON 0 CPM_PCIE0_PF0_SECONDARY_PCIE_CAP_NEXTPTR 0\
CPM_PCIE0_PF0_SRIOV_ARI_CAPBL_HIER_PRESERVED 0 CPM_PCIE0_PF0_SRIOV_BAR0_64BIT 0\
CPM_PCIE0_PF0_SRIOV_BAR0_CONTROL Disabled CPM_PCIE0_PF0_SRIOV_BAR0_ENABLED 1\
CPM_PCIE0_PF0_SRIOV_BAR0_PREFETCHABLE 0 CPM_PCIE0_PF0_SRIOV_BAR0_SCALE\
Kilobytes CPM_PCIE0_PF0_SRIOV_BAR0_SIZE 4 CPM_PCIE0_PF0_SRIOV_BAR0_TYPE Memory\
CPM_PCIE0_PF0_SRIOV_BAR1_64BIT 0 CPM_PCIE0_PF0_SRIOV_BAR1_CONTROL Disabled\
CPM_PCIE0_PF0_SRIOV_BAR1_ENABLED 0 CPM_PCIE0_PF0_SRIOV_BAR1_PREFETCHABLE 0\
CPM_PCIE0_PF0_SRIOV_BAR1_SCALE Bytes CPM_PCIE0_PF0_SRIOV_BAR1_SIZE 128\
CPM_PCIE0_PF0_SRIOV_BAR1_TYPE Memory CPM_PCIE0_PF0_SRIOV_BAR2_64BIT 0\
CPM_PCIE0_PF0_SRIOV_BAR2_CONTROL Disabled CPM_PCIE0_PF0_SRIOV_BAR2_ENABLED 0\
CPM_PCIE0_PF0_SRIOV_BAR2_PREFETCHABLE 0 CPM_PCIE0_PF0_SRIOV_BAR2_SCALE Bytes\
CPM_PCIE0_PF0_SRIOV_BAR2_SIZE 128 CPM_PCIE0_PF0_SRIOV_BAR2_TYPE Memory\
CPM_PCIE0_PF0_SRIOV_BAR3_64BIT 0 CPM_PCIE0_PF0_SRIOV_BAR3_CONTROL Disabled\
CPM_PCIE0_PF0_SRIOV_BAR3_ENABLED 0 CPM_PCIE0_PF0_SRIOV_BAR3_PREFETCHABLE 0\
CPM_PCIE0_PF0_SRIOV_BAR3_SCALE Bytes CPM_PCIE0_PF0_SRIOV_BAR3_SIZE 128\
CPM_PCIE0_PF0_SRIOV_BAR3_TYPE Memory CPM_PCIE0_PF0_SRIOV_BAR4_64BIT 0\
CPM_PCIE0_PF0_SRIOV_BAR4_CONTROL Disabled CPM_PCIE0_PF0_SRIOV_BAR4_ENABLED 0\
CPM_PCIE0_PF0_SRIOV_BAR4_PREFETCHABLE 0 CPM_PCIE0_PF0_SRIOV_BAR4_SCALE Bytes\
CPM_PCIE0_PF0_SRIOV_BAR4_SIZE 128 CPM_PCIE0_PF0_SRIOV_BAR4_TYPE Memory\
CPM_PCIE0_PF0_SRIOV_BAR5_64BIT 0 CPM_PCIE0_PF0_SRIOV_BAR5_CONTROL Disabled\
CPM_PCIE0_PF0_SRIOV_BAR5_ENABLED 0 CPM_PCIE0_PF0_SRIOV_BAR5_PREFETCHABLE 0\
CPM_PCIE0_PF0_SRIOV_BAR5_SCALE Bytes CPM_PCIE0_PF0_SRIOV_BAR5_SIZE 128\
CPM_PCIE0_PF0_SRIOV_BAR5_TYPE Memory CPM_PCIE0_PF0_SRIOV_CAP_ENABLE 0\
CPM_PCIE0_PF0_SRIOV_CAP_INITIAL_VF 4 CPM_PCIE0_PF0_SRIOV_CAP_NEXTPTR 0\
CPM_PCIE0_PF0_SRIOV_CAP_TOTAL_VF 0 CPM_PCIE0_PF0_SRIOV_CAP_VER 1\
CPM_PCIE0_PF0_SRIOV_FIRST_VF_OFFSET 4 CPM_PCIE0_PF0_SRIOV_FUNC_DEP_LINK 0\
CPM_PCIE0_PF0_SRIOV_SUPPORTED_PAGE_SIZE 553 CPM_PCIE0_PF0_SRIOV_VF_DEVICE_ID\
C03F CPM_PCIE0_PF0_SUB_CLASS_INTF_MENU Other_memory_controller\
CPM_PCIE0_PF0_SUB_CLASS_VALUE 80 CPM_PCIE0_PF0_TPHR_CAP_DEV_SPECIFIC_MODE 1\
CPM_PCIE0_PF0_TPHR_CAP_ENABLE 0 CPM_PCIE0_PF0_TPHR_CAP_INT_VEC_MODE 1\
CPM_PCIE0_PF0_TPHR_CAP_NEXTPTR 0 CPM_PCIE0_PF0_TPHR_CAP_ST_TABLE_LOC\
ST_Table_not_present CPM_PCIE0_PF0_TPHR_CAP_ST_TABLE_SIZE 16\
CPM_PCIE0_PF0_TPHR_CAP_VER 1 CPM_PCIE0_PF0_TPHR_ENABLE 0\
CPM_PCIE0_PF0_USE_CLASS_CODE_LOOKUP_ASSISTANT 1 CPM_PCIE0_PF0_VC_ARB_CAPABILITY\
0 CPM_PCIE0_PF0_VC_ARB_TBL_OFFSET 0 CPM_PCIE0_PF0_VC_CAP_ENABLED 0\
CPM_PCIE0_PF0_VC_CAP_NEXTPTR 0 CPM_PCIE0_PF0_VC_CAP_VER 1\
CPM_PCIE0_PF0_VC_EXTENDED_COUNT 0 CPM_PCIE0_PF0_VC_LOW_PRIORITY_EXTENDED_COUNT\
0 CPM_PCIE0_PF0_XDMA_64BIT 0 CPM_PCIE0_PF0_XDMA_ENABLED 0\
CPM_PCIE0_PF0_XDMA_PREFETCHABLE 0 CPM_PCIE0_PF0_XDMA_SCALE Kilobytes\
CPM_PCIE0_PF0_XDMA_SIZE 128 CPM_PCIE0_PF1_AER_CAP_NEXTPTR 0\
CPM_PCIE0_PF1_ARI_CAP_NEXTPTR 0 CPM_PCIE0_PF1_ARI_CAP_NEXT_FUNC 0\
CPM_PCIE0_PF1_ATS_CAP_NEXTPTR 0 CPM_PCIE0_PF1_ATS_CAP_ON 0\
CPM_PCIE0_PF1_AXILITE_MASTER_64BIT 0 CPM_PCIE0_PF1_AXILITE_MASTER_ENABLED 0\
CPM_PCIE0_PF1_AXILITE_MASTER_PREFETCHABLE 0 CPM_PCIE0_PF1_AXILITE_MASTER_SCALE\
Kilobytes CPM_PCIE0_PF1_AXILITE_MASTER_SIZE 128\
CPM_PCIE0_PF1_AXIST_BYPASS_64BIT 0 CPM_PCIE0_PF1_AXIST_BYPASS_ENABLED 0\
CPM_PCIE0_PF1_AXIST_BYPASS_PREFETCHABLE 0 CPM_PCIE0_PF1_AXIST_BYPASS_SCALE\
Kilobytes CPM_PCIE0_PF1_AXIST_BYPASS_SIZE 128 CPM_PCIE0_PF1_BAR0_64BIT 0\
CPM_PCIE0_PF1_BAR0_CONTROL 0 CPM_PCIE0_PF1_BAR0_ENABLED 1\
CPM_PCIE0_PF1_BAR0_PREFETCHABLE 0 CPM_PCIE0_PF1_BAR0_QDMA_64BIT 1\
CPM_PCIE0_PF1_BAR0_QDMA_AXCACHE 0 CPM_PCIE0_PF1_BAR0_QDMA_CONTROL 0\
CPM_PCIE0_PF1_BAR0_QDMA_ENABLED 1 CPM_PCIE0_PF1_BAR0_QDMA_PREFETCHABLE 1\
CPM_PCIE0_PF1_BAR0_QDMA_SCALE Kilobytes CPM_PCIE0_PF1_BAR0_QDMA_SIZE 256\
CPM_PCIE0_PF1_BAR0_QDMA_TYPE DMA CPM_PCIE0_PF1_BAR0_SCALE Kilobytes\
CPM_PCIE0_PF1_BAR0_SIZE 128 CPM_PCIE0_PF1_BAR0_SRIOV_QDMA_64BIT 0\
CPM_PCIE0_PF1_BAR0_SRIOV_QDMA_CONTROL 0 CPM_PCIE0_PF1_BAR0_SRIOV_QDMA_ENABLED 1\
CPM_PCIE0_PF1_BAR0_SRIOV_QDMA_PREFETCHABLE 0\
CPM_PCIE0_PF1_BAR0_SRIOV_QDMA_SCALE Kilobytes\
CPM_PCIE0_PF1_BAR0_SRIOV_QDMA_SIZE 128 CPM_PCIE0_PF1_BAR0_SRIOV_QDMA_TYPE DMA\
CPM_PCIE0_PF1_BAR0_TYPE Memory CPM_PCIE0_PF1_BAR0_XDMA_64BIT 0\
CPM_PCIE0_PF1_BAR0_XDMA_AXCACHE 0 CPM_PCIE0_PF1_BAR0_XDMA_CONTROL 0\
CPM_PCIE0_PF1_BAR0_XDMA_ENABLED 0 CPM_PCIE0_PF1_BAR0_XDMA_PREFETCHABLE 0\
CPM_PCIE0_PF1_BAR0_XDMA_SCALE Bytes CPM_PCIE0_PF1_BAR0_XDMA_SIZE 128\
CPM_PCIE0_PF1_BAR0_XDMA_TYPE AXI_Bridge_Master CPM_PCIE0_PF1_BAR1_64BIT 0\
CPM_PCIE0_PF1_BAR1_CONTROL 0 CPM_PCIE0_PF1_BAR1_ENABLED 0\
CPM_PCIE0_PF1_BAR1_PREFETCHABLE 0 CPM_PCIE0_PF1_BAR1_QDMA_64BIT 0\
CPM_PCIE0_PF1_BAR1_QDMA_AXCACHE 0 CPM_PCIE0_PF1_BAR1_QDMA_CONTROL 0\
CPM_PCIE0_PF1_BAR1_QDMA_ENABLED 0 CPM_PCIE0_PF1_BAR1_QDMA_PREFETCHABLE 0\
CPM_PCIE0_PF1_BAR1_QDMA_SCALE Bytes CPM_PCIE0_PF1_BAR1_QDMA_SIZE 128\
CPM_PCIE0_PF1_BAR1_QDMA_TYPE AXI_Bridge_Master CPM_PCIE0_PF1_BAR1_SCALE Bytes\
CPM_PCIE0_PF1_BAR1_SIZE 128 CPM_PCIE0_PF1_BAR1_SRIOV_QDMA_64BIT 0\
CPM_PCIE0_PF1_BAR1_SRIOV_QDMA_CONTROL 0 CPM_PCIE0_PF1_BAR1_SRIOV_QDMA_ENABLED 0\
CPM_PCIE0_PF1_BAR1_SRIOV_QDMA_PREFETCHABLE 0\
CPM_PCIE0_PF1_BAR1_SRIOV_QDMA_SCALE Bytes CPM_PCIE0_PF1_BAR1_SRIOV_QDMA_SIZE 1\
CPM_PCIE0_PF1_BAR1_SRIOV_QDMA_TYPE AXI_Bridge_Master CPM_PCIE0_PF1_BAR1_TYPE\
Memory CPM_PCIE0_PF1_BAR1_XDMA_64BIT 0 CPM_PCIE0_PF1_BAR1_XDMA_AXCACHE 0\
CPM_PCIE0_PF1_BAR1_XDMA_CONTROL 0 CPM_PCIE0_PF1_BAR1_XDMA_ENABLED 0\
CPM_PCIE0_PF1_BAR1_XDMA_PREFETCHABLE 0 CPM_PCIE0_PF1_BAR1_XDMA_SCALE Bytes\
CPM_PCIE0_PF1_BAR1_XDMA_SIZE 128 CPM_PCIE0_PF1_BAR1_XDMA_TYPE AXI_Bridge_Master\
CPM_PCIE0_PF1_BAR2_64BIT 0 CPM_PCIE0_PF1_BAR2_CONTROL 0\
CPM_PCIE0_PF1_BAR2_ENABLED 0 CPM_PCIE0_PF1_BAR2_PREFETCHABLE 0\
CPM_PCIE0_PF1_BAR2_QDMA_64BIT 0 CPM_PCIE0_PF1_BAR2_QDMA_AXCACHE 0\
CPM_PCIE0_PF1_BAR2_QDMA_CONTROL 0 CPM_PCIE0_PF1_BAR2_QDMA_ENABLED 0\
CPM_PCIE0_PF1_BAR2_QDMA_PREFETCHABLE 0 CPM_PCIE0_PF1_BAR2_QDMA_SCALE Bytes\
CPM_PCIE0_PF1_BAR2_QDMA_SIZE 128 CPM_PCIE0_PF1_BAR2_QDMA_TYPE AXI_Bridge_Master\
CPM_PCIE0_PF1_BAR2_SCALE Bytes CPM_PCIE0_PF1_BAR2_SIZE 128\
CPM_PCIE0_PF1_BAR2_SRIOV_QDMA_64BIT 0 CPM_PCIE0_PF1_BAR2_SRIOV_QDMA_CONTROL 0\
CPM_PCIE0_PF1_BAR2_SRIOV_QDMA_ENABLED 0\
CPM_PCIE0_PF1_BAR2_SRIOV_QDMA_PREFETCHABLE 0\
CPM_PCIE0_PF1_BAR2_SRIOV_QDMA_SCALE Bytes CPM_PCIE0_PF1_BAR2_SRIOV_QDMA_SIZE 1\
CPM_PCIE0_PF1_BAR2_SRIOV_QDMA_TYPE AXI_Bridge_Master CPM_PCIE0_PF1_BAR2_TYPE\
Memory CPM_PCIE0_PF1_BAR2_XDMA_64BIT 0 CPM_PCIE0_PF1_BAR2_XDMA_AXCACHE 0\
CPM_PCIE0_PF1_BAR2_XDMA_CONTROL 0 CPM_PCIE0_PF1_BAR2_XDMA_ENABLED 0\
CPM_PCIE0_PF1_BAR2_XDMA_PREFETCHABLE 0 CPM_PCIE0_PF1_BAR2_XDMA_SCALE Bytes\
CPM_PCIE0_PF1_BAR2_XDMA_SIZE 128 CPM_PCIE0_PF1_BAR2_XDMA_TYPE AXI_Bridge_Master\
CPM_PCIE0_PF1_BAR3_64BIT 0 CPM_PCIE0_PF1_BAR3_CONTROL 0\
CPM_PCIE0_PF1_BAR3_ENABLED 0 CPM_PCIE0_PF1_BAR3_PREFETCHABLE 0\
CPM_PCIE0_PF1_BAR3_QDMA_64BIT 0 CPM_PCIE0_PF1_BAR3_QDMA_AXCACHE 0\
CPM_PCIE0_PF1_BAR3_QDMA_CONTROL 0 CPM_PCIE0_PF1_BAR3_QDMA_ENABLED 0\
CPM_PCIE0_PF1_BAR3_QDMA_PREFETCHABLE 0 CPM_PCIE0_PF1_BAR3_QDMA_SCALE Bytes\
CPM_PCIE0_PF1_BAR3_QDMA_SIZE 128 CPM_PCIE0_PF1_BAR3_QDMA_TYPE AXI_Bridge_Master\
CPM_PCIE0_PF1_BAR3_SCALE Bytes CPM_PCIE0_PF1_BAR3_SIZE 128\
CPM_PCIE0_PF1_BAR3_SRIOV_QDMA_64BIT 0 CPM_PCIE0_PF1_BAR3_SRIOV_QDMA_CONTROL 0\
CPM_PCIE0_PF1_BAR3_SRIOV_QDMA_ENABLED 0\
CPM_PCIE0_PF1_BAR3_SRIOV_QDMA_PREFETCHABLE 0\
CPM_PCIE0_PF1_BAR3_SRIOV_QDMA_SCALE Bytes CPM_PCIE0_PF1_BAR3_SRIOV_QDMA_SIZE 1\
CPM_PCIE0_PF1_BAR3_SRIOV_QDMA_TYPE AXI_Bridge_Master CPM_PCIE0_PF1_BAR3_TYPE\
Memory CPM_PCIE0_PF1_BAR3_XDMA_64BIT 0 CPM_PCIE0_PF1_BAR3_XDMA_AXCACHE 0\
CPM_PCIE0_PF1_BAR3_XDMA_CONTROL 0 CPM_PCIE0_PF1_BAR3_XDMA_ENABLED 0\
CPM_PCIE0_PF1_BAR3_XDMA_PREFETCHABLE 0 CPM_PCIE0_PF1_BAR3_XDMA_SCALE Bytes\
CPM_PCIE0_PF1_BAR3_XDMA_SIZE 128 CPM_PCIE0_PF1_BAR3_XDMA_TYPE AXI_Bridge_Master\
CPM_PCIE0_PF1_BAR4_64BIT 0 CPM_PCIE0_PF1_BAR4_CONTROL 0\
CPM_PCIE0_PF1_BAR4_ENABLED 0 CPM_PCIE0_PF1_BAR4_PREFETCHABLE 0\
CPM_PCIE0_PF1_BAR4_QDMA_64BIT 0 CPM_PCIE0_PF1_BAR4_QDMA_AXCACHE 0\
CPM_PCIE0_PF1_BAR4_QDMA_CONTROL 0 CPM_PCIE0_PF1_BAR4_QDMA_ENABLED 0\
CPM_PCIE0_PF1_BAR4_QDMA_PREFETCHABLE 0 CPM_PCIE0_PF1_BAR4_QDMA_SCALE Bytes\
CPM_PCIE0_PF1_BAR4_QDMA_SIZE 128 CPM_PCIE0_PF1_BAR4_QDMA_TYPE AXI_Bridge_Master\
CPM_PCIE0_PF1_BAR4_SCALE Bytes CPM_PCIE0_PF1_BAR4_SIZE 128\
CPM_PCIE0_PF1_BAR4_SRIOV_QDMA_64BIT 0 CPM_PCIE0_PF1_BAR4_SRIOV_QDMA_CONTROL 0\
CPM_PCIE0_PF1_BAR4_SRIOV_QDMA_ENABLED 0\
CPM_PCIE0_PF1_BAR4_SRIOV_QDMA_PREFETCHABLE 0\
CPM_PCIE0_PF1_BAR4_SRIOV_QDMA_SCALE Bytes CPM_PCIE0_PF1_BAR4_SRIOV_QDMA_SIZE 1\
CPM_PCIE0_PF1_BAR4_SRIOV_QDMA_TYPE AXI_Bridge_Master CPM_PCIE0_PF1_BAR4_TYPE\
Memory CPM_PCIE0_PF1_BAR4_XDMA_64BIT 0 CPM_PCIE0_PF1_BAR4_XDMA_AXCACHE 0\
CPM_PCIE0_PF1_BAR4_XDMA_CONTROL 0 CPM_PCIE0_PF1_BAR4_XDMA_ENABLED 0\
CPM_PCIE0_PF1_BAR4_XDMA_PREFETCHABLE 0 CPM_PCIE0_PF1_BAR4_XDMA_SCALE Bytes\
CPM_PCIE0_PF1_BAR4_XDMA_SIZE 128 CPM_PCIE0_PF1_BAR4_XDMA_TYPE AXI_Bridge_Master\
CPM_PCIE0_PF1_BAR5_64BIT 0 CPM_PCIE0_PF1_BAR5_CONTROL 0\
CPM_PCIE0_PF1_BAR5_ENABLED 0 CPM_PCIE0_PF1_BAR5_PREFETCHABLE 0\
CPM_PCIE0_PF1_BAR5_QDMA_64BIT 0 CPM_PCIE0_PF1_BAR5_QDMA_AXCACHE 0\
CPM_PCIE0_PF1_BAR5_QDMA_CONTROL 0 CPM_PCIE0_PF1_BAR5_QDMA_ENABLED 0\
CPM_PCIE0_PF1_BAR5_QDMA_PREFETCHABLE 0 CPM_PCIE0_PF1_BAR5_QDMA_SCALE Bytes\
CPM_PCIE0_PF1_BAR5_QDMA_SIZE 128 CPM_PCIE0_PF1_BAR5_QDMA_TYPE AXI_Bridge_Master\
CPM_PCIE0_PF1_BAR5_SCALE Bytes CPM_PCIE0_PF1_BAR5_SIZE 128\
CPM_PCIE0_PF1_BAR5_SRIOV_QDMA_64BIT 0 CPM_PCIE0_PF1_BAR5_SRIOV_QDMA_CONTROL 0\
CPM_PCIE0_PF1_BAR5_SRIOV_QDMA_ENABLED 0\
CPM_PCIE0_PF1_BAR5_SRIOV_QDMA_PREFETCHABLE 0\
CPM_PCIE0_PF1_BAR5_SRIOV_QDMA_SCALE Bytes CPM_PCIE0_PF1_BAR5_SRIOV_QDMA_SIZE 1\
CPM_PCIE0_PF1_BAR5_SRIOV_QDMA_TYPE AXI_Bridge_Master CPM_PCIE0_PF1_BAR5_TYPE\
Memory CPM_PCIE0_PF1_BAR5_XDMA_64BIT 0 CPM_PCIE0_PF1_BAR5_XDMA_AXCACHE 0\
CPM_PCIE0_PF1_BAR5_XDMA_CONTROL 0 CPM_PCIE0_PF1_BAR5_XDMA_ENABLED 0\
CPM_PCIE0_PF1_BAR5_XDMA_PREFETCHABLE 0 CPM_PCIE0_PF1_BAR5_XDMA_SCALE Bytes\
CPM_PCIE0_PF1_BAR5_XDMA_SIZE 128 CPM_PCIE0_PF1_BAR5_XDMA_TYPE AXI_Bridge_Master\
CPM_PCIE0_PF1_BASE_CLASS_MENU Memory_controller CPM_PCIE0_PF1_BASE_CLASS_VALUE\
05 CPM_PCIE0_PF1_CAPABILITY_POINTER 80 CPM_PCIE0_PF1_CAP_NEXTPTR 0\
CPM_PCIE0_PF1_CFG_DEV_ID B13F CPM_PCIE0_PF1_CFG_REV_ID 0\
CPM_PCIE0_PF1_CFG_SUBSYS_ID 7 CPM_PCIE0_PF1_CFG_SUBSYS_VEND_ID 10EE\
CPM_PCIE0_PF1_CLASS_CODE 0x000 CPM_PCIE0_PF1_DLL_FEATURE_CAP_NEXTPTR 0\
CPM_PCIE0_PF1_DSN_CAP_ENABLE 0 CPM_PCIE0_PF1_DSN_CAP_NEXTPTR 10C\
CPM_PCIE0_PF1_EXPANSION_ROM_ENABLED 0 CPM_PCIE0_PF1_EXPANSION_ROM_QDMA_ENABLED\
0 CPM_PCIE0_PF1_EXPANSION_ROM_QDMA_SCALE Kilobytes\
CPM_PCIE0_PF1_EXPANSION_ROM_QDMA_SIZE 2 CPM_PCIE0_PF1_EXPANSION_ROM_SCALE\
Kilobytes CPM_PCIE0_PF1_EXPANSION_ROM_SIZE 2 CPM_PCIE0_PF1_INTERFACE_VALUE 00\
CPM_PCIE0_PF1_INTERRUPT_PIN NONE CPM_PCIE0_PF1_MSIX_CAP_NEXTPTR 0\
CPM_PCIE0_PF1_MSIX_CAP_PBA_BIR BAR_0 CPM_PCIE0_PF1_MSIX_CAP_PBA_OFFSET 50\
CPM_PCIE0_PF1_MSIX_CAP_TABLE_BIR BAR_0 CPM_PCIE0_PF1_MSIX_CAP_TABLE_OFFSET 40\
CPM_PCIE0_PF1_MSIX_CAP_TABLE_SIZE 007 CPM_PCIE0_PF1_MSIX_ENABLED 1\
CPM_PCIE0_PF1_MSI_CAP_MULTIMSGCAP 1_vector CPM_PCIE0_PF1_MSI_CAP_NEXTPTR 0\
CPM_PCIE0_PF1_MSI_CAP_PERVECMASKCAP 0 CPM_PCIE0_PF1_MSI_ENABLED 1\
CPM_PCIE0_PF1_PASID_CAP_NEXTPTR 0 CPM_PCIE0_PF1_PCIEBAR2AXIBAR_AXIL_MASTER 0\
CPM_PCIE0_PF1_PCIEBAR2AXIBAR_AXIST_BYPASS 0 CPM_PCIE0_PF1_PCIEBAR2AXIBAR_QDMA_0\
0x0000000000000000 CPM_PCIE0_PF1_PCIEBAR2AXIBAR_QDMA_1 0x0000000000000000\
CPM_PCIE0_PF1_PCIEBAR2AXIBAR_QDMA_2 0x0000000000000000\
CPM_PCIE0_PF1_PCIEBAR2AXIBAR_QDMA_3 0x0000000000000000\
CPM_PCIE0_PF1_PCIEBAR2AXIBAR_QDMA_4 0x0000000000000000\
CPM_PCIE0_PF1_PCIEBAR2AXIBAR_QDMA_5 0x0000000000000000\
CPM_PCIE0_PF1_PCIEBAR2AXIBAR_SRIOV_QDMA_0 0x0000000000000000\
CPM_PCIE0_PF1_PCIEBAR2AXIBAR_SRIOV_QDMA_1 0x0000000000000000\
CPM_PCIE0_PF1_PCIEBAR2AXIBAR_SRIOV_QDMA_2 0x0000000000000000\
CPM_PCIE0_PF1_PCIEBAR2AXIBAR_SRIOV_QDMA_3 0x0000000000000000\
CPM_PCIE0_PF1_PCIEBAR2AXIBAR_SRIOV_QDMA_4 0x0000000000000000\
CPM_PCIE0_PF1_PCIEBAR2AXIBAR_SRIOV_QDMA_5 0x0000000000000000\
CPM_PCIE0_PF1_PCIEBAR2AXIBAR_XDMA_0 0 CPM_PCIE0_PF1_PCIEBAR2AXIBAR_XDMA_1 0\
CPM_PCIE0_PF1_PCIEBAR2AXIBAR_XDMA_2 0 CPM_PCIE0_PF1_PCIEBAR2AXIBAR_XDMA_3 0\
CPM_PCIE0_PF1_PCIEBAR2AXIBAR_XDMA_4 0 CPM_PCIE0_PF1_PCIEBAR2AXIBAR_XDMA_5 0\
CPM_PCIE0_PF1_PM_CAP_NEXTPTR 0 CPM_PCIE0_PF1_PRI_CAP_NEXTPTR 0\
CPM_PCIE0_PF1_PRI_CAP_ON 0 CPM_PCIE0_PF1_SRIOV_ARI_CAPBL_HIER_PRESERVED 0\
CPM_PCIE0_PF1_SRIOV_BAR0_64BIT 0 CPM_PCIE0_PF1_SRIOV_BAR0_CONTROL Disabled\
CPM_PCIE0_PF1_SRIOV_BAR0_ENABLED 1 CPM_PCIE0_PF1_SRIOV_BAR0_PREFETCHABLE 0\
CPM_PCIE0_PF1_SRIOV_BAR0_SCALE Kilobytes CPM_PCIE0_PF1_SRIOV_BAR0_SIZE 4\
CPM_PCIE0_PF1_SRIOV_BAR0_TYPE Memory CPM_PCIE0_PF1_SRIOV_BAR1_64BIT 0\
CPM_PCIE0_PF1_SRIOV_BAR1_CONTROL Disabled CPM_PCIE0_PF1_SRIOV_BAR1_ENABLED 0\
CPM_PCIE0_PF1_SRIOV_BAR1_PREFETCHABLE 0 CPM_PCIE0_PF1_SRIOV_BAR1_SCALE Bytes\
CPM_PCIE0_PF1_SRIOV_BAR1_SIZE 128 CPM_PCIE0_PF1_SRIOV_BAR1_TYPE Memory\
CPM_PCIE0_PF1_SRIOV_BAR2_64BIT 0 CPM_PCIE0_PF1_SRIOV_BAR2_CONTROL Disabled\
CPM_PCIE0_PF1_SRIOV_BAR2_ENABLED 0 CPM_PCIE0_PF1_SRIOV_BAR2_PREFETCHABLE 0\
CPM_PCIE0_PF1_SRIOV_BAR2_SCALE Bytes CPM_PCIE0_PF1_SRIOV_BAR2_SIZE 128\
CPM_PCIE0_PF1_SRIOV_BAR2_TYPE Memory CPM_PCIE0_PF1_SRIOV_BAR3_64BIT 0\
CPM_PCIE0_PF1_SRIOV_BAR3_CONTROL Disabled CPM_PCIE0_PF1_SRIOV_BAR3_ENABLED 0\
CPM_PCIE0_PF1_SRIOV_BAR3_PREFETCHABLE 0 CPM_PCIE0_PF1_SRIOV_BAR3_SCALE Bytes\
CPM_PCIE0_PF1_SRIOV_BAR3_SIZE 128 CPM_PCIE0_PF1_SRIOV_BAR3_TYPE Memory\
CPM_PCIE0_PF1_SRIOV_BAR4_64BIT 0 CPM_PCIE0_PF1_SRIOV_BAR4_CONTROL Disabled\
CPM_PCIE0_PF1_SRIOV_BAR4_ENABLED 0 CPM_PCIE0_PF1_SRIOV_BAR4_PREFETCHABLE 0\
CPM_PCIE0_PF1_SRIOV_BAR4_SCALE Bytes CPM_PCIE0_PF1_SRIOV_BAR4_SIZE 128\
CPM_PCIE0_PF1_SRIOV_BAR4_TYPE Memory CPM_PCIE0_PF1_SRIOV_BAR5_64BIT 0\
CPM_PCIE0_PF1_SRIOV_BAR5_CONTROL Disabled CPM_PCIE0_PF1_SRIOV_BAR5_ENABLED 0\
CPM_PCIE0_PF1_SRIOV_BAR5_PREFETCHABLE 0 CPM_PCIE0_PF1_SRIOV_BAR5_SCALE Bytes\
CPM_PCIE0_PF1_SRIOV_BAR5_SIZE 128 CPM_PCIE0_PF1_SRIOV_BAR5_TYPE Memory\
CPM_PCIE0_PF1_SRIOV_CAP_ENABLE 0 CPM_PCIE0_PF1_SRIOV_CAP_INITIAL_VF 4\
CPM_PCIE0_PF1_SRIOV_CAP_NEXTPTR 0 CPM_PCIE0_PF1_SRIOV_CAP_TOTAL_VF 0\
CPM_PCIE0_PF1_SRIOV_CAP_VER 1 CPM_PCIE0_PF1_SRIOV_FIRST_VF_OFFSET 7\
CPM_PCIE0_PF1_SRIOV_FUNC_DEP_LINK 0 CPM_PCIE0_PF1_SRIOV_SUPPORTED_PAGE_SIZE 553\
CPM_PCIE0_PF1_SRIOV_VF_DEVICE_ID C13F CPM_PCIE0_PF1_SUB_CLASS_INTF_MENU\
Other_memory_controller CPM_PCIE0_PF1_SUB_CLASS_VALUE 80\
CPM_PCIE0_PF1_TPHR_CAP_NEXTPTR 0 CPM_PCIE0_PF1_USE_CLASS_CODE_LOOKUP_ASSISTANT\
1 CPM_PCIE0_PF1_VEND_ID 10EE CPM_PCIE0_PF1_XDMA_64BIT 0\
CPM_PCIE0_PF1_XDMA_ENABLED 0 CPM_PCIE0_PF1_XDMA_PREFETCHABLE 0\
CPM_PCIE0_PF1_XDMA_SCALE Kilobytes CPM_PCIE0_PF1_XDMA_SIZE 128\
CPM_PCIE0_PF2_AER_CAP_NEXTPTR 0 CPM_PCIE0_PF2_ARI_CAP_NEXTPTR 0\
CPM_PCIE0_PF2_ARI_CAP_NEXT_FUNC 0 CPM_PCIE0_PF2_ATS_CAP_NEXTPTR 0\
CPM_PCIE0_PF2_ATS_CAP_ON 0 CPM_PCIE0_PF2_AXILITE_MASTER_64BIT 0\
CPM_PCIE0_PF2_AXILITE_MASTER_ENABLED 0\
CPM_PCIE0_PF2_AXILITE_MASTER_PREFETCHABLE 0 CPM_PCIE0_PF2_AXILITE_MASTER_SCALE\
Kilobytes CPM_PCIE0_PF2_AXILITE_MASTER_SIZE 128\
CPM_PCIE0_PF2_AXIST_BYPASS_64BIT 0 CPM_PCIE0_PF2_AXIST_BYPASS_ENABLED 0\
CPM_PCIE0_PF2_AXIST_BYPASS_PREFETCHABLE 0 CPM_PCIE0_PF2_AXIST_BYPASS_SCALE\
Kilobytes CPM_PCIE0_PF2_AXIST_BYPASS_SIZE 128 CPM_PCIE0_PF2_BAR0_64BIT 0\
CPM_PCIE0_PF2_BAR0_CONTROL 0 CPM_PCIE0_PF2_BAR0_ENABLED 1\
CPM_PCIE0_PF2_BAR0_PREFETCHABLE 0 CPM_PCIE0_PF2_BAR0_QDMA_64BIT 1\
CPM_PCIE0_PF2_BAR0_QDMA_AXCACHE 0 CPM_PCIE0_PF2_BAR0_QDMA_CONTROL 0\
CPM_PCIE0_PF2_BAR0_QDMA_ENABLED 1 CPM_PCIE0_PF2_BAR0_QDMA_PREFETCHABLE 1\
CPM_PCIE0_PF2_BAR0_QDMA_SCALE Kilobytes CPM_PCIE0_PF2_BAR0_QDMA_SIZE 256\
CPM_PCIE0_PF2_BAR0_QDMA_TYPE DMA CPM_PCIE0_PF2_BAR0_SCALE Kilobytes\
CPM_PCIE0_PF2_BAR0_SIZE 128 CPM_PCIE0_PF2_BAR0_SRIOV_QDMA_64BIT 0\
CPM_PCIE0_PF2_BAR0_SRIOV_QDMA_CONTROL 0 CPM_PCIE0_PF2_BAR0_SRIOV_QDMA_ENABLED 1\
CPM_PCIE0_PF2_BAR0_SRIOV_QDMA_PREFETCHABLE 0\
CPM_PCIE0_PF2_BAR0_SRIOV_QDMA_SCALE Kilobytes\
CPM_PCIE0_PF2_BAR0_SRIOV_QDMA_SIZE 128 CPM_PCIE0_PF2_BAR0_SRIOV_QDMA_TYPE DMA\
CPM_PCIE0_PF2_BAR0_TYPE Memory CPM_PCIE0_PF2_BAR0_XDMA_64BIT 0\
CPM_PCIE0_PF2_BAR0_XDMA_AXCACHE 0 CPM_PCIE0_PF2_BAR0_XDMA_CONTROL 0\
CPM_PCIE0_PF2_BAR0_XDMA_ENABLED 0 CPM_PCIE0_PF2_BAR0_XDMA_PREFETCHABLE 0\
CPM_PCIE0_PF2_BAR0_XDMA_SCALE Bytes CPM_PCIE0_PF2_BAR0_XDMA_SIZE 128\
CPM_PCIE0_PF2_BAR0_XDMA_TYPE AXI_Bridge_Master CPM_PCIE0_PF2_BAR1_64BIT 0\
CPM_PCIE0_PF2_BAR1_CONTROL 0 CPM_PCIE0_PF2_BAR1_ENABLED 0\
CPM_PCIE0_PF2_BAR1_PREFETCHABLE 0 CPM_PCIE0_PF2_BAR1_QDMA_64BIT 0\
CPM_PCIE0_PF2_BAR1_QDMA_AXCACHE 0 CPM_PCIE0_PF2_BAR1_QDMA_CONTROL 0\
CPM_PCIE0_PF2_BAR1_QDMA_ENABLED 0 CPM_PCIE0_PF2_BAR1_QDMA_PREFETCHABLE 0\
CPM_PCIE0_PF2_BAR1_QDMA_SCALE Bytes CPM_PCIE0_PF2_BAR1_QDMA_SIZE 128\
CPM_PCIE0_PF2_BAR1_QDMA_TYPE AXI_Bridge_Master CPM_PCIE0_PF2_BAR1_SCALE Bytes\
CPM_PCIE0_PF2_BAR1_SIZE 128 CPM_PCIE0_PF2_BAR1_SRIOV_QDMA_64BIT 0\
CPM_PCIE0_PF2_BAR1_SRIOV_QDMA_CONTROL 0 CPM_PCIE0_PF2_BAR1_SRIOV_QDMA_ENABLED 0\
CPM_PCIE0_PF2_BAR1_SRIOV_QDMA_PREFETCHABLE 0\
CPM_PCIE0_PF2_BAR1_SRIOV_QDMA_SCALE Bytes CPM_PCIE0_PF2_BAR1_SRIOV_QDMA_SIZE 1\
CPM_PCIE0_PF2_BAR1_SRIOV_QDMA_TYPE AXI_Bridge_Master CPM_PCIE0_PF2_BAR1_TYPE\
Memory CPM_PCIE0_PF2_BAR1_XDMA_64BIT 0 CPM_PCIE0_PF2_BAR1_XDMA_AXCACHE 0\
CPM_PCIE0_PF2_BAR1_XDMA_CONTROL 0 CPM_PCIE0_PF2_BAR1_XDMA_ENABLED 0\
CPM_PCIE0_PF2_BAR1_XDMA_PREFETCHABLE 0 CPM_PCIE0_PF2_BAR1_XDMA_SCALE Bytes\
CPM_PCIE0_PF2_BAR1_XDMA_SIZE 128 CPM_PCIE0_PF2_BAR1_XDMA_TYPE AXI_Bridge_Master\
CPM_PCIE0_PF2_BAR2_64BIT 0 CPM_PCIE0_PF2_BAR2_CONTROL 0\
CPM_PCIE0_PF2_BAR2_ENABLED 0 CPM_PCIE0_PF2_BAR2_PREFETCHABLE 0\
CPM_PCIE0_PF2_BAR2_QDMA_64BIT 0 CPM_PCIE0_PF2_BAR2_QDMA_AXCACHE 0\
CPM_PCIE0_PF2_BAR2_QDMA_CONTROL 0 CPM_PCIE0_PF2_BAR2_QDMA_ENABLED 0\
CPM_PCIE0_PF2_BAR2_QDMA_PREFETCHABLE 0 CPM_PCIE0_PF2_BAR2_QDMA_SCALE Bytes\
CPM_PCIE0_PF2_BAR2_QDMA_SIZE 128 CPM_PCIE0_PF2_BAR2_QDMA_TYPE AXI_Bridge_Master\
CPM_PCIE0_PF2_BAR2_SCALE Bytes CPM_PCIE0_PF2_BAR2_SIZE 128\
CPM_PCIE0_PF2_BAR2_SRIOV_QDMA_64BIT 0 CPM_PCIE0_PF2_BAR2_SRIOV_QDMA_CONTROL 0\
CPM_PCIE0_PF2_BAR2_SRIOV_QDMA_ENABLED 0\
CPM_PCIE0_PF2_BAR2_SRIOV_QDMA_PREFETCHABLE 0\
CPM_PCIE0_PF2_BAR2_SRIOV_QDMA_SCALE Bytes CPM_PCIE0_PF2_BAR2_SRIOV_QDMA_SIZE 1\
CPM_PCIE0_PF2_BAR2_SRIOV_QDMA_TYPE AXI_Bridge_Master CPM_PCIE0_PF2_BAR2_TYPE\
Memory CPM_PCIE0_PF2_BAR2_XDMA_64BIT 0 CPM_PCIE0_PF2_BAR2_XDMA_AXCACHE 0\
CPM_PCIE0_PF2_BAR2_XDMA_CONTROL 0 CPM_PCIE0_PF2_BAR2_XDMA_ENABLED 0\
CPM_PCIE0_PF2_BAR2_XDMA_PREFETCHABLE 0 CPM_PCIE0_PF2_BAR2_XDMA_SCALE Bytes\
CPM_PCIE0_PF2_BAR2_XDMA_SIZE 128 CPM_PCIE0_PF2_BAR2_XDMA_TYPE AXI_Bridge_Master\
CPM_PCIE0_PF2_BAR3_64BIT 0 CPM_PCIE0_PF2_BAR3_CONTROL 0\
CPM_PCIE0_PF2_BAR3_ENABLED 0 CPM_PCIE0_PF2_BAR3_PREFETCHABLE 0\
CPM_PCIE0_PF2_BAR3_QDMA_64BIT 0 CPM_PCIE0_PF2_BAR3_QDMA_AXCACHE 0\
CPM_PCIE0_PF2_BAR3_QDMA_CONTROL 0 CPM_PCIE0_PF2_BAR3_QDMA_ENABLED 0\
CPM_PCIE0_PF2_BAR3_QDMA_PREFETCHABLE 0 CPM_PCIE0_PF2_BAR3_QDMA_SCALE Bytes\
CPM_PCIE0_PF2_BAR3_QDMA_SIZE 128 CPM_PCIE0_PF2_BAR3_QDMA_TYPE AXI_Bridge_Master\
CPM_PCIE0_PF2_BAR3_SCALE Bytes CPM_PCIE0_PF2_BAR3_SIZE 128\
CPM_PCIE0_PF2_BAR3_SRIOV_QDMA_64BIT 0 CPM_PCIE0_PF2_BAR3_SRIOV_QDMA_CONTROL 0\
CPM_PCIE0_PF2_BAR3_SRIOV_QDMA_ENABLED 0\
CPM_PCIE0_PF2_BAR3_SRIOV_QDMA_PREFETCHABLE 0\
CPM_PCIE0_PF2_BAR3_SRIOV_QDMA_SCALE Bytes CPM_PCIE0_PF2_BAR3_SRIOV_QDMA_SIZE 1\
CPM_PCIE0_PF2_BAR3_SRIOV_QDMA_TYPE AXI_Bridge_Master CPM_PCIE0_PF2_BAR3_TYPE\
Memory CPM_PCIE0_PF2_BAR3_XDMA_64BIT 0 CPM_PCIE0_PF2_BAR3_XDMA_AXCACHE 0\
CPM_PCIE0_PF2_BAR3_XDMA_CONTROL 0 CPM_PCIE0_PF2_BAR3_XDMA_ENABLED 0\
CPM_PCIE0_PF2_BAR3_XDMA_PREFETCHABLE 0 CPM_PCIE0_PF2_BAR3_XDMA_SCALE Bytes\
CPM_PCIE0_PF2_BAR3_XDMA_SIZE 128 CPM_PCIE0_PF2_BAR3_XDMA_TYPE AXI_Bridge_Master\
CPM_PCIE0_PF2_BAR4_64BIT 0 CPM_PCIE0_PF2_BAR4_CONTROL 0\
CPM_PCIE0_PF2_BAR4_ENABLED 0 CPM_PCIE0_PF2_BAR4_PREFETCHABLE 0\
CPM_PCIE0_PF2_BAR4_QDMA_64BIT 0 CPM_PCIE0_PF2_BAR4_QDMA_AXCACHE 0\
CPM_PCIE0_PF2_BAR4_QDMA_CONTROL 0 CPM_PCIE0_PF2_BAR4_QDMA_ENABLED 0\
CPM_PCIE0_PF2_BAR4_QDMA_PREFETCHABLE 0 CPM_PCIE0_PF2_BAR4_QDMA_SCALE Bytes\
CPM_PCIE0_PF2_BAR4_QDMA_SIZE 128 CPM_PCIE0_PF2_BAR4_QDMA_TYPE AXI_Bridge_Master\
CPM_PCIE0_PF2_BAR4_SCALE Bytes CPM_PCIE0_PF2_BAR4_SIZE 128\
CPM_PCIE0_PF2_BAR4_SRIOV_QDMA_64BIT 0 CPM_PCIE0_PF2_BAR4_SRIOV_QDMA_CONTROL 0\
CPM_PCIE0_PF2_BAR4_SRIOV_QDMA_ENABLED 0\
CPM_PCIE0_PF2_BAR4_SRIOV_QDMA_PREFETCHABLE 0\
CPM_PCIE0_PF2_BAR4_SRIOV_QDMA_SCALE Bytes CPM_PCIE0_PF2_BAR4_SRIOV_QDMA_SIZE 1\
CPM_PCIE0_PF2_BAR4_SRIOV_QDMA_TYPE AXI_Bridge_Master CPM_PCIE0_PF2_BAR4_TYPE\
Memory CPM_PCIE0_PF2_BAR4_XDMA_64BIT 0 CPM_PCIE0_PF2_BAR4_XDMA_AXCACHE 0\
CPM_PCIE0_PF2_BAR4_XDMA_CONTROL 0 CPM_PCIE0_PF2_BAR4_XDMA_ENABLED 0\
CPM_PCIE0_PF2_BAR4_XDMA_PREFETCHABLE 0 CPM_PCIE0_PF2_BAR4_XDMA_SCALE Bytes\
CPM_PCIE0_PF2_BAR4_XDMA_SIZE 128 CPM_PCIE0_PF2_BAR4_XDMA_TYPE AXI_Bridge_Master\
CPM_PCIE0_PF2_BAR5_64BIT 0 CPM_PCIE0_PF2_BAR5_CONTROL 0\
CPM_PCIE0_PF2_BAR5_ENABLED 0 CPM_PCIE0_PF2_BAR5_PREFETCHABLE 0\
CPM_PCIE0_PF2_BAR5_QDMA_64BIT 0 CPM_PCIE0_PF2_BAR5_QDMA_AXCACHE 0\
CPM_PCIE0_PF2_BAR5_QDMA_CONTROL 0 CPM_PCIE0_PF2_BAR5_QDMA_ENABLED 0\
CPM_PCIE0_PF2_BAR5_QDMA_PREFETCHABLE 0 CPM_PCIE0_PF2_BAR5_QDMA_SCALE Bytes\
CPM_PCIE0_PF2_BAR5_QDMA_SIZE 128 CPM_PCIE0_PF2_BAR5_QDMA_TYPE AXI_Bridge_Master\
CPM_PCIE0_PF2_BAR5_SCALE Bytes CPM_PCIE0_PF2_BAR5_SIZE 128\
CPM_PCIE0_PF2_BAR5_SRIOV_QDMA_64BIT 0 CPM_PCIE0_PF2_BAR5_SRIOV_QDMA_CONTROL 0\
CPM_PCIE0_PF2_BAR5_SRIOV_QDMA_ENABLED 0\
CPM_PCIE0_PF2_BAR5_SRIOV_QDMA_PREFETCHABLE 0\
CPM_PCIE0_PF2_BAR5_SRIOV_QDMA_SCALE Bytes CPM_PCIE0_PF2_BAR5_SRIOV_QDMA_SIZE 1\
CPM_PCIE0_PF2_BAR5_SRIOV_QDMA_TYPE AXI_Bridge_Master CPM_PCIE0_PF2_BAR5_TYPE\
Memory CPM_PCIE0_PF2_BAR5_XDMA_64BIT 0 CPM_PCIE0_PF2_BAR5_XDMA_AXCACHE 0\
CPM_PCIE0_PF2_BAR5_XDMA_CONTROL 0 CPM_PCIE0_PF2_BAR5_XDMA_ENABLED 0\
CPM_PCIE0_PF2_BAR5_XDMA_PREFETCHABLE 0 CPM_PCIE0_PF2_BAR5_XDMA_SCALE Bytes\
CPM_PCIE0_PF2_BAR5_XDMA_SIZE 128 CPM_PCIE0_PF2_BAR5_XDMA_TYPE AXI_Bridge_Master\
CPM_PCIE0_PF2_BASE_CLASS_MENU Memory_controller CPM_PCIE0_PF2_BASE_CLASS_VALUE\
05 CPM_PCIE0_PF2_CAPABILITY_POINTER 80 CPM_PCIE0_PF2_CAP_NEXTPTR 0\
CPM_PCIE0_PF2_CFG_DEV_ID B23F CPM_PCIE0_PF2_CFG_REV_ID 0\
CPM_PCIE0_PF2_CFG_SUBSYS_ID 7 CPM_PCIE0_PF2_CFG_SUBSYS_VEND_ID 10EE\
CPM_PCIE0_PF2_CLASS_CODE 0x000 CPM_PCIE0_PF2_DLL_FEATURE_CAP_NEXTPTR 0\
CPM_PCIE0_PF2_DSN_CAP_ENABLE 0 CPM_PCIE0_PF2_DSN_CAP_NEXTPTR 10C\
CPM_PCIE0_PF2_EXPANSION_ROM_ENABLED 0 CPM_PCIE0_PF2_EXPANSION_ROM_QDMA_ENABLED\
0 CPM_PCIE0_PF2_EXPANSION_ROM_QDMA_SCALE Kilobytes\
CPM_PCIE0_PF2_EXPANSION_ROM_QDMA_SIZE 2 CPM_PCIE0_PF2_EXPANSION_ROM_SCALE\
Kilobytes CPM_PCIE0_PF2_EXPANSION_ROM_SIZE 2 CPM_PCIE0_PF2_INTERFACE_VALUE 00\
CPM_PCIE0_PF2_INTERRUPT_PIN NONE CPM_PCIE0_PF2_MSIX_CAP_NEXTPTR 0\
CPM_PCIE0_PF2_MSIX_CAP_PBA_BIR BAR_0 CPM_PCIE0_PF2_MSIX_CAP_PBA_OFFSET 50\
CPM_PCIE0_PF2_MSIX_CAP_TABLE_BIR BAR_0 CPM_PCIE0_PF2_MSIX_CAP_TABLE_OFFSET 40\
CPM_PCIE0_PF2_MSIX_CAP_TABLE_SIZE 007 CPM_PCIE0_PF2_MSIX_ENABLED 1\
CPM_PCIE0_PF2_MSI_CAP_MULTIMSGCAP 1_vector CPM_PCIE0_PF2_MSI_CAP_NEXTPTR 0\
CPM_PCIE0_PF2_MSI_CAP_PERVECMASKCAP 0 CPM_PCIE0_PF2_MSI_ENABLED 1\
CPM_PCIE0_PF2_PASID_CAP_MAX_PASID_WIDTH 1 CPM_PCIE0_PF2_PASID_CAP_NEXTPTR 0\
CPM_PCIE0_PF2_PCIEBAR2AXIBAR_AXIL_MASTER 0\
CPM_PCIE0_PF2_PCIEBAR2AXIBAR_AXIST_BYPASS 0 CPM_PCIE0_PF2_PCIEBAR2AXIBAR_QDMA_0\
0x0000000000000000 CPM_PCIE0_PF2_PCIEBAR2AXIBAR_QDMA_1 0x0000000000000000\
CPM_PCIE0_PF2_PCIEBAR2AXIBAR_QDMA_2 0x0000000000000000\
CPM_PCIE0_PF2_PCIEBAR2AXIBAR_QDMA_3 0x0000000000000000\
CPM_PCIE0_PF2_PCIEBAR2AXIBAR_QDMA_4 0x0000000000000000\
CPM_PCIE0_PF2_PCIEBAR2AXIBAR_QDMA_5 0x0000000000000000\
CPM_PCIE0_PF2_PCIEBAR2AXIBAR_SRIOV_QDMA_0 0x0000000000000000\
CPM_PCIE0_PF2_PCIEBAR2AXIBAR_SRIOV_QDMA_1 0x0000000000000000\
CPM_PCIE0_PF2_PCIEBAR2AXIBAR_SRIOV_QDMA_2 0x0000000000000000\
CPM_PCIE0_PF2_PCIEBAR2AXIBAR_SRIOV_QDMA_3 0x0000000000000000\
CPM_PCIE0_PF2_PCIEBAR2AXIBAR_SRIOV_QDMA_4 0x0000000000000000\
CPM_PCIE0_PF2_PCIEBAR2AXIBAR_SRIOV_QDMA_5 0x0000000000000000\
CPM_PCIE0_PF2_PCIEBAR2AXIBAR_XDMA_0 0 CPM_PCIE0_PF2_PCIEBAR2AXIBAR_XDMA_1 0\
CPM_PCIE0_PF2_PCIEBAR2AXIBAR_XDMA_2 0 CPM_PCIE0_PF2_PCIEBAR2AXIBAR_XDMA_3 0\
CPM_PCIE0_PF2_PCIEBAR2AXIBAR_XDMA_4 0 CPM_PCIE0_PF2_PCIEBAR2AXIBAR_XDMA_5 0\
CPM_PCIE0_PF2_PM_CAP_NEXTPTR 0 CPM_PCIE0_PF2_PRI_CAP_NEXTPTR 0\
CPM_PCIE0_PF2_PRI_CAP_ON 0 CPM_PCIE0_PF2_SRIOV_ARI_CAPBL_HIER_PRESERVED 0\
CPM_PCIE0_PF2_SRIOV_BAR0_64BIT 0 CPM_PCIE0_PF2_SRIOV_BAR0_CONTROL Disabled\
CPM_PCIE0_PF2_SRIOV_BAR0_ENABLED 1 CPM_PCIE0_PF2_SRIOV_BAR0_PREFETCHABLE 0\
CPM_PCIE0_PF2_SRIOV_BAR0_SCALE Kilobytes CPM_PCIE0_PF2_SRIOV_BAR0_SIZE 4\
CPM_PCIE0_PF2_SRIOV_BAR0_TYPE Memory CPM_PCIE0_PF2_SRIOV_BAR1_64BIT 0\
CPM_PCIE0_PF2_SRIOV_BAR1_CONTROL Disabled CPM_PCIE0_PF2_SRIOV_BAR1_ENABLED 0\
CPM_PCIE0_PF2_SRIOV_BAR1_PREFETCHABLE 0 CPM_PCIE0_PF2_SRIOV_BAR1_SCALE Bytes\
CPM_PCIE0_PF2_SRIOV_BAR1_SIZE 128 CPM_PCIE0_PF2_SRIOV_BAR1_TYPE Memory\
CPM_PCIE0_PF2_SRIOV_BAR2_64BIT 0 CPM_PCIE0_PF2_SRIOV_BAR2_CONTROL Disabled\
CPM_PCIE0_PF2_SRIOV_BAR2_ENABLED 0 CPM_PCIE0_PF2_SRIOV_BAR2_PREFETCHABLE 0\
CPM_PCIE0_PF2_SRIOV_BAR2_SCALE Bytes CPM_PCIE0_PF2_SRIOV_BAR2_SIZE 128\
CPM_PCIE0_PF2_SRIOV_BAR2_TYPE Memory CPM_PCIE0_PF2_SRIOV_BAR3_64BIT 0\
CPM_PCIE0_PF2_SRIOV_BAR3_CONTROL Disabled CPM_PCIE0_PF2_SRIOV_BAR3_ENABLED 0\
CPM_PCIE0_PF2_SRIOV_BAR3_PREFETCHABLE 0 CPM_PCIE0_PF2_SRIOV_BAR3_SCALE Bytes\
CPM_PCIE0_PF2_SRIOV_BAR3_SIZE 128 CPM_PCIE0_PF2_SRIOV_BAR3_TYPE Memory\
CPM_PCIE0_PF2_SRIOV_BAR4_64BIT 0 CPM_PCIE0_PF2_SRIOV_BAR4_CONTROL Disabled\
CPM_PCIE0_PF2_SRIOV_BAR4_ENABLED 0 CPM_PCIE0_PF2_SRIOV_BAR4_PREFETCHABLE 0\
CPM_PCIE0_PF2_SRIOV_BAR4_SCALE Bytes CPM_PCIE0_PF2_SRIOV_BAR4_SIZE 128\
CPM_PCIE0_PF2_SRIOV_BAR4_TYPE Memory CPM_PCIE0_PF2_SRIOV_BAR5_64BIT 0\
CPM_PCIE0_PF2_SRIOV_BAR5_CONTROL Disabled CPM_PCIE0_PF2_SRIOV_BAR5_ENABLED 0\
CPM_PCIE0_PF2_SRIOV_BAR5_PREFETCHABLE 0 CPM_PCIE0_PF2_SRIOV_BAR5_SCALE Bytes\
CPM_PCIE0_PF2_SRIOV_BAR5_SIZE 128 CPM_PCIE0_PF2_SRIOV_BAR5_TYPE Memory\
CPM_PCIE0_PF2_SRIOV_CAP_ENABLE 0 CPM_PCIE0_PF2_SRIOV_CAP_INITIAL_VF 4\
CPM_PCIE0_PF2_SRIOV_CAP_NEXTPTR 0 CPM_PCIE0_PF2_SRIOV_CAP_TOTAL_VF 0\
CPM_PCIE0_PF2_SRIOV_CAP_VER 1 CPM_PCIE0_PF2_SRIOV_FIRST_VF_OFFSET 10\
CPM_PCIE0_PF2_SRIOV_FUNC_DEP_LINK 0 CPM_PCIE0_PF2_SRIOV_SUPPORTED_PAGE_SIZE 553\
CPM_PCIE0_PF2_SRIOV_VF_DEVICE_ID C23F CPM_PCIE0_PF2_SUB_CLASS_INTF_MENU\
Other_memory_controller CPM_PCIE0_PF2_SUB_CLASS_VALUE 80\
CPM_PCIE0_PF2_TPHR_CAP_NEXTPTR 0 CPM_PCIE0_PF2_USE_CLASS_CODE_LOOKUP_ASSISTANT\
1 CPM_PCIE0_PF2_VEND_ID 10EE CPM_PCIE0_PF2_XDMA_64BIT 0\
CPM_PCIE0_PF2_XDMA_ENABLED 0 CPM_PCIE0_PF2_XDMA_PREFETCHABLE 0\
CPM_PCIE0_PF2_XDMA_SCALE Kilobytes CPM_PCIE0_PF2_XDMA_SIZE 128\
CPM_PCIE0_PF3_AER_CAP_NEXTPTR 0 CPM_PCIE0_PF3_ARI_CAP_NEXTPTR 0\
CPM_PCIE0_PF3_ARI_CAP_NEXT_FUNC 0 CPM_PCIE0_PF3_ATS_CAP_NEXTPTR 0\
CPM_PCIE0_PF3_ATS_CAP_ON 0 CPM_PCIE0_PF3_AXILITE_MASTER_64BIT 0\
CPM_PCIE0_PF3_AXILITE_MASTER_ENABLED 0\
CPM_PCIE0_PF3_AXILITE_MASTER_PREFETCHABLE 0 CPM_PCIE0_PF3_AXILITE_MASTER_SCALE\
Kilobytes CPM_PCIE0_PF3_AXILITE_MASTER_SIZE 128\
CPM_PCIE0_PF3_AXIST_BYPASS_64BIT 0 CPM_PCIE0_PF3_AXIST_BYPASS_ENABLED 0\
CPM_PCIE0_PF3_AXIST_BYPASS_PREFETCHABLE 0 CPM_PCIE0_PF3_AXIST_BYPASS_SCALE\
Kilobytes CPM_PCIE0_PF3_AXIST_BYPASS_SIZE 128 CPM_PCIE0_PF3_BAR0_64BIT 0\
CPM_PCIE0_PF3_BAR0_CONTROL 0 CPM_PCIE0_PF3_BAR0_ENABLED 1\
CPM_PCIE0_PF3_BAR0_PREFETCHABLE 0 CPM_PCIE0_PF3_BAR0_QDMA_64BIT 1\
CPM_PCIE0_PF3_BAR0_QDMA_AXCACHE 0 CPM_PCIE0_PF3_BAR0_QDMA_CONTROL 0\
CPM_PCIE0_PF3_BAR0_QDMA_ENABLED 1 CPM_PCIE0_PF3_BAR0_QDMA_PREFETCHABLE 1\
CPM_PCIE0_PF3_BAR0_QDMA_SCALE Kilobytes CPM_PCIE0_PF3_BAR0_QDMA_SIZE 256\
CPM_PCIE0_PF3_BAR0_QDMA_TYPE DMA CPM_PCIE0_PF3_BAR0_SCALE Kilobytes\
CPM_PCIE0_PF3_BAR0_SIZE 128 CPM_PCIE0_PF3_BAR0_SRIOV_QDMA_64BIT 0\
CPM_PCIE0_PF3_BAR0_SRIOV_QDMA_CONTROL 0 CPM_PCIE0_PF3_BAR0_SRIOV_QDMA_ENABLED 1\
CPM_PCIE0_PF3_BAR0_SRIOV_QDMA_PREFETCHABLE 0\
CPM_PCIE0_PF3_BAR0_SRIOV_QDMA_SCALE Kilobytes\
CPM_PCIE0_PF3_BAR0_SRIOV_QDMA_SIZE 128 CPM_PCIE0_PF3_BAR0_SRIOV_QDMA_TYPE DMA\
CPM_PCIE0_PF3_BAR0_TYPE Memory CPM_PCIE0_PF3_BAR0_XDMA_64BIT 0\
CPM_PCIE0_PF3_BAR0_XDMA_AXCACHE 0 CPM_PCIE0_PF3_BAR0_XDMA_CONTROL 0\
CPM_PCIE0_PF3_BAR0_XDMA_ENABLED 0 CPM_PCIE0_PF3_BAR0_XDMA_PREFETCHABLE 0\
CPM_PCIE0_PF3_BAR0_XDMA_SCALE Bytes CPM_PCIE0_PF3_BAR0_XDMA_SIZE 128\
CPM_PCIE0_PF3_BAR0_XDMA_TYPE AXI_Bridge_Master CPM_PCIE0_PF3_BAR1_64BIT 0\
CPM_PCIE0_PF3_BAR1_CONTROL 0 CPM_PCIE0_PF3_BAR1_ENABLED 0\
CPM_PCIE0_PF3_BAR1_PREFETCHABLE 0 CPM_PCIE0_PF3_BAR1_QDMA_64BIT 0\
CPM_PCIE0_PF3_BAR1_QDMA_AXCACHE 0 CPM_PCIE0_PF3_BAR1_QDMA_CONTROL 0\
CPM_PCIE0_PF3_BAR1_QDMA_ENABLED 0 CPM_PCIE0_PF3_BAR1_QDMA_PREFETCHABLE 0\
CPM_PCIE0_PF3_BAR1_QDMA_SCALE Bytes CPM_PCIE0_PF3_BAR1_QDMA_SIZE 128\
CPM_PCIE0_PF3_BAR1_QDMA_TYPE AXI_Bridge_Master CPM_PCIE0_PF3_BAR1_SCALE Bytes\
CPM_PCIE0_PF3_BAR1_SIZE 128 CPM_PCIE0_PF3_BAR1_SRIOV_QDMA_64BIT 0\
CPM_PCIE0_PF3_BAR1_SRIOV_QDMA_CONTROL 0 CPM_PCIE0_PF3_BAR1_SRIOV_QDMA_ENABLED 0\
CPM_PCIE0_PF3_BAR1_SRIOV_QDMA_PREFETCHABLE 0\
CPM_PCIE0_PF3_BAR1_SRIOV_QDMA_SCALE Bytes CPM_PCIE0_PF3_BAR1_SRIOV_QDMA_SIZE 1\
CPM_PCIE0_PF3_BAR1_SRIOV_QDMA_TYPE AXI_Bridge_Master CPM_PCIE0_PF3_BAR1_TYPE\
Memory CPM_PCIE0_PF3_BAR1_XDMA_64BIT 0 CPM_PCIE0_PF3_BAR1_XDMA_AXCACHE 0\
CPM_PCIE0_PF3_BAR1_XDMA_CONTROL 0 CPM_PCIE0_PF3_BAR1_XDMA_ENABLED 0\
CPM_PCIE0_PF3_BAR1_XDMA_PREFETCHABLE 0 CPM_PCIE0_PF3_BAR1_XDMA_SCALE Bytes\
CPM_PCIE0_PF3_BAR1_XDMA_SIZE 128 CPM_PCIE0_PF3_BAR1_XDMA_TYPE AXI_Bridge_Master\
CPM_PCIE0_PF3_BAR2_64BIT 0 CPM_PCIE0_PF3_BAR2_CONTROL 0\
CPM_PCIE0_PF3_BAR2_ENABLED 0 CPM_PCIE0_PF3_BAR2_PREFETCHABLE 0\
CPM_PCIE0_PF3_BAR2_QDMA_64BIT 0 CPM_PCIE0_PF3_BAR2_QDMA_AXCACHE 0\
CPM_PCIE0_PF3_BAR2_QDMA_CONTROL 0 CPM_PCIE0_PF3_BAR2_QDMA_ENABLED 0\
CPM_PCIE0_PF3_BAR2_QDMA_PREFETCHABLE 0 CPM_PCIE0_PF3_BAR2_QDMA_SCALE Bytes\
CPM_PCIE0_PF3_BAR2_QDMA_SIZE 128 CPM_PCIE0_PF3_BAR2_QDMA_TYPE AXI_Bridge_Master\
CPM_PCIE0_PF3_BAR2_SCALE Bytes CPM_PCIE0_PF3_BAR2_SIZE 128\
CPM_PCIE0_PF3_BAR2_SRIOV_QDMA_64BIT 0 CPM_PCIE0_PF3_BAR2_SRIOV_QDMA_CONTROL 0\
CPM_PCIE0_PF3_BAR2_SRIOV_QDMA_ENABLED 0\
CPM_PCIE0_PF3_BAR2_SRIOV_QDMA_PREFETCHABLE 0\
CPM_PCIE0_PF3_BAR2_SRIOV_QDMA_SCALE Bytes CPM_PCIE0_PF3_BAR2_SRIOV_QDMA_SIZE 1\
CPM_PCIE0_PF3_BAR2_SRIOV_QDMA_TYPE AXI_Bridge_Master CPM_PCIE0_PF3_BAR2_TYPE\
Memory CPM_PCIE0_PF3_BAR2_XDMA_64BIT 0 CPM_PCIE0_PF3_BAR2_XDMA_AXCACHE 0\
CPM_PCIE0_PF3_BAR2_XDMA_CONTROL 0 CPM_PCIE0_PF3_BAR2_XDMA_ENABLED 0\
CPM_PCIE0_PF3_BAR2_XDMA_PREFETCHABLE 0 CPM_PCIE0_PF3_BAR2_XDMA_SCALE Bytes\
CPM_PCIE0_PF3_BAR2_XDMA_SIZE 128 CPM_PCIE0_PF3_BAR2_XDMA_TYPE AXI_Bridge_Master\
CPM_PCIE0_PF3_BAR3_64BIT 0 CPM_PCIE0_PF3_BAR3_CONTROL 0\
CPM_PCIE0_PF3_BAR3_ENABLED 0 CPM_PCIE0_PF3_BAR3_PREFETCHABLE 0\
CPM_PCIE0_PF3_BAR3_QDMA_64BIT 0 CPM_PCIE0_PF3_BAR3_QDMA_AXCACHE 0\
CPM_PCIE0_PF3_BAR3_QDMA_CONTROL 0 CPM_PCIE0_PF3_BAR3_QDMA_ENABLED 0\
CPM_PCIE0_PF3_BAR3_QDMA_PREFETCHABLE 0 CPM_PCIE0_PF3_BAR3_QDMA_SCALE Bytes\
CPM_PCIE0_PF3_BAR3_QDMA_SIZE 128 CPM_PCIE0_PF3_BAR3_QDMA_TYPE AXI_Bridge_Master\
CPM_PCIE0_PF3_BAR3_SCALE Bytes CPM_PCIE0_PF3_BAR3_SIZE 128\
CPM_PCIE0_PF3_BAR3_SRIOV_QDMA_64BIT 0 CPM_PCIE0_PF3_BAR3_SRIOV_QDMA_CONTROL 0\
CPM_PCIE0_PF3_BAR3_SRIOV_QDMA_ENABLED 0\
CPM_PCIE0_PF3_BAR3_SRIOV_QDMA_PREFETCHABLE 0\
CPM_PCIE0_PF3_BAR3_SRIOV_QDMA_SCALE Bytes CPM_PCIE0_PF3_BAR3_SRIOV_QDMA_SIZE 1\
CPM_PCIE0_PF3_BAR3_SRIOV_QDMA_TYPE AXI_Bridge_Master CPM_PCIE0_PF3_BAR3_TYPE\
Memory CPM_PCIE0_PF3_BAR3_XDMA_64BIT 0 CPM_PCIE0_PF3_BAR3_XDMA_AXCACHE 0\
CPM_PCIE0_PF3_BAR3_XDMA_CONTROL 0 CPM_PCIE0_PF3_BAR3_XDMA_ENABLED 0\
CPM_PCIE0_PF3_BAR3_XDMA_PREFETCHABLE 0 CPM_PCIE0_PF3_BAR3_XDMA_SCALE Bytes\
CPM_PCIE0_PF3_BAR3_XDMA_SIZE 128 CPM_PCIE0_PF3_BAR3_XDMA_TYPE AXI_Bridge_Master\
CPM_PCIE0_PF3_BAR4_64BIT 0 CPM_PCIE0_PF3_BAR4_CONTROL 0\
CPM_PCIE0_PF3_BAR4_ENABLED 0 CPM_PCIE0_PF3_BAR4_PREFETCHABLE 0\
CPM_PCIE0_PF3_BAR4_QDMA_64BIT 0 CPM_PCIE0_PF3_BAR4_QDMA_AXCACHE 0\
CPM_PCIE0_PF3_BAR4_QDMA_CONTROL 0 CPM_PCIE0_PF3_BAR4_QDMA_ENABLED 0\
CPM_PCIE0_PF3_BAR4_QDMA_PREFETCHABLE 0 CPM_PCIE0_PF3_BAR4_QDMA_SCALE Bytes\
CPM_PCIE0_PF3_BAR4_QDMA_SIZE 128 CPM_PCIE0_PF3_BAR4_QDMA_TYPE AXI_Bridge_Master\
CPM_PCIE0_PF3_BAR4_SCALE Bytes CPM_PCIE0_PF3_BAR4_SIZE 128\
CPM_PCIE0_PF3_BAR4_SRIOV_QDMA_64BIT 0 CPM_PCIE0_PF3_BAR4_SRIOV_QDMA_CONTROL 0\
CPM_PCIE0_PF3_BAR4_SRIOV_QDMA_ENABLED 0\
CPM_PCIE0_PF3_BAR4_SRIOV_QDMA_PREFETCHABLE 0\
CPM_PCIE0_PF3_BAR4_SRIOV_QDMA_SCALE Bytes CPM_PCIE0_PF3_BAR4_SRIOV_QDMA_SIZE 1\
CPM_PCIE0_PF3_BAR4_SRIOV_QDMA_TYPE AXI_Bridge_Master CPM_PCIE0_PF3_BAR4_TYPE\
Memory CPM_PCIE0_PF3_BAR4_XDMA_64BIT 0 CPM_PCIE0_PF3_BAR4_XDMA_AXCACHE 0\
CPM_PCIE0_PF3_BAR4_XDMA_CONTROL 0 CPM_PCIE0_PF3_BAR4_XDMA_ENABLED 0\
CPM_PCIE0_PF3_BAR4_XDMA_PREFETCHABLE 0 CPM_PCIE0_PF3_BAR4_XDMA_SCALE Bytes\
CPM_PCIE0_PF3_BAR4_XDMA_SIZE 128 CPM_PCIE0_PF3_BAR4_XDMA_TYPE AXI_Bridge_Master\
CPM_PCIE0_PF3_BAR5_64BIT 0 CPM_PCIE0_PF3_BAR5_CONTROL 0\
CPM_PCIE0_PF3_BAR5_ENABLED 0 CPM_PCIE0_PF3_BAR5_PREFETCHABLE 0\
CPM_PCIE0_PF3_BAR5_QDMA_64BIT 0 CPM_PCIE0_PF3_BAR5_QDMA_AXCACHE 0\
CPM_PCIE0_PF3_BAR5_QDMA_CONTROL 0 CPM_PCIE0_PF3_BAR5_QDMA_ENABLED 0\
CPM_PCIE0_PF3_BAR5_QDMA_PREFETCHABLE 0 CPM_PCIE0_PF3_BAR5_QDMA_SCALE Bytes\
CPM_PCIE0_PF3_BAR5_QDMA_SIZE 128 CPM_PCIE0_PF3_BAR5_QDMA_TYPE AXI_Bridge_Master\
CPM_PCIE0_PF3_BAR5_SCALE Bytes CPM_PCIE0_PF3_BAR5_SIZE 128\
CPM_PCIE0_PF3_BAR5_SRIOV_QDMA_64BIT 0 CPM_PCIE0_PF3_BAR5_SRIOV_QDMA_CONTROL 0\
CPM_PCIE0_PF3_BAR5_SRIOV_QDMA_ENABLED 0\
CPM_PCIE0_PF3_BAR5_SRIOV_QDMA_PREFETCHABLE 0\
CPM_PCIE0_PF3_BAR5_SRIOV_QDMA_SCALE Bytes CPM_PCIE0_PF3_BAR5_SRIOV_QDMA_SIZE 1\
CPM_PCIE0_PF3_BAR5_SRIOV_QDMA_TYPE AXI_Bridge_Master CPM_PCIE0_PF3_BAR5_TYPE\
Memory CPM_PCIE0_PF3_BAR5_XDMA_64BIT 0 CPM_PCIE0_PF3_BAR5_XDMA_AXCACHE 0\
CPM_PCIE0_PF3_BAR5_XDMA_CONTROL 0 CPM_PCIE0_PF3_BAR5_XDMA_ENABLED 0\
CPM_PCIE0_PF3_BAR5_XDMA_PREFETCHABLE 0 CPM_PCIE0_PF3_BAR5_XDMA_SCALE Bytes\
CPM_PCIE0_PF3_BAR5_XDMA_SIZE 128 CPM_PCIE0_PF3_BAR5_XDMA_TYPE AXI_Bridge_Master\
CPM_PCIE0_PF3_BASE_CLASS_MENU Memory_controller CPM_PCIE0_PF3_BASE_CLASS_VALUE\
05 CPM_PCIE0_PF3_CAPABILITY_POINTER 80 CPM_PCIE0_PF3_CAP_NEXTPTR 0\
CPM_PCIE0_PF3_CFG_DEV_ID B33F CPM_PCIE0_PF3_CFG_REV_ID 0\
CPM_PCIE0_PF3_CFG_SUBSYS_ID 7 CPM_PCIE0_PF3_CFG_SUBSYS_VEND_ID 10EE\
CPM_PCIE0_PF3_CLASS_CODE 0x000 CPM_PCIE0_PF3_DLL_FEATURE_CAP_NEXTPTR 0\
CPM_PCIE0_PF3_DSN_CAP_ENABLE 0 CPM_PCIE0_PF3_DSN_CAP_NEXTPTR 10C\
CPM_PCIE0_PF3_EXPANSION_ROM_ENABLED 0 CPM_PCIE0_PF3_EXPANSION_ROM_QDMA_ENABLED\
0 CPM_PCIE0_PF3_EXPANSION_ROM_QDMA_SCALE Kilobytes\
CPM_PCIE0_PF3_EXPANSION_ROM_QDMA_SIZE 2 CPM_PCIE0_PF3_EXPANSION_ROM_SCALE\
Kilobytes CPM_PCIE0_PF3_EXPANSION_ROM_SIZE 2 CPM_PCIE0_PF3_INTERFACE_VALUE 00\
CPM_PCIE0_PF3_INTERRUPT_PIN NONE CPM_PCIE0_PF3_MSIX_CAP_NEXTPTR 0\
CPM_PCIE0_PF3_MSIX_CAP_PBA_BIR BAR_0 CPM_PCIE0_PF3_MSIX_CAP_PBA_OFFSET 50\
CPM_PCIE0_PF3_MSIX_CAP_TABLE_BIR BAR_0 CPM_PCIE0_PF3_MSIX_CAP_TABLE_OFFSET 40\
CPM_PCIE0_PF3_MSIX_CAP_TABLE_SIZE 007 CPM_PCIE0_PF3_MSIX_ENABLED 1\
CPM_PCIE0_PF3_MSI_CAP_MULTIMSGCAP 1_vector CPM_PCIE0_PF3_MSI_CAP_NEXTPTR 0\
CPM_PCIE0_PF3_MSI_CAP_PERVECMASKCAP 0 CPM_PCIE0_PF3_MSI_ENABLED 1\
CPM_PCIE0_PF3_PASID_CAP_NEXTPTR 0 CPM_PCIE0_PF3_PCIEBAR2AXIBAR_AXIL_MASTER 0\
CPM_PCIE0_PF3_PCIEBAR2AXIBAR_AXIST_BYPASS 0 CPM_PCIE0_PF3_PCIEBAR2AXIBAR_QDMA_0\
0x0000000000000000 CPM_PCIE0_PF3_PCIEBAR2AXIBAR_QDMA_1 0x0000000000000000\
CPM_PCIE0_PF3_PCIEBAR2AXIBAR_QDMA_2 0x0000000000000000\
CPM_PCIE0_PF3_PCIEBAR2AXIBAR_QDMA_3 0x0000000000000000\
CPM_PCIE0_PF3_PCIEBAR2AXIBAR_QDMA_4 0x0000000000000000\
CPM_PCIE0_PF3_PCIEBAR2AXIBAR_QDMA_5 0x0000000000000000\
CPM_PCIE0_PF3_PCIEBAR2AXIBAR_SRIOV_QDMA_0 0x0000000000000000\
CPM_PCIE0_PF3_PCIEBAR2AXIBAR_SRIOV_QDMA_1 0x0000000000000000\
CPM_PCIE0_PF3_PCIEBAR2AXIBAR_SRIOV_QDMA_2 0x0000000000000000\
CPM_PCIE0_PF3_PCIEBAR2AXIBAR_SRIOV_QDMA_3 0x0000000000000000\
CPM_PCIE0_PF3_PCIEBAR2AXIBAR_SRIOV_QDMA_4 0x0000000000000000\
CPM_PCIE0_PF3_PCIEBAR2AXIBAR_SRIOV_QDMA_5 0x0000000000000000\
CPM_PCIE0_PF3_PCIEBAR2AXIBAR_XDMA_0 0 CPM_PCIE0_PF3_PCIEBAR2AXIBAR_XDMA_1 0\
CPM_PCIE0_PF3_PCIEBAR2AXIBAR_XDMA_2 0 CPM_PCIE0_PF3_PCIEBAR2AXIBAR_XDMA_3 0\
CPM_PCIE0_PF3_PCIEBAR2AXIBAR_XDMA_4 0 CPM_PCIE0_PF3_PCIEBAR2AXIBAR_XDMA_5 0\
CPM_PCIE0_PF3_PM_CAP_NEXTPTR 0 CPM_PCIE0_PF3_PRI_CAP_NEXTPTR 0\
CPM_PCIE0_PF3_PRI_CAP_ON 0 CPM_PCIE0_PF3_SRIOV_ARI_CAPBL_HIER_PRESERVED 0\
CPM_PCIE0_PF3_SRIOV_BAR0_64BIT 0 CPM_PCIE0_PF3_SRIOV_BAR0_CONTROL Disabled\
CPM_PCIE0_PF3_SRIOV_BAR0_ENABLED 1 CPM_PCIE0_PF3_SRIOV_BAR0_PREFETCHABLE 0\
CPM_PCIE0_PF3_SRIOV_BAR0_SCALE Kilobytes CPM_PCIE0_PF3_SRIOV_BAR0_SIZE 4\
CPM_PCIE0_PF3_SRIOV_BAR0_TYPE Memory CPM_PCIE0_PF3_SRIOV_BAR1_64BIT 0\
CPM_PCIE0_PF3_SRIOV_BAR1_CONTROL Disabled CPM_PCIE0_PF3_SRIOV_BAR1_ENABLED 0\
CPM_PCIE0_PF3_SRIOV_BAR1_PREFETCHABLE 0 CPM_PCIE0_PF3_SRIOV_BAR1_SCALE Bytes\
CPM_PCIE0_PF3_SRIOV_BAR1_SIZE 128 CPM_PCIE0_PF3_SRIOV_BAR1_TYPE Memory\
CPM_PCIE0_PF3_SRIOV_BAR2_64BIT 0 CPM_PCIE0_PF3_SRIOV_BAR2_CONTROL Disabled\
CPM_PCIE0_PF3_SRIOV_BAR2_ENABLED 0 CPM_PCIE0_PF3_SRIOV_BAR2_PREFETCHABLE 0\
CPM_PCIE0_PF3_SRIOV_BAR2_SCALE Bytes CPM_PCIE0_PF3_SRIOV_BAR2_SIZE 128\
CPM_PCIE0_PF3_SRIOV_BAR2_TYPE Memory CPM_PCIE0_PF3_SRIOV_BAR3_64BIT 0\
CPM_PCIE0_PF3_SRIOV_BAR3_CONTROL Disabled CPM_PCIE0_PF3_SRIOV_BAR3_ENABLED 0\
CPM_PCIE0_PF3_SRIOV_BAR3_PREFETCHABLE 0 CPM_PCIE0_PF3_SRIOV_BAR3_SCALE Bytes\
CPM_PCIE0_PF3_SRIOV_BAR3_SIZE 128 CPM_PCIE0_PF3_SRIOV_BAR3_TYPE Memory\
CPM_PCIE0_PF3_SRIOV_BAR4_64BIT 0 CPM_PCIE0_PF3_SRIOV_BAR4_CONTROL Disabled\
CPM_PCIE0_PF3_SRIOV_BAR4_ENABLED 0 CPM_PCIE0_PF3_SRIOV_BAR4_PREFETCHABLE 0\
CPM_PCIE0_PF3_SRIOV_BAR4_SCALE Bytes CPM_PCIE0_PF3_SRIOV_BAR4_SIZE 128\
CPM_PCIE0_PF3_SRIOV_BAR4_TYPE Memory CPM_PCIE0_PF3_SRIOV_BAR5_64BIT 0\
CPM_PCIE0_PF3_SRIOV_BAR5_CONTROL Disabled CPM_PCIE0_PF3_SRIOV_BAR5_ENABLED 0\
CPM_PCIE0_PF3_SRIOV_BAR5_PREFETCHABLE 0 CPM_PCIE0_PF3_SRIOV_BAR5_SCALE Bytes\
CPM_PCIE0_PF3_SRIOV_BAR5_SIZE 128 CPM_PCIE0_PF3_SRIOV_BAR5_TYPE Memory\
CPM_PCIE0_PF3_SRIOV_CAP_ENABLE 0 CPM_PCIE0_PF3_SRIOV_CAP_INITIAL_VF 4\
CPM_PCIE0_PF3_SRIOV_CAP_NEXTPTR 0 CPM_PCIE0_PF3_SRIOV_CAP_TOTAL_VF 0\
CPM_PCIE0_PF3_SRIOV_CAP_VER 1 CPM_PCIE0_PF3_SRIOV_FIRST_VF_OFFSET 13\
CPM_PCIE0_PF3_SRIOV_FUNC_DEP_LINK 0 CPM_PCIE0_PF3_SRIOV_SUPPORTED_PAGE_SIZE 553\
CPM_PCIE0_PF3_SRIOV_VF_DEVICE_ID C33F CPM_PCIE0_PF3_SUB_CLASS_INTF_MENU\
Other_memory_controller CPM_PCIE0_PF3_SUB_CLASS_VALUE 80\
CPM_PCIE0_PF3_TPHR_CAP_NEXTPTR 0 CPM_PCIE0_PF3_USE_CLASS_CODE_LOOKUP_ASSISTANT\
1 CPM_PCIE0_PF3_VEND_ID 10EE CPM_PCIE0_PF3_XDMA_64BIT 0\
CPM_PCIE0_PF3_XDMA_ENABLED 0 CPM_PCIE0_PF3_XDMA_PREFETCHABLE 0\
CPM_PCIE0_PF3_XDMA_SCALE Kilobytes CPM_PCIE0_PF3_XDMA_SIZE 128\
CPM_PCIE0_PL_LINK_CAP_MAX_LINK_SPEED Gen3 CPM_PCIE0_PL_LINK_CAP_MAX_LINK_WIDTH\
NONE CPM_PCIE0_PL_UPSTREAM_FACING 1 CPM_PCIE0_PL_USER_SPARE 0\
CPM_PCIE0_PM_ASPML0S_TIMEOUT 0 CPM_PCIE0_PM_ASPML1_ENTRY_DELAY 0\
CPM_PCIE0_PM_ENABLE_L23_ENTRY 0 CPM_PCIE0_PM_ENABLE_SLOT_POWER_CAPTURE 1\
CPM_PCIE0_PM_L1_REENTRY_DELAY 0 CPM_PCIE0_PM_PME_TURNOFF_ACK_DELAY 0\
CPM_PCIE0_PORT_TYPE PCI_Express_Endpoint_device CPM_PCIE0_QDMA_MULTQ_MAX 2048\
CPM_PCIE0_QDMA_PARITY_SETTINGS None CPM_PCIE0_REF_CLK_FREQ 100_MHz\
CPM_PCIE0_SRIOV_CAP_ENABLE 0 CPM_PCIE0_SRIOV_FIRST_VF_OFFSET 4\
CPM_PCIE0_TL2CFG_IF_PARITY_CHK 0 CPM_PCIE0_TL_PF_ENABLE_REG 1\
CPM_PCIE0_TL_USER_SPARE 0 CPM_PCIE0_TX_FC_IF 0\
CPM_PCIE0_TYPE1_MEMBASE_MEMLIMIT_BRIDGE_ENABLE Disabled\
CPM_PCIE0_TYPE1_MEMBASE_MEMLIMIT_ENABLE Disabled\
CPM_PCIE0_TYPE1_PREFETCHABLE_MEMBASE_BRIDGE_MEMLIMIT Disabled\
CPM_PCIE0_TYPE1_PREFETCHABLE_MEMBASE_MEMLIMIT Disabled CPM_PCIE0_USER_CLK2_FREQ\
125_MHz CPM_PCIE0_USER_CLK_FREQ 125_MHz CPM_PCIE0_USER_EDR_CLK2_FREQ 312.5_MHz\
CPM_PCIE0_USER_EDR_CLK_FREQ 312.5_MHz CPM_PCIE0_VC0_CAPABILITY_POINTER 80\
CPM_PCIE0_VC1_BASE_DISABLE 0 CPM_PCIE0_VFG0_ARI_CAP_NEXTPTR 0\
CPM_PCIE0_VFG0_ATS_CAP_NEXTPTR 0 CPM_PCIE0_VFG0_ATS_CAP_ON 0\
CPM_PCIE0_VFG0_MSIX_CAP_NEXTPTR 0 CPM_PCIE0_VFG0_MSIX_CAP_PBA_BIR BAR_0\
CPM_PCIE0_VFG0_MSIX_CAP_PBA_OFFSET 50 CPM_PCIE0_VFG0_MSIX_CAP_TABLE_BIR BAR_0\
CPM_PCIE0_VFG0_MSIX_CAP_TABLE_OFFSET 40 CPM_PCIE0_VFG0_MSIX_CAP_TABLE_SIZE 001\
CPM_PCIE0_VFG0_MSIX_ENABLED 1 CPM_PCIE0_VFG0_PRI_CAP_ON 0\
CPM_PCIE0_VFG0_TPHR_CAP_NEXTPTR 0 CPM_PCIE0_VFG1_ARI_CAP_NEXTPTR 0\
CPM_PCIE0_VFG1_ATS_CAP_NEXTPTR 0 CPM_PCIE0_VFG1_ATS_CAP_ON 0\
CPM_PCIE0_VFG1_MSIX_CAP_NEXTPTR 0 CPM_PCIE0_VFG1_MSIX_CAP_PBA_BIR BAR_0\
CPM_PCIE0_VFG1_MSIX_CAP_PBA_OFFSET 50 CPM_PCIE0_VFG1_MSIX_CAP_TABLE_BIR BAR_0\
CPM_PCIE0_VFG1_MSIX_CAP_TABLE_OFFSET 40 CPM_PCIE0_VFG1_MSIX_CAP_TABLE_SIZE 001\
CPM_PCIE0_VFG1_MSIX_ENABLED 1 CPM_PCIE0_VFG1_PRI_CAP_ON 0\
CPM_PCIE0_VFG1_TPHR_CAP_NEXTPTR 0 CPM_PCIE0_VFG2_ARI_CAP_NEXTPTR 0\
CPM_PCIE0_VFG2_ATS_CAP_NEXTPTR 0 CPM_PCIE0_VFG2_ATS_CAP_ON 0\
CPM_PCIE0_VFG2_MSIX_CAP_NEXTPTR 0 CPM_PCIE0_VFG2_MSIX_CAP_PBA_BIR BAR_0\
CPM_PCIE0_VFG2_MSIX_CAP_PBA_OFFSET 50 CPM_PCIE0_VFG2_MSIX_CAP_TABLE_BIR BAR_0\
CPM_PCIE0_VFG2_MSIX_CAP_TABLE_OFFSET 40 CPM_PCIE0_VFG2_MSIX_CAP_TABLE_SIZE 001\
CPM_PCIE0_VFG2_MSIX_ENABLED 1 CPM_PCIE0_VFG2_PRI_CAP_ON 0\
CPM_PCIE0_VFG2_TPHR_CAP_NEXTPTR 0 CPM_PCIE0_VFG3_ARI_CAP_NEXTPTR 0\
CPM_PCIE0_VFG3_ATS_CAP_NEXTPTR 0 CPM_PCIE0_VFG3_ATS_CAP_ON 0\
CPM_PCIE0_VFG3_MSIX_CAP_NEXTPTR 0 CPM_PCIE0_VFG3_MSIX_CAP_PBA_BIR BAR_0\
CPM_PCIE0_VFG3_MSIX_CAP_PBA_OFFSET 50 CPM_PCIE0_VFG3_MSIX_CAP_TABLE_BIR BAR_0\
CPM_PCIE0_VFG3_MSIX_CAP_TABLE_OFFSET 40 CPM_PCIE0_VFG3_MSIX_CAP_TABLE_SIZE 001\
CPM_PCIE0_VFG3_MSIX_ENABLED 1 CPM_PCIE0_VFG3_PRI_CAP_ON 0\
CPM_PCIE0_VFG3_TPHR_CAP_NEXTPTR 0 CPM_PCIE0_XDMA_AXILITE_SLAVE_IF 0\
CPM_PCIE0_XDMA_AXI_ID_WIDTH 2 CPM_PCIE0_XDMA_DSC_BYPASS_RD 0000\
CPM_PCIE0_XDMA_DSC_BYPASS_WR 0000 CPM_PCIE0_XDMA_IRQ 1\
CPM_PCIE0_XDMA_PARITY_SETTINGS None CPM_PCIE0_XDMA_RNUM_CHNL 1\
CPM_PCIE0_XDMA_RNUM_RIDS 2 CPM_PCIE0_XDMA_STS_PORTS 0 CPM_PCIE0_XDMA_WNUM_CHNL\
1 CPM_PCIE0_XDMA_WNUM_RIDS 2 CPM_PCIE1_AER_CAP_ENABLED 0\
CPM_PCIE1_ARI_CAP_ENABLED 1 CPM_PCIE1_ASYNC_MODE SRNS CPM_PCIE1_ATS_PRI_CAP_ON\
0 CPM_PCIE1_AXIBAR_NUM 1 CPM_PCIE1_AXISTEN_IF_CC_ALIGNMENT_MODE DWORD_Aligned\
CPM_PCIE1_AXISTEN_IF_COMPL_TIMEOUT_REG0 BEBC20\
CPM_PCIE1_AXISTEN_IF_COMPL_TIMEOUT_REG1 2FAF080\
CPM_PCIE1_AXISTEN_IF_CQ_ALIGNMENT_MODE DWORD_Aligned\
CPM_PCIE1_AXISTEN_IF_ENABLE_256_TAGS 0 CPM_PCIE1_AXISTEN_IF_ENABLE_CLIENT_TAG 0\
CPM_PCIE1_AXISTEN_IF_ENABLE_INTERNAL_MSIX_TABLE 0\
CPM_PCIE1_AXISTEN_IF_ENABLE_MESSAGE_RID_CHECK 1\
CPM_PCIE1_AXISTEN_IF_ENABLE_MSG_ROUTE 0\
CPM_PCIE1_AXISTEN_IF_ENABLE_RX_MSG_INTFC 0\
CPM_PCIE1_AXISTEN_IF_ENABLE_RX_TAG_SCALING 0\
CPM_PCIE1_AXISTEN_IF_ENABLE_TX_TAG_SCALING 0\
CPM_PCIE1_AXISTEN_IF_EXTEND_CPL_TIMEOUT 16ms_to_1s CPM_PCIE1_AXISTEN_IF_EXT_512\
0 CPM_PCIE1_AXISTEN_IF_EXT_512_CC_STRADDLE 0\
CPM_PCIE1_AXISTEN_IF_EXT_512_CQ_STRADDLE 0\
CPM_PCIE1_AXISTEN_IF_EXT_512_RC_4TLP_STRADDLE 1\
CPM_PCIE1_AXISTEN_IF_EXT_512_RC_STRADDLE 1\
CPM_PCIE1_AXISTEN_IF_EXT_512_RQ_STRADDLE 1\
CPM_PCIE1_AXISTEN_IF_RC_ALIGNMENT_MODE DWORD_Aligned\
CPM_PCIE1_AXISTEN_IF_RC_STRADDLE 0 CPM_PCIE1_AXISTEN_IF_RQ_ALIGNMENT_MODE\
DWORD_Aligned CPM_PCIE1_AXISTEN_IF_RX_PARITY_EN 1\
CPM_PCIE1_AXISTEN_IF_SIM_SHORT_CPL_TIMEOUT 0 CPM_PCIE1_AXISTEN_IF_TX_PARITY_EN\
0 CPM_PCIE1_AXISTEN_IF_WIDTH 64 CPM_PCIE1_AXISTEN_MSIX_VECTORS_PER_FUNCTION 8\
CPM_PCIE1_AXISTEN_USER_SPARE 0 CPM_PCIE1_CCIX_EN 0\
CPM_PCIE1_CCIX_OPT_TLP_GEN_AND_RECEPT_EN_CONTROL_INTERNAL 0\
CPM_PCIE1_CCIX_VENDOR_ID 0 CPM_PCIE1_CFG_CTL_IF 0 CPM_PCIE1_CFG_EXT_IF 0\
CPM_PCIE1_CFG_FC_IF 0 CPM_PCIE1_CFG_MGMT_IF 0 CPM_PCIE1_CFG_SPEC_4_0 0\
CPM_PCIE1_CFG_STS_IF 0 CPM_PCIE1_CFG_VEND_ID 10EE CPM_PCIE1_CONTROLLER_ENABLE 0\
CPM_PCIE1_COPY_PF0_ENABLED 0 CPM_PCIE1_COPY_SRIOV_PF0_ENABLED 1\
CPM_PCIE1_CORE_CLK_FREQ 500 CPM_PCIE1_CORE_EDR_CLK_FREQ 625\
CPM_PCIE1_DSC_BYPASS_RD 0 CPM_PCIE1_DSC_BYPASS_WR 0 CPM_PCIE1_EDR_IF 0\
CPM_PCIE1_EDR_LINK_SPEED None CPM_PCIE1_EN_PARITY 0\
CPM_PCIE1_EXT_PCIE_CFG_SPACE_ENABLED None CPM_PCIE1_FUNCTIONAL_MODE None\
CPM_PCIE1_LANE_REVERSAL_EN 1 CPM_PCIE1_LEGACY_EXT_PCIE_CFG_SPACE_ENABLED 0\
CPM_PCIE1_LINK_DEBUG_AXIST_EN 0 CPM_PCIE1_LINK_DEBUG_EN 0\
CPM_PCIE1_LINK_SPEED1_FOR_POWER GEN1 CPM_PCIE1_LINK_WIDTH1_FOR_POWER 0\
CPM_PCIE1_MAX_LINK_SPEED 2.5_GT/s CPM_PCIE1_MCAP_CAP_NEXTPTR 0\
CPM_PCIE1_MCAP_ENABLE 0 CPM_PCIE1_MESG_RSVD_IF 0 CPM_PCIE1_MESG_TRANSMIT_IF 0\
CPM_PCIE1_MODE1_FOR_POWER NONE CPM_PCIE1_MODES None CPM_PCIE1_MODE_SELECTION\
Basic CPM_PCIE1_MSIX_RP_ENABLED 1 CPM_PCIE1_MSI_X_OPTIONS None\
CPM_PCIE1_PASID_IF 0 CPM_PCIE1_PF0_AER_CAP_ECRC_GEN_AND_CHECK_CAPABLE 0\
CPM_PCIE1_PF0_AER_CAP_NEXTPTR 0 CPM_PCIE1_PF0_ARI_CAP_NEXTPTR 0\
CPM_PCIE1_PF0_ARI_CAP_NEXT_FUNC 0 CPM_PCIE1_PF0_ARI_CAP_VER 1\
CPM_PCIE1_PF0_ATS_CAP_NEXTPTR 0 CPM_PCIE1_PF0_ATS_CAP_ON 0\
CPM_PCIE1_PF0_AXILITE_MASTER_64BIT 0 CPM_PCIE1_PF0_AXILITE_MASTER_ENABLED 0\
CPM_PCIE1_PF0_AXILITE_MASTER_PREFETCHABLE 0 CPM_PCIE1_PF0_AXILITE_MASTER_SCALE\
Kilobytes CPM_PCIE1_PF0_AXILITE_MASTER_SIZE 128\
CPM_PCIE1_PF0_AXIST_BYPASS_64BIT 0 CPM_PCIE1_PF0_AXIST_BYPASS_ENABLED 0\
CPM_PCIE1_PF0_AXIST_BYPASS_PREFETCHABLE 0 CPM_PCIE1_PF0_AXIST_BYPASS_SCALE\
Kilobytes CPM_PCIE1_PF0_AXIST_BYPASS_SIZE 128 CPM_PCIE1_PF0_BAR0_64BIT 0\
CPM_PCIE1_PF0_BAR0_CONTROL 0 CPM_PCIE1_PF0_BAR0_ENABLED 1\
CPM_PCIE1_PF0_BAR0_PREFETCHABLE 0 CPM_PCIE1_PF0_BAR0_SCALE Kilobytes\
CPM_PCIE1_PF0_BAR0_SIZE 128 CPM_PCIE1_PF0_BAR0_TYPE Memory\
CPM_PCIE1_PF0_BAR1_64BIT 0 CPM_PCIE1_PF0_BAR1_CONTROL 0\
CPM_PCIE1_PF0_BAR1_ENABLED 0 CPM_PCIE1_PF0_BAR1_PREFETCHABLE 0\
CPM_PCIE1_PF0_BAR1_SCALE Bytes CPM_PCIE1_PF0_BAR1_SIZE 128\
CPM_PCIE1_PF0_BAR1_TYPE Memory CPM_PCIE1_PF0_BAR2_64BIT 0\
CPM_PCIE1_PF0_BAR2_CONTROL 0 CPM_PCIE1_PF0_BAR2_ENABLED 0\
CPM_PCIE1_PF0_BAR2_PREFETCHABLE 0 CPM_PCIE1_PF0_BAR2_SCALE Bytes\
CPM_PCIE1_PF0_BAR2_SIZE 128 CPM_PCIE1_PF0_BAR2_TYPE Memory\
CPM_PCIE1_PF0_BAR3_64BIT 0 CPM_PCIE1_PF0_BAR3_CONTROL 0\
CPM_PCIE1_PF0_BAR3_ENABLED 0 CPM_PCIE1_PF0_BAR3_PREFETCHABLE 0\
CPM_PCIE1_PF0_BAR3_SCALE Bytes CPM_PCIE1_PF0_BAR3_SIZE 128\
CPM_PCIE1_PF0_BAR3_TYPE Memory CPM_PCIE1_PF0_BAR4_64BIT 0\
CPM_PCIE1_PF0_BAR4_CONTROL 0 CPM_PCIE1_PF0_BAR4_ENABLED 0\
CPM_PCIE1_PF0_BAR4_PREFETCHABLE 0 CPM_PCIE1_PF0_BAR4_SCALE Bytes\
CPM_PCIE1_PF0_BAR4_SIZE 128 CPM_PCIE1_PF0_BAR4_TYPE Memory\
CPM_PCIE1_PF0_BAR5_64BIT 0 CPM_PCIE1_PF0_BAR5_CONTROL 0\
CPM_PCIE1_PF0_BAR5_ENABLED 0 CPM_PCIE1_PF0_BAR5_PREFETCHABLE 0\
CPM_PCIE1_PF0_BAR5_SCALE Bytes CPM_PCIE1_PF0_BAR5_SIZE 128\
CPM_PCIE1_PF0_BAR5_TYPE Memory CPM_PCIE1_PF0_BASE_CLASS_MENU Memory_controller\
CPM_PCIE1_PF0_BASE_CLASS_VALUE 05 CPM_PCIE1_PF0_CAPABILITY_POINTER 80\
CPM_PCIE1_PF0_CAP_NEXTPTR 0 CPM_PCIE1_PF0_CFG_DEV_ID B034\
CPM_PCIE1_PF0_CFG_REV_ID 0 CPM_PCIE1_PF0_CFG_SUBSYS_ID 7\
CPM_PCIE1_PF0_CFG_SUBSYS_VEND_ID 10EE CPM_PCIE1_PF0_CLASS_CODE 58000\
CPM_PCIE1_PF0_DEV_CAP_10B_TAG_EN 0 CPM_PCIE1_PF0_DEV_CAP_ENDPOINT_L0S_LATENCY\
less_than_64ns CPM_PCIE1_PF0_DEV_CAP_ENDPOINT_L1S_LATENCY less_than_1us\
CPM_PCIE1_PF0_DEV_CAP_EXT_TAG_EN 0\
CPM_PCIE1_PF0_DEV_CAP_FUNCTION_LEVEL_RESET_CAPABLE 0\
CPM_PCIE1_PF0_DEV_CAP_MAX_PAYLOAD 1024_bytes CPM_PCIE1_PF0_DLL_FEATURE_CAP_ID 0\
CPM_PCIE1_PF0_DLL_FEATURE_CAP_NEXTPTR 0 CPM_PCIE1_PF0_DLL_FEATURE_CAP_ON 0\
CPM_PCIE1_PF0_DLL_FEATURE_CAP_VER 1 CPM_PCIE1_PF0_DSN_CAP_ENABLE 0\
CPM_PCIE1_PF0_DSN_CAP_NEXTPTR 0 CPM_PCIE1_PF0_EXPANSION_ROM_ENABLED 0\
CPM_PCIE1_PF0_EXPANSION_ROM_SCALE Kilobytes CPM_PCIE1_PF0_EXPANSION_ROM_SIZE 2\
CPM_PCIE1_PF0_INTERFACE_VALUE 0 CPM_PCIE1_PF0_INTERRUPT_PIN NONE\
CPM_PCIE1_PF0_LINK_CAP_ASPM_SUPPORT No_ASPM\
CPM_PCIE1_PF0_LINK_STATUS_SLOT_CLOCK_CONFIG 1 CPM_PCIE1_PF0_MARGINING_CAP_ID 0\
CPM_PCIE1_PF0_MARGINING_CAP_NEXTPTR 0 CPM_PCIE1_PF0_MARGINING_CAP_ON 0\
CPM_PCIE1_PF0_MARGINING_CAP_VER 1 CPM_PCIE1_PF0_MSIX_CAP_NEXTPTR 0\
CPM_PCIE1_PF0_MSIX_CAP_PBA_BIR BAR_0 CPM_PCIE1_PF0_MSIX_CAP_PBA_OFFSET 50\
CPM_PCIE1_PF0_MSIX_CAP_TABLE_BIR BAR_0 CPM_PCIE1_PF0_MSIX_CAP_TABLE_OFFSET 40\
CPM_PCIE1_PF0_MSIX_CAP_TABLE_SIZE 001 CPM_PCIE1_PF0_MSIX_ENABLED 1\
CPM_PCIE1_PF0_MSI_CAP_MULTIMSGCAP 1_vector CPM_PCIE1_PF0_MSI_CAP_NEXTPTR 0\
CPM_PCIE1_PF0_MSI_CAP_PERVECMASKCAP 0 CPM_PCIE1_PF0_MSI_ENABLED 1\
CPM_PCIE1_PF0_PASID_CAP_MAX_PASID_WIDTH 1 CPM_PCIE1_PF0_PASID_CAP_NEXTPTR 0\
CPM_PCIE1_PF0_PASID_CAP_ON 0 CPM_PCIE1_PF0_PCIEBAR2AXIBAR_AXIL_MASTER 0\
CPM_PCIE1_PF0_PCIEBAR2AXIBAR_AXIST_BYPASS 0 CPM_PCIE1_PF0_PL16_CAP_ID 0\
CPM_PCIE1_PF0_PL16_CAP_NEXTPTR 0 CPM_PCIE1_PF0_PL16_CAP_ON 0\
CPM_PCIE1_PF0_PL16_CAP_VER 1 CPM_PCIE1_PF0_PM_CAP_ID 0\
CPM_PCIE1_PF0_PM_CAP_NEXTPTR 0 CPM_PCIE1_PF0_PM_CAP_PMESUPPORT_D0 1\
CPM_PCIE1_PF0_PM_CAP_PMESUPPORT_D1 1 CPM_PCIE1_PF0_PM_CAP_PMESUPPORT_D3COLD 1\
CPM_PCIE1_PF0_PM_CAP_PMESUPPORT_D3HOT 1 CPM_PCIE1_PF0_PM_CAP_SUPP_D1_STATE 1\
CPM_PCIE1_PF0_PM_CAP_VER_ID 3 CPM_PCIE1_PF0_PM_CSR_NOSOFTRESET 1\
CPM_PCIE1_PF0_PRI_CAP_NEXTPTR 0 CPM_PCIE1_PF0_PRI_CAP_ON 0\
CPM_PCIE1_PF0_SECONDARY_PCIE_CAP_NEXTPTR 0\
CPM_PCIE1_PF0_SRIOV_ARI_CAPBL_HIER_PRESERVED 0 CPM_PCIE1_PF0_SRIOV_BAR0_64BIT 0\
CPM_PCIE1_PF0_SRIOV_BAR0_CONTROL Disabled CPM_PCIE1_PF0_SRIOV_BAR0_ENABLED 1\
CPM_PCIE1_PF0_SRIOV_BAR0_PREFETCHABLE 0 CPM_PCIE1_PF0_SRIOV_BAR0_SCALE\
Kilobytes CPM_PCIE1_PF0_SRIOV_BAR0_SIZE 4 CPM_PCIE1_PF0_SRIOV_BAR0_TYPE Memory\
CPM_PCIE1_PF0_SRIOV_BAR1_64BIT 0 CPM_PCIE1_PF0_SRIOV_BAR1_CONTROL Disabled\
CPM_PCIE1_PF0_SRIOV_BAR1_ENABLED 0 CPM_PCIE1_PF0_SRIOV_BAR1_PREFETCHABLE 0\
CPM_PCIE1_PF0_SRIOV_BAR1_SCALE Bytes CPM_PCIE1_PF0_SRIOV_BAR1_SIZE 128\
CPM_PCIE1_PF0_SRIOV_BAR1_TYPE Memory CPM_PCIE1_PF0_SRIOV_BAR2_64BIT 0\
CPM_PCIE1_PF0_SRIOV_BAR2_CONTROL Disabled CPM_PCIE1_PF0_SRIOV_BAR2_ENABLED 0\
CPM_PCIE1_PF0_SRIOV_BAR2_PREFETCHABLE 0 CPM_PCIE1_PF0_SRIOV_BAR2_SCALE Bytes\
CPM_PCIE1_PF0_SRIOV_BAR2_SIZE 128 CPM_PCIE1_PF0_SRIOV_BAR2_TYPE Memory\
CPM_PCIE1_PF0_SRIOV_BAR3_64BIT 0 CPM_PCIE1_PF0_SRIOV_BAR3_CONTROL Disabled\
CPM_PCIE1_PF0_SRIOV_BAR3_ENABLED 0 CPM_PCIE1_PF0_SRIOV_BAR3_PREFETCHABLE 0\
CPM_PCIE1_PF0_SRIOV_BAR3_SCALE Bytes CPM_PCIE1_PF0_SRIOV_BAR3_SIZE 128\
CPM_PCIE1_PF0_SRIOV_BAR3_TYPE Memory CPM_PCIE1_PF0_SRIOV_BAR4_64BIT 0\
CPM_PCIE1_PF0_SRIOV_BAR4_CONTROL Disabled CPM_PCIE1_PF0_SRIOV_BAR4_ENABLED 0\
CPM_PCIE1_PF0_SRIOV_BAR4_PREFETCHABLE 0 CPM_PCIE1_PF0_SRIOV_BAR4_SCALE Bytes\
CPM_PCIE1_PF0_SRIOV_BAR4_SIZE 128 CPM_PCIE1_PF0_SRIOV_BAR4_TYPE Memory\
CPM_PCIE1_PF0_SRIOV_BAR5_64BIT 0 CPM_PCIE1_PF0_SRIOV_BAR5_CONTROL Disabled\
CPM_PCIE1_PF0_SRIOV_BAR5_ENABLED 0 CPM_PCIE1_PF0_SRIOV_BAR5_PREFETCHABLE 0\
CPM_PCIE1_PF0_SRIOV_BAR5_SCALE Bytes CPM_PCIE1_PF0_SRIOV_BAR5_SIZE 128\
CPM_PCIE1_PF0_SRIOV_BAR5_TYPE Memory CPM_PCIE1_PF0_SRIOV_CAP_ENABLE 0\
CPM_PCIE1_PF0_SRIOV_CAP_INITIAL_VF 4 CPM_PCIE1_PF0_SRIOV_CAP_NEXTPTR 0\
CPM_PCIE1_PF0_SRIOV_CAP_TOTAL_VF 0 CPM_PCIE1_PF0_SRIOV_CAP_VER 1\
CPM_PCIE1_PF0_SRIOV_FIRST_VF_OFFSET 4 CPM_PCIE1_PF0_SRIOV_FUNC_DEP_LINK 0\
CPM_PCIE1_PF0_SRIOV_SUPPORTED_PAGE_SIZE 553 CPM_PCIE1_PF0_SRIOV_VF_DEVICE_ID\
C034 CPM_PCIE1_PF0_SUB_CLASS_INTF_MENU Other_memory_controller\
CPM_PCIE1_PF0_SUB_CLASS_VALUE 80 CPM_PCIE1_PF0_TPHR_CAP_DEV_SPECIFIC_MODE 1\
CPM_PCIE1_PF0_TPHR_CAP_ENABLE 0 CPM_PCIE1_PF0_TPHR_CAP_INT_VEC_MODE 1\
CPM_PCIE1_PF0_TPHR_CAP_NEXTPTR 0 CPM_PCIE1_PF0_TPHR_CAP_ST_TABLE_LOC\
ST_Table_not_present CPM_PCIE1_PF0_TPHR_CAP_ST_TABLE_SIZE 16\
CPM_PCIE1_PF0_TPHR_CAP_VER 1 CPM_PCIE1_PF0_TPHR_ENABLE 0\
CPM_PCIE1_PF0_USE_CLASS_CODE_LOOKUP_ASSISTANT 1 CPM_PCIE1_PF0_VC_ARB_CAPABILITY\
0 CPM_PCIE1_PF0_VC_ARB_TBL_OFFSET 0 CPM_PCIE1_PF0_VC_CAP_ENABLED 0\
CPM_PCIE1_PF0_VC_CAP_NEXTPTR 0 CPM_PCIE1_PF0_VC_CAP_VER 1\
CPM_PCIE1_PF0_VC_EXTENDED_COUNT 0 CPM_PCIE1_PF0_VC_LOW_PRIORITY_EXTENDED_COUNT\
0 CPM_PCIE1_PF1_AER_CAP_NEXTPTR 0 CPM_PCIE1_PF1_ARI_CAP_NEXTPTR 0\
CPM_PCIE1_PF1_ARI_CAP_NEXT_FUNC 0 CPM_PCIE1_PF1_ATS_CAP_NEXTPTR 0\
CPM_PCIE1_PF1_ATS_CAP_ON 0 CPM_PCIE1_PF1_AXILITE_MASTER_64BIT 0\
CPM_PCIE1_PF1_AXILITE_MASTER_ENABLED 0\
CPM_PCIE1_PF1_AXILITE_MASTER_PREFETCHABLE 0 CPM_PCIE1_PF1_AXILITE_MASTER_SCALE\
Kilobytes CPM_PCIE1_PF1_AXILITE_MASTER_SIZE 128\
CPM_PCIE1_PF1_AXIST_BYPASS_64BIT 0 CPM_PCIE1_PF1_AXIST_BYPASS_ENABLED 0\
CPM_PCIE1_PF1_AXIST_BYPASS_PREFETCHABLE 0 CPM_PCIE1_PF1_AXIST_BYPASS_SCALE\
Kilobytes CPM_PCIE1_PF1_AXIST_BYPASS_SIZE 128 CPM_PCIE1_PF1_BAR0_64BIT 0\
CPM_PCIE1_PF1_BAR0_CONTROL 0 CPM_PCIE1_PF1_BAR0_ENABLED 1\
CPM_PCIE1_PF1_BAR0_PREFETCHABLE 0 CPM_PCIE1_PF1_BAR0_SCALE Kilobytes\
CPM_PCIE1_PF1_BAR0_SIZE 128 CPM_PCIE1_PF1_BAR0_TYPE Memory\
CPM_PCIE1_PF1_BAR1_64BIT 0 CPM_PCIE1_PF1_BAR1_CONTROL 0\
CPM_PCIE1_PF1_BAR1_ENABLED 0 CPM_PCIE1_PF1_BAR1_PREFETCHABLE 0\
CPM_PCIE1_PF1_BAR1_SCALE Bytes CPM_PCIE1_PF1_BAR1_SIZE 128\
CPM_PCIE1_PF1_BAR1_TYPE Memory CPM_PCIE1_PF1_BAR2_64BIT 0\
CPM_PCIE1_PF1_BAR2_CONTROL 0 CPM_PCIE1_PF1_BAR2_ENABLED 0\
CPM_PCIE1_PF1_BAR2_PREFETCHABLE 0 CPM_PCIE1_PF1_BAR2_SCALE Bytes\
CPM_PCIE1_PF1_BAR2_SIZE 128 CPM_PCIE1_PF1_BAR2_TYPE Memory\
CPM_PCIE1_PF1_BAR3_64BIT 0 CPM_PCIE1_PF1_BAR3_CONTROL 0\
CPM_PCIE1_PF1_BAR3_ENABLED 0 CPM_PCIE1_PF1_BAR3_PREFETCHABLE 0\
CPM_PCIE1_PF1_BAR3_SCALE Bytes CPM_PCIE1_PF1_BAR3_SIZE 128\
CPM_PCIE1_PF1_BAR3_TYPE Memory CPM_PCIE1_PF1_BAR4_64BIT 0\
CPM_PCIE1_PF1_BAR4_CONTROL 0 CPM_PCIE1_PF1_BAR4_ENABLED 0\
CPM_PCIE1_PF1_BAR4_PREFETCHABLE 0 CPM_PCIE1_PF1_BAR4_SCALE Bytes\
CPM_PCIE1_PF1_BAR4_SIZE 128 CPM_PCIE1_PF1_BAR4_TYPE Memory\
CPM_PCIE1_PF1_BAR5_64BIT 0 CPM_PCIE1_PF1_BAR5_CONTROL 0\
CPM_PCIE1_PF1_BAR5_ENABLED 0 CPM_PCIE1_PF1_BAR5_PREFETCHABLE 0\
CPM_PCIE1_PF1_BAR5_SCALE Bytes CPM_PCIE1_PF1_BAR5_SIZE 128\
CPM_PCIE1_PF1_BAR5_TYPE Memory CPM_PCIE1_PF1_BASE_CLASS_MENU Memory_controller\
CPM_PCIE1_PF1_BASE_CLASS_VALUE 05 CPM_PCIE1_PF1_CAPABILITY_POINTER 80\
CPM_PCIE1_PF1_CAP_NEXTPTR 0 CPM_PCIE1_PF1_CFG_DEV_ID B134\
CPM_PCIE1_PF1_CFG_REV_ID 0 CPM_PCIE1_PF1_CFG_SUBSYS_ID 7\
CPM_PCIE1_PF1_CFG_SUBSYS_VEND_ID 10EE CPM_PCIE1_PF1_CLASS_CODE 0x000\
CPM_PCIE1_PF1_DLL_FEATURE_CAP_NEXTPTR 0 CPM_PCIE1_PF1_DSN_CAP_ENABLE 0\
CPM_PCIE1_PF1_DSN_CAP_NEXTPTR 10C CPM_PCIE1_PF1_EXPANSION_ROM_ENABLED 0\
CPM_PCIE1_PF1_EXPANSION_ROM_SCALE Kilobytes CPM_PCIE1_PF1_EXPANSION_ROM_SIZE 2\
CPM_PCIE1_PF1_INTERFACE_VALUE 00 CPM_PCIE1_PF1_INTERRUPT_PIN NONE\
CPM_PCIE1_PF1_MSIX_CAP_NEXTPTR 0 CPM_PCIE1_PF1_MSIX_CAP_PBA_BIR BAR_0\
CPM_PCIE1_PF1_MSIX_CAP_PBA_OFFSET 50 CPM_PCIE1_PF1_MSIX_CAP_TABLE_BIR BAR_0\
CPM_PCIE1_PF1_MSIX_CAP_TABLE_OFFSET 40 CPM_PCIE1_PF1_MSIX_CAP_TABLE_SIZE 001\
CPM_PCIE1_PF1_MSIX_ENABLED 1 CPM_PCIE1_PF1_MSI_CAP_MULTIMSGCAP 1_vector\
CPM_PCIE1_PF1_MSI_CAP_NEXTPTR 0 CPM_PCIE1_PF1_MSI_CAP_PERVECMASKCAP 0\
CPM_PCIE1_PF1_MSI_ENABLED 1 CPM_PCIE1_PF1_PASID_CAP_NEXTPTR 0\
CPM_PCIE1_PF1_PCIEBAR2AXIBAR_AXIL_MASTER 0\
CPM_PCIE1_PF1_PCIEBAR2AXIBAR_AXIST_BYPASS 0 CPM_PCIE1_PF1_PM_CAP_NEXTPTR 0\
CPM_PCIE1_PF1_PRI_CAP_NEXTPTR 0 CPM_PCIE1_PF1_PRI_CAP_ON 0\
CPM_PCIE1_PF1_SRIOV_ARI_CAPBL_HIER_PRESERVED 0 CPM_PCIE1_PF1_SRIOV_BAR0_64BIT 0\
CPM_PCIE1_PF1_SRIOV_BAR0_CONTROL Disabled CPM_PCIE1_PF1_SRIOV_BAR0_ENABLED 1\
CPM_PCIE1_PF1_SRIOV_BAR0_PREFETCHABLE 0 CPM_PCIE1_PF1_SRIOV_BAR0_SCALE\
Kilobytes CPM_PCIE1_PF1_SRIOV_BAR0_SIZE 4 CPM_PCIE1_PF1_SRIOV_BAR0_TYPE Memory\
CPM_PCIE1_PF1_SRIOV_BAR1_64BIT 0 CPM_PCIE1_PF1_SRIOV_BAR1_CONTROL Disabled\
CPM_PCIE1_PF1_SRIOV_BAR1_ENABLED 0 CPM_PCIE1_PF1_SRIOV_BAR1_PREFETCHABLE 0\
CPM_PCIE1_PF1_SRIOV_BAR1_SCALE Bytes CPM_PCIE1_PF1_SRIOV_BAR1_SIZE 128\
CPM_PCIE1_PF1_SRIOV_BAR1_TYPE Memory CPM_PCIE1_PF1_SRIOV_BAR2_64BIT 0\
CPM_PCIE1_PF1_SRIOV_BAR2_CONTROL Disabled CPM_PCIE1_PF1_SRIOV_BAR2_ENABLED 0\
CPM_PCIE1_PF1_SRIOV_BAR2_PREFETCHABLE 0 CPM_PCIE1_PF1_SRIOV_BAR2_SCALE Bytes\
CPM_PCIE1_PF1_SRIOV_BAR2_SIZE 128 CPM_PCIE1_PF1_SRIOV_BAR2_TYPE Memory\
CPM_PCIE1_PF1_SRIOV_BAR3_64BIT 0 CPM_PCIE1_PF1_SRIOV_BAR3_CONTROL Disabled\
CPM_PCIE1_PF1_SRIOV_BAR3_ENABLED 0 CPM_PCIE1_PF1_SRIOV_BAR3_PREFETCHABLE 0\
CPM_PCIE1_PF1_SRIOV_BAR3_SCALE Bytes CPM_PCIE1_PF1_SRIOV_BAR3_SIZE 128\
CPM_PCIE1_PF1_SRIOV_BAR3_TYPE Memory CPM_PCIE1_PF1_SRIOV_BAR4_64BIT 0\
CPM_PCIE1_PF1_SRIOV_BAR4_CONTROL Disabled CPM_PCIE1_PF1_SRIOV_BAR4_ENABLED 0\
CPM_PCIE1_PF1_SRIOV_BAR4_PREFETCHABLE 0 CPM_PCIE1_PF1_SRIOV_BAR4_SCALE Bytes\
CPM_PCIE1_PF1_SRIOV_BAR4_SIZE 128 CPM_PCIE1_PF1_SRIOV_BAR4_TYPE Memory\
CPM_PCIE1_PF1_SRIOV_BAR5_64BIT 0 CPM_PCIE1_PF1_SRIOV_BAR5_CONTROL Disabled\
CPM_PCIE1_PF1_SRIOV_BAR5_ENABLED 0 CPM_PCIE1_PF1_SRIOV_BAR5_PREFETCHABLE 0\
CPM_PCIE1_PF1_SRIOV_BAR5_SCALE Bytes CPM_PCIE1_PF1_SRIOV_BAR5_SIZE 128\
CPM_PCIE1_PF1_SRIOV_BAR5_TYPE Memory CPM_PCIE1_PF1_SRIOV_CAP_ENABLE 0\
CPM_PCIE1_PF1_SRIOV_CAP_INITIAL_VF 4 CPM_PCIE1_PF1_SRIOV_CAP_NEXTPTR 0\
CPM_PCIE1_PF1_SRIOV_CAP_TOTAL_VF 0 CPM_PCIE1_PF1_SRIOV_CAP_VER 1\
CPM_PCIE1_PF1_SRIOV_FIRST_VF_OFFSET 7 CPM_PCIE1_PF1_SRIOV_FUNC_DEP_LINK 0\
CPM_PCIE1_PF1_SRIOV_SUPPORTED_PAGE_SIZE 553 CPM_PCIE1_PF1_SRIOV_VF_DEVICE_ID\
C134 CPM_PCIE1_PF1_SUB_CLASS_INTF_MENU Other_memory_controller\
CPM_PCIE1_PF1_SUB_CLASS_VALUE 80 CPM_PCIE1_PF1_TPHR_CAP_NEXTPTR 0\
CPM_PCIE1_PF1_USE_CLASS_CODE_LOOKUP_ASSISTANT 1 CPM_PCIE1_PF1_VEND_ID 10EE\
CPM_PCIE1_PF2_AER_CAP_NEXTPTR 0 CPM_PCIE1_PF2_ARI_CAP_NEXTPTR 0\
CPM_PCIE1_PF2_ARI_CAP_NEXT_FUNC 0 CPM_PCIE1_PF2_ATS_CAP_NEXTPTR 0\
CPM_PCIE1_PF2_ATS_CAP_ON 0 CPM_PCIE1_PF2_AXILITE_MASTER_64BIT 0\
CPM_PCIE1_PF2_AXILITE_MASTER_ENABLED 0\
CPM_PCIE1_PF2_AXILITE_MASTER_PREFETCHABLE 0 CPM_PCIE1_PF2_AXILITE_MASTER_SCALE\
Kilobytes CPM_PCIE1_PF2_AXILITE_MASTER_SIZE 128\
CPM_PCIE1_PF2_AXIST_BYPASS_64BIT 0 CPM_PCIE1_PF2_AXIST_BYPASS_ENABLED 0\
CPM_PCIE1_PF2_AXIST_BYPASS_PREFETCHABLE 0 CPM_PCIE1_PF2_AXIST_BYPASS_SCALE\
Kilobytes CPM_PCIE1_PF2_AXIST_BYPASS_SIZE 128 CPM_PCIE1_PF2_BAR0_64BIT 0\
CPM_PCIE1_PF2_BAR0_CONTROL 0 CPM_PCIE1_PF2_BAR0_ENABLED 1\
CPM_PCIE1_PF2_BAR0_PREFETCHABLE 0 CPM_PCIE1_PF2_BAR0_SCALE Kilobytes\
CPM_PCIE1_PF2_BAR0_SIZE 128 CPM_PCIE1_PF2_BAR0_TYPE Memory\
CPM_PCIE1_PF2_BAR1_64BIT 0 CPM_PCIE1_PF2_BAR1_CONTROL 0\
CPM_PCIE1_PF2_BAR1_ENABLED 0 CPM_PCIE1_PF2_BAR1_PREFETCHABLE 0\
CPM_PCIE1_PF2_BAR1_SCALE Bytes CPM_PCIE1_PF2_BAR1_SIZE 128\
CPM_PCIE1_PF2_BAR1_TYPE Memory CPM_PCIE1_PF2_BAR2_64BIT 0\
CPM_PCIE1_PF2_BAR2_CONTROL 0 CPM_PCIE1_PF2_BAR2_ENABLED 0\
CPM_PCIE1_PF2_BAR2_PREFETCHABLE 0 CPM_PCIE1_PF2_BAR2_SCALE Bytes\
CPM_PCIE1_PF2_BAR2_SIZE 128 CPM_PCIE1_PF2_BAR2_TYPE Memory\
CPM_PCIE1_PF2_BAR3_64BIT 0 CPM_PCIE1_PF2_BAR3_CONTROL 0\
CPM_PCIE1_PF2_BAR3_ENABLED 0 CPM_PCIE1_PF2_BAR3_PREFETCHABLE 0\
CPM_PCIE1_PF2_BAR3_SCALE Bytes CPM_PCIE1_PF2_BAR3_SIZE 128\
CPM_PCIE1_PF2_BAR3_TYPE Memory CPM_PCIE1_PF2_BAR4_64BIT 0\
CPM_PCIE1_PF2_BAR4_CONTROL 0 CPM_PCIE1_PF2_BAR4_ENABLED 0\
CPM_PCIE1_PF2_BAR4_PREFETCHABLE 0 CPM_PCIE1_PF2_BAR4_SCALE Bytes\
CPM_PCIE1_PF2_BAR4_SIZE 128 CPM_PCIE1_PF2_BAR4_TYPE Memory\
CPM_PCIE1_PF2_BAR5_64BIT 0 CPM_PCIE1_PF2_BAR5_CONTROL 0\
CPM_PCIE1_PF2_BAR5_ENABLED 0 CPM_PCIE1_PF2_BAR5_PREFETCHABLE 0\
CPM_PCIE1_PF2_BAR5_SCALE Bytes CPM_PCIE1_PF2_BAR5_SIZE 128\
CPM_PCIE1_PF2_BAR5_TYPE Memory CPM_PCIE1_PF2_BASE_CLASS_MENU Memory_controller\
CPM_PCIE1_PF2_BASE_CLASS_VALUE 05 CPM_PCIE1_PF2_CAPABILITY_POINTER 80\
CPM_PCIE1_PF2_CAP_NEXTPTR 0 CPM_PCIE1_PF2_CFG_DEV_ID B234\
CPM_PCIE1_PF2_CFG_REV_ID 0 CPM_PCIE1_PF2_CFG_SUBSYS_ID 7\
CPM_PCIE1_PF2_CFG_SUBSYS_VEND_ID 10EE CPM_PCIE1_PF2_CLASS_CODE 0x000\
CPM_PCIE1_PF2_DLL_FEATURE_CAP_NEXTPTR 0 CPM_PCIE1_PF2_DSN_CAP_ENABLE 0\
CPM_PCIE1_PF2_DSN_CAP_NEXTPTR 10C CPM_PCIE1_PF2_EXPANSION_ROM_ENABLED 0\
CPM_PCIE1_PF2_EXPANSION_ROM_SCALE Kilobytes CPM_PCIE1_PF2_EXPANSION_ROM_SIZE 2\
CPM_PCIE1_PF2_INTERFACE_VALUE 00 CPM_PCIE1_PF2_INTERRUPT_PIN NONE\
CPM_PCIE1_PF2_MSIX_CAP_NEXTPTR 0 CPM_PCIE1_PF2_MSIX_CAP_PBA_BIR BAR_0\
CPM_PCIE1_PF2_MSIX_CAP_PBA_OFFSET 50 CPM_PCIE1_PF2_MSIX_CAP_TABLE_BIR BAR_0\
CPM_PCIE1_PF2_MSIX_CAP_TABLE_OFFSET 40 CPM_PCIE1_PF2_MSIX_CAP_TABLE_SIZE 001\
CPM_PCIE1_PF2_MSIX_ENABLED 1 CPM_PCIE1_PF2_MSI_CAP_MULTIMSGCAP 1_vector\
CPM_PCIE1_PF2_MSI_CAP_NEXTPTR 0 CPM_PCIE1_PF2_MSI_CAP_PERVECMASKCAP 0\
CPM_PCIE1_PF2_MSI_ENABLED 1 CPM_PCIE1_PF2_PASID_CAP_MAX_PASID_WIDTH 1\
CPM_PCIE1_PF2_PASID_CAP_NEXTPTR 0 CPM_PCIE1_PF2_PCIEBAR2AXIBAR_AXIL_MASTER 0\
CPM_PCIE1_PF2_PCIEBAR2AXIBAR_AXIST_BYPASS 0 CPM_PCIE1_PF2_PM_CAP_NEXTPTR 0\
CPM_PCIE1_PF2_PRI_CAP_NEXTPTR 0 CPM_PCIE1_PF2_PRI_CAP_ON 0\
CPM_PCIE1_PF2_SRIOV_ARI_CAPBL_HIER_PRESERVED 0 CPM_PCIE1_PF2_SRIOV_BAR0_64BIT 0\
CPM_PCIE1_PF2_SRIOV_BAR0_CONTROL Disabled CPM_PCIE1_PF2_SRIOV_BAR0_ENABLED 1\
CPM_PCIE1_PF2_SRIOV_BAR0_PREFETCHABLE 0 CPM_PCIE1_PF2_SRIOV_BAR0_SCALE\
Kilobytes CPM_PCIE1_PF2_SRIOV_BAR0_SIZE 4 CPM_PCIE1_PF2_SRIOV_BAR0_TYPE Memory\
CPM_PCIE1_PF2_SRIOV_BAR1_64BIT 0 CPM_PCIE1_PF2_SRIOV_BAR1_CONTROL Disabled\
CPM_PCIE1_PF2_SRIOV_BAR1_ENABLED 0 CPM_PCIE1_PF2_SRIOV_BAR1_PREFETCHABLE 0\
CPM_PCIE1_PF2_SRIOV_BAR1_SCALE Bytes CPM_PCIE1_PF2_SRIOV_BAR1_SIZE 128\
CPM_PCIE1_PF2_SRIOV_BAR1_TYPE Memory CPM_PCIE1_PF2_SRIOV_BAR2_64BIT 0\
CPM_PCIE1_PF2_SRIOV_BAR2_CONTROL Disabled CPM_PCIE1_PF2_SRIOV_BAR2_ENABLED 0\
CPM_PCIE1_PF2_SRIOV_BAR2_PREFETCHABLE 0 CPM_PCIE1_PF2_SRIOV_BAR2_SCALE Bytes\
CPM_PCIE1_PF2_SRIOV_BAR2_SIZE 128 CPM_PCIE1_PF2_SRIOV_BAR2_TYPE Memory\
CPM_PCIE1_PF2_SRIOV_BAR3_64BIT 0 CPM_PCIE1_PF2_SRIOV_BAR3_CONTROL Disabled\
CPM_PCIE1_PF2_SRIOV_BAR3_ENABLED 0 CPM_PCIE1_PF2_SRIOV_BAR3_PREFETCHABLE 0\
CPM_PCIE1_PF2_SRIOV_BAR3_SCALE Bytes CPM_PCIE1_PF2_SRIOV_BAR3_SIZE 128\
CPM_PCIE1_PF2_SRIOV_BAR3_TYPE Memory CPM_PCIE1_PF2_SRIOV_BAR4_64BIT 0\
CPM_PCIE1_PF2_SRIOV_BAR4_CONTROL Disabled CPM_PCIE1_PF2_SRIOV_BAR4_ENABLED 0\
CPM_PCIE1_PF2_SRIOV_BAR4_PREFETCHABLE 0 CPM_PCIE1_PF2_SRIOV_BAR4_SCALE Bytes\
CPM_PCIE1_PF2_SRIOV_BAR4_SIZE 128 CPM_PCIE1_PF2_SRIOV_BAR4_TYPE Memory\
CPM_PCIE1_PF2_SRIOV_BAR5_64BIT 0 CPM_PCIE1_PF2_SRIOV_BAR5_CONTROL Disabled\
CPM_PCIE1_PF2_SRIOV_BAR5_ENABLED 0 CPM_PCIE1_PF2_SRIOV_BAR5_PREFETCHABLE 0\
CPM_PCIE1_PF2_SRIOV_BAR5_SCALE Bytes CPM_PCIE1_PF2_SRIOV_BAR5_SIZE 128\
CPM_PCIE1_PF2_SRIOV_BAR5_TYPE Memory CPM_PCIE1_PF2_SRIOV_CAP_ENABLE 0\
CPM_PCIE1_PF2_SRIOV_CAP_INITIAL_VF 4 CPM_PCIE1_PF2_SRIOV_CAP_NEXTPTR 0\
CPM_PCIE1_PF2_SRIOV_CAP_TOTAL_VF 0 CPM_PCIE1_PF2_SRIOV_CAP_VER 1\
CPM_PCIE1_PF2_SRIOV_FIRST_VF_OFFSET 10 CPM_PCIE1_PF2_SRIOV_FUNC_DEP_LINK 0\
CPM_PCIE1_PF2_SRIOV_SUPPORTED_PAGE_SIZE 553 CPM_PCIE1_PF2_SRIOV_VF_DEVICE_ID\
C234 CPM_PCIE1_PF2_SUB_CLASS_INTF_MENU Other_memory_controller\
CPM_PCIE1_PF2_SUB_CLASS_VALUE 80 CPM_PCIE1_PF2_TPHR_CAP_NEXTPTR 0\
CPM_PCIE1_PF2_USE_CLASS_CODE_LOOKUP_ASSISTANT 1 CPM_PCIE1_PF2_VEND_ID 10EE\
CPM_PCIE1_PF3_AER_CAP_NEXTPTR 0 CPM_PCIE1_PF3_ARI_CAP_NEXTPTR 0\
CPM_PCIE1_PF3_ARI_CAP_NEXT_FUNC 0 CPM_PCIE1_PF3_ATS_CAP_NEXTPTR 0\
CPM_PCIE1_PF3_ATS_CAP_ON 0 CPM_PCIE1_PF3_AXILITE_MASTER_64BIT 0\
CPM_PCIE1_PF3_AXILITE_MASTER_ENABLED 0\
CPM_PCIE1_PF3_AXILITE_MASTER_PREFETCHABLE 0 CPM_PCIE1_PF3_AXILITE_MASTER_SCALE\
Kilobytes CPM_PCIE1_PF3_AXILITE_MASTER_SIZE 128\
CPM_PCIE1_PF3_AXIST_BYPASS_64BIT 0 CPM_PCIE1_PF3_AXIST_BYPASS_ENABLED 0\
CPM_PCIE1_PF3_AXIST_BYPASS_PREFETCHABLE 0 CPM_PCIE1_PF3_AXIST_BYPASS_SCALE\
Kilobytes CPM_PCIE1_PF3_AXIST_BYPASS_SIZE 128 CPM_PCIE1_PF3_BAR0_64BIT 0\
CPM_PCIE1_PF3_BAR0_CONTROL 0 CPM_PCIE1_PF3_BAR0_ENABLED 1\
CPM_PCIE1_PF3_BAR0_PREFETCHABLE 0 CPM_PCIE1_PF3_BAR0_SCALE Kilobytes\
CPM_PCIE1_PF3_BAR0_SIZE 128 CPM_PCIE1_PF3_BAR0_TYPE Memory\
CPM_PCIE1_PF3_BAR1_64BIT 0 CPM_PCIE1_PF3_BAR1_CONTROL 0\
CPM_PCIE1_PF3_BAR1_ENABLED 0 CPM_PCIE1_PF3_BAR1_PREFETCHABLE 0\
CPM_PCIE1_PF3_BAR1_SCALE Bytes CPM_PCIE1_PF3_BAR1_SIZE 128\
CPM_PCIE1_PF3_BAR1_TYPE Memory CPM_PCIE1_PF3_BAR2_64BIT 0\
CPM_PCIE1_PF3_BAR2_CONTROL 0 CPM_PCIE1_PF3_BAR2_ENABLED 0\
CPM_PCIE1_PF3_BAR2_PREFETCHABLE 0 CPM_PCIE1_PF3_BAR2_SCALE Bytes\
CPM_PCIE1_PF3_BAR2_SIZE 128 CPM_PCIE1_PF3_BAR2_TYPE Memory\
CPM_PCIE1_PF3_BAR3_64BIT 0 CPM_PCIE1_PF3_BAR3_CONTROL 0\
CPM_PCIE1_PF3_BAR3_ENABLED 0 CPM_PCIE1_PF3_BAR3_PREFETCHABLE 0\
CPM_PCIE1_PF3_BAR3_SCALE Bytes CPM_PCIE1_PF3_BAR3_SIZE 128\
CPM_PCIE1_PF3_BAR3_TYPE Memory CPM_PCIE1_PF3_BAR4_64BIT 0\
CPM_PCIE1_PF3_BAR4_CONTROL 0 CPM_PCIE1_PF3_BAR4_ENABLED 0\
CPM_PCIE1_PF3_BAR4_PREFETCHABLE 0 CPM_PCIE1_PF3_BAR4_SCALE Bytes\
CPM_PCIE1_PF3_BAR4_SIZE 128 CPM_PCIE1_PF3_BAR4_TYPE Memory\
CPM_PCIE1_PF3_BAR5_64BIT 0 CPM_PCIE1_PF3_BAR5_CONTROL 0\
CPM_PCIE1_PF3_BAR5_ENABLED 0 CPM_PCIE1_PF3_BAR5_PREFETCHABLE 0\
CPM_PCIE1_PF3_BAR5_SCALE Bytes CPM_PCIE1_PF3_BAR5_SIZE 128\
CPM_PCIE1_PF3_BAR5_TYPE Memory CPM_PCIE1_PF3_BASE_CLASS_MENU Memory_controller\
CPM_PCIE1_PF3_BASE_CLASS_VALUE 05 CPM_PCIE1_PF3_CAPABILITY_POINTER 80\
CPM_PCIE1_PF3_CAP_NEXTPTR 0 CPM_PCIE1_PF3_CFG_DEV_ID B334\
CPM_PCIE1_PF3_CFG_REV_ID 0 CPM_PCIE1_PF3_CFG_SUBSYS_ID 7\
CPM_PCIE1_PF3_CFG_SUBSYS_VEND_ID 10EE CPM_PCIE1_PF3_CLASS_CODE 0x000\
CPM_PCIE1_PF3_DLL_FEATURE_CAP_NEXTPTR 0 CPM_PCIE1_PF3_DSN_CAP_ENABLE 0\
CPM_PCIE1_PF3_DSN_CAP_NEXTPTR 10C CPM_PCIE1_PF3_EXPANSION_ROM_ENABLED 0\
CPM_PCIE1_PF3_EXPANSION_ROM_SCALE Kilobytes CPM_PCIE1_PF3_EXPANSION_ROM_SIZE 2\
CPM_PCIE1_PF3_INTERFACE_VALUE 00 CPM_PCIE1_PF3_INTERRUPT_PIN NONE\
CPM_PCIE1_PF3_MSIX_CAP_NEXTPTR 0 CPM_PCIE1_PF3_MSIX_CAP_PBA_BIR BAR_0\
CPM_PCIE1_PF3_MSIX_CAP_PBA_OFFSET 50 CPM_PCIE1_PF3_MSIX_CAP_TABLE_BIR BAR_0\
CPM_PCIE1_PF3_MSIX_CAP_TABLE_OFFSET 40 CPM_PCIE1_PF3_MSIX_CAP_TABLE_SIZE 001\
CPM_PCIE1_PF3_MSIX_ENABLED 1 CPM_PCIE1_PF3_MSI_CAP_MULTIMSGCAP 1_vector\
CPM_PCIE1_PF3_MSI_CAP_NEXTPTR 0 CPM_PCIE1_PF3_MSI_CAP_PERVECMASKCAP 0\
CPM_PCIE1_PF3_MSI_ENABLED 1 CPM_PCIE1_PF3_PASID_CAP_NEXTPTR 0\
CPM_PCIE1_PF3_PCIEBAR2AXIBAR_AXIL_MASTER 0\
CPM_PCIE1_PF3_PCIEBAR2AXIBAR_AXIST_BYPASS 0 CPM_PCIE1_PF3_PM_CAP_NEXTPTR 0\
CPM_PCIE1_PF3_PRI_CAP_NEXTPTR 0 CPM_PCIE1_PF3_PRI_CAP_ON 0\
CPM_PCIE1_PF3_SRIOV_ARI_CAPBL_HIER_PRESERVED 0 CPM_PCIE1_PF3_SRIOV_BAR0_64BIT 0\
CPM_PCIE1_PF3_SRIOV_BAR0_CONTROL Disabled CPM_PCIE1_PF3_SRIOV_BAR0_ENABLED 1\
CPM_PCIE1_PF3_SRIOV_BAR0_PREFETCHABLE 0 CPM_PCIE1_PF3_SRIOV_BAR0_SCALE\
Kilobytes CPM_PCIE1_PF3_SRIOV_BAR0_SIZE 4 CPM_PCIE1_PF3_SRIOV_BAR0_TYPE Memory\
CPM_PCIE1_PF3_SRIOV_BAR1_64BIT 0 CPM_PCIE1_PF3_SRIOV_BAR1_CONTROL Disabled\
CPM_PCIE1_PF3_SRIOV_BAR1_ENABLED 0 CPM_PCIE1_PF3_SRIOV_BAR1_PREFETCHABLE 0\
CPM_PCIE1_PF3_SRIOV_BAR1_SCALE Bytes CPM_PCIE1_PF3_SRIOV_BAR1_SIZE 128\
CPM_PCIE1_PF3_SRIOV_BAR1_TYPE Memory CPM_PCIE1_PF3_SRIOV_BAR2_64BIT 0\
CPM_PCIE1_PF3_SRIOV_BAR2_CONTROL Disabled CPM_PCIE1_PF3_SRIOV_BAR2_ENABLED 0\
CPM_PCIE1_PF3_SRIOV_BAR2_PREFETCHABLE 0 CPM_PCIE1_PF3_SRIOV_BAR2_SCALE Bytes\
CPM_PCIE1_PF3_SRIOV_BAR2_SIZE 128 CPM_PCIE1_PF3_SRIOV_BAR2_TYPE Memory\
CPM_PCIE1_PF3_SRIOV_BAR3_64BIT 0 CPM_PCIE1_PF3_SRIOV_BAR3_CONTROL Disabled\
CPM_PCIE1_PF3_SRIOV_BAR3_ENABLED 0 CPM_PCIE1_PF3_SRIOV_BAR3_PREFETCHABLE 0\
CPM_PCIE1_PF3_SRIOV_BAR3_SCALE Bytes CPM_PCIE1_PF3_SRIOV_BAR3_SIZE 128\
CPM_PCIE1_PF3_SRIOV_BAR3_TYPE Memory CPM_PCIE1_PF3_SRIOV_BAR4_64BIT 0\
CPM_PCIE1_PF3_SRIOV_BAR4_CONTROL Disabled CPM_PCIE1_PF3_SRIOV_BAR4_ENABLED 0\
CPM_PCIE1_PF3_SRIOV_BAR4_PREFETCHABLE 0 CPM_PCIE1_PF3_SRIOV_BAR4_SCALE Bytes\
CPM_PCIE1_PF3_SRIOV_BAR4_SIZE 128 CPM_PCIE1_PF3_SRIOV_BAR4_TYPE Memory\
CPM_PCIE1_PF3_SRIOV_BAR5_64BIT 0 CPM_PCIE1_PF3_SRIOV_BAR5_CONTROL Disabled\
CPM_PCIE1_PF3_SRIOV_BAR5_ENABLED 0 CPM_PCIE1_PF3_SRIOV_BAR5_PREFETCHABLE 0\
CPM_PCIE1_PF3_SRIOV_BAR5_SCALE Bytes CPM_PCIE1_PF3_SRIOV_BAR5_SIZE 128\
CPM_PCIE1_PF3_SRIOV_BAR5_TYPE Memory CPM_PCIE1_PF3_SRIOV_CAP_ENABLE 0\
CPM_PCIE1_PF3_SRIOV_CAP_INITIAL_VF 4 CPM_PCIE1_PF3_SRIOV_CAP_NEXTPTR 0\
CPM_PCIE1_PF3_SRIOV_CAP_TOTAL_VF 0 CPM_PCIE1_PF3_SRIOV_CAP_VER 1\
CPM_PCIE1_PF3_SRIOV_FIRST_VF_OFFSET 13 CPM_PCIE1_PF3_SRIOV_FUNC_DEP_LINK 0\
CPM_PCIE1_PF3_SRIOV_SUPPORTED_PAGE_SIZE 553 CPM_PCIE1_PF3_SRIOV_VF_DEVICE_ID\
C334 CPM_PCIE1_PF3_SUB_CLASS_INTF_MENU Other_memory_controller\
CPM_PCIE1_PF3_SUB_CLASS_VALUE 80 CPM_PCIE1_PF3_TPHR_CAP_NEXTPTR 0\
CPM_PCIE1_PF3_USE_CLASS_CODE_LOOKUP_ASSISTANT 1 CPM_PCIE1_PF3_VEND_ID 10EE\
CPM_PCIE1_PL_LINK_CAP_MAX_LINK_SPEED Gen3 CPM_PCIE1_PL_LINK_CAP_MAX_LINK_WIDTH\
NONE CPM_PCIE1_PL_UPSTREAM_FACING 1 CPM_PCIE1_PL_USER_SPARE 0\
CPM_PCIE1_PM_ASPML0S_TIMEOUT 0 CPM_PCIE1_PM_ASPML1_ENTRY_DELAY 0\
CPM_PCIE1_PM_ENABLE_L23_ENTRY 0 CPM_PCIE1_PM_ENABLE_SLOT_POWER_CAPTURE 1\
CPM_PCIE1_PM_L1_REENTRY_DELAY 0 CPM_PCIE1_PM_PME_TURNOFF_ACK_DELAY 0\
CPM_PCIE1_PORT_TYPE PCI_Express_Endpoint_device CPM_PCIE1_REF_CLK_FREQ 100_MHz\
CPM_PCIE1_SRIOV_CAP_ENABLE 0 CPM_PCIE1_SRIOV_FIRST_VF_OFFSET 4\
CPM_PCIE1_TL2CFG_IF_PARITY_CHK 0 CPM_PCIE1_TL_PF_ENABLE_REG 1\
CPM_PCIE1_TL_USER_SPARE 0 CPM_PCIE1_TX_FC_IF 0\
CPM_PCIE1_TYPE1_MEMBASE_MEMLIMIT_ENABLE Disabled\
CPM_PCIE1_TYPE1_PREFETCHABLE_MEMBASE_MEMLIMIT Disabled CPM_PCIE1_USER_CLK2_FREQ\
125_MHz CPM_PCIE1_USER_CLK_FREQ 125_MHz CPM_PCIE1_USER_EDR_CLK2_FREQ 312.5_MHz\
CPM_PCIE1_USER_EDR_CLK_FREQ 312.5_MHz CPM_PCIE1_VC0_CAPABILITY_POINTER 80\
CPM_PCIE1_VC1_BASE_DISABLE 0 CPM_PCIE1_VFG0_ARI_CAP_NEXTPTR 0\
CPM_PCIE1_VFG0_ATS_CAP_NEXTPTR 0 CPM_PCIE1_VFG0_ATS_CAP_ON 0\
CPM_PCIE1_VFG0_MSIX_CAP_NEXTPTR 0 CPM_PCIE1_VFG0_MSIX_CAP_PBA_BIR BAR_0\
CPM_PCIE1_VFG0_MSIX_CAP_PBA_OFFSET 50 CPM_PCIE1_VFG0_MSIX_CAP_TABLE_BIR BAR_0\
CPM_PCIE1_VFG0_MSIX_CAP_TABLE_OFFSET 40 CPM_PCIE1_VFG0_MSIX_CAP_TABLE_SIZE 001\
CPM_PCIE1_VFG0_MSIX_ENABLED 1 CPM_PCIE1_VFG0_PRI_CAP_ON 0\
CPM_PCIE1_VFG0_TPHR_CAP_NEXTPTR 0 CPM_PCIE1_VFG1_ARI_CAP_NEXTPTR 0\
CPM_PCIE1_VFG1_ATS_CAP_NEXTPTR 0 CPM_PCIE1_VFG1_ATS_CAP_ON 0\
CPM_PCIE1_VFG1_MSIX_CAP_NEXTPTR 0 CPM_PCIE1_VFG1_MSIX_CAP_PBA_BIR BAR_0\
CPM_PCIE1_VFG1_MSIX_CAP_PBA_OFFSET 50 CPM_PCIE1_VFG1_MSIX_CAP_TABLE_BIR BAR_0\
CPM_PCIE1_VFG1_MSIX_CAP_TABLE_OFFSET 40 CPM_PCIE1_VFG1_MSIX_CAP_TABLE_SIZE 001\
CPM_PCIE1_VFG1_MSIX_ENABLED 1 CPM_PCIE1_VFG1_PRI_CAP_ON 0\
CPM_PCIE1_VFG1_TPHR_CAP_NEXTPTR 0 CPM_PCIE1_VFG2_ARI_CAP_NEXTPTR 0\
CPM_PCIE1_VFG2_ATS_CAP_NEXTPTR 0 CPM_PCIE1_VFG2_ATS_CAP_ON 0\
CPM_PCIE1_VFG2_MSIX_CAP_NEXTPTR 0 CPM_PCIE1_VFG2_MSIX_CAP_PBA_BIR BAR_0\
CPM_PCIE1_VFG2_MSIX_CAP_PBA_OFFSET 50 CPM_PCIE1_VFG2_MSIX_CAP_TABLE_BIR BAR_0\
CPM_PCIE1_VFG2_MSIX_CAP_TABLE_OFFSET 40 CPM_PCIE1_VFG2_MSIX_CAP_TABLE_SIZE 001\
CPM_PCIE1_VFG2_MSIX_ENABLED 1 CPM_PCIE1_VFG2_PRI_CAP_ON 0\
CPM_PCIE1_VFG2_TPHR_CAP_NEXTPTR 0 CPM_PCIE1_VFG3_ARI_CAP_NEXTPTR 0\
CPM_PCIE1_VFG3_ATS_CAP_NEXTPTR 0 CPM_PCIE1_VFG3_ATS_CAP_ON 0\
CPM_PCIE1_VFG3_MSIX_CAP_NEXTPTR 0 CPM_PCIE1_VFG3_MSIX_CAP_PBA_BIR BAR_0\
CPM_PCIE1_VFG3_MSIX_CAP_PBA_OFFSET 50 CPM_PCIE1_VFG3_MSIX_CAP_TABLE_BIR BAR_0\
CPM_PCIE1_VFG3_MSIX_CAP_TABLE_OFFSET 40 CPM_PCIE1_VFG3_MSIX_CAP_TABLE_SIZE 001\
CPM_PCIE1_VFG3_MSIX_ENABLED 1 CPM_PCIE1_VFG3_PRI_CAP_ON 0\
CPM_PCIE1_VFG3_TPHR_CAP_NEXTPTR 0 CPM_PCIE_CHANNELS_FOR_POWER 0\
CPM_PERIPHERAL_EN 0 CPM_PERIPHERAL_TEST_EN 0 CPM_QUAD0_ADDN_PORTS 0\
CPM_QUAD1_ADDN_PORTS 0 CPM_QUAD2_ADDN_PORTS 0 CPM_QUAD3_ADDN_PORTS 0\
CPM_REQ_AGENTS_0_ENABLE 0 CPM_REQ_AGENTS_0_L2_ENABLE 0 CPM_REQ_AGENTS_1_ENABLE\
0 CPM_SELECT_GTOUTCLK TXOUTCLK CPM_TYPE1_MEMBASE_MEMLIMIT_ENABLE Disabled\
CPM_TYPE1_PREFETCHABLE_MEMBASE_MEMLIMIT Disabled CPM_USE_MODES None\
CPM_XDMA_2PF_INTERRUPT_ENABLE 0 CPM_XDMA_TL_PF_VISIBLE 1 CPM_XPIPE_0_CLKDLY_CFG\
0 CPM_XPIPE_0_CLK_CFG 0 CPM_XPIPE_0_INSTANTIATED 0 CPM_XPIPE_0_LINK0_CFG\
DISABLE CPM_XPIPE_0_LINK1_CFG DISABLE CPM_XPIPE_0_LOC QUAD0 CPM_XPIPE_0_MODE 0\
CPM_XPIPE_0_REG_CFG 0 CPM_XPIPE_0_RSVD 0 CPM_XPIPE_1_CLKDLY_CFG 0\
CPM_XPIPE_1_CLK_CFG 0 CPM_XPIPE_1_INSTANTIATED 0 CPM_XPIPE_1_LINK0_CFG DISABLE\
CPM_XPIPE_1_LINK1_CFG DISABLE CPM_XPIPE_1_LOC QUAD1 CPM_XPIPE_1_MODE 0\
CPM_XPIPE_1_REG_CFG 0 CPM_XPIPE_1_RSVD 0 CPM_XPIPE_2_CLKDLY_CFG 0\
CPM_XPIPE_2_CLK_CFG 0 CPM_XPIPE_2_INSTANTIATED 0 CPM_XPIPE_2_LINK0_CFG DISABLE\
CPM_XPIPE_2_LINK1_CFG DISABLE CPM_XPIPE_2_LOC QUAD2 CPM_XPIPE_2_MODE 0\
CPM_XPIPE_2_REG_CFG 0 CPM_XPIPE_2_RSVD 0 CPM_XPIPE_3_CLKDLY_CFG 0\
CPM_XPIPE_3_CLK_CFG 0 CPM_XPIPE_3_INSTANTIATED 0 CPM_XPIPE_3_LINK0_CFG DISABLE\
CPM_XPIPE_3_LINK1_CFG DISABLE CPM_XPIPE_3_LOC QUAD3 CPM_XPIPE_3_MODE 0\
CPM_XPIPE_3_REG_CFG 0 CPM_XPIPE_3_RSVD 0 GT_REFCLK_MHZ 156.25 PS_HSDP0_REFCLK 0\
PS_HSDP1_REFCLK 0 PS_HSDP_EGRESS_TRAFFIC JTAG PS_HSDP_INGRESS_TRAFFIC JTAG\
PS_HSDP_MODE NONE PS_USE_NOC_PS_PCI_0 0 PS_USE_PS_NOC_PCI_0 0\
PS_USE_PS_NOC_PCI_1 0}\
   CONFIG.DDR_MEMORY_MODE {Enable} \
   CONFIG.DEBUG_MODE {Custom} \
   CONFIG.DESIGN_MODE {1} \
   CONFIG.DEVICE_INTEGRITY_MODE {Custom} \
   CONFIG.PS_BOARD_INTERFACE {Custom} \
   CONFIG.PS_PMC_CONFIG {AURORA_LINE_RATE_GPBS 10.0 BOOT_SECONDARY_PCIE_ENABLE 0 CLOCK_MODE Custom\
Component_Name chipscopy_ex_versal_cips_0_0 DDR_MEMORY_MODE {Connectivity to\
DDR via NOC} DESIGN_MODE 1 DEVICE_INTEGRITY_MODE Custom DIS_AUTO_POL_CHECK 0\
GT_REFCLK_MHZ 156.25 INIT_CLK_MHZ 125 INV_POLARITY 0 PCIE_APERTURES_DUAL_ENABLE\
0 PCIE_APERTURES_SINGLE_ENABLE 0 PL_SEM_GPIO_ENABLE 0 PMC_ALT_REF_CLK_FREQMHZ\
33.333 PMC_BANK_0_IO_STANDARD LVCMOS1.8 PMC_BANK_1_IO_STANDARD LVCMOS1.8\
PMC_CIPS_MODE ADVANCE PMC_CORE_SUBSYSTEM_LOAD 10\
PMC_CRP_CFU_REF_CTRL_ACT_FREQMHZ 399.996002 PMC_CRP_CFU_REF_CTRL_DIVISOR0 3\
PMC_CRP_CFU_REF_CTRL_FREQMHZ 400 PMC_CRP_CFU_REF_CTRL_SRCSEL PPLL\
PMC_CRP_DFT_OSC_REF_CTRL_ACT_FREQMHZ 400 PMC_CRP_DFT_OSC_REF_CTRL_DIVISOR0 3\
PMC_CRP_DFT_OSC_REF_CTRL_FREQMHZ 400 PMC_CRP_DFT_OSC_REF_CTRL_SRCSEL PPLL\
PMC_CRP_EFUSE_REF_CTRL_ACT_FREQMHZ 100.000000 PMC_CRP_EFUSE_REF_CTRL_FREQMHZ\
100.000000 PMC_CRP_EFUSE_REF_CTRL_SRCSEL IRO_CLK/4\
PMC_CRP_HSM0_REF_CTRL_ACT_FREQMHZ 33.333000 PMC_CRP_HSM0_REF_CTRL_DIVISOR0 36\
PMC_CRP_HSM0_REF_CTRL_FREQMHZ 33.333 PMC_CRP_HSM0_REF_CTRL_SRCSEL PPLL\
PMC_CRP_HSM1_REF_CTRL_ACT_FREQMHZ 133.332001 PMC_CRP_HSM1_REF_CTRL_DIVISOR0 9\
PMC_CRP_HSM1_REF_CTRL_FREQMHZ 133.333 PMC_CRP_HSM1_REF_CTRL_SRCSEL PPLL\
PMC_CRP_I2C_REF_CTRL_ACT_FREQMHZ 100 PMC_CRP_I2C_REF_CTRL_DIVISOR0 12\
PMC_CRP_I2C_REF_CTRL_FREQMHZ 100 PMC_CRP_I2C_REF_CTRL_SRCSEL PPLL\
PMC_CRP_LSBUS_REF_CTRL_ACT_FREQMHZ 149.998505 PMC_CRP_LSBUS_REF_CTRL_DIVISOR0 8\
PMC_CRP_LSBUS_REF_CTRL_FREQMHZ 150 PMC_CRP_LSBUS_REF_CTRL_SRCSEL PPLL\
PMC_CRP_NOC_REF_CTRL_ACT_FREQMHZ 999.989990 PMC_CRP_NOC_REF_CTRL_FREQMHZ 1000\
PMC_CRP_NOC_REF_CTRL_SRCSEL NPLL PMC_CRP_NPI_REF_CTRL_ACT_FREQMHZ 299.997009\
PMC_CRP_NPI_REF_CTRL_DIVISOR0 4 PMC_CRP_NPI_REF_CTRL_FREQMHZ 300\
PMC_CRP_NPI_REF_CTRL_SRCSEL PPLL PMC_CRP_NPLL_CTRL_CLKOUTDIV 4\
PMC_CRP_NPLL_CTRL_FBDIV 120 PMC_CRP_NPLL_CTRL_SRCSEL REF_CLK\
PMC_CRP_NPLL_TO_XPD_CTRL_DIVISOR0 1 PMC_CRP_OSPI_REF_CTRL_ACT_FREQMHZ 200\
PMC_CRP_OSPI_REF_CTRL_DIVISOR0 4 PMC_CRP_OSPI_REF_CTRL_FREQMHZ 200\
PMC_CRP_OSPI_REF_CTRL_SRCSEL PPLL PMC_CRP_PL0_REF_CTRL_ACT_FREQMHZ 333.329987\
PMC_CRP_PL0_REF_CTRL_DIVISOR0 3 PMC_CRP_PL0_REF_CTRL_FREQMHZ 334\
PMC_CRP_PL0_REF_CTRL_SRCSEL NPLL PMC_CRP_PL1_REF_CTRL_ACT_FREQMHZ 100\
PMC_CRP_PL1_REF_CTRL_DIVISOR0 3 PMC_CRP_PL1_REF_CTRL_FREQMHZ 334\
PMC_CRP_PL1_REF_CTRL_SRCSEL NPLL PMC_CRP_PL2_REF_CTRL_ACT_FREQMHZ 100\
PMC_CRP_PL2_REF_CTRL_DIVISOR0 3 PMC_CRP_PL2_REF_CTRL_FREQMHZ 334\
PMC_CRP_PL2_REF_CTRL_SRCSEL NPLL PMC_CRP_PL3_REF_CTRL_ACT_FREQMHZ 100\
PMC_CRP_PL3_REF_CTRL_DIVISOR0 3 PMC_CRP_PL3_REF_CTRL_FREQMHZ 334\
PMC_CRP_PL3_REF_CTRL_SRCSEL NPLL PMC_CRP_PL5_REF_CTRL_FREQMHZ 400\
PMC_CRP_PPLL_CTRL_CLKOUTDIV 2 PMC_CRP_PPLL_CTRL_FBDIV 72\
PMC_CRP_PPLL_CTRL_SRCSEL REF_CLK PMC_CRP_PPLL_TO_XPD_CTRL_DIVISOR0 1\
PMC_CRP_QSPI_REF_CTRL_ACT_FREQMHZ 300 PMC_CRP_QSPI_REF_CTRL_DIVISOR0 4\
PMC_CRP_QSPI_REF_CTRL_FREQMHZ 300 PMC_CRP_QSPI_REF_CTRL_SRCSEL PPLL\
PMC_CRP_SDIO0_REF_CTRL_ACT_FREQMHZ 200 PMC_CRP_SDIO0_REF_CTRL_DIVISOR0 6\
PMC_CRP_SDIO0_REF_CTRL_FREQMHZ 200 PMC_CRP_SDIO0_REF_CTRL_SRCSEL PPLL\
PMC_CRP_SDIO1_REF_CTRL_ACT_FREQMHZ 200 PMC_CRP_SDIO1_REF_CTRL_DIVISOR0 6\
PMC_CRP_SDIO1_REF_CTRL_FREQMHZ 200 PMC_CRP_SDIO1_REF_CTRL_SRCSEL PPLL\
PMC_CRP_SD_DLL_REF_CTRL_ACT_FREQMHZ 1200 PMC_CRP_SD_DLL_REF_CTRL_DIVISOR0 1\
PMC_CRP_SD_DLL_REF_CTRL_FREQMHZ 1200 PMC_CRP_SD_DLL_REF_CTRL_SRCSEL PPLL\
PMC_CRP_SWITCH_TIMEOUT_CTRL_ACT_FREQMHZ 1.000000\
PMC_CRP_SWITCH_TIMEOUT_CTRL_DIVISOR0 100 PMC_CRP_SWITCH_TIMEOUT_CTRL_FREQMHZ 1\
PMC_CRP_SWITCH_TIMEOUT_CTRL_SRCSEL IRO_CLK/4\
PMC_CRP_SYSMON_REF_CTRL_ACT_FREQMHZ 299.997009 PMC_CRP_SYSMON_REF_CTRL_FREQMHZ\
299.997009 PMC_CRP_SYSMON_REF_CTRL_SRCSEL NPI_REF_CLK\
PMC_CRP_TEST_PATTERN_REF_CTRL_ACT_FREQMHZ 200\
PMC_CRP_TEST_PATTERN_REF_CTRL_DIVISOR0 6 PMC_CRP_TEST_PATTERN_REF_CTRL_FREQMHZ\
200 PMC_CRP_TEST_PATTERN_REF_CTRL_SRCSEL PPLL\
PMC_CRP_USB_SUSPEND_CTRL_ACT_FREQMHZ 0.200000 PMC_CRP_USB_SUSPEND_CTRL_DIVISOR0\
500 PMC_CRP_USB_SUSPEND_CTRL_FREQMHZ 0.2 PMC_CRP_USB_SUSPEND_CTRL_SRCSEL\
IRO_CLK/4 PMC_EXTERNAL_TAMPER {{ENABLE 0} {IO NONE}} PMC_GPIO0_MIO_PERIPHERAL\
{{ENABLE 0} {IO {PMC_MIO 0 .. 25}}} PMC_GPIO1_MIO_PERIPHERAL {{ENABLE 0} {IO\
{PMC_MIO 26 .. 51}}} PMC_GPIO_EMIO_PERIPHERAL_ENABLE 0 PMC_GPIO_EMIO_WIDTH 64\
PMC_GPIO_EMIO_WIDTH_HDL 64 PMC_HSM0_CLK_ENABLE 1 PMC_HSM1_CLK_ENABLE 1\
PMC_I2CPMC_PERIPHERAL {{ENABLE 0} {IO {PMC_MIO 46 .. 47}}} PMC_MIO0 {{AUX_IO 0}\
{DIRECTION out} {DRIVE_STRENGTH 8mA} {OUTPUT_DATA default} {PULL pullup}\
{SCHMITT 1} {SLEW slow} {USAGE Unassigned}} PMC_MIO1 {{AUX_IO 0} {DIRECTION\
inout} {DRIVE_STRENGTH 8mA} {OUTPUT_DATA default} {PULL pullup} {SCHMITT 0}\
{SLEW slow} {USAGE Unassigned}} PMC_MIO10 {{AUX_IO 0} {DIRECTION inout}\
{DRIVE_STRENGTH 8mA} {OUTPUT_DATA default} {PULL pullup} {SCHMITT 0} {SLEW\
slow} {USAGE Unassigned}} PMC_MIO11 {{AUX_IO 0} {DIRECTION inout}\
{DRIVE_STRENGTH 8mA} {OUTPUT_DATA default} {PULL pullup} {SCHMITT 0} {SLEW\
slow} {USAGE Unassigned}} PMC_MIO12 {{AUX_IO 0} {DIRECTION out} {DRIVE_STRENGTH\
8mA} {OUTPUT_DATA default} {PULL pullup} {SCHMITT 1} {SLEW slow} {USAGE\
Unassigned}} PMC_MIO13 {{AUX_IO 0} {DIRECTION out} {DRIVE_STRENGTH 8mA}\
{OUTPUT_DATA default} {PULL pullup} {SCHMITT 1} {SLEW slow} {USAGE Unassigned}}\
PMC_MIO14 {{AUX_IO 0} {DIRECTION inout} {DRIVE_STRENGTH 8mA} {OUTPUT_DATA\
default} {PULL pullup} {SCHMITT 0} {SLEW slow} {USAGE Unassigned}} PMC_MIO15\
{{AUX_IO 0} {DIRECTION inout} {DRIVE_STRENGTH 8mA} {OUTPUT_DATA default} {PULL\
pullup} {SCHMITT 0} {SLEW slow} {USAGE Unassigned}} PMC_MIO16 {{AUX_IO 0}\
{DIRECTION inout} {DRIVE_STRENGTH 8mA} {OUTPUT_DATA default} {PULL pullup}\
{SCHMITT 0} {SLEW slow} {USAGE Unassigned}} PMC_MIO17 {{AUX_IO 0} {DIRECTION\
inout} {DRIVE_STRENGTH 8mA} {OUTPUT_DATA default} {PULL pullup} {SCHMITT 0}\
{SLEW slow} {USAGE Unassigned}} PMC_MIO18 {{AUX_IO 0} {DIRECTION in}\
{DRIVE_STRENGTH 8mA} {OUTPUT_DATA default} {PULL pullup} {SCHMITT 0} {SLEW\
slow} {USAGE Unassigned}} PMC_MIO19 {{AUX_IO 0} {DIRECTION inout}\
{DRIVE_STRENGTH 8mA} {OUTPUT_DATA default} {PULL pullup} {SCHMITT 0} {SLEW\
slow} {USAGE Unassigned}} PMC_MIO2 {{AUX_IO 0} {DIRECTION inout}\
{DRIVE_STRENGTH 8mA} {OUTPUT_DATA default} {PULL pullup} {SCHMITT 0} {SLEW\
slow} {USAGE Unassigned}} PMC_MIO20 {{AUX_IO 0} {DIRECTION inout}\
{DRIVE_STRENGTH 8mA} {OUTPUT_DATA default} {PULL pullup} {SCHMITT 0} {SLEW\
slow} {USAGE Unassigned}} PMC_MIO21 {{AUX_IO 0} {DIRECTION inout}\
{DRIVE_STRENGTH 8mA} {OUTPUT_DATA default} {PULL pullup} {SCHMITT 0} {SLEW\
slow} {USAGE Unassigned}} PMC_MIO22 {{AUX_IO 0} {DIRECTION inout}\
{DRIVE_STRENGTH 8mA} {OUTPUT_DATA default} {PULL pullup} {SCHMITT 0} {SLEW\
slow} {USAGE Unassigned}} PMC_MIO23 {{AUX_IO 0} {DIRECTION in} {DRIVE_STRENGTH\
8mA} {OUTPUT_DATA default} {PULL pullup} {SCHMITT 0} {SLEW slow} {USAGE\
Unassigned}} PMC_MIO24 {{AUX_IO 0} {DIRECTION out} {DRIVE_STRENGTH 8mA}\
{OUTPUT_DATA default} {PULL pullup} {SCHMITT 1} {SLEW slow} {USAGE Unassigned}}\
PMC_MIO25 {{AUX_IO 0} {DIRECTION in} {DRIVE_STRENGTH 8mA} {OUTPUT_DATA default}\
{PULL pullup} {SCHMITT 0} {SLEW slow} {USAGE Unassigned}} PMC_MIO26 {{AUX_IO 0}\
{DIRECTION inout} {DRIVE_STRENGTH 8mA} {OUTPUT_DATA default} {PULL pullup}\
{SCHMITT 0} {SLEW slow} {USAGE Unassigned}} PMC_MIO27 {{AUX_IO 0} {DIRECTION\
inout} {DRIVE_STRENGTH 8mA} {OUTPUT_DATA default} {PULL pullup} {SCHMITT 0}\
{SLEW slow} {USAGE Unassigned}} PMC_MIO28 {{AUX_IO 0} {DIRECTION in}\
{DRIVE_STRENGTH 8mA} {OUTPUT_DATA default} {PULL pullup} {SCHMITT 0} {SLEW\
slow} {USAGE Unassigned}} PMC_MIO29 {{AUX_IO 0} {DIRECTION inout}\
{DRIVE_STRENGTH 8mA} {OUTPUT_DATA default} {PULL pullup} {SCHMITT 0} {SLEW\
slow} {USAGE Unassigned}} PMC_MIO3 {{AUX_IO 0} {DIRECTION inout}\
{DRIVE_STRENGTH 8mA} {OUTPUT_DATA default} {PULL pullup} {SCHMITT 0} {SLEW\
slow} {USAGE Unassigned}} PMC_MIO30 {{AUX_IO 0} {DIRECTION inout}\
{DRIVE_STRENGTH 8mA} {OUTPUT_DATA default} {PULL pullup} {SCHMITT 0} {SLEW\
slow} {USAGE Unassigned}} PMC_MIO31 {{AUX_IO 0} {DIRECTION inout}\
{DRIVE_STRENGTH 8mA} {OUTPUT_DATA default} {PULL pullup} {SCHMITT 0} {SLEW\
slow} {USAGE Unassigned}} PMC_MIO32 {{AUX_IO 0} {DIRECTION inout}\
{DRIVE_STRENGTH 8mA} {OUTPUT_DATA default} {PULL pullup} {SCHMITT 0} {SLEW\
slow} {USAGE Unassigned}} PMC_MIO33 {{AUX_IO 0} {DIRECTION inout}\
{DRIVE_STRENGTH 8mA} {OUTPUT_DATA default} {PULL pullup} {SCHMITT 0} {SLEW\
slow} {USAGE Unassigned}} PMC_MIO34 {{AUX_IO 0} {DIRECTION inout}\
{DRIVE_STRENGTH 8mA} {OUTPUT_DATA default} {PULL pullup} {SCHMITT 0} {SLEW\
slow} {USAGE Unassigned}} PMC_MIO35 {{AUX_IO 0} {DIRECTION inout}\
{DRIVE_STRENGTH 8mA} {OUTPUT_DATA default} {PULL pullup} {SCHMITT 0} {SLEW\
slow} {USAGE Unassigned}} PMC_MIO36 {{AUX_IO 0} {DIRECTION inout}\
{DRIVE_STRENGTH 8mA} {OUTPUT_DATA default} {PULL pullup} {SCHMITT 0} {SLEW\
slow} {USAGE Unassigned}} PMC_MIO37 {{AUX_IO 0} {DIRECTION out} {DRIVE_STRENGTH\
8mA} {OUTPUT_DATA high} {PULL pullup} {SCHMITT 0} {SLEW slow} {USAGE GPIO}}\
PMC_MIO38 {{AUX_IO 0} {DIRECTION in} {DRIVE_STRENGTH 8mA} {OUTPUT_DATA default}\
{PULL pullup} {SCHMITT 0} {SLEW slow} {USAGE Unassigned}} PMC_MIO39 {{AUX_IO 0}\
{DIRECTION in} {DRIVE_STRENGTH 8mA} {OUTPUT_DATA default} {PULL pullup}\
{SCHMITT 0} {SLEW slow} {USAGE Unassigned}} PMC_MIO4 {{AUX_IO 0} {DIRECTION\
inout} {DRIVE_STRENGTH 8mA} {OUTPUT_DATA default} {PULL pullup} {SCHMITT 0}\
{SLEW slow} {USAGE Unassigned}} PMC_MIO40 {{AUX_IO 0} {DIRECTION out}\
{DRIVE_STRENGTH 8mA} {OUTPUT_DATA default} {PULL pullup} {SCHMITT 1} {SLEW\
slow} {USAGE Unassigned}} PMC_MIO41 {{AUX_IO 0} {DIRECTION in} {DRIVE_STRENGTH\
8mA} {OUTPUT_DATA default} {PULL pullup} {SCHMITT 0} {SLEW slow} {USAGE\
Unassigned}} PMC_MIO42 {{AUX_IO 0} {DIRECTION in} {DRIVE_STRENGTH 8mA}\
{OUTPUT_DATA default} {PULL pullup} {SCHMITT 0} {SLEW slow} {USAGE Unassigned}}\
PMC_MIO43 {{AUX_IO 0} {DIRECTION out} {DRIVE_STRENGTH 8mA} {OUTPUT_DATA\
default} {PULL pullup} {SCHMITT 1} {SLEW slow} {USAGE Unassigned}} PMC_MIO44\
{{AUX_IO 0} {DIRECTION inout} {DRIVE_STRENGTH 8mA} {OUTPUT_DATA default} {PULL\
pullup} {SCHMITT 0} {SLEW slow} {USAGE Unassigned}} PMC_MIO45 {{AUX_IO 0}\
{DIRECTION inout} {DRIVE_STRENGTH 8mA} {OUTPUT_DATA default} {PULL pullup}\
{SCHMITT 0} {SLEW slow} {USAGE Unassigned}} PMC_MIO46 {{AUX_IO 0} {DIRECTION\
inout} {DRIVE_STRENGTH 8mA} {OUTPUT_DATA default} {PULL pullup} {SCHMITT 0}\
{SLEW slow} {USAGE Unassigned}} PMC_MIO47 {{AUX_IO 0} {DIRECTION inout}\
{DRIVE_STRENGTH 8mA} {OUTPUT_DATA default} {PULL pullup} {SCHMITT 0} {SLEW\
slow} {USAGE Unassigned}} PMC_MIO48 {{AUX_IO 0} {DIRECTION in} {DRIVE_STRENGTH\
8mA} {OUTPUT_DATA default} {PULL pullup} {SCHMITT 0} {SLEW slow} {USAGE\
Unassigned}} PMC_MIO49 {{AUX_IO 0} {DIRECTION in} {DRIVE_STRENGTH 8mA}\
{OUTPUT_DATA default} {PULL pullup} {SCHMITT 0} {SLEW slow} {USAGE Unassigned}}\
PMC_MIO5 {{AUX_IO 0} {DIRECTION out} {DRIVE_STRENGTH 8mA} {OUTPUT_DATA default}\
{PULL pullup} {SCHMITT 1} {SLEW slow} {USAGE Unassigned}} PMC_MIO50 {{AUX_IO 0}\
{DIRECTION in} {DRIVE_STRENGTH 8mA} {OUTPUT_DATA default} {PULL pullup}\
{SCHMITT 0} {SLEW slow} {USAGE Unassigned}} PMC_MIO51 {{AUX_IO 0} {DIRECTION\
out} {DRIVE_STRENGTH 8mA} {OUTPUT_DATA default} {PULL pullup} {SCHMITT 1} {SLEW\
slow} {USAGE Unassigned}} PMC_MIO6 {{AUX_IO 0} {DIRECTION out} {DRIVE_STRENGTH\
8mA} {OUTPUT_DATA default} {PULL pullup} {SCHMITT 1} {SLEW slow} {USAGE\
Unassigned}} PMC_MIO7 {{AUX_IO 0} {DIRECTION out} {DRIVE_STRENGTH 8mA}\
{OUTPUT_DATA default} {PULL pullup} {SCHMITT 1} {SLEW slow} {USAGE Unassigned}}\
PMC_MIO8 {{AUX_IO 0} {DIRECTION inout} {DRIVE_STRENGTH 8mA} {OUTPUT_DATA\
default} {PULL pullup} {SCHMITT 0} {SLEW slow} {USAGE Unassigned}} PMC_MIO9\
{{AUX_IO 0} {DIRECTION inout} {DRIVE_STRENGTH 8mA} {OUTPUT_DATA default} {PULL\
pullup} {SCHMITT 0} {SLEW slow} {USAGE Unassigned}} PMC_MIO_EN_FOR_PL_PCIE 0\
PMC_MIO_TREE_PERIPHERALS {#####################################GPIO\
1########################################} PMC_MIO_TREE_SIGNALS\
#####################################gpio_1_pin[37]########################################\
PMC_NOC_PMC_ADDR_WIDTH 64 PMC_NOC_PMC_DATA_WIDTH 128 PMC_OSPI_COHERENCY 0\
PMC_OSPI_PERIPHERAL {{ENABLE 0} {IO {PMC_MIO 0 .. 11}} {MODE Single}}\
PMC_OSPI_ROUTE_THROUGH_FPD 0 PMC_PL_ALT_REF_CLK_FREQMHZ 33.333\
PMC_PMC_NOC_ADDR_WIDTH 64 PMC_PMC_NOC_DATA_WIDTH 128 PMC_QSPI_COHERENCY 0\
PMC_QSPI_FBCLK {{ENABLE 0} {IO {PMC_MIO 6}}} PMC_QSPI_PERIPHERAL_DATA_MODE x4\
PMC_QSPI_PERIPHERAL_ENABLE 0 PMC_QSPI_PERIPHERAL_MODE {Dual Parallel}\
PMC_QSPI_ROUTE_THROUGH_FPD 0 PMC_REF_CLK_FREQMHZ 33.333 PMC_SD0 {{CD_ENABLE 0}\
{CD_IO {PMC_MIO 24}} {POW_ENABLE 0} {POW_IO {PMC_MIO 17}} {RESET_ENABLE 0}\
{RESET_IO {PMC_MIO 17}} {WP_ENABLE 0} {WP_IO {PMC_MIO 25}}} PMC_SD0_COHERENCY 0\
PMC_SD0_DATA_TRANSFER_MODE 4Bit PMC_SD0_PERIPHERAL {{ENABLE 0} {IO {PMC_MIO 13\
.. 25}}} PMC_SD0_ROUTE_THROUGH_FPD 0 PMC_SD0_SLOT_TYPE {SD 2.0}\
PMC_SD0_SPEED_MODE {default speed} PMC_SD1 {{CD_ENABLE 0} {CD_IO {PMC_MIO 28}}\
{POW_ENABLE 0} {POW_IO {PMC_MIO 51}} {RESET_ENABLE 0} {RESET_IO {PMC_MIO 1}}\
{WP_ENABLE 0} {WP_IO {PMC_MIO 1}}} PMC_SD1_COHERENCY 0\
PMC_SD1_DATA_TRANSFER_MODE 8Bit PMC_SD1_PERIPHERAL {{ENABLE 0} {IO {PMC_MIO 26\
.. 36}}} PMC_SD1_ROUTE_THROUGH_FPD 0 PMC_SD1_SLOT_TYPE {SD 3.0}\
PMC_SD1_SPEED_MODE {high speed} PMC_SHOW_CCI_SMMU_SETTINGS 0\
PMC_SMAP_PERIPHERAL {{ENABLE 0} {IO {32 Bit}}} PMC_TAMPER_EXTMIO_ENABLE 0\
PMC_TAMPER_EXTMIO_ERASE_BBRAM 0 PMC_TAMPER_EXTMIO_RESPONSE {SYS INTERRUPT}\
PMC_TAMPER_GLITCHDETECT_ENABLE 0 PMC_TAMPER_GLITCHDETECT_ERASE_BBRAM 0\
PMC_TAMPER_GLITCHDETECT_RESPONSE {SYS INTERRUPT} PMC_TAMPER_JTAGDETECT_ENABLE 0\
PMC_TAMPER_JTAGDETECT_ERASE_BBRAM 0 PMC_TAMPER_JTAGDETECT_RESPONSE {SYS\
INTERRUPT} PMC_TAMPER_TEMPERATURE_ENABLE 0 PMC_TAMPER_TEMPERATURE_ERASE_BBRAM 0\
PMC_TAMPER_TEMPERATURE_RESPONSE {SYS INTERRUPT} PMC_TAMPER_TRIGGER_ERASE_BBRAM\
0 PMC_TAMPER_TRIGGER_REGISTER 0 PMC_TAMPER_TRIGGER_RESPONSE {SYS INTERRUPT}\
PMC_USE_CFU_SEU 0 PMC_USE_NOC_PMC_AXI0 0 PMC_USE_PL_PMC_AUX_REF_CLK 0\
PMC_USE_PMC_NOC_AXI0 1 PSPMC_MANUAL_CLK_ENABLE 0 PS_A72_ACTIVE_BLOCKS 2\
PS_A72_LOAD 90 PS_BANK_2_IO_STANDARD LVCMOS1.8 PS_BANK_3_IO_STANDARD LVCMOS1.8\
PS_BOARD_INTERFACE Custom PS_CAN0_CLK {{ENABLE 0} {IO {PMC_MIO 0}}}\
PS_CAN0_PERIPHERAL {{ENABLE 0} {IO {PMC_MIO 8 .. 9}}} PS_CAN1_CLK {{ENABLE 0}\
{IO {PMC_MIO 0}}} PS_CAN1_PERIPHERAL {{ENABLE 0} {IO {PMC_MIO 40 .. 41}}}\
PS_CRF_ACPU_CTRL_ACT_FREQMHZ 1349.986450 PS_CRF_ACPU_CTRL_DIVISOR0 1\
PS_CRF_ACPU_CTRL_FREQMHZ 1350 PS_CRF_ACPU_CTRL_SRCSEL APLL\
PS_CRF_APLL_CTRL_CLKOUTDIV 2 PS_CRF_APLL_CTRL_FBDIV 81 PS_CRF_APLL_CTRL_SRCSEL\
REF_CLK PS_CRF_APLL_TO_XPD_CTRL_DIVISOR0 1 PS_CRF_DBG_FPD_CTRL_ACT_FREQMHZ\
399.996002 PS_CRF_DBG_FPD_CTRL_DIVISOR0 3 PS_CRF_DBG_FPD_CTRL_FREQMHZ 400\
PS_CRF_DBG_FPD_CTRL_SRCSEL PPLL PS_CRF_DBG_TRACE_CTRL_ACT_FREQMHZ 300\
PS_CRF_DBG_TRACE_CTRL_DIVISOR0 3 PS_CRF_DBG_TRACE_CTRL_FREQMHZ 300\
PS_CRF_DBG_TRACE_CTRL_SRCSEL PPLL PS_CRF_FPD_LSBUS_CTRL_ACT_FREQMHZ 149.998505\
PS_CRF_FPD_LSBUS_CTRL_DIVISOR0 8 PS_CRF_FPD_LSBUS_CTRL_FREQMHZ 150\
PS_CRF_FPD_LSBUS_CTRL_SRCSEL PPLL PS_CRF_FPD_TOP_SWITCH_CTRL_ACT_FREQMHZ\
824.991760 PS_CRF_FPD_TOP_SWITCH_CTRL_DIVISOR0 1\
PS_CRF_FPD_TOP_SWITCH_CTRL_FREQMHZ 825 PS_CRF_FPD_TOP_SWITCH_CTRL_SRCSEL RPLL\
PS_CRL_CAN0_REF_CTRL_ACT_FREQMHZ 100 PS_CRL_CAN0_REF_CTRL_DIVISOR0 12\
PS_CRL_CAN0_REF_CTRL_FREQMHZ 100 PS_CRL_CAN0_REF_CTRL_SRCSEL PPLL\
PS_CRL_CAN1_REF_CTRL_ACT_FREQMHZ 100 PS_CRL_CAN1_REF_CTRL_DIVISOR0 12\
PS_CRL_CAN1_REF_CTRL_FREQMHZ 100 PS_CRL_CAN1_REF_CTRL_SRCSEL PPLL\
PS_CRL_CPM_TOPSW_REF_CTRL_ACT_FREQMHZ 824.991760\
PS_CRL_CPM_TOPSW_REF_CTRL_DIVISOR0 2 PS_CRL_CPM_TOPSW_REF_CTRL_FREQMHZ 825\
PS_CRL_CPM_TOPSW_REF_CTRL_SRCSEL RPLL PS_CRL_CPU_R5_CTRL_ACT_FREQMHZ 599.994019\
PS_CRL_CPU_R5_CTRL_DIVISOR0 2 PS_CRL_CPU_R5_CTRL_FREQMHZ 600\
PS_CRL_CPU_R5_CTRL_SRCSEL PPLL PS_CRL_DBG_LPD_CTRL_ACT_FREQMHZ 399.996002\
PS_CRL_DBG_LPD_CTRL_DIVISOR0 3 PS_CRL_DBG_LPD_CTRL_FREQMHZ 400\
PS_CRL_DBG_LPD_CTRL_SRCSEL PPLL PS_CRL_DBG_TSTMP_CTRL_ACT_FREQMHZ 399.996002\
PS_CRL_DBG_TSTMP_CTRL_DIVISOR0 3 PS_CRL_DBG_TSTMP_CTRL_FREQMHZ 400\
PS_CRL_DBG_TSTMP_CTRL_SRCSEL PPLL PS_CRL_GEM0_REF_CTRL_ACT_FREQMHZ 125\
PS_CRL_GEM0_REF_CTRL_DIVISOR0 4 PS_CRL_GEM0_REF_CTRL_FREQMHZ 125\
PS_CRL_GEM0_REF_CTRL_SRCSEL NPLL PS_CRL_GEM1_REF_CTRL_ACT_FREQMHZ 125\
PS_CRL_GEM1_REF_CTRL_DIVISOR0 4 PS_CRL_GEM1_REF_CTRL_FREQMHZ 125\
PS_CRL_GEM1_REF_CTRL_SRCSEL NPLL PS_CRL_GEM_TSU_REF_CTRL_ACT_FREQMHZ 250\
PS_CRL_GEM_TSU_REF_CTRL_DIVISOR0 2 PS_CRL_GEM_TSU_REF_CTRL_FREQMHZ 250\
PS_CRL_GEM_TSU_REF_CTRL_SRCSEL NPLL PS_CRL_I2C0_REF_CTRL_ACT_FREQMHZ 100\
PS_CRL_I2C0_REF_CTRL_DIVISOR0 12 PS_CRL_I2C0_REF_CTRL_FREQMHZ 100\
PS_CRL_I2C0_REF_CTRL_SRCSEL PPLL PS_CRL_I2C1_REF_CTRL_ACT_FREQMHZ 100\
PS_CRL_I2C1_REF_CTRL_DIVISOR0 12 PS_CRL_I2C1_REF_CTRL_FREQMHZ 100\
PS_CRL_I2C1_REF_CTRL_SRCSEL PPLL PS_CRL_IOU_SWITCH_CTRL_ACT_FREQMHZ 249.997498\
PS_CRL_IOU_SWITCH_CTRL_DIVISOR0 4 PS_CRL_IOU_SWITCH_CTRL_FREQMHZ 250\
PS_CRL_IOU_SWITCH_CTRL_SRCSEL NPLL PS_CRL_LPD_LSBUS_CTRL_ACT_FREQMHZ 149.998505\
PS_CRL_LPD_LSBUS_CTRL_DIVISOR0 8 PS_CRL_LPD_LSBUS_CTRL_FREQMHZ 150\
PS_CRL_LPD_LSBUS_CTRL_SRCSEL PPLL PS_CRL_LPD_TOP_SWITCH_CTRL_ACT_FREQMHZ\
599.994019 PS_CRL_LPD_TOP_SWITCH_CTRL_DIVISOR0 2\
PS_CRL_LPD_TOP_SWITCH_CTRL_FREQMHZ 600 PS_CRL_LPD_TOP_SWITCH_CTRL_SRCSEL PPLL\
PS_CRL_PSM_REF_CTRL_ACT_FREQMHZ 399.996002 PS_CRL_PSM_REF_CTRL_DIVISOR0 3\
PS_CRL_PSM_REF_CTRL_FREQMHZ 400 PS_CRL_PSM_REF_CTRL_SRCSEL PPLL\
PS_CRL_RPLL_CTRL_CLKOUTDIV 2 PS_CRL_RPLL_CTRL_FBDIV 99 PS_CRL_RPLL_CTRL_SRCSEL\
REF_CLK PS_CRL_RPLL_TO_XPD_CTRL_DIVISOR0 2 PS_CRL_SPI0_REF_CTRL_ACT_FREQMHZ 200\
PS_CRL_SPI0_REF_CTRL_DIVISOR0 6 PS_CRL_SPI0_REF_CTRL_FREQMHZ 200\
PS_CRL_SPI0_REF_CTRL_SRCSEL PPLL PS_CRL_SPI1_REF_CTRL_ACT_FREQMHZ 200\
PS_CRL_SPI1_REF_CTRL_DIVISOR0 6 PS_CRL_SPI1_REF_CTRL_FREQMHZ 200\
PS_CRL_SPI1_REF_CTRL_SRCSEL PPLL PS_CRL_TIMESTAMP_REF_CTRL_ACT_FREQMHZ\
99.999001 PS_CRL_TIMESTAMP_REF_CTRL_DIVISOR0 12\
PS_CRL_TIMESTAMP_REF_CTRL_FREQMHZ 100 PS_CRL_TIMESTAMP_REF_CTRL_SRCSEL PPLL\
PS_CRL_UART0_REF_CTRL_ACT_FREQMHZ 100 PS_CRL_UART0_REF_CTRL_DIVISOR0 12\
PS_CRL_UART0_REF_CTRL_FREQMHZ 100 PS_CRL_UART0_REF_CTRL_SRCSEL PPLL\
PS_CRL_UART1_REF_CTRL_ACT_FREQMHZ 100 PS_CRL_UART1_REF_CTRL_DIVISOR0 12\
PS_CRL_UART1_REF_CTRL_FREQMHZ 100 PS_CRL_UART1_REF_CTRL_SRCSEL PPLL\
PS_CRL_USB0_BUS_REF_CTRL_ACT_FREQMHZ 20 PS_CRL_USB0_BUS_REF_CTRL_DIVISOR0 60\
PS_CRL_USB0_BUS_REF_CTRL_FREQMHZ 20 PS_CRL_USB0_BUS_REF_CTRL_SRCSEL PPLL\
PS_CRL_USB3_DUAL_REF_CTRL_ACT_FREQMHZ 100 PS_CRL_USB3_DUAL_REF_CTRL_DIVISOR0\
100 PS_CRL_USB3_DUAL_REF_CTRL_FREQMHZ 100 PS_CRL_USB3_DUAL_REF_CTRL_SRCSEL PPLL\
PS_DDRC_ENABLE 1 PS_DDR_RAM_HIGHADDR_OFFSET 34359738368\
PS_DDR_RAM_LOWADDR_OFFSET 2147483648 PS_ENABLE_HSDP 0 PS_ENET0_MDIO {{ENABLE 0}\
{IO {PS_MIO 24 .. 25}}} PS_ENET0_PERIPHERAL {{ENABLE 0} {IO {PS_MIO 0 .. 11}}}\
PS_ENET1_MDIO {{ENABLE 0} {IO {PMC_MIO 50 .. 51}}} PS_ENET1_PERIPHERAL {{ENABLE\
0} {IO {PS_MIO 12 .. 23}}} PS_EN_AXI_STATUS_PORTS 0\
PS_EN_PORTS_CONTROLLER_BASED 0 PS_EXPAND_CORESIGHT 0 PS_EXPAND_FPD_SLAVES 0\
PS_EXPAND_GIC 0 PS_EXPAND_LPD_SLAVES 0 PS_FPD_INTERCONNECT_LOAD 90\
PS_FTM_CTI_IN0 0 PS_FTM_CTI_IN1 0 PS_FTM_CTI_IN2 0 PS_FTM_CTI_IN3 0\
PS_FTM_CTI_OUT0 0 PS_FTM_CTI_OUT1 0 PS_FTM_CTI_OUT2 0 PS_FTM_CTI_OUT3 0\
PS_GEM0_COHERENCY 0 PS_GEM0_ROUTE_THROUGH_FPD 0 PS_GEM1_COHERENCY 0\
PS_GEM1_ROUTE_THROUGH_FPD 0 PS_GEM_TSU {{ENABLE 0} {IO {PS_MIO 24}}}\
PS_GEM_TSU_CLK_PORT_PAIR 0 PS_GEN_IPI0_ENABLE 0 PS_GEN_IPI0_MASTER A72\
PS_GEN_IPI1_ENABLE 0 PS_GEN_IPI1_MASTER A72 PS_GEN_IPI2_ENABLE 0\
PS_GEN_IPI2_MASTER A72 PS_GEN_IPI3_ENABLE 0 PS_GEN_IPI3_MASTER A72\
PS_GEN_IPI4_ENABLE 0 PS_GEN_IPI4_MASTER A72 PS_GEN_IPI5_ENABLE 0\
PS_GEN_IPI5_MASTER A72 PS_GEN_IPI6_ENABLE 0 PS_GEN_IPI6_MASTER A72\
PS_GEN_IPI_PMCNOBUF_ENABLE 1 PS_GEN_IPI_PMCNOBUF_MASTER PMC\
PS_GEN_IPI_PMC_ENABLE 1 PS_GEN_IPI_PMC_MASTER PMC PS_GEN_IPI_PSM_ENABLE 1\
PS_GEN_IPI_PSM_MASTER PSM PS_GPIO2_MIO_PERIPHERAL {{ENABLE 0} {IO {PS_MIO 0 ..\
25}}} PS_GPIO_EMIO_PERIPHERAL_ENABLE 0 PS_GPIO_EMIO_WIDTH 32 PS_HSDP0_REFCLK 0\
PS_HSDP1_REFCLK 0 PS_HSDP_EGRESS_TRAFFIC JTAG PS_HSDP_INGRESS_TRAFFIC JTAG\
PS_HSDP_MODE NONE PS_HSDP_SAME_EGRESS_AS_INGRESS_TRAFFIC 1\
PS_HSDP_SAME_INGRESS_EGRESS_TRAFFIC JTAG PS_I2C0_PERIPHERAL {{ENABLE 0} {IO\
{PS_MIO 2 .. 3}}} PS_I2C1_PERIPHERAL {{ENABLE 0} {IO {PMC_MIO 44 .. 45}}}\
PS_I2CSYSMON_PERIPHERAL {{ENABLE 0} {IO {PS_MIO 23 .. 25}}} PS_IRQ_USAGE {{CH0\
0} {CH1 0} {CH10 0} {CH11 0} {CH12 0} {CH13 0} {CH14 0} {CH15 0} {CH2 0} {CH3\
0} {CH4 0} {CH5 0} {CH6 0} {CH7 0} {CH8 0} {CH9 0}} PS_LPDMA0_COHERENCY 0\
PS_LPDMA0_ROUTE_THROUGH_FPD 0 PS_LPDMA1_COHERENCY 0 PS_LPDMA1_ROUTE_THROUGH_FPD\
0 PS_LPDMA2_COHERENCY 0 PS_LPDMA2_ROUTE_THROUGH_FPD 0 PS_LPDMA3_COHERENCY 0\
PS_LPDMA3_ROUTE_THROUGH_FPD 0 PS_LPDMA4_COHERENCY 0 PS_LPDMA4_ROUTE_THROUGH_FPD\
0 PS_LPDMA5_COHERENCY 0 PS_LPDMA5_ROUTE_THROUGH_FPD 0 PS_LPDMA6_COHERENCY 0\
PS_LPDMA6_ROUTE_THROUGH_FPD 0 PS_LPDMA7_COHERENCY 0 PS_LPDMA7_ROUTE_THROUGH_FPD\
0 PS_LPD_DMA_CHANNEL_ENABLE {{CH0 0} {CH1 0} {CH2 0} {CH3 0} {CH4 0} {CH5 0}\
{CH6 0} {CH7 0}} PS_LPD_DMA_CH_TZ {{CH0 NonSecure} {CH1 NonSecure} {CH2\
NonSecure} {CH3 NonSecure} {CH4 NonSecure} {CH5 NonSecure} {CH6 NonSecure} {CH7\
NonSecure}} PS_LPD_DMA_ENABLE 0 PS_LPD_INTERCONNECT_LOAD 90 PS_MIO0 {{AUX_IO 0}\
{DIRECTION out} {DRIVE_STRENGTH 8mA} {OUTPUT_DATA default} {PULL pullup}\
{SCHMITT 1} {SLEW slow} {USAGE Unassigned}} PS_MIO1 {{AUX_IO 0} {DIRECTION out}\
{DRIVE_STRENGTH 8mA} {OUTPUT_DATA default} {PULL pullup} {SCHMITT 1} {SLEW\
slow} {USAGE Unassigned}} PS_MIO10 {{AUX_IO 0} {DIRECTION in} {DRIVE_STRENGTH\
8mA} {OUTPUT_DATA default} {PULL pullup} {SCHMITT 0} {SLEW slow} {USAGE\
Unassigned}} PS_MIO11 {{AUX_IO 0} {DIRECTION in} {DRIVE_STRENGTH 8mA}\
{OUTPUT_DATA default} {PULL pullup} {SCHMITT 0} {SLEW slow} {USAGE Unassigned}}\
PS_MIO12 {{AUX_IO 0} {DIRECTION out} {DRIVE_STRENGTH 8mA} {OUTPUT_DATA default}\
{PULL pullup} {SCHMITT 1} {SLEW slow} {USAGE Unassigned}} PS_MIO13 {{AUX_IO 0}\
{DIRECTION out} {DRIVE_STRENGTH 8mA} {OUTPUT_DATA default} {PULL pullup}\
{SCHMITT 1} {SLEW slow} {USAGE Unassigned}} PS_MIO14 {{AUX_IO 0} {DIRECTION\
out} {DRIVE_STRENGTH 8mA} {OUTPUT_DATA default} {PULL pullup} {SCHMITT 1} {SLEW\
slow} {USAGE Unassigned}} PS_MIO15 {{AUX_IO 0} {DIRECTION out} {DRIVE_STRENGTH\
8mA} {OUTPUT_DATA default} {PULL pullup} {SCHMITT 1} {SLEW slow} {USAGE\
Unassigned}} PS_MIO16 {{AUX_IO 0} {DIRECTION out} {DRIVE_STRENGTH 8mA}\
{OUTPUT_DATA default} {PULL pullup} {SCHMITT 1} {SLEW slow} {USAGE Unassigned}}\
PS_MIO17 {{AUX_IO 0} {DIRECTION out} {DRIVE_STRENGTH 8mA} {OUTPUT_DATA default}\
{PULL pullup} {SCHMITT 1} {SLEW slow} {USAGE Unassigned}} PS_MIO18 {{AUX_IO 0}\
{DIRECTION in} {DRIVE_STRENGTH 8mA} {OUTPUT_DATA default} {PULL pullup}\
{SCHMITT 0} {SLEW slow} {USAGE Unassigned}} PS_MIO19 {{AUX_IO 0} {DIRECTION in}\
{DRIVE_STRENGTH 8mA} {OUTPUT_DATA default} {PULL disable} {SCHMITT 0} {SLEW\
slow} {USAGE Unassigned}} PS_MIO2 {{AUX_IO 0} {DIRECTION out} {DRIVE_STRENGTH\
8mA} {OUTPUT_DATA default} {PULL pullup} {SCHMITT 1} {SLEW slow} {USAGE\
Unassigned}} PS_MIO20 {{AUX_IO 0} {DIRECTION in} {DRIVE_STRENGTH 8mA}\
{OUTPUT_DATA default} {PULL pullup} {SCHMITT 0} {SLEW slow} {USAGE Unassigned}}\
PS_MIO21 {{AUX_IO 0} {DIRECTION in} {DRIVE_STRENGTH 8mA} {OUTPUT_DATA default}\
{PULL disable} {SCHMITT 0} {SLEW slow} {USAGE Unassigned}} PS_MIO22 {{AUX_IO 0}\
{DIRECTION in} {DRIVE_STRENGTH 8mA} {OUTPUT_DATA default} {PULL pullup}\
{SCHMITT 0} {SLEW slow} {USAGE Unassigned}} PS_MIO23 {{AUX_IO 0} {DIRECTION in}\
{DRIVE_STRENGTH 8mA} {OUTPUT_DATA default} {PULL pullup} {SCHMITT 0} {SLEW\
slow} {USAGE Unassigned}} PS_MIO24 {{AUX_IO 0} {DIRECTION out} {DRIVE_STRENGTH\
8mA} {OUTPUT_DATA default} {PULL pullup} {SCHMITT 1} {SLEW slow} {USAGE\
Unassigned}} PS_MIO25 {{AUX_IO 0} {DIRECTION inout} {DRIVE_STRENGTH 8mA}\
{OUTPUT_DATA default} {PULL pullup} {SCHMITT 0} {SLEW slow} {USAGE Unassigned}}\
PS_MIO3 {{AUX_IO 0} {DIRECTION out} {DRIVE_STRENGTH 8mA} {OUTPUT_DATA default}\
{PULL pullup} {SCHMITT 1} {SLEW slow} {USAGE Unassigned}} PS_MIO4 {{AUX_IO 0}\
{DIRECTION out} {DRIVE_STRENGTH 8mA} {OUTPUT_DATA default} {PULL pullup}\
{SCHMITT 1} {SLEW slow} {USAGE Unassigned}} PS_MIO5 {{AUX_IO 0} {DIRECTION out}\
{DRIVE_STRENGTH 8mA} {OUTPUT_DATA default} {PULL pullup} {SCHMITT 1} {SLEW\
slow} {USAGE Unassigned}} PS_MIO6 {{AUX_IO 0} {DIRECTION in} {DRIVE_STRENGTH\
8mA} {OUTPUT_DATA default} {PULL pullup} {SCHMITT 0} {SLEW slow} {USAGE\
Unassigned}} PS_MIO7 {{AUX_IO 0} {DIRECTION in} {DRIVE_STRENGTH 8mA}\
{OUTPUT_DATA default} {PULL disable} {SCHMITT 0} {SLEW slow} {USAGE\
Unassigned}} PS_MIO8 {{AUX_IO 0} {DIRECTION in} {DRIVE_STRENGTH 8mA}\
{OUTPUT_DATA default} {PULL pullup} {SCHMITT 0} {SLEW slow} {USAGE Unassigned}}\
PS_MIO9 {{AUX_IO 0} {DIRECTION in} {DRIVE_STRENGTH 8mA} {OUTPUT_DATA default}\
{PULL disable} {SCHMITT 0} {SLEW slow} {USAGE Unassigned}}\
PS_M_AXI_FPD_DATA_WIDTH 128 PS_M_AXI_GP4_DATA_WIDTH 128 PS_M_AXI_LPD_DATA_WIDTH\
128 PS_NOC_PS_CCI_DATA_WIDTH 128 PS_NOC_PS_NCI_DATA_WIDTH 128\
PS_NOC_PS_PCI_DATA_WIDTH 128 PS_NOC_PS_PMC_DATA_WIDTH 128\
PS_NUM_F2P0_INTR_INPUTS 1 PS_NUM_F2P1_INTR_INPUTS 1 PS_NUM_FABRIC_RESETS 1\
PS_OCM_ACTIVE_BLOCKS 1 PS_PCIE1_PERIPHERAL_ENABLE 0 PS_PCIE2_PERIPHERAL_ENABLE\
0 PS_PCIE_EP_RESET1_IO None PS_PCIE_EP_RESET2_IO None PS_PCIE_PERIPHERAL_ENABLE\
0 PS_PCIE_RESET {{ENABLE 0} {IO {PS_MIO 18 .. 19}}} PS_PCIE_ROOT_RESET1_IO None\
PS_PCIE_ROOT_RESET1_POLARITY {Active Low} PS_PCIE_ROOT_RESET2_IO None\
PS_PCIE_ROOT_RESET2_POLARITY {Active Low} PS_PL_DONE 0 PS_PMCPL_CLK0_BUF 1\
PS_PMCPL_CLK1_BUF 1 PS_PMCPL_CLK2_BUF 1 PS_PMCPL_CLK3_BUF 1\
PS_PMCPL_IRO_CLK_BUF 1 PS_PMU_PERIPHERAL_ENABLE 0 PS_PS_ENABLE 0\
PS_PS_NOC_CCI_DATA_WIDTH 128 PS_PS_NOC_NCI_DATA_WIDTH 128\
PS_PS_NOC_PCI_DATA_WIDTH 128 PS_PS_NOC_PMC_DATA_WIDTH 128\
PS_PS_NOC_RPU_DATA_WIDTH 128 PS_R5_ACTIVE_BLOCKS 2 PS_R5_LOAD 90\
PS_RPU_COHERENCY 0 PS_SLR_TYPE master PS_SMON_PL_PORTS_ENABLE 0 PS_SPI0\
{{GRP_SS0_ENABLE 0} {GRP_SS0_IO {PMC_MIO 15}} {GRP_SS1_ENABLE 0} {GRP_SS1_IO\
{PMC_MIO 14}} {GRP_SS2_ENABLE 0} {GRP_SS2_IO {PMC_MIO 13}} {PERIPHERAL_ENABLE\
0} {PERIPHERAL_IO {PMC_MIO 12 .. 17}}} PS_SPI1 {{GRP_SS0_ENABLE 0} {GRP_SS0_IO\
{PS_MIO 9}} {GRP_SS1_ENABLE 0} {GRP_SS1_IO {PS_MIO 8}} {GRP_SS2_ENABLE 0}\
{GRP_SS2_IO {PS_MIO 7}} {PERIPHERAL_ENABLE 0} {PERIPHERAL_IO {PS_MIO 6 .. 11}}}\
PS_S_AXI_ACE_DATA_WIDTH 128 PS_S_AXI_ACP_DATA_WIDTH 128 PS_S_AXI_FPD_DATA_WIDTH\
128 PS_S_AXI_GP2_DATA_WIDTH 128 PS_S_AXI_LPD_DATA_WIDTH 128\
PS_TCM_ACTIVE_BLOCKS 2 PS_TRACE_PERIPHERAL {{ENABLE 0} {IO {PMC_MIO 30 .. 47}}}\
PS_TRACE_WIDTH 32Bit PS_TRISTATE_INVERTED 0 PS_TTC0_CLK {{ENABLE 0} {IO {PS_MIO\
6}}} PS_TTC0_PERIPHERAL_ENABLE 1 PS_TTC0_REF_CTRL_ACT_FREQMHZ 149.998505\
PS_TTC0_REF_CTRL_FREQMHZ 149.998505 PS_TTC0_WAVEOUT {{ENABLE 0} {IO {PS_MIO\
7}}} PS_TTC1_CLK {{ENABLE 0} {IO {PS_MIO 12}}} PS_TTC1_PERIPHERAL_ENABLE 0\
PS_TTC1_REF_CTRL_ACT_FREQMHZ 100 PS_TTC1_REF_CTRL_FREQMHZ 100 PS_TTC1_WAVEOUT\
{{ENABLE 0} {IO {PS_MIO 13}}} PS_TTC2_CLK {{ENABLE 0} {IO {PS_MIO 2}}}\
PS_TTC2_PERIPHERAL_ENABLE 0 PS_TTC2_REF_CTRL_ACT_FREQMHZ 100\
PS_TTC2_REF_CTRL_FREQMHZ 100 PS_TTC2_WAVEOUT {{ENABLE 0} {IO {PS_MIO 3}}}\
PS_TTC3_CLK {{ENABLE 0} {IO {PS_MIO 16}}} PS_TTC3_PERIPHERAL_ENABLE 0\
PS_TTC3_REF_CTRL_ACT_FREQMHZ 100 PS_TTC3_REF_CTRL_FREQMHZ 100 PS_TTC3_WAVEOUT\
{{ENABLE 0} {IO {PS_MIO 17}}} PS_TTC_APB_CLK_TTC0_SEL APB\
PS_TTC_APB_CLK_TTC1_SEL APB PS_TTC_APB_CLK_TTC2_SEL APB PS_TTC_APB_CLK_TTC3_SEL\
APB PS_UART0_BAUD_RATE 115200 PS_UART0_PERIPHERAL {{ENABLE 0} {IO {PMC_MIO 42\
.. 43}}} PS_UART0_RTS_CTS {{ENABLE 0} {IO {PS_MIO 2 .. 3}}} PS_UART1_BAUD_RATE\
115200 PS_UART1_PERIPHERAL {{ENABLE 0} {IO {PMC_MIO 4 .. 5}}} PS_UART1_RTS_CTS\
{{ENABLE 0} {IO {PMC_MIO 6 .. 7}}} PS_USB3_PERIPHERAL {{ENABLE 0} {IO {PMC_MIO\
13 .. 25}}} PS_USB_COHERENCY 0 PS_USB_ROUTE_THROUGH_FPD 0 PS_USE_ACE_LITE 0\
PS_USE_APU_EVENT_BUS 0 PS_USE_APU_INTERRUPT 0 PS_USE_AXI4_EXT_USER_BITS 0\
PS_USE_BSCAN_USER1 0 PS_USE_BSCAN_USER2 0 PS_USE_BSCAN_USER3 0\
PS_USE_BSCAN_USER4 0 PS_USE_CAPTURE 0 PS_USE_CLK 0 PS_USE_DEBUG_TEST 0\
PS_USE_DIFF_RW_CLK_S_AXI_FPD 0 PS_USE_DIFF_RW_CLK_S_AXI_GP2 0\
PS_USE_DIFF_RW_CLK_S_AXI_LPD 0 PS_USE_ENET0_PTP 0 PS_USE_ENET1_PTP 0\
PS_USE_FIFO_ENET0 0 PS_USE_FIFO_ENET1 0 PS_USE_FPD_AXI_NOC0 0\
PS_USE_FPD_AXI_NOC1 0 PS_USE_FPD_CCI_NOC 1 PS_USE_FPD_CCI_NOC0 1\
PS_USE_FPD_CCI_NOC1 0 PS_USE_FPD_CCI_NOC2 0 PS_USE_FPD_CCI_NOC3 0\
PS_USE_FTM_GPI 0 PS_USE_FTM_GPO 0 PS_USE_HSDP_PL 0 PS_USE_M_AXI_FPD 0\
PS_USE_M_AXI_LPD 0 PS_USE_NOC_FPD_AXI0 0 PS_USE_NOC_FPD_AXI1 0\
PS_USE_NOC_FPD_CCI0 0 PS_USE_NOC_FPD_CCI1 0 PS_USE_NOC_LPD_AXI0 1\
PS_USE_NOC_PS_PCI_0 0 PS_USE_NOC_PS_PMC_0 0 PS_USE_NPI_CLK 0 PS_USE_NPI_RST 0\
PS_USE_PL_FPD_AUX_REF_CLK 0 PS_USE_PL_LPD_AUX_REF_CLK 0 PS_USE_PMC 0\
PS_USE_PMCPL_CLK0 1 PS_USE_PMCPL_CLK1 0 PS_USE_PMCPL_CLK2 0 PS_USE_PMCPL_CLK3 0\
PS_USE_PMCPL_IRO_CLK 0 PS_USE_PSPL_IRQ_FPD 0 PS_USE_PSPL_IRQ_LPD 0\
PS_USE_PSPL_IRQ_PMC 0 PS_USE_PS_NOC_PCI_0 0 PS_USE_PS_NOC_PCI_1 0\
PS_USE_PS_NOC_PMC_0 0 PS_USE_PS_NOC_PMC_1 0 PS_USE_RPU_EVENT 0\
PS_USE_RPU_INTERRUPT 0 PS_USE_RTC 0 PS_USE_SMMU 0 PS_USE_STARTUP 0 PS_USE_STM 0\
PS_USE_S_ACP_FPD 0 PS_USE_S_AXI_ACE 0 PS_USE_S_AXI_FPD 0 PS_USE_S_AXI_GP2 0\
PS_USE_S_AXI_LPD 0 PS_USE_TRACE_ATB 0 PS_WDT0_REF_CTRL_ACT_FREQMHZ 100\
PS_WDT0_REF_CTRL_FREQMHZ 100 PS_WDT0_REF_CTRL_SEL NONE\
PS_WDT1_REF_CTRL_ACT_FREQMHZ 100 PS_WDT1_REF_CTRL_FREQMHZ 100\
PS_WDT1_REF_CTRL_SEL NONE PS_WWDT0_CLK {{ENABLE 0} {IO {PMC_MIO 0}}}\
PS_WWDT0_PERIPHERAL {{ENABLE 0} {IO {PMC_MIO 0 .. 5}}} PS_WWDT1_CLK {{ENABLE 0}\
{IO {PMC_MIO 6}}} PS_WWDT1_PERIPHERAL {{ENABLE 0} {IO {PMC_MIO 6 .. 11}}}\
SEM_ERROR_HANDLE_OPTIONS {Detect & Correct} SEM_EVENT_LOG_OPTIONS {Log &\
Notify} SEM_MEM_BUILT_IN_SELF_TEST 0 SEM_MEM_ENABLE_ALL_TEST_FEATURE 0\
SEM_MEM_ENABLE_SCAN_AFTER 0 SEM_MEM_GOLDEN_ECC 0 SEM_MEM_GOLDEN_ECC_SW 0\
SEM_MEM_SCAN 0 SEM_NPI_BUILT_IN_SELF_TEST 0 SEM_NPI_ENABLE_ALL_TEST_FEATURE 0\
SEM_NPI_ENABLE_SCAN_AFTER 0 SEM_NPI_GOLDEN_CHECKSUM_SW 0 SEM_NPI_SCAN 0\
SEM_TIME_INTERVAL_BETWEEN_SCANS 0 SMON_ALARMS Set_Alarms_On\
SMON_ENABLE_INT_VOLTAGE_MONITORING 0 SMON_ENABLE_TEMP_AVERAGING 0\
SMON_INTERFACE_TO_USE None SMON_INT_MEASUREMENT_ALARM_ENABLE 0\
SMON_INT_MEASUREMENT_AVG_ENABLE 0 SMON_INT_MEASUREMENT_ENABLE 0\
SMON_INT_MEASUREMENT_MODE 0 SMON_INT_MEASUREMENT_TH_HIGH 0\
SMON_INT_MEASUREMENT_TH_LOW 0 SMON_MEAS0 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00}\
{ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE {2 V unipolar}} {NAME\
GTY_AVCCAUX_103}} SMON_MEAS1 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER\
2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE {2 V unipolar}} {NAME GTY_AVCCAUX_104}}\
SMON_MEAS10 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN\
0} {ENABLE 0} {MODE {2 V unipolar}} {NAME GTY_AVCCAUX_206}} SMON_MEAS100\
{{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE\
0} {MODE None} {NAME 0}} SMON_MEAS101 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00}\
{ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE None} {NAME 0}} SMON_MEAS102\
{{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE\
0} {MODE None} {NAME 0}} SMON_MEAS103 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00}\
{ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE None} {NAME 0}} SMON_MEAS104\
{{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE\
0} {MODE None} {NAME 0}} SMON_MEAS105 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00}\
{ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE None} {NAME 0}} SMON_MEAS106\
{{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE\
0} {MODE None} {NAME 0}} SMON_MEAS107 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00}\
{ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE None} {NAME 0}} SMON_MEAS108\
{{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE\
0} {MODE None} {NAME 0}} SMON_MEAS109 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00}\
{ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE None} {NAME 0}} SMON_MEAS11\
{{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE\
0} {MODE {2 V unipolar}} {NAME GTY_AVCC_103}} SMON_MEAS110 {{ALARM_ENABLE 0}\
{ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE None}\
{NAME 0}} SMON_MEAS111 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00}\
{AVERAGE_EN 0} {ENABLE 0} {MODE None} {NAME 0}} SMON_MEAS112 {{ALARM_ENABLE 0}\
{ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE None}\
{NAME 0}} SMON_MEAS113 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00}\
{AVERAGE_EN 0} {ENABLE 0} {MODE None} {NAME 0}} SMON_MEAS114 {{ALARM_ENABLE 0}\
{ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE None}\
{NAME 0}} SMON_MEAS115 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00}\
{AVERAGE_EN 0} {ENABLE 0} {MODE None} {NAME 0}} SMON_MEAS116 {{ALARM_ENABLE 0}\
{ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE None}\
{NAME 0}} SMON_MEAS117 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00}\
{AVERAGE_EN 0} {ENABLE 0} {MODE None} {NAME 0}} SMON_MEAS118 {{ALARM_ENABLE 0}\
{ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE None}\
{NAME 0}} SMON_MEAS119 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00}\
{AVERAGE_EN 0} {ENABLE 0} {MODE None} {NAME 0}} SMON_MEAS12 {{ALARM_ENABLE 0}\
{ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE {2 V\
unipolar}} {NAME GTY_AVCC_104}} SMON_MEAS120 {{ALARM_ENABLE 0} {ALARM_LOWER\
0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE None} {NAME 0}}\
SMON_MEAS121 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00}\
{AVERAGE_EN 0} {ENABLE 0} {MODE None} {NAME 0}} SMON_MEAS122 {{ALARM_ENABLE 0}\
{ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE None}\
{NAME 0}} SMON_MEAS123 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00}\
{AVERAGE_EN 0} {ENABLE 0} {MODE None} {NAME 0}} SMON_MEAS124 {{ALARM_ENABLE 0}\
{ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE None}\
{NAME 0}} SMON_MEAS125 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00}\
{AVERAGE_EN 0} {ENABLE 0} {MODE None} {NAME 0}} SMON_MEAS126 {{ALARM_ENABLE 0}\
{ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE None}\
{NAME 0}} SMON_MEAS127 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00}\
{AVERAGE_EN 0} {ENABLE 0} {MODE None} {NAME 0}} SMON_MEAS128 {{ALARM_ENABLE 0}\
{ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE None}\
{NAME 0}} SMON_MEAS129 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00}\
{AVERAGE_EN 0} {ENABLE 0} {MODE None} {NAME 0}} SMON_MEAS13 {{ALARM_ENABLE 0}\
{ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE {2 V\
unipolar}} {NAME GTY_AVCC_105}} SMON_MEAS130 {{ALARM_ENABLE 0} {ALARM_LOWER\
0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE None} {NAME 0}}\
SMON_MEAS131 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00}\
{AVERAGE_EN 0} {ENABLE 0} {MODE None} {NAME 0}} SMON_MEAS132 {{ALARM_ENABLE 0}\
{ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE None}\
{NAME 0}} SMON_MEAS133 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00}\
{AVERAGE_EN 0} {ENABLE 0} {MODE None} {NAME 0}} SMON_MEAS134 {{ALARM_ENABLE 0}\
{ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE None}\
{NAME 0}} SMON_MEAS135 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00}\
{AVERAGE_EN 0} {ENABLE 0} {MODE None} {NAME 0}} SMON_MEAS136 {{ALARM_ENABLE 0}\
{ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE None}\
{NAME 0}} SMON_MEAS137 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00}\
{AVERAGE_EN 0} {ENABLE 0} {MODE None} {NAME 0}} SMON_MEAS138 {{ALARM_ENABLE 0}\
{ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE None}\
{NAME 0}} SMON_MEAS139 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00}\
{AVERAGE_EN 0} {ENABLE 0} {MODE None} {NAME 0}} SMON_MEAS14 {{ALARM_ENABLE 0}\
{ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE {2 V\
unipolar}} {NAME GTY_AVCC_106}} SMON_MEAS140 {{ALARM_ENABLE 0} {ALARM_LOWER\
0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE None} {NAME 0}}\
SMON_MEAS141 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00}\
{AVERAGE_EN 0} {ENABLE 0} {MODE None} {NAME 0}} SMON_MEAS142 {{ALARM_ENABLE 0}\
{ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE None}\
{NAME 0}} SMON_MEAS143 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00}\
{AVERAGE_EN 0} {ENABLE 0} {MODE None} {NAME 0}} SMON_MEAS144 {{ALARM_ENABLE 0}\
{ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE None}\
{NAME 0}} SMON_MEAS145 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00}\
{AVERAGE_EN 0} {ENABLE 0} {MODE None} {NAME 0}} SMON_MEAS146 {{ALARM_ENABLE 0}\
{ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE None}\
{NAME 0}} SMON_MEAS147 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00}\
{AVERAGE_EN 0} {ENABLE 0} {MODE None} {NAME 0}} SMON_MEAS148 {{ALARM_ENABLE 0}\
{ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE None}\
{NAME 0}} SMON_MEAS149 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00}\
{AVERAGE_EN 0} {ENABLE 0} {MODE None} {NAME 0}} SMON_MEAS15 {{ALARM_ENABLE 0}\
{ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE {2 V\
unipolar}} {NAME GTY_AVCC_200}} SMON_MEAS150 {{ALARM_ENABLE 0} {ALARM_LOWER\
0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE None} {NAME 0}}\
SMON_MEAS151 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00}\
{AVERAGE_EN 0} {ENABLE 0} {MODE None} {NAME 0}} SMON_MEAS152 {{ALARM_ENABLE 0}\
{ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE None}\
{NAME 0}} SMON_MEAS153 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00}\
{AVERAGE_EN 0} {ENABLE 0} {MODE None} {NAME 0}} SMON_MEAS154 {{ALARM_ENABLE 0}\
{ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE None}\
{NAME 0}} SMON_MEAS155 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00}\
{AVERAGE_EN 0} {ENABLE 0} {MODE None} {NAME 0}} SMON_MEAS156 {{ALARM_ENABLE 0}\
{ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE None}\
{NAME 0}} SMON_MEAS157 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00}\
{AVERAGE_EN 0} {ENABLE 0} {MODE None} {NAME 0}} SMON_MEAS158 {{ALARM_ENABLE 0}\
{ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE None}\
{NAME 0}} SMON_MEAS159 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00}\
{AVERAGE_EN 0} {ENABLE 0} {MODE None} {NAME 0}} SMON_MEAS16 {{ALARM_ENABLE 0}\
{ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE {2 V\
unipolar}} {NAME GTY_AVCC_201}} SMON_MEAS160 {{ALARM_ENABLE 0} {ALARM_LOWER\
0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE None} {NAME 0}}\
SMON_MEAS161 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00}\
{AVERAGE_EN 0} {ENABLE 0} {MODE None} {NAME 0}} SMON_MEAS162 {{ALARM_ENABLE 0}\
{ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE None}\
{NAME 0}} SMON_MEAS163 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00}\
{AVERAGE_EN 0} {ENABLE 0} {MODE None} {NAME 0}} SMON_MEAS164 {{ALARM_ENABLE 0}\
{ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE None}\
{NAME 0}} SMON_MEAS165 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00}\
{AVERAGE_EN 0} {ENABLE 0} {MODE None} {NAME 0}} SMON_MEAS166 {{ALARM_ENABLE 0}\
{ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE None}\
{NAME 0}} SMON_MEAS167 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00}\
{AVERAGE_EN 0} {ENABLE 0} {MODE None} {NAME 0}} SMON_MEAS168 {{ALARM_ENABLE 0}\
{ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE None}\
{NAME 0}} SMON_MEAS169 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00}\
{AVERAGE_EN 0} {ENABLE 0} {MODE None} {NAME 0}} SMON_MEAS17 {{ALARM_ENABLE 0}\
{ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE {2 V\
unipolar}} {NAME GTY_AVCC_202}} SMON_MEAS170 {{ALARM_ENABLE 0} {ALARM_LOWER\
0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE None} {NAME 0}}\
SMON_MEAS171 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00}\
{AVERAGE_EN 0} {ENABLE 0} {MODE None} {NAME 0}} SMON_MEAS172 {{ALARM_ENABLE 0}\
{ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE None}\
{NAME 0}} SMON_MEAS173 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00}\
{AVERAGE_EN 0} {ENABLE 0} {MODE None} {NAME 0}} SMON_MEAS174 {{ALARM_ENABLE 0}\
{ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE None}\
{NAME 0}} SMON_MEAS175 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00}\
{AVERAGE_EN 0} {ENABLE 0} {MODE None} {NAME 0}} SMON_MEAS18 {{ALARM_ENABLE 0}\
{ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE {2 V\
unipolar}} {NAME GTY_AVCC_203}} SMON_MEAS19 {{ALARM_ENABLE 0} {ALARM_LOWER\
0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE {2 V unipolar}} {NAME\
GTY_AVCC_204}} SMON_MEAS2 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER\
2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE {2 V unipolar}} {NAME GTY_AVCCAUX_105}}\
SMON_MEAS20 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN\
0} {ENABLE 0} {MODE {2 V unipolar}} {NAME GTY_AVCC_205}} SMON_MEAS21\
{{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE\
0} {MODE {2 V unipolar}} {NAME GTY_AVCC_206}} SMON_MEAS22 {{ALARM_ENABLE 0}\
{ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE {2 V\
unipolar}} {NAME GTY_AVTT_103}} SMON_MEAS23 {{ALARM_ENABLE 0} {ALARM_LOWER\
0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE {2 V unipolar}} {NAME\
GTY_AVTT_104}} SMON_MEAS24 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER\
2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE {2 V unipolar}} {NAME GTY_AVTT_105}}\
SMON_MEAS25 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN\
0} {ENABLE 0} {MODE {2 V unipolar}} {NAME GTY_AVTT_106}} SMON_MEAS26\
{{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE\
0} {MODE {2 V unipolar}} {NAME GTY_AVTT_200}} SMON_MEAS27 {{ALARM_ENABLE 0}\
{ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE {2 V\
unipolar}} {NAME GTY_AVTT_201}} SMON_MEAS28 {{ALARM_ENABLE 0} {ALARM_LOWER\
0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE {2 V unipolar}} {NAME\
GTY_AVTT_202}} SMON_MEAS29 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER\
2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE {2 V unipolar}} {NAME GTY_AVTT_203}}\
SMON_MEAS3 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN\
0} {ENABLE 0} {MODE {2 V unipolar}} {NAME GTY_AVCCAUX_106}} SMON_MEAS30\
{{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE\
0} {MODE {2 V unipolar}} {NAME GTY_AVTT_204}} SMON_MEAS31 {{ALARM_ENABLE 0}\
{ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE {2 V\
unipolar}} {NAME GTY_AVTT_205}} SMON_MEAS32 {{ALARM_ENABLE 0} {ALARM_LOWER\
0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE {2 V unipolar}} {NAME\
GTY_AVTT_206}} SMON_MEAS33 {{ALARM_ENABLE 1} {ALARM_LOWER 0.00} {ALARM_UPPER\
2.00} {AVERAGE_EN 0} {ENABLE 1} {MODE 2} {NAME VCCAUX}} SMON_MEAS34\
{{ALARM_ENABLE 1} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE\
1} {MODE 2} {NAME VCCAUX_PMC}} SMON_MEAS35 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00}\
{ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE {2 V unipolar}} {NAME\
VCCAUX_SMON}} SMON_MEAS36 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER\
2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE {2 V unipolar}} {NAME VCCINT}}\
SMON_MEAS37 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN\
0} {ENABLE 0} {MODE {4 V unipolar}} {NAME VCCO_306}} SMON_MEAS38 {{ALARM_ENABLE\
0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE {4 V\
unipolar}} {NAME VCCO_406}} SMON_MEAS39 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00}\
{ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE {4 V unipolar}} {NAME\
VCCO_500}} SMON_MEAS4 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00}\
{AVERAGE_EN 0} {ENABLE 0} {MODE {2 V unipolar}} {NAME GTY_AVCCAUX_200}}\
SMON_MEAS40 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN\
0} {ENABLE 0} {MODE {4 V unipolar}} {NAME VCCO_501}} SMON_MEAS41 {{ALARM_ENABLE\
0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE {4 V\
unipolar}} {NAME VCCO_502}} SMON_MEAS42 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00}\
{ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE {4 V unipolar}} {NAME\
VCCO_503}} SMON_MEAS43 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00}\
{AVERAGE_EN 0} {ENABLE 0} {MODE {2 V unipolar}} {NAME VCCO_700}} SMON_MEAS44\
{{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE\
0} {MODE {2 V unipolar}} {NAME VCCO_701}} SMON_MEAS45 {{ALARM_ENABLE 0}\
{ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE {2 V\
unipolar}} {NAME VCCO_702}} SMON_MEAS46 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00}\
{ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE {2 V unipolar}} {NAME\
VCCO_703}} SMON_MEAS47 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00}\
{AVERAGE_EN 0} {ENABLE 0} {MODE {2 V unipolar}} {NAME VCCO_704}} SMON_MEAS48\
{{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE\
0} {MODE {2 V unipolar}} {NAME VCCO_705}} SMON_MEAS49 {{ALARM_ENABLE 0}\
{ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE {2 V\
unipolar}} {NAME VCCO_706}} SMON_MEAS5 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00}\
{ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE {2 V unipolar}} {NAME\
GTY_AVCCAUX_201}} SMON_MEAS50 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER\
2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE {2 V unipolar}} {NAME VCCO_707}}\
SMON_MEAS51 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN\
0} {ENABLE 0} {MODE {2 V unipolar}} {NAME VCCO_708}} SMON_MEAS52 {{ALARM_ENABLE\
0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE {2 V\
unipolar}} {NAME VCCO_709}} SMON_MEAS53 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00}\
{ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE {2 V unipolar}} {NAME\
VCCO_710}} SMON_MEAS54 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00}\
{AVERAGE_EN 0} {ENABLE 0} {MODE {2 V unipolar}} {NAME VCCO_711}} SMON_MEAS55\
{{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE\
0} {MODE {2 V unipolar}} {NAME VCC_BATT}} SMON_MEAS56 {{ALARM_ENABLE 1}\
{ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 1} {MODE 2} {NAME\
VCC_PMC}} SMON_MEAS57 {{ALARM_ENABLE 1} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00}\
{AVERAGE_EN 0} {ENABLE 1} {MODE 2} {NAME VCC_PSFP}} SMON_MEAS58 {{ALARM_ENABLE\
1} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 1} {MODE 2}\
{NAME VCC_PSLP}} SMON_MEAS59 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER\
2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE {2 V unipolar}} {NAME VCC_RAM}}\
SMON_MEAS6 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN\
0} {ENABLE 0} {MODE {2 V unipolar}} {NAME GTY_AVCCAUX_202}} SMON_MEAS60\
{{ALARM_ENABLE 1} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE\
1} {MODE 2} {NAME VCC_SOC}} SMON_MEAS61 {{ALARM_ENABLE 1} {ALARM_LOWER 0.00}\
{ALARM_UPPER 0.0} {AVERAGE_EN 0} {ENABLE 1} {MODE 2} {NAME VP_VN}} SMON_MEAS62\
{{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE\
0} {MODE None} {NAME VCC_PMC}} SMON_MEAS63 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00}\
{ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE None} {NAME VCC_PSFP}}\
SMON_MEAS64 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN\
0} {ENABLE 0} {MODE None} {NAME VCC_PSLP}} SMON_MEAS65 {{ALARM_ENABLE 0}\
{ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE None}\
{NAME VCC_RAM}} SMON_MEAS66 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER\
2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE None} {NAME VCC_SOC}} SMON_MEAS67\
{{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE\
0} {MODE None} {NAME VP_VN}} SMON_MEAS68 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00}\
{ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE None} {NAME 0}} SMON_MEAS69\
{{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE\
0} {MODE None} {NAME 0}} SMON_MEAS7 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00}\
{ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE {2 V unipolar}} {NAME\
GTY_AVCCAUX_203}} SMON_MEAS70 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER\
2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE None} {NAME 0}} SMON_MEAS71\
{{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE\
0} {MODE None} {NAME 0}} SMON_MEAS72 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00}\
{ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE None} {NAME 0}} SMON_MEAS73\
{{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE\
0} {MODE None} {NAME 0}} SMON_MEAS74 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00}\
{ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE None} {NAME 0}} SMON_MEAS75\
{{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE\
0} {MODE None} {NAME 0}} SMON_MEAS76 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00}\
{ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE None} {NAME 0}} SMON_MEAS77\
{{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE\
0} {MODE None} {NAME 0}} SMON_MEAS78 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00}\
{ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE None} {NAME 0}} SMON_MEAS79\
{{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE\
0} {MODE None} {NAME 0}} SMON_MEAS8 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00}\
{ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE {2 V unipolar}} {NAME\
GTY_AVCCAUX_204}} SMON_MEAS80 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER\
2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE None} {NAME 0}} SMON_MEAS81\
{{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE\
0} {MODE None} {NAME 0}} SMON_MEAS82 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00}\
{ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE None} {NAME 0}} SMON_MEAS83\
{{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE\
0} {MODE None} {NAME 0}} SMON_MEAS84 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00}\
{ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE None} {NAME 0}} SMON_MEAS85\
{{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE\
0} {MODE None} {NAME 0}} SMON_MEAS86 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00}\
{ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE None} {NAME 0}} SMON_MEAS87\
{{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE\
0} {MODE None} {NAME 0}} SMON_MEAS88 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00}\
{ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE None} {NAME 0}} SMON_MEAS89\
{{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE\
0} {MODE None} {NAME 0}} SMON_MEAS9 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00}\
{ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE {2 V unipolar}} {NAME\
GTY_AVCCAUX_205}} SMON_MEAS90 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER\
2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE None} {NAME 0}} SMON_MEAS91\
{{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE\
0} {MODE None} {NAME 0}} SMON_MEAS92 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00}\
{ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE None} {NAME 0}} SMON_MEAS93\
{{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE\
0} {MODE None} {NAME 0}} SMON_MEAS94 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00}\
{ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE None} {NAME 0}} SMON_MEAS95\
{{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE\
0} {MODE None} {NAME 0}} SMON_MEAS96 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00}\
{ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE None} {NAME 0}} SMON_MEAS97\
{{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE\
0} {MODE None} {NAME 0}} SMON_MEAS98 {{ALARM_ENABLE 0} {ALARM_LOWER 0.00}\
{ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE 0} {MODE None} {NAME 0}} SMON_MEAS99\
{{ALARM_ENABLE 0} {ALARM_LOWER 0.00} {ALARM_UPPER 2.00} {AVERAGE_EN 0} {ENABLE\
0} {MODE None} {NAME 0}} SMON_MEASUREMENT_COUNT 62 SMON_MEASUREMENT_LIST\
BANK_VOLTAGE:GTY_AVTT-GTY_AVTT_103,GTY_AVTT_104,GTY_AVTT_105,GTY_AVTT_106,GTY_AVTT_200,GTY_AVTT_201,GTY_AVTT_202,GTY_AVTT_203,GTY_AVTT_204,GTY_AVTT_205,GTY_AVTT_206#VCC-GTY_AVCC_103,GTY_AVCC_104,GTY_AVCC_105,GTY_AVCC_106,GTY_AVCC_200,GTY_AVCC_201,GTY_AVCC_202,GTY_AVCC_203,GTY_AVCC_204,GTY_AVCC_205,GTY_AVCC_206#VCCAUX-GTY_AVCCAUX_103,GTY_AVCCAUX_104,GTY_AVCCAUX_105,GTY_AVCCAUX_106,GTY_AVCCAUX_200,GTY_AVCCAUX_201,GTY_AVCCAUX_202,GTY_AVCCAUX_203,GTY_AVCCAUX_204,GTY_AVCCAUX_205,GTY_AVCCAUX_206#VCCO-VCCO_306,VCCO_406,VCCO_500,VCCO_501,VCCO_502,VCCO_503,VCCO_700,VCCO_701,VCCO_702,VCCO_703,VCCO_704,VCCO_705,VCCO_706,VCCO_707,VCCO_708,VCCO_709,VCCO_710,VCCO_711|DEDICATED_PAD:VP-VP_VN|SUPPLY_VOLTAGE:VCC-VCC_BATT,VCC_PMC,VCC_PSFP,VCC_PSLP,VCC_RAM,VCC_SOC#VCCAUX-VCCAUX,VCCAUX_PMC,VCCAUX_SMON#VCCINT-VCCINT\
SMON_OT {{THRESHOLD_LOWER -55} {THRESHOLD_UPPER 125}} SMON_PMBUS_ADDRESS 0x0\
SMON_PMBUS_UNRESTRICTED 0 SMON_REFERENCE_SOURCE Internal\
SMON_TEMP_AVERAGING_SAMPLES 8 SMON_TEMP_THRESHOLD 0 SMON_USER_TEMP\
{{THRESHOLD_LOWER 0} {THRESHOLD_UPPER 125} {USER_ALARM_TYPE window}}\
SMON_VAUX_CH0 {{ALARM_ENABLE 0} {ALARM_LOWER 0} {ALARM_UPPER 0} {AVERAGE_EN 0}\
{ENABLE 0} {IO_N PMC_MIO1_500} {IO_P PMC_MIO0_500} {MODE {1 V unipolar}} {NAME\
VAUX_CH0}} SMON_VAUX_CH1 {{ALARM_ENABLE 0} {ALARM_LOWER 0} {ALARM_UPPER 0}\
{AVERAGE_EN 0} {ENABLE 0} {IO_N PMC_MIO1_500} {IO_P PMC_MIO0_500} {MODE {1 V\
unipolar}} {NAME VAUX_CH1}} SMON_VAUX_CH10 {{ALARM_ENABLE 0} {ALARM_LOWER 0}\
{ALARM_UPPER 0} {AVERAGE_EN 0} {ENABLE 0} {IO_N PMC_MIO1_500} {IO_P\
PMC_MIO0_500} {MODE {1 V unipolar}} {NAME VAUX_CH10}} SMON_VAUX_CH11\
{{ALARM_ENABLE 0} {ALARM_LOWER 0} {ALARM_UPPER 0} {AVERAGE_EN 0} {ENABLE 0}\
{IO_N PMC_MIO1_500} {IO_P PMC_MIO0_500} {MODE {1 V unipolar}} {NAME VAUX_CH11}}\
SMON_VAUX_CH12 {{ALARM_ENABLE 0} {ALARM_LOWER 0} {ALARM_UPPER 0} {AVERAGE_EN 0}\
{ENABLE 0} {IO_N PMC_MIO1_500} {IO_P PMC_MIO0_500} {MODE {1 V unipolar}} {NAME\
VAUX_CH12}} SMON_VAUX_CH13 {{ALARM_ENABLE 0} {ALARM_LOWER 0} {ALARM_UPPER 0}\
{AVERAGE_EN 0} {ENABLE 0} {IO_N PMC_MIO1_500} {IO_P PMC_MIO0_500} {MODE {1 V\
unipolar}} {NAME VAUX_CH13}} SMON_VAUX_CH14 {{ALARM_ENABLE 0} {ALARM_LOWER 0}\
{ALARM_UPPER 0} {AVERAGE_EN 0} {ENABLE 0} {IO_N PMC_MIO1_500} {IO_P\
PMC_MIO0_500} {MODE {1 V unipolar}} {NAME VAUX_CH14}} SMON_VAUX_CH15\
{{ALARM_ENABLE 0} {ALARM_LOWER 0} {ALARM_UPPER 0} {AVERAGE_EN 0} {ENABLE 0}\
{IO_N PMC_MIO1_500} {IO_P PMC_MIO0_500} {MODE {1 V unipolar}} {NAME VAUX_CH15}}\
SMON_VAUX_CH2 {{ALARM_ENABLE 0} {ALARM_LOWER 0} {ALARM_UPPER 0} {AVERAGE_EN 0}\
{ENABLE 0} {IO_N PMC_MIO1_500} {IO_P PMC_MIO0_500} {MODE {1 V unipolar}} {NAME\
VAUX_CH2}} SMON_VAUX_CH3 {{ALARM_ENABLE 0} {ALARM_LOWER 0} {ALARM_UPPER 0}\
{AVERAGE_EN 0} {ENABLE 0} {IO_N PMC_MIO1_500} {IO_P PMC_MIO0_500} {MODE {1 V\
unipolar}} {NAME VAUX_CH3}} SMON_VAUX_CH4 {{ALARM_ENABLE 0} {ALARM_LOWER 0}\
{ALARM_UPPER 0} {AVERAGE_EN 0} {ENABLE 0} {IO_N PMC_MIO1_500} {IO_P\
PMC_MIO0_500} {MODE {1 V unipolar}} {NAME VAUX_CH4}} SMON_VAUX_CH5\
{{ALARM_ENABLE 0} {ALARM_LOWER 0} {ALARM_UPPER 0} {AVERAGE_EN 0} {ENABLE 0}\
{IO_N PMC_MIO1_500} {IO_P PMC_MIO0_500} {MODE {1 V unipolar}} {NAME VAUX_CH5}}\
SMON_VAUX_CH6 {{ALARM_ENABLE 0} {ALARM_LOWER 0} {ALARM_UPPER 0} {AVERAGE_EN 0}\
{ENABLE 0} {IO_N PMC_MIO1_500} {IO_P PMC_MIO0_500} {MODE {1 V unipolar}} {NAME\
VAUX_CH6}} SMON_VAUX_CH7 {{ALARM_ENABLE 0} {ALARM_LOWER 0} {ALARM_UPPER 0}\
{AVERAGE_EN 0} {ENABLE 0} {IO_N PMC_MIO1_500} {IO_P PMC_MIO0_500} {MODE {1 V\
unipolar}} {NAME VAUX_CH7}} SMON_VAUX_CH8 {{ALARM_ENABLE 0} {ALARM_LOWER 0}\
{ALARM_UPPER 0} {AVERAGE_EN 0} {ENABLE 0} {IO_N PMC_MIO1_500} {IO_P\
PMC_MIO0_500} {MODE {1 V unipolar}} {NAME VAUX_CH8}} SMON_VAUX_CH9\
{{ALARM_ENABLE 0} {ALARM_LOWER 0} {ALARM_UPPER 0} {AVERAGE_EN 0} {ENABLE 0}\
{IO_N PMC_MIO1_500} {IO_P PMC_MIO0_500} {MODE {1 V unipolar}} {NAME VAUX_CH9}}\
SMON_VAUX_IO_BANK MIO_BANK0 SMON_VOLTAGE_AVERAGING_SAMPLES None\
SPP_PSPMC_FROM_CORE_WIDTH 12000 SPP_PSPMC_TO_CORE_WIDTH 12000 SUBPRESET1 Custom\
USE_UART0_IN_DEVICE_BOOT 0}\
   CONFIG.PS_PMC_CONFIG_APPLIED {1} \
 ] $versal_cips_0

  # Create interface connections
  connect_bd_intf_net -intf_net axi_noc_0_CH0_DDR4_0 [get_bd_intf_ports ddr4_dimm1] [get_bd_intf_pins axi_noc_0/CH0_DDR4_0]
  connect_bd_intf_net -intf_net axi_noc_0_M00_AXI [get_bd_intf_pins axi_noc_0/M00_AXI] [get_bd_intf_pins noc_tg_bc/SLOT_0_AXI]
  set_property HDL_ATTRIBUTE.DEBUG {true} [get_bd_intf_nets axi_noc_0_M00_AXI]
  connect_bd_intf_net -intf_net axi_noc_0_M01_AXI [get_bd_intf_pins axi_noc_0/M01_AXI] [get_bd_intf_pins noc_tg_bc/S00_AXI]
  connect_bd_intf_net -intf_net bridge_refclkX0Y10_diff_gt_ref_clock_1 [get_bd_intf_ports bridge_refclkX0Y10_diff_gt_ref_clock] [get_bd_intf_pins gty_quad_105/bridge_refclkX0Y10_diff_gt_ref_clock]
  connect_bd_intf_net -intf_net bridge_refclkX1Y10_diff_gt_ref_clock_1 [get_bd_intf_ports bridge_refclkX1Y10_diff_gt_ref_clock] [get_bd_intf_pins gty_quad_205/bridge_refclkX1Y10_diff_gt_ref_clock]
  connect_bd_intf_net -intf_net bridge_refclkX1Y2_diff_gt_ref_clock_1 [get_bd_intf_ports bridge_refclkX1Y2_diff_gt_ref_clock] [get_bd_intf_pins gty_quad_201/bridge_refclkX1Y2_diff_gt_ref_clock]
  connect_bd_intf_net -intf_net bridge_refclkX1Y8_diff_gt_ref_clock_1 [get_bd_intf_ports bridge_refclkX1Y8_diff_gt_ref_clock] [get_bd_intf_pins gty_quad_204/bridge_refclkX1Y8_diff_gt_ref_clock]
  connect_bd_intf_net -intf_net ddr4_dimm1_sma_clk_1 [get_bd_intf_ports ddr4_dimm1_sma_clk] [get_bd_intf_pins axi_noc_0/sys_clk0]
  connect_bd_intf_net -intf_net gt_quad_base_1_GT_Serial [get_bd_intf_ports GT_Serial_1] [get_bd_intf_pins gty_quad_201/GT_Serial_1]
  connect_bd_intf_net -intf_net gt_quad_base_2_GT_Serial [get_bd_intf_ports GT_Serial_2] [get_bd_intf_pins gty_quad_204/GT_Serial_2]
  connect_bd_intf_net -intf_net gt_quad_base_3_GT_Serial [get_bd_intf_ports GT_Serial_3] [get_bd_intf_pins gty_quad_205/GT_Serial_3]
  connect_bd_intf_net -intf_net gt_quad_base_GT_Serial [get_bd_intf_ports GT_Serial] [get_bd_intf_pins gty_quad_105/GT_Serial]
  connect_bd_intf_net -intf_net noc_tg_M_AXI [get_bd_intf_pins axi_noc_0/S00_AXI] [get_bd_intf_pins noc_tg_bc/M_AXI]
  connect_bd_intf_net -intf_net versal_cips_0_FPD_CCI_NOC_0 [get_bd_intf_pins axi_noc_0/S01_AXI] [get_bd_intf_pins versal_cips_0/FPD_CCI_NOC_0]
  connect_bd_intf_net -intf_net versal_cips_0_FPD_CCI_NOC_1 [get_bd_intf_pins axi_noc_0/S02_AXI] [get_bd_intf_pins versal_cips_0/FPD_CCI_NOC_1]
  connect_bd_intf_net -intf_net versal_cips_0_FPD_CCI_NOC_2 [get_bd_intf_pins axi_noc_0/S03_AXI] [get_bd_intf_pins versal_cips_0/FPD_CCI_NOC_2]
  connect_bd_intf_net -intf_net versal_cips_0_FPD_CCI_NOC_3 [get_bd_intf_pins axi_noc_0/S04_AXI] [get_bd_intf_pins versal_cips_0/FPD_CCI_NOC_3]
  connect_bd_intf_net -intf_net versal_cips_0_LPD_AXI_NOC_0 [get_bd_intf_pins axi_noc_0/S05_AXI] [get_bd_intf_pins versal_cips_0/LPD_AXI_NOC_0]
  connect_bd_intf_net -intf_net versal_cips_0_PMC_NOC_AXI_0 [get_bd_intf_pins axi_noc_0/S06_AXI] [get_bd_intf_pins versal_cips_0/PMC_NOC_AXI_0]

  # Create port connections
  connect_bd_net -net clk_wizard_0_clk_out1 [get_bd_pins axi_noc_0/aclk6] [get_bd_pins clk_wizard_0/clk_out1] [get_bd_pins gty_quad_105/apb3clk] [get_bd_pins gty_quad_201/apb3clk] [get_bd_pins gty_quad_204/apb3clk] [get_bd_pins gty_quad_205/apb3clk] [get_bd_pins noc_tg_bc/pclk] [get_bd_pins proc_sys_reset_0/slowest_sync_clk]
  connect_bd_net -net clk_wizard_0_clk_out2 [get_bd_pins clk_wizard_0/clk_out2] [get_bd_pins counters/clk100]
  connect_bd_net -net clk_wizard_0_clk_out3 [get_bd_pins clk_wizard_0/clk_out3] [get_bd_pins counters/clk200]
  connect_bd_net -net clk_wizard_0_clk_out4 [get_bd_pins axi_noc_0/aclk7] [get_bd_pins clk_wizard_0/clk_out4] [get_bd_pins noc_tg_bc/clk]
  connect_bd_net -net proc_sys_reset_0_interconnect_aresetn [get_bd_pins noc_tg_bc/aresetn] [get_bd_pins proc_sys_reset_0/interconnect_aresetn]
  connect_bd_net -net proc_sys_reset_zzz_peripheral_aresetn [get_bd_pins noc_tg_bc/rst_n] [get_bd_pins proc_sys_reset_0/peripheral_aresetn]
  connect_bd_net -net versal_cips_0_fpd_cci_noc_axi0_clk [get_bd_pins axi_noc_0/aclk0] [get_bd_pins versal_cips_0/fpd_cci_noc_axi0_clk]
  connect_bd_net -net versal_cips_0_fpd_cci_noc_axi1_clk [get_bd_pins axi_noc_0/aclk1] [get_bd_pins versal_cips_0/fpd_cci_noc_axi1_clk]
  connect_bd_net -net versal_cips_0_fpd_cci_noc_axi2_clk [get_bd_pins axi_noc_0/aclk2] [get_bd_pins versal_cips_0/fpd_cci_noc_axi2_clk]
  connect_bd_net -net versal_cips_0_fpd_cci_noc_axi3_clk [get_bd_pins axi_noc_0/aclk3] [get_bd_pins versal_cips_0/fpd_cci_noc_axi3_clk]
  connect_bd_net -net versal_cips_0_lpd_axi_noc_clk [get_bd_pins axi_noc_0/aclk4] [get_bd_pins versal_cips_0/lpd_axi_noc_clk]
  connect_bd_net -net versal_cips_0_pl0_ref_clk1 [get_bd_pins clk_wizard_0/clk_in1] [get_bd_pins versal_cips_0/pl0_ref_clk]
  connect_bd_net -net versal_cips_0_pl0_resetn [get_bd_pins proc_sys_reset_0/ext_reset_in] [get_bd_pins versal_cips_0/pl0_resetn]
  connect_bd_net -net versal_cips_0_pmc_axi_noc_axi0_clk [get_bd_pins axi_noc_0/aclk5] [get_bd_pins versal_cips_0/pmc_axi_noc_axi0_clk]

  # Create address segments
  assign_bd_address -offset 0x00000000 -range 0x80000000 -target_address_space [get_bd_addr_spaces versal_cips_0/FPD_CCI_NOC_0] [get_bd_addr_segs axi_noc_0/S01_AXI/C0_DDR_LOW0] -force
  assign_bd_address -offset 0x00000000 -range 0x80000000 -target_address_space [get_bd_addr_spaces versal_cips_0/LPD_AXI_NOC_0] [get_bd_addr_segs axi_noc_0/S05_AXI/C0_DDR_LOW0] -force
  assign_bd_address -offset 0x00000000 -range 0x80000000 -target_address_space [get_bd_addr_spaces versal_cips_0/PMC_NOC_AXI_0] [get_bd_addr_segs axi_noc_0/S06_AXI/C0_DDR_LOW0] -force
  assign_bd_address -offset 0x000800000000 -range 0x000180000000 -target_address_space [get_bd_addr_spaces versal_cips_0/FPD_CCI_NOC_0] [get_bd_addr_segs axi_noc_0/S01_AXI/C0_DDR_LOW1] -force
  assign_bd_address -offset 0x000800000000 -range 0x000180000000 -target_address_space [get_bd_addr_spaces versal_cips_0/LPD_AXI_NOC_0] [get_bd_addr_segs axi_noc_0/S05_AXI/C0_DDR_LOW1] -force
  assign_bd_address -offset 0x000800000000 -range 0x000180000000 -target_address_space [get_bd_addr_spaces versal_cips_0/PMC_NOC_AXI_0] [get_bd_addr_segs axi_noc_0/S06_AXI/C0_DDR_LOW1] -force
  assign_bd_address -offset 0x00000000 -range 0x80000000 -target_address_space [get_bd_addr_spaces versal_cips_0/FPD_CCI_NOC_1] [get_bd_addr_segs axi_noc_0/S02_AXI/C1_DDR_LOW0] -force
  assign_bd_address -offset 0x000800000000 -range 0x000180000000 -target_address_space [get_bd_addr_spaces versal_cips_0/FPD_CCI_NOC_1] [get_bd_addr_segs axi_noc_0/S02_AXI/C1_DDR_LOW1] -force
  assign_bd_address -offset 0x00000000 -range 0x80000000 -target_address_space [get_bd_addr_spaces versal_cips_0/FPD_CCI_NOC_2] [get_bd_addr_segs axi_noc_0/S03_AXI/C2_DDR_LOW0] -force
  assign_bd_address -offset 0x000800000000 -range 0x000180000000 -target_address_space [get_bd_addr_spaces versal_cips_0/FPD_CCI_NOC_2] [get_bd_addr_segs axi_noc_0/S03_AXI/C2_DDR_LOW1] -force
  assign_bd_address -offset 0x00000000 -range 0x80000000 -target_address_space [get_bd_addr_spaces versal_cips_0/FPD_CCI_NOC_3] [get_bd_addr_segs axi_noc_0/S04_AXI/C3_DDR_LOW0] -force
  assign_bd_address -offset 0x000800000000 -range 0x000180000000 -target_address_space [get_bd_addr_spaces versal_cips_0/FPD_CCI_NOC_3] [get_bd_addr_segs axi_noc_0/S04_AXI/C3_DDR_LOW1] -force
  assign_bd_address -offset 0x020100000000 -range 0x00002000 -target_address_space [get_bd_addr_spaces versal_cips_0/PMC_NOC_AXI_0] [get_bd_addr_segs noc_tg_bc/noc_bc/S_AXI/Mem0] -force
  assign_bd_address -offset 0x020180000000 -range 0x00010000 -target_address_space [get_bd_addr_spaces versal_cips_0/PMC_NOC_AXI_0] [get_bd_addr_segs noc_tg_bc/noc_sim_trig/AXI4_LITE/Reg] -force
  assign_bd_address -offset 0x00000000 -range 0x80000000 -target_address_space [get_bd_addr_spaces noc_tg_bc/noc_tg/Data] [get_bd_addr_segs axi_noc_0/S00_AXI/C0_DDR_LOW0] -force
  assign_bd_address -offset 0x000800000000 -range 0x000180000000 -target_address_space [get_bd_addr_spaces noc_tg_bc/noc_tg/Data] [get_bd_addr_segs axi_noc_0/S00_AXI/C0_DDR_LOW1] -force

  # Exclude Address Segments
  exclude_bd_addr_seg -target_address_space [get_bd_addr_spaces versal_cips_0/FPD_CCI_NOC_0] [get_bd_addr_segs noc_tg_bc/noc_sim_trig/AXI4_LITE/Reg]

  # Perform GUI Layout
  regenerate_bd_layout -layout_string {
   "ActiveEmotionalView":"Default View",
   "Default View_ScaleFactor":"0.719835",
   "Default View_TopLeft":"-436,-181",
   "DisplayHardenedConnections":"1",
   "DisplayPinAutomationMissing":"1",
   "DisplayPinsOfHiddenNets":"1",
   "DisplayTieOff":"1",
   "ExpandedHierarchyInLayout":"",
   "comment_0":"ChipScoPy Configurable Example Design (CED)
-----------------------------------------------------------------
This CED targets the vmk180 evaluation board and is designed 
to be used with the ChipScoPy API examples found at 
https://github.com/Xilinx/chipscopy

This design includes support for the following API examples:
- GTY transceivers for IBERT API examples
- DDR4 memory controller for DDRMC API examples
- SysMon voltage and temp sensors for SysMon API examples
- NoC, traffic generator, and BRAM controller for 
  NoC Perfmon API examples
- Binary counters and DDS cores for ILA and VIO API examples",
   "commentid":"comment_0|",
   "font_comment_0":"15",
   "guistr":"# # String gsaved with Nlview 7.0r4  2019-12-20 bk=1.5203 VDI=41 GEI=36 GUI=JA:10.0 TLS
#  -string -flagsOSRD
preplace port GT_Serial -pg 1 -lvl 3 -x 1850 -y 640 -defaultsOSRD
preplace port GT_Serial_1 -pg 1 -lvl 3 -x 1850 -y 750 -defaultsOSRD
preplace port GT_Serial_2 -pg 1 -lvl 3 -x 1850 -y 860 -defaultsOSRD
preplace port GT_Serial_3 -pg 1 -lvl 3 -x 1850 -y 970 -defaultsOSRD
preplace port bridge_refclkX0Y10_diff_gt_ref_clock -pg 1 -lvl 0 -x -10 -y 630 -defaultsOSRD
preplace port bridge_refclkX1Y10_diff_gt_ref_clock -pg 1 -lvl 0 -x -10 -y 960 -defaultsOSRD
preplace port bridge_refclkX1Y2_diff_gt_ref_clock -pg 1 -lvl 0 -x -10 -y 740 -defaultsOSRD
preplace port bridge_refclkX1Y8_diff_gt_ref_clock -pg 1 -lvl 0 -x -10 -y 850 -defaultsOSRD
preplace port ddr4_dimm1 -pg 1 -lvl 3 -x 1850 -y 230 -defaultsOSRD
preplace port ddr4_dimm1_sma_clk -pg 1 -lvl 0 -x -10 -y 230 -defaultsOSRD
preplace inst clk_wizard_0 -pg 1 -lvl 1 -x 940 -y 320 -defaultsOSRD
preplace inst counters -pg 1 -lvl 2 -x 1590 -y 520 -defaultsOSRD
preplace inst gty_quad_105 -pg 1 -lvl 2 -x 1590 -y 640 -defaultsOSRD
preplace inst gty_quad_201 -pg 1 -lvl 2 -x 1590 -y 750 -defaultsOSRD
preplace inst gty_quad_204 -pg 1 -lvl 2 -x 1590 -y 860 -defaultsOSRD
preplace inst gty_quad_205 -pg 1 -lvl 2 -x 1590 -y 970 -defaultsOSRD
preplace inst noc_tg_bc -pg 1 -lvl 2 -x 1590 -y 370 -defaultsOSRD
preplace inst proc_sys_reset_0 -pg 1 -lvl 1 -x 940 -y 510 -defaultsOSRD
preplace inst axi_noc_0 -pg 1 -lvl 2 -x 1590 -y 30 -defaultsOSRD
preplace inst versal_cips_0 -pg 1 -lvl 1 -x 940 -y 30 -defaultsOSRD
preplace netloc clk_wizard_0_clk_out1 1 0 2 30 610 1280
preplace netloc clk_wizard_0_clk_out2 1 1 1 1240 310n
preplace netloc clk_wizard_0_clk_out3 1 1 1 1210 330n
preplace netloc clk_wizard_0_clk_out4 1 1 1 1300 180n
preplace netloc proc_sys_reset_0_interconnect_aresetn 1 1 1 1200 360n
preplace netloc proc_sys_reset_zzz_peripheral_aresetn 1 1 1 1290 400n
preplace netloc versal_cips_0_fpd_cci_noc_axi0_clk 1 1 1 1210 40n
preplace netloc versal_cips_0_fpd_cci_noc_axi1_clk 1 1 1 1220 60n
preplace netloc versal_cips_0_fpd_cci_noc_axi2_clk 1 1 1 1230 80n
preplace netloc versal_cips_0_fpd_cci_noc_axi3_clk 1 1 1 1250 100n
preplace netloc versal_cips_0_lpd_axi_noc_clk 1 1 1 1260 120n
preplace netloc versal_cips_0_pl0_ref_clk1 1 0 2 10 -160 1200
preplace netloc versal_cips_0_pl0_resetn 1 0 2 20 220 1200
preplace netloc versal_cips_0_pmc_axi_noc_axi0_clk 1 1 1 1270 140n
preplace netloc axi_noc_0_CH0_DDR4_0 1 2 1 1820J 50n
preplace netloc axi_noc_0_M00_AXI 1 1 2 1320J 240 1810
preplace netloc axi_noc_0_M01_AXI 1 1 2 1330J 250 1800
preplace netloc bridge_refclkX0Y10_diff_gt_ref_clock_1 1 0 2 NJ 630 NJ
preplace netloc bridge_refclkX1Y10_diff_gt_ref_clock_1 1 0 2 NJ 960 NJ
preplace netloc bridge_refclkX1Y2_diff_gt_ref_clock_1 1 0 2 NJ 740 NJ
preplace netloc bridge_refclkX1Y8_diff_gt_ref_clock_1 1 0 2 NJ 850 NJ
preplace netloc ddr4_dimm1_sma_clk_1 1 0 2 NJ 230 1240J
preplace netloc gt_quad_base_1_GT_Serial 1 2 1 NJ 750
preplace netloc gt_quad_base_2_GT_Serial 1 2 1 NJ 860
preplace netloc gt_quad_base_3_GT_Serial 1 2 1 NJ 970
preplace netloc gt_quad_base_GT_Serial 1 2 1 NJ 640
preplace netloc noc_tg_M_AXI 1 1 2 1310 260 1800
preplace netloc versal_cips_0_FPD_CCI_NOC_0 1 1 1 N -100
preplace netloc versal_cips_0_FPD_CCI_NOC_1 1 1 1 N -80
preplace netloc versal_cips_0_FPD_CCI_NOC_2 1 1 1 N -60
preplace netloc versal_cips_0_FPD_CCI_NOC_3 1 1 1 N -40
preplace netloc versal_cips_0_LPD_AXI_NOC_0 1 1 1 N -20
preplace netloc versal_cips_0_PMC_NOC_AXI_0 1 1 1 N 0
preplace cgraphic comment_0 place top 60 70 textcolor 4 linecolor 3 linewidth 2
levelinfo -pg 1 -10 940 1590 1850
pagesize -pg 1 -db -bbox -sgen -330 -180 1990 1440
",
   "linecolor_comment_0":"#000080",
   "textcolor_comment_0":"#800000"
}

  # Restore current instance
  current_bd_instance $oldCurInst

  validate_bd_design
  save_bd_design
}
# End of create_root_design()


##################################################################
# MAIN FLOW
##################################################################

create_root_design ""


