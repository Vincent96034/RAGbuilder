from typing import List

from langchain_core.runnables import chain
from langchain.schema.document import Document


@chain
def simple_doc_cleaner(documents: List[Document]) -> List[Document]:
    """Simple document cleaner. Removes all newlines from the page content.

    Args:
        documents (List[Document]): A list of documents.

    Returns:
        List[Document]: The cleaned documents.
    """
    for doc in documents:
        doc.page_content = doc.page_content.replace('\n', '')
    return documents
