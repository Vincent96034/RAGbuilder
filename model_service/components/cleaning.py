from typing import List

from langchain.schema.document import Document
from langchain_core.runnables import chain


@chain
def remove_newlines(document: Document) -> List[Document]:
    """Simple document cleaner. Removes all newlines from the page content.

    Args:
        documents (List[Document]): A list of documents.

    Returns:
        List[Document]: The cleaned documents.
    """
    document.page_content.replace('\n', '')
    return document
