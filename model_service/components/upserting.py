from typing import List

from langchain_core.runnables import chain
from langchain_core.vectorstores import VectorStore
from langchain.schema.document import Document


@chain
def upsert_documents(
    documents: List[Document],
    vectorstore: VectorStore,
    namespace: str = None
) -> List[str]:
    """Upsert documents into the vector store.

    Args:
        documents (List[Document]): A list of documents to be upserted.
        vectorstore (VectorStore): The vector store to upsert the documents into.
        namespace (str, optional): The namespace to upsert the documents into. Defaults to None.

    Returns:
        List[str]: A list of document IDs.
    """
    return vectorstore.add_documents(documents, namespace=namespace)
