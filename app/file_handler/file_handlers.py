from typing import List
import logging
from abc import ABC, abstractmethod

from fastapi import UploadFile, HTTPException
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.schema.document import Document

from app.file_handler.file_utils import temporary_file
from app.file_handler.file_sanitizers import (sanitize_text, sanitize_pdf)

logger = logging.getLogger(__name__)


class AbstractFileHandler(ABC):
    """Abstract class for file handlers. File handlers are responsible for reading files
    and returning a list of langchain documents. Implementations override the `read`
    method.

    Usage:
    ```
        handler = PDFHandler()
        documents = handler.read(file)
    ```
    """
    def __init__(self, file: UploadFile, extension: str):
        self.file = file
        self.extension = extension

    @abstractmethod
    async def read(self, file: UploadFile) -> List[Document]:
        """Reads the file and returns a list of langchain documents. Those documents are
        structured like this:
        ```
            Document(
                page_content="The content of the page",
                metadata={"source": "The source of the document"},
            )
        ```
        """
        pass


class PDFHandler(AbstractFileHandler):
    """Class for handling PDF-Files. Implements the `read`.

    Usage:
    ```
        handler = PDFHandler()
        documents = handler.read(file)
    ```
    """
    async def read(self) -> List[Document]:
        content = await self.file.read()
        try:
            async with temporary_file(content, suffix=self.extension, sanitize_fn=sanitize_pdf) as tmp_path:
                loader = PyPDFLoader(file_path=tmp_path)
                documents = loader.load()
                for doc in documents:
                    doc.metadata.pop("source", None)
        except Exception as e:
            logger.error(f"Failed to process PDF: {e}")
            raise HTTPException(status_code=500, detail="Failed to process PDF")
        logger.debug(f"Loaded {len(documents)} documents from PDF")
        return documents


class TXTHandler(AbstractFileHandler):
    """Class for handling TXT-Files. Implements the `read`.

    Usage:
    ```
        handler = TXTHandler()
        documents = handler.read(file)
    ```
    """
    async def read(self):
        content = await self.file.read()
        try:
            async with temporary_file(content, suffix=self.extension, sanitize_fn=sanitize_text) as tmp_path:
                loader = TextLoader(file_path=tmp_path)
                documents = loader.load()
                for doc in documents:
                    doc.metadata.pop("source", None)
        except Exception as e:
            logger.error(f"Failed to process TXT: {e}")
            raise HTTPException(status_code=500, detail="Failed to process TXT")
        logger.debug(f"Loaded {len(documents)} documents from TXT")
        return documents
