#!/bin/sh
# The next line is executed by /bin/sh, but not tcl \
exec /usr/local/bin/tclsh8.3 $0 ${1+"$@"}

## read the xml dictionary files and output a list of headwords

package require xml
package require stem

set tag {}

proc clean_word {word} {
    set word [string tolower [string trim $word]]
    regsub -all {[^a-z -]} $word {} word
    return $word
}
 
set verbforms {}
proc collect {data args} {
    global tag headword words verbforms errlog
    switch -glob $tag {
	headword {	
	    set headword [clean_word $data]
	    set words($headword) 1
#	    puts "$headword"
	}
	*form {
	    regsub -all {(,|or|\))} $data {} data
	    set theforms [split $data]
	    if {[llength $theforms] > 5} { 
		puts $errlog "bad verbforms for $headword"
	    } else {
		foreach v $theforms {
		    if {$v != {}} {
#			puts "verb($headword) {$v}"
			## record this as a word
			set words($v) 1
		    }
		}
	    }
	}
    }
    return {}
}

## add any new undefined words to undefined
proc check_text {text undefined} {
    global words errlog undefindex headword

    set result {}
    foreach w [split $text] {
	set w [clean_word $w]
	if {[info exists words($w)]} {
	    ## ok
	} elseif {[info exists words([clean_word [stem::stem $w]])]} {
	    ## also ok, the word stem exists
	} else {
	    puts $errlog "$w : [clean_word [stem::stem $w]]"
	    ## insert $w into undefined if it's not already there
	    if {[lsearch -exact $undefined $w] == -1} {
		lappend undefined $w
	    }
	    ## and add headword to the inverted index for $w
	    if {[info exists undefindex($w)]} {
		if {[lsearch -exact $undefindex($w) $headword] == -1} {
		    lappend undefindex($w) $headword 
		}
	    } else { 
		set undefindex($w) $headword
	    }
	}
    }
    return $undefined
}

set undefined {}
proc check {data args} {
    global tag headword words undefined undeflog
    switch $tag {
	headword {	
	    if {[info exists headword]} {
		if {[llength $undefined] > 0} {
		    puts "$headword:\t[lsort $undefined]"
		    foreach ick $undefined {
			puts $undeflog $ick
		    }
		}
		set undefined {}
	    }
	    set headword [clean_word $data]
	}
	definition {
	    set undefined [check_text $data $undefined]
	} 
    }
    return {}
}


proc start {name attlist args} {
    global tag 
    set tag $name
}


proc make_parser {} {
    return [xml::parser\
		-characterdatacommand collect\
		-elementstartcommand  start
	       ]
}

proc make_check_parser {} {
    return [xml::parser\
		-characterdatacommand check\
		-elementstartcommand  start
	       ]
}

set errlog [open headword.errlog w]
set undeflog [open undefined.txt w]


foreach in $argv {
    if {[catch {open $in} ch]} {
	puts stderr "unable to open file \"$in\""             
	exit 1
    }
    set p [make_parser]
    if {[catch {$p parse [read $ch]} err]} {
	puts stderr $err
	exit 1
    }
    catch {close $ch}
}


foreach in $argv {
    if {[catch {open $in} ch]} {
	puts stderr "unable to open file \"$in\""             
	exit 1
    }
    set p [make_check_parser]
    if {[catch {$p parse [read $ch]} err]} {
	puts stderr $err
	exit 1
    }
    catch {close $ch}
}

close $errlog
close $undeflog 

set idx [open undefined.inv w]
foreach k [array names undefindex] {
    puts $idx "$k:[llength $undefindex($k)]:\t[lsort $undefindex($k)]"
}
close $idx

## write out the words
set idx [open words.txt w]
foreach k [array names words] {
    puts $idx "$k"
}
close $idx


## Local Variables:
## mode: tcl
## End:
