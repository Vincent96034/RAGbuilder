import logging
from typing import List

from langchain.schema.document import Document
from langchain_core.vectorstores import VectorStore
from langchain_cohere import CohereRerank
from langchain_core.runnables import RunnableParallel, RunnablePassthrough

from model_service.models import RAGVanillaV1
from model_service.components.reranking import Reranker


logger = logging.getLogger(__name__)


class RAGRerankV1CH(RAGVanillaV1):
    """The RAG-rerank-v1-ch model is a RAG model that uses a vector store for simple
    document retrieval, but reranks the retrieved documents using a Cohere model. The
    model is initialized with a vector store, and the number of documents to retrieve and
    rerank.

    Initialization Parameters:
        vectorstore (VectorStore): An instance of VectorStore that this model will use for
            storing and retrieving document vectors.
        chunk_size (int, optional): The size of text chunks, in characters, that documents
            should be split into before being indexed. Defaults to 1500.
        chunk_overlap (int, optional): The number of characters that consecutive chunks
            should overlap. Overlapping can help ensure that the context is not lost at
            the boundaries of chunks. Defaults to 50.
        k_retrieve (int, optional): The number of documents to retrieve from the vector
            store. Defaults to 35.
        k_rerank (int, optional): The number of documents to rerank using the Cohere
            model. Defaults to 5. This is the final number of documents that will be
            returned by invoking the model.

    Usage:
    ```python
    from langchain_pinecone import PineconeVectorStore
    from langchain_openai import OpenAIEmbeddings
    from model_service.models import RAGRerankV1CH

    # Initialize the VectorStore
    vectorstore = PineconeVectorStore(
                    index_name="ragbuilder", 
                    embedding=OpenAIEmbeddings())
    model = RAGRerankV1CH(vectorstore)
    documents = List[Documents]

    # Index the documents
    model.index(documents, namespace="test_user_id")

    # Retrieve similar documents
    model.invoke(
        input_data="Search query here.",
        namespace="test_user_id",
        filters={"project_id": "test-project"})
    ```
    """
    instance_id = "RAG-rerank-v1-ch"

    def __init__(
            self,
            vectorstore: VectorStore,
            chunk_size: int = 1500,
            chunk_overlap: int = 50,
            k_retrieve: int = 35,
            k_rerank: int = 5,
    ) -> None:
        super().__init__(vectorstore=vectorstore, chunk_size=chunk_size,
                         chunk_overlap=chunk_overlap, k=k_retrieve)
        self.k_retrieve = k_retrieve
        self.k_rerank = k_rerank

    def index(self, documents: List[Document], namespace: str = None) -> None:
        """Indexes a list of documents by splitting them into chunks, cleaning, and then
        adding these chunks to the vector store.

        Args:
            documents (List[Document]): The list of documents to be indexed. Each document
                can (and should) have metadata attached to it.
            metadata (dict, optional): An optional dictionary of metadata to attach to the
                documents. Note that this is applied for all documents in the list.
            namespace (str, optional): An optional namespace identifier to scope the
                indexing operation. When specified, all chunks derived from the documents
                are indexed under this namespace.

        Returns:
            List[str]: The list of document IDs that were indexed.
        """
        super().index(documents, namespace=namespace)

    def invoke(self,
               input_data: str,
               *,
               filters: dict = {},
               namespace: str = None,
               ) -> List[Document]:
        """Invoke the model to retrieve documents similar to the given input data,
        applying specific filters. User can set a namespace to scope the search query.
        After initial retrieval, the model will rerank the retrieved documents and output
        the top k_rerank documents.

        Args:
            input_data (str): The input data to use for the retrieval operation
            filters (dict, optional): Additional search parameters and filters to apply to
                the retrieval query. By default, the number of results ('k') is set to 4.
            namespace (str, optional): An optional namespace identifier to scope the 
                search query. This can also be set in the filters dictionary.

        Returns:
            List[Document]: The list of k_rerank most similar documents retrieved by the
            model.
        """
        search_kwargs = {"k": self.k_retrieve, "filter": filters}
        if namespace:
            search_kwargs["namespace"] = namespace
        retriever = self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs=search_kwargs)
        ch = CohereRerank(top_n=self.k_rerank)
        reranker = Reranker(ch)

        chain = (
            RunnableParallel({"documents": retriever, "query": RunnablePassthrough()})
            | reranker
        )

        chain = self._configure_chain(chain, user_id=namespace)
        return chain.invoke(input_data)
