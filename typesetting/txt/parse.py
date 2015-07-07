
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
    ('[cp8.5]',''),
    ('[cf2]',''),
    ('[cf1]',  '.'),
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
    ('~[fa[xp\'}]}','')
])
#maybe more rubbish

## process input
line_info_default={'headword' : " ",'pronounce':" ",'ps':" ",'rest':" ", 'note':" ", 'comment':" ",  'senses':" ", 'definition':" ", 'example':" "}

sense_default={'id':1,'ps':" ",'rest':" ", 'note':" ", 'comment':" ",'definition':" ", 'example':" "}
#patterns

#headword at start of line for after [j31]\n[j111]
headword=re.compile(r'(\[j111\]|--\[\w+\]|--)([\w, ]*)(\.*)')
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
definition=re.compile(r'([\S\S]+?)\[cf2\]')
example=re.compile(r'\[cf2\]([\S\s]+?)(\[j\d\d\][\s\S]*)')
note=re.compile(r'\[j30\]([\S\s]+?)\[j31\]')

def readfile(filename="a.txt", dir="output"):
    #collecct json lines to write to rdf graph
    lines_out=[]

        ## overwrite exiting file
    location=os.path.join(dir,filename)
    out = open(location+"out.txt", 'w+',encoding='utf-8')
    f = open(filename, encoding='utf-8')

    lines=[]
    line_collect=""
    start_rec=False


    for line in f:

        #clean up line
        linetxt=line.strip('\n').strip(' ')

        #find header
        matches=headword.match(linetxt)
        #seprate out header words with '|' and combine all lines for word
        if matches:

            #if header word collect first reference to pattern
            line_data=headword.sub(r'\2',matches.group(0),1).strip()
            linetxt=headword.sub(r'\3',matches.group(0),1)
            #save previous line  if have a headword in that line
            if start_rec: lines.append(line_collect)

            #start newline
            line_collect=line_data+'| '+linetxt
            start_rec=True

        else:

            # don't collect rubbish at start
            if line_collect: line_collect+=' '+linetxt
            #headword across two lines

    lines.append(line_collect.strip(" "))

    for line in lines:
        #start new line
        line_info={'headword' : " ",'pronounce':" ",'ps':" ",'rest':" ", 'note':" ", 'comment':" ", 'senses':" ",'definition':" ", 'example':" "}
        #collect all items under headword
        newline=line.split('|')

        line_info["headword"]=line.split('|')[0]
        #print(line_info["headword"])
        if len(newline)>1:

            linetxt=line.split('|')[1].strip()
        else:
            linetxt=""
         #match pronounce
        linetxt=get_part(linetxt,'pronounce',pronounce,line_info)

        linetxt=get_part(linetxt,'comment',comment,line_info,2,8).strip()

        #check senses (1-?)

        senses=[]

        #collect empty senses

        if sense.match(linetxt):

            while sense_line.match(linetxt):

                sense_line_info={'id':1,'ps':" ",'rest':" ", 'note':" ",'comment':" ", 'definition':" ", 'example':" "}
                #just get id in sense_line

                get_part(linetxt,'id',sense_line,sense_line_info,2,1)

                #get rest of line for next run - put back start of search
                linetxt="\optima,0\[cf3][hmp3]"+get_part(linetxt,'rest',sense_line,sense_line_info,4,1)

                sensetxt=sense_line_info['rest']


                sensetxt=get_part(sensetxt,'ps',ps,sense_line_info,2,8)
                #put back the start of example
                sensetxt='[cf2] '+get_part(sensetxt,'definition',definition,sense_line_info,1,8)
                oldtxt=""
                if example.match(sensetxt):
                    sense_line_info['example']=[]
                    while sensetxt!=oldtxt:
                        oldtxt=sensetxt
                        sensetxt=get_part(sensetxt,'example',example,sense_line_info,1,8,True)

                sensetxt=get_part(sensetxt,'note',note,sense_line_info,1,8)

                sense_line_info['rest']=clean_char(sensetxt,26).strip(' ')
                senses.append(sense_line_info)
            #get last sense
            sense_line_info={'id':1,'ps':" ",'rest':" ", 'note':" ",'comment':" ",'definition':" ",'example':" "}

            #retrieve next sense from selected part of linetxt (no end of sense_line so use sense)
            #collect id and return remainder of match
            sensetxt=get_part(linetxt,'id',sense,sense_line_info,2,1)

            sensetxt=get_part(sensetxt,'ps',ps,sense_line_info,2,8)
            sensetxt="[cf2] "+get_part(sensetxt,'definition',definition,sense_line_info,1,8)
            oldtxt=""
            if example.match(sensetxt):
                sense_line_info['example']=[]
                while sensetxt!=oldtxt:
                        oldtxt=sensetxt
                        sensetxt=get_part(sensetxt,'example',example,sense_line_info,1,8,True)
            sensetxt=get_part(sensetxt,'note',note,sense_line_info,1,8)

            sense_line_info['rest']=clean_char(sensetxt,26).strip(' ')

            senses.append(sense_line_info)

            line_info['senses']=senses


        else:

            linetxt=get_part(linetxt,'ps',ps,line_info,2,8)

            linetxt="[cf2] "+get_part(linetxt,'definition',definition,line_info,1,8)
            oldtxt=""
            if example.match(linetxt):
                line_info['example']=[]
                while linetxt!=oldtxt:
                    oldtxt=linetxt
                    linetxt=get_part(linetxt,'example',example,line_info,1,8,True)
            linetxt=get_part(linetxt,'note',note,line_info,1,8)
            line_info['rest']=clean_char(linetxt,26).strip(' ')
        if line_info:
            #pprint.pprint(line_info)
            pprint.pprint(line_info, stream=out)

        out.write(os.linesep)
        lines_out.append(line_info)
    out.close()
    return lines_out

def get_part(text, word_part, pattern, line_txt,sub_str=1, exitnum=0, many=False):

    matches=pattern.search(text)


            #now match for word_part using pattern and collect only sub_string of match eg 1=\1
    if matches:

        result=matches.group(sub_str)
        result=clean_char(result,exitnum).strip(' ')
                #get rest of line
        if many:
                line_txt[word_part].append(result)
        else:
            line_txt[word_part]=result
        text=pattern.sub(r'',text,1).strip(' ')

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


#OUtput to RDF

def genID(prefix, name):
    """Return a URI for this name"""

    m = hashlib.md5()

    m.update(name.encode('utf-8'))

    h = m.hexdigest()

    return prefix[h]

def normalise_name(name):
    """Return a normalised version of this name"""

    return string.capwords(name)



# output uri
WORK = rdflib.Namespace('http://lemon-model.net/lexica/uby/ow_eng/')
SOURCE = rdflib.Namespace('http://www.omegawiki.org/')
NAME = rdflib.Namespace('http://lemon-model.net/lemon#')
UBY = rdflib.Namespace('http://purl.org/olia/ubyCat.owl#')
LEMON = rdflib.Namespace(u"http://lemon-model.net/lemon#")
SENSE=rdflib.Namespace(u"http://lemon-model.net/lemon#sense")
ONTOLEX=rdflib.Namespace('http://www.w3.org/community/ontolex/')
SO = rdflib.Namespace('http://schema.org/')
#??
FOAF = rdflib.Namespace('http://xmlns.com/foaf/0.1/')
RDF = rdflib.Namespace(u"http://www.w3.org/1999/02/22-rdf-syntax-ns#")
RDFS = rdflib.Namespace(u"http://www.w3.org/2000/01/rdf-schema#")
DC = rdflib.Namespace(u"http://purl.org/dc/terms/")


def genrdf(record, graph, integer_id):
    """Generate RDF for a single record"""


    work= WORK['OW_eng_LexicalEntry_'+str(integer_id)]
    #this is wrong...
    name_word=record['headword'].split(',')

    name = genID(NAME, name_word[0])
    graph.add((work,RDF.type, LEMON.canonicalForm))

    graph.add((work, RDF.type, LEMON.Form))

    graph.add((work,LEMON.writtenRep,rdflib.Literal(record['headword'])))
    graph.add((work, LEMON.writtenRep, rdflib.Literal(record['pronounce']+'@enAU')))
    graph.add((work, LEMON.writtenRep, rdflib.Literal(record['comment'])))
    if len (record['senses'])>1:
        for sense in record['senses']:

            ##senseid = genID(SENSE,'OW_eng_SENSE_'+str(sense['id']))

            graph.add((work, UBY.partofSpeech, rdflib.Literal(sense['ps'])))
            graph.add((work, UBY.definition, rdflib.Literal(sense['definition'])))
            for example in sense['example']:
                graph.add((work, UBY.usageExample, rdflib.Literal(example)))
            graph.add((work, UBY.note, rdflib.Literal(sense['note'])))
            graph.add((work, UBY.rest, rdflib.Literal(sense['rest'])))

           # graph.add((work, UBY.lexicalSense, senseid))
    else:
        graph.add((work, UBY.partofSpeech, rdflib.Literal(record['ps'])))
        graph.add((work, UBY.definition, rdflib.Literal(record['definition'])))
        for example in record['example']:
                graph.add((work, UBY.usageExample, rdflib.Literal(example)))
        graph.add((work, UBY.note, rdflib.Literal(record['note'])))
        graph.add((work, UBY.rest, rdflib.Literal(record['rest'])))

# record the mention
    graph.add((work, SO.mentions, name))



def gen_output(graph, datafile, outdir=""):

    turtle = graph.serialize(format='turtle')
    #print(turtle)

    basename, ext = os.path.splitext(os.path.splitext(datafile)[0])

    if outdir:
        #print (os.path.join(outdir, basename + ".ttl"))
        with open(os.path.join(outdir, basename + ".ttl"), 'w') as out:
            out.write(turtle)
    else:
        with open(basename + ".ttl", 'w') as out:
            out.write(turtle)

    out.close()

if __name__=="__main__":


    integer_id=0
    if len(sys.argv)>1:
        parser = argparse.ArgumentParser(description='convert Typesetting files to JSON')
        parser.add_argument('--outdir', default='results', help='directory for output files')
        parser.add_argument('files', metavar='files', nargs='+', help='input data files')
        args = parser.parse_args()

        if not os.path.exists(args.outdir):
            os.makedirs(args.outdir)

        for datafile in args.files:


            graph = rdflib.Graph()
            with gzip.open(datafile) as fd:
                text= readfile(fd,args.outdir)
                for d in text:
                    genrdf(d, graph, integer_id)
                    integer_id+=1
                gen_output(graph, datafile, args.outdir)

    else:
        if not os.path.exists("output"):
            os.makedirs("output")
        text=readfile()

        graph = rdflib.Graph()
        datafile="output/a.txtout.txt"
        with open(datafile) as fd:
            for d in text:
                genrdf(d, graph, integer_id)
                integer_id+-1
            gen_output(graph, datafile)
    #output to RDF


