                               pronunciation.py

                                    README
                                    
-------------------------------------------------------------------------------

Functions for the extraction and processing of pronunciation data from the 
typesetting files for the Australian Learners' Dictionary (ALD)

-------------------------------------------------------------------------------

                                 TYPICAL USAGE
                                
The typical usage is to run the following from the command-line:

python pronunciation.py ../typesetting aus_sampa.lex

This will produce a lexicon from the typesetting files as aus_sampa.lex. If
you wish to heuristically extend the dictionary using the suffix addition
rules, run:

python pronunciation.py -s suffix_rules.txt ../typesetting aus_sampa.lex

If you wish to incorporate another lexicon, for example the maptask
lexicon (maptask_landmarks.txt), use the -l option (the incorporated
lexicon will not be subjected to heuristic extension if the -s option
is used simultaneously with the -l option):

python pronunciation.py -l maptask_landmarks.txt ../typesetting aus_sampa.lex

For more detailed usage information run:

python pronunciation.py --help

If you want to do something more complicated, you can import as a Python
module:

>>import pronunciation as pr

-------------------------------------------------------------------------------

                                   OVERVIEW

This Python 2.7 script is designed to parse the ALD typesetting files and
extract orthographic representation -> phonetic representation pairs, and
to convert those pairs to the format required by the MAUS alignment system.

A brief overview of the typical usage: 
- For each chunk containing a definition, the raw typesetting strings
containing the headword (orthographic representation) and pronunciation
(which is comprised of typesetting directives which instruct the printer
to produce an IPA representation) are isolated.
- Each headword and pronunciation string is processed to remove extraneous
typesetting information
- Each headword is stripped of punctuation and converted to lowercase
- Each pronunciation string is converted to a SAMPA variant using tables
compiled by John Dines, and extended for this application (see char_map
below)
- Each pronunciation string is then converted to SAMPA_Aus using conversion
tables provided by Linda Buckley (see aus_map below)
- The processed headword and pronunciations are compiled into a dictionary
data structure
- The dictionary is (optionally) extended to variant forms of some words
using some rules which specify the addition of suffixes (see suffix_rules 
below). NOTE: this is a bit of a scattershot approach and will certainly
produce pronunciations for words that aren't real. If you're only going
to use the resultant lexicon to look up pronunciations of known words,
then that is probably not a problem, but otherwise, be careful.
- The dictionary is then written to a lexicon file (space-separated)

-------------------------------------------------------------------------------

                                INPUT FILES
                                
-directory: Specify the directory containing the ALD typesetting files

-char_map: This file specifies the typesetting directives -> SAMPA 
(variant used by Dines) conversion. One corresponding pair is placed
on each line, whitespace-separated. A hash character (#) is used to 
delineate comments: anything appearing after one on a line is ignored.

-aus_map: This file specifies the subsequent conversion to SAMPA_Aus,
and uses the same format as char_map. You can specify multiple characters
for each corresponding pair: longer strings will be converted in preference
to shorter ones.

-suffix_rules: This file specifies the rules for adding suffixes to words in
order to heuristically extend the dictionary. Comments can be added as in 
char_map.txt. Each line specifies one suffix addition rule, with four
whitespace-separated parts:

(1) (2) (3) (4)

(1) is a regular expression: if the orthographic representation of a word
does not match this regex, the suffix will not be added to that word

(2) is a regular expression: if the pronunciation (SAMPA_Aus) of a word
does not match this regex, the suffix will not be added to that word

(3) is the suffix to be appended to the orthographic representation of
each word that matches the regexes specified in (1) and (2)

(4) is the suffix to be appended to the SAMPA_Aus representation of
each word that matches the regexes specified in (1) and (2)

NOTE: for (3) and (4), one or more less-than characters ('<') can
be placed at the beginning of the suffix. For each of these,
one character will be deleted from the end of the word before
the suffix (minus the '<' characters) is appended. For example,
if the word is 'sky' and the suffix is '<ies', then the 'y' will
be deleted to produce 'skies'. 

Also note that the rules are applied top-to-bottom: if a suffix rule 
produces a word that collides with a word that was originally in the 
dictionary, the original will not be overwritten, but if it collides
with a word built using a suffix rule that appears on a previous line
in the suffix rule file, the suffix rule appearing on the lowest line
in the file will take precedence.
