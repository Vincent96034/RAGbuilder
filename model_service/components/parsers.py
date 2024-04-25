from typing import List

from langchain.schema.document import Document


def llm_to_doc_parser(out):
    """Parse the output of a language model into a `Document`."""
    doc = Document(
        page_content=out["summary"].content,
        metadata=out["document"].metadata.copy())
    doc.metadata["is_summary"] = True
    return doc


def doc_output_parser(docs: Document | List[Document]) -> str:
    """Parse the output of a language model into a `Document`."""
    ret_str = ""
    if isinstance(docs, Document):
        docs = [docs]
    for doc in docs:
        # todo: dont hardcode this
        src = doc.metadata.get("file_title", "N/A")
        ret_str += f"{doc.page_content}\nSOURCE: {src}\n---\n\n"
    return ret_str
