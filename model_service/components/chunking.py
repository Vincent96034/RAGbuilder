from typing import List

from langchain_core.runnables import chain
from langchain.schema.document import Document
from langchain_text_splitters import TextSplitter


@chain
def chunk_documents(
    documents: List[Document],
    splitter: TextSplitter,
) -> List[Document]:
    """Chunk documents into smaller pieces, using the provided splitter.

    Args:
        documents (List[Document]): A list of documents to be chunked.
        splitter (TextSplitter): The splitter to be used for chunking.

    Returns:
        List[Document]: A list of chunked documents.
    """
    return splitter.split_documents(documents)
