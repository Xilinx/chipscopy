//------------------------------------------------------------------------------
//  (c) Copyright 2023 Advanced Micro Devices, Inc. All rights reserved.
//
//  This file contains confidential and proprietary information
//  of AMD, Inc. and is protected under U.S. and
//  international copyright and other intellectual property
//  laws.
//
//  DISCLAIMER
//  This disclaimer is not a license and does not grant any
//  rights to the materials distributed herewith. Except as
//  otherwise provided in a valid license issued to you by
//  AMD, and to the maximum extent permitted by applicable
//  law: (1) THESE MATERIALS ARE MADE AVAILABLE "AS IS" AND
//  WITH ALL FAULTS, AND AMD HEREBY DISCLAIMS ALL WARRANTIES
//  AND CONDITIONS, EXPRESS, IMPLIED, OR STATUTORY, INCLUDING
//  BUT NOT LIMITED TO WARRANTIES OF MERCHANTABILITY, NON-
//  INFRINGEMENT, OR FITNESS FOR ANY PARTICULAR PURPOSE; and
//  (2) AMD shall not be liable (whether in contract or tort,
//  including negligence, or under any other theory of
//  liability) for any loss or damage of any kind or nature
//  related to, arising under or in connection with these
//  materials, including for any direct, or any indirect,
//  special, incidental, or consequential loss or damage
//  (including loss of data, profits, goodwill, or any type of
//  loss or damage suffered as a result of any action brought
//  by a third party) even if such damage or loss was
//  reasonably foreseeable or AMD had been advised of the
//  possibility of the same.
//
//  CRITICAL APPLICATIONS
//  AMD products are not designed or intended to be fail-
//  safe, or for use in any application requiring fail-safe
//  performance, such as life-support or safety devices or
//  systems, Class III medical devices, nuclear facilities,
//  applications related to the deployment of airbags, or any
//  other applications that could lead to death, personal
//  injury, or severe property or environmental damage
//  (individually and collectively, "Critical
//  Applications"). Customer assumes the sole risk and
//  liability of any use of AMD products in Critical
//  Applications, subject only to applicable laws and
//  regulations governing limitations on product liability.
//
//  THIS COPYRIGHT NOTICE AND DISCLAIMER MUST BE RETAINED AS
//  PART OF THIS FILE AT ALL TIMES.
//------------------------------------------------------------------------------


`timescale 1ps/1ps

// =====================================================================================================================
// This example design top module instantiates the example design wrapper; slices vectored ports for per-channel
// assignment; and instantiates example resources such as buffers, pattern generators, and pattern checkers for core
// demonstration purposes
// =====================================================================================================================

module gty_vcu117_isi_example_top (

  // Differential reference clock inputs
  input  wire mgtrefclk1_x0y3_p,
  input  wire mgtrefclk1_x0y3_n,

  // Serial data ports for transceiver channel 0
  input  wire ch0_gtyrxn_in,
  input  wire ch0_gtyrxp_in,
  output wire ch0_gtytxn_out,
  output wire ch0_gtytxp_out,

  // Serial data ports for transceiver channel 1
  input  wire ch1_gtyrxn_in,
  input  wire ch1_gtyrxp_in,
  output wire ch1_gtytxn_out,
  output wire ch1_gtytxp_out,

  // Serial data ports for transceiver channel 2
  input  wire ch2_gtyrxn_in,
  input  wire ch2_gtyrxp_in,
  output wire ch2_gtytxn_out,
  output wire ch2_gtytxp_out,

  // Serial data ports for transceiver channel 3
  input  wire ch3_gtyrxn_in,
  input  wire ch3_gtyrxp_in,
  output wire ch3_gtytxn_out,
  output wire ch3_gtytxp_out,

  // Serial data ports for transceiver channel 4
  input  wire ch4_gtyrxn_in,
  input  wire ch4_gtyrxp_in,
  output wire ch4_gtytxn_out,
  output wire ch4_gtytxp_out,

  // Serial data ports for transceiver channel 5
  input  wire ch5_gtyrxn_in,
  input  wire ch5_gtyrxp_in,
  output wire ch5_gtytxn_out,
  output wire ch5_gtytxp_out,

  // Serial data ports for transceiver channel 6
  input  wire ch6_gtyrxn_in,
  input  wire ch6_gtyrxp_in,
  output wire ch6_gtytxn_out,
  output wire ch6_gtytxp_out,

  // Serial data ports for transceiver channel 7
  input  wire ch7_gtyrxn_in,
  input  wire ch7_gtyrxp_in,
  output wire ch7_gtytxn_out,
  output wire ch7_gtytxp_out,

  // Serial data ports for transceiver channel 8
  input  wire ch8_gtyrxn_in,
  input  wire ch8_gtyrxp_in,
  output wire ch8_gtytxn_out,
  output wire ch8_gtytxp_out,

  // Serial data ports for transceiver channel 9
  input  wire ch9_gtyrxn_in,
  input  wire ch9_gtyrxp_in,
  output wire ch9_gtytxn_out,
  output wire ch9_gtytxp_out,

  // Serial data ports for transceiver channel 10
  input  wire ch10_gtyrxn_in,
  input  wire ch10_gtyrxp_in,
  output wire ch10_gtytxn_out,
  output wire ch10_gtytxp_out,

  // Serial data ports for transceiver channel 11
  input  wire ch11_gtyrxn_in,
  input  wire ch11_gtyrxp_in,
  output wire ch11_gtytxn_out,
  output wire ch11_gtytxp_out,

  // Serial data ports for transceiver channel 12
  input  wire ch12_gtyrxn_in,
  input  wire ch12_gtyrxp_in,
  output wire ch12_gtytxn_out,
  output wire ch12_gtytxp_out,

  // Serial data ports for transceiver channel 13
  input  wire ch13_gtyrxn_in,
  input  wire ch13_gtyrxp_in,
  output wire ch13_gtytxn_out,
  output wire ch13_gtytxp_out,

  // User-provided ports for reset helper block(s)
  input  wire hb_gtwiz_reset_clk_freerun_in,
  input  wire hb_gtwiz_reset_all_in,

  // PRBS-based link status ports
  input  wire link_down_latched_reset_in,
  output wire link_status_out,
  output reg  link_down_latched_out = 1'b1

);


  // ===================================================================================================================
  // PER-CHANNEL SIGNAL ASSIGNMENTS
  // ===================================================================================================================

  // The core and example design wrapper vectorize ports across all enabled transceiver channel and common instances for
  // simplicity and compactness. This example design top module assigns slices of each vector to individual, per-channel
  // signal vectors for use if desired. Signals which connect to helper blocks are prefixed "hb#", signals which connect
  // to transceiver common primitives are prefixed "cm#", and signals which connect to transceiver channel primitives
  // are prefixed "ch#", where "#" is the sequential resource number.

  //--------------------------------------------------------------------------------------------------------------------
  wire [13:0] gtyrxn_int;
  assign gtyrxn_int[0:0] = ch0_gtyrxn_in;
  assign gtyrxn_int[1:1] = ch1_gtyrxn_in;
  assign gtyrxn_int[2:2] = ch2_gtyrxn_in;
  assign gtyrxn_int[3:3] = ch3_gtyrxn_in;
  assign gtyrxn_int[4:4] = ch4_gtyrxn_in;
  assign gtyrxn_int[5:5] = ch5_gtyrxn_in;
  assign gtyrxn_int[6:6] = ch6_gtyrxn_in;
  assign gtyrxn_int[7:7] = ch7_gtyrxn_in;
  assign gtyrxn_int[8:8] = ch8_gtyrxn_in;
  assign gtyrxn_int[9:9] = ch9_gtyrxn_in;
  assign gtyrxn_int[10:10] = ch10_gtyrxn_in;
  assign gtyrxn_int[11:11] = ch11_gtyrxn_in;
  assign gtyrxn_int[12:12] = ch12_gtyrxn_in;
  assign gtyrxn_int[13:13] = ch13_gtyrxn_in;

  //--------------------------------------------------------------------------------------------------------------------
  wire [13:0] gtyrxp_int;
  assign gtyrxp_int[0:0] = ch0_gtyrxp_in;
  assign gtyrxp_int[1:1] = ch1_gtyrxp_in;
  assign gtyrxp_int[2:2] = ch2_gtyrxp_in;
  assign gtyrxp_int[3:3] = ch3_gtyrxp_in;
  assign gtyrxp_int[4:4] = ch4_gtyrxp_in;
  assign gtyrxp_int[5:5] = ch5_gtyrxp_in;
  assign gtyrxp_int[6:6] = ch6_gtyrxp_in;
  assign gtyrxp_int[7:7] = ch7_gtyrxp_in;
  assign gtyrxp_int[8:8] = ch8_gtyrxp_in;
  assign gtyrxp_int[9:9] = ch9_gtyrxp_in;
  assign gtyrxp_int[10:10] = ch10_gtyrxp_in;
  assign gtyrxp_int[11:11] = ch11_gtyrxp_in;
  assign gtyrxp_int[12:12] = ch12_gtyrxp_in;
  assign gtyrxp_int[13:13] = ch13_gtyrxp_in;

  //--------------------------------------------------------------------------------------------------------------------
  wire [13:0] gtytxn_int;
  assign ch0_gtytxn_out = gtytxn_int[0:0];
  assign ch1_gtytxn_out = gtytxn_int[1:1];
  assign ch2_gtytxn_out = gtytxn_int[2:2];
  assign ch3_gtytxn_out = gtytxn_int[3:3];
  assign ch4_gtytxn_out = gtytxn_int[4:4];
  assign ch5_gtytxn_out = gtytxn_int[5:5];
  assign ch6_gtytxn_out = gtytxn_int[6:6];
  assign ch7_gtytxn_out = gtytxn_int[7:7];
  assign ch8_gtytxn_out = gtytxn_int[8:8];
  assign ch9_gtytxn_out = gtytxn_int[9:9];
  assign ch10_gtytxn_out = gtytxn_int[10:10];
  assign ch11_gtytxn_out = gtytxn_int[11:11];
  assign ch12_gtytxn_out = gtytxn_int[12:12];
  assign ch13_gtytxn_out = gtytxn_int[13:13];

  //--------------------------------------------------------------------------------------------------------------------
  wire [13:0] gtytxp_int;
  assign ch0_gtytxp_out = gtytxp_int[0:0];
  assign ch1_gtytxp_out = gtytxp_int[1:1];
  assign ch2_gtytxp_out = gtytxp_int[2:2];
  assign ch3_gtytxp_out = gtytxp_int[3:3];
  assign ch4_gtytxp_out = gtytxp_int[4:4];
  assign ch5_gtytxp_out = gtytxp_int[5:5];
  assign ch6_gtytxp_out = gtytxp_int[6:6];
  assign ch7_gtytxp_out = gtytxp_int[7:7];
  assign ch8_gtytxp_out = gtytxp_int[8:8];
  assign ch9_gtytxp_out = gtytxp_int[9:9];
  assign ch10_gtytxp_out = gtytxp_int[10:10];
  assign ch11_gtytxp_out = gtytxp_int[11:11];
  assign ch12_gtytxp_out = gtytxp_int[12:12];
  assign ch13_gtytxp_out = gtytxp_int[13:13];

  //--------------------------------------------------------------------------------------------------------------------
  wire [0:0] gtwiz_userclk_tx_reset_int;
  wire [0:0] hb0_gtwiz_userclk_tx_reset_int;
  assign gtwiz_userclk_tx_reset_int[0:0] = hb0_gtwiz_userclk_tx_reset_int;

  //--------------------------------------------------------------------------------------------------------------------
  wire [0:0] gtwiz_userclk_tx_srcclk_int;
  wire [0:0] hb0_gtwiz_userclk_tx_srcclk_int;
  assign hb0_gtwiz_userclk_tx_srcclk_int = gtwiz_userclk_tx_srcclk_int[0:0];

  //--------------------------------------------------------------------------------------------------------------------
  wire [0:0] gtwiz_userclk_tx_usrclk_int;
  wire [0:0] hb0_gtwiz_userclk_tx_usrclk_int;
  assign hb0_gtwiz_userclk_tx_usrclk_int = gtwiz_userclk_tx_usrclk_int[0:0];

  //--------------------------------------------------------------------------------------------------------------------
  wire [0:0] gtwiz_userclk_tx_usrclk2_int;
  wire [0:0] hb0_gtwiz_userclk_tx_usrclk2_int;
  assign hb0_gtwiz_userclk_tx_usrclk2_int = gtwiz_userclk_tx_usrclk2_int[0:0];

  //--------------------------------------------------------------------------------------------------------------------
  wire [0:0] gtwiz_userclk_tx_active_int;
  wire [0:0] hb0_gtwiz_userclk_tx_active_int;
  assign hb0_gtwiz_userclk_tx_active_int = gtwiz_userclk_tx_active_int[0:0];

  //--------------------------------------------------------------------------------------------------------------------
  wire [0:0] gtwiz_userclk_rx_reset_int;
  wire [0:0] hb0_gtwiz_userclk_rx_reset_int;
  assign gtwiz_userclk_rx_reset_int[0:0] = hb0_gtwiz_userclk_rx_reset_int;

  //--------------------------------------------------------------------------------------------------------------------
  wire [0:0] gtwiz_userclk_rx_srcclk_int;
  wire [0:0] hb0_gtwiz_userclk_rx_srcclk_int;
  assign hb0_gtwiz_userclk_rx_srcclk_int = gtwiz_userclk_rx_srcclk_int[0:0];

  //--------------------------------------------------------------------------------------------------------------------
  wire [0:0] gtwiz_userclk_rx_usrclk_int;
  wire [0:0] hb0_gtwiz_userclk_rx_usrclk_int;
  assign hb0_gtwiz_userclk_rx_usrclk_int = gtwiz_userclk_rx_usrclk_int[0:0];

  //--------------------------------------------------------------------------------------------------------------------
  wire [0:0] gtwiz_userclk_rx_usrclk2_int;
  wire [0:0] hb0_gtwiz_userclk_rx_usrclk2_int;
  assign hb0_gtwiz_userclk_rx_usrclk2_int = gtwiz_userclk_rx_usrclk2_int[0:0];

  //--------------------------------------------------------------------------------------------------------------------
  wire [0:0] gtwiz_userclk_rx_active_int;
  wire [0:0] hb0_gtwiz_userclk_rx_active_int;
  assign hb0_gtwiz_userclk_rx_active_int = gtwiz_userclk_rx_active_int[0:0];

  //--------------------------------------------------------------------------------------------------------------------
  wire [0:0] gtwiz_reset_clk_freerun_int;
  wire [0:0] hb0_gtwiz_reset_clk_freerun_int = 1'b0;
  assign gtwiz_reset_clk_freerun_int[0:0] = hb0_gtwiz_reset_clk_freerun_int;

  //--------------------------------------------------------------------------------------------------------------------
  wire [0:0] gtwiz_reset_all_int;
  wire [0:0] hb0_gtwiz_reset_all_int = 1'b0;
  assign gtwiz_reset_all_int[0:0] = hb0_gtwiz_reset_all_int;

  //--------------------------------------------------------------------------------------------------------------------
  wire [0:0] gtwiz_reset_tx_pll_and_datapath_int;
  wire [0:0] hb0_gtwiz_reset_tx_pll_and_datapath_int;
  assign gtwiz_reset_tx_pll_and_datapath_int[0:0] = hb0_gtwiz_reset_tx_pll_and_datapath_int;

  //--------------------------------------------------------------------------------------------------------------------
  wire [0:0] gtwiz_reset_tx_datapath_int;
  wire [0:0] hb0_gtwiz_reset_tx_datapath_int;
  assign gtwiz_reset_tx_datapath_int[0:0] = hb0_gtwiz_reset_tx_datapath_int;

  //--------------------------------------------------------------------------------------------------------------------
  wire [0:0] gtwiz_reset_rx_pll_and_datapath_int;
  wire [0:0] hb0_gtwiz_reset_rx_pll_and_datapath_int = 1'b0;
  assign gtwiz_reset_rx_pll_and_datapath_int[0:0] = hb0_gtwiz_reset_rx_pll_and_datapath_int;

  //--------------------------------------------------------------------------------------------------------------------
  wire [0:0] gtwiz_reset_rx_datapath_int;
  wire [0:0] hb0_gtwiz_reset_rx_datapath_int = 1'b0;
  assign gtwiz_reset_rx_datapath_int[0:0] = hb0_gtwiz_reset_rx_datapath_int;

  //--------------------------------------------------------------------------------------------------------------------
  wire [0:0] gtwiz_reset_rx_cdr_stable_int;
  wire [0:0] hb0_gtwiz_reset_rx_cdr_stable_int;
  assign hb0_gtwiz_reset_rx_cdr_stable_int = gtwiz_reset_rx_cdr_stable_int[0:0];

  //--------------------------------------------------------------------------------------------------------------------
  wire [0:0] gtwiz_reset_tx_done_int;
  wire [0:0] hb0_gtwiz_reset_tx_done_int;
  assign hb0_gtwiz_reset_tx_done_int = gtwiz_reset_tx_done_int[0:0];

  //--------------------------------------------------------------------------------------------------------------------
  wire [0:0] gtwiz_reset_rx_done_int;
  wire [0:0] hb0_gtwiz_reset_rx_done_int;
  assign hb0_gtwiz_reset_rx_done_int = gtwiz_reset_rx_done_int[0:0];

  //--------------------------------------------------------------------------------------------------------------------
  wire [447:0] gtwiz_userdata_tx_int;
  wire [31:0] hb0_gtwiz_userdata_tx_int;
  wire [31:0] hb1_gtwiz_userdata_tx_int;
  wire [31:0] hb2_gtwiz_userdata_tx_int;
  wire [31:0] hb3_gtwiz_userdata_tx_int;
  wire [31:0] hb4_gtwiz_userdata_tx_int;
  wire [31:0] hb5_gtwiz_userdata_tx_int;
  wire [31:0] hb6_gtwiz_userdata_tx_int;
  wire [31:0] hb7_gtwiz_userdata_tx_int;
  wire [31:0] hb8_gtwiz_userdata_tx_int;
  wire [31:0] hb9_gtwiz_userdata_tx_int;
  wire [31:0] hb10_gtwiz_userdata_tx_int;
  wire [31:0] hb11_gtwiz_userdata_tx_int;
  wire [31:0] hb12_gtwiz_userdata_tx_int;
  wire [31:0] hb13_gtwiz_userdata_tx_int;
  assign gtwiz_userdata_tx_int[31:0] = hb0_gtwiz_userdata_tx_int;
  assign gtwiz_userdata_tx_int[63:32] = hb1_gtwiz_userdata_tx_int;
  assign gtwiz_userdata_tx_int[95:64] = hb2_gtwiz_userdata_tx_int;
  assign gtwiz_userdata_tx_int[127:96] = hb3_gtwiz_userdata_tx_int;
  assign gtwiz_userdata_tx_int[159:128] = hb4_gtwiz_userdata_tx_int;
  assign gtwiz_userdata_tx_int[191:160] = hb5_gtwiz_userdata_tx_int;
  assign gtwiz_userdata_tx_int[223:192] = hb6_gtwiz_userdata_tx_int;
  assign gtwiz_userdata_tx_int[255:224] = hb7_gtwiz_userdata_tx_int;
  assign gtwiz_userdata_tx_int[287:256] = hb8_gtwiz_userdata_tx_int;
  assign gtwiz_userdata_tx_int[319:288] = hb9_gtwiz_userdata_tx_int;
  assign gtwiz_userdata_tx_int[351:320] = hb10_gtwiz_userdata_tx_int;
  assign gtwiz_userdata_tx_int[383:352] = hb11_gtwiz_userdata_tx_int;
  assign gtwiz_userdata_tx_int[415:384] = hb12_gtwiz_userdata_tx_int;
  assign gtwiz_userdata_tx_int[447:416] = hb13_gtwiz_userdata_tx_int;

  //--------------------------------------------------------------------------------------------------------------------
  wire [447:0] gtwiz_userdata_rx_int;
  wire [31:0] hb0_gtwiz_userdata_rx_int;
  wire [31:0] hb1_gtwiz_userdata_rx_int;
  wire [31:0] hb2_gtwiz_userdata_rx_int;
  wire [31:0] hb3_gtwiz_userdata_rx_int;
  wire [31:0] hb4_gtwiz_userdata_rx_int;
  wire [31:0] hb5_gtwiz_userdata_rx_int;
  wire [31:0] hb6_gtwiz_userdata_rx_int;
  wire [31:0] hb7_gtwiz_userdata_rx_int;
  wire [31:0] hb8_gtwiz_userdata_rx_int;
  wire [31:0] hb9_gtwiz_userdata_rx_int;
  wire [31:0] hb10_gtwiz_userdata_rx_int;
  wire [31:0] hb11_gtwiz_userdata_rx_int;
  wire [31:0] hb12_gtwiz_userdata_rx_int;
  wire [31:0] hb13_gtwiz_userdata_rx_int;
  assign hb0_gtwiz_userdata_rx_int = gtwiz_userdata_rx_int[31:0];
  assign hb1_gtwiz_userdata_rx_int = gtwiz_userdata_rx_int[63:32];
  assign hb2_gtwiz_userdata_rx_int = gtwiz_userdata_rx_int[95:64];
  assign hb3_gtwiz_userdata_rx_int = gtwiz_userdata_rx_int[127:96];
  assign hb4_gtwiz_userdata_rx_int = gtwiz_userdata_rx_int[159:128];
  assign hb5_gtwiz_userdata_rx_int = gtwiz_userdata_rx_int[191:160];
  assign hb6_gtwiz_userdata_rx_int = gtwiz_userdata_rx_int[223:192];
  assign hb7_gtwiz_userdata_rx_int = gtwiz_userdata_rx_int[255:224];
  assign hb8_gtwiz_userdata_rx_int = gtwiz_userdata_rx_int[287:256];
  assign hb9_gtwiz_userdata_rx_int = gtwiz_userdata_rx_int[319:288];
  assign hb10_gtwiz_userdata_rx_int = gtwiz_userdata_rx_int[351:320];
  assign hb11_gtwiz_userdata_rx_int = gtwiz_userdata_rx_int[383:352];
  assign hb12_gtwiz_userdata_rx_int = gtwiz_userdata_rx_int[415:384];
  assign hb13_gtwiz_userdata_rx_int = gtwiz_userdata_rx_int[447:416];

  //--------------------------------------------------------------------------------------------------------------------
  wire [3:0] gtrefclk01_int;
  wire [0:0] cm0_gtrefclk01_int;
  wire [0:0] cm1_gtrefclk01_int;
  wire [0:0] cm2_gtrefclk01_int;
  wire [0:0] cm3_gtrefclk01_int;
  assign gtrefclk01_int[0:0] = cm0_gtrefclk01_int;
  assign gtrefclk01_int[1:1] = cm1_gtrefclk01_int;
  assign gtrefclk01_int[2:2] = cm2_gtrefclk01_int;
  assign gtrefclk01_int[3:3] = cm3_gtrefclk01_int;

  //--------------------------------------------------------------------------------------------------------------------
  wire [3:0] qpll1outclk_int;
  wire [0:0] cm0_qpll1outclk_int;
  wire [0:0] cm1_qpll1outclk_int;
  wire [0:0] cm2_qpll1outclk_int;
  wire [0:0] cm3_qpll1outclk_int;
  assign cm0_qpll1outclk_int = qpll1outclk_int[0:0];
  assign cm1_qpll1outclk_int = qpll1outclk_int[1:1];
  assign cm2_qpll1outclk_int = qpll1outclk_int[2:2];
  assign cm3_qpll1outclk_int = qpll1outclk_int[3:3];

  //--------------------------------------------------------------------------------------------------------------------
  wire [3:0] qpll1outrefclk_int;
  wire [0:0] cm0_qpll1outrefclk_int;
  wire [0:0] cm1_qpll1outrefclk_int;
  wire [0:0] cm2_qpll1outrefclk_int;
  wire [0:0] cm3_qpll1outrefclk_int;
  assign cm0_qpll1outrefclk_int = qpll1outrefclk_int[0:0];
  assign cm1_qpll1outrefclk_int = qpll1outrefclk_int[1:1];
  assign cm2_qpll1outrefclk_int = qpll1outrefclk_int[2:2];
  assign cm3_qpll1outrefclk_int = qpll1outrefclk_int[3:3];

  //--------------------------------------------------------------------------------------------------------------------
  wire [139:0] drpaddr_int;
  wire [9:0] ch0_drpaddr_int = 10'b0000000000;
  wire [9:0] ch1_drpaddr_int = 10'b0000000000;
  wire [9:0] ch2_drpaddr_int = 10'b0000000000;
  wire [9:0] ch3_drpaddr_int = 10'b0000000000;
  wire [9:0] ch4_drpaddr_int = 10'b0000000000;
  wire [9:0] ch5_drpaddr_int = 10'b0000000000;
  wire [9:0] ch6_drpaddr_int = 10'b0000000000;
  wire [9:0] ch7_drpaddr_int = 10'b0000000000;
  wire [9:0] ch8_drpaddr_int = 10'b0000000000;
  wire [9:0] ch9_drpaddr_int = 10'b0000000000;
  wire [9:0] ch10_drpaddr_int = 10'b0000000000;
  wire [9:0] ch11_drpaddr_int = 10'b0000000000;
  wire [9:0] ch12_drpaddr_int = 10'b0000000000;
  wire [9:0] ch13_drpaddr_int = 10'b0000000000;
  assign drpaddr_int[9:0] = ch0_drpaddr_int;
  assign drpaddr_int[19:10] = ch1_drpaddr_int;
  assign drpaddr_int[29:20] = ch2_drpaddr_int;
  assign drpaddr_int[39:30] = ch3_drpaddr_int;
  assign drpaddr_int[49:40] = ch4_drpaddr_int;
  assign drpaddr_int[59:50] = ch5_drpaddr_int;
  assign drpaddr_int[69:60] = ch6_drpaddr_int;
  assign drpaddr_int[79:70] = ch7_drpaddr_int;
  assign drpaddr_int[89:80] = ch8_drpaddr_int;
  assign drpaddr_int[99:90] = ch9_drpaddr_int;
  assign drpaddr_int[109:100] = ch10_drpaddr_int;
  assign drpaddr_int[119:110] = ch11_drpaddr_int;
  assign drpaddr_int[129:120] = ch12_drpaddr_int;
  assign drpaddr_int[139:130] = ch13_drpaddr_int;

  //--------------------------------------------------------------------------------------------------------------------
  wire [13:0] drpclk_int;
  wire [0:0] ch0_drpclk_int = 1'b0;
  wire [0:0] ch1_drpclk_int = 1'b0;
  wire [0:0] ch2_drpclk_int = 1'b0;
  wire [0:0] ch3_drpclk_int = 1'b0;
  wire [0:0] ch4_drpclk_int = 1'b0;
  wire [0:0] ch5_drpclk_int = 1'b0;
  wire [0:0] ch6_drpclk_int = 1'b0;
  wire [0:0] ch7_drpclk_int = 1'b0;
  wire [0:0] ch8_drpclk_int = 1'b0;
  wire [0:0] ch9_drpclk_int = 1'b0;
  wire [0:0] ch10_drpclk_int = 1'b0;
  wire [0:0] ch11_drpclk_int = 1'b0;
  wire [0:0] ch12_drpclk_int = 1'b0;
  wire [0:0] ch13_drpclk_int = 1'b0;
  assign drpclk_int[0:0] = ch0_drpclk_int;
  assign drpclk_int[1:1] = ch1_drpclk_int;
  assign drpclk_int[2:2] = ch2_drpclk_int;
  assign drpclk_int[3:3] = ch3_drpclk_int;
  assign drpclk_int[4:4] = ch4_drpclk_int;
  assign drpclk_int[5:5] = ch5_drpclk_int;
  assign drpclk_int[6:6] = ch6_drpclk_int;
  assign drpclk_int[7:7] = ch7_drpclk_int;
  assign drpclk_int[8:8] = ch8_drpclk_int;
  assign drpclk_int[9:9] = ch9_drpclk_int;
  assign drpclk_int[10:10] = ch10_drpclk_int;
  assign drpclk_int[11:11] = ch11_drpclk_int;
  assign drpclk_int[12:12] = ch12_drpclk_int;
  assign drpclk_int[13:13] = ch13_drpclk_int;

  //--------------------------------------------------------------------------------------------------------------------
  wire [223:0] drpdi_int;
  wire [15:0] ch0_drpdi_int = 16'b0000000000000000;
  wire [15:0] ch1_drpdi_int = 16'b0000000000000000;
  wire [15:0] ch2_drpdi_int = 16'b0000000000000000;
  wire [15:0] ch3_drpdi_int = 16'b0000000000000000;
  wire [15:0] ch4_drpdi_int = 16'b0000000000000000;
  wire [15:0] ch5_drpdi_int = 16'b0000000000000000;
  wire [15:0] ch6_drpdi_int = 16'b0000000000000000;
  wire [15:0] ch7_drpdi_int = 16'b0000000000000000;
  wire [15:0] ch8_drpdi_int = 16'b0000000000000000;
  wire [15:0] ch9_drpdi_int = 16'b0000000000000000;
  wire [15:0] ch10_drpdi_int = 16'b0000000000000000;
  wire [15:0] ch11_drpdi_int = 16'b0000000000000000;
  wire [15:0] ch12_drpdi_int = 16'b0000000000000000;
  wire [15:0] ch13_drpdi_int = 16'b0000000000000000;
  assign drpdi_int[15:0] = ch0_drpdi_int;
  assign drpdi_int[31:16] = ch1_drpdi_int;
  assign drpdi_int[47:32] = ch2_drpdi_int;
  assign drpdi_int[63:48] = ch3_drpdi_int;
  assign drpdi_int[79:64] = ch4_drpdi_int;
  assign drpdi_int[95:80] = ch5_drpdi_int;
  assign drpdi_int[111:96] = ch6_drpdi_int;
  assign drpdi_int[127:112] = ch7_drpdi_int;
  assign drpdi_int[143:128] = ch8_drpdi_int;
  assign drpdi_int[159:144] = ch9_drpdi_int;
  assign drpdi_int[175:160] = ch10_drpdi_int;
  assign drpdi_int[191:176] = ch11_drpdi_int;
  assign drpdi_int[207:192] = ch12_drpdi_int;
  assign drpdi_int[223:208] = ch13_drpdi_int;

  //--------------------------------------------------------------------------------------------------------------------
  wire [13:0] drpen_int;
  wire [0:0] ch0_drpen_int = 1'b0;
  wire [0:0] ch1_drpen_int = 1'b0;
  wire [0:0] ch2_drpen_int = 1'b0;
  wire [0:0] ch3_drpen_int = 1'b0;
  wire [0:0] ch4_drpen_int = 1'b0;
  wire [0:0] ch5_drpen_int = 1'b0;
  wire [0:0] ch6_drpen_int = 1'b0;
  wire [0:0] ch7_drpen_int = 1'b0;
  wire [0:0] ch8_drpen_int = 1'b0;
  wire [0:0] ch9_drpen_int = 1'b0;
  wire [0:0] ch10_drpen_int = 1'b0;
  wire [0:0] ch11_drpen_int = 1'b0;
  wire [0:0] ch12_drpen_int = 1'b0;
  wire [0:0] ch13_drpen_int = 1'b0;
  assign drpen_int[0:0] = ch0_drpen_int;
  assign drpen_int[1:1] = ch1_drpen_int;
  assign drpen_int[2:2] = ch2_drpen_int;
  assign drpen_int[3:3] = ch3_drpen_int;
  assign drpen_int[4:4] = ch4_drpen_int;
  assign drpen_int[5:5] = ch5_drpen_int;
  assign drpen_int[6:6] = ch6_drpen_int;
  assign drpen_int[7:7] = ch7_drpen_int;
  assign drpen_int[8:8] = ch8_drpen_int;
  assign drpen_int[9:9] = ch9_drpen_int;
  assign drpen_int[10:10] = ch10_drpen_int;
  assign drpen_int[11:11] = ch11_drpen_int;
  assign drpen_int[12:12] = ch12_drpen_int;
  assign drpen_int[13:13] = ch13_drpen_int;

  //--------------------------------------------------------------------------------------------------------------------
  wire [13:0] drpwe_int;
  wire [0:0] ch0_drpwe_int = 1'b0;
  wire [0:0] ch1_drpwe_int = 1'b0;
  wire [0:0] ch2_drpwe_int = 1'b0;
  wire [0:0] ch3_drpwe_int = 1'b0;
  wire [0:0] ch4_drpwe_int = 1'b0;
  wire [0:0] ch5_drpwe_int = 1'b0;
  wire [0:0] ch6_drpwe_int = 1'b0;
  wire [0:0] ch7_drpwe_int = 1'b0;
  wire [0:0] ch8_drpwe_int = 1'b0;
  wire [0:0] ch9_drpwe_int = 1'b0;
  wire [0:0] ch10_drpwe_int = 1'b0;
  wire [0:0] ch11_drpwe_int = 1'b0;
  wire [0:0] ch12_drpwe_int = 1'b0;
  wire [0:0] ch13_drpwe_int = 1'b0;
  assign drpwe_int[0:0] = ch0_drpwe_int;
  assign drpwe_int[1:1] = ch1_drpwe_int;
  assign drpwe_int[2:2] = ch2_drpwe_int;
  assign drpwe_int[3:3] = ch3_drpwe_int;
  assign drpwe_int[4:4] = ch4_drpwe_int;
  assign drpwe_int[5:5] = ch5_drpwe_int;
  assign drpwe_int[6:6] = ch6_drpwe_int;
  assign drpwe_int[7:7] = ch7_drpwe_int;
  assign drpwe_int[8:8] = ch8_drpwe_int;
  assign drpwe_int[9:9] = ch9_drpwe_int;
  assign drpwe_int[10:10] = ch10_drpwe_int;
  assign drpwe_int[11:11] = ch11_drpwe_int;
  assign drpwe_int[12:12] = ch12_drpwe_int;
  assign drpwe_int[13:13] = ch13_drpwe_int;

  //--------------------------------------------------------------------------------------------------------------------
  wire [13:0] eyescanreset_int;
  wire [0:0] ch0_eyescanreset_int = 1'b0;
  wire [0:0] ch1_eyescanreset_int = 1'b0;
  wire [0:0] ch2_eyescanreset_int = 1'b0;
  wire [0:0] ch3_eyescanreset_int = 1'b0;
  wire [0:0] ch4_eyescanreset_int = 1'b0;
  wire [0:0] ch5_eyescanreset_int = 1'b0;
  wire [0:0] ch6_eyescanreset_int = 1'b0;
  wire [0:0] ch7_eyescanreset_int = 1'b0;
  wire [0:0] ch8_eyescanreset_int = 1'b0;
  wire [0:0] ch9_eyescanreset_int = 1'b0;
  wire [0:0] ch10_eyescanreset_int = 1'b0;
  wire [0:0] ch11_eyescanreset_int = 1'b0;
  wire [0:0] ch12_eyescanreset_int = 1'b0;
  wire [0:0] ch13_eyescanreset_int = 1'b0;
  assign eyescanreset_int[0:0] = ch0_eyescanreset_int;
  assign eyescanreset_int[1:1] = ch1_eyescanreset_int;
  assign eyescanreset_int[2:2] = ch2_eyescanreset_int;
  assign eyescanreset_int[3:3] = ch3_eyescanreset_int;
  assign eyescanreset_int[4:4] = ch4_eyescanreset_int;
  assign eyescanreset_int[5:5] = ch5_eyescanreset_int;
  assign eyescanreset_int[6:6] = ch6_eyescanreset_int;
  assign eyescanreset_int[7:7] = ch7_eyescanreset_int;
  assign eyescanreset_int[8:8] = ch8_eyescanreset_int;
  assign eyescanreset_int[9:9] = ch9_eyescanreset_int;
  assign eyescanreset_int[10:10] = ch10_eyescanreset_int;
  assign eyescanreset_int[11:11] = ch11_eyescanreset_int;
  assign eyescanreset_int[12:12] = ch12_eyescanreset_int;
  assign eyescanreset_int[13:13] = ch13_eyescanreset_int;

  //--------------------------------------------------------------------------------------------------------------------
  wire [41:0] loopback_int;
  // This vector is not sliced because it is directly assigned in a debug core instance below

  //--------------------------------------------------------------------------------------------------------------------
  wire [13:0] rxlpmen_int;
  wire [0:0] ch0_rxlpmen_int = 1'b0;
  wire [0:0] ch1_rxlpmen_int = 1'b0;
  wire [0:0] ch2_rxlpmen_int = 1'b0;
  wire [0:0] ch3_rxlpmen_int = 1'b0;
  wire [0:0] ch4_rxlpmen_int = 1'b0;
  wire [0:0] ch5_rxlpmen_int = 1'b0;
  wire [0:0] ch6_rxlpmen_int = 1'b0;
  wire [0:0] ch7_rxlpmen_int = 1'b0;
  wire [0:0] ch8_rxlpmen_int = 1'b0;
  wire [0:0] ch9_rxlpmen_int = 1'b0;
  wire [0:0] ch10_rxlpmen_int = 1'b0;
  wire [0:0] ch11_rxlpmen_int = 1'b0;
  wire [0:0] ch12_rxlpmen_int = 1'b0;
  wire [0:0] ch13_rxlpmen_int = 1'b0;
  assign rxlpmen_int[0:0] = ch0_rxlpmen_int;
  assign rxlpmen_int[1:1] = ch1_rxlpmen_int;
  assign rxlpmen_int[2:2] = ch2_rxlpmen_int;
  assign rxlpmen_int[3:3] = ch3_rxlpmen_int;
  assign rxlpmen_int[4:4] = ch4_rxlpmen_int;
  assign rxlpmen_int[5:5] = ch5_rxlpmen_int;
  assign rxlpmen_int[6:6] = ch6_rxlpmen_int;
  assign rxlpmen_int[7:7] = ch7_rxlpmen_int;
  assign rxlpmen_int[8:8] = ch8_rxlpmen_int;
  assign rxlpmen_int[9:9] = ch9_rxlpmen_int;
  assign rxlpmen_int[10:10] = ch10_rxlpmen_int;
  assign rxlpmen_int[11:11] = ch11_rxlpmen_int;
  assign rxlpmen_int[12:12] = ch12_rxlpmen_int;
  assign rxlpmen_int[13:13] = ch13_rxlpmen_int;

  //--------------------------------------------------------------------------------------------------------------------
  wire [41:0] rxrate_int;
  wire [2:0] ch0_rxrate_int = 3'b000;
  wire [2:0] ch1_rxrate_int = 3'b000;
  wire [2:0] ch2_rxrate_int = 3'b000;
  wire [2:0] ch3_rxrate_int = 3'b000;
  wire [2:0] ch4_rxrate_int = 3'b000;
  wire [2:0] ch5_rxrate_int = 3'b000;
  wire [2:0] ch6_rxrate_int = 3'b000;
  wire [2:0] ch7_rxrate_int = 3'b000;
  wire [2:0] ch8_rxrate_int = 3'b000;
  wire [2:0] ch9_rxrate_int = 3'b000;
  wire [2:0] ch10_rxrate_int = 3'b000;
  wire [2:0] ch11_rxrate_int = 3'b000;
  wire [2:0] ch12_rxrate_int = 3'b000;
  wire [2:0] ch13_rxrate_int = 3'b000;
  assign rxrate_int[2:0] = ch0_rxrate_int;
  assign rxrate_int[5:3] = ch1_rxrate_int;
  assign rxrate_int[8:6] = ch2_rxrate_int;
  assign rxrate_int[11:9] = ch3_rxrate_int;
  assign rxrate_int[14:12] = ch4_rxrate_int;
  assign rxrate_int[17:15] = ch5_rxrate_int;
  assign rxrate_int[20:18] = ch6_rxrate_int;
  assign rxrate_int[23:21] = ch7_rxrate_int;
  assign rxrate_int[26:24] = ch8_rxrate_int;
  assign rxrate_int[29:27] = ch9_rxrate_int;
  assign rxrate_int[32:30] = ch10_rxrate_int;
  assign rxrate_int[35:33] = ch11_rxrate_int;
  assign rxrate_int[38:36] = ch12_rxrate_int;
  assign rxrate_int[41:39] = ch13_rxrate_int;

  //--------------------------------------------------------------------------------------------------------------------
  wire [69:0] txdiffctrl_int;
  wire [4:0] ch0_txdiffctrl_int = 5'b11000;
  wire [4:0] ch1_txdiffctrl_int = 5'b11000;
  wire [4:0] ch2_txdiffctrl_int = 5'b11000;
  wire [4:0] ch3_txdiffctrl_int = 5'b11000;
  wire [4:0] ch4_txdiffctrl_int = 5'b11000;
  wire [4:0] ch5_txdiffctrl_int = 5'b11000;
  wire [4:0] ch6_txdiffctrl_int = 5'b11000;
  wire [4:0] ch7_txdiffctrl_int = 5'b11000;
  wire [4:0] ch8_txdiffctrl_int = 5'b11000;
  wire [4:0] ch9_txdiffctrl_int = 5'b11000;
  wire [4:0] ch10_txdiffctrl_int = 5'b11000;
  wire [4:0] ch11_txdiffctrl_int = 5'b11000;
  wire [4:0] ch12_txdiffctrl_int = 5'b11000;
  wire [4:0] ch13_txdiffctrl_int = 5'b11000;
  assign txdiffctrl_int[4:0] = ch0_txdiffctrl_int;
  assign txdiffctrl_int[9:5] = ch1_txdiffctrl_int;
  assign txdiffctrl_int[14:10] = ch2_txdiffctrl_int;
  assign txdiffctrl_int[19:15] = ch3_txdiffctrl_int;
  assign txdiffctrl_int[24:20] = ch4_txdiffctrl_int;
  assign txdiffctrl_int[29:25] = ch5_txdiffctrl_int;
  assign txdiffctrl_int[34:30] = ch6_txdiffctrl_int;
  assign txdiffctrl_int[39:35] = ch7_txdiffctrl_int;
  assign txdiffctrl_int[44:40] = ch8_txdiffctrl_int;
  assign txdiffctrl_int[49:45] = ch9_txdiffctrl_int;
  assign txdiffctrl_int[54:50] = ch10_txdiffctrl_int;
  assign txdiffctrl_int[59:55] = ch11_txdiffctrl_int;
  assign txdiffctrl_int[64:60] = ch12_txdiffctrl_int;
  assign txdiffctrl_int[69:65] = ch13_txdiffctrl_int;

  //--------------------------------------------------------------------------------------------------------------------
  wire [69:0] txpostcursor_int;
  // This vector is not sliced because it is directly assigned in a debug core instance below

  //--------------------------------------------------------------------------------------------------------------------
  wire [69:0] txprecursor_int;
  // This vector is not sliced because it is directly assigned in a debug core instance below

  //--------------------------------------------------------------------------------------------------------------------
  wire [223:0] drpdo_int;
  wire [15:0] ch0_drpdo_int;
  wire [15:0] ch1_drpdo_int;
  wire [15:0] ch2_drpdo_int;
  wire [15:0] ch3_drpdo_int;
  wire [15:0] ch4_drpdo_int;
  wire [15:0] ch5_drpdo_int;
  wire [15:0] ch6_drpdo_int;
  wire [15:0] ch7_drpdo_int;
  wire [15:0] ch8_drpdo_int;
  wire [15:0] ch9_drpdo_int;
  wire [15:0] ch10_drpdo_int;
  wire [15:0] ch11_drpdo_int;
  wire [15:0] ch12_drpdo_int;
  wire [15:0] ch13_drpdo_int;
  assign ch0_drpdo_int = drpdo_int[15:0];
  assign ch1_drpdo_int = drpdo_int[31:16];
  assign ch2_drpdo_int = drpdo_int[47:32];
  assign ch3_drpdo_int = drpdo_int[63:48];
  assign ch4_drpdo_int = drpdo_int[79:64];
  assign ch5_drpdo_int = drpdo_int[95:80];
  assign ch6_drpdo_int = drpdo_int[111:96];
  assign ch7_drpdo_int = drpdo_int[127:112];
  assign ch8_drpdo_int = drpdo_int[143:128];
  assign ch9_drpdo_int = drpdo_int[159:144];
  assign ch10_drpdo_int = drpdo_int[175:160];
  assign ch11_drpdo_int = drpdo_int[191:176];
  assign ch12_drpdo_int = drpdo_int[207:192];
  assign ch13_drpdo_int = drpdo_int[223:208];

  //--------------------------------------------------------------------------------------------------------------------
  wire [13:0] drprdy_int;
  wire [0:0] ch0_drprdy_int;
  wire [0:0] ch1_drprdy_int;
  wire [0:0] ch2_drprdy_int;
  wire [0:0] ch3_drprdy_int;
  wire [0:0] ch4_drprdy_int;
  wire [0:0] ch5_drprdy_int;
  wire [0:0] ch6_drprdy_int;
  wire [0:0] ch7_drprdy_int;
  wire [0:0] ch8_drprdy_int;
  wire [0:0] ch9_drprdy_int;
  wire [0:0] ch10_drprdy_int;
  wire [0:0] ch11_drprdy_int;
  wire [0:0] ch12_drprdy_int;
  wire [0:0] ch13_drprdy_int;
  assign ch0_drprdy_int = drprdy_int[0:0];
  assign ch1_drprdy_int = drprdy_int[1:1];
  assign ch2_drprdy_int = drprdy_int[2:2];
  assign ch3_drprdy_int = drprdy_int[3:3];
  assign ch4_drprdy_int = drprdy_int[4:4];
  assign ch5_drprdy_int = drprdy_int[5:5];
  assign ch6_drprdy_int = drprdy_int[6:6];
  assign ch7_drprdy_int = drprdy_int[7:7];
  assign ch8_drprdy_int = drprdy_int[8:8];
  assign ch9_drprdy_int = drprdy_int[9:9];
  assign ch10_drprdy_int = drprdy_int[10:10];
  assign ch11_drprdy_int = drprdy_int[11:11];
  assign ch12_drprdy_int = drprdy_int[12:12];
  assign ch13_drprdy_int = drprdy_int[13:13];

  //--------------------------------------------------------------------------------------------------------------------
  wire [13:0] gtpowergood_int;
  wire [0:0] ch0_gtpowergood_int;
  wire [0:0] ch1_gtpowergood_int;
  wire [0:0] ch2_gtpowergood_int;
  wire [0:0] ch3_gtpowergood_int;
  wire [0:0] ch4_gtpowergood_int;
  wire [0:0] ch5_gtpowergood_int;
  wire [0:0] ch6_gtpowergood_int;
  wire [0:0] ch7_gtpowergood_int;
  wire [0:0] ch8_gtpowergood_int;
  wire [0:0] ch9_gtpowergood_int;
  wire [0:0] ch10_gtpowergood_int;
  wire [0:0] ch11_gtpowergood_int;
  wire [0:0] ch12_gtpowergood_int;
  wire [0:0] ch13_gtpowergood_int;
  assign ch0_gtpowergood_int = gtpowergood_int[0:0];
  assign ch1_gtpowergood_int = gtpowergood_int[1:1];
  assign ch2_gtpowergood_int = gtpowergood_int[2:2];
  assign ch3_gtpowergood_int = gtpowergood_int[3:3];
  assign ch4_gtpowergood_int = gtpowergood_int[4:4];
  assign ch5_gtpowergood_int = gtpowergood_int[5:5];
  assign ch6_gtpowergood_int = gtpowergood_int[6:6];
  assign ch7_gtpowergood_int = gtpowergood_int[7:7];
  assign ch8_gtpowergood_int = gtpowergood_int[8:8];
  assign ch9_gtpowergood_int = gtpowergood_int[9:9];
  assign ch10_gtpowergood_int = gtpowergood_int[10:10];
  assign ch11_gtpowergood_int = gtpowergood_int[11:11];
  assign ch12_gtpowergood_int = gtpowergood_int[12:12];
  assign ch13_gtpowergood_int = gtpowergood_int[13:13];

  //--------------------------------------------------------------------------------------------------------------------
  wire [13:0] rxpmaresetdone_int;
  wire [0:0] ch0_rxpmaresetdone_int;
  wire [0:0] ch1_rxpmaresetdone_int;
  wire [0:0] ch2_rxpmaresetdone_int;
  wire [0:0] ch3_rxpmaresetdone_int;
  wire [0:0] ch4_rxpmaresetdone_int;
  wire [0:0] ch5_rxpmaresetdone_int;
  wire [0:0] ch6_rxpmaresetdone_int;
  wire [0:0] ch7_rxpmaresetdone_int;
  wire [0:0] ch8_rxpmaresetdone_int;
  wire [0:0] ch9_rxpmaresetdone_int;
  wire [0:0] ch10_rxpmaresetdone_int;
  wire [0:0] ch11_rxpmaresetdone_int;
  wire [0:0] ch12_rxpmaresetdone_int;
  wire [0:0] ch13_rxpmaresetdone_int;
  assign ch0_rxpmaresetdone_int = rxpmaresetdone_int[0:0];
  assign ch1_rxpmaresetdone_int = rxpmaresetdone_int[1:1];
  assign ch2_rxpmaresetdone_int = rxpmaresetdone_int[2:2];
  assign ch3_rxpmaresetdone_int = rxpmaresetdone_int[3:3];
  assign ch4_rxpmaresetdone_int = rxpmaresetdone_int[4:4];
  assign ch5_rxpmaresetdone_int = rxpmaresetdone_int[5:5];
  assign ch6_rxpmaresetdone_int = rxpmaresetdone_int[6:6];
  assign ch7_rxpmaresetdone_int = rxpmaresetdone_int[7:7];
  assign ch8_rxpmaresetdone_int = rxpmaresetdone_int[8:8];
  assign ch9_rxpmaresetdone_int = rxpmaresetdone_int[9:9];
  assign ch10_rxpmaresetdone_int = rxpmaresetdone_int[10:10];
  assign ch11_rxpmaresetdone_int = rxpmaresetdone_int[11:11];
  assign ch12_rxpmaresetdone_int = rxpmaresetdone_int[12:12];
  assign ch13_rxpmaresetdone_int = rxpmaresetdone_int[13:13];

  //--------------------------------------------------------------------------------------------------------------------
  wire [13:0] txpmaresetdone_int;
  wire [0:0] ch0_txpmaresetdone_int;
  wire [0:0] ch1_txpmaresetdone_int;
  wire [0:0] ch2_txpmaresetdone_int;
  wire [0:0] ch3_txpmaresetdone_int;
  wire [0:0] ch4_txpmaresetdone_int;
  wire [0:0] ch5_txpmaresetdone_int;
  wire [0:0] ch6_txpmaresetdone_int;
  wire [0:0] ch7_txpmaresetdone_int;
  wire [0:0] ch8_txpmaresetdone_int;
  wire [0:0] ch9_txpmaresetdone_int;
  wire [0:0] ch10_txpmaresetdone_int;
  wire [0:0] ch11_txpmaresetdone_int;
  wire [0:0] ch12_txpmaresetdone_int;
  wire [0:0] ch13_txpmaresetdone_int;
  assign ch0_txpmaresetdone_int = txpmaresetdone_int[0:0];
  assign ch1_txpmaresetdone_int = txpmaresetdone_int[1:1];
  assign ch2_txpmaresetdone_int = txpmaresetdone_int[2:2];
  assign ch3_txpmaresetdone_int = txpmaresetdone_int[3:3];
  assign ch4_txpmaresetdone_int = txpmaresetdone_int[4:4];
  assign ch5_txpmaresetdone_int = txpmaresetdone_int[5:5];
  assign ch6_txpmaresetdone_int = txpmaresetdone_int[6:6];
  assign ch7_txpmaresetdone_int = txpmaresetdone_int[7:7];
  assign ch8_txpmaresetdone_int = txpmaresetdone_int[8:8];
  assign ch9_txpmaresetdone_int = txpmaresetdone_int[9:9];
  assign ch10_txpmaresetdone_int = txpmaresetdone_int[10:10];
  assign ch11_txpmaresetdone_int = txpmaresetdone_int[11:11];
  assign ch12_txpmaresetdone_int = txpmaresetdone_int[12:12];
  assign ch13_txpmaresetdone_int = txpmaresetdone_int[13:13];


  // ===================================================================================================================
  // BUFFERS
  // ===================================================================================================================

  // Buffer the hb_gtwiz_reset_all_in input and logically combine it with the internal signal from the example
  // initialization block as well as the VIO-sourced reset
  wire hb_gtwiz_reset_all_vio_int;
  wire hb_gtwiz_reset_all_buf_int;
  wire hb_gtwiz_reset_all_init_int;
  wire hb_gtwiz_reset_all_int;

  IBUF ibuf_hb_gtwiz_reset_all_inst (
    .I (hb_gtwiz_reset_all_in),
    .O (hb_gtwiz_reset_all_buf_int)
  );

  assign hb_gtwiz_reset_all_int = hb_gtwiz_reset_all_buf_int || hb_gtwiz_reset_all_init_int || hb_gtwiz_reset_all_vio_int;

  // Globally buffer the free-running input clock
  wire hb_gtwiz_reset_clk_freerun_buf_int;

  BUFG bufg_clk_freerun_inst (
    .I (hb_gtwiz_reset_clk_freerun_in),
    .O (hb_gtwiz_reset_clk_freerun_buf_int)
  );

  // Instantiate a differential reference clock buffer for each reference clock differential pair in this configuration,
  // and assign the single-ended output of each differential reference clock buffer to the appropriate PLL input signal

  // Differential reference clock buffer for MGTREFCLK1_X0Y3
  wire mgtrefclk1_x0y3_int;

  IBUFDS_GTE4 #(
    .REFCLK_EN_TX_PATH  (1'b0),
    .REFCLK_HROW_CK_SEL (2'b00),
    .REFCLK_ICNTL_RX    (2'b00)
  ) IBUFDS_GTE4_MGTREFCLK1_X0Y3_INST (
    .I     (mgtrefclk1_x0y3_p),
    .IB    (mgtrefclk1_x0y3_n),
    .CEB   (1'b0),
    .O     (mgtrefclk1_x0y3_int),
    .ODIV2 ()
  );

  assign cm0_gtrefclk01_int = mgtrefclk1_x0y3_int;
  assign cm1_gtrefclk01_int = mgtrefclk1_x0y3_int;
  assign cm2_gtrefclk01_int = mgtrefclk1_x0y3_int;
  assign cm3_gtrefclk01_int = mgtrefclk1_x0y3_int;


  // ===================================================================================================================
  // USER CLOCKING RESETS
  // ===================================================================================================================

  // The TX user clocking helper block should be held in reset until the clock source of that block is known to be
  // stable. The following assignment is an example of how that stability can be determined, based on the selected TX
  // user clock source. Replace the assignment with the appropriate signal or logic to achieve that behavior as needed.
  assign hb0_gtwiz_userclk_tx_reset_int = ~(&txpmaresetdone_int);

  // The RX user clocking helper block should be held in reset until the clock source of that block is known to be
  // stable. The following assignment is an example of how that stability can be determined, based on the selected RX
  // user clock source. Replace the assignment with the appropriate signal or logic to achieve that behavior as needed.
  assign hb0_gtwiz_userclk_rx_reset_int = ~(&rxpmaresetdone_int);


  // ===================================================================================================================
  // PRBS STIMULUS, CHECKING, AND LINK MANAGEMENT
  // ===================================================================================================================

  // PRBS stimulus
  // -------------------------------------------------------------------------------------------------------------------

  // PRBS-based data stimulus module for transceiver channel 0
  (* DONT_TOUCH = "TRUE" *)
  gty_vcu117_isi_example_stimulus_raw example_stimulus_inst0 (
    .gtwiz_reset_all_in          (hb_gtwiz_reset_all_int),
    .gtwiz_userclk_tx_usrclk2_in (hb0_gtwiz_userclk_tx_usrclk2_int),
    .gtwiz_userclk_tx_active_in  (hb0_gtwiz_userclk_tx_active_int),
    .txdata_out                  (hb0_gtwiz_userdata_tx_int)
  );

  // PRBS-based data stimulus module for transceiver channel 1
  (* DONT_TOUCH = "TRUE" *)
  gty_vcu117_isi_example_stimulus_raw example_stimulus_inst1 (
    .gtwiz_reset_all_in          (hb_gtwiz_reset_all_int),
    .gtwiz_userclk_tx_usrclk2_in (hb0_gtwiz_userclk_tx_usrclk2_int),
    .gtwiz_userclk_tx_active_in  (hb0_gtwiz_userclk_tx_active_int),
    .txdata_out                  (hb1_gtwiz_userdata_tx_int)
  );

  // PRBS-based data stimulus module for transceiver channel 2
  (* DONT_TOUCH = "TRUE" *)
  gty_vcu117_isi_example_stimulus_raw example_stimulus_inst2 (
    .gtwiz_reset_all_in          (hb_gtwiz_reset_all_int),
    .gtwiz_userclk_tx_usrclk2_in (hb0_gtwiz_userclk_tx_usrclk2_int),
    .gtwiz_userclk_tx_active_in  (hb0_gtwiz_userclk_tx_active_int),
    .txdata_out                  (hb2_gtwiz_userdata_tx_int)
  );

  // PRBS-based data stimulus module for transceiver channel 3
  (* DONT_TOUCH = "TRUE" *)
  gty_vcu117_isi_example_stimulus_raw example_stimulus_inst3 (
    .gtwiz_reset_all_in          (hb_gtwiz_reset_all_int),
    .gtwiz_userclk_tx_usrclk2_in (hb0_gtwiz_userclk_tx_usrclk2_int),
    .gtwiz_userclk_tx_active_in  (hb0_gtwiz_userclk_tx_active_int),
    .txdata_out                  (hb3_gtwiz_userdata_tx_int)
  );

  // PRBS-based data stimulus module for transceiver channel 4
  (* DONT_TOUCH = "TRUE" *)
  gty_vcu117_isi_example_stimulus_raw example_stimulus_inst4 (
    .gtwiz_reset_all_in          (hb_gtwiz_reset_all_int),
    .gtwiz_userclk_tx_usrclk2_in (hb0_gtwiz_userclk_tx_usrclk2_int),
    .gtwiz_userclk_tx_active_in  (hb0_gtwiz_userclk_tx_active_int),
    .txdata_out                  (hb4_gtwiz_userdata_tx_int)
  );

  // PRBS-based data stimulus module for transceiver channel 5
  (* DONT_TOUCH = "TRUE" *)
  gty_vcu117_isi_example_stimulus_raw example_stimulus_inst5 (
    .gtwiz_reset_all_in          (hb_gtwiz_reset_all_int),
    .gtwiz_userclk_tx_usrclk2_in (hb0_gtwiz_userclk_tx_usrclk2_int),
    .gtwiz_userclk_tx_active_in  (hb0_gtwiz_userclk_tx_active_int),
    .txdata_out                  (hb5_gtwiz_userdata_tx_int)
  );

  // PRBS-based data stimulus module for transceiver channel 6
  (* DONT_TOUCH = "TRUE" *)
  gty_vcu117_isi_example_stimulus_raw example_stimulus_inst6 (
    .gtwiz_reset_all_in          (hb_gtwiz_reset_all_int),
    .gtwiz_userclk_tx_usrclk2_in (hb0_gtwiz_userclk_tx_usrclk2_int),
    .gtwiz_userclk_tx_active_in  (hb0_gtwiz_userclk_tx_active_int),
    .txdata_out                  (hb6_gtwiz_userdata_tx_int)
  );

  // PRBS-based data stimulus module for transceiver channel 7
  (* DONT_TOUCH = "TRUE" *)
  gty_vcu117_isi_example_stimulus_raw example_stimulus_inst7 (
    .gtwiz_reset_all_in          (hb_gtwiz_reset_all_int),
    .gtwiz_userclk_tx_usrclk2_in (hb0_gtwiz_userclk_tx_usrclk2_int),
    .gtwiz_userclk_tx_active_in  (hb0_gtwiz_userclk_tx_active_int),
    .txdata_out                  (hb7_gtwiz_userdata_tx_int)
  );

  // PRBS-based data stimulus module for transceiver channel 8
  (* DONT_TOUCH = "TRUE" *)
  gty_vcu117_isi_example_stimulus_raw example_stimulus_inst8 (
    .gtwiz_reset_all_in          (hb_gtwiz_reset_all_int),
    .gtwiz_userclk_tx_usrclk2_in (hb0_gtwiz_userclk_tx_usrclk2_int),
    .gtwiz_userclk_tx_active_in  (hb0_gtwiz_userclk_tx_active_int),
    .txdata_out                  (hb8_gtwiz_userdata_tx_int)
  );

  // PRBS-based data stimulus module for transceiver channel 9
  (* DONT_TOUCH = "TRUE" *)
  gty_vcu117_isi_example_stimulus_raw example_stimulus_inst9 (
    .gtwiz_reset_all_in          (hb_gtwiz_reset_all_int),
    .gtwiz_userclk_tx_usrclk2_in (hb0_gtwiz_userclk_tx_usrclk2_int),
    .gtwiz_userclk_tx_active_in  (hb0_gtwiz_userclk_tx_active_int),
    .txdata_out                  (hb9_gtwiz_userdata_tx_int)
  );

  // PRBS-based data stimulus module for transceiver channel 10
  (* DONT_TOUCH = "TRUE" *)
  gty_vcu117_isi_example_stimulus_raw example_stimulus_inst10 (
    .gtwiz_reset_all_in          (hb_gtwiz_reset_all_int),
    .gtwiz_userclk_tx_usrclk2_in (hb0_gtwiz_userclk_tx_usrclk2_int),
    .gtwiz_userclk_tx_active_in  (hb0_gtwiz_userclk_tx_active_int),
    .txdata_out                  (hb10_gtwiz_userdata_tx_int)
  );

  // PRBS-based data stimulus module for transceiver channel 11
  (* DONT_TOUCH = "TRUE" *)
  gty_vcu117_isi_example_stimulus_raw example_stimulus_inst11 (
    .gtwiz_reset_all_in          (hb_gtwiz_reset_all_int),
    .gtwiz_userclk_tx_usrclk2_in (hb0_gtwiz_userclk_tx_usrclk2_int),
    .gtwiz_userclk_tx_active_in  (hb0_gtwiz_userclk_tx_active_int),
    .txdata_out                  (hb11_gtwiz_userdata_tx_int)
  );

  // PRBS-based data stimulus module for transceiver channel 12
  (* DONT_TOUCH = "TRUE" *)
  gty_vcu117_isi_example_stimulus_raw example_stimulus_inst12 (
    .gtwiz_reset_all_in          (hb_gtwiz_reset_all_int),
    .gtwiz_userclk_tx_usrclk2_in (hb0_gtwiz_userclk_tx_usrclk2_int),
    .gtwiz_userclk_tx_active_in  (hb0_gtwiz_userclk_tx_active_int),
    .txdata_out                  (hb12_gtwiz_userdata_tx_int)
  );

  // PRBS-based data stimulus module for transceiver channel 13
  (* DONT_TOUCH = "TRUE" *)
  gty_vcu117_isi_example_stimulus_raw example_stimulus_inst13 (
    .gtwiz_reset_all_in          (hb_gtwiz_reset_all_int),
    .gtwiz_userclk_tx_usrclk2_in (hb0_gtwiz_userclk_tx_usrclk2_int),
    .gtwiz_userclk_tx_active_in  (hb0_gtwiz_userclk_tx_active_int),
    .txdata_out                  (hb13_gtwiz_userdata_tx_int)
  );

  // PRBS checking
  // -------------------------------------------------------------------------------------------------------------------

  // Declare a signal vector of PRBS match indicators, with one indicator bit per transceiver channel
  wire [13:0] prbs_match_int;

  // PRBS-based data checking module for transceiver channel 0
  gty_vcu117_isi_example_checking_raw example_checking_inst0 (
    .gtwiz_reset_all_in          (hb_gtwiz_reset_all_int || ~hb0_gtwiz_reset_rx_done_int ),
    .gtwiz_userclk_rx_usrclk2_in (hb0_gtwiz_userclk_rx_usrclk2_int),
    .gtwiz_userclk_rx_active_in  (hb0_gtwiz_userclk_rx_active_int),
    .rxdata_in                   (hb0_gtwiz_userdata_rx_int),
    .prbs_match_out              (prbs_match_int[0])
  );

  // PRBS-based data checking module for transceiver channel 1
  gty_vcu117_isi_example_checking_raw example_checking_inst1 (
    .gtwiz_reset_all_in          (hb_gtwiz_reset_all_int || ~hb0_gtwiz_reset_rx_done_int ),
    .gtwiz_userclk_rx_usrclk2_in (hb0_gtwiz_userclk_rx_usrclk2_int),
    .gtwiz_userclk_rx_active_in  (hb0_gtwiz_userclk_rx_active_int),
    .rxdata_in                   (hb1_gtwiz_userdata_rx_int),
    .prbs_match_out              (prbs_match_int[1])
  );

  // PRBS-based data checking module for transceiver channel 2
  gty_vcu117_isi_example_checking_raw example_checking_inst2 (
    .gtwiz_reset_all_in          (hb_gtwiz_reset_all_int || ~hb0_gtwiz_reset_rx_done_int ),
    .gtwiz_userclk_rx_usrclk2_in (hb0_gtwiz_userclk_rx_usrclk2_int),
    .gtwiz_userclk_rx_active_in  (hb0_gtwiz_userclk_rx_active_int),
    .rxdata_in                   (hb2_gtwiz_userdata_rx_int),
    .prbs_match_out              (prbs_match_int[2])
  );

  // PRBS-based data checking module for transceiver channel 3
  gty_vcu117_isi_example_checking_raw example_checking_inst3 (
    .gtwiz_reset_all_in          (hb_gtwiz_reset_all_int || ~hb0_gtwiz_reset_rx_done_int ),
    .gtwiz_userclk_rx_usrclk2_in (hb0_gtwiz_userclk_rx_usrclk2_int),
    .gtwiz_userclk_rx_active_in  (hb0_gtwiz_userclk_rx_active_int),
    .rxdata_in                   (hb3_gtwiz_userdata_rx_int),
    .prbs_match_out              (prbs_match_int[3])
  );

  // PRBS-based data checking module for transceiver channel 4
  gty_vcu117_isi_example_checking_raw example_checking_inst4 (
    .gtwiz_reset_all_in          (hb_gtwiz_reset_all_int || ~hb0_gtwiz_reset_rx_done_int ),
    .gtwiz_userclk_rx_usrclk2_in (hb0_gtwiz_userclk_rx_usrclk2_int),
    .gtwiz_userclk_rx_active_in  (hb0_gtwiz_userclk_rx_active_int),
    .rxdata_in                   (hb4_gtwiz_userdata_rx_int),
    .prbs_match_out              (prbs_match_int[4])
  );

  // PRBS-based data checking module for transceiver channel 5
  gty_vcu117_isi_example_checking_raw example_checking_inst5 (
    .gtwiz_reset_all_in          (hb_gtwiz_reset_all_int || ~hb0_gtwiz_reset_rx_done_int ),
    .gtwiz_userclk_rx_usrclk2_in (hb0_gtwiz_userclk_rx_usrclk2_int),
    .gtwiz_userclk_rx_active_in  (hb0_gtwiz_userclk_rx_active_int),
    .rxdata_in                   (hb5_gtwiz_userdata_rx_int),
    .prbs_match_out              (prbs_match_int[5])
  );

  // PRBS-based data checking module for transceiver channel 6
  gty_vcu117_isi_example_checking_raw example_checking_inst6 (
    .gtwiz_reset_all_in          (hb_gtwiz_reset_all_int || ~hb0_gtwiz_reset_rx_done_int ),
    .gtwiz_userclk_rx_usrclk2_in (hb0_gtwiz_userclk_rx_usrclk2_int),
    .gtwiz_userclk_rx_active_in  (hb0_gtwiz_userclk_rx_active_int),
    .rxdata_in                   (hb6_gtwiz_userdata_rx_int),
    .prbs_match_out              (prbs_match_int[6])
  );

  // PRBS-based data checking module for transceiver channel 7
  gty_vcu117_isi_example_checking_raw example_checking_inst7 (
    .gtwiz_reset_all_in          (hb_gtwiz_reset_all_int || ~hb0_gtwiz_reset_rx_done_int ),
    .gtwiz_userclk_rx_usrclk2_in (hb0_gtwiz_userclk_rx_usrclk2_int),
    .gtwiz_userclk_rx_active_in  (hb0_gtwiz_userclk_rx_active_int),
    .rxdata_in                   (hb7_gtwiz_userdata_rx_int),
    .prbs_match_out              (prbs_match_int[7])
  );

  // PRBS-based data checking module for transceiver channel 8
  gty_vcu117_isi_example_checking_raw example_checking_inst8 (
    .gtwiz_reset_all_in          (hb_gtwiz_reset_all_int || ~hb0_gtwiz_reset_rx_done_int ),
    .gtwiz_userclk_rx_usrclk2_in (hb0_gtwiz_userclk_rx_usrclk2_int),
    .gtwiz_userclk_rx_active_in  (hb0_gtwiz_userclk_rx_active_int),
    .rxdata_in                   (hb8_gtwiz_userdata_rx_int),
    .prbs_match_out              (prbs_match_int[8])
  );

  // PRBS-based data checking module for transceiver channel 9
  gty_vcu117_isi_example_checking_raw example_checking_inst9 (
    .gtwiz_reset_all_in          (hb_gtwiz_reset_all_int || ~hb0_gtwiz_reset_rx_done_int ),
    .gtwiz_userclk_rx_usrclk2_in (hb0_gtwiz_userclk_rx_usrclk2_int),
    .gtwiz_userclk_rx_active_in  (hb0_gtwiz_userclk_rx_active_int),
    .rxdata_in                   (hb9_gtwiz_userdata_rx_int),
    .prbs_match_out              (prbs_match_int[9])
  );

  // PRBS-based data checking module for transceiver channel 10
  gty_vcu117_isi_example_checking_raw example_checking_inst10 (
    .gtwiz_reset_all_in          (hb_gtwiz_reset_all_int || ~hb0_gtwiz_reset_rx_done_int ),
    .gtwiz_userclk_rx_usrclk2_in (hb0_gtwiz_userclk_rx_usrclk2_int),
    .gtwiz_userclk_rx_active_in  (hb0_gtwiz_userclk_rx_active_int),
    .rxdata_in                   (hb10_gtwiz_userdata_rx_int),
    .prbs_match_out              (prbs_match_int[10])
  );

  // PRBS-based data checking module for transceiver channel 11
  gty_vcu117_isi_example_checking_raw example_checking_inst11 (
    .gtwiz_reset_all_in          (hb_gtwiz_reset_all_int || ~hb0_gtwiz_reset_rx_done_int ),
    .gtwiz_userclk_rx_usrclk2_in (hb0_gtwiz_userclk_rx_usrclk2_int),
    .gtwiz_userclk_rx_active_in  (hb0_gtwiz_userclk_rx_active_int),
    .rxdata_in                   (hb11_gtwiz_userdata_rx_int),
    .prbs_match_out              (prbs_match_int[11])
  );

  // PRBS-based data checking module for transceiver channel 12
  gty_vcu117_isi_example_checking_raw example_checking_inst12 (
    .gtwiz_reset_all_in          (hb_gtwiz_reset_all_int || ~hb0_gtwiz_reset_rx_done_int ),
    .gtwiz_userclk_rx_usrclk2_in (hb0_gtwiz_userclk_rx_usrclk2_int),
    .gtwiz_userclk_rx_active_in  (hb0_gtwiz_userclk_rx_active_int),
    .rxdata_in                   (hb12_gtwiz_userdata_rx_int),
    .prbs_match_out              (prbs_match_int[12])
  );

  // PRBS-based data checking module for transceiver channel 13
  gty_vcu117_isi_example_checking_raw example_checking_inst13 (
    .gtwiz_reset_all_in          (hb_gtwiz_reset_all_int || ~hb0_gtwiz_reset_rx_done_int ),
    .gtwiz_userclk_rx_usrclk2_in (hb0_gtwiz_userclk_rx_usrclk2_int),
    .gtwiz_userclk_rx_active_in  (hb0_gtwiz_userclk_rx_active_int),
    .rxdata_in                   (hb13_gtwiz_userdata_rx_int),
    .prbs_match_out              (prbs_match_int[13])
  );

  // PRBS match and related link management
  // -------------------------------------------------------------------------------------------------------------------

  // Perform a bitwise NAND of all PRBS match indicators, creating a combinatorial indication of any PRBS mismatch
  // across all transceiver channels
  wire prbs_error_any_async = ~(&prbs_match_int);
  wire prbs_error_any_sync;

  // Synchronize the PRBS mismatch indicator the free-running clock domain, using a reset synchronizer with asynchronous
  // reset and synchronous removal
  (* DONT_TOUCH = "TRUE" *)
  gty_vcu117_isi_example_reset_synchronizer reset_synchronizer_prbs_match_all_inst (
    .clk_in (hb_gtwiz_reset_clk_freerun_buf_int),
    .rst_in (prbs_error_any_async),
    .rst_out(prbs_error_any_sync)
  );

  // Implement an example link status state machine using a simple leaky bucket mechanism. The link status indicates
  // the continual PRBS match status to both the top-level observer and the initialization state machine, while being
  // tolerant of occasional bit errors. This is an example and can be modified as necessary.
  localparam ST_LINK_DOWN = 1'b0;
  localparam ST_LINK_UP   = 1'b1;
  reg        sm_link      = ST_LINK_DOWN;
  reg [6:0]  link_ctr     = 7'd0;

  always @(posedge hb_gtwiz_reset_clk_freerun_buf_int) begin
    case (sm_link)
      // The link is considered to be down when the link counter initially has a value less than 67. When the link is
      // down, the counter is incremented on each cycle where all PRBS bits match, but reset whenever any PRBS mismatch
      // occurs. When the link counter reaches 67, transition to the link up state.
      ST_LINK_DOWN: begin
        if (prbs_error_any_sync !== 1'b0) begin
          link_ctr <= 7'd0;
        end
        else begin
          if (link_ctr < 7'd67)
            link_ctr <= link_ctr + 7'd1;
          else
            sm_link <= ST_LINK_UP;
        end
      end

      // When the link is up, the link counter is decreased by 34 whenever any PRBS mismatch occurs, but is increased by
      // only 1 on each cycle where all PRBS bits match, up to its saturation point of 67. If the link counter reaches
      // 0 (including rollover protection), transition to the link down state.
      ST_LINK_UP: begin
        if (prbs_error_any_sync !== 1'b0) begin
          if (link_ctr > 7'd33) begin
            link_ctr <= link_ctr - 7'd34;
            if (link_ctr == 7'd34)
              sm_link  <= ST_LINK_DOWN;
          end
          else begin
            link_ctr <= 7'd0;
            sm_link  <= ST_LINK_DOWN;
          end
        end
        else begin
          if (link_ctr < 7'd67)
            link_ctr <= link_ctr + 7'd1;
        end
      end
    endcase
  end

  // Synchronize the latched link down reset input and the VIO-driven signal into the free-running clock domain
  wire link_down_latched_reset_vio_int;
  wire link_down_latched_reset_sync;

  (* DONT_TOUCH = "TRUE" *)
  gty_vcu117_isi_example_bit_synchronizer bit_synchronizer_link_down_latched_reset_inst (
    .clk_in (hb_gtwiz_reset_clk_freerun_buf_int),
    .i_in   (link_down_latched_reset_in || link_down_latched_reset_vio_int),
    .o_out  (link_down_latched_reset_sync)
  );

  // Reset the latched link down indicator when the synchronized latched link down reset signal is high. Otherwise, set
  // the latched link down indicator upon losing link. This indicator is available for user reference.
  always @(posedge hb_gtwiz_reset_clk_freerun_buf_int) begin
    if (link_down_latched_reset_sync)
      link_down_latched_out <= 1'b0;
    else if (!sm_link)
      link_down_latched_out <= 1'b1;
  end

  // Assign the link status indicator to the top-level two-state output for user reference
  assign link_status_out = sm_link;


  // ===================================================================================================================
  // INITIALIZATION
  // ===================================================================================================================

  // Declare the receiver reset signals that interface to the reset controller helper block. For this configuration,
  // which uses the same PLL type for transmitter and receiver, the "reset RX PLL and datapath" feature is not used.
  wire hb_gtwiz_reset_rx_pll_and_datapath_int = 1'b0;
  wire hb_gtwiz_reset_rx_datapath_int;

  // Declare signals which connect the VIO instance to the initialization module for debug purposes
  wire       init_done_int;
  wire [3:0] init_retry_ctr_int;

  // Combine the receiver reset signals form the initialization module and the VIO to drive the appropriate reset
  // controller helper block reset input
  wire hb_gtwiz_reset_rx_pll_and_datapath_vio_int;
  wire hb_gtwiz_reset_rx_datapath_vio_int;
  wire hb_gtwiz_reset_rx_datapath_init_int;

  assign hb_gtwiz_reset_rx_datapath_int = hb_gtwiz_reset_rx_datapath_init_int || hb_gtwiz_reset_rx_datapath_vio_int;

  // The example initialization module interacts with the reset controller helper block and other example design logic
  // to retry failed reset attempts in order to mitigate bring-up issues such as initially-unavilable reference clocks
  // or data connections. It also resets the receiver in the event of link loss in an attempt to regain link, so please
  // note the possibility that this behavior can have the effect of overriding or disturbing user-provided inputs that
  // destabilize the data stream. It is a demonstration only and can be modified to suit your system needs.
  gty_vcu117_isi_example_init example_init_inst (
    .clk_freerun_in  (hb_gtwiz_reset_clk_freerun_buf_int),
    .reset_all_in    (hb_gtwiz_reset_all_int),
    .tx_init_done_in (gtwiz_reset_tx_done_int),
    .rx_init_done_in (gtwiz_reset_rx_done_int),
    .rx_data_good_in (sm_link),
    .reset_all_out   (hb_gtwiz_reset_all_init_int),
    .reset_rx_out    (hb_gtwiz_reset_rx_datapath_init_int),
    .init_done_out   (init_done_int),
    .retry_ctr_out   (init_retry_ctr_int)
  );


  // ===================================================================================================================
  // VIO FOR HARDWARE BRING-UP AND DEBUG
  // ===================================================================================================================

  // Synchronize gtpowergood into the free-running clock domain for VIO usage
  wire [13:0] gtpowergood_vio_sync;

  (* DONT_TOUCH = "TRUE" *)
  gty_vcu117_isi_example_bit_synchronizer bit_synchronizer_vio_gtpowergood_0_inst (
    .clk_in (hb_gtwiz_reset_clk_freerun_buf_int),
    .i_in   (gtpowergood_int[0]),
    .o_out  (gtpowergood_vio_sync[0])
  );

  (* DONT_TOUCH = "TRUE" *)
  gty_vcu117_isi_example_bit_synchronizer bit_synchronizer_vio_gtpowergood_1_inst (
    .clk_in (hb_gtwiz_reset_clk_freerun_buf_int),
    .i_in   (gtpowergood_int[1]),
    .o_out  (gtpowergood_vio_sync[1])
  );

  (* DONT_TOUCH = "TRUE" *)
  gty_vcu117_isi_example_bit_synchronizer bit_synchronizer_vio_gtpowergood_2_inst (
    .clk_in (hb_gtwiz_reset_clk_freerun_buf_int),
    .i_in   (gtpowergood_int[2]),
    .o_out  (gtpowergood_vio_sync[2])
  );

  (* DONT_TOUCH = "TRUE" *)
  gty_vcu117_isi_example_bit_synchronizer bit_synchronizer_vio_gtpowergood_3_inst (
    .clk_in (hb_gtwiz_reset_clk_freerun_buf_int),
    .i_in   (gtpowergood_int[3]),
    .o_out  (gtpowergood_vio_sync[3])
  );

  (* DONT_TOUCH = "TRUE" *)
  gty_vcu117_isi_example_bit_synchronizer bit_synchronizer_vio_gtpowergood_4_inst (
    .clk_in (hb_gtwiz_reset_clk_freerun_buf_int),
    .i_in   (gtpowergood_int[4]),
    .o_out  (gtpowergood_vio_sync[4])
  );

  (* DONT_TOUCH = "TRUE" *)
  gty_vcu117_isi_example_bit_synchronizer bit_synchronizer_vio_gtpowergood_5_inst (
    .clk_in (hb_gtwiz_reset_clk_freerun_buf_int),
    .i_in   (gtpowergood_int[5]),
    .o_out  (gtpowergood_vio_sync[5])
  );

  (* DONT_TOUCH = "TRUE" *)
  gty_vcu117_isi_example_bit_synchronizer bit_synchronizer_vio_gtpowergood_6_inst (
    .clk_in (hb_gtwiz_reset_clk_freerun_buf_int),
    .i_in   (gtpowergood_int[6]),
    .o_out  (gtpowergood_vio_sync[6])
  );

  (* DONT_TOUCH = "TRUE" *)
  gty_vcu117_isi_example_bit_synchronizer bit_synchronizer_vio_gtpowergood_7_inst (
    .clk_in (hb_gtwiz_reset_clk_freerun_buf_int),
    .i_in   (gtpowergood_int[7]),
    .o_out  (gtpowergood_vio_sync[7])
  );

  (* DONT_TOUCH = "TRUE" *)
  gty_vcu117_isi_example_bit_synchronizer bit_synchronizer_vio_gtpowergood_8_inst (
    .clk_in (hb_gtwiz_reset_clk_freerun_buf_int),
    .i_in   (gtpowergood_int[8]),
    .o_out  (gtpowergood_vio_sync[8])
  );

  (* DONT_TOUCH = "TRUE" *)
  gty_vcu117_isi_example_bit_synchronizer bit_synchronizer_vio_gtpowergood_9_inst (
    .clk_in (hb_gtwiz_reset_clk_freerun_buf_int),
    .i_in   (gtpowergood_int[9]),
    .o_out  (gtpowergood_vio_sync[9])
  );

  (* DONT_TOUCH = "TRUE" *)
  gty_vcu117_isi_example_bit_synchronizer bit_synchronizer_vio_gtpowergood_10_inst (
    .clk_in (hb_gtwiz_reset_clk_freerun_buf_int),
    .i_in   (gtpowergood_int[10]),
    .o_out  (gtpowergood_vio_sync[10])
  );

  (* DONT_TOUCH = "TRUE" *)
  gty_vcu117_isi_example_bit_synchronizer bit_synchronizer_vio_gtpowergood_11_inst (
    .clk_in (hb_gtwiz_reset_clk_freerun_buf_int),
    .i_in   (gtpowergood_int[11]),
    .o_out  (gtpowergood_vio_sync[11])
  );

  (* DONT_TOUCH = "TRUE" *)
  gty_vcu117_isi_example_bit_synchronizer bit_synchronizer_vio_gtpowergood_12_inst (
    .clk_in (hb_gtwiz_reset_clk_freerun_buf_int),
    .i_in   (gtpowergood_int[12]),
    .o_out  (gtpowergood_vio_sync[12])
  );

  (* DONT_TOUCH = "TRUE" *)
  gty_vcu117_isi_example_bit_synchronizer bit_synchronizer_vio_gtpowergood_13_inst (
    .clk_in (hb_gtwiz_reset_clk_freerun_buf_int),
    .i_in   (gtpowergood_int[13]),
    .o_out  (gtpowergood_vio_sync[13])
  );

  // Synchronize txpmaresetdone into the free-running clock domain for VIO usage
  wire [13:0] txpmaresetdone_vio_sync;

  (* DONT_TOUCH = "TRUE" *)
  gty_vcu117_isi_example_bit_synchronizer bit_synchronizer_vio_txpmaresetdone_0_inst (
    .clk_in (hb_gtwiz_reset_clk_freerun_buf_int),
    .i_in   (txpmaresetdone_int[0]),
    .o_out  (txpmaresetdone_vio_sync[0])
  );

  (* DONT_TOUCH = "TRUE" *)
  gty_vcu117_isi_example_bit_synchronizer bit_synchronizer_vio_txpmaresetdone_1_inst (
    .clk_in (hb_gtwiz_reset_clk_freerun_buf_int),
    .i_in   (txpmaresetdone_int[1]),
    .o_out  (txpmaresetdone_vio_sync[1])
  );

  (* DONT_TOUCH = "TRUE" *)
  gty_vcu117_isi_example_bit_synchronizer bit_synchronizer_vio_txpmaresetdone_2_inst (
    .clk_in (hb_gtwiz_reset_clk_freerun_buf_int),
    .i_in   (txpmaresetdone_int[2]),
    .o_out  (txpmaresetdone_vio_sync[2])
  );

  (* DONT_TOUCH = "TRUE" *)
  gty_vcu117_isi_example_bit_synchronizer bit_synchronizer_vio_txpmaresetdone_3_inst (
    .clk_in (hb_gtwiz_reset_clk_freerun_buf_int),
    .i_in   (txpmaresetdone_int[3]),
    .o_out  (txpmaresetdone_vio_sync[3])
  );

  (* DONT_TOUCH = "TRUE" *)
  gty_vcu117_isi_example_bit_synchronizer bit_synchronizer_vio_txpmaresetdone_4_inst (
    .clk_in (hb_gtwiz_reset_clk_freerun_buf_int),
    .i_in   (txpmaresetdone_int[4]),
    .o_out  (txpmaresetdone_vio_sync[4])
  );

  (* DONT_TOUCH = "TRUE" *)
  gty_vcu117_isi_example_bit_synchronizer bit_synchronizer_vio_txpmaresetdone_5_inst (
    .clk_in (hb_gtwiz_reset_clk_freerun_buf_int),
    .i_in   (txpmaresetdone_int[5]),
    .o_out  (txpmaresetdone_vio_sync[5])
  );

  (* DONT_TOUCH = "TRUE" *)
  gty_vcu117_isi_example_bit_synchronizer bit_synchronizer_vio_txpmaresetdone_6_inst (
    .clk_in (hb_gtwiz_reset_clk_freerun_buf_int),
    .i_in   (txpmaresetdone_int[6]),
    .o_out  (txpmaresetdone_vio_sync[6])
  );

  (* DONT_TOUCH = "TRUE" *)
  gty_vcu117_isi_example_bit_synchronizer bit_synchronizer_vio_txpmaresetdone_7_inst (
    .clk_in (hb_gtwiz_reset_clk_freerun_buf_int),
    .i_in   (txpmaresetdone_int[7]),
    .o_out  (txpmaresetdone_vio_sync[7])
  );

  (* DONT_TOUCH = "TRUE" *)
  gty_vcu117_isi_example_bit_synchronizer bit_synchronizer_vio_txpmaresetdone_8_inst (
    .clk_in (hb_gtwiz_reset_clk_freerun_buf_int),
    .i_in   (txpmaresetdone_int[8]),
    .o_out  (txpmaresetdone_vio_sync[8])
  );

  (* DONT_TOUCH = "TRUE" *)
  gty_vcu117_isi_example_bit_synchronizer bit_synchronizer_vio_txpmaresetdone_9_inst (
    .clk_in (hb_gtwiz_reset_clk_freerun_buf_int),
    .i_in   (txpmaresetdone_int[9]),
    .o_out  (txpmaresetdone_vio_sync[9])
  );

  (* DONT_TOUCH = "TRUE" *)
  gty_vcu117_isi_example_bit_synchronizer bit_synchronizer_vio_txpmaresetdone_10_inst (
    .clk_in (hb_gtwiz_reset_clk_freerun_buf_int),
    .i_in   (txpmaresetdone_int[10]),
    .o_out  (txpmaresetdone_vio_sync[10])
  );

  (* DONT_TOUCH = "TRUE" *)
  gty_vcu117_isi_example_bit_synchronizer bit_synchronizer_vio_txpmaresetdone_11_inst (
    .clk_in (hb_gtwiz_reset_clk_freerun_buf_int),
    .i_in   (txpmaresetdone_int[11]),
    .o_out  (txpmaresetdone_vio_sync[11])
  );

  (* DONT_TOUCH = "TRUE" *)
  gty_vcu117_isi_example_bit_synchronizer bit_synchronizer_vio_txpmaresetdone_12_inst (
    .clk_in (hb_gtwiz_reset_clk_freerun_buf_int),
    .i_in   (txpmaresetdone_int[12]),
    .o_out  (txpmaresetdone_vio_sync[12])
  );

  (* DONT_TOUCH = "TRUE" *)
  gty_vcu117_isi_example_bit_synchronizer bit_synchronizer_vio_txpmaresetdone_13_inst (
    .clk_in (hb_gtwiz_reset_clk_freerun_buf_int),
    .i_in   (txpmaresetdone_int[13]),
    .o_out  (txpmaresetdone_vio_sync[13])
  );

  // Synchronize rxpmaresetdone into the free-running clock domain for VIO usage
  wire [13:0] rxpmaresetdone_vio_sync;

  (* DONT_TOUCH = "TRUE" *)
  gty_vcu117_isi_example_bit_synchronizer bit_synchronizer_vio_rxpmaresetdone_0_inst (
    .clk_in (hb_gtwiz_reset_clk_freerun_buf_int),
    .i_in   (rxpmaresetdone_int[0]),
    .o_out  (rxpmaresetdone_vio_sync[0])
  );

  (* DONT_TOUCH = "TRUE" *)
  gty_vcu117_isi_example_bit_synchronizer bit_synchronizer_vio_rxpmaresetdone_1_inst (
    .clk_in (hb_gtwiz_reset_clk_freerun_buf_int),
    .i_in   (rxpmaresetdone_int[1]),
    .o_out  (rxpmaresetdone_vio_sync[1])
  );

  (* DONT_TOUCH = "TRUE" *)
  gty_vcu117_isi_example_bit_synchronizer bit_synchronizer_vio_rxpmaresetdone_2_inst (
    .clk_in (hb_gtwiz_reset_clk_freerun_buf_int),
    .i_in   (rxpmaresetdone_int[2]),
    .o_out  (rxpmaresetdone_vio_sync[2])
  );

  (* DONT_TOUCH = "TRUE" *)
  gty_vcu117_isi_example_bit_synchronizer bit_synchronizer_vio_rxpmaresetdone_3_inst (
    .clk_in (hb_gtwiz_reset_clk_freerun_buf_int),
    .i_in   (rxpmaresetdone_int[3]),
    .o_out  (rxpmaresetdone_vio_sync[3])
  );

  (* DONT_TOUCH = "TRUE" *)
  gty_vcu117_isi_example_bit_synchronizer bit_synchronizer_vio_rxpmaresetdone_4_inst (
    .clk_in (hb_gtwiz_reset_clk_freerun_buf_int),
    .i_in   (rxpmaresetdone_int[4]),
    .o_out  (rxpmaresetdone_vio_sync[4])
  );

  (* DONT_TOUCH = "TRUE" *)
  gty_vcu117_isi_example_bit_synchronizer bit_synchronizer_vio_rxpmaresetdone_5_inst (
    .clk_in (hb_gtwiz_reset_clk_freerun_buf_int),
    .i_in   (rxpmaresetdone_int[5]),
    .o_out  (rxpmaresetdone_vio_sync[5])
  );

  (* DONT_TOUCH = "TRUE" *)
  gty_vcu117_isi_example_bit_synchronizer bit_synchronizer_vio_rxpmaresetdone_6_inst (
    .clk_in (hb_gtwiz_reset_clk_freerun_buf_int),
    .i_in   (rxpmaresetdone_int[6]),
    .o_out  (rxpmaresetdone_vio_sync[6])
  );

  (* DONT_TOUCH = "TRUE" *)
  gty_vcu117_isi_example_bit_synchronizer bit_synchronizer_vio_rxpmaresetdone_7_inst (
    .clk_in (hb_gtwiz_reset_clk_freerun_buf_int),
    .i_in   (rxpmaresetdone_int[7]),
    .o_out  (rxpmaresetdone_vio_sync[7])
  );

  (* DONT_TOUCH = "TRUE" *)
  gty_vcu117_isi_example_bit_synchronizer bit_synchronizer_vio_rxpmaresetdone_8_inst (
    .clk_in (hb_gtwiz_reset_clk_freerun_buf_int),
    .i_in   (rxpmaresetdone_int[8]),
    .o_out  (rxpmaresetdone_vio_sync[8])
  );

  (* DONT_TOUCH = "TRUE" *)
  gty_vcu117_isi_example_bit_synchronizer bit_synchronizer_vio_rxpmaresetdone_9_inst (
    .clk_in (hb_gtwiz_reset_clk_freerun_buf_int),
    .i_in   (rxpmaresetdone_int[9]),
    .o_out  (rxpmaresetdone_vio_sync[9])
  );

  (* DONT_TOUCH = "TRUE" *)
  gty_vcu117_isi_example_bit_synchronizer bit_synchronizer_vio_rxpmaresetdone_10_inst (
    .clk_in (hb_gtwiz_reset_clk_freerun_buf_int),
    .i_in   (rxpmaresetdone_int[10]),
    .o_out  (rxpmaresetdone_vio_sync[10])
  );

  (* DONT_TOUCH = "TRUE" *)
  gty_vcu117_isi_example_bit_synchronizer bit_synchronizer_vio_rxpmaresetdone_11_inst (
    .clk_in (hb_gtwiz_reset_clk_freerun_buf_int),
    .i_in   (rxpmaresetdone_int[11]),
    .o_out  (rxpmaresetdone_vio_sync[11])
  );

  (* DONT_TOUCH = "TRUE" *)
  gty_vcu117_isi_example_bit_synchronizer bit_synchronizer_vio_rxpmaresetdone_12_inst (
    .clk_in (hb_gtwiz_reset_clk_freerun_buf_int),
    .i_in   (rxpmaresetdone_int[12]),
    .o_out  (rxpmaresetdone_vio_sync[12])
  );

  (* DONT_TOUCH = "TRUE" *)
  gty_vcu117_isi_example_bit_synchronizer bit_synchronizer_vio_rxpmaresetdone_13_inst (
    .clk_in (hb_gtwiz_reset_clk_freerun_buf_int),
    .i_in   (rxpmaresetdone_int[13]),
    .o_out  (rxpmaresetdone_vio_sync[13])
  );

  // Synchronize gtwiz_reset_tx_done into the free-running clock domain for VIO usage
  wire [0:0] gtwiz_reset_tx_done_vio_sync;

  (* DONT_TOUCH = "TRUE" *)
  gty_vcu117_isi_example_bit_synchronizer bit_synchronizer_vio_gtwiz_reset_tx_done_0_inst (
    .clk_in (hb_gtwiz_reset_clk_freerun_buf_int),
    .i_in   (gtwiz_reset_tx_done_int[0]),
    .o_out  (gtwiz_reset_tx_done_vio_sync[0])
  );

  // Synchronize gtwiz_reset_rx_done into the free-running clock domain for VIO usage
  wire [0:0] gtwiz_reset_rx_done_vio_sync;

  (* DONT_TOUCH = "TRUE" *)
  gty_vcu117_isi_example_bit_synchronizer bit_synchronizer_vio_gtwiz_reset_rx_done_0_inst (
    .clk_in (hb_gtwiz_reset_clk_freerun_buf_int),
    .i_in   (gtwiz_reset_rx_done_int[0]),
    .o_out  (gtwiz_reset_rx_done_vio_sync[0])
  );


  // Instantiate the VIO IP core for hardware bring-up and debug purposes, connecting relevant debug and analysis
  // signals which have been enabled during Wizard IP customization. This initial set of connected signals is
  // provided as a convenience and example, but more or fewer ports can be used as needed; simply re-customize and
  // re-generate the VIO instance, then connect any exposed signals that are needed. Signals which are synchronous to
  // clocks other than the free-running clock will require synchronization. For usage, refer to Vivado Design Suite
  // User Guide: Programming and Debugging (UG908)
  gty_vcu117_isi_vio_0 gty_vcu117_isi_vio_0_inst (
    .clk (hb_gtwiz_reset_clk_freerun_buf_int)
    ,.probe_in0 (link_status_out)
    ,.probe_in1 (link_down_latched_out)
    ,.probe_in2 (init_done_int)
    ,.probe_in3 (init_retry_ctr_int)
    ,.probe_in4 (gtpowergood_vio_sync)
    ,.probe_in5 (txpmaresetdone_vio_sync)
    ,.probe_in6 (rxpmaresetdone_vio_sync)
    ,.probe_in7 (gtwiz_reset_tx_done_vio_sync)
    ,.probe_in8 (gtwiz_reset_rx_done_vio_sync)
    ,.probe_out0 (hb_gtwiz_reset_all_vio_int)
    ,.probe_out1 (hb0_gtwiz_reset_tx_pll_and_datapath_int)
    ,.probe_out2 (hb0_gtwiz_reset_tx_datapath_int)
    ,.probe_out3 (hb_gtwiz_reset_rx_pll_and_datapath_vio_int)
    ,.probe_out4 (hb_gtwiz_reset_rx_datapath_vio_int)
    ,.probe_out5 (link_down_latched_reset_vio_int)
    ,.probe_out6 (txprecursor_int)
    ,.probe_out7 (txpostcursor_int)
    ,.probe_out8 (loopback_int)
  );


  // ===================================================================================================================
  // EXAMPLE WRAPPER INSTANCE
  // ===================================================================================================================

  // Instantiate the example design wrapper, mapping its enabled ports to per-channel internal signals and example
  // resources as appropriate
  gty_vcu117_isi_example_wrapper example_wrapper_inst (
    .gtyrxn_in                               (gtyrxn_int)
   ,.gtyrxp_in                               (gtyrxp_int)
   ,.gtytxn_out                              (gtytxn_int)
   ,.gtytxp_out                              (gtytxp_int)
   ,.gtwiz_userclk_tx_reset_in               (gtwiz_userclk_tx_reset_int)
   ,.gtwiz_userclk_tx_srcclk_out             (gtwiz_userclk_tx_srcclk_int)
   ,.gtwiz_userclk_tx_usrclk_out             (gtwiz_userclk_tx_usrclk_int)
   ,.gtwiz_userclk_tx_usrclk2_out            (gtwiz_userclk_tx_usrclk2_int)
   ,.gtwiz_userclk_tx_active_out             (gtwiz_userclk_tx_active_int)
   ,.gtwiz_userclk_rx_reset_in               (gtwiz_userclk_rx_reset_int)
   ,.gtwiz_userclk_rx_srcclk_out             (gtwiz_userclk_rx_srcclk_int)
   ,.gtwiz_userclk_rx_usrclk_out             (gtwiz_userclk_rx_usrclk_int)
   ,.gtwiz_userclk_rx_usrclk2_out            (gtwiz_userclk_rx_usrclk2_int)
   ,.gtwiz_userclk_rx_active_out             (gtwiz_userclk_rx_active_int)
   ,.gtwiz_reset_clk_freerun_in              ({1{hb_gtwiz_reset_clk_freerun_buf_int}})
   ,.gtwiz_reset_all_in                      ({1{hb_gtwiz_reset_all_int}})
   ,.gtwiz_reset_tx_pll_and_datapath_in      (gtwiz_reset_tx_pll_and_datapath_int)
   ,.gtwiz_reset_tx_datapath_in              (gtwiz_reset_tx_datapath_int)
   ,.gtwiz_reset_rx_pll_and_datapath_in      ({1{hb_gtwiz_reset_rx_pll_and_datapath_int}})
   ,.gtwiz_reset_rx_datapath_in              ({1{hb_gtwiz_reset_rx_datapath_int}})
   ,.gtwiz_reset_rx_cdr_stable_out           (gtwiz_reset_rx_cdr_stable_int)
   ,.gtwiz_reset_tx_done_out                 (gtwiz_reset_tx_done_int)
   ,.gtwiz_reset_rx_done_out                 (gtwiz_reset_rx_done_int)
   ,.gtwiz_userdata_tx_in                    (gtwiz_userdata_tx_int)
   ,.gtwiz_userdata_rx_out                   (gtwiz_userdata_rx_int)
   ,.gtrefclk01_in                           (gtrefclk01_int)
   ,.qpll1outclk_out                         (qpll1outclk_int)
   ,.qpll1outrefclk_out                      (qpll1outrefclk_int)
   ,.drpaddr_in                              (drpaddr_int)
   ,.drpclk_in                               (drpclk_int)
   ,.drpdi_in                                (drpdi_int)
   ,.drpen_in                                (drpen_int)
   ,.drpwe_in                                (drpwe_int)
   ,.eyescanreset_in                         (eyescanreset_int)
   ,.loopback_in                             (loopback_int)
   ,.rxlpmen_in                              (rxlpmen_int)
   ,.rxrate_in                               (rxrate_int)
   ,.txdiffctrl_in                           (txdiffctrl_int)
   ,.txpostcursor_in                         (txpostcursor_int)
   ,.txprecursor_in                          (txprecursor_int)
   ,.drpdo_out                               (drpdo_int)
   ,.drprdy_out                              (drprdy_int)
   ,.gtpowergood_out                         (gtpowergood_int)
   ,.rxpmaresetdone_out                      (rxpmaresetdone_int)
   ,.txpmaresetdone_out                      (txpmaresetdone_int)
);


endmodule
