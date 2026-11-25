
// file: ibert.sv
//////////////////////////////////////////////////////////////////////////////

//
// Module example_ibert

//////////////////////////////////////////////////////////////////////////////
`define C_NUM_DUALS 1
module example_ibert
(
  // GT top level ports
  input  wire  d0_ch0_rxp_in,
  input  wire  d0_ch0_rxn_in,
  input  wire  d0_ch1_rxp_in,
  input  wire  d0_ch1_rxn_in ,
  output wire  d0_ch0_txp_out,
  output wire  d0_ch0_txn_out,
  output wire  d0_ch1_txp_out,
  output wire  d0_ch1_txn_out,

  input        gtm_sysclkp_i,
  input        gtm_sysclkn_i,

  input        [`C_NUM_DUALS-1:0] gtm_refclkp_i,
  input        [`C_NUM_DUALS-1:0] gtm_refclkn_i
);


  //
  // Ibert refclk internal signals
  //
   wire  [`C_NUM_DUALS-1:0] gtm_refclk_i;
   wire  gtm_sysclk_i;
   wire  s_dclk;
   reg [7:0] sysmon_daddr_in = 8'd0;
   wire sysmon_reset_in;
   wire sysmon_drdy_out;
   wire [15:0] sysmon_do_out;
   wire [1:0] sysmon_slave_sel;
   wire sysmon_den_in;

  generate
  genvar i;
    for (i=0; i < `C_NUM_DUALS; i=i+1) begin : i_ibufds_gtm
    //
    // Refclk IBUFDS instantiations
    //
      IBUFDS_GTM u_buf_refclk
        (
          .O            (gtm_refclk_i[i]),
          .ODIV2        (),
          .CEB          (1'b0),
          .I            (gtm_refclkp_i[i]),
          .IB           (gtm_refclkn_i[i])
        );
      end
  endgenerate

  //
  // Sysclock IBUFDS instantiation
  //
  IBUFGDS
   #(.DIFF_TERM("FALSE"))
   u_ibufgds
    (
      .I(gtm_sysclkp_i),
      .IB(gtm_sysclkn_i),
      .O(gtm_sysclk_i)
    );

  //
  // IBERT core instantiation
  //
  ibert u_ibert_gtm_core
  (
    .d0_gtrefclk_i      (gtm_refclk_i[0]),
    .d0_gtnorthrefclk_i (1'b0),
    .d0_gtsouthrefclk_i (1'b0),
    .d0_gtm_ch0_rxp_in  (d0_ch0_rxp_in ),
    .d0_gtm_ch0_rxn_in  (d0_ch0_rxn_in ),
    .d0_gtm_ch1_rxp_in  (d0_ch1_rxp_in ),
    .d0_gtm_ch1_rxn_in  (d0_ch1_rxn_in ),
    .d0_gtm_ch0_txp_out (d0_ch0_txp_out),
    .d0_gtm_ch0_txn_out (d0_ch0_txn_out),
    .d0_gtm_ch1_txp_out (d0_ch1_txp_out),
    .d0_gtm_ch1_txn_out (d0_ch1_txn_out),
    .sysmon_drdy_out(sysmon_drdy_out),
    .sysmon_do_out(sysmon_do_out),
    .sysmon_slave_sel(sysmon_slave_sel),
    .sysmon_reset_in(sysmon_reset_in),
    .sysmon_den_in(sysmon_den_in),
    .s_dclk(s_dclk),
    .clk(gtm_sysclk_i)
   );


 ibert_SysMon U_SYSMON (
  .di_in(16'd0),              
  .daddr_in(sysmon_daddr_in), 
  .den_in(sysmon_den_in),     
  .dwe_in(1'b0),              
  .drdy_out(sysmon_drdy_out), 
  .do_out(sysmon_do_out),     
  .dclk_in(s_dclk),     
  .reset_in(sysmon_reset_in), 
  .channel_out(),            
  .eoc_out(),                 
  .alarm_out(),               
  .eos_out(),                 
  .busy_out()                
);
endmodule
