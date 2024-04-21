import logging
from functools import partial
from typing import List, Optional

from langchain_core.vectorstores import VectorStore
from langchain_core.language_models import BaseLanguageModel
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import Runnable  # RunnableParallel

from langchain.agents import AgentExecutor, create_react_agent
from langchain.schema.document import Document
from langchain.tools.render import render_text_description_and_args
from langchain.tools.retriever import create_retriever_tool
from langchain.tools import Tool
from langchain_core.prompts import BasePromptTemplate, format_document

from langchain_openai import ChatOpenAI

from model_service.models.abm_router_v1_si import ABMRouterV1SI
from model_service.core.prompts import from_file


logger = logging.getLogger(__name__)

REACT_PROMPT = PromptTemplate.from_file("model_service/prompts/react.md")
CHUNK_RETR_DESCR = from_file("model_service/prompts/descriptions/chunk_retriever.md")
SUMMARY_RETR_DESCR = from_file("model_service/prompts/descriptions/summary_retriever.md")
HYBRID_RETR_DESCR = from_file("model_service/prompts/descriptions/hybrid_retriever.md")


class RunnableInput(BaseModel):
    """Input to the retriever."""
    # in this case, the input is for the hybrid retriever
    query: str = Field(description="query to look up in retriever")


class ABMReActV1SI(ABMRouterV1SI):
    instance_id = "ABM-react-v1-si"

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
        super().__init__(
            vectorstore=vectorstore,
            index_llm=index_llm,
            invoke_llm=invoke_llm,
            llm_token_limit=llm_token_limit,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            chunk_size_si=chunk_size_si,
            chunk_overlap_si=chunk_overlap_si,
            k=k)

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
        super().index(documents, metadata=metadata, namespace=namespace)

    def invoke(self,
               input_data: str,
               *,
               filters: dict = {},
               namespace: str = None,
               ) -> List[Document]:
        search_kwargs = {"k": self.k, "filter": filters}
        if namespace:
            search_kwargs["namespace"] = namespace
        if self.invoke_llm is None:
            self.invoke_llm = ChatOpenAI(temperature=0, model_name="gpt-4-turbo")

        search_kwargs['filter']['is_summary'] = False
        chunk_retriever = self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs=search_kwargs)
        chunk_retriever_tool = create_retriever_tool(
            retriever=chunk_retriever,
            name="Chunk Retriever",
            description=CHUNK_RETR_DESCR,
        )

        search_kwargs['filter']['is_summary'] = True
        summary_retriever = self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs=search_kwargs)
        summary_retriever_tool = create_retriever_tool(
            retriever=summary_retriever,
            name="Summary Retriever",
            description=SUMMARY_RETR_DESCR,
        )

        # todo: fix hybrid retriever: trace_id: b1138889-0f5c-48e9-bf94-b23de7d168ec
        # hybrid_retriever = RunnableParallel(
        #     chunk_search=chunk_retriever,
        #     summary_search=summary_retriever)
        # hybrid_retriever_tool = _create_runnable_tool(
        #     runnable=hybrid_retriever,
        #     name="Hybrid Retriever",
        #     description=HYBRID_RETR_DESCR,
        # )

        tools = [chunk_retriever_tool, summary_retriever_tool]
        agent = create_react_agent(
            llm=self.invoke_llm,
            tools=tools,
            prompt=REACT_PROMPT,
            tools_renderer=render_text_description_and_args
        )
        chain = AgentExecutor(agent=agent, tools=tools, verbose=True)
        chain = self._configure_chain(chain, user_id=namespace)
        return chain.invoke({"input": input_data})


def _run_runnable(
    query: str,
    runnable: Runnable,
    document_prompt: BasePromptTemplate,
    document_separator: str
) -> str:
    docs = runnable.invoke(query)
    return document_separator.join(
        format_document(doc, document_prompt) for doc in docs
    )


async def _arun_runnable(
    query: str,
    runnable: Runnable,
    document_prompt: BasePromptTemplate,
    document_separator: str
) -> str:
    docs = await runnable.invoke(query)
    return document_separator.join(
        format_document(doc, document_prompt) for doc in docs
    )


def _create_runnable_tool(runnable, name, description, document_prompt=None, document_separator="\n\n"):
    func = partial(
        _run_runnable,
        runnable=runnable,
        document_prompt=document_prompt,
        document_separator=document_separator,
    )
    afunc = partial(
        _arun_runnable,
        runnable=runnable,
        document_prompt=document_prompt,
        document_separator=document_separator,
    )
    return Tool(
        name=name,
        description=description,
        func=func,
        coroutine=afunc,
        args_schema=RunnableInput,
    )
