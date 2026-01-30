from typing import Any, Dict, List

from langchain_core.callbacks.manager import CallbackManagerForRetrieverRun
from langchain_classic.retrievers import EnsembleRetriever
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_core.vectorstores.base import VectorStore

from src.data_manager.vectorstore.retrievers.bm25_retriever import BM25LexicalRetriever
from src.utils.logging import get_logger

logger = get_logger(__name__)

class HybridRetriever(BaseRetriever):
    """
    Hybrid retriever that combines BM25 (lexical) and semantic vector search.
    """
    vectorstore: VectorStore
    k: int
    bm25_weight: float = 0.6
    semantic_weight: float = 0.4
    bm25_k1: float = 0.5
    bm25_b: float = 0.75
    _bm25_retriever: BM25LexicalRetriever = None
    _ensemble_retriever: EnsembleRetriever = None
    _dense_retriever: BaseRetriever = None
    
    def __init__(self, vectorstore: VectorStore, k: int = 3,
                 bm25_weight: float = 0.6, semantic_weight: float = 0.4,
                 bm25_k1: float = 0.5, bm25_b: float = 0.75):
        super().__init__(
            vectorstore=vectorstore, 
            k=k,
            bm25_weight=bm25_weight,
            semantic_weight=semantic_weight,
            bm25_k1=bm25_k1,
            bm25_b=bm25_b
        )
        self.k = k
        self._initialize_retrievers()
    
    def _initialize_retrievers(self):
        """
        Initialize BM25 and ensemble retrievers with documents from the vectorstore.
        """
        try:
            dense_retriever = self.vectorstore.as_retriever(search_kwargs={"k": self.k})
            self._dense_retriever = dense_retriever

            self._bm25_retriever = BM25LexicalRetriever(
                vectorstore=self.vectorstore,
                k=self.k,
                bm25_k1=self.bm25_k1,
                bm25_b=self.bm25_b,
            )

            if not self._bm25_retriever.ready:
                logger.warning(
                    "BM25 retriever not initialised; falling back to semantic search only."
                )
                self._ensemble_retriever = None
                return
            
            self._ensemble_retriever = EnsembleRetriever(
                retrievers=[self._bm25_retriever, dense_retriever],
                weights=[self.bm25_weight, self.semantic_weight]
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize hybrid retriever: {e}")
            raise
    
    def _get_relevant_documents(self, query: str, *, run_manager: CallbackManagerForRetrieverRun = None) -> List[Document]:
        """
        Retrieve relevant documents using hybrid search (BM25 + semantic).
        Falls back to semantic search only if hybrid search is not available.
        
        Returns:
            List of (Document, score) tuples. Score is -1.0 placeholder for hybrid/fallback.
        """
        logger.debug(f"Query: {query}")
        logger.debug(f"Using hybrid search (BM25 + semantic) to retrieve top-{self.k} docs")
        if self._ensemble_retriever is None:
            if self._dense_retriever is None:
                raise RuntimeError("HybridRetriever not initialised; no retriever available.")
            logger.debug("Falling back to semantic-only retriever")
            # Return docs with placeholder scores to match expected format
            fallback_docs = self._dense_retriever.invoke(query)
            return [(doc, -1.0) for doc in fallback_docs]

        # Get combined results from ensemble
        ensemble_docs = self._ensemble_retriever._get_relevant_documents(query, run_manager=run_manager)
        logger.debug(f"Ensemble returned {len(ensemble_docs)} final documents")
        
        # Return placeholder scores for hybrid search
        logger.debug("Using placeholder score (-1) for hybrid search results")
        docs_with_scores = self._compute_hybrid_scores(ensemble_docs, query)
        
        return docs_with_scores
    
    def _compute_hybrid_scores(self, ensemble_docs, query):
        """
        Return hardcoded -1 scores for hybrid search.
        This is a temporary placeholder until proper hybrid scoring is implemented.
        The -1 indicates to users that these scores are not yet calibrated.
        """
        docs_with_scores = []
        
        for doc in ensemble_docs:
            # Use -1 as a placeholder score to indicate scores are not yet properly implemented
            docs_with_scores.append((doc, -1.0))
            
            logger.debug(f"Doc: {doc.metadata.get('filename', 'unknown')[:50]}... Score=-1.0 (placeholder)")
        
        return docs_with_scores
