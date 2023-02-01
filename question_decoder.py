import spacy
nlp = spacy.load("en_core_web_sm")
from rdflib.namespace import Namespace
import pandas as pd
import rdflib
import re
import locale
from rapidfuzz import fuzz
_ = locale.setlocale(locale.LC_ALL, '')
import numpy as np
from sklearn.metrics import pairwise_distances
import csv

def factual_emb(question, graph):
    movie = pd.read_csv("D:\\atai_conv_agent\\subjects.csv")

    relations = pd.read_csv("D:\\atai_conv_agent\\predicates.csv")

    def get_ent_rel(question):
        temp_sub = []
        for i in movie.iloc[ : , 1].values:

            if i.lower() in question.lower():
                temp_sub.append(i)

        entities_sub = max(temp_sub, key = len)

        # for token in doc:
        #     print(token.text, token.dep_, token.pos_)

        if "cast" in question.lower() or "cast member" in question.lower() or "casted" in question.lower():
            entities_rel = "cast member"

        elif "publication" in question.lower():
                entities_rel = "publication date"

        else:
            doc = nlp(question)
            temp_rel = []
            temp_rel_scores = []

            try:
                for i in relations.iloc[ : , 1].values:

                    if i.lower() in question.lower() and i.lower() not in entities_sub:
                        temp_rel.append(i)

                entities_rel = max(temp_rel, key = len)
                
            except:
                # print("START")
                pos = []

                for token in doc:
                    pos.append(token.pos_)

                if "NOUN" in pos:
                    # print("VERB")
                    for token in doc:
                        if token.pos_ == "NOUN" and token.text not in entities_sub:
                            for rel in relations.iloc[ : , 1].values:
                                temp_rel_scores.append(fuzz.ratio(token.text, rel))

                elif "VERB" in pos:
                    # print("NOUN")
                    for token in doc:
                        if token.pos_ == "VERB" and token.text not in entities_sub:
                            # print(token.text)
                            for rel in relations.iloc[ : , 1].values:
                                temp_rel_scores.append(fuzz.ratio(token.text, rel))
                
                max_idx = np.argmax(temp_rel_scores)
                entities_rel = (relations.iloc[ : , 1].values)[max_idx]

        return entities_sub, entities_rel

    ent, rel = get_ent_rel(question)

    df_rel = relations.query('predicates == "%s"'%(rel))
    rel_link = rdflib.term.URIRef(df_rel.iloc[ 0 , -1])

    df_mv = movie.query('subjects == "%s"'%(ent))

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

    temp = []

    try:
        for i in df_mv.iloc[ : , -1].values:
            try:
                obj_list = []
                try:
                    for triple in graph.triples((rdflib.term.URIRef(i), rel_link, None)):
                        # print(triple)
                        if type(triple[2]) == rdflib.term.Literal:
                            x = triple[2]
                        else:
                            x = get_entity_labels(triple[2])
                        obj_list.append(x)
                        
                    if len(obj_list) > 0:
                        temp.append(" ".join(obj_list))
                        # print(obj_list)
                except:
                    pass

            except Exception as e:
                print(str(e))

        temp = np.unique(temp)

        final_answer = "The answer for your question is " + " ".join(temp)
        
        if len(temp) == 0:
            print(temp[1])

    except:
        ent, rel = get_ent_rel(question)

        df_rel = relations.query('predicates == "%s"'%(rel))
        rel_link = rdflib.term.URIRef(df_rel.iloc[ 0 , -1])

        df_mv = movie.query('subjects == "%s"'%(ent))

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

        # df_movies = pd.read_csv("D:\\atai_conv_agent\\movie_title_rating.csv")
        # movies = np.unique(df_movies.title.values.tolist())

        entity_emb = np.load('D:\\Downloads\\ddis-graph-embeddings\\ddis-graph-embeddings\\entity_embeds.npy')
        relation_emb = np.load('D:\\Downloads\\ddis-graph-embeddings\\ddis-graph-embeddings\\relation_embeds.npy')

        with open('D:\\Downloads\\ddis-graph-embeddings\\ddis-graph-embeddings\\entity_ids.del', 'r') as ifile:
            ent2id = {rdflib.term.URIRef(ent): int(idx) for idx, ent in csv.reader(ifile, delimiter='\t')}
            id2ent = {v: k for k, v in ent2id.items()}
        with open('D:\\Downloads\\ddis-graph-embeddings\\ddis-graph-embeddings\\relation_ids.del', 'r') as ifile:
            rel2id = {rdflib.term.URIRef(rel): int(idx) for idx, rel in csv.reader(ifile, delimiter='\t')}
            id2rel = {v: k for k, v in rel2id.items()}

        head = entity_emb[ent2id[rdflib.term.URIRef(df_mv.iloc[ 0 , -1])]]
        pred = relation_emb[rel2id[rel_link]]
        lhs = head + pred
        dist = pairwise_distances(lhs.reshape(1, -1), entity_emb).reshape(-1)

        most_likely = dist.argsort()

        df_emb = pd.DataFrame([
            (id2ent[idx][len(WD):], id2ent[idx], dist[idx], rank+1)
            for rank, idx in enumerate(most_likely[:10])],
            columns=('Entity', 'Label', 'Score', 'Rank'))

        df_emb['Label'] = df_emb['Label'].apply(get_entity_labels)
        answer = df_emb['Label'].values
        final_answer = answer[0]
        final_answer = "The answers that you have asked for have been calculated from the embedding of the graph, which is " + (final_answer)

    print(final_answer)

question = "Who were casted in Taxi Driver"

print(factual_emb(question, graph))
