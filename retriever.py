from embedder import VectorStore


class Retriever:
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store

    def retrieve(self, query: str, k: int = 5, score_threshold: float = 0.2) -> str:
        query_vector = self.vector_store.embed(query)

        results = self.vector_store.client.query_points(
            collection_name=self.vector_store.collection_name,
            query=query_vector,
            limit=k,
            score_threshold=score_threshold,
        ).points

        if not results:
            return ""

        context_parts = []
        for hit in results:
            payload = hit.payload
            source = payload.get("source", "unknown")
            page = payload.get("page", "?")
            text = payload.get("text", "")
            context_parts.append(f"[source:{source} | page:{page}]\n{text}")

        return "\n\n---\n\n".join(context_parts)
