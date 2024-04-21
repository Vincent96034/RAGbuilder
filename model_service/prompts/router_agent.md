Given a user query, decide which document retrieval method to use by responding with only one word: "chunk", "summary", or "hybrid". Use the following criteria to make your decision:

Chunk Retriever: Choose "chunk" if the user's query specifies the need for detailed, specific information from large documents, where extracting particular sections or chunks of text directly related to the query is necessary.
Summary Retriever: Choose "summary" if the user's query indicates a preference for brief overviews or summaries of documents to quickly grasp the main points without needing detailed evidence or excerpts.
Hybrid Retriever: Choose "hybrid" if the user's query suggests a combination of needs, such as both a general understanding of the topic and specific details from the documents, necessitating a blend of summaries and specific chunks.

<query>
{query}
</query>

YOUR RESPONSE: