"""
RAG Service (The Brain's Executive)
Orchestrates the interplay between Memory (Vector Store) and Logic (LLM).
"""

import logging
from typing import Any

from AFO.services.langchain_openai_service import AIRequest, langchain_openai_service
from AFO.services.vector_memory_service import vector_memory_service

logger = logging.getLogger(__name__)


class RAGService:
    """
    Retrieval-Augmented Generation Service.
    Retrieves facts from Vector Memory and generates answers using OpenAI.
    """

    def __init__(self) -> None:
        self.memory = vector_memory_service
        self.llm = langchain_openai_service

    async def ask(self, query: str) -> dict[str, Any]:
        """
        Asks Julie a question. She will search her memory first.

        Args:
            query: The user's question.

        Returns:
            Dict containing:
            - answer: The AI's response.
            - sources: List of documents used for the answer.
            - context_used: Boolean, true if memory was found and used.
        """
        # 1. Retrieve Context
        logger.info(f"RAG Search for: {query}")
        retrieved_docs = await self.memory.search(query, n_results=3)

        context_str = ""
        sources = []

        if retrieved_docs:
            logger.info(f"Found {len(retrieved_docs)} relevant memories.")
            context_parts = []
            for i, doc in enumerate(retrieved_docs):
                # Format: [Source: filename] content...
                source_name = doc.get("metadata", {}).get("filename", "Unknown Source")
                text = doc.get("text", "").strip()
                context_parts.append(f"[Source {i + 1}: {source_name}]\n{text}")
                sources.append(doc)

            context_str = "\n\n".join(context_parts)
        else:
            logger.info("No relevant memories found.")

        # 2. Construct Prompt
        if context_str:
            system_instruction = (
                "You are Julie, a helpful AI Accountant for AFO Kingdom.\n"
                "Answer the user's question using ONLY the provided Context.\n"
                "If the answer is not in the Context, say 'I don't have that information in my records.'\n"
                "Cite the source number (e.g., [Source 1]) when referencing facts."
            )
            final_prompt = f"{system_instruction}\n\n=== CONTEXT ===\n{context_str}\n\n=== QUESTION ===\n{query}"
            context_used = True
        else:
            # Fallback to general knowledge if no context found
            final_prompt = (
                f"You are Julie, a helpful AI Accountant.\n"
                f"User Question: {query}\n"
                f"(Note: No internal records were found for this query. "
                f"Answer based on general knowledge.)"
            )
            context_used = False

        # 3. Generate Answer
        try:
            request = AIRequest(
                prompt=final_prompt,
                temperature=0.3,  # Low temp for factual Q&A
                max_tokens=1000,
            )

            response = await self.llm.process_request(request)
            answer = response.response

            return {"answer": answer, "sources": sources, "context_used": context_used}

        except Exception as e:
            logger.error(f"RAG Generation failed: {e}")
            return {
                "answer": "I apologize, but I encountered an error while processing your request.",
                "error": str(e),
                "sources": [],
                "context_used": False,
            }


rag_service = RAGService()
