<p><a target="_blank" href="https://app.eraser.io/workspace/XGnGgYJWgaJ7nOJ20uOk" id="edit-in-eraser-github-link"><img alt="Edit in Eraser" src="https://firebasestorage.googleapis.com/v0/b/second-petal-295822.appspot.com/o/images%2Fgithub%2FOpen%20in%20Eraser.svg?alt=media&amp;token=968381c8-a7e7-472a-8ed6-4a6626da5501"></a></p>

# Overview
Models define a workflow or sequence of steps for a task. This could be a simple RAG Architecture, but also allows for more complex processes that include multiple Agents communicating with each other. All models are built on-top of `LangChain` 's services - therefore the usage of models also tries to be similar to `LangChain` 's functionality.

Each `Model` has to implement 2 methods: 

- `invoke`  defines the workflow steps for the model. This is usually a form of LangChain `chain`, but can have other custom functionalities.
- `index [optional]` defines the steps that are needed to for example upsert data into a vector database for later retrieval or similar. This is an optional method.
Each implementation should allow for tracing using LangSmith.

```
class AbstractModel(ABC):

    def index(self, documents: List[Document]):
        """Define indexing for the model."""
        ...
        
    def invoke(self, input, **kwargs):
        """Define invoking the model flow."""
        ...
```
# List of Models
## Default RAG Model: `default-rag` 
The simples of all models, implementing simple Retrieval Augmented Generation (RAG) functionality.

![default-rag](/.eraser/XGnGgYJWgaJ7nOJ20uOk___uhYyRb2BDJfubX2UCW5pdkwIUaj2___---figure---kC3E4kepACrL4GCHeRew7---figure---PTamuutIJLUpPCkaFPwPXw.png "default-rag")






<!--- Eraser file: https://app.eraser.io/workspace/XGnGgYJWgaJ7nOJ20uOk --->