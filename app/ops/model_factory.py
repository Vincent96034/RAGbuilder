import os

from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore

from model_service.models import AbstractModel, DefaultRAG


def get_vectorstore():
    index_name = os.getenv("PINECONE_INDEX_NAME")
    if not index_name:
        raise ValueError("PINECONE_INDEX_NAME is not set")
    
    vs = PineconeVectorStore(index_name=index_name, embedding=OpenAIEmbeddings())
    return vs


def model_factory(modeltype_id: str, model_config: dict) -> AbstractModel:

    model_repo = {
        "default-rag": DefaultRAG
    }

    if modeltype_id not in model_repo:
        raise ValueError(f"Model {modeltype_id} not found.")

    model = model_repo[modeltype_id]
    vectorstore = get_vectorstore()
    return model(vectorstore=vectorstore, **model_config)
