#!/bin/sh
# The next line is executed by /bin/sh, but not tcl \
exec /usr/local/bin/tclsh8.3 $0 ${1+"$@"}

if [catch {open [lindex $argv 0]} in] {
    error "Can't open file"
}

while {[gets $in line] >= 0} {

    ## get square bracketed commands
    set cmds [regexp -all -inline -- {(\[[^\]]*\])} $line]
    foreach c $cmds {
	puts $c
    }
    ## now get \\ cmds
    set cmds [regexp -all -inline -- {(\\[^\\]*\\)} $line]
    foreach c $cmds {
	puts $c
    }

}




## Local Variables:
## mode: tcl
## End:
