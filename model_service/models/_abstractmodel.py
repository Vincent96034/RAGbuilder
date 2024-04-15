import os
import inspect
from abc import ABC, abstractmethod
from typing import List, Any, Optional

from langchain_core.vectorstores import VectorStore
from langchain_core.runnables import Runnable
from langchain.schema.document import Document


class AbstractModel(ABC):
    """Abstract class for models. Each implementation should define an instance_id and the
    following methods: index, deindex (default available), and invoke.

    Args:
        vectorstore (VectorStore, optional): The vectorstore to use for indexing.
    """
    instance_id = None
    """The instance ID of the model. This should be set by subclasses."""

    def __init__(self, vectorstore: Optional[VectorStore] = None, **kwargs):
        self._check_environment()
        self.vectorstore = vectorstore
        print(f"Model `{self.instance_id}` initialized.")

    @abstractmethod
    def index(self, documents: List[Document], **kwargs) -> Any:
        """Define indexing for the model.

        Args:
            documents (List[Document]): A list of documents to index.
            **kwargs: Additional keyword arguments.

        Returns:
            Any
        """
        ...

    @abstractmethod
    def invoke(self, input_data, **kwargs) -> List[Document]:
        """Invoke the model with input data. This method should define Runnable and return
        self._invoke(chain, input_data) to run the chain.

        Args:
            input_data: The input data to the model.
            **kwargs: Additional keyword arguments.

        Returns:
            List[Document]: The result of the model invocation.
        """
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

    def _configure_chain(self, chain: Runnable, user_id: str = None) -> Runnable:
        """Configure the chain with metadata for tracing. Apply this before invoking the
        chain to attach metadata to the run.
        """
        method_name = inspect.stack()[1].function or "unknown"
        metadata = {
            "instance_id": self.instance_id or "unknown",
            "user_id": user_id,
            "method": method_name}
        chain = chain.with_config({
            "run_name": f"[{self.instance_id}]-{method_name}",
            "tags": [self.instance_id or "unknown"],
            "metadata": metadata})
        return chain

    def _check_environment(self):
        """Check the environment for required variables. Can be overridden by subclasses.
        Currently checks for LANGCHAIN_API_KEY and OPENAI_API_KEY.

        Raises:
            Exception: If either LANGCHAIN_API_KEY or OPENAI_API_KEY is not set.
        """
        if os.getenv("LANGCHAIN_API_KEY") is None:
            raise Exception("LANGCHAIN_API_KEY is not set")
        if os.getenv("OPENAI_API_KEY") is None:
            raise Exception("OPENAI_API_KEY is not set")

    def __repr__(self):
        return f"<{self.__class__.__name__} instance_id={self.instance_id}>"
