import os
# from qdrant_client import QdrantClient # MOVED TO _initialize
# from qdrant_client.http import models # MOVED TO _initialize
# from sentence_transformers import SentenceTransformer # MOVED TO _initialize
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import logging

logger = logging.getLogger(__name__)

class RagService:
    _instance = None
    _model = None
    _client = None
    COLLECTION_NAME = "disease_solutions"
    VECTOR_SIZE = 384  # size for all-MiniLM-L6-v2

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RagService, cls).__new__(cls)
        return cls._instance

    def _initialize(self):
        if self.__class__._client is None:
            try:
                from qdrant_client import QdrantClient
                from qdrant_client.http import models
                from sentence_transformers import SentenceTransformer
                
                # Initialize Qdrant (using local storage for simplicity)
                db_path = os.path.join(settings.BASE_DIR, "vectordb")
                if not os.path.exists(db_path):
                    os.makedirs(db_path)
                
                logger.info(f"Initializing Qdrant at: {os.path.abspath(db_path)}")
                
                # Check for stale lock file and log warning if it exists
                lock_path = os.path.join(db_path, ".lock")
                if os.path.exists(lock_path):
                    logger.warning(f"Qdrant lock file detected at {lock_path}. This may cause initialization to hang.")

                # Use self.__class__ to ensure we set the class-level singleton
                self.__class__._client = QdrantClient(path=db_path)
                
                logger.info("Initializing SentenceTransformer model: all-MiniLM-L6-v2")
                self.__class__._model = SentenceTransformer('all-MiniLM-L6-v2')
                
                self._ensure_collection()
                logger.info("RagService initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize RagService: {e}")
                import traceback
                logger.error(traceback.format_exc())
                raise e

    def _ensure_collection(self):
        from qdrant_client.http import models
        collections = self.__class__._client.get_collections().collections
        exists = any(c.name == self.__class__.COLLECTION_NAME for c in collections)
        
        if not exists:
            self.__class__._client.create_collection(
                collection_name=self.__class__.COLLECTION_NAME,
                vectors_config=models.VectorParams(
                    size=self.__class__.VECTOR_SIZE,
                    distance=models.Distance.COSINE
                )
            )

    def upsert_chunks(self, chunks, metadata_list):
        self._initialize()
        logger.info(f"Embedding {len(chunks)} chunks...")
        embeddings = self.__class__._model.encode(chunks)
        logger.info("Embedding complete.")
        
        points = []
        for i, (chunk, metadata, vector) in enumerate(zip(chunks, metadata_list, embeddings)):
            points.append(models.PointStruct(
                id=i + hash(chunk) % 10**10, # Simple deterministic ID
                vector=vector.tolist(),
                payload={
                    "text": chunk,
                    **metadata
                }
            ))
            
        logger.info(f"Upserting {len(points)} points to Qdrant collection '{self.COLLECTION_NAME}'...")
        self.__class__._client.upsert(
            collection_name=self.COLLECTION_NAME,
            points=points
        )
        logger.info("Upsert successful.")

    def query(self, text, limit=3):
        self._initialize()
        vector = self.__class__._model.encode(text).tolist()
        
        # In newer qdrant-client versions, 'search' might be replaced by 'query_points'
        # or require specific import patterns. We use query_points for the new Query API.
        response = self.__class__._client.query_points(
            collection_name=self.COLLECTION_NAME,
            query=vector,
            limit=limit
        )
        
        return [res.payload for res in response.points]

    def get_all_sources(self):
        """Retrieve a list of unique document sources currently in the collection."""
        self._initialize()
        try:
            # Scroll through the collection to get all points (or a large batch)
            # In a production app with millions of chunks, you might use a separate RDBMS table for files.
            # Here we extract unique 'source' properties from the vector DB payload.
            records, _ = self.__class__._client.scroll(
                collection_name=self.COLLECTION_NAME,
                limit=10000,
                with_payload=True,
                with_vectors=False
            )
            
            sources = set()
            for record in records:
                if record.payload and "source" in record.payload:
                    sources.add(record.payload["source"])
            
            return sorted(list(sources))
        except Exception as e:
            logger.error(f"Error retrieving sources: {e}")
            return []
            
    def delete_by_source(self, source_name):
        """Delete all points associated with a given source file."""
        self._initialize()
        from qdrant_client.http.models import Filter, FieldCondition, MatchValue
        try:
            self.__class__._client.delete(
                collection_name=self.COLLECTION_NAME,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="source",
                            match=MatchValue(value=source_name)
                        )
                    ]
                )
            )
            logger.info(f"Deleted all chunks for source: {source_name}")
            return True
        except Exception as e:
            logger.error(f"Error deleting source {source_name}: {e}")
            return False

# Singleton instance
rag_service = RagService()
