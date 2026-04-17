"""
Memory actions: store, search, and delete knowledge in ChromaDB.

Each function is designed to be called from MCP tool handlers in main.py.
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from tools.logger import log_action
from tools.memory.client import embed_texts, get_collection


VALID_CATEGORIES = {"facts", "learnings", "task results"}

def action_store(
    content: str,
    category: str,
    source: str | None = None,
) -> dict[str, Any]:
    """Store a piece of knowledge in long-term memory.

    Args:
        content: The text content to memorize.
        category: Classification label (e.g. user_preference, fact, learning, task_result).
        source: Optional provenance information.

    Returns:
        Dict with the generated document ID and status.
    """
    if category not in VALID_CATEGORIES:
        return {"error": f"Invalid category '{category}'. Must be one of: {', '.join(sorted(VALID_CATEGORIES))}"}

    log_action("memory_store", [content[:80], category])

    doc_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    embeddings = embed_texts([content])

    collection = get_collection()
    collection.add(
        ids=[doc_id],
        embeddings=embeddings,
        documents=[content],
        metadatas=[
            {
                "category": category,
                "source": source or "",
                "created_at": now,
            }
        ],
    )

    return {"id": doc_id, "status": "stored"}


def action_search(
    query: str,
    n_results: int = 5,
    category: str | None = None,
    max_distance: float = 1.0,
) -> dict[str, Any]:
    """Search long-term memory for knowledge relevant to a query.

    Args:
        query: Natural-language search query.
        n_results: Maximum number of results to return.
        category: Optional category filter.
        max_distance: Maximum cosine distance to be considered relevant.

    Returns:
        Dict with a list of matching memory entries.
    """
    if category is not None and category not in VALID_CATEGORIES:
        return {"error": f"Invalid category '{category}'. Must be one of: {', '.join(sorted(VALID_CATEGORIES))}"}

    log_action("memory_search", [query[:80], n_results, category, max_distance])

    query_embedding = embed_texts([query], is_query=True)

    where_filter = {"category": category} if category else None

    collection = get_collection()
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=n_results,
        where=where_filter,
        include=["documents", "metadatas", "distances"],
    )

    entries = []
    if results and results["ids"]:
        for i, doc_id in enumerate(results["ids"][0]):
            dist = results["distances"][0][i]
            if dist <= max_distance:
                entries.append(
                    {
                        "id": doc_id,
                        "content": results["documents"][0][i],
                        "category": results["metadatas"][0][i].get("category", ""),
                        "source": results["metadatas"][0][i].get("source", ""),
                        "created_at": results["metadatas"][0][i].get("created_at", ""),
                        "distance": dist,
                    }
                )

    return {"query": query, "count": len(entries), "results": entries}


def action_delete(memory_id: str) -> dict[str, Any]:
    """Delete a specific memory entry by its ID.

    Args:
        memory_id: The UUID of the memory to delete.

    Returns:
        Dict with deletion status.
    """
    log_action("memory_delete", [memory_id])

    collection = get_collection()
    collection.delete(ids=[memory_id])

    return {"id": memory_id, "status": "deleted"}
