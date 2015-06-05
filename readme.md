Australian Learners Dictionary
==============

This project contains data from the print version of the 
Australian Learners Dictionary, published by NCELTR at Macquarie University in 1997. 

The dictionary was edited by Chris Candlin and David Blair and was designed
to support second language learners of Australian English.   This data has now
been made available by Macquarie University to support research.  It is 
distributed under a Creative Commons Non Commercial Sharealike Licence
https://creativecommons.org/licenses/by-nc/2.5/au/

The data here represents the only electronic record of the final publication
and is in the form of typesetting files from the publisher.  There are 
also partial data files in what looks like CSV format for some entries but these
are not complete.   Copy editing was done on the print version and so the
typesetting files are the only true record of the published dictionary. 

The format of the data in the typesetting files is not documented.  

Some code was written a long time ago to try to extract structured data from
the typesetting files with a goal of being able to produce a second edition. 
This code is written in Tcl and extracts entries from the data to generate
an XML version, however it is not complete and not fully tested. 

Contents of this project
-----------------

* data: DTA (looks like CSV) and NDX files for some entries
* typesetting: one file per letter, typesetting format
* typesetting/txt: typesetting files with unix line endings as .txt files
* tcl: code written to process the data and convert to XML
* dines: code in C++ written to extract just the pronunciation data
* xsl: stylesheets used to manipulate XML output of tcl code
* output: sample output of tcl scripts and other products of earlier work


