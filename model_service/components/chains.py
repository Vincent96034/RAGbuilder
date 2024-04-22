from langchain.schema.document import Document
from langchain_core.runnables import (
    Runnable,
    RunnableParallel,
    RunnableLambda,
    RunnablePassthrough
)

from model_service.components import (
    DocumentChunker,
    BatchChainRunner
)


def build_stuff_chain(llm: Runnable, prompt, sleep_time: float = 0.1) -> RunnableParallel:
    """Build a chain that takes a `Document` and a prompt and returns a summary of the
    document as a `Document`.
    """
    stuff_chain = (
        RunnableParallel(
            summary=prompt | llm,
            document=RunnablePassthrough(),
        )
        | RunnableLambda(lambda out: _llm_to_doc_parser(out))
    ).with_config({"run_name": "Stuff Chain"})
    return stuff_chain


def build_map_chain(splitter, stuff_chain):
    """Build a chain that takes a (large) document, splits it into multiple chunks and
    summarizes each chunk. The summaries are then returned as a list of `Document`s.
    """
    batch_stuff_chain = BatchChainRunner(stuff_chain)
    map_chain = (
        DocumentChunker(splitter)
        | RunnableLambda(batch_stuff_chain)
    ).with_config({"run_name": "Map Chain"})
    return map_chain


def build_reduce_chain(stuff_chain):
    """Build a chain that takes a list of `Document`s, summarises them and returns a
    single `Document`.
    """
    reduce_chain = (
        RunnableLambda(lambda docs: _merge_summaries(docs))
        | stuff_chain
    ).with_config({"run_name": "Reduce Chain"})
    return reduce_chain


def _merge_summaries(docs):
    """Merge the summaries of multiple `Document`s into a single `Document`."""
    print("_merge_summaries", docs)
    page_content = " ".join([doc.page_content for doc in docs])
    doc = Document(page_content=page_content, metadata=docs[0].metadata.copy())
    doc.metadata["is_summary"] = True
    return doc


def _llm_to_doc_parser(out):
    """Parse the output of a language model into a `Document`."""
    doc = Document(
        page_content=out["summary"].content,
        metadata=out["document"].metadata.copy())
    doc.metadata["is_summary"] = True
    return doc
