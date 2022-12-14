import pandas as pd
import numpy as np

mult_list = ["show me", "show a", "looks", "look like", "looks like", "photo", "picture", "image", "still frame",
        "behind the scene", "poster"]

recm_list = ["recommend", "suggest", "movie like", "film like", "movies like", "films like"]

def run_filter(question):
    question_type = None

    df = pd.read_csv("movie-ratings.csv")
    movies = np.unique(df.titles.values.tolist())

    try:
        temp = []
        for i in movies:

            if i.lower() in question.lower():
                temp.append(i)

        ini_entity = max(temp, key = len)
    except:
        ini_entity = None

    if ini_entity == None:

        for i in mult_list:
            if i in question:
                question_type = "Multimedia"
                break

        for i in recm_list:
            if i in question:
                question_type = "Recommender"
    
    else:
        for i in mult_list:
            if (i in question) and (i not in ini_entity):
                question_type = "Multimedia"
                break

        for i in recm_list:
            if (i in question) and (i not in ini_entity):
                question_type = "Recommender"
                break
    
    return question_type
