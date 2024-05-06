import concurrent.futures
import sys
from typing import (
    Literal,
    get_args,
)

import networkx as nx
import nltk
import tiktoken
import torch
from langchain.text_splitter import (
    RecursiveCharacterTextSplitter,
)
from sklearn.cluster import (
    KMeans,
)
from sklearn.metrics import (
    pairwise_distances_argmin_min,
)


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


ModelType = Literal[
    "HuggingFaceEmbeddings",
    "OpenAIEmbeddingFunction",
    "SentenceTransformer",
]


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

    def __init__(self, model, model_class: ModelType):
        self._model = model
        if model_class not in get_args(ModelType):
            raise ValueError(
                f"""Embeddding Model was not implemented for {model_class},
                  available model class are {get_args(ModelType)}"""
            )
        self.model_class: ModelType = model_class

    def encode(self, list_chunk: list[str]) -> torch.Tensor:
        match self.model_class:

            case "OpenAIEmbeddingFunction":
                embeddings = openai_encode_multithreading(self._model, list_chunk)
                return torch.tensor(embeddings, device=self._device)

            case "HuggingFaceEmbeddings":
                embeddings = self._model.embed_documents(
                    list_chunk,
                )
                return torch.tensor(embeddings, device=self._device)

            case "SentenceTransformer":
                embeddings = self._model.encode(
                    list_chunk,
                    convert_to_numpy=False,
                    convert_to_tensor=True,
                    normalize_embeddings=True,
                )
                return embeddings

            case _:
                raise ValueError(
                    f"""EmbeddingModel.encode is not implemented for
                    model_class : {type(self._model)}
                    , supported class are {get_args(ModelType)}"""
                )

    @staticmethod
    def from_hugging_hub_sentence_transformer(
        model_path: str,
    ) -> "EmbeddingModel":
        from sentence_transformers import (
            SentenceTransformer,
        )

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

    T_evaluations = torch.transpose(evaluations, 0, 1)

    matrix_cosine = torch.matmul(evaluations, T_evaluations)
    matrix_cosine = matrix_cosine.tolist()

    for i in range(len(list_chunk)):
        for j in range(i + 1, len(list_chunk)):
            result[(i, j)] = float(matrix_cosine[i][j])

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


def text_rank_iterator(list_chunk: list[str], embedding_model: EmbeddingModel):
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
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=chunk_size, chunk_overlap=0
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
) -> str:
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
    if (
        chunk_type == "chunks"
        and embedding_model.model_class != "OpenAIEmbeddingFunction"
    ):
        list_chunk = split_chunk(text, size // n_clusters)
    elif (
        chunk_type == "chunks"
        and embedding_model.model_class == "OpenAIEmbeddingFunction"
    ):
        chunk_size = 200  # Chunk size limit for OpenAIEmbeddingFunction
        n_clusters = size // chunk_size + 1
        list_chunk = split_chunk(text, chunk_size)
    elif chunk_type == "sentences":
        list_chunk = split_sentences(text)

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

    res = ""
    for idx in chunk_idx:
        res += list_chunk[idx]

    # Skip the last space ^^
    return res


def build_text_prompt(
    text: str,
    size: int,
    embedding_model: EmbeddingModel,
    *,
    chunk_type: Literal["sentences", "chunks"] = "sentences",
    chunk_size: int = 200,
) -> str:
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
        list_chunks = split_chunk(text, chunk_size)

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

    result_text = ""
    for idx_chunk in idx_result:
        result_text += list_chunks[idx_chunk]

    return result_text


if __name__ == "__main__":
    pass
