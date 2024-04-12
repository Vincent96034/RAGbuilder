from typing import List, Protocol

from langchain.schema.document import Document

from model_service.components.base import BaseCustomRunnable


class RerankerProto(Protocol):
    def rerank(self) -> None:
        ...


class Reranker(BaseCustomRunnable):
    """A runnable that reranks a list of documents based on a query using a reranker
    model.

    Args:
        reranker (RerankerProto): The reranker model to use for reranking.

    Input:
        documents_and_query (dict): A dictionary containing the documents and the query to
            rerank the documents with. The dictionary should have the following keys:
            - "documents": A list of documents to rerank.
            - "query": The query to rerank the documents with.

    Returns:
        List[Doucment]: A ordered list of reranked documents.

    """

    def __init__(self, reranker: RerankerProto):
        super().__init__(reranker=reranker)

    def invoke(self,
               documents_and_query: dict,
               reranker: RerankerProto
               ) -> List[Document]:

        documents = documents_and_query["documents"]
        query = documents_and_query["query"]

        ids = reranker.rerank(documents, query)
        return [documents[index["index"]] for index in ids]
