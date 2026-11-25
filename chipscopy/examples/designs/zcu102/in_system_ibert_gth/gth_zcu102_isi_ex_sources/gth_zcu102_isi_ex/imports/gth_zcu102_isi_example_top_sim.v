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

module gth_zcu102_isi_example_top_sim ();


  // -------------------------------------------------------------------------------------------------------------------
  // Signal declarations and basic example design stimulus
  // -------------------------------------------------------------------------------------------------------------------

  // Declare wires to loop back serial data ports for transceiver channel 0
  wire ch0_gthxn;
  wire ch0_gthxp;

  // Declare wires to loop back serial data ports for transceiver channel 1
  wire ch1_gthxn;
  wire ch1_gthxp;

  // Declare wires to loop back serial data ports for transceiver channel 2
  wire ch2_gthxn;
  wire ch2_gthxp;

  // Declare wires to loop back serial data ports for transceiver channel 3
  wire ch3_gthxn;
  wire ch3_gthxp;

  // Declare wires to loop back serial data ports for transceiver channel 4
  wire ch4_gthxn;
  wire ch4_gthxp;

  // Declare wires to loop back serial data ports for transceiver channel 5
  wire ch5_gthxn;
  wire ch5_gthxp;

  // Declare wires to loop back serial data ports for transceiver channel 6
  wire ch6_gthxn;
  wire ch6_gthxp;

  // Declare wires to loop back serial data ports for transceiver channel 7
  wire ch7_gthxn;
  wire ch7_gthxp;

  // Declare wires to loop back serial data ports for transceiver channel 8
  wire ch8_gthxn;
  wire ch8_gthxp;

  // Declare wires to loop back serial data ports for transceiver channel 9
  wire ch9_gthxn;
  wire ch9_gthxp;

  // Declare wires to loop back serial data ports for transceiver channel 10
  wire ch10_gthxn;
  wire ch10_gthxp;

  // Declare wires to loop back serial data ports for transceiver channel 11
  wire ch11_gthxn;
  wire ch11_gthxp;

  // Declare wires to loop back serial data ports for transceiver channel 12
  wire ch12_gthxn;
  wire ch12_gthxp;

  // Declare wires to loop back serial data ports for transceiver channel 13
  wire ch13_gthxn;
  wire ch13_gthxp;

  // Declare wires to loop back serial data ports for transceiver channel 14
  wire ch14_gthxn;
  wire ch14_gthxp;

  // Declare register to drive reference clock at location MGTREFCLK0_X1Y3
  reg mgtrefclk0_x1y3 = 1'b0;

  // Drive that reference clock at the appropriate frequency
  // NOTE: the following simulation reference clock period may be up to +/- 2ps from its nominal value, due to rounding
  // within Verilog timescale granularity, especially when transmitter and receiver reference clock frequencies differ
  initial begin
    mgtrefclk0_x1y3 = 1'b0;
    forever
      mgtrefclk0_x1y3 = #3200 ~mgtrefclk0_x1y3;
  end

  // Declare register to drive reference clock at location MGTREFCLK0_X0Y2
  reg mgtrefclk0_x0y2 = 1'b0;

  // Drive that reference clock at the appropriate frequency
  // NOTE: the following simulation reference clock period may be up to +/- 2ps from its nominal value, due to rounding
  // within Verilog timescale granularity, especially when transmitter and receiver reference clock frequencies differ
  initial begin
    mgtrefclk0_x0y2 = 1'b0;
    forever
      mgtrefclk0_x0y2 = #3200 ~mgtrefclk0_x0y2;
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

  gth_zcu102_isi_example_top example_top_inst (
    .mgtrefclk0_x0y2_p (mgtrefclk0_x0y2),
    .mgtrefclk0_x0y2_n (~mgtrefclk0_x0y2),
    .mgtrefclk0_x1y3_p (mgtrefclk0_x1y3),
    .mgtrefclk0_x1y3_n (~mgtrefclk0_x1y3),
    .ch0_gthrxn_in (ch0_gthxn),
    .ch0_gthrxp_in (ch0_gthxp),
    .ch0_gthtxn_out (ch0_gthxn),
    .ch0_gthtxp_out (ch0_gthxp),
    .ch1_gthrxn_in (ch1_gthxn),
    .ch1_gthrxp_in (ch1_gthxp),
    .ch1_gthtxn_out (ch1_gthxn),
    .ch1_gthtxp_out (ch1_gthxp),
    .ch2_gthrxn_in (ch2_gthxn),
    .ch2_gthrxp_in (ch2_gthxp),
    .ch2_gthtxn_out (ch2_gthxn),
    .ch2_gthtxp_out (ch2_gthxp),
    .ch3_gthrxn_in (ch3_gthxn),
    .ch3_gthrxp_in (ch3_gthxp),
    .ch3_gthtxn_out (ch3_gthxn),
    .ch3_gthtxp_out (ch3_gthxp),
    .ch4_gthrxn_in (ch4_gthxn),
    .ch4_gthrxp_in (ch4_gthxp),
    .ch4_gthtxn_out (ch4_gthxn),
    .ch4_gthtxp_out (ch4_gthxp),
    .ch5_gthrxn_in (ch5_gthxn),
    .ch5_gthrxp_in (ch5_gthxp),
    .ch5_gthtxn_out (ch5_gthxn),
    .ch5_gthtxp_out (ch5_gthxp),
    .ch6_gthrxn_in (ch6_gthxn),
    .ch6_gthrxp_in (ch6_gthxp),
    .ch6_gthtxn_out (ch6_gthxn),
    .ch6_gthtxp_out (ch6_gthxp),
    .ch7_gthrxn_in (ch7_gthxn),
    .ch7_gthrxp_in (ch7_gthxp),
    .ch7_gthtxn_out (ch7_gthxn),
    .ch7_gthtxp_out (ch7_gthxp),
    .ch8_gthrxn_in (ch8_gthxn),
    .ch8_gthrxp_in (ch8_gthxp),
    .ch8_gthtxn_out (ch8_gthxn),
    .ch8_gthtxp_out (ch8_gthxp),
    .ch9_gthrxn_in (ch9_gthxn),
    .ch9_gthrxp_in (ch9_gthxp),
    .ch9_gthtxn_out (ch9_gthxn),
    .ch9_gthtxp_out (ch9_gthxp),
    .ch10_gthrxn_in (ch10_gthxn),
    .ch10_gthrxp_in (ch10_gthxp),
    .ch10_gthtxn_out (ch10_gthxn),
    .ch10_gthtxp_out (ch10_gthxp),
    .ch11_gthrxn_in (ch11_gthxn),
    .ch11_gthrxp_in (ch11_gthxp),
    .ch11_gthtxn_out (ch11_gthxn),
    .ch11_gthtxp_out (ch11_gthxp),
    .ch12_gthrxn_in (ch12_gthxn),
    .ch12_gthrxp_in (ch12_gthxp),
    .ch12_gthtxn_out (ch12_gthxn),
    .ch12_gthtxp_out (ch12_gthxp),
    .ch13_gthrxn_in (ch13_gthxn),
    .ch13_gthrxp_in (ch13_gthxp),
    .ch13_gthtxn_out (ch13_gthxn),
    .ch13_gthtxp_out (ch13_gthxp),
    .ch14_gthrxn_in (ch14_gthxn),
    .ch14_gthrxp_in (ch14_gthxp),
    .ch14_gthtxn_out (ch14_gthxn),
    .ch14_gthtxp_out (ch14_gthxp),
    .hb_gtwiz_reset_clk_freerun_in (hb_gtwiz_reset_clk_freerun),
    .hb_gtwiz_reset_all_in (hb_gtwiz_reset_all),
    .link_down_latched_reset_in (link_down_latched_reset),
    .link_status_out (link_status),
    .link_down_latched_out (link_down_latched)
  );


endmodule
