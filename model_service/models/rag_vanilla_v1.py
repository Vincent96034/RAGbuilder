import logging
from typing import List

from langchain.schema.document import Document
from langchain_core.vectorstores import VectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter

from model_service.models.abstractmodel import AbstractModel
from model_service.components import (
    remove_newlines,
    DocumentChunker,
    VectorStoreUpserter
)

logger = logging.getLogger(__name__)


class RAGVanillaV1(AbstractModel):
    """The DefaultRag Model utilizes a vector store for simple document indexing and
    retrieval. The Model does not any QA-Agents, but returns plain documents, based on
    similarity.

    Initialization Parameters:
        vectorstore (VectorStore): An instance of VectorStore that this model will use for
            storing and retrieving document vectors.
        chunk_size (int, optional): The size of text chunks, in characters, that documents
            should be split into before being indexed. Defaults to 1500.
        chunk_overlap (int, optional): The number of characters that consecutive chunks
            should overlap. Overlapping can help ensure that the context is not lost at
            the boundaries of chunks. Defaults to 50.
        k (int, optional): The number of documents to retrieve from the vector store.

    Usage:
    ```python
    from langchain_pinecone import PineconeVectorStore
    from langchain_openai import OpenAIEmbeddings
    from model_service.models import DefaultRAG

    # Initialize the VectorStore
    vectorstore = PineconeVectorStore(
                    index_name="ragbuilder", 
                    embedding=OpenAIEmbeddings())
    model = DefaultRAG(vectorstore)
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
    instance_id = "RAG-vanilla-v1"

    def __init__(
            self,
            vectorstore: VectorStore,
            chunk_size: int = 1500,
            chunk_overlap: int = 50,
            k: int = 5
    ) -> None:
        super().__init__()
        self.vectorstore = vectorstore
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.k = k

    def index(self,
              documents: List[Document],
              *,
              metadata: dict = None,
              namespace: str = None,
              ) -> None:
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
        if metadata is not None:
            [document.metadata.update(metadata) for document in documents]
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap)
        chunk_documents = DocumentChunker(splitter)
        upsert_documents = VectorStoreUpserter(self.vectorstore, namespace=namespace)

        chain = remove_newlines | chunk_documents | upsert_documents
        chain = self._configure_chain(chain, user_id=namespace)
        return chain.batch(documents)

    def invoke(self,
               input_data: str,
               *,
               filters: dict = {},
               namespace: str = None,
               ) -> List[Document]:
        """Invoke the model to retrieve documents similar to the given input data,
        applying specific filters. User can set a namespace to scope the search query.

        Args:
            input_data (str): The input data to use for the retrieval operation
            filters (dict, optional): Additional search parameters and filters to apply to
                the retrieval query. By default, the number of results ('k') is set to 4.
            namespace (str, optional): An optional namespace identifier to scope the 
                search query. This can also be set in the filters dictionary.

        Returns:
            List[Document]: The list of k most similar documents retrieved by the model.
        """
        search_kwargs = {"k": self.k, "filter": filters}
        if namespace:
            search_kwargs["namespace"] = namespace
        retriever = self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs=search_kwargs)

        chain = self._configure_chain(retriever, user_id=namespace)
        return chain.invoke(input_data)
