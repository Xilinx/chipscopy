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
// This example design top simulation module instantiates the example design top module, provides basic stimulus to it
// while looping back transceiver data from transmit to receive, and utilizes the PRBS checker-based link status
// indicator to demonstrate simple data integrity checking of the design. This module is for use in simulation only.
// =====================================================================================================================

module gty_vcu117_isi_example_top_sim ();


  // -------------------------------------------------------------------------------------------------------------------
  // Signal declarations and basic example design stimulus
  // -------------------------------------------------------------------------------------------------------------------

  // Declare wires to loop back serial data ports for transceiver channel 0
  wire ch0_gtyxn;
  wire ch0_gtyxp;

  // Declare wires to loop back serial data ports for transceiver channel 1
  wire ch1_gtyxn;
  wire ch1_gtyxp;

  // Declare wires to loop back serial data ports for transceiver channel 2
  wire ch2_gtyxn;
  wire ch2_gtyxp;

  // Declare wires to loop back serial data ports for transceiver channel 3
  wire ch3_gtyxn;
  wire ch3_gtyxp;

  // Declare wires to loop back serial data ports for transceiver channel 4
  wire ch4_gtyxn;
  wire ch4_gtyxp;

  // Declare wires to loop back serial data ports for transceiver channel 5
  wire ch5_gtyxn;
  wire ch5_gtyxp;

  // Declare wires to loop back serial data ports for transceiver channel 6
  wire ch6_gtyxn;
  wire ch6_gtyxp;

  // Declare wires to loop back serial data ports for transceiver channel 7
  wire ch7_gtyxn;
  wire ch7_gtyxp;

  // Declare wires to loop back serial data ports for transceiver channel 8
  wire ch8_gtyxn;
  wire ch8_gtyxp;

  // Declare wires to loop back serial data ports for transceiver channel 9
  wire ch9_gtyxn;
  wire ch9_gtyxp;

  // Declare wires to loop back serial data ports for transceiver channel 10
  wire ch10_gtyxn;
  wire ch10_gtyxp;

  // Declare wires to loop back serial data ports for transceiver channel 11
  wire ch11_gtyxn;
  wire ch11_gtyxp;

  // Declare wires to loop back serial data ports for transceiver channel 12
  wire ch12_gtyxn;
  wire ch12_gtyxp;

  // Declare wires to loop back serial data ports for transceiver channel 13
  wire ch13_gtyxn;
  wire ch13_gtyxp;

  // Declare register to drive reference clock at location MGTREFCLK1_X0Y3
  reg mgtrefclk1_x0y3 = 1'b0;

  // Drive that reference clock at the appropriate frequency
  // NOTE: the following simulation reference clock period may be up to +/- 2ps from its nominal value, due to rounding
  // within Verilog timescale granularity, especially when transmitter and receiver reference clock frequencies differ
  initial begin
    mgtrefclk1_x0y3 = 1'b0;
    forever
      mgtrefclk1_x0y3 = #3200 ~mgtrefclk1_x0y3;
  end

  // Declare registers to drive reset helper block(s)
  reg hb_gtwiz_reset_clk_freerun = 1'b0;
  reg hb_gtwiz_reset_all         = 1'b1;

  // Drive the helper block free running clock
  initial begin
    hb_gtwiz_reset_clk_freerun = 1'b0;
    forever
      hb_gtwiz_reset_clk_freerun = #4000 ~hb_gtwiz_reset_clk_freerun;
  end

  // Drive the helper block "reset all" input high, then low after some time
  initial begin
    hb_gtwiz_reset_all = 1'b1;
    #5E6;
    repeat (100)
      @(hb_gtwiz_reset_clk_freerun);
    hb_gtwiz_reset_all = 1'b0;
  end

  // Declare registers and wires to interface to the PRBS-based link status ports
  reg  link_down_latched_reset = 1'b0;
  wire link_status;
  wire link_down_latched;

  // -------------------------------------------------------------------------------------------------------------------
  // Basic data integrity checking, making use of PRBS-based link status ports
  // -------------------------------------------------------------------------------------------------------------------

  // Create a basic timeout indicator which is used to abort the simulation of no link is achieved after 2ms
  reg simulation_timeout_check = 1'b0;
  initial begin
    simulation_timeout_check = 1'b0;
    #2E9;
    simulation_timeout_check = 1'b1;
  end

  // Create a basic stable link monitor which is set after 2048 consecutive cycles of link up and is reset after any
  // link loss
  reg [10:0] link_up_ctr = 11'd0;
  reg        link_stable = 1'b0;
  always @(posedge hb_gtwiz_reset_clk_freerun) begin
    if (link_status !== 1'b1) begin
      link_up_ctr <= 11'd0;
      link_stable <= 1'b0;
    end
    else begin
      if (&link_up_ctr)
        link_stable <= 1'b1;
      else
        link_up_ctr <= link_up_ctr + 11'd1;
    end
  end

  // Perform basic checking of the simulation outcome based on stable link monitor
  initial begin

    // Await de-assertion of the master reset signal
    @(negedge hb_gtwiz_reset_all);

    // Await assertion of initial link indication or simulation timeout indicator
    @(posedge link_stable, simulation_timeout_check);

    // If the simulation timeout indicator was asserted, the simulation failed to achieve initial link up in a
    // reasonable time, so display an error message and quit
    if (simulation_timeout_check) begin
      $display("Time : %12d ps   FAIL: simulation timeout. Link never achieved.", $time);
      $display("** Error: Test did not complete successfully");
      $finish;
    end

    // If the initial link was achieved, display this message and continue checks as follows
    else begin
      $display("Time : %12d ps   Initial link achieved across all transceiver channels.", $time);

      // Reset the latched link down indicator, which is always set prior to initially achieving link
      $display("Time : %12d ps   Resetting latched link down indicator.", $time);
      link_down_latched_reset = 1'b1;
      repeat (5)
        @(hb_gtwiz_reset_clk_freerun);
      link_down_latched_reset = 1'b0;

      // Continue to run the simulation for long enough to detect any subsequent errors causing link loss which may
      // occur within a reasonable simulation time
      $display("Time : %12d ps   Continuing simulation for 50us to check for maintenance of link.", $time);
      #5E7;

      // At simulation completion, if the link indicator is still high and no intermittent link loss was detected,
      // display a success message. Otherwise, display a failure message. Complete the simulation in either case.
      if ((link_status === 1'b1) && (link_down_latched === 1'b0)) begin
        $display("Time : %12d ps   PASS: simulation completed with maintained link.", $time);
        $display("** Test completed successfully");
      end
      else begin
        $display("Time : %12d ps   FAIL: simulation completed with subsequent link loss after after initial link.", $time);
        $display("** Error: Test did not complete successfully");
      end

      $finish;
    end
  end

  // -------------------------------------------------------------------------------------------------------------------
  // Instantiate example design top module as the simulation DUT
  // -------------------------------------------------------------------------------------------------------------------

  gty_vcu117_isi_example_top example_top_inst (
    .mgtrefclk1_x0y3_p (mgtrefclk1_x0y3),
    .mgtrefclk1_x0y3_n (~mgtrefclk1_x0y3),
    .ch0_gtyrxn_in (ch0_gtyxn),
    .ch0_gtyrxp_in (ch0_gtyxp),
    .ch0_gtytxn_out (ch0_gtyxn),
    .ch0_gtytxp_out (ch0_gtyxp),
    .ch1_gtyrxn_in (ch1_gtyxn),
    .ch1_gtyrxp_in (ch1_gtyxp),
    .ch1_gtytxn_out (ch1_gtyxn),
    .ch1_gtytxp_out (ch1_gtyxp),
    .ch2_gtyrxn_in (ch2_gtyxn),
    .ch2_gtyrxp_in (ch2_gtyxp),
    .ch2_gtytxn_out (ch2_gtyxn),
    .ch2_gtytxp_out (ch2_gtyxp),
    .ch3_gtyrxn_in (ch3_gtyxn),
    .ch3_gtyrxp_in (ch3_gtyxp),
    .ch3_gtytxn_out (ch3_gtyxn),
    .ch3_gtytxp_out (ch3_gtyxp),
    .ch4_gtyrxn_in (ch4_gtyxn),
    .ch4_gtyrxp_in (ch4_gtyxp),
    .ch4_gtytxn_out (ch4_gtyxn),
    .ch4_gtytxp_out (ch4_gtyxp),
    .ch5_gtyrxn_in (ch5_gtyxn),
    .ch5_gtyrxp_in (ch5_gtyxp),
    .ch5_gtytxn_out (ch5_gtyxn),
    .ch5_gtytxp_out (ch5_gtyxp),
    .ch6_gtyrxn_in (ch6_gtyxn),
    .ch6_gtyrxp_in (ch6_gtyxp),
    .ch6_gtytxn_out (ch6_gtyxn),
    .ch6_gtytxp_out (ch6_gtyxp),
    .ch7_gtyrxn_in (ch7_gtyxn),
    .ch7_gtyrxp_in (ch7_gtyxp),
    .ch7_gtytxn_out (ch7_gtyxn),
    .ch7_gtytxp_out (ch7_gtyxp),
    .ch8_gtyrxn_in (ch8_gtyxn),
    .ch8_gtyrxp_in (ch8_gtyxp),
    .ch8_gtytxn_out (ch8_gtyxn),
    .ch8_gtytxp_out (ch8_gtyxp),
    .ch9_gtyrxn_in (ch9_gtyxn),
    .ch9_gtyrxp_in (ch9_gtyxp),
    .ch9_gtytxn_out (ch9_gtyxn),
    .ch9_gtytxp_out (ch9_gtyxp),
    .ch10_gtyrxn_in (ch10_gtyxn),
    .ch10_gtyrxp_in (ch10_gtyxp),
    .ch10_gtytxn_out (ch10_gtyxn),
    .ch10_gtytxp_out (ch10_gtyxp),
    .ch11_gtyrxn_in (ch11_gtyxn),
    .ch11_gtyrxp_in (ch11_gtyxp),
    .ch11_gtytxn_out (ch11_gtyxn),
    .ch11_gtytxp_out (ch11_gtyxp),
    .ch12_gtyrxn_in (ch12_gtyxn),
    .ch12_gtyrxp_in (ch12_gtyxp),
    .ch12_gtytxn_out (ch12_gtyxn),
    .ch12_gtytxp_out (ch12_gtyxp),
    .ch13_gtyrxn_in (ch13_gtyxn),
    .ch13_gtyrxp_in (ch13_gtyxp),
    .ch13_gtytxn_out (ch13_gtyxn),
    .ch13_gtytxp_out (ch13_gtyxp),
    .hb_gtwiz_reset_clk_freerun_in (hb_gtwiz_reset_clk_freerun),
    .hb_gtwiz_reset_all_in (hb_gtwiz_reset_all),
    .link_down_latched_reset_in (link_down_latched_reset),
    .link_status_out (link_status),
    .link_down_latched_out (link_down_latched)
  );


endmodule
