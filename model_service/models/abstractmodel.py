from abc import ABC
from typing import List

from langchain.schema.document import Document


class AbstractModel(ABC):

    def upsert(self, documents: List[Document]):
        """Define upsert for model."""
        ...

    def invoke(self, input, **kwargs):
        """Define invoke for model."""
        ...