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
    RunnablePassthrough
)

from model_service.models._abstractmodel import AbstractModel
from model_service.components import (
    remove_newlines,
    DocumentChunker,
    VectorStoreUpserter,
    BatchChainRunner
)

logger = logging.getLogger(__name__)

summarize_prompt_template = """Write a concise summary of the following:

"{context}"

CONCISE SUMMARY:"""
summarize_prompt = PromptTemplate.from_template(summarize_prompt_template)


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

        def _llm_to_doc_parser(out):
            return Document(
                page_content=out["summary"].content,
                metadata=out["document"].metadata.copy())

        def _merge_summaries(docs):
            page_content = " ".join([doc.page_content for doc in docs])
            doc = Document(page_content=page_content, metadata=docs[0].metadata.copy())
            doc.metadata["is_summary"] = True
            return doc

        # stuff chain: if the document is small enough, summarize it directly
        stuff_chain = (
            RunnableParallel(
                summary=summarize_prompt | self.llm,
                document=RunnablePassthrough(),
            )
            | RunnableLambda(lambda out: _llm_to_doc_parser(out))
        )

        # map chain: split the document into chunks, summarize each chunk
        batch_stuff_chain = BatchChainRunner(stuff_chain)
        print(type(batch_stuff_chain))

        map_chain = (
            DocumentChunker(summary_splitter)
            | RunnableLambda(batch_stuff_chain)
        ).with_config({"run_name": "Map Chain"})

        # reduce chain: combine the summaries of the chunks
        reduce_chain = (
            RunnableLambda(lambda docs: _merge_summaries(docs))
            | stuff_chain
        ).with_config({"run_name": "Reduce Chain"})

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
