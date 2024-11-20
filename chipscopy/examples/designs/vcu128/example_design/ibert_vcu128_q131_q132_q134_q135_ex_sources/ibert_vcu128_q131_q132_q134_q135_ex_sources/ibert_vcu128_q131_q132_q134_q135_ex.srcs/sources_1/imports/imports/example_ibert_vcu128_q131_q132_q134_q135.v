// Copyright (C) 2024, Advanced Micro Devices, Inc.
// 
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
// 
//     http://www.apache.org/licenses/LICENSE-2.0
// 
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.






// file: ibert_vcu128_q131_q132.v
//////////////////////////////////////////////////////////////////////////////

//
// Module example_ibert_vcu128_q131_q132

//////////////////////////////////////////////////////////////////////////////





`define C_NUM_GTY_QUADS 4
`define C_GTY_TOTAL_CH 16
`define C_GTY_REFCLKS_USED 4
module example_ibert_vcu128_q131_q132_q134_q135
(
  // GT top level ports
  output [(`C_GTY_TOTAL_CH)-1:0]		gty_txn_o,
  output [(`C_GTY_TOTAL_CH)-1:0]		gty_txp_o,
  input  [(`C_GTY_TOTAL_CH)-1:0]    	gty_rxn_i,
  input  [(`C_GTY_TOTAL_CH)-1:0]   	gty_rxp_i,
  input                           	gty_sysclkp_i,
  input                           	gty_sysclkn_i,
  input  [`C_GTY_REFCLKS_USED-1:0]      gty_refclk0p_i,
  input  [`C_GTY_REFCLKS_USED-1:0]      gty_refclk0n_i,
  input  [`C_GTY_REFCLKS_USED-1:0]      gty_refclk1p_i,
  input  [`C_GTY_REFCLKS_USED-1:0]      gty_refclk1n_i
);

  //
  // Ibert refclk internal signals
  //
   wire  [`C_NUM_GTY_QUADS-1:0]    gty_qrefclk0_i;
   wire  [`C_NUM_GTY_QUADS-1:0]    gty_qrefclk1_i;
   wire  [`C_NUM_GTY_QUADS-1:0]    gty_qnorthrefclk0_i;
   wire  [`C_NUM_GTY_QUADS-1:0]    gty_qnorthrefclk1_i;        	
   wire  [`C_NUM_GTY_QUADS-1:0]    gty_qsouthrefclk0_i;
   wire  [`C_NUM_GTY_QUADS-1:0]    gty_qsouthrefclk1_i;
   wire  [`C_NUM_GTY_QUADS-1:0]    gty_qrefclk00_i;
   wire  [`C_NUM_GTY_QUADS-1:0]    gty_qrefclk10_i;
   wire  [`C_NUM_GTY_QUADS-1:0]    gty_qrefclk01_i;
   wire  [`C_NUM_GTY_QUADS-1:0]    gty_qrefclk11_i;  
   wire  [`C_NUM_GTY_QUADS-1:0]    gty_qnorthrefclk00_i;
   wire  [`C_NUM_GTY_QUADS-1:0]    gty_qnorthrefclk10_i;
   wire  [`C_NUM_GTY_QUADS-1:0]    gty_qnorthrefclk01_i;
   wire  [`C_NUM_GTY_QUADS-1:0]    gty_qnorthrefclk11_i;  
   wire  [`C_NUM_GTY_QUADS-1:0]    gty_qsouthrefclk00_i;
   wire  [`C_NUM_GTY_QUADS-1:0]    gty_qsouthrefclk10_i;
   wire  [`C_NUM_GTY_QUADS-1:0]    gty_qsouthrefclk01_i;
   wire  [`C_NUM_GTY_QUADS-1:0]    gty_qsouthrefclk11_i; 
   wire  [`C_GTY_REFCLKS_USED-1:0] gty_refclk0_i;
   wire  [`C_GTY_REFCLKS_USED-1:0] gty_refclk1_i;
   wire  [`C_GTY_REFCLKS_USED-1:0] gty_odiv2_0_i;
   wire  [`C_GTY_REFCLKS_USED-1:0] gty_odiv2_1_i;
   wire                        gty_sysclk_i;

  //
  // Refclk IBUFDS instantiations
  //







 
    IBUFDS_GTE4 u_buf_q7_clk0
      (
        .O            (gty_refclk0_i[0]),
        .ODIV2        (gty_odiv2_0_i[0]),
        .CEB          (1'b0),
        .I            (gty_refclk0p_i[0]),
        .IB           (gty_refclk0n_i[0])
      );

    IBUFDS_GTE4 u_buf_q7_clk1
      (
        .O            (gty_refclk1_i[0]),
        .ODIV2        (gty_odiv2_1_i[0]),
        .CEB          (1'b0),
        .I            (gty_refclk1p_i[0]),
        .IB           (gty_refclk1n_i[0])
      );


 
    IBUFDS_GTE4 u_buf_q8_clk0
      (
        .O            (gty_refclk0_i[1]),
        .ODIV2        (gty_odiv2_0_i[1]),
        .CEB          (1'b0),
        .I            (gty_refclk0p_i[1]),
        .IB           (gty_refclk0n_i[1])
      );

    IBUFDS_GTE4 u_buf_q8_clk1
      (
        .O            (gty_refclk1_i[1]),
        .ODIV2        (gty_odiv2_1_i[1]),
        .CEB          (1'b0),
        .I            (gty_refclk1p_i[1]),
        .IB           (gty_refclk1n_i[1])
      );


    IBUFDS_GTE4 u_buf_q10_clk0
      (
        .O            (gty_refclk0_i[2]),
        .ODIV2        (gty_odiv2_0_i[2]),
        .CEB          (1'b0),
        .I            (gty_refclk0p_i[2]),
        .IB           (gty_refclk0n_i[2])
      );

    IBUFDS_GTE4 u_buf_q10_clk1
      (
        .O            (gty_refclk1_i[2]),
        .ODIV2        (gty_odiv2_1_i[2]),
        .CEB          (1'b0),
        .I            (gty_refclk1p_i[2]),
        .IB           (gty_refclk1n_i[2])
      );


 
    IBUFDS_GTE4 u_buf_q11_clk0
      (
        .O            (gty_refclk0_i[3]),
        .ODIV2        (gty_odiv2_0_i[3]),
        .CEB          (1'b0),
        .I            (gty_refclk0p_i[3]),
        .IB           (gty_refclk0n_i[3])
      );

    IBUFDS_GTE4 u_buf_q11_clk1
      (
        .O            (gty_refclk1_i[3]),
        .ODIV2        (gty_odiv2_1_i[3]),
        .CEB          (1'b0),
        .I            (gty_refclk1p_i[3]),
        .IB           (gty_refclk1n_i[3])
      );


  //
  // Refclk connection from each IBUFDS to respective quads depending on the source selected in gui
  //





  assign gty_qrefclk0_i[0] = gty_refclk0_i[0];
  assign gty_qrefclk1_i[0] = gty_refclk1_i[0];
  assign gty_qnorthrefclk0_i[0] = 1'b0;
  assign gty_qnorthrefclk1_i[0] = 1'b0;
  assign gty_qsouthrefclk0_i[0] = 1'b0;
  assign gty_qsouthrefclk1_i[0] = 1'b0;
//GTYE4_COMMON clock connection
  assign gty_qrefclk00_i[0] = gty_refclk0_i[0];
  assign gty_qrefclk10_i[0] = gty_refclk1_i[0];
  assign gty_qrefclk01_i[0] = 1'b0;
  assign gty_qrefclk11_i[0] = 1'b0;  
  assign gty_qnorthrefclk00_i[0] = 1'b0;
  assign gty_qnorthrefclk10_i[0] = 1'b0;
  assign gty_qnorthrefclk01_i[0] = 1'b0;
  assign gty_qnorthrefclk11_i[0] = 1'b0;  
  assign gty_qsouthrefclk00_i[0] = 1'b0;
  assign gty_qsouthrefclk10_i[0] = 1'b0;  
  assign gty_qsouthrefclk01_i[0] = 1'b0;
  assign gty_qsouthrefclk11_i[0] = 1'b0; 
 

  assign gty_qrefclk0_i[1] = gty_refclk0_i[1];
  assign gty_qrefclk1_i[1] = gty_refclk1_i[1];
  assign gty_qnorthrefclk0_i[1] = 1'b0;
  assign gty_qnorthrefclk1_i[1] = 1'b0;
  assign gty_qsouthrefclk0_i[1] = 1'b0;
  assign gty_qsouthrefclk1_i[1] = 1'b0;
//GTYE4_COMMON clock connection
  assign gty_qrefclk00_i[1] = gty_refclk0_i[1];
  assign gty_qrefclk10_i[1] = gty_refclk1_i[1];
  assign gty_qrefclk01_i[1] = 1'b0;
  assign gty_qrefclk11_i[1] = 1'b0;  
  assign gty_qnorthrefclk00_i[1] = 1'b0;
  assign gty_qnorthrefclk10_i[1] = 1'b0;
  assign gty_qnorthrefclk01_i[1] = 1'b0;
  assign gty_qnorthrefclk11_i[1] = 1'b0;  
  assign gty_qsouthrefclk00_i[1] = 1'b0;
  assign gty_qsouthrefclk10_i[1] = 1'b0;  
  assign gty_qsouthrefclk01_i[1] = 1'b0;
  assign gty_qsouthrefclk11_i[1] = 1'b0; 


  assign gty_qrefclk0_i[2] = gty_refclk0_i[2];
  assign gty_qrefclk1_i[2] = gty_refclk1_i[2];
  assign gty_qnorthrefclk0_i[2] = 1'b0;
  assign gty_qnorthrefclk1_i[2] = 1'b0;
  assign gty_qsouthrefclk0_i[2] = 1'b0;
  assign gty_qsouthrefclk1_i[2] = 1'b0;
//GTYE4_COMMON clock connection
  assign gty_qrefclk00_i[2] = gty_refclk0_i[2];
  assign gty_qrefclk10_i[2] = gty_refclk1_i[2];
  assign gty_qrefclk01_i[2] = 1'b0;
  assign gty_qrefclk11_i[2] = 1'b0;  
  assign gty_qnorthrefclk00_i[2] = 1'b0;
  assign gty_qnorthrefclk10_i[2] = 1'b0;
  assign gty_qnorthrefclk01_i[2] = 1'b0;
  assign gty_qnorthrefclk11_i[2] = 1'b0;  
  assign gty_qsouthrefclk00_i[2] = 1'b0;
  assign gty_qsouthrefclk10_i[2] = 1'b0;  
  assign gty_qsouthrefclk01_i[2] = 1'b0;
  assign gty_qsouthrefclk11_i[2] = 1'b0; 
 

  assign gty_qrefclk0_i[3] = gty_refclk0_i[3];
  assign gty_qrefclk1_i[3] = gty_refclk1_i[3];
  assign gty_qnorthrefclk0_i[3] = 1'b0;
  assign gty_qnorthrefclk1_i[3] = 1'b0;
  assign gty_qsouthrefclk0_i[3] = 1'b0;
  assign gty_qsouthrefclk1_i[3] = 1'b0;
//GTYE4_COMMON clock connection
  assign gty_qrefclk00_i[3] = gty_refclk0_i[3];
  assign gty_qrefclk10_i[3] = gty_refclk1_i[3];
  assign gty_qrefclk01_i[3] = 1'b0;
  assign gty_qrefclk11_i[3] = 1'b0;  
  assign gty_qnorthrefclk00_i[3] = 1'b0;
  assign gty_qnorthrefclk10_i[3] = 1'b0;
  assign gty_qnorthrefclk01_i[3] = 1'b0;
  assign gty_qnorthrefclk11_i[3] = 1'b0;  
  assign gty_qsouthrefclk00_i[3] = 1'b0;
  assign gty_qsouthrefclk10_i[3] = 1'b0;  
  assign gty_qsouthrefclk01_i[3] = 1'b0;
  assign gty_qsouthrefclk11_i[3] = 1'b0; 
 

  //
  // Sysclock IBUFDS instantiation
  //
  IBUFGDS 
   #(.DIFF_TERM("FALSE"))
   u_ibufgds
    (
      .I(gty_sysclkp_i),
      .IB(gty_sysclkn_i),
      .O(gty_sysclk_i)
    );


  //
  // IBERT core instantiation
  //
  ibert_vcu128_q131_q132 u_ibert_gty_core_a
    (
      .txn_o(gty_txn_o[1:0]),
      .txp_o(gty_txp_o[1:0]),
      .rxn_i(gty_rxn_i[1:0]),
      .rxp_i(gty_rxp_i[1:0]),
      .clk(gty_sysclk_i),
      .gtrefclk0_i(gty_qrefclk0_i[1:0]),
      .gtrefclk1_i(gty_qrefclk1_i[1:0]),
      .gtnorthrefclk0_i(gty_qnorthrefclk0_i[1:0]),
      .gtnorthrefclk1_i(gty_qnorthrefclk1_i[1:0]),
      .gtsouthrefclk0_i(gty_qsouthrefclk0_i[1:0]),
      .gtsouthrefclk1_i(gty_qsouthrefclk1_i[1:0]),
      .gtrefclk00_i(gty_qrefclk00_i[1:0]),
      .gtrefclk10_i(gty_qrefclk10_i[1:0]),
      .gtrefclk01_i(gty_qrefclk01_i[1:0]),
      .gtrefclk11_i(gty_qrefclk11_i[1:0]),
      .gtnorthrefclk00_i(gty_qnorthrefclk00_i[1:0]),
      .gtnorthrefclk10_i(gty_qnorthrefclk10_i[1:0]),
      .gtnorthrefclk01_i(gty_qnorthrefclk01_i[1:0]),
      .gtnorthrefclk11_i(gty_qnorthrefclk11_i[1:0]),
      .gtsouthrefclk00_i(gty_qsouthrefclk00_i[1:0]),
      .gtsouthrefclk10_i(gty_qsouthrefclk10_i[1:0]),
      .gtsouthrefclk01_i(gty_qsouthrefclk01_i[1:0]),
      .gtsouthrefclk11_i(gty_qsouthrefclk11_i[1:0])
    );

  ibert_vcu128_q134_q135 u_ibert_gty_core_b
    (
      .txn_o(gty_txn_o[3:2]),
      .txp_o(gty_txp_o[3:2]),
      .rxn_i(gty_rxn_i[3:2]),
      .rxp_i(gty_rxp_i[3:2]),
      .clk(gty_sysclk_i),
      .gtrefclk0_i(gty_qrefclk0_i[3:2]),
      .gtrefclk1_i(gty_qrefclk1_i[3:2]),
      .gtnorthrefclk0_i(gty_qnorthrefclk0_i[3:2]),
      .gtnorthrefclk1_i(gty_qnorthrefclk1_i[3:2]),
      .gtsouthrefclk0_i(gty_qsouthrefclk0_i[3:2]),
      .gtsouthrefclk1_i(gty_qsouthrefclk1_i[3:2]),
      .gtrefclk00_i(gty_qrefclk00_i[3:2]),
      .gtrefclk10_i(gty_qrefclk10_i[3:2]),
      .gtrefclk01_i(gty_qrefclk01_i[3:2]),
      .gtrefclk11_i(gty_qrefclk11_i[3:2]),
      .gtnorthrefclk00_i(gty_qnorthrefclk00_i[3:2]),
      .gtnorthrefclk10_i(gty_qnorthrefclk10_i[3:2]),
      .gtnorthrefclk01_i(gty_qnorthrefclk01_i[3:2]),
      .gtnorthrefclk11_i(gty_qnorthrefclk11_i[3:2]),
      .gtsouthrefclk00_i(gty_qsouthrefclk00_i[3:2]),
      .gtsouthrefclk10_i(gty_qsouthrefclk10_i[3:2]),
      .gtsouthrefclk01_i(gty_qsouthrefclk01_i[3:2]),
      .gtsouthrefclk11_i(gty_qsouthrefclk11_i[3:2])
    );

endmodule
