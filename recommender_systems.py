import re
import json
import rdflib
import numpy as np
import pandas as pd
from rdflib.namespace import Namespace, RDF, RDFS, XSD

graph = rdflib.Graph()
graph.parse('D:\\Downloads\\ddis-movie-graph.nt\\14_graph.nt', format = 'turtle')

header = '''
PREFIX ddis: <http://ddis.ch/atai/>
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX schema: <http://schema.org/>
'''

tuple_dir = list(graph.query(header + '''
SELECT ?lbl WHERE {
?genre wdt:label "director" .
}
'''))

vari = "P57"

def get_lab(code):
    code = re.sub("http://www.wikidata.org/prop/direct/", "", code)

    tuple_list = list(graph.query(header + '''
    SELECT  *
    WHERE {
            wdt:%s rdfs:label ?label .
        }
    '''%(code)))

    return tuple_list[0]

print(get_lab(vari))

predicates = {}

for s, p, o in graph:
    predicates[p.toPython()] = re.sub("http://www.wikidata.org/prop/direct/", "", p.toPython())


list_p = []

for key,value in predicates.items():
    if "http://www.wikidata.org/prop/direct/" in key:
        list_p.append(key)

df = pd.DataFrame()
df["col_1"] = list_p

df["col_1"] = df["col_1"].apply(get_lab)

film_list = list(graph.query(header + '''
SELECT ?lbl WHERE {
    SELECT ?movie ?lbl WHERE {
        ?movie wdt:P31 wd:Q11424 .        
        ?movie rdfs:label ?lbl .
    }
}
'''))

print(len(np.unique(tuple_list)))

for elements in tuple_list:
    print(elements[0])

def get_rating(film):
    try:
        tuple_list = list(graph.query(header + '''
        SELECT  ?rating
        WHERE {
                ?movie rdfs:label "%s"@en .
                OPTIONAL { ?movie ddis:rating ?rating } .
            }
        '''%(film)))

        tuple_list = tuple_list[0][0]
    except:
        tuple_list ='0'

    return float(tuple_list)

df_movie = pd.DataFrame()
df_movie["titles"] = np.unique(film_list)
df_movie["ratings"] = df_movie["titles"].apply(get_rating)

print(get_rating("Apocalypse Now"))

def get_genre(film):
    try:
        tuple_list = list(graph.query(header + '''
        SELECT  ?genre
        WHERE {
                ?movie rdfs:label "%s"@en .
                OPTIONAL { ?movie wdt:P136 ?genre } .
            }
        '''%(film)))

    except:
        tuple_list = ''

    temp_list = []
    for i in tuple_list:
        temp_list.append(i[0].toPython())

    return temp_list

df_movie["genre"] = df_movie["titles"].apply(get_genre)

df_movie.head()

def get_director(film):
    try:
        tuple_list = list(graph.query(header + '''
        SELECT  ?dir
        WHERE {
                ?movie rdfs:label "%s"@en .
                OPTIONAL { ?movie wdt:P57 ?dir } .
            }
        '''%(film)))

    except:
        tuple_list = ''

    temp_list = []
    for i in tuple_list:
        temp_list.append(i[0].toPython())

    if len(temp_list)>0:
        temp_list = temp_list[0]
    else:
        temp_list = ""

    return temp_list

print(get_director("The Godfather"))

df_movie["director"] = df_movie["titles"].apply(get_director)

df_movie.head()

from sklearn import preprocessing
  
# label_encoder object knows how to understand word labels.
label_encoder = preprocessing.LabelEncoder()
  
# Encode labels in column 'species'.
df_movie['director']= label_encoder.fit_transform(df_movie['director'])
  
len(df_movie['director'].unique())

txr = label_encoder.transform(["http://www.wikidata.org/entity/Q2110132"])
print(txr[0])
def find_neighbours(film):
    genres = get_genre(film)
    director = get_director(film)
    director = label_encoder.transform([director])[0]
    rating = get_rating(rating)

    rec_list = []

    dir_list = df_movie.query("director = str(%s)"%(director))

    if len(dir_list) > 10:
        for i in range(10):
            rec_list.append(dir_list[i])
    else:
        for i in dir_list:
            rec_list.append(i)

director = 2525
dir_list = df_movie.query("director == %s"%(director))