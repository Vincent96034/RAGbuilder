from typing import Any, List, Optional
from langchain_pinecone import PineconeVectorStore


class PineconeVectorStoreWrapper(PineconeVectorStore):
    """Wrapper for PineconeVectorStore to allow for deletion by filter."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def delete(
        self,
        ids: Optional[List[str]] = None,
        delete_all: Optional[bool] = None,
        namespace: Optional[str] = None,
        filter: Optional[dict] = None,
        **kwargs: Any,
    ) -> None:
        """Delete by vector IDs or filter. This is a workaround to the current Pinecone
        API limitation of deleting by filter only for paying users.

        Args:
            ids: List of ids to delete.
            filter: Dictionary of conditions to filter vectors to delete.
        """
        if namespace is None:
            namespace = self._namespace

        if delete_all:
            self._index.delete(delete_all=True, namespace=namespace, **kwargs)
        elif ids is not None:
            chunk_size = 1000
            for i in range(0, len(ids), chunk_size):
                chunk = ids[i : i + chunk_size]
                self._index.delete(ids=chunk, namespace=namespace, **kwargs)
        elif filter is not None:
            results = self._index.query(
                vector=self._embedding.embed_query(""),
                top_k=1000,
                include_metadata=True,
                namespace=namespace,
                filter=filter,)
            matches = results["matches"]
            ids = [match["id"] for match in matches]
            if len(ids) > 0:
                self._index.delete(ids=ids, namespace=namespace, **kwargs)
        else:
            raise ValueError("Either ids, delete_all, or filter must be provided.")

        return None

    
    
