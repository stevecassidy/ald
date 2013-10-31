    if {0} {
    ## [cf2]noun [cf1] gives the part of speech as long as it's at  
    ## the start of the line
    if {[regexp {\[cf2\]([^\[]*)\[cf1\](.*)} $line => pos line]} {
	if {[info exists form]} {
	    set posel [tag_text pos $form $pos]
	} else {
	    carp "no form for part of speech:" $pos
	}
    }
    ## in some cases the closing [cf1] might be on the next line
    if {[regexp {\[cf2\]([^\[]*) *$} $line => pos]} {
	if {[info exists form]} {
	    set posel [tag_text pos $form $pos]
	} else {
	    carp "no form for part of speech:" $pos
	}
	set line {}
    }

    
    ## if we have a pos tag then we can move on to the definition
    if {![info exists defn] && [info exists posel] && [info exists form]} {
	set defn [create_tag $form definition]
    }

}

    if {0} {
    ## bold: \optima,0\[cf3]A\minion,0\[cf1] 
    set boldre {([^\\]*)(\\(optima|minion),0\\)?\[cf[23]\]([^\\]*)(\\(optima|minion),0\\)?\[cf1\]([^\\]*)}
    set boldbits [regexp -inline -all -- $boldre $line] 

    if {$boldbits != {}} {
	set line {}
    }
    foreach {match pre ig ig btext ig ig post} $boldbits {
	set line [join [list $pre |* $btext *| $post] " "]
    }	

    ## bold words are given as [cf2]word[cf1] and can get used
    ## for various means, try to catch the ones that are just boldness 
    if {[regexp {(.*[^\\])(\\minion,0\\)?\[cf2\]([^\\\[]+)(\\minion,0\\)?\[cf1\](.*)} $line => pre ignore btext ignore post]} {
	# just now we'll replace this with a fake tag in the text
	set line [join [list $pre |* $btext *| $post] " "]
    }
}

    if {0} {
    ## examples are introduced by [cf2] and separated by [j33]
    if {[regexp {(.*)\[cf2\](.*)\[j33\](.*)} $line => pre etext post]} {
#	puts "whole example: {$pre} {$etext} {$post}"
	# create an example node
	if {[info exists form]} {
	    set example [create_tag $form example]
	} else {
	    carp "no form to put this example in:" $etext
	}
	## add the pre text to the current definition  
	if [info exists defn] {
	    add_text $defn $pre
	} else {
	    carp "no defn for this text:" $pre
	}
	add_text $example $etext 
	set line $post
    }

    if {[regexp {(.*)\[cf2\](.*)} $line => pre post]} {
#	puts "example2: {$pre} {$post}"
	# create an example node
	if {[info exists form]} {
	    set example [create_tag $form example]
	} else {
	    carp "no form to put this example in:" $post
	}
	## add the pre text to the current definition
	add_text_to_oneof {note defn} $pre 
	set line $post
    }


    if {[regexp {(.*)\[j33\](.*)} $line => pre post]} {
#	puts "two examples: {$pre} {$post}"
	## add pre to existing example
	if [info exists example] {
	    add_text $example $pre
	} else {
	    carp "losing example text:" $pre
	}
	# create an example node
	if {[info exists form]} {
	    set example [create_tag $form example]
	} else {
	    carp "no form to put this example in:" $post
	}
	set line $post
    }
}
