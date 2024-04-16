import logging
from typing import List, Optional

import tiktoken
from langchain_openai import ChatOpenAI
from langchain.schema.document import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.vectorstores import VectorStore
from langchain_core.language_models import BaseLanguageModel
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import (
    RunnableParallel,
    RunnableLambda,
)

from model_service.models._abstractmodel import AbstractModel
from model_service.components.chains import (
    build_stuff_chain,
    build_reduce_chain,
    build_map_chain
)
from model_service.components import (
    remove_newlines,
    DocumentChunker,
    VectorStoreUpserter
)

logger = logging.getLogger(__name__)


SUMMARIZE_PROMPT = PromptTemplate.from_template(
    """Write a concise summary (about 300 words) of the following:

"{context}"

CONCISE SUMMARY:"""
)

SUMMARIZE_PROMPT_SHORT = PromptTemplate.from_template(
    """Write a concise summary (max 200 words) of the following:

"{context}"

CONCISE SUMMARY:"""
)


class ABMRouterV1SI(AbstractModel):
    instance_id = "ABM-router-v1-si"
    """AgentBasedModel-Router-V1-SearchIndex"""

    def __init__(
            self,
            vectorstore: VectorStore,
            llm: Optional[BaseLanguageModel] = None,
            llm_token_limit: Optional[int] = None,
            chunk_size: int = 1500,
            chunk_overlap: int = 50,
            chunk_size_si: int = 40_000,
            chunk_overlap_si: int = 2000,
            k: int = 5
    ) -> None:
        super().__init__()
        self.vectorstore = vectorstore
        self.llm = llm
        self.llm_token_limit = llm_token_limit
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.chunk_size_si = chunk_size_si
        self.chunk_overlap_si = chunk_overlap_si
        self.k = k

    def index(self,
              documents: List[Document],
              *,
              metadata: dict = None,
              namespace: str = None,
              ) -> None:
        if self.llm is None:
            self.llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo-16k")
            self.llm_token_limit = 16000
        else:
            if not self.llm_token_limit:
                raise ValueError("llm_token_limit must be set if llm is provided")
        if self.llm_token_limit * 4 < (self.chunk_size_si + 4000):
            # buffer of 4000 tokens (~1000 characters)
            logger.warning(
                "`llm_token_limit` is close to the `chunk_size_si`, this may cause "
                "issues with summarizing chunks. Decrease `chunk_size_si`.")
        if metadata is not None:
            [document.metadata.update(metadata) for document in documents]

        document_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap)
        summary_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size_si, chunk_overlap=self.chunk_overlap_si)
        upsert_documents = VectorStoreUpserter(self.vectorstore, namespace=namespace)

        # stuff chain: if the document is small enough, summarize it directly
        stuff_chain = build_stuff_chain(self.llm, SUMMARIZE_PROMPT)

        # map chain: split the doc into chunks, summarize each
        stuff_chain_mapping = build_stuff_chain(self.llm, SUMMARIZE_PROMPT_SHORT)
        map_chain = build_map_chain(summary_splitter, stuff_chain_mapping)

        # reduce chain: combine the summaries of the chunks
        reduce_chain = build_reduce_chain(stuff_chain)

        # map-reduce chain: split doc into chunks, summarize each, combine the summaries
        map_reduce_chain = (map_chain | reduce_chain).with_config(
            {"run_name": "Map Reduce Chain"})

        def _route(document: Document):
            encoding = tiktoken.encoding_for_model(self.llm.model_name)
            num_tokens = len(encoding.encode(document.page_content))
            if num_tokens <= self.llm_token_limit:
                return stuff_chain
            else:
                return map_reduce_chain

        chunk_chain = (
            remove_newlines
            | DocumentChunker(document_splitter)
            | upsert_documents
        )

        summarize_chain = (
            remove_newlines
            | RunnableLambda(_route)
            | upsert_documents
        )

        parallel_chain = RunnableParallel(
            chunking=chunk_chain, summarizing=summarize_chain)

        chain = self._configure_chain(parallel_chain, user_id=namespace)
        return chain.batch(documents)

    def invoke(self,
               input_data: str,
               *,
               filters: dict = {},
               namespace: str = None,
               ) -> List[Document]:

        chain = ""
        chain = self._configure_chain(chain, user_id=namespace)
        return chain.invoke(input_data)
