import os

from langchain_openai import OpenAIEmbeddings

from model_service.vectorstores import PineconeVectorStoreWrapper

from model_service.models._abstractmodel import AbstractModel
from model_service.models import (
    RAGVanillaV1,
    RAGRerankV1CH,
    ABMRouterV1SI,
    ABMReActV1SI
)


def get_vectorstore():
    index_name = os.getenv("PINECONE_INDEX_NAME")
    if not index_name:
        raise ValueError("PINECONE_INDEX_NAME is not set")

    vs = PineconeVectorStoreWrapper(index_name=index_name, embedding=OpenAIEmbeddings())
    return vs


def model_factory(modeltype_id: str, model_config: dict) -> AbstractModel:

    model_repo = {
        "RAG-vanilla-v1": RAGVanillaV1,
        "RAG-rerank-v1-ch": RAGRerankV1CH,
        "ABM-router-v1-si": ABMRouterV1SI,
        "ABM-react-v1-si": ABMReActV1SI
    }

    if modeltype_id not in model_repo:
        raise ValueError(f"Model {modeltype_id} not found.")

    model = model_repo[modeltype_id]
    vectorstore = get_vectorstore()
    return model(vectorstore=vectorstore, **model_config)
