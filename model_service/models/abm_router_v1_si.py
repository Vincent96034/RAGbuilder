import logging
from typing import List, Optional

import tiktoken
from langchain_openai import ChatOpenAI
from langchain.schema.document import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.vectorstores import VectorStore
from langchain_core.language_models import BaseLanguageModel
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
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

SUMMARIZE_PROMPT = PromptTemplate.from_file("model_service/prompts/summarize_300.md")
SUMMARIZE_PROMPT_SHORT = PromptTemplate.from_file(
    "model_service/prompts/summarize_200.md")
ROUTE_AGENT_PROMPT = PromptTemplate.from_file("model_service/prompts/router_agent.md")


class ABMRouterV1SI(AbstractModel):
    """The AgentBasedModel-Router-V1-SearchIndex (ABMRouterV1SI) uses a Router Agent to
    decide in which Vector-Store to search in. Documents indexed are summarized. When
    invoked, the agent decides whether to search for the query in the chunked documents,
    the summaries, or both.

    Initialization Parameters:
        vectorstore (VectorStore): An instance of VectorStore that this model will use for
            storing and retrieving document vectors.
        index_llm (Optional[BaseLanguageModel], optional): A language model used for
            indexing. Defaults to None, which auto-selects a default language model
            configuration.
        invoke_llm (Optional[BaseLanguageModel], optional): A language model used for
            invoking or querying. Defaults to None, automatically selecting a default
            model when needed.
        llm_token_limit (Optional[int], optional): The maximum number of tokens that the
            language model can process in one go. Necessary if a language model is
            provided. Defaults to None.
        chunk_size (int, optional): The size of text chunks, in characters, that documents
            should be split into for processing. Defaults to 1500.
        chunk_overlap (int, optional): The number of characters that consecutive chunks
            should overlap to maintain context. Defaults to 50.
        chunk_size_si (int, optional): Similar to chunk_size, but specifically for search
            indexing. Defaults to 40,000.
        chunk_overlap_si (int, optional): The overlap for chunks specifically in search
            indexing. Defaults to 2000.
        k (int, optional): The number of documents to retrieve during the invoke process.
            Defaults to 5.

    Usage:
    ```python
    # Initialize the VectorStore and models
    vectorstore = VectorStoreImplementation()
    model = ABMRouterV1SI(vectorstore)
    documents = List[Document]

    # Index documents
    model.index(documents, namespace="your_namespace")

    # Retrieve and process documents based on input query
    results = model.invoke("Your query here.", namespace="your_namespace")
    ```
    """
    instance_id = "ABM-router-v1-si"

    def __init__(
            self,
            vectorstore: VectorStore,
            index_llm: Optional[BaseLanguageModel] = None,
            invoke_llm: Optional[BaseLanguageModel] = None,
            llm_token_limit: Optional[int] = None,
            chunk_size: int = 1500,
            chunk_overlap: int = 50,
            chunk_size_si: int = 40_000,
            chunk_overlap_si: int = 2000,
            k: int = 5
    ) -> None:
        super().__init__()
        self.vectorstore = vectorstore
        self.index_llm = index_llm
        self.invoke_llm = invoke_llm
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
        """Indexes documents by processing them into chunks and summarizing each chunk for
        efficient retrieval. If metadata is provided, it updates the metadata for each
        document before indexing.

        Parameters:
            documents (List[Document]): A list of documents to be indexed.
            metadata (dict, optional): Metadata to update in each document before indexing.
                Defaults to None.
            namespace (str, optional): A namespace to categorize and retrieve the indexed
                documents. Useful for multi-tenant environments. Defaults to None.
        """
        if self.index_llm is None:
            self.index_llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo-16k")
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
        for document in documents:
            document.metadata["is_summary"] = False

        document_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap)
        summary_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size_si, chunk_overlap=self.chunk_overlap_si)
        upsert_documents = VectorStoreUpserter(self.vectorstore, namespace=namespace)

        # stuff chain: if the document is small enough, summarize it directly
        stuff_chain = build_stuff_chain(self.index_llm, SUMMARIZE_PROMPT)

        # map chain: split the doc into chunks, summarize each
        stuff_chain_mapping = build_stuff_chain(self.index_llm, SUMMARIZE_PROMPT_SHORT)
        map_chain = build_map_chain(summary_splitter, stuff_chain_mapping)

        # reduce chain: combine the summaries of the chunks
        reduce_chain = build_reduce_chain(stuff_chain)

        # map-reduce chain: split doc into chunks, summarize each, combine the summaries
        map_reduce_chain = (map_chain | reduce_chain).with_config(
            {"run_name": "Map Reduce Chain"})

        def _route(document: Document):
            encoding = tiktoken.encoding_for_model(self.index_llm.model_name)
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
        """Invokes the model to retrieve documents based on the input data. A Router Agent
        decides whether to search for document chunks, the summaries, or both.

        Parameters:
            input_data (str): The input user query.
            filters (dict, optional): Additional filters to apply during retrieval.
            namespace (str, optional): The namespace from which to retrieve documents.
                Defaults to None.

        Returns:
            List[Document]: A list of documents that match the query and filters provided.
        """
        search_kwargs = {"k": self.k, "filter": filters}
        if namespace:
            search_kwargs["namespace"] = namespace
        if self.invoke_llm is None:
            self.invoke_llm = ChatOpenAI(temperature=0, model_name="gpt-4-turbo")

        search_kwargs['filter']['is_summary'] = False
        chunk_retriever = self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs=search_kwargs)

        search_kwargs['filter']['is_summary'] = True
        summary_retriever = self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs=search_kwargs)

        hybrid_retriever = RunnableParallel(
            chunk_search=chunk_retriever,
            summary_search=summary_retriever)

        def _route(info):
            if "summary" in info["retriever"].lower():
                retr = summary_retriever
            elif "hybrid" in info["retriever"].lower():
                retr = hybrid_retriever
            else:
                retr = chunk_retriever

            query = info["query"]
            return retr.invoke(query)

        router_agent = (
            ROUTE_AGENT_PROMPT
            | self.invoke_llm
            | StrOutputParser()
        )

        chain = (
            {"retriever": router_agent, "query": lambda x: x["query"]}
            | RunnableLambda(_route)
        )
        chain = self._configure_chain(chain, user_id=namespace)
        return chain.invoke({"query": input_data})
