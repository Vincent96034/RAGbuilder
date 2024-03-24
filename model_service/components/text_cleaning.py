from typing import List
from langchain.schema.document import Document


def simple_doc_cleaner(documents: List[Document]) -> List[Document]:
    for doc in documents:
        doc.page_content = doc.page_content.replace('\n', '')
    return documents