# RAGBuilder

RAGBuilder is a platform designed to build Retrieval Augmented Generation (RAG) applications. It leverages FastAPI for serving models as APIs and LangChain for defining workflows and models. This project can be used to augment LLMs with retrieved data, e.g. creating a custom GPT with access to personal / internal data.


## Table of Contents

1. [Overview](#overview)
2. [Project Structure](#project-structure)
3. [Installation](#installation)
4. [Usage](#usage)
5. [Models](#models)
6. [Customization](#customization)
7. [Contributing](#contributing)
8. [Documentation and Support](#documentation-and-support)

## Overview

RAGBuilder aims to provide a flexible and scalable platform for building and deploying RAG models. It integrates FastAPI for creating robust and efficient APIs and utilizes LangChain for managing model workflows. RAGBuilder supports various model types, from simple RAG architectures to complex agent-based models.


## Project Structure

```
backend
├── app
│   ├── config 
│   ├── db
│   ├── file_handler
│   ├── ops
│   ├── routes
│   ├── schemas
│   ├── utils
│   ├── __init__.py
│   └── main.py
├── model_service
│   ├── components
│   ├── core
│   ├── models
│   ├── prompts
│   ├── vectorstores
│   ├── __init__.py
│   └── README.md
├── tests
└── requirements.txt
```

- **app**: Contains the FastAPI application, including configuration, database models (using Firebase), file handlers, operations, routes, schemas, and utilities.
- **model_service**: Contains the model definitions and services. Models are built on top of LangChain's services and include various RAG implementations and agent-based models.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/RAGBuilder.git
   cd RAGBuilder
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Start the FastAPI server:
   ```bash
   uvicorn app.main:app --reload
   ```

4. Note: The project is connected to a Google Firebase project. Users need to provide the necessary database schemas and credentials to run the webserver. The `model_service` can be used independently of the FastAPI app.

## Usage

Here's an example of how to use the `model_service`:

```python
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings
from model_service.models import DefaultRAG

# Initialize the VectorStore
vectorstore = PineconeVectorStore(
    index_name="ragbuilder", 
    embedding=OpenAIEmbeddings()
)
model = DefaultRAG(vectorstore)

# Sample documents
documents = [
    Document(page_content="The capital of France is Paris", metadata={"user_id": "test", "project_id": "test-project", "page": "1"}),
    Document(page_content="The capital of Germany is Berlin", metadata={"user_id": "test", "project_id": "test-project2", "page": "2"}),
    Document(page_content="The capital of Spain is Madrid", metadata={"user_id": "test", "project_id": "test-project", "page": "1"})
]

# Index the documents
model.index(documents, namespace="test_user_id")

# Retrieve similar documents
model.invoke(
    input_data="I love the city Rome in Italy.",
    namespace="test_user_id",
    filters={"project_id": "test-project"}
)
```

## Models
Currently, the following models are implemented. More might be added in the future:

#### RAGVanillaV1
A vanilla RAG model that provides basic RAG capabilities. This model is useful for applications that need quick and simple retrieval-augmented generation without additional processing or filtering.

#### RAGRerankV1CH
A RAG model with reranking capabilities using the Cohere API. This model is ideal for scenarios where the quality of the retrieved documents needs to be enhanced by reranking them based on their relevance to the query.

#### ABMRouterV1SI
An agent-based model (ABM) using a router agent and a summary index. This model creates a secondary index of summarized documents, which can be useful for applications that require more concise information retrieval, such as summarizing large documents or datasets.

#### ABMReActV1SI
A ReAct model that also uses the summary index. This model is still in development but aims to combine reactive agents with summarized indexing to provide dynamic and context-aware information retrieval.

## Customization

Users can create custom models by inheriting from `model_service.models._abstractmodel.AbstractModel` and implementing the required methods (`index`, `invoke`, and optionally `deindex`).

## Contributing

While the project is not primarily designed for contributions, new ideas and models are appreciated.
