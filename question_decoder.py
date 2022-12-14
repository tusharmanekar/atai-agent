import spacy
nlp = spacy.load("en_core_web_sm")
from rdflib.namespace import Namespace
import pandas as pd
import rdflib
import re
import locale
_ = locale.setlocale(locale.LC_ALL, '')
import numpy as np
from sklearn.metrics import pairwise_distances
import csv
import operator

def run_qdec(question, graph):

    header = '''
                PREFIX ddis: <http://ddis.ch/atai/>
                PREFIX wd: <http://www.wikidata.org/entity/>
                PREFIX wdt: <http://www.wikidata.org/prop/direct/>
                PREFIX schema: <http://schema.org/>
            '''

    WD = Namespace('http://www.wikidata.org/entity/')
    WDT = Namespace('http://www.wikidata.org/prop/direct/')
    SCHEMA = Namespace('http://schema.org/')
    DDIS = Namespace('http://ddis.ch/atai/')

    '''
    graph = rdflib.Graph()
    graph.parse('/Users/sanjanawarambhey/Downloads/14_graph.nt', format = 'turtle')
    '''
    df_movies = pd.read_csv("D:\\atai_conv_agent\\movie_title_rating.csv")
    movies = np.unique(df_movies.title.values.tolist())

    entity_emb = np.load('D:\\Downloads\\ddis-graph-embeddings\\ddis-graph-embeddings\\entity_embeds.npy')
    relation_emb = np.load('D:\\Downloads\\ddis-graph-embeddings\\ddis-graph-embeddings\\relation_embeds.npy')

    with open('D:\\Downloads\\ddis-graph-embeddings\\ddis-graph-embeddings\\entity_ids.del', 'r') as ifile:
        ent2id = {rdflib.term.URIRef(ent): int(idx) for idx, ent in csv.reader(ifile, delimiter='\t')}
        id2ent = {v: k for k, v in ent2id.items()}
    with open('D:\\Downloads\\ddis-graph-embeddings\\ddis-graph-embeddings\\relation_ids.del', 'r') as ifile:
        rel2id = {rdflib.term.URIRef(rel): int(idx) for idx, rel in csv.reader(ifile, delimiter='\t')}
        id2rel = {v: k for k, v in rel2id.items()}

    def get_entity_relation(ques):
        temp = []
        for i in movies:

            if i.lower() in ques.lower():
                temp.append(i)

        entities = max(temp, key = len)


        q_p = [("what is the (.*) of ENTITY?"), ("who is the (.*) of ENTITY?"), ("what was ENTITY (.*) for ?"),("who was the (.*) in ENTITY?"), ("who were (.*) in ENTITY?"), ("who was the (.*) of ENTITY?"), ("what (.*) did the ENTITY recieve?"),("what (.*) did the ENTITY get?")]
        print("question pattern: {}\n".format(q_p))
        for i in q_p:

            ques = re.sub(entities, "ENTITY", ques.rstrip("?"))  
            if re.match(i.lower(), ques.lower()) != None:
                rel = re.match(i.lower(), ques.lower()).group(1)
                print("recognized relation: {}\n".format(rel))

        return(entities, rel)



    def get_entity_node(x):
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
        } '''%(x)))

        s = tuple_list[0][0]

        return s 

    def get_relation_labels(code):
        try:
            code = re.sub("http://www.wikidata.org/prop/direct/", "", code)
            header = '''
                    PREFIX ddis: <http://ddis.ch/atai/>
                    PREFIX wd: <http://www.wikidata.org/entity/>
                    PREFIX wdt: <http://www.wikidata.org/prop/direct/>
                    PREFIX schema: <http://schema.org/>
                '''

            tuple_list = list(graph.query(header + '''
            SELECT  *
            WHERE {
                    wdt:%s rdfs:label ?label .
                }
            '''%(code)))
            return tuple_list[0][0]

        except:
            pass

    def levenshteinDistance(s1, s2):
        if len(s1) > len(s2):
            s1, s2 = s2, s1

        distances = range(len(s1) + 1)
        for i2, c2 in enumerate(s2):
            distances_ = [i2+1]
            for i1, c1 in enumerate(s1):
                if c1 == c2:
                    distances_.append(distances[i1])
                else:
                    distances_.append(1 + min((distances[i1], distances[i1 + 1], distances_[-1])))
            distances = distances_
        return distances[-1]

    def get_entity_labels(code):
        code = re.sub("http://www.wikidata.org/entity/", "", code)
        header = '''
                PREFIX ddis: <http://ddis.ch/atai/>
                PREFIX wd: <http://www.wikidata.org/entity/>
                PREFIX wdt: <http://www.wikidata.org/prop/direct/>
                PREFIX schema: <http://schema.org/>
            '''

        tuple_list_m = list(graph.query(header + '''
        SELECT  *
        WHERE {
                wd:%s rdfs:label ?label .
            }
        '''%(code)))
        x = tuple_list_m[0][0].toPython()

        return x


    def get_predicate_label(node, relation):
        rel2lbl = {obj: str(pre) for pre, obj in graph.predicate_objects(node)}
        df = pd.DataFrame()
        df = pd.DataFrame(rel2lbl.items(), columns=['obj','pred'])
        df['pred_labels'] = df['pred'].apply(get_relation_labels)
        scores = {}
        for m in df.iloc[:,-1].values:
            try:
                scores[m] = 1 - levenshteinDistance(relation,m.toPython())
            except:
                scores[m] = -10000
        result = max(scores.items(), key=operator.itemgetter(1))[0]
        result_link = np.unique(df[df['pred_labels']==result]['pred'])
        return(result, result_link[0])

    entity, relation = get_entity_relation(question)
    node = get_entity_node(entity)

    (lable, link) = get_predicate_label(node, relation)

    pred_code = re.sub("http://www.wikidata.org/prop/direct/", "", link)

    tuple_P = set(graph.query('''
            PREFIX ddis: <http://ddis.ch/atai/>
            PREFIX wd: <http://www.wikidata.org/entity/>
            PREFIX wdt: <http://www.wikidata.org/prop/direct/>
            PREFIX schema: <http://schema.org/>

            SELECT ?obj ?lbl WHERE {
                ?ent rdfs:label "%s"@en .
                ?ent wdt:%s ?obj .
                ?obj rdfs:label ?lbl .
            }
            '''%(entity,pred_code)))

    answer = {ent[len(WD):]: str(lbl) for ent, lbl in (i for i in tuple_P)}

    if answer != {} and pred_code != 'P577':
        final_answer = list(answer.values())
        if len(final_answer)>1:
            print("The answer to your question gathered knowledge graph is as follows: " + (' and '.join(final_answer)))
        else:
            print("The answer to your question gathered from the knowledge graph is " + (final_answer[0]))
    elif pred_code == 'P577':
        tuple_P = list(graph.query(header + '''
            SELECT * WHERE {
                ?movie rdfs:label "%s"@en .
                ?movie wdt:P57/rdfs:label ?director .
                OPTIONAL { ?movie ddis:rating ?rating } .
                OPTIONAL { ?movie wdt:%s ?value}
        }'''%(entity, 'P577')))

        answer = np.array(tuple_P[0][3].toPython())
        final_answer = answer
        print("The date that you have asked as calculated from the knowledge graph is " + str(final_answer))
    else: 
        head = entity_emb[ent2id[node]]
        pred = relation_emb[rel2id[DDIS.indirectSubclassOf]]
        lhs = head + pred
        dist = pairwise_distances(lhs.reshape(1, -1), entity_emb).reshape(-1)

        most_likely = dist.argsort()

        df_emb = pd.DataFrame([
            (id2ent[idx][len(WD):], id2ent[idx], dist[idx], rank+1)
            for rank, idx in enumerate(most_likely[:10])],
            columns=('Entity', 'Label', 'Score', 'Rank'))

        df_emb['Label'] = df_emb['Label'].apply(get_entity_labels)
        answer = df_emb['Label'].values
        final_answer = answer

        print("The answers that you have asked for have been calculated from the embedding of the graph, which is " + (' and '.join(final_answer)))
