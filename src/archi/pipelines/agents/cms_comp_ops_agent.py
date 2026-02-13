from __future__ import annotations

import json
import os
from typing import Any, Callable, Dict, List, Sequence, Optional

from langchain_core.documents import Document
from langchain.agents.middleware import TodoListMiddleware, LLMToolSelectorMiddleware

from src.utils.logging import get_logger
from src.archi.pipelines.agents.base_react import BaseReActAgent
from src.data_manager.vectorstore.retrievers import HybridRetriever
from src.archi.pipelines.agents.tools import (
    create_document_fetch_tool,
    create_file_search_tool,
    create_metadata_search_tool,
    create_metadata_schema_tool,
    create_retriever_tool,
    RemoteCatalogClient,
)
from src.archi.pipelines.agents.utils.history_utils import infer_speaker

logger = get_logger(__name__)


class CMSCompOpsAgent(BaseReActAgent):
    """Agent designed for CMS CompOps operations."""

    def __init__(
        self,
        config: Dict[str, Any],
        *args,
        **kwargs,
    ) -> None:
        super().__init__(config, *args, **kwargs)

        self.catalog_service = RemoteCatalogClient.from_deployment_config(self.config)
        self._vector_retrievers = None
        self._vector_tool = None
        self.enable_vector_tools = "search_vectorstore_hybrid" in self.selected_tool_names

        self.rebuild_static_tools()
        self.rebuild_static_middleware()
        self.refresh_agent()

    def get_tool_registry(self) -> Dict[str, Callable[[], Any]]:
        return {name: entry["builder"] for name, entry in self._tool_definitions().items()}

    def get_tool_descriptions(self) -> Dict[str, str]:
        return {name: entry["description"] for name, entry in self._tool_definitions().items()}

    def _tool_definitions(self) -> Dict[str, Dict[str, Any]]:
        return {
            "search_local_files": {
                "builder": self._build_file_search_tool,
                "description": (
                    "Grep-like search over file contents. Provide a distinctive phrase or regex; optionally use "
                    "regex=true, case_sensitive=true, and context (before/after). Returns matching lines with hashes; "
                    "use fetch_catalog_document for full text."
                ),
            },
            "search_metadata_index": {
                "builder": self._build_metadata_search_tool,
                "description": (
                    "Query the files' metadata catalog (ticket IDs, source URLs, resource types, etc.). "
                    "Supports key:value filters and OR (e.g., source_type:git OR url:https://... ticket_id:CMS-123). "
                    "Returns matching files with metadata; use fetch_catalog_document to pull full text."
                ),
            },
            "list_metadata_schema": {
                "builder": self._build_metadata_schema_tool,
                "description": (
                    "List metadata schema hints: supported keys, distinct source_type values, and suffixes. "
                    "Use this to learn which key:value filters are available before searching."
                ),
            },
            "fetch_catalog_document": {
                "builder": self._build_fetch_tool,
                "description": (
                    "Fetch full document text by resource hash after a search hit. "
                    "Use this sparingly to pull only the most relevant files."
                ),
            },
            "search_vectorstore_hybrid": {
                "builder": self._build_vector_tool_placeholder,
                "description": (
                    "Hybrid search over the knowledge base that combines both lexical (BM25) and semantic (vector) search."
                ),
            },
            "mcp": {
                "builder": self._build_mcp_tools,
                "description": "Access tools served via configured MCP servers.",
            },
        }

    def _build_file_search_tool(self) -> Callable:
        description = self._tool_definitions()["search_local_files"]["description"]
        return create_file_search_tool(
            self.catalog_service,
            description=description,
            store_docs=self._store_documents,
        )

    def _build_metadata_search_tool(self) -> Callable:
        description = self._tool_definitions()["search_metadata_index"]["description"]
        return create_metadata_search_tool(
            self.catalog_service,
            description=description,
            store_docs=self._store_documents,
        )

    def _build_metadata_schema_tool(self) -> Callable:
        description = self._tool_definitions()["list_metadata_schema"]["description"]
        return create_metadata_schema_tool(
            self.catalog_service,
            description=description,
        )

    def _build_fetch_tool(self) -> Callable:
        description = self._tool_definitions()["fetch_catalog_document"]["description"]
        return create_document_fetch_tool(
            self.catalog_service,
            description=description,
        )

    def _build_vector_tool_placeholder(self) -> List[Callable]:
        return []

    # def _build_static_middleware(self) -> List[Callable]:
    #     """
    #     Initialize middleware: currently, testing what works best.
    #     This is static.
    #     """
    #     todolist_middleware = TodoListMiddleware()
    #     llmtoolselector_middleware = LLMToolSelectorMiddleware(
    #         model=self.agent_llm,
    #         max_tools=3,
    #     )
    #     return [todolist_middleware, llmtoolselector_middleware]

    def _store_documents(self, stage: str, docs: Sequence[Document]) -> None:
        """Centralised helper used by tools to record documents into the active memory."""
        memory = self.active_memory
        if not memory:
            return
        # Prefer memory convenience method if available
        try:
            logger.debug("Recording %d documents from stage '%s' via record_documents", len(docs), stage)
            memory.record_documents(stage, docs)
        except Exception:
            # fallback to explicit record + note
            memory.record(stage, docs)
            memory.note(f"{stage} returned {len(list(docs))} document(s).")

    def _prepare_inputs(self, history: Any, **kwargs) -> Dict[str, Any]:
        """Create list of messages using LangChain's formatting."""
        history = history or []
        history_messages = [infer_speaker(msg[0])(msg[1]) for msg in history]
        return {"history": history_messages}

    def _prepare_agent_inputs(self, **kwargs) -> Dict[str, Any]:
        """Prepare agent state and formatted inputs shared by invoke/stream."""

        # event-level memory (which documents were retrieved)
        memory = self.start_run_memory()

        # refresh vs connection
        vectorstore = kwargs.get("vectorstore")
        if vectorstore:
            self._update_vector_retrievers(vectorstore)
        else:
            self._vector_retrievers = None
            self._vector_tools = None
        extra_tools = self._vector_tools if self._vector_tools else None

        self.refresh_agent(extra_tools=extra_tools)

        inputs = self._prepare_inputs(history=kwargs.get("history"))
        history_messages = inputs["history"]
        if history_messages:
            memory.note(f"History contains {len(history_messages)} message(s).")
            last_message = history_messages[-1]
            content = self._message_content(last_message)
            if content:
                snippet = content if len(content) <= 200 else f"{content[:197]}..."
                memory.note(f"Latest user message: {snippet}")
        return {"messages": history_messages}

    def _update_vector_retrievers(self, vectorstore: Any) -> None:
        """Instantiate or refresh the vectorstore retriever tool using hybrid retrieval."""
        if not self.enable_vector_tools:
            self._vector_retrievers = None
            self._vector_tools = None
            return
        retrievers_cfg = self.dm_config.get("retrievers", {})
        hybrid_cfg = retrievers_cfg.get("hybrid_retriever", {})

        k = hybrid_cfg.get("num_documents_to_retrieve", 5)
        bm25_weight = hybrid_cfg.get("bm25_weight", 0.6)
        semantic_weight = hybrid_cfg.get("semantic_weight", 0.4)

        hybrid_retriever = HybridRetriever(
            vectorstore=vectorstore,
            k=k,
            bm25_weight=bm25_weight,
            semantic_weight=semantic_weight,
        )

        hybrid_description = self._tool_definitions()["search_vectorstore_hybrid"]["description"]

        self._vector_retrievers = [hybrid_retriever]
        self._vector_tools = []
        self._vector_tools.append(
            create_retriever_tool(
                hybrid_retriever,
                name="search_vectorstore_hybrid",
                description=hybrid_description,
                store_docs=self._store_documents,
            )
        )
