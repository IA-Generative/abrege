import torch
import nltk
import networkx as nx


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
class Model:
    """A small wrapper around the real model

    to make your own with your model, please use this class
    """

    def __init__(self):
        pass

    def encode(self, *args, **kwargs):
        return self._model.encode(*args, **kwargs)

    @staticmethod
    def from_hugging_hub(model_path: str) -> "Model":
        from sentence_transformers import SentenceTransformer

        model = Model()
        model._model = SentenceTransformer(model_path)
        return model


def split_sentences(text: str) -> list[str]:
    """Split a text around sentences, but does not remove those characters

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


def build_weight(list_sentence: list[str], model: Model) -> dict[(int, int), float]:
    """
    compute similarity between each pair of sentences and put them in a dict
    mapped with their cosine simalirity

    Parameters
    ------------
    list_sentence : list[str]
        list of sentences
    model : Model
        model to use embeddings from

    Returns
    ----------
    dict[(int, int), float]
        a dict mapping each pair of sentences (indexed by their order in orginal text)
        to their cosine similarity
    """
    result = {}
    evaluations = model.encode(
        list_sentence,
        normalize_embeddings=True,
        convert_to_numpy=False,
        convert_to_tensor=True,
    )

    for i, _ in enumerate(list_sentence):
        for j in range(i + 1, len(list_sentence)):
            result[(i, j)] = float(torch.dot(evaluations[i], evaluations[j]))

    return result


def build_graph(
    list_sentence: list[str], dict_weight: dict[(int, int), float]
) -> nx.Graph:
    """
    Compute the similarity graph
    Parameters
    --------------
    list_sentences: list[str]
        list of sentences
    dict_weight : dict[(int, int), float]
        a mapping of pair of sentence (index in original text) and cosine similarity

    Returns
    ---------
    networkx.Graph
        graph of similarity
    """

    graph = nx.Graph()
    graph.add_nodes_from(range(len(list_sentence)))

    for (idx_sent1, idx_sent2), weight in dict_weight.items():
        graph.add_edge(idx_sent1, idx_sent2, weight=weight)

    return graph


def text_rank_iterator(list_sentences: list[str], embedding_model: Model):
    """
    Yield the top sentences of the models, according to the embdeddings delivred
    by embeddding_model

    Parameters
    --------------
    list_sentences : list[str]
        list of sentences to extract best from
    embdeding_model: Model
        model to use for embdeddings of sentences

    Yield
    --------
    int
        index of the best sentences so far
    """

    # Next build a similarity relation between each pair of sentences
    dict_weight = build_weight(list_sentences, embedding_model)

    # Build the graph
    graph = build_graph(list_sentences, dict_weight)

    # And apply the text rank algorithm
    calculated_page_rank = nx.pagerank(graph, weight="weight", max_iter=1000, tol=0.1)

    # Sort the sentences
    sentence_order = sorted(
        calculated_page_rank.items(), key=lambda x: x[1], reverse=True
    )

    # Yield the first sentence
    yield sentence_order[0][0]

    # Yield the other if not to close from previous yield
    i = 1
    yielded_sentences = [sentence_order[0][0]]
    while i < len(sentence_order):
        idx_cur_sent = sentence_order[i][0]
        add_sent = True
        for idx_prev_sent in yielded_sentences:
            cosine = dict_weight.get((idx_cur_sent, idx_prev_sent)) or dict_weight.get(
                (idx_prev_sent, idx_cur_sent)
            )
            if cosine > 0.8:
                add_sent = False
                break

        if add_sent:
            yielded_sentences.append(idx_cur_sent)
            yield idx_cur_sent
        i += 1


def build_text_prompt(text: str, size: int, embedding_model: Model = None) -> str:
    """
    Build from the text the extractive summary using TextRank algorithm that fit size

    Parameters
    ------------
    text: str
        Original text to summarize
    size : int
        maximal size of the return string
    embedding_model : Mode = None
        embedding_model use to compute cosine similarity, default model if none

    Returns
    ----------
    str
        extractive summary of text with len < size
    """

    if embedding_model == None:
        embedding_model = Model.from_hugging_hub("dangvantuan/sentence-camembert-base")

    list_sentences = split_sentences(text)

    sentence_idx_iterator = iter(text_rank_iterator(list_sentences, embedding_model))

    sentence_len = 0
    sentence_result = []
    while True:
        idx_next = next(sentence_idx_iterator)
        if sentence_len + len(list_sentences[idx_next]) > size:
            break

        sentence_len += len(list_sentences[idx_next])
        sentence_result.append(idx_next)

    # Sort result sentences to have them in same order as in the text
    sentence_result.sort()

    result_text = ""
    for idx_sentence in sentence_result:
        result_text += list_sentences[idx_sentence]

    return result_text
