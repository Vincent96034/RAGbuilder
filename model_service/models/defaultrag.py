from typing import List

from langchain.schema.document import Document

from model_service.models.abstractmodel import AbstractModel


class DefaultRAG(AbstractModel):
    """DefaultRAG model class."""

    def upsert(self, documents: List[Document]):
        """Upsert the model."""
        pass
    
    def invoke(self, input, **kwargs):
        """Invoke the model."""
        pass