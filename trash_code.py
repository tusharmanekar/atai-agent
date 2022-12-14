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
