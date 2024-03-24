import os
from typing import List, Any
from abc import ABC, abstractmethod

from langchain_core.runnables import Runnable
from langchain.schema.document import Document


class AbstractModel(ABC):
    instance_id = None

    def __init__(self, ):
        self._check_environment()

    @abstractmethod
    def index(self, documents: List[Document], **kwargs):
        """Define indexing for the model."""
        ...

    @abstractmethod
    def invoke(self, input_data, **kwargs):
        """Invoke the model with input data. This method should define Runnable and return
        self._invoke(chain, input_data) to run the chain."""
        ...

    def _invoke(self, chain: Runnable, input_data: Any = None, user_id: str = None):
        metadata = {
            "instance_id": self.instance_id or "unknown",
            "user_id": user_id
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
