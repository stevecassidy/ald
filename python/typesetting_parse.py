
import json
import gzip
import rdflib
import hashlib
import string
import argparse
import sys, os
import re,codecs,collections
import json, pprint


from rdflib.namespace import XSD




#cleanup mappings
mapping=collections.OrderedDict([
    ('\\optima,0',''),
    ('\\[cf3]',''),
    ('\\minion,0',''),
    ('\\[cf1]',''),
    ('[cp8.7]',''),
    ('[hmp3]',''),
    ('\\',"'"),
    ('/',''),
    ('[j33]',''),
    ('[j30]',''),
    ('[j31]',''),
    ('[cf2]',''),
    ('[cf1]',  '.'),
    ('[cp8.5]',''),

    ('[cf3]',  'r'),
    ('[j19]',	'T'),
    ('[j21]',	'D'),
    ('[j14]',	'S'),
    ('[j15]',	'Z'),
    ('[j18]',	'N'),
    ('[j11]',	'I'),
    ('[j12]',	'A'),
    ('[j16]',	'O'),
    ('[j20]',	'o:'),
    ('[j23]',	'U'),
    ('[j13]',	'@:'),
    ('[j17]',	'@'),
    ('[j24]',	'`'),
    ('[j25]',  ';'),
    ('[ju11]',   'I'),
    ('[ch',   '"'),
    ('|', '%'),
    ('o',       '@'),
    ('[iw-1]', '@'),
    ('i',	'i:'),
    ('e',	'E'),
    ('a',	'a:'),
    ('...',	'V'),
    ('u'	,'u:'),
    ('[@l1]',''),
    ('~[fa[xp\'}]}','')
])
#maybe more rubbish
min_check=8

#patterns

#headword at start of line for after [j31]\n[j111]
headword=re.compile(r'((\[ir\(s76\),\(s75+6\)\]|\[j111\]|--\[\w+\]|\[iw1\]--|--)([\w, ]*)(\.*))')
#pronouciation ending in comment '(' or ps '[cf2]'
pronounce=re.compile(r'\/\\*times,0\\([\d\w.\/\\,\s\[\]]+?)(\[cp8.7\][\/]?)')
#comments
comment=re.compile(r'\((\\minion,0\\|)[ ]?\[cf2\]([\S\s]+?)\\minion,0\\\[cf1\]\)')
#ps
ps=re.compile(r'(|\[hmp3\]|\\minion,0\\)\[cf2\]([\S\s]+?)\[cf1\]')


chars=re.compile(r'(\[[\d\w]*\])')
sense=re.compile(r'(|[\[\]\+\S\s ]*)\\optima,0\\\[cf3\]\[hmp3\](\d)')

#get one whole sense
sense_line=re.compile(r'(|[\[\]\+\S\s ]*)\\optima,0\\\[cf3\]\[hmp3\](\d)(\\optima,0\\|)([\S\s]+?)\[cf3\]\[hmp3\]')
#have to check separately for [cf2] first
definition1=re.compile(r'([\S\s]+?)\[cf2\]')
definition2=re.compile(r'([\S\s]+?)(\[cf2\]|\.)')
example=re.compile(r'(\[cf2\])')
example_line1=re.compile(r'\[cf2\] ([\S\s]*)\.')
example_line2=re.compile(r'\[j33\] ([\S\s]*)\.')
note=re.compile(r'((\[j30\]|\[j34\]|\[j32\]) \.\.\.([\S\s]*)(\[j31\]|\[j30\]|\.))')

def split_entries(typetext):
    """Read the typesetting file and split into entries
    return a list of entries, one per headword"""

    entries=[]
    line_collect=""
    start_rec=False

    for line in typetext.split('\n'):
        #print "LINE:", line

        #clean up line
        linetxt=line.strip('\n').strip(' ')

        #find header
        matches=headword.match(linetxt)
        #seprate out header words with '|' and combine all lines for word
        if matches:

            #if header word collect first reference to pattern
            line_data=headword.sub(r'\3',matches.group(0),1).strip()

            linetxt=headword.sub(r'\4',matches.group(0),1)
            #save previous line  if have a headword in that line
            if start_rec: entries.append(line_collect)

            #start newline
            line_collect=line_data+'| '+linetxt
            start_rec=True

        else:

            # don't collect rubbish at start but combine lines
            if line_collect: line_collect+=' '+linetxt
            #headword across two lines

    entries.append(line_collect.strip(" "))

    return entries





def type_to_dictlist(typefile):
    """Convert a typesetting file to list of dictionaries,
    one per headword"""

    result=[]

    with open(typefile) as fd:
        typetext = fd.read()

    for entry in split_entries(typetext):
        info = process_entry(entry)
        result.append(info)

    return result

def process_entry(entry):
    """Extract information from a single dictionary entry
    Return a dictionary with the entry properties.
    """

    line_info_default={
        'headword' : "",
        'pronounce':"",
        'ps':"",
        'rest':"",
        'note':[],
        'comment':"",
        'senses':"",
        'definition':"",
        'example':[]
    }
    sense_default={
        'id':1,
        'ps':"",
        'rest':"",
        'note':[],
        'comment':"",
        'definition':"",
        'example':[]
    }


    line_info = line_info_default.copy()
    sense_line_info=sense_default.copy()

    #collect all items under headword
    newline=entry.split('|')

    line_info["headword"]=entry.split('|')[0]
    #print(line_info["headword"])
    if len(newline)>1:

        linetxt=entry.split('|')[1].strip()
    else:
        linetxt=""

    #match pronounce
    linetxt=get_part(linetxt,'pronounce',pronounce,line_info)

    linetxt=get_part(linetxt,'comment',comment,line_info,2,8).strip()

    senses=[]

    if sense.match(linetxt):

            while sense_line.match(linetxt):

                sense_line_info=sense_default
                #just get id in sense_line

                get_part(linetxt,'id',sense_line,sense_line_info,2,1)

                #get rest of line for next run - put back start of search
                linetxt="\optima,0\[cf3][hmp3]"+get_part(linetxt,'rest',sense_line,sense_line_info,4,1)

                sensetxt=sense_line_info['rest']

                sense_line_info['rest']=""
                sensetxt=get_part(sensetxt,'ps',ps,sense_line_info,2,8)
                #remove notes
                sensetxt=get_part(sensetxt,'note',note,sense_line_info,2,min_check+4,True)
                #put back the start of definition
                sensetxt1='[cf2] '+get_part(sensetxt,'definition',definition1,sense_line_info,1,8)
                if sense_line_info['definition']=='':
                        sensetxt='[cf2] '+get_part(sensetxt,'definition',definition2,sense_line_info,1,8)
                else: sensetxt=sensetxt1

                oldtxt=""
                if example.match(sensetxt):
                    #first pass
                    example_line=example_line1
                    while sensetxt!=oldtxt:
                        oldtxt=sensetxt
                        sensetxt=get_part(sensetxt,'example',example_line,sense_line_info,1,min_check,True)
                        #second pass
                        example_line=example_line2


                sense_line_info['rest']=clean_char(sensetxt).strip(' ')
                #sense_line_info['rest']=''
                senses.append(sense_line_info)
            #get last sense
            sense_line_info=sense_default

            #retrieve next sense from selected part of linetxt (no end of sense_line so use sense)
            #collect id and return remainder of match
            sensetxt=get_part(linetxt,'id',sense,sense_line_info,2,1)

            sensetxt=get_part(sensetxt,'ps',ps,sense_line_info,2,8)
            sensetxt=get_part(sensetxt,'note',note,sense_line_info,2,min_check+4,True)

            sensetxt1="[cf2] "+get_part(sensetxt,'definition',definition1,sense_line_info,1,8)
            if sense_line_info['definition']=='':
                    sensetxt='[cf2] '+get_part(sensetxt,'definition',definition2,sense_line_info,1,8)
            else: sensetxt=sensetxt1


            oldtxt=""
            if example.match(sensetxt):
                #first pass
                example_line=example_line1
                while sensetxt!=oldtxt:
                        oldtxt=sensetxt
                        sensetxt=get_part(sensetxt,'example',example_line,sense_line_info,1,min_check,True)
                        #second pass
                        example_line=example_line2

            sense_line_info['rest']=clean_char(sensetxt).strip(' ')

            senses.append(sense_line_info)

            line_info['senses']=senses


    else:

            linetxt=get_part(linetxt,'ps',ps,line_info,2,8)

            #remove NOTE
            linetxt=get_part(linetxt,'note',note,line_info,2,min_check+4,True)

            linetxt1="[cf2] "+get_part(linetxt,'definition',definition1,line_info,1,8)
            if line_info['definition']=='':

                    linetxt='[cf2] '+get_part(linetxt,'definition',definition2,line_info,1,8)
            else: linetxt=linetxt1

            oldtxt=""
            if example.match(linetxt):
                #first pass
                example_line=example_line1
                while linetxt!=oldtxt:
                    oldtxt=linetxt
                    linetxt=get_part(linetxt,'example',example_line,line_info,1,min_check,True)
                    #second pass
                    example_line=example_line2


            line_info['rest']=clean_char(linetxt).strip(' ')



    return line_info


def get_part(text, word_part, pattern, line_txt,sub_str=1, exitnum=0, many=False):

    matches=pattern.search(text)

    retext=text
            #now match for word_part using pattern and collect only sub_string of match eg 1=\1
    if matches:

        result=matches.group(sub_str)

        result=clean_char(result,exitnum).strip(' ')

                #get rest of line
        if many:
             #example has second part in next match group

            line_txt[word_part].append(clean_char(matches.group(1),exitnum).strip(' '))


        else:
            line_txt[word_part]=clean_char(result,exitnum).strip(' ')
        text=pattern.sub(r'',text,1).strip(' ')
    #if (word_part==""):
    #print (word_part +' - '+str(line_txt[word_part]))

    return text

def clean_char(text, num=0):
    #remove special chars
    iter=0
    for item in mapping:

            text=re.sub(re.escape(item), mapping[item], text)

            iter+=1
            if iter==num: break
    return text



if __name__=="__main__":

    if len(sys.argv)>1:
        parser = argparse.ArgumentParser(description='convert Typesetting files to JSON')
        parser.add_argument('--outdir', default='results', help='directory for output files')
        parser.add_argument('files', metavar='files', nargs='+', help='input data files')
        args = parser.parse_args()

        if not os.path.exists(args.outdir):
            os.makedirs(args.outdir)

        for datafile in args.files:
            base, ext = os.path.splitext(os.path.basename(datafile))
            print (datafile)
            outfile = os.path.join(args.outdir, base + ".json")
            entries = type_to_dictlist(datafile)

            with open(outfile, 'w') as out:
                json.dump(entries, out, indent=4)


    else:
        fileout='output'
        filename='../typesetting/txt/a.txt'


        text=type_to_dictlist(filename)
            ## overwrite exiting file

        out = open("out.txt", 'w+',encoding='utf-8')
        for line in text:
              json.dump(line, out, indent=4)
              out.write(os.linesep)
        out.close()

    #output to RDF
