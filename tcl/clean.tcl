#!/bin/sh
# The next line is executed by /bin/sh, but not tcl \
exec /usr/local/bin/tclsh8.3 $0 ${1+"$@"}

package require dom::tcl

array set charmap {
p	p
b	b
t	t
d	d
k	k
g	g
f	f
v	v
[j19]	T
[j21]	D
s	s
z	z
[j14]	S
[j15]	Z
m	m
n	n
[j18]	N
l	l
r	r
j	j
w	w
h	h
i	i:
[j11]	I
e	E
[j12]	A
a	a:
... 	V
[j16]	O
[j20]	o:
[j23]	U
u	u:
[j13]	@:
[j17]	@
[j24]	`
[j25]   ; 
,       ,
-	-
}

## notify lossage
proc carp {msg stuff} {
    if {![regexp {^ *$} $stuff]} {
	puts "$msg {$stuff}"
    }
}


proc phonetic {text} {
    global charmap
    # first deal with [j??] things
    foreach k [lsort [array names charmap]] {
		regsub -all {([.\[\]])} $k {\\\1} kpat
		if [regsub -all -- "$kpat" $text $charmap($k) text] {
	    	#puts "$k -> $charmap($k)"
	    	#puts "TEXT: $text"
		}
    }
    #puts "PHONES: $text"
    return $text
}

proc create_tag {top tagname} {
    return [::dom::document createElement $top $tagname]
}

proc add_text {node text} {
    ## remove any remaining font optima|minion stuff
    regsub -all {\\(optima|minion),0\\} $text {} text

    ## remove command text in square brackets, 
    ## this is just for the first phase of the ALD conversion
    ## to facilitate counting. We'll want them back later to
    ## split the definitions up more correctly
    regsub -all {\[[^\]]+\]} $text {} text

    return [::dom::document createTextNode $node $text]
}

## add the text to the first node in nodelist that exists
proc add_text_to_oneof {nodelist text} {
    
    if {$text == {}} { return }

    foreach varname $nodelist {
	if {[uplevel info exists $varname]} {
	    upvar $varname node
#	    puts "$varname text: $text" 
	    add_text $node $text
	    return
	}
    }
    carp "Nowhere to put text:" $text
}



proc tag_text {tag node text} {
    set tt [::dom::document createElement $node $tag]
    return [add_text $tt $text]
}


## split verb or plural forms: remove , and 'or' returning a list
proc split_forms {text} {
    regsub -all {(,| or )} $text { } text
    regsub -all { +} $text { } text
    if {[string equal $text { }]} {
	return {}
    } else {
	return [split $text { }]
    }
}



proc output {doc file} {
    if [catch {open $file w} out] {
	error "Problem opening $file"
    }

    set els {entry form definition}
    puts $out [dom::DOMImplementation serialize $doc -newline $els]
    close $out
}

set doc [::dom::DOMImplementation create]
set top [::dom::document createElement $doc dictionary]


if [catch {open [lindex $argv 0]} in] {
    error "Can't open input file [lindex $argv 0]"
}

while {[gets $in line]>= 0} {

    ## if the line ends in ~ just join it to the next line 
    if {[regexp {(.*)~$} $line => contline]} {
	continue
    }
    if {[info exists contline]} {
	set line "$contline$line"
	unset contline
    }

        ## remove [xx commands
    foreach cmd {bh ch ct fp fj gc nb np sf sp xc xn xx xs} {
	regsub -all "\\\[$cmd" $line {} line
    }
    ## remove <>
    regsub -all {<>} $line {} line

    ## headword, can start with --, ~--, [j111] and sometimes other 
    ## things intrude, eg. [iw-1][cj3,6,9]--accumulate
    ## (haven't done the last one yet).
    if {[regexp {^~?(\[.*\])?(--|\[j111\])(\[.*\])?(\[nb)?(.*)$} $line => w x y z head]} {
	set e [create_tag $top entry]
	tag_text headword $e $head
	catch {unset posel}
	catch {unset form}
	catch {unset defn}
	catch {unset example}
	catch {unset note}
	continue
    } 

    ## grab the pronunciation
    if [regexp {/\\times,0\\\[cp8.5\]([^\\/]*)/?\\minion,0\\\[cp8\.7\]/?(.*)} $line => pron line] {
	if [info exists e] {
	    tag_text pron $e [phonetic $pron]
	}
    } 

    ## (plural|verb) forms
    if {[regexp {\((\\minion,0\\)?\[cf2\]([a-z]+) forms? \\optima,0\\\[cf3\](.*)\\minion,0\\\[cf1\]\)(.*)} $line => ignore which forms line]} {

	# it could be that we ate too much text for the forms, check to see 
	# if the ending string is in $forms and chop if it is
	if {[regexp {(.*)\\minion,0\\\[cf1\]\)(.*)} $forms => pre post]} {
	    set forms $pre
	    set line "$post $line"
	}
	
	if [info exists e] {
	    set whichform [join [list $which form] {}]

	    foreach theform [split_forms $forms] {
		tag_text $whichform $e $theform
	    }

	} else {
	    carp "no entry for $which forms:" $forms
	}
    } 


    ## (plural|verb) forms, might be split over lines :-(
    if {[regexp {\((\\minion,0\\)?\[cf2\]([a-z]+) forms?( \\optima,0\\\[cf3\])?(.*)} $line => ignore which ignore forms]} {

	## but $forms can't contain the end form, this shouldn't happen but...
	if {[regexp {(.*)\\minion,0\\\[cf1\]\)(.*)} $forms => pre post]} {
	    set forms $pre
	    set line "$post $line"
	}
	set whichform [join [list $which form] {}]

	if [info exists e] {

	    foreach theform [split_forms $forms] {
		tag_text $whichform $e $theform
	    }

	} else {
	    carp "no entry for $whichforms forms:" $forms
	}
	set line {}
    } 

    ## and now we need to stick the extra text into the xforms next time
    if {[regexp {^(.*)\\minion,0\\\[cf1\]\)(.*)} $line => forms post]} {

	regsub {^\\optima,0\\\[cf3\]} $forms {} forms

	if {[info exists e] && [info exists whichform]} {

	    foreach theform [split_forms $forms] {
		tag_text $whichform $e $theform
	    }

	} else {
	    carp "no entry for some forms:" $forms
	}
	set line $post

    }

    ## A word form is introduced by a number in bold 
    if {[regexp {(.*)\\optima,0\\\[cf3\]\[hmp3\]([0-9a-z]+)\s*\\minion,0\\(.*)} $line => pre  number post]} {

	## pre needs to be put in an earlier <defn> if there is one, othewise?
	if {![regexp {^ *$} $pre]} {
	    add_text_to_oneof {note example defn} $pre
	}

	## create a new form with this number
	set form [create_tag $e form]
	dom::element setAttribute $form number $number

	## we're now done with the last definition
	catch {unset defn}
	catch {unset example}
	catch {unset note}

	## and create a new one
	set defn [create_tag $form definition]

	set line $post
    }

    ## or it might be just [hmp3]
    if {[regexp {(.*)\[hmp3\](.*)} $line => pre line]} {
	## add $pre to last thing
	add_text_to_oneof {note example defn} $pre
	## create a new form 
	set form [create_tag $e form]

	## we're now done with the last definition
	catch {unset defn}
	catch {unset example}
	catch {unset note}

	## and create a new one
	set defn [create_tag $form definition]
    }

    
    ## or sometimes just a bold number -- but this could be risky...
    if {[regexp  {(.*)\\optima,0\\\[cf3\]([0-9]+)\s*\\minion,0\\(.*)} $line => pre number post]} {

	## pre needs to be put in an earlier <defn> if there is one, othewise?
	if {![regexp {^ *$} $pre]} {
	    add_text_to_oneof {note example defn} $pre
	}

	## create a new form with this number
	set form [create_tag $e form]
	dom::element setAttribute $form number $number

	## we're now done with the last definition
	catch {unset defn}
	catch {unset example}
	catch {unset note}

	## and create a new one
	set defn [create_tag $form definition]

	set line $post
    }



    ## cut.tcl goes here

    ## notes are introduced by [j30]
    if {[regexp {(.*)\[j30\](.*)} $line => pre post]} {
#	puts "note: {$pre} {$post}"
	# create an example node
	if {[info exists form]} {
	    set note [create_tag $form note]
	} else {
	    carp "no form to put this note in:" $post
	}
	## add the pre text to the current definition or example
	add_text_to_oneof {example defn} $pre
	set line $post
    }



    ## just content, add it as a text node to the definition or ...
    add_text_to_oneof {note example defn e} $line
}


set outfile [lindex $argv 1]
output $doc $outfile





## Local Variables:
## mode: tcl
## End:
