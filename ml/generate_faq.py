import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans

def get_emb_model(model_name='intfloat/multilingual-e5-large-instruct'):
    model = SentenceTransformer(model_name)
    return model

# df имеет столбцы question и answer (те, что у нас в админке видны), n_clusters - количество вопросов, надо подгонять под реальный датасет
def gen_faq(df, model, n_clusters=10):
    question_embeddings = model.encode(df['question'].tolist(), normalize_embeddings=True)

    clustering = KMeans(n_clusters=n_clusters, random_state=52)
    df['cluster'] = clustering.fit_predict(question_embeddings)

    faq = []
    for cluster in sorted(df['cluster'].unique()):
        cluster_df = df[df['cluster'] == cluster]
        centroid = clustering.cluster_centers_[cluster]
        distances = cluster_df['question'].apply(lambda x: model.encode(x))
        cluster_df['distance'] = distances.apply(lambda emb: ((emb - centroid) ** 2).sum() ** 0.5)
        representative = cluster_df.loc[cluster_df['distance'].idxmin()]
        faq.append({
            'question': representative['question'],
            'answer': representative['answer'],
            'count': len(cluster_df)
        })
    
    faq = sorted(faq, key=lambda x: x['count'], reverse=True)
    
    return faq

# use
# model = get_emb_model()
# df = ... # получить из бд
# faq = gen_faq(df, model)
# for item in faq:
#     print(f"FAQ: {item['question']} (asked {item['count']} times)")
#     print(f"Answer: {item['answer']}\n")