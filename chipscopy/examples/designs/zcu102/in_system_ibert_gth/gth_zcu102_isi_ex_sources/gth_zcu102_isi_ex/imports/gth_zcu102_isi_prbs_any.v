//------------------------------------------------------------------------------
//    File Name:  PRBS_ANY.v
//      Version:  1.0
//         Date:  6-jul-10
//------------------------------------------------------------------------------
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

//--------------------------------------------------------------------------
// DESCRIPTION
//--------------------------------------------------------------------------
//   This module generates or check a PRBS pattern. The following table shows how
//   to set the PARAMETERS for compliance to ITU-T Recommendation O.150 Section 5.
//
//   When the CHK_MODE is "false", it uses a  LFSR strucure to generate the
//   PRBS pattern.
//   When the CHK_MODE is "true", the incoming data are loaded into prbs registers
//   and compared with the locally generated PRBS
//
//--------------------------------------------------------------------------
// PARAMETERS
//--------------------------------------------------------------------------
//   CHK_MODE     : true =>  check mode
//                  false => generate mode
//   INV_PATTERN  : true : invert prbs pattern
//                     in "generate mode" the generated prbs is inverted bit-wise at outputs
//                     in "check mode" the input data are inverted before processing
//   POLY_LENGHT  : length of the polynomial (= number of shift register stages)
//   POLY_TAP     : intermediate stage that is xor-ed with the last stage to generate to next prbs bit
//   NBITS        : bus size of DATA_IN and DATA_OUT
//
//--------------------------------------------------------------------------
// NOTES
//--------------------------------------------------------------------------
//
//
//   Set paramaters to the following values for a ITU-T compliant PRBS
//------------------------------------------------------------------------------
// POLY_LENGHT POLY_TAP INV_PATTERN  || nbr of   bit seq.   max 0      feedback
//                                   || stages    length  sequence      stages
//------------------------------------------------------------------------------
//     7          6       false      ||    7         127      6 ni        6, 7   (*)
//     9          5       false      ||    9         511      8 ni        5, 9
//    11          9       false      ||   11        2047     10 ni        9,11
//    15         14       true       ||   15       32767     15 i        14,15
//    20          3       false      ||   20     1048575     19 ni        3,20
//    23         18       true       ||   23     8388607     23 i        18,23
//    29         27       true       ||   29   536870911     29 i        27,29
//    31         28       true       ||   31  2147483647     31 i        28,31
//
// i=inverted, ni= non-inverted
// (*) non standard
//----------------------------------------------------------------------------
//
// In the generated parallel PRBS, LSB is the first generated bit, for example
//         if the PRBS serial stream is : 000001111011... then
//         the generated PRBS with a parallelism of 3 bit becomes:
//            data_out(2) = 0  1  1  1 ...
//            data_out(1) = 0  0  1  1 ...
//            data_out(0) = 0  0  1  0 ...
// In the received parallel PRBS, LSB is oldest bit received
//
// RESET pin is not needed for power-on reset : all registers are properly inizialized
// in the source code.
//
//------------------------------------------------------------------------------
// PINS DESCRIPTION
//------------------------------------------------------------------------------
//
//      RST          : in : syncronous reset active high
//      CLK          : in : system clock
//      DATA_IN      : in : inject error (in generate mode)
//                          data to be checked (in check mode)
//      EN           : in : enable/pause pattern generation/check
//      DATA_OUT     : out: generated prbs pattern (in generate mode)
//                          error found (in check mode)
//
//-------------------------------------------------------------------------------------------------
// History:
//      Version    : 1.0
//      Date       : 6-jul-10
//      Author     : Daniele Riccardi
//      Description: First release
//
// Subsequent cosmetic modifications by AMD for integration into the UltraScale FPGAs
// Transceivers Wizard example design.
//-------------------------------------------------------------------------------------------------

`timescale 1ps/1ps

module gth_zcu102_isi_prbs_any(RST, CLK, DATA_IN, EN, DATA_OUT);

  //--------------------------------------------
  // Configuration parameters
  //--------------------------------------------
   parameter CHK_MODE = 0;
   parameter INV_PATTERN = 0;
   parameter POLY_LENGHT = 31;
   parameter POLY_TAP = 3;
   parameter NBITS = 16;

  //--------------------------------------------
  // Input/Outputs
  //--------------------------------------------

   input  wire RST;
   input  wire CLK;
   input  wire [NBITS - 1:0] DATA_IN;
   input  wire EN;
   output reg  [NBITS - 1:0] DATA_OUT = {NBITS{1'b1}};

  //--------------------------------------------
  // Internal variables
  //--------------------------------------------

   wire [1:POLY_LENGHT] prbs[NBITS:0];
   wire [NBITS - 1:0] data_in_i;
   wire [NBITS - 1:0] prbs_xor_a;
   wire [NBITS - 1:0] prbs_xor_b;
   wire [NBITS:1] prbs_msb;
   reg  [1:POLY_LENGHT]prbs_reg = {(POLY_LENGHT){1'b1}};

  //--------------------------------------------
  // Implementation
  //--------------------------------------------

   assign data_in_i = INV_PATTERN == 0 ? DATA_IN : ( ~DATA_IN);
   assign prbs[0] = prbs_reg;

   genvar I;
   generate for (I=0; I<NBITS; I=I+1) begin : g1
      assign prbs_xor_a[I] = prbs[I][POLY_TAP] ^ prbs[I][POLY_LENGHT];
      assign prbs_xor_b[I] = prbs_xor_a[I] ^ data_in_i[I];
      assign prbs_msb[I+1] = CHK_MODE == 0 ? prbs_xor_a[I]  :  data_in_i[I];
      assign prbs[I+1] = {prbs_msb[I+1] , prbs[I][1:POLY_LENGHT-1]};
   end
   endgenerate

   always @(posedge CLK) begin
      if(RST == 1'b 1) begin
         prbs_reg <= {POLY_LENGHT{1'b1}};
         DATA_OUT <= {NBITS{1'b1}};
      end
      else if(EN == 1'b 1) begin
         DATA_OUT <= prbs_xor_b;
         prbs_reg <= prbs[NBITS];
      end
  end

endmodule
