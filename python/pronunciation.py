""" Functions to extract a SAMPA pronunciation dictionary from
    the typesetting files for the Australian Learner's Dictionary."""

import string
import os
import csv
import re
import getopt
import sys

USAGE = """ USAGE: python pronunciation.py [OPTION]... DIRECTORY OUT_FILE

          Given typesetting files in DIRECTORY, produce SAMPA lexicon
          as OUT_FILE.

          Options:

          -d DELIMITER
                use the given delimiter for the lexicon file

          -m CHAR_MAP
                use the given character map file for the translation
                
          -a AUS_MAP
                use the given character map for the SAMPA_Aus conversion
                
          -s SUFFIX_RULES
                (optional) extend the dictionary with the given suffix rules
          """

class UnknownSymbolError(Exception):
    """Raised when an unknown symbol is encountered while
       attempting to convert the typesetting files to    
       SAMPA"""

    def __init__(self, symbol):
        self.symbol = symbol


class AusConversionError(Exception):
    """Raised when an unknown symbol is encountered while
       attempting to convert to SAMPA_Aus"""

    def __init__(self, bad_string):
        self.bad_string = bad_string
        
class SuffixRule:
    """Represents a rule for adding a suffix to a word"""
    
    def __init__(self, ortho_condition, pron_condition, 
                 ortho_suffix, pron_suffix):
                 
        """Condition (regex) on the orthographic representation of the word
           for the suffix to be applied"""
        self.ortho_condition = ortho_condition
        
        """Condition (regex) on the SAMPA_Aus pronunciation of the word
           for the suffix to be applied"""
        self.pron_condition = pron_condition
        
        """Suffix as appended to the orthographic representation"""
        self.ortho_suffix = ortho_suffix
        
        """Suffix as appended to the SAMPA_Aus representation"""
        self.pron_suffix = pron_suffix


def make_sampa_lex(directory, out_file,
                   delimiter=None, 
                   char_map_filename=None,
                   aus_map_filename=None,
                   suffix_rule_filename=None,
                   include_lex_filename=None):
    """Take the directory of typesetting files and produce
       a MAUS-compatible SAMPA lexicon"""

    delimiter = delimiter or '\t'
    char_map_filename = char_map_filename or 'char_map.txt'
    aus_map_filename = aus_map_filename or 'aus_map.txt'

    typeset_dict = compile_dict(directory)
    sampa_dict = dict_convert(typeset_dict, char_map_filename)
    
    if suffix_rule_filename is not None:
        suffix_rules = load_suffix_rules(suffix_rule_filename)
        sampa_dict = apply_suffix_rules(sampa_dict, suffix_rules)

    if include_lex_filename is not None:
        sampa_dict.update(load_lex(include_lex_filename))
        
    dict_to_lex(sampa_dict, out_file, delimiter)


def load_lex(lex_filename):
    """Load a lexicon file as a dictionary"""

    dictionary = dict()

    with open(lex_filename,  'r') as f:
        for line in f:
            line_pair = line.split()
            dictionary[line_pair[0]] = line_pair[1]

    return dictionary


def dict_convert(dictionary,
                 char_map_filename='char_map.txt', 
                 aus_map_filename='aus_map.txt'):
    """Take a word -> typeset pronunciation dictionary and
       produce a word -> SAMPA pronunciation dictionary"""

    converted_dict = dict()
    char_map = load_char_map(char_map_filename)
    aus_map = load_char_map(aus_map_filename)

    for k, v in dictionary.items():
        try:
            converted_dict[k] = pronstring_to_sampa(v, char_map, aus_map)
        except UnknownSymbolError as use:
            print('Unknown symbol encountered.')
            print('Word: ' + k)
            print('Pronunciation: ' + v)
            print('Symbol: ' + use.symbol)
            raise

    return converted_dict


def load_char_map(filename):
    """Load a character map (as a dictionary) from a file"""
    
    char_map = dict()
    
    lists = load_lists(filename, 2)
    for list_pair in lists:
        char_map[list_pair[0]] = list_pair[1]
        
    return char_map
    
    
def apply_suffix_rules(dictionary, rules):
    """Apply a set of suffix rules to a dictionary 
       and return the extended dictionary"""
       
    extended_dict = dict(dictionary)
    
    for rule in rules:
        for orth, pron in dictionary.items():
            if re.search(rule.ortho_condition, orth) and \
               re.search(rule.pron_condition, pron) and \
               orth + rule.ortho_suffix not in extended_dict.keys():
                extended_dict[orth + rule.ortho_suffix] = pron + rule.pron_suffix
                
    return extended_dict

    
def load_suffix_rules(filename):
    """Load a set of suffix rules from a file"""
    
    suffixes = set()
    lists = load_lists(filename, 4)
    
    for rule_list in lists:
        suffixes.add(SuffixRule(rule_list[0], rule_list[1], rule_list[2], rule_list[3]))
        
    return suffixes
    

def load_lists(filename, n):
    """Load some lists of symbols from a file, one list per line.
       Each list should contain n symbols, and the symbols are
       whitespace-delimited. If a line does not contain
       at least n symbols, the list corresponding to that
       line will be padded with empty strings. """

    loaded_lists = []

    # anything appearing after a hash on a line is a comment
    comment_regex = re.compile('#.*$', re.DOTALL)

    with open(filename, 'r') as f:
        for line in f:
            line = comment_regex.sub('', line)
            if not line.strip(): continue
            symbols = line.split()
            if len(symbols) >= n:
                loaded_lists.append(symbols[:n])
            else:
                while len(symbols) < n:
                    symbols.append('')
                loaded_lists.append(symbols)

    return loaded_lists
    

def convert_to_aus_sampa(sampa_str, aus_map):
    """Take a pronunciation string in the SAMPA variant used in Dines'
       mapping and convert it to SAMPA_Aus."""
       
    aus_str = ''   
      
    # get a list of the keys, longest first, then match them with the string
    sorted_keys = sorted(aus_map.keys(), key=lambda x: len(x), reverse=True)
    while sampa_str:
        matched = False
        for key in sorted_keys:
            match = re.match(re.escape(key), sampa_str)
            if match:
                matched = True
                aus_str += aus_map[match.group()]
                sampa_str = sampa_str[match.end():]
                break
        
        if not matched:
            print("Could not convert to SAMPA_Aus: " + sampa_str)
            raise AusConversionError(sampa_str)
                
    return aus_str


def pronstring_to_sampa(pronstring, char_map, aus_map):
    """Take a pronunciation string from the typesetting file and
       produce the equivalent SAMPA representation."""

    # divide the string into typesetting symbols (with special cases)
    symbols = []
    str_index = 0
    while str_index < len(pronstring):
        symb = pronstring[str_index]

        #handle symbols like [j11]
        if symb == '[':
            while str_index < len(pronstring):
                str_index += 1
                symb += pronstring[str_index] 
                if pronstring[str_index] == ']': break

                # check for some other special cases without closing brackets
                if symb == '[ch' or symb == '[fj': break

        #repeated periods are one symbol
        elif symb == '.':
            while str_index + 1 < len(pronstring):
                if pronstring[str_index + 1] == '.':
                    symb += pronstring[str_index + 1]
                else: break
                str_index += 1
                
        if symb.strip(): symbols.append(symb) #exclude whitespace
        str_index += 1

    try:
        #translate each symbol to SAMPA using the loaded charmap
        sampa_str = ''.join([char_map[symb] for symb in symbols])
    except KeyError as ker:
        raise UnknownSymbolError(ker.message)
    
    #convert the SAMPA string to SAMPA_Aus
    aus_sampa_str = convert_to_aus_sampa(sampa_str, aus_map)

    return aus_sampa_str


def dict_to_lex(dictionary, out_file, delimiter='\t'):
    """Export a dictionary to a MAUS-compatible lexicon"""

    with open(out_file, 'wb') as f:
        for k in sorted(dictionary.keys()):
            f.write(k + delimiter + dictionary[k] + '\n')


def dict_to_csv(dictionary, out_file, dialect='excel-tab'):
    """Export a dictionary to a file (with specified csv dialect)"""
    
    with open(out_file, 'wb') as f:
        writer = csv.DictWriter(f, dictionary.keys(), dialect=dialect)
        writer.writeheader()
        writer.writerow(dictionary)
  

def compile_dict(directory):
    """Go through each typesetting file and build one big dictionary"""
    
    alphabet = list(string.ascii_lowercase)
    master_dict = dict()

    for letter in alphabet:
        filepath = os.path.join(directory, letter)
        master_dict.update(file_to_dict(filepath))

    return master_dict


def file_to_dict(filename):
    """Generate a headword -> pronunciation (in the typesetting markup)
       dictionary from a given typesetting file"""

    file_dict = dict()

    for headwords, pron in extract_prons(filename):
        for head in headwords:
            file_dict[head] = pron

    return file_dict


""" 
Regexes for strings that should not appear in a headword 
(will be stripped out, one by one, in order, when each 
headstring is processed)
"""
EXCLUDE_FROM_HEAD = ['\r', '\[nb', '\[xp.*?\[ap', \
                     '\[.*?\]', r'\\minion,0\\', "'"]

def process_headstring(headstring):
    """Take the string that spans from a definition delimiter to the
       beginning of a pronunciation string, clean it up, and try to  
       extract the headword or headwords from it"""
    
    for regex in EXCLUDE_FROM_HEAD:
        headstring = re.sub(regex, '', headstring)

    return [hs.strip().lower() for hs in headstring.split(',') if hs.strip()]


""" 
Regexes for strings that should not appear in a pronunciation
(will be stripped out, one by one, in order, when each 
pronstring is processed)
"""
EXCLUDE_FROM_PRON = [r'^\\times,0\\\[cp8\.[0-9]\]', \
                     r'\\minion,0\\\[cp8\.[0-9]\]?.$',\
                     r'\\minion,0\\']

def process_pronstring(pronstring):
    """ Process the pronunciation string to clean it up """

    pronstring = re.sub('\n|\r', ' ', pronstring)

    # remove the trailing and leading junk
    for reg in EXCLUDE_FROM_PRON:
        pronstring = re.sub(reg, '', pronstring)

    return pronstring.split(',')[0] # take only the first pronunciaton


def extract_prons(filename):
    """Extract pairs from a file, each containing a list of headwords
       and a pronunciation string"""

    pronlist = []
    for block in def_blocks(filename):
        spl = block.split('/')
        if len(spl) < 2: continue #this isn't a proper definition block 
        headstring = spl[0]

        found_pron = False
        for splstr in spl[1:]:
            if splstr.startswith(r'\times'): #prons always start like this
                pronstring = splstr
                found_pron = True
                break
            else:
                headstring += '/' + splstr

        if not found_pron: continue # no pronunciation in this block

        clean_headstring = process_headstring(headstring)
        clean_pronstring = process_pronstring(pronstring)

        if clean_pronstring != '??': # '??' indicates a missing pronunciation
            pronlist.append([clean_headstring, clean_pronstring])

    return pronlist


def def_blocks(filename):
    """Generate a list of definition blocks from the a file 
       (strings that begin with '--' or '[j31]' and end just
       before the next one of those)"""

    with open(filename, 'r') as f:
        return re.compile('\[j31\]|--').split(f.read())


def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        opts, args = getopt.getopt(argv[1:], 'hd:m:a:s:', ['help'])
    except getopt.error, msg:
        print(msg)
        print('use --help for usage information')
        sys.exit(2)

    delimiter = None
    char_map = None
    aus_map = None
    suffix_rules = None
    include_lex = None

    for o, a in opts:
        if o in ('-h', '--help'):
            print USAGE
            sys.exit(0)
        elif o == '-d':
            delimiter = a
        elif o == '-m':
            char_map = a
        elif o == '-a':
            aus_map = a
        elif o == '-s':
            suffix_rules = a
        elif o == '-l':
            include_lex = a

    if len(args) != 2:
        print('incorrect number of arguments, use --help for usage information')
        sys.exit(2)

    directory = args[0]
    out_file = args[1]

    make_sampa_lex(directory, out_file, delimiter, char_map, aus_map, suffix_rules, include_lex)


if __name__ == "__main__":
    main()
