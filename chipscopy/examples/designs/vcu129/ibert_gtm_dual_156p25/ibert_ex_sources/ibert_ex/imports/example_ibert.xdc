
# file:ibert.xdc
####################################################################################

##**************************************************************************
set_property BITSTREAM.GENERAL.COMPRESS TRUE [current_design] 
create_clock -period 3.333 [get_ports gtm_sysclkp_i]
set_clock_groups -group [get_clocks -of_objects [get_ports gtm_sysclkp_i] -include_generated_clocks] -asynchronous
set_property C_CLK_INPUT_FREQ_HZ 300000000 [get_debug_cores dbg_hub]
set_property C_ENABLE_CLK_DIVIDER true [get_debug_cores dbg_hub]
connect_debug_port dbg_hub/clk [get_pins u_ibufgds/O]


set_property LOC GTM_REFCLK_X0Y1 [get_cells i_ibufds_gtm[0].u_buf_refclk]

create_clock -period 6.4 [get_pins i_ibufds_gtm[0].u_buf_refclk/O]
set_clock_groups -group [get_clocks -of_objects [get_pins i_ibufds_gtm[0].u_buf_refclk/O] -include_generated_clocks] -asynchronous

create_clock -period 5.12 [get_pins u_ibert_gtm_core/inst/DUAL0.U_DUAL/u_gtm_wiz_ip_top*/inst/dual0/gtm_dual_inst/CH0_DMONITOROUTCLK]
create_clock -period 5.12 [get_pins u_ibert_gtm_core/inst/DUAL0.U_DUAL/u_gtm_wiz_ip_top*/inst/dual0/gtm_dual_inst/CH1_DMONITOROUTCLK]
set_clock_groups -asynchronous -group [get_clocks -of_objects [get_pins u_ibert_gtm_core/inst/DUAL0.U_DUAL/u_gtm_wiz_ip_top*/inst/dual0/gtm_dual_inst/CH0_DMONITOROUTCLK] -include_generated_clocks]
set_clock_groups -asynchronous -group [get_clocks -of_objects [get_pins u_ibert_gtm_core/inst/DUAL0.U_DUAL/u_gtm_wiz_ip_top*/inst/dual0/gtm_dual_inst/CH1_DMONITOROUTCLK] -include_generated_clocks]

##
## System clock pin locs and timing constraints
##
set_property PACKAGE_PIN AW35 [get_ports gtm_sysclkp_i]
set_property IOSTANDARD DIFF_SSTL12 [get_ports gtm_sysclkp_i]

set_property LOC GTM_DUAL_X0Y1 [get_cells u_ibert_gtm_core/inst/DUAL0.U_DUAL/u_gtm_wiz_ip_top*/inst/dual0/gtm_dual_inst]

set_case_analysis 0 [get_pins {u_ibert_gtm_core/inst/DUAL*/u_gtm_wiz_ip_top*/inst/dual0/gtm_dual_inst/PLLREFCLKSEL[2]}]
set_case_analysis 0 [get_pins {u_ibert_gtm_core/inst/DUAL*/u_gtm_wiz_ip_top*/inst/dual0/gtm_dual_inst/PLLREFCLKSEL[1]}]
set_case_analysis 1 [get_pins {u_ibert_gtm_core/inst/DUAL*/u_gtm_wiz_ip_top*/inst/dual0/gtm_dual_inst/PLLREFCLKSEL[0]}]

set_case_analysis 1 [get_pins {u_ibert_gtm_core/inst/DUAL*/u_gtm_wiz_ip_top*/inst/dual0/gtm_dual_inst/CH0_TXOUTCLKSEL[2]}]
set_case_analysis 0 [get_pins {u_ibert_gtm_core/inst/DUAL*/u_gtm_wiz_ip_top*/inst/dual0/gtm_dual_inst/CH0_TXOUTCLKSEL[1]}]
set_case_analysis 1 [get_pins {u_ibert_gtm_core/inst/DUAL*/u_gtm_wiz_ip_top*/inst/dual0/gtm_dual_inst/CH0_TXOUTCLKSEL[0]}]

set_case_analysis 1 [get_pins {u_ibert_gtm_core/inst/DUAL*/u_gtm_wiz_ip_top*/inst/dual0/gtm_dual_inst/CH1_TXOUTCLKSEL[2]}]
set_case_analysis 0 [get_pins {u_ibert_gtm_core/inst/DUAL*/u_gtm_wiz_ip_top*/inst/dual0/gtm_dual_inst/CH1_TXOUTCLKSEL[1]}]
set_case_analysis 1 [get_pins {u_ibert_gtm_core/inst/DUAL*/u_gtm_wiz_ip_top*/inst/dual0/gtm_dual_inst/CH1_TXOUTCLKSEL[0]}]

set_case_analysis 1 [get_pins {u_ibert_gtm_core/inst/DUAL*/u_gtm_wiz_ip_top*/inst/dual0/gtm_dual_inst/CH0_RXOUTCLKSEL[2]}]
set_case_analysis 0 [get_pins {u_ibert_gtm_core/inst/DUAL*/u_gtm_wiz_ip_top*/inst/dual0/gtm_dual_inst/CH0_RXOUTCLKSEL[1]}]
set_case_analysis 1 [get_pins {u_ibert_gtm_core/inst/DUAL*/u_gtm_wiz_ip_top*/inst/dual0/gtm_dual_inst/CH0_RXOUTCLKSEL[0]}]

set_case_analysis 1 [get_pins {u_ibert_gtm_core/inst/DUAL*/u_gtm_wiz_ip_top*/inst/dual0/gtm_dual_inst/CH1_RXOUTCLKSEL[2]}]
set_case_analysis 0 [get_pins {u_ibert_gtm_core/inst/DUAL*/u_gtm_wiz_ip_top*/inst/dual0/gtm_dual_inst/CH1_RXOUTCLKSEL[1]}]
set_case_analysis 1 [get_pins {u_ibert_gtm_core/inst/DUAL*/u_gtm_wiz_ip_top*/inst/dual0/gtm_dual_inst/CH1_RXOUTCLKSEL[0]}]

set_case_analysis 0 [get_pins {u_ibert_gtm_core/inst/DUAL*/u_gtm_wiz_ip_top*/inst/dual0/gtm_dual_inst/SDMDATA[*]}]

set_clock_groups -asynchronous -group [get_clocks -of_objects [get_pins u_ibert_gtm_core/inst/DUAL*/u_gtm_wiz_ip_top*/inst/dual0/gtm_dual_inst/CH0_TXPROGDIVCLK] -include_generated_clocks]
set_clock_groups -asynchronous -group [get_clocks -of_objects [get_pins u_ibert_gtm_core/inst/DUAL*/u_gtm_wiz_ip_top*/inst/dual0/gtm_dual_inst/CH1_TXPROGDIVCLK] -include_generated_clocks]
set_clock_groups -asynchronous -group [get_clocks -of_objects [get_pins u_ibert_gtm_core/inst/DUAL*/u_gtm_wiz_ip_top*/inst/dual0/gtm_dual_inst/CH1_RXPROGDIVCLK] -include_generated_clocks]
set_clock_groups -asynchronous -group [get_clocks -of_objects [get_pins u_ibert_gtm_core/inst/DUAL*/u_gtm_wiz_ip_top*/inst/dual0/gtm_dual_inst/CH0_RXPROGDIVCLK] -include_generated_clocks]

set_case_analysis 0 [get_pins {u_ibert_gtm_core/inst/DUAL*/u_gtm_wiz_ip_top*/inst/dual0/gtm_dual_inst/PLLFBDIV[0]}]
set_case_analysis 1 [get_pins {u_ibert_gtm_core/inst/DUAL*/u_gtm_wiz_ip_top*/inst/dual0/gtm_dual_inst/PLLFBDIV[1]}]
set_case_analysis 1 [get_pins {u_ibert_gtm_core/inst/DUAL*/u_gtm_wiz_ip_top*/inst/dual0/gtm_dual_inst/PLLFBDIV[2]}]
set_case_analysis 1 [get_pins {u_ibert_gtm_core/inst/DUAL*/u_gtm_wiz_ip_top*/inst/dual0/gtm_dual_inst/PLLFBDIV[3]}]
set_case_analysis 0 [get_pins {u_ibert_gtm_core/inst/DUAL*/u_gtm_wiz_ip_top*/inst/dual0/gtm_dual_inst/PLLFBDIV[4]}]
set_case_analysis 0 [get_pins {u_ibert_gtm_core/inst/DUAL*/u_gtm_wiz_ip_top*/inst/dual0/gtm_dual_inst/PLLFBDIV[5]}]
set_case_analysis 1 [get_pins {u_ibert_gtm_core/inst/DUAL*/u_gtm_wiz_ip_top*/inst/dual0/gtm_dual_inst/PLLFBDIV[6]}]
set_case_analysis 0 [get_pins {u_ibert_gtm_core/inst/DUAL*/u_gtm_wiz_ip_top*/inst/dual0/gtm_dual_inst/PLLFBDIV[7]}]
