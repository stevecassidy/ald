#!/bin/sh
# The next line is executed by /bin/sh, but not tcl \
exec /usr/local/bin/tclsh8.3 $0 ${1+"$@"}

if [catch {open [lindex $argv 0]} in] {
    error "Can't open file"
}

while {[gets $in line] >= 0} {

    ## remove [xx commands
    foreach cmd {bh ch ct fp gc nb np sf sp xc xn xx xs} {
	regsub -all "\\\[$cmd" $line { } line
    }


    ## remove <>
    regsub -all {<>} $line { } line


    ## remove square bracketed commands
    regsub -all {(\[[^\]]*\])} $line { } line
    ## now remove \\ cmds
    regsub -all {(\\[^\\]*\\)} $line { } line

    puts $line

}




## Local Variables:
## mode: tcl
## End:
