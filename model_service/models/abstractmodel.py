import os
from typing import List, Any, Optional
from abc import ABC, abstractmethod

from langchain_core.runnables import Runnable
from langchain.schema.document import Document


class AbstractModel(ABC):
    instance_id = None

    def __init__(self, vectorstore=None, **kwargs):
        self._check_environment()
        self.vectorstore = vectorstore

    @abstractmethod
    def index(self, documents: List[Document], **kwargs):
        """Define indexing for the model."""
        ...

    def deindex(self,
                ids: Optional[List[str]] = None,
                delete_all: Optional[bool] = None,
                namespace: Optional[str] = None,
                filter: Optional[dict] = None
                ) -> None:
        """Define deindexing for the model. This is the default implementation, that
        deletes by vector IDs or filter.

        Parameters:
            - ids (List[str, optional]): List of ids to delete.
            - filter: Dictionary of conditions to filter vectors to delete.
            - delete_all (bool, optional): If True, delete all vectors in the namespace.
            - namespace (str, optional): The namespace to delete from.
        
        Returns:
            None
        """
        self.vectorstore.delete(ids, delete_all=delete_all,
                                filter=filter, namespace=namespace)

    @abstractmethod
    def invoke(self, input_data, **kwargs) -> List[Document]:
        """Invoke the model with input data. This method should define Runnable and return
        self._invoke(chain, input_data) to run the chain."""
        ...

    def _invoke(self, chain: Runnable, input_data: Any = None, user_id: str = None):
        metadata = {
            "instance_id": self.instance_id or "unknown",
            "user_id": user_id,
            "method": "invoke"
        }
        chain = chain.with_config({
            "tags": [self.instance_id or "unknown"],
            "metadata": metadata})
        return chain.invoke(input=input_data)

    def _check_environment(self):
        if os.getenv("LANGCHAIN_API_KEY") is None:
            raise Exception("LANGCHAIN_API_KEY is not set")
        if os.getenv("OPENAI_API_KEY") is None:
            raise Exception("OPENAI_API_KEY is not set")
        
    def __repr__(self):
        return f"<{self.__class__.__name__} instance_id={self.instance_id}>"
