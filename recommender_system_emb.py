import csv
import numpy as np
import os
import rdflib
import pandas as pd
import re
from sklearn.metrics import pairwise_distances

def run_recm(question, graph):
    question_split = question.split(",")

    df = pd.read_csv("D:\\Downloads\\movie_title_rating.csv")
    movies = np.unique(df.title.values.tolist())

    mjr_temp = []

    for j in question_split:
        try:
            temp = []

            for i in movies:

                if i.lower() in j.lower():
                    temp.append(i)
            ini_entity = max(temp, key = len)
            mjr_temp.append(ini_entity)
        except Exception as e:
            print(str(e))
        
    for i in mjr_temp:
        if i not in question:
            mjr_temp.remove(i)


    # define some prefixes
    WD = rdflib.Namespace('http://www.wikidata.org/entity/')
    WDT = rdflib.Namespace('http://www.wikidata.org/prop/direct/')
    DDIS = rdflib.Namespace('http://ddis.ch/atai/')
    RDFS = rdflib.namespace.RDFS
    SCHEMA = rdflib.Namespace('http://schema.org/')

    # load the graph
    # graph = rdflib.Graph().parse(os.path.join('D:', 'Downloads', 'ddis-movie-graph.nt', 'ddis-movie-graph.nt'), format='turtle')
    
    '''
    graph = rdflib.Graph()
    graph.parse('D:\\Downloads\\ddis-movie-graph.nt\\14_graph.nt', format = 'turtle')'''

    # load the embeddings
    entity_emb = np.load('D:\\Downloads\\ddis-graph-embeddings\\ddis-graph-embeddings\\entity_embeds.npy')
    relation_emb = np.load('D:\\Downloads\\ddis-graph-embeddings\\ddis-graph-embeddings\\relation_embeds.npy')

    # load the dictionaries
    with open(('D:\\Downloads\\ddis-graph-embeddings\\ddis-graph-embeddings\\entity_ids.del'), 'r') as ifile:
        ent2id = {rdflib.term.URIRef(ent): int(idx) for idx, ent in csv.reader(ifile, delimiter='\t')}
        id2ent = {v: k for k, v in ent2id.items()}
        
    with open(('D:\\Downloads\\ddis-graph-embeddings\\ddis-graph-embeddings\\relation_ids.del'), 'r') as ifile:
        rel2id = {rdflib.term.URIRef(rel): int(idx) for idx, rel in csv.reader(ifile, delimiter='\t')}
        id2rel = {v: k for k, v in rel2id.items()}

    ent2lbl = {ent: str(lbl) for ent, lbl in graph.subject_objects(RDFS.label)}
    lbl2ent = {lbl: ent for ent, lbl in ent2lbl.items()}


    header = '''
    PREFIX ddis: <http://ddis.ch/atai/>
    PREFIX wd: <http://www.wikidata.org/entity/>
    PREFIX wdt: <http://www.wikidata.org/prop/direct/>
    PREFIX schema: <http://schema.org/>
    '''

    tuple_list = list(graph.query(header + '''
        SELECT * WHERE {
            ?movie rdfs:label "%s"@en .
            ?movie wdt:P57/rdfs:label ?director .
            OPTIONAL { ?movie ddis:rating ?rating } .
            OPTIONAL { ?movie wdt:P577 ?value}
    }'''%(mjr_temp[0])))

    movie_code = re.sub("http://www.wikidata.org/entity/", "", tuple_list[0][0])

    # which entities are similar to "Harry Potter and the Goblet of Fire"
    st = rdflib.term.URIRef(WD + movie_code)

    ent = ent2id[st]
    
    # we compare the embedding of the query entity to all other entity embeddings
    dist = pairwise_distances(entity_emb[ent].reshape(1, -1), entity_emb).reshape(-1)
    # order by plausibility
    most_likely = dist.argsort()

    df_sugg = pd.DataFrame([
        (
            id2ent[idx][len(WD):], # qid
            ent2lbl[id2ent[idx]],  # label
            dist[idx],             # score
            rank+1,                # rank
        )
        for rank, idx in enumerate(most_likely[:15])],
        columns=('Entity', 'Label', 'Score', 'Rank'))

    answer = "The recommendations based on the movies you liked are- "

    for i in df_sugg.iloc[ 1: , 1].values:
        answer = answer + "\n" + i

    ent = "The Godfather"
    code = "P750"

    tuple_list = list(graph.query(header + '''
        SELECT * WHERE {
            ?movie rdfs:label "%s"@en .
            ?movie wdt:P57/rdfs:label ?director .
            OPTIONAL { ?movie ddis:rating ?rating } .
            OPTIONAL { ?movie wdt:%s ?value}
    }'''%(ent, code)))

    return answer