set origin_dir [file normalize [file dirname [info script]]]
set project_root [file join $origin_dir project_gtm121_156p25]
set example_root [file join $origin_dir ibert_ex_gtm121_156p25]

file delete -force $project_root $example_root

create_project project_gtm121_156p25 $project_root -part xcvu29p-fsga2577-3-e -force

create_ip -name ibert_ultrascale_gtm -vendor xilinx.com -library ip -module_name ibert
set_property -dict [list \
    CONFIG.C_PROTOCOL_DUAL0 {None} \
    CONFIG.C_PROTOCOL_DUAL1 {Custom_1_/_25_Gbps} \
    CONFIG.C_REFCLK_SOURCE_DUAL_1 {MGTREFCLK0_121} \
    CONFIG.C_PROTOCOL_REFCLK_FREQUENCY_1 {156.25} \
    CONFIG.C_PROTOCOL_MAXLINERATE_1 {25} \
    CONFIG.C_PROTOCOL_PLL_1 {NRZ} \
    CONFIG.C_SYSCLK_FREQUENCY {300} \
    CONFIG.C_SYSCLK_IO_PIN_LOC_P {AW35} \
    CONFIG.C_SYSCLK_IO_PIN_LOC_N {AW36} \
    CONFIG.C_SYSCLK_IO_PIN_STD {DIFF_SSTL12} \
    CONFIG.Component_Name {ibert} \
] [get_ips ibert]

puts "==== REQUESTED_CONFIG ===="
foreach prop [list \
    CONFIG.C_PROTOCOL_DUAL1 \
    CONFIG.C_REFCLK_SOURCE_DUAL_1 \
    CONFIG.C_PROTOCOL_REFCLK_FREQUENCY_1 \
    CONFIG.C_PROTOCOL_MAXLINERATE_1 \
    CONFIG.C_PROTOCOL_PLL_1 \
    CONFIG.C_SYSCLK_FREQUENCY \
    CONFIG.C_SYSCLK_IO_PIN_LOC_P \
    CONFIG.C_SYSCLK_IO_PIN_LOC_N \
    CONFIG.C_SYSCLK_IO_PIN_STD \
] {
    puts "$prop=[get_property $prop [get_ips ibert]]"
}

generate_target all [get_ips ibert]
open_example_project -force -dir $example_root [get_ips ibert]
close_project
open_project [file join $example_root ibert_ex ibert_ex.xpr]

set xdc_path [file join $example_root ibert_ex imports example_ibert.xdc]
if {![file exists $xdc_path]} {
    set xdc_matches [glob -nocomplain -types f [file join $example_root * imports example_ibert.xdc]]
    if {[llength $xdc_matches] == 0} {
        error "Could not locate generated example_ibert.xdc under $example_root"
    }
    set xdc_path [lindex $xdc_matches 0]
}

set fh [open $xdc_path r]
set xdc_text [read $fh]
close $fh

foreach required [list \
    {set_property LOC GTM_REFCLK_X0Y1} \
    {create_clock -period 6.4} \
    {set_property PACKAGE_PIN AW35} \
    {set_property LOC GTM_DUAL_X0Y1} \
] {
    if {[string first $required $xdc_text] < 0} {
        error "Generated XDC $xdc_path does not contain required text: $required"
    }
}

if {[string first {set_property IOSTANDARD DIFF_SSTL12} $xdc_text] < 0} {
    puts "WARN: Generated XDC did not carry DIFF_SSTL12; board file documents AW35/AW36 as DIFF_SSTL12, generated text follows:"
    regexp -line {set_property IOSTANDARD .+gtm_sysclkp_i.} $xdc_text match
    puts $match
}

puts "GENERATED_XDC=$xdc_path"
set_property top example_ibert [current_fileset]
update_compile_order -fileset sources_1
launch_runs impl_1 -to_step write_bitstream -jobs 8
wait_on_run impl_1

set impl_status [get_property STATUS [get_runs impl_1]]
puts "GTM_IMPL_STATUS=$impl_status"
if {![string match "*Complete*" $impl_status]} {
    error "GTM implementation did not complete: $impl_status"
}

set bit_matches [glob -nocomplain -types f [file join $example_root * *.runs impl_1 example_ibert.bit]]
set ltx_matches [glob -nocomplain -types f [file join $example_root * *.runs impl_1 example_ibert.ltx]]
puts "BIT_PATH=[lindex $bit_matches 0]"
puts "LTX_PATH=[lindex $ltx_matches 0]"
close_project
exit
