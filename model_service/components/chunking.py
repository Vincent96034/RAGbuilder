from typing import List

from langchain.schema.document import Document
from langchain_text_splitters import TextSplitter

from model_service.components.base import BaseCustomRunnable


class DocumentChunker(BaseCustomRunnable):
    """Chunk documents into smaller pieces, using the provided splitter.

    Args:
        splitter (TextSplitter): The splitter to be used for chunking.

    Input:
        documents (List[Document]): A list of documents to be chunked.

    Returns:
        List[Document]: A list of chunked documents.
    """

    def __init__(self, splitter: TextSplitter):
        super().__init__(splitter=splitter)

    def invoke(self,
               document: Document,
               splitter: TextSplitter) -> List[Document]:
        return splitter.split_documents([document])
