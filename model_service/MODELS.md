<p><a target="_blank" href="https://app.eraser.io/workspace/XGnGgYJWgaJ7nOJ20uOk" id="edit-in-eraser-github-link"><img alt="Edit in Eraser" src="https://firebasestorage.googleapis.com/v0/b/second-petal-295822.appspot.com/o/images%2Fgithub%2FOpen%20in%20Eraser.svg?alt=media&amp;token=968381c8-a7e7-472a-8ed6-4a6626da5501"></a></p>

# Overview
Models define a workflow or sequence of steps for a task. This could be a simple RAG Architecture, but also allows for more complex processes that include multiple Agents communicating with each other. All models are built on-top of `LangChain` 's services - therefore the usage of models also tries to be similar to `LangChain` 's functionality.

Each `Model` has to implement 2 methods: 

- `invoke`  defines the workflow steps for the model. This is usually a form of LangChain `chain`, but can have other custom functionalities.
- `index [pseudo-optional]` defines the steps that are needed to for example upsert data into a vector database for later retrieval or similar. This is an optional method.
Each implementation should allow for tracing using LangSmith.

```python
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

**Usage:**
```python
from langchain_openai import OpenAIEmbeddings
from langchain.schema.document import Document
from langchain_pinecone import PineconeVectorStore 
from model_service.models import DefaultRAG

# create sample documents
docs = [
    Document(page_content="The capital of France is Paris",
        metadata={"user_id": "vincent-test", "project_id": "test-project", "page": "1"}),
    Document(page_content="The capital of Germany is Berlin",
        metadata={"user_id": "vincent-test", "project_id": "test-project2", "page": "2"}),
    Document(page_content="The capital of Spain is Madrid",
        metadata={"user_id": "vincent-test", "project_id": "test-project", "page": "1"}),
]

# initialize vectorstore and model
vectorstore = PineconeVectorStore(index_name="ragbuilder", embedding=OpenAIEmbeddings())
model = DefaultRAG(vectorstore)

# index documents: this uploads the documents under the namespace 'vincent-test' to pinecone
model.index(docs, namespace="vincent-test")

# invoke model: this makes a similarity search for the specified query in the 'vincent-test'
# namespace, filtering by project_id 'test-project'. This will return only 2 of the documents
# because the 2nd document is in 'test-project2'.
# Note: the optional parameter 'user_id' is used to add metadata to the LangSmith trace.
model.invoke(
    input_data="I love the city Rome in Italy.",
    namespace="vincent-test",
    filters={"project_id": "test-project"},
    user_id="vincent-test",
)
```





<!--- Eraser file: https://app.eraser.io/workspace/XGnGgYJWgaJ7nOJ20uOk --->