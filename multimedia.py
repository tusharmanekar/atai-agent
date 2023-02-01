import json
import rdflib
import numpy as np
import random
import webbrowser

from rdflib.namespace import Namespace, RDF, RDFS, XSD

question = "show me a photo of Anne Hathaway"

def run_mult(question, graph, data):
    import spacy
    nlp = spacy.load("en_core_web_sm")

    doc = nlp(question)

    name = ""

    for token in doc:
        if token.pos_ == "PROPN":
            name = name + token.text + " "
        
    name = name.strip()
    '''
    f = open('D:\\Downloads\\images.json\\images.json')
    data = json.load(f)'''


    # graph = rdflib.Graph()
    # graph.parse('D:\\Downloads\\ddis-movie-graph.nt\\14_graph.nt', format = 'turtle')

    WD = Namespace('http://www.wikidata.org/entity/')
    WDT = Namespace('http://www.wikidata.org/prop/direct/')
    SCHEMA = Namespace('http://schema.org/')
    DDIS = Namespace('http://ddis.ch/atai/')

    film_list = [str(s) for s, in graph.query('''
    PREFIX ddis: <http://ddis.ch/atai/>
    PREFIX wd: <http://www.wikidata.org/entity/>
    PREFIX wdt: <http://www.wikidata.org/prop/direct/>
    PREFIX schema: <http://schema.org/>

    SELECT ?lbl WHERE {
        ?actor rdfs:label "%s"@en .
        ?movie rdfs:label ?lbl .
        ?movie wdt:P161 ?actor .
    }
    '''%(name))]

    film_shortlist = []

    for film in film_list:
        try:
            header = '''
            PREFIX ddis: <http://ddis.ch/atai/>
            PREFIX wd: <http://www.wikidata.org/entity/>
            PREFIX wdt: <http://www.wikidata.org/prop/direct/>
            PREFIX schema: <http://schema.org/>
            '''

            tuple_list = list(graph.query(header + '''SELECT ?value WHERE {
            ?movie rdfs:label "%s"@en .
            OPTIONAL { ?movie wdt:P345 ?value}}''' %(film)))

            first_tuple = tuple_list[0]

            for elements in first_tuple:
                film_shortlist.append(elements)
        except:
            pass
            # print(film)
    
    

    for _ in range(10):
        samp = random.sample(film_shortlist, 2)
        # print(samp)

        unq_1 = []

        for entry in data:
            try:
                if entry["movie"][0] == samp[0].toPython():
                    # print(entry["cast"])
                    for i in entry["cast"]:
                        unq_1.append(i)
            except:
                pass

        unq_2 = []

        for entry in data:
            try:
                if entry["movie"][0] == samp[1].toPython():
                    # print(entry["cast"])
                    for i in entry["cast"]:
                        unq_2.append(i)
            except:
                pass
        
        if set(unq_1).intersection(set(unq_2)) != None:
            target = set(unq_1).intersection(set(unq_2))
            break
        else:
            pass
    
    targ = []

    for i in target:
        targ.append(i)

    img_list = []

    for entry in data:
        if (len(entry["movie"]) != 0):
            # print(entry["movie"])
            if targ[0] in entry["cast"]:
                img_list.append(entry["img"])
                break

    image = "https://files.ifi.uzh.ch/ddis/teaching/2021/ATAI/dataset/movienet/images/" + img_list[0]

    return webbrowser.open(image)

print(run_mult(question, graph, data))
