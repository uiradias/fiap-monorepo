"""ChromaDB vector store for patient record storage and retrieval."""

from typing import List, Optional, Dict, Any
import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

from config.settings import Settings


class VectorStore:
    """
    Repository for patient records using ChromaDB.

    This class implements the Repository pattern to abstract
    vector database operations from the rest of the application.
    """

    def __init__(self, settings: Settings):
        """
        Initialize the vector store.

        Args:
            settings: Application settings containing ChromaDB config.
        """
        self._settings = settings
        self._embeddings = OpenAIEmbeddings(api_key=settings.openai_api_key)

        # Initialize ChromaDB with persistent storage
        self._client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )

        self._collection_name = settings.collection_name
        self._vectorstore: Optional[Chroma] = None

    def initialize(self) -> None:
        """Initialize or load the vector store collection."""
        self._vectorstore = Chroma(
            client=self._client,
            collection_name=self._collection_name,
            embedding_function=self._embeddings,
        )

    def add_documents(
        self,
        texts: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str],
    ) -> None:
        """
        Add documents to the vector store.

        Args:
            texts: List of document texts to embed and store.
            metadatas: List of metadata dicts for each document.
            ids: List of unique IDs for each document.
        """
        if self._vectorstore is None:
            self.initialize()

        self._vectorstore.add_texts(
            texts=texts,
            metadatas=metadatas,
            ids=ids,
        )

    def search(
        self,
        query: str,
        k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents.

        Args:
            query: The search query.
            k: Number of results to return.
            filter_metadata: Optional metadata filter.

        Returns:
            List of matching documents with content and metadata.
        """
        if self._vectorstore is None:
            self.initialize()

        if filter_metadata:
            results = self._vectorstore.similarity_search(
                query=query,
                k=k,
                filter=filter_metadata,
            )
        else:
            results = self._vectorstore.similarity_search(
                query=query,
                k=k,
            )

        return [
            {
                "content": doc.page_content,
                "metadata": doc.metadata,
            }
            for doc in results
        ]

    def search_by_patient(
        self,
        query: str,
        patient_identifier: str,
        k: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Search for documents related to a specific patient.

        Args:
            query: The search query.
            patient_identifier: Patient name or ID.
            k: Number of results to return.

        Returns:
            List of matching documents.
        """
        if self._vectorstore is None:
            self.initialize()

        # Search with patient filter
        # Try matching by ID or name
        results = self._vectorstore.similarity_search(
            query=f"{patient_identifier} {query}",
            k=k,
        )

        # Filter results that match the patient
        filtered = []
        patient_lower = patient_identifier.lower()

        for doc in results:
            metadata = doc.metadata
            if (
                metadata.get("patient_id", "").lower() == patient_lower
                or patient_lower in metadata.get("patient_name", "").lower()
                or patient_lower in doc.page_content.lower()
            ):
                filtered.append(
                    {
                        "content": doc.page_content,
                        "metadata": metadata,
                    }
                )

        return filtered if filtered else [
            {"content": doc.page_content, "metadata": doc.metadata}
            for doc in results[:k]
        ]

    def clear_collection(self) -> None:
        """Clear all documents from the collection."""
        try:
            self._client.delete_collection(self._collection_name)
        except ValueError:
            pass  # Collection doesn't exist
        self._vectorstore = None
        self.initialize()

    def get_collection_count(self) -> int:
        """Get the number of documents in the collection."""
        if self._vectorstore is None:
            self.initialize()

        collection = self._client.get_collection(self._collection_name)
        return collection.count()
