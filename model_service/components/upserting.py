from typing import List

from langchain_core.vectorstores import VectorStore
from langchain.schema.document import Document

from model_service.components.base import BaseCustomRunnable


class VectorStoreUpserter(BaseCustomRunnable):
    """Upsert documents into the vector store.

    Args:
        vectorstore (VectorStore): The vector store to upsert the documents into.
        namespace (str, optional): The namespace to upsert the documents into. Defaults to
            None.

    Input:
        documents (List[Document]): A list of documents to be upserted.

    Returns:
        List[str]: A list of document IDs.
    """

    def __init__(self, vectorstore: VectorStore, namespace: str = None):
        super().__init__(vectorstore=vectorstore, namespace=namespace)

    def invoke(self,
               documents: List[Document],
               vectorstore: VectorStore,
               namespace: str = None
               ) -> List[str]:
        return vectorstore.add_documents(documents, namespace=namespace)
