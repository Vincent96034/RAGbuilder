from typing import List
from functools import partial
from abc import ABC, abstractmethod

from langchain.schema.document import Document
from langchain_core.runnables.config import RunnableConfig
from langchain_core.runnables import RunnableLambda


class BaseCustomRunnable(ABC):
    def __init__(self, *args, **kwargs):
        self.func = partial(self.invoke, *args, **kwargs)
        self.runnable = RunnableLambda(self.func, name=self.__class__.__name__)

    @abstractmethod
    def invoke(self, *args, **kwargs):
        pass

    def __call__(self, *args, **kwargs):
        return self.runnable.invoke(*args, **kwargs, config=RunnableConfig(run_name=self.__class__.__name__))


class BatchChainRunner(BaseCustomRunnable):
    """Run a chain on a batch of documents."""

    def __init__(self, chain):
        super().__init__(chain=chain)

    def invoke(self, documents: List[Document], chain) -> List[Document]:
        return chain.batch(documents)
