import lmstudio as lms
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from langchain_community.document_loaders import DirectoryLoader, UnstructuredFileLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


class VectorStore:
    MARKDOWN_SEPARATORS = [
        "\n#{1,6} ",
        "```\n",
        "\n\\*\\*\\*+\n",
        "\n---+\n",
        "\n___+\n",
        "\n\n",
        "\n",
        " ",
        "",
    ]

    def __init__(self, collection_name: str, vector_size: int, qdrant_url: str, embed_model_name: str):
        self.collection_name = collection_name
        self.vector_size = vector_size
        self.client = QdrantClient(url=qdrant_url)
        self.embed_model = lms.embedding_model(embed_model_name)

    def load_and_index(self, pdf_dir: str, chunk_size: int = 1200, chunk_overlap: int = 200):
        docs = self._load_docs(pdf_dir)
        splits = self._split_docs(docs, chunk_size, chunk_overlap)
        self._create_collection_if_needed()
        self._upsert(splits)
        print("Lưu vào Qdrant thành công!")

    def embed(self, text: str):
        return self.embed_model.embed(text)

    def _load_docs(self, pdf_dir: str):
        loader = DirectoryLoader(
            path=pdf_dir,
            glob="**/*.pdf",
            loader_cls=UnstructuredFileLoader,
            show_progress=True,
            use_multithreading=True,
        )
        return loader.load()

    def _split_docs(self, docs, chunk_size: int, chunk_overlap: int):
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            add_start_index=True,
            strip_whitespace=True,
            separators=self.MARKDOWN_SEPARATORS,
        )
        return splitter.split_documents(docs)

    def _create_collection_if_needed(self):
        if not self.client.collection_exists(self.collection_name):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size, distance=Distance.COSINE),
            )

    def _upsert(self, splits, batch_size: int = 100):
        points = [
            PointStruct(
                id=i,
                vector=self.embed_model.embed(doc.page_content),
                payload={
                    "text": doc.page_content,
                    "source": doc.metadata.get("source", "unknown"),
                    "page": doc.metadata.get("page", 0),
                },
            )
            for i, doc in enumerate(splits)
        ]

        for start in range(0, len(points), batch_size):
            batch = points[start: start + batch_size]
            self.client.upsert(
                collection_name=self.collection_name, points=batch)
            print(
                f"  Đã upsert {min(start + batch_size, len(points))}/{len(points)} points")
