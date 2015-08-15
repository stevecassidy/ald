__author__ = 'ckutay'

import json
import gzip
import rdflib
import hashlib
import string
import argparse
import sys, os
import typesetting_parse

from rdflib.namespace import XSD

# output uri
# output uri
ALD = rdflib.Namespace('http://example.net/lexicon/ald/')
PROP = rdflib.Namespace('http://example.net/schema/')


SOURCE = rdflib.Namespace('http://www.omegawiki.org/')
UBY = rdflib.Namespace('http://purl.org/olia/ubyCat.owl#')
LEMON = rdflib.Namespace(u"http://lemon-model.net/lemon#")
ONTOLEX=rdflib.Namespace('http://www.w3.org/community/ontolex/')
SO = rdflib.Namespace('http://schema.org/')

#??
FOAF = rdflib.Namespace('http://xmlns.com/foaf/0.1/')
RDF = rdflib.Namespace(u"http://www.w3.org/1999/02/22-rdf-syntax-ns#")
RDFS = rdflib.Namespace(u"http://www.w3.org/2000/01/rdf-schema#")
DC = rdflib.Namespace(u"http://purl.org/dc/terms/")


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

    headword = genID(ALD, (record['headword']).encode('utf-8'))
    graph.add((headword, RDF.type, LEMON.canonicalForm))

    graph.add((headword, RDF.type, LEMON.Form))

    graph.add((headword,LEMON.writtenRep,rdflib.Literal(record['headword'])))
    # these need to be diff properties
    graph.add((headword, PROP.sampaaus, rdflib.Literal(record['pronounce']q)))
    if not record['comment'] == "":
        graph.add((headword, LEMON.comment, rdflib.Literal(record['comment'])))

    for sense in record['senses']:

        senseid = genID(SENSE,('OW_eng_SENSE_'+str(sense['id'])).encode('utf-8'))

        if not sense['ps'] == "":
            graph.add((senseid, UBY.partofSpeech, rdflib.Literal(sense['ps'])))
        if not sense['definition'] == "":
            graph.add((senseid, UBY.definition, rdflib.Literal(sense['definition'])))
        for example in sense['example']:
            graph.add((senseid, UBY.usageExample, rdflib.Literal(example)))
        for note in sense['note']:
            graph.add((senseid, UBY.note, rdflib.Literal(note)))

        graph.add((headword, UBY.lexicalSense, senseid))


    else:
        if not record['ps'] == "":
            graph.add((headword, UBY.partofSpeech, rdflib.Literal(record['ps'])))
        if not record['definition'] == "":
            graph.add((headword, UBY.definition, rdflib.Literal(record['definition'])))

        for example in record['example']:
                graph.add((headword, UBY.usageExample, rdflib.Literal(example)))
        for note in record['note']:
                graph.add((headword, UBY.note, rdflib.Literal(note)))


def gen_output(graph, datafile, outdir="."):

    turtle = graph.serialize(format='turtle').decode('utf-8')
    basename, ext = os.path.splitext(os.path.splitext(datafile)[0])
    print turtle
    return

    if outdir:
        print (os.path.join(outdir, basename + ".ttl"))
        with open(os.path.join(outdir, basename + ".ttl"), 'w') as out:
            out.write(turtle)
    else:
        with open(basename + ".ttl", 'w') as out:
            out.write(turtle)

    out.close()

if __name__=='__main__':

        graph = rdflib.Graph()
        datafile=sys.argv[1]
        graph.bind("lemon", LEMON)
        graph.bind("uby", UBY)
        graph.bind('prop', PROP)

        graph.add((PROP.sampaaus, RDFS.subpropertyof, LEMON.representation))
        graph.add((ALD[''], RDF.type, LEMON.Lexicon))

        records=typesetting_parse.type_to_dictlist(datafile)
            #for d in ner_records(fd):
        for d in records:
            genrdf(d, graph)
        gen_output(graph, datafile)
