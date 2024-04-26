import sys
from sklearn.cluster import KMeans
from sklearn.metrics import pairwise_distances_argmin_min
import concurrent.futures
import torch
import nltk
import networkx as nx
from line_profiler import profile
from langchain_text_splitters.character import RecursiveCharacterTextSplitter


def openai_encode_multithreading(
    model, lc: list[str], max_batch_size=32
) -> list[list[int]]:
    """Encode the list of sentence using multithreading

    Parameters
    ------------
    model
        OpenAI embedding model function used to embed sentences
    lc: list[str]
        list of chunks of text to embed
    max_batch_size : int = 32
        maximal size of a batch than can be embedded by the model

    Returns
    -----------
    list[list[int]]
        a list of embedded vectors
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_embedding = [
            executor.submit(model, lc[c_count : c_count + max_batch_size])
            for c_count in range(0, len(lc), max_batch_size)
        ]

        result = []
        for future in concurrent.futures.as_completed(future_embedding):
            try:
                result += future.result()
            except Exception as err:
                print(err)
                sys.exit(1)
        return result


class EmbeddingModel:
    """A small wrapper around the real model, to use in text_rank and k-means

    Attributes
    -----------
    _model : Any
        model to wrap
    model_class : str {'hugging_hub', 'openai_ef'}
        the class of the model (to know how to encode data)

    Examples
    -----------
    >>> llm = OpenAIEmbeddingFunction(
        api_key = your_api_key
        api_base = your_api_base
    )
    >>> embedding_model = EmbeddingModel(llm, model_class="openai_ef")
    >>> sentence_transformer = SentenceTransformer("some_path")
    >>> embedding_model = EmbeddingModel(sentence_transformer, "hugging_hub")

    """

    _device = "cuda" if torch.cuda.is_available() else "cpu"

    def __init__(self, model, model_class: str):
        self._model = model
        self.model_class = model_class

    def encode(self, list_sentences: list[str]) -> torch.Tensor:
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

            case "HuggingFaceEmbeddings":
                embeddings = self._model.embed_documents(list_sentences)
                return torch.tensor(embeddings, device=self._device)

    @staticmethod
    def from_hugging_hub_sentence_transformer(model_path: str) -> "EmbeddingModel":
        from sentence_transformers import SentenceTransformer

        return EmbeddingModel(SentenceTransformer(model_path), "hugging_hub")


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


def build_weight(
    list_sentence: list[str], model: EmbeddingModel
) -> dict[(int, int), float]:
    """Compute the weight (cosine similarity) of the graph

    Parameters
    ----------
    list_sentence : list[str]
        list of sentence to compute similarity between
    model : EmbeddingModel
        model used to embed sentences

    Returns
    -------
    dict[(int, int), float]
        map between a pair of sentence index and their cosine similarity
    """

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
def text_rank_iterator(list_sentences: list[str], embedding_model: EmbeddingModel):
    """
    Yield the top sentences of the models, according to the embeddings computed
    by embedding_model

    Parameters
    --------------
    list_sentences : list[str]
        list of sentences to extract best from
    embedding_model: EmbeddingModel
        model to use for embeddings of sentences

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


def chunk_splitter(text: str, chunk_size: int = 300) -> list[str]:
    """split the text into chunk with a small overlap

    Parameters
    ----------
    text : str
        text to be split
    chunk_size : int = 500
        size of chunk

    Returns
    -------
    list[str]
        list of the chunks
    """
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=chunk_size, chunk_overlap=15
    )
    split_text = text_splitter.split_text(text)
    return split_text


def build_text_prompt_kmeans(
    text: str, n_clusters: int, embedding_model: EmbeddingModel
) -> str:
    """Build an extractive summary using k-means algorithm
    for each cluster, extract the closet chunk to the center and add it to the summary

    Parameters
    ----------
    text : str
        text to compute summary
    n_clusters : int
        number of cluster (and thus sentences in the summary) to compute
    embedding_model : EmbeddingModel
        model to use to compute embeddings of chunk

    Returns
    -------
    str
        extractive summary
    """
    # First we have to split the text, for the moment, split aroud setences
    # Maybe it would be better to split around chunk with some overlap to have better control
    # on context and size of the summary
    list_chunk = chunk_splitter(text)

    # Then we embed each sentences using the model
    embeddings = embedding_model.encode(list_chunk).cpu().numpy()

    # Now we can use k means algorithm to compute cluster
    kmean = KMeans(n_clusters=n_clusters)
    clusters = kmean.fit_predict(embeddings)

    clusters_to_embeddings = [[] for _ in range(n_clusters)]
    cluster_map = [[] for _ in range(n_clusters)]

    for embedding, cluster, idx in zip(embeddings, clusters, range(len(list_chunk))):
        clusters_to_embeddings[cluster].append(embedding)
        cluster_map[cluster].append(idx)

    # Now we compute the closest sentences to each cluster center
    sentences_idx = []
    for embeddings_list, cluster_center, idx_map in zip(
        clusters_to_embeddings, kmean.cluster_centers_, cluster_map
    ):
        embedding_center, _ = pairwise_distances_argmin_min(
            cluster_center.reshape(1, -1), embeddings_list
        )
        sentences_idx.append(idx_map[int(embedding_center[0])])

    # Finally return the sentences in order
    sentences_idx.sort()

    res = ""
    for idx in sentences_idx:
        res += list_chunk[idx]

    return res


def build_text_prompt(text: str, size: int, embedding_model: EmbeddingModel) -> str:
    """
    Build from the text the extractive summary using TextRank algorithm that fit size

    Parameters
    ------------
    text: str
        Original text to summarize
    size : int
        maximal size of the return string
    embedding_model : EmbeddingModel
        embedding_model use to compute cosine similarity, default model if none

    Returns
    ----------
    str
        extractive summary of text with len < size
    """

    if embedding_model is None:
        embedding_model = EmbeddingModel.from_hugging_hub_sentence_transformer(
            "dangvantuan/sentence-camembert-base"
        )

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


def test_kmeans():
    embedding_model = EmbeddingModel.from_hugging_hub_sentence_transformer(
        "dangvantuan/sentence-camembert-base"
    )

    from py_pdf_parser.loaders import load_file

    document = load_file("Malo_Adler_Thesis.pdf")
    text2 = ""
    for element in document.elements:
        text2 += element.text()

    res = build_text_prompt_kmeans(text2, 10, embedding_model)
    print(res)

    print("\n TextRANK \n")

    res2 = build_text_prompt(text2, len(res), embedding_model)
    print(res2)
    print(len(res))


if __name__ == "__main__":
    test_kmeans()
