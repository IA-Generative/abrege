from threading import Thread
import torch
import nltk
import networkx as nx
from line_profiler import profile


class ThreadWithReturnValue(Thread):

    def __init__(
        self, group=None, target=None, name=None, args=(), kwargs={}, Verbose=None
    ):
        Thread.__init__(self, group, target, name, args, kwargs)
        self._return = None

    def run(self):
        if self._target is not None:
            self._return = self._target(*self._args, **self._kwargs)

    def join(self, *args):
        Thread.join(self, *args)
        return self._return


def thread_encode(model, list_sentence):
    thread = ThreadWithReturnValue(target=model, args=[list_sentence])
    return thread


def openai_encode_multithreading(model, list_sentences, max_batch_size=32):
    sc = 0
    thread_list = []

    while sc < len(list_sentences):
        thread_list.append(
            thread_encode(model, list_sentences[sc : sc + max_batch_size])
        )
        thread_list[-1].start()
        thread_list[-1].run()
        sc += max_batch_size

    res = []
    for t in thread_list:
        res += t.join()

    return res


class Model:
    """A small wrapper around the real model

    to make your own with your model, please use this class
    """

    _device = "cuda" if torch.cuda.is_available() else "cpu"

    def __init__(self, model, model_class: str):
        self._model = model
        self.model_class = model_class

    def encode(self, list_sentences: list[str]) -> torch.tensor:
        match self.model_class:
            case "hugging_hub":
                return self._model.encode(
                    list_sentences,
                    normalize_embeddings=True,
                    convert_to_numpy=False,
                    convert_to_tensor=True,
                )

            case "openai_ef":
                embeddings = openai_encode_multithreading(self._model, list_sentences)
                return torch.tensor(embeddings, device=self._device)

    def from_hugging_hub(model_path: str) -> "Model":
        from sentence_transformers import SentenceTransformer

        return Model(SentenceTransformer(model_path), "hugging_hub")


def split_sentences(text: str) -> list[str]:
    """Split a text around sentences, but does not remove those characters

    Parameters
    ------------
    text : str
        text to be split into sentences

    Returns
    ----------
    list[str]
        a list of sentences in order
    """
    return nltk.tokenize.sent_tokenize(text)


def build_weight(list_sentence, model):

    result = {}
    evaluations = model.encode(list_sentence)

    T_evaluations = torch.transpose(evaluations, 0, 1)

    matrix_cosine = torch.matmul(evaluations, T_evaluations)
    matrix_cosine = matrix_cosine.tolist()

    for i in range(len(list_sentence)):
        for j in range(i + 1, len(list_sentence)):
            result[(i, j)] = float(matrix_cosine[i][j])

    return result


def build_graph(
    list_sentence: list[str], dict_weight: dict[(int, int), float]
) -> nx.Graph:
    """
    Compute the similarity graph
    Parameters
    --------------
    list_sentence : list[str]
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


@profile
def text_rank_iterator(list_sentences: list[str], embedding_model: Model):
    """
    Yield the top sentences of the models, according to the embdeddings delivred
    by embeddding_model

    Parameters
    --------------
    list_sentences : list[str]
        list of sentences to extract best from
    embedding_model: Model
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
    try:
        calculated_page_rank = nx.pagerank(graph, weight="weight")
    except nx.PowerIterationFailedConvergence:
        # If algorithm didn't manage to converge, try it with less precision
        calculated_page_rank = nx.pagerank(
            graph, weight="weight", max_iter=1000, tol=0.1
        )

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

    if embedding_model is None:
        embedding_model = Model.from_hugging_hub("dangvantuan/sentence-camembert-base")

    list_sentences = split_sentences(text)

    sentence_idx_iterator = iter(text_rank_iterator(list_sentences, embedding_model))

    sentence_len = 0
    sentence_result = []
    try:
        while True:
            idx_next = next(sentence_idx_iterator)
            if sentence_len + len(list_sentences[idx_next]) > size:
                break

            sentence_len += len(list_sentences[idx_next])
            sentence_result.append(idx_next)
    except StopIteration:
        pass

    # Sort result sentences to have them in same order as in the text
    sentence_result.sort()

    result_text = ""
    for idx_sentence in sentence_result:
        result_text += list_sentences[idx_sentence]

    return result_text


def test_time():
    from langchain_community.document_loaders import PyPDFLoader

    loader = PyPDFLoader("Malo_Adler_Thesis.pdf")
    pages = loader.load()

    text = ""
    for page in pages:
        text += page.page_content

    build_text_prompt(text, 3000)


if __name__ == "__main__":
    pass
