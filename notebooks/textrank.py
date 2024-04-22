import random as rd
import torch
import nltk
import networkx as nx
from sentence_transformers import SentenceTransformer


# Road map :
# 
# Extraire du texte chaque phrase (str.split ?)
# 
# chercher à preprocess le texte pour obtenir les relations de similiratés entre chaque phrase
# - Word2Vec 200 https://sparknlp.org/2022/02/01/word2vec_wac_200_fr.html avec nltk d'abord ?
# - frenchnlp https://pypi.org/project/frenchnlp/
# - en utilisant un modèle camembert https://huggingface.co/dangvantuan/sentence-camembert-base (sans doute le base, un peu moins gros)
# 
# Construire le graphe
# networkx
# 
# TextRank algo
# newtworkx
# 
# Récupération des phrases avec le plus haut score mais sans trop de similarité
model = SentenceTransformer("paraphrase-albert-small-v2")

def split_sentences(text: str) -> list[str]:
    """Split a text around sentences, but does not remove stop characters
    
    Parameters
    ------------
    text : str
        text to be splitted into sentences

    Returns
    ----------
    list[str]
        a list of sentences in order
    """
    return nltk.tokenize.sent_tokenize(text)


def build_weight(list_sentence: list[str], eval) -> dict[(str, str), float]:

    """
    Compute similarity between each pair of sentences
    """
    result = {}
    evaluations = model.encode(list_sentence, normalize_embeddings=True, convert_to_numpy=False, convert_to_tensor=True)

    for i, sentence1 in enumerate(list_sentence):
        for j, sentence2 in enumerate(list_sentence[i+1:]):
            result[(sentence1, sentence2)] = float(torch.dot(evaluations[i], evaluations[j]))

    return result


def build_graph(list_sentence: list[str], dict_weight: dict[(str, str), float]) -> nx.Graph:

    """Compute the graph of similarity"""

    graph = nx.Graph()
    graph.add_nodes_from(list_sentence)

    for ((sentence1, sentence2), weight) in dict_weight.items():
        graph.add_edge(sentence1, sentence2, weight=weight)

    return graph


def cosine_evaluation(sent1: str, sent2: str) -> float:
    
    x, y = model.encode([sent1, sent2], normalize_embeddings=True, convert_to_tensor=True, convert_to_numpy=False)

    return float(torch.dot(x, y))

def text_rank(text: str):
    
    """
    Yield the top sentences of the text, if not to close

    Parameters
    --------------
    text : str
        Text to extract top sentences
    """

    # First split the text into list of sentences
    list_sentence = split_sentences(text)

    # Next build a similarity relation between each pair of sentences
    dict_weight = build_weight(list_sentence, cosine_evaluation)

    # Build the graph
    graph = build_graph(list_sentence, dict_weight)
    calculated_page_rank = nx.pagerank(graph, weight='weight')

    # Sort the sentences
    sentence_order = sorted(calculated_page_rank.items(), key=lambda x: x[1], reverse=True)

    yield sentence_order[0][0]
    i = 1
    yielded_sentences = [sentence_order[0][0]]
    while i < len(sentence_order):
        cur_sent = sentence_order[i][0]
        add_sent = True
        for prev_sent in yielded_sentences:
            cosine = dict_weight.get((cur_sent, prev_sent)) or dict_weight.get((prev_sent, cur_sent))
            if cosine > 0.8:
                add_sent = False
                break

        if add_sent:
            yielded_sentences.append(cur_sent)
            yield cur_sent
        i += 1
                

def test():
    with open("../small_text.txt", 'r') as f:
        long_text = f.read()
    
    sentence_iterator = iter(text_rank(long_text))
    for i in range(20):
        tmp = next(sentence_iterator)
        print(f'Sentence rank: {i}, Sentence: {tmp}')

if __name__ == "__main__":
    test()