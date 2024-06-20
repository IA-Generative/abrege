import concurrent.futures
from typing import (
    Literal,
    get_args,
)

import networkx as nx
import nltk
import tiktoken
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sklearn.cluster import (
    KMeans,
)
from sklearn.metrics import (
    pairwise_distances_argmin_min,
)
import numpy as np
from transformers import AutoTokenizer


tokenizer = AutoTokenizer.from_pretrained("OrdalieTech/Solon-embeddings-large-0.1")


def openai_encode_multithreading(
    model, lc: list[str], max_batch_size: int = 32
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
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_embedding = executor.map(
            model,
            [
                lc[c_count : c_count + max_batch_size]
                for c_count in range(0, len(lc), max_batch_size)
            ],
        )
    result = []
    for embedding in future_embedding:
        result += embedding
    return result


ModelType = Literal[
    "HuggingFaceEmbeddings",
    "OpenAIEmbeddingFunction",
    "SentenceTransformer",
    "OpenAIEmbeddings",
    "OpenAI",
]


class EmbeddingModel:
    """A small wrapper around the real model, to use in text_rank and k-means

    Attributes
    -----------
    _model : Any
        model to wrap

    """

    def __init__(
        self,
        model,
    ):
        self._model = model
        name_class = type(self._model).__name__
        self.model_class = name_class
        if self.model_class not in get_args(ModelType):
            raise ValueError(
                f"""Embeddding Model was not implemented for {self.model_class},
                  available model class are {get_args(ModelType)}"""
            )

    def encode(self, list_chunk: list[str]) -> np.ndarray:
        match self.model_class:

            case "OpenAIEmbeddingFunction":
                embeddings = openai_encode_multithreading(self._model, list_chunk)
                return np.array(embeddings)

            case "HuggingFaceEmbeddings":
                # encode_kwargs = {"normalize_embeddings": True}
                embeddings = self._model.embed_documents(list_chunk)
                return np.array(embeddings)

            case "SentenceTransformer":
                embeddings = self._model.encode(
                    list_chunk,
                    convert_to_numpy=False,
                    convert_to_tensor=True,
                    normalize_embeddings=True,
                )
                return embeddings

            case "OpenAIEmbeddings":
                embeddings = self._model.embed_query("say what")
                raise NotImplementedError
                return np.array(embeddings)

            case "OpenAI":
                embeddings = [
                    self._model.embeddings.create(input=[chunk], model="")
                    .data[0]
                    .embedding
                    for chunk in list_chunk
                ]
                return np.array(embeddings)

            case _:
                raise ValueError(
                    f"""EmbeddingModel.encode is not implemented for
                    model_class : {type(self._model)}
                    , supported class are {get_args(ModelType)}"""
                )


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
    list_chunk: list[str], model: EmbeddingModel
) -> dict[(int, int), float]:
    """Compute the weight (cosine similarity) of the graph

    Parameters
    ----------
    list_chunk : list[str]
        list of chunk of text (can be either sentences or just chunk)
    model : EmbeddingModel
        model used to embed sentences

    Returns
    -------
    dict[(int, int), float]
        map between a pair of sentence index and their cosine similarity
    """

    result = {}
    evaluations = model.encode(list_chunk)

    T_evaluations = np.swapaxes(evaluations, 0, 1)

    matrix_cosine = np.matmul(evaluations, T_evaluations)

    for i in range(len(list_chunk)):
        for j in range(i + 1, len(list_chunk)):
            result[(i, j)] = float(matrix_cosine[i, j])

    return result


def build_graph(
    list_chunk: list[str], dict_weight: dict[(int, int), float]
) -> nx.Graph:
    """
    Compute the similarity graph
    Parameters
    --------------
    list_chunk : list[str]
        list of chunk of text (can be either sentences or just chunk)
    dict_weight : dict[(int, int), float]
        a mapping of pair of sentence (index in original text) and cosine
        similarity

    Returns
    ---------
    networkx.Graph
        graph of similarity
    """

    graph = nx.Graph()
    graph.add_nodes_from(range(len(list_chunk)))

    for (idx_sent1, idx_sent2), weight in dict_weight.items():
        graph.add_edge(idx_sent1, idx_sent2, weight=weight)

    return graph


def compute_textrank_score(list_chunk: list[str], embedding_model: EmbeddingModel):

    # Next build a similarity relation between each pair of sentences
    dict_weight = build_weight(list_chunk, embedding_model)

    # Build the graph
    graph = build_graph(list_chunk, dict_weight)

    # And apply the text rank algorithm
    try:
        calculated_page_rank = nx.pagerank(graph, weight="weight")
    except nx.PowerIterationFailedConvergence:
        # If algorithm didn't manage to converge, try it with less precisi:w
        calculated_page_rank = nx.pagerank(
            graph, weight="weight", max_iter=1000, tol=0.1
        )
    return calculated_page_rank


def text_rank_iterator2(list_chunk: list[str], embedding_model: EmbeddingModel):
    """
    Yield the top sentences of the models, according to the embeddings computed
    by embedding_model

    Parameters
    --------------
    list_chunk : list[str]
        list of chunk of text (can be either sentences or just chunk)

    embedding_model: EmbeddingModel
        model to use for embeddings of sentences

    Yield
    --------
    int
        index of the best sentences so far
    """

    # Next build a similarity relation between each pair of sentences
    dict_weight = build_weight(list_chunk, embedding_model)

    # Build the graph
    graph = build_graph(list_chunk, dict_weight)

    # And apply the text rank algorithm
    try:
        calculated_page_rank = nx.pagerank(graph, weight="weight")
    except nx.PowerIterationFailedConvergence:
        # If algorithm didn't manage to converge, try it with less precisi:w
        calculated_page_rank = nx.pagerank(
            graph, weight="weight", max_iter=1000, tol=0.1
        )

    # Sort the sentences
    chunk_order = sorted(calculated_page_rank.items(), key=lambda x: x[1], reverse=True)

    # Yield the first sentence
    yield chunk_order[0][0]

    # Yield the other if not to close from previous yield
    i = 1
    yielded_chunks = [chunk_order[0][0]]
    while i < len(chunk_order):
        idx_cur_sent = chunk_order[i][0]
        add_sent = True
        for idx_prev_sent in yielded_chunks:
            cosine = dict_weight.get((idx_cur_sent, idx_prev_sent)) or dict_weight.get(
                (idx_prev_sent, idx_cur_sent)
            )
            if cosine > 0.8:
                add_sent = False
                break

        if add_sent:
            yielded_chunks.append(idx_cur_sent)
            yield idx_cur_sent
        i += 1


def split_chunk(text: str, chunk_size: int = 300) -> list[str]:
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
    text_splitter = RecursiveCharacterTextSplitter.from_huggingface_tokenizer(
        tokenizer, chunk_size=chunk_size, chunk_overlap=30
    )
    split_text = text_splitter.split_text(text)
    return split_text


def build_text_prompt_kmeans(
    text: str,
    size: int,
    embedding_model: EmbeddingModel,
    n_clusters: int = 10,
    *,
    chunk_type: Literal["sentences", "chunks"] = "chunks",
) -> list[str]:
    """Build an extractive summary using k-means algorithm
    for each cluster, extract the closet chunk to the center and add it to the
    summary

    Parameters
    ----------
    text : str
        text to compute summary
    size : int
        size of the text (in term of tokens) to compute
    embedding_model : EmbeddingModel
        model to use to compute embeddings of chunk
    n_clusters : int = 10
        number cluster to build (size of chunk = size // nb_chunks)
    chunk_type : Literal['sentences', 'chunks'], optional
        the type of chunks to construct clusters around
        default to chunks

    Returns
    -------
    str
        extractive summary
    """
    # First we have to split the text
    if chunk_type == "chunks" and embedding_model.model_class not in [
        "OpenAIEmbeddingFunction",
        "OpenAI",
    ]:
        list_chunk = split_chunk(text, size // n_clusters)
    elif chunk_type == "chunks" and embedding_model.model_class in [
        "OpenAIEmbeddingFunction",
        "OpenAI",
    ]:
        chunk_size = 512  # Chunk size limit for OpenAIEmbeddingFunction
        n_clusters = size // chunk_size + 1
        list_chunk = split_chunk(text, chunk_size)
    elif chunk_type == "sentences":
        list_chunk = split_sentences(text)

    # Then we embed each sentences using the model
    embeddings = embedding_model.encode(list_chunk)

    # Now we can use k means algorithm to compute cluster
    kmean = KMeans(n_clusters=n_clusters)
    clusters = kmean.fit_predict(embeddings)

    clusters_to_embeddings = [[] for _ in range(n_clusters)]
    cluster_map = [[] for _ in range(n_clusters)]

    for idx, (embedding, cluster) in enumerate(zip(embeddings, clusters)):
        clusters_to_embeddings[cluster].append(embedding)
        cluster_map[cluster].append(idx)

    # Now we compute the closest chunk to each cluster center
    chunk_idx = []
    for embeddings_list, cluster_center, idx_map in zip(
        clusters_to_embeddings, kmean.cluster_centers_, cluster_map
    ):
        embedding_center, _ = pairwise_distances_argmin_min(
            cluster_center.reshape(1, -1), embeddings_list
        )
        chunk_idx.append(idx_map[int(embedding_center[0])])

    # Finally return the chunk in order
    chunk_idx.sort()

    return [list_chunk[idx] for idx in chunk_idx]


def build_text_prompt_text_rank(
    text: str,
    size: int,
    embedding_model: EmbeddingModel,
    *,
    chunk_type: Literal["sentences", "chunks"] = "chunks",
    chunk_size: int = 1000,
) -> list[str]:
    """
    Build from the text the extractive summary using TextRank algorithm that
    fit size

    Parameters
    ------------
    text: str
        Original text to summarize
    size : int
        maximal size of the return string, in term of token
        (token are counted by tiktoken.get_encoding('cl100k_base'))
    embedding_model : EmbeddingModel
        embedding_model use to compute cosine similarity
    chunk_type : Literal["sentences, "chunks"], optional
        the type of chunks to split the text and rank betweens
        default to sentence
    chunk_size : int, optional
        the size of chunks if chunk_type = 'chunks'
        default to 100

    Returns
    ----------
    str
        extractive summary of text with len < size
    """
    if chunk_type == "sentences":
        list_chunks = split_sentences(text)
    elif chunk_type == "chunks":
        if embedding_model.model_class in ["OpenAIEmbeddingFunction", "OpenAI"]:
            chunk_size = 512  # token size limit for this class
        list_chunks = split_chunk(text, chunk_size=chunk_size)

    chunk_idx_iterator = iter(text_rank_iterator(list_chunks, embedding_model))

    result_len = 0
    idx_result = []
    enc = tiktoken.get_encoding("cl100k_base")
    try:
        while True:
            idx_next = next(chunk_idx_iterator)
            num_token_next = len(enc.encode(list_chunks[idx_next]))
            if result_len + num_token_next > size:
                break

            result_len += num_token_next
            idx_result.append(idx_next)
    except StopIteration:
        pass

    # Sort result sentences to have them in same order as in the text
    idx_result.sort()

    return [list_chunks[idx] for idx in idx_result]


def text_rank_iterator(list_chunks: list[str], embedding_model: EmbeddingModel):
    """
    Yield the top sentences of the models, according to the embeddings computed
    by embedding_model

    Parameters
    --------------
    list_chunk : list[str]
        list of chunk of text (can be either sentences or just chunk)

    embedding_model: EmbeddingModel
        model to use for embeddings of sentences

    Yield
    --------
    int
        index of the best sentences so far
    """
    # First get the embeddings
    embeddings = embedding_model.encode(list_chunks)

    # The build the cosine similarity matrix
    cosine_matrix = np.matmul(embeddings, np.swapaxes(embeddings, 0, 1))

    # Compute the best scorer in PageRank
    chunk_rank = page_rank(cosine_matrix)

    # Next we iter through the best chunk according to text rank
    # If we found a chunk that has a similarity to close to a previous yielded chunk
    # we skip it to avoid redundance
    idx = 0
    previous_yielded = []
    while idx < len(chunk_rank):
        chunk_idx = chunk_rank[idx]
        send_chunk = True
        for p_yielded_idx in previous_yielded:
            if np.all(
                cosine_matrix[chunk_rank, p_yielded_idx] > 0.8
            ):  # Ref : Malo Adler thesis
                send_chunk = False
                break

        if send_chunk:
            previous_yielded.append(chunk_idx)
            yield chunk_idx

        idx += 1


class PowerIterationFailedConvergence(Exception):

    def __init__(self, *args):
        super().__init__(*args)


def page_rank(
    cosine_matrix: np.ndarray,
    alpha: float = 0.85,
    eps: float = 0.000001,
    max_iter: int = 100,
) -> np.ndarray:
    """
    Compute the page rank algorithm on the given embeddins

    Parameters
    -----------
    cosine_matrix: np.ndarray
        Matrix of dimensions (n, n) where n is the number of chunks representing where
        M[i, j] = cosine_simaliraty(list_chunk[i], list_chunk[j])
    alpha: float
        damping factor
        default to 0.85
    eps: float
        tolerance for convergence
        default to 0.01
    max_iter: int
        maximum number of iteration
        default to 100

    Returns
    ---------
    np.ndarray
        array of length n containing the pagerank values
    """
    n_iter = 0
    sum_row = np.sum(cosine_matrix, axis=1)
    T_cosine_matrix = np.transpose(cosine_matrix)
    P0 = np.array([alpha for _ in cosine_matrix])
    P1 = (1 - alpha) + (alpha * np.matmul(T_cosine_matrix, P0 / sum_row))
    while np.linalg.norm(P0 - P1) > eps and n_iter < max_iter:
        n_iter += 1
        P0 = P1
        P1 = (1 - alpha) + (alpha * np.matmul(T_cosine_matrix, P0 / sum_row))
    if n_iter == max_iter:
        raise PowerIterationFailedConvergence(
            f"Failed to convergence under {eps} in {max_iter} iterations"
        )

    return np.argsort(P1)[::-1]


if __name__ == "__main__":
    import os
    from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

    llm = OpenAIEmbeddingFunction(
        api_key=os.environ["OPENAI_API_KEY"], api_base=os.environ["OPENAI_API_BASE"]
    )
    embedding_model = EmbeddingModel(llm, model_class="openai_ef")
