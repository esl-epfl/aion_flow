crashbackups stop
gds read std_cells_claude/AION_inv_nand2_nor2_1.gds
if {[lsearch [cellname list topcells] {AION_inv_nand2_nor2_1}] < 0} {
    set _fp [open {/foss/designs/aion_flow/tools/aion_layout/std_cells_claude/drc/AION_inv_nand2_nor2_1.magic.drc/drc_AION_inv_nand2_nor2_1.cellmismatch} w]
    puts $_fp [cellname list topcells]
    close $_fp
    quit -noprompt
}
load AION_inv_nand2_nor2_1
set drc_rpt_path /foss/designs/aion_flow/tools/aion_layout/std_cells_claude/drc/AION_inv_nand2_nor2_1.magic.drc/AION_inv_nand2_nor2_1.magic.drc.rpt
set fout [open $drc_rpt_path w]
set oscale [cif scale out]
set cell_name AION_inv_nand2_nor2_1
select top cell
drc euclidean on
drc style drc(full)
drc check
set drcresult [drc listall why]
set count 0
puts $fout "$cell_name"
puts $fout "----------------------------------------"
foreach {errtype coordlist} $drcresult {
  puts $fout $errtype
  puts $fout "----------------------------------------"
  foreach coord $coordlist {
    set bllx [expr {$oscale * [lindex $coord 0]}]
    set blly [expr {$oscale * [lindex $coord 1]}]
    set burx [expr {$oscale * [lindex $coord 2]}]
    set bury [expr {$oscale * [lindex $coord 3]}]
    set coords [format " %.3fum %.3fum %.3fum %.3fum" $bllx $blly $burx $bury]
    puts $fout "$coords"
    set count [expr {$count + 1} ]
  }
  puts $fout "----------------------------------------"
}
puts $fout "\[INFO\] COUNT: $count"
puts $fout "\[INFO\] Should be divided by 3 or 4"
puts $fout ""
close $fout
quit -noprompt
