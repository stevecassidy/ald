__author__ = 'ckutay'

import json
import gzip
import rdflib
import hashlib
import string
import argparse
import sys, os

from rdflib.namespace import XSD

# output uri
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

def ner_records(fd):
    """Read the JSON data in filename, yielding a sequence
    of dictionaries, one per record"""

    text = ""
    for line in fd.readlines():
        line = line.strip()
        if line == "},{" or line == "}":
            text += "}"
            d = json.loads(text)
            text = "{"
            yield d
        elif line == "[" or line == "]":
            pass
        elif line == "{":
            text = line
        else:
            text += line

def genID(prefix, name):
    """Return a URI for this name"""

    m = hashlib.md5()
    m.update(name)
    h = m.hexdigest()

    return prefix[h]

def normalise_name(name):
    """Return a normalised version of this name"""

    return string.capwords(name)



def genrdf(record, graph):

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

if __name__=='__main__':

    if len(sys.argv)>1:

        parser = argparse.ArgumentParser(description='convert NER output to RDF')
        parser.add_argument('--outdir', default='results', help='directory for output files')
        parser.add_argument('files', metavar='files', nargs='+', help='input data files')
        args = parser.parse_args()

        if not os.path.exists(args.outdir):
            os.makedirs(args.outdir)

        for datafile in args.files:
            graph = rdflib.Graph()
            with gzip.open(datafile) as fd:
                for d in ner_records(fd):
                    genrdf(d, graph)
                gen_output(graph, datafile, args.outdir)
    else:
        if not os.path.exists("output"):
            os.makedirs("output")
        graph = rdflib.Graph()
        datafile="output/a.txtout.txt"
        with open(datafile) as fd:
            for d in ner_records(fd):
                genrdf(d, graph)
            gen_output(graph, datafile)
