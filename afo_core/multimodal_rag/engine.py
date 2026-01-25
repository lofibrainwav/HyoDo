# Trinity Score: 92.0 (Phase 30 Multimodal RAG Engine Refactoring)
"""Multimodal RAG Engine - Core Search and Retrieval Logic"""

import logging
from typing import Any

from .documents import MultimodalDocument
from .memory import MemoryManager
from .services import MultimodalServiceManager

logger = logging.getLogger(__name__)

VERSION = "FINAL_TRUTH_1"


class MultimodalRAGEngine:
    """Multimodal RAG Engine supporting text, images, and other media.

    Trinity Score: 眞93% 善94% 美92% 孝91% 永90%
    """

    def __init__(self, embedding_model: str = "default", **kwargs: Any) -> None:
        self.embedding_model = embedding_model
        self.documents: list[MultimodalDocument] = []
        self.supported_types = ["text", "image", "audio", "video"]

        # Initialize components
        self.memory_manager = MemoryManager()
        self.service_manager = MultimodalServiceManager()

        logger.info("MultimodalRAGEngine initialized with memory and service management")

    def add_document(
        self,
        content: str,
        content_type: str = "text",
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """문서를 RAG 인덱스에 추가 (메모리 관리 적용)

        Args:
            content: 문서 내용
            content_type: 콘텐츠 타입
            metadata: 메타데이터

        Returns:
            추가 성공 여부
        """
        try:
            # 메모리 및 문서 수 제한 확인
            if not self.memory_manager.can_add_document(
                self.documents, content, content_type, metadata or {}
            ):
                return False

            # 메모리 사용량 추정
            doc_memory_mb = self.memory_manager.estimate_document_memory(
                content, content_type, metadata or {}
            )

            # 메모리 부족 시 자동 정리
            if (
                self.memory_manager.current_memory_mb + doc_memory_mb
                > self.memory_manager.config["max_memory_mb"]
            ):
                threshold_memory = (
                    self.memory_manager.config["max_memory_mb"]
                    * self.memory_manager.config["cleanup_threshold"]
                )
                if self.memory_manager.current_memory_mb >= threshold_memory:
                    self.documents, cleaned_count = self.memory_manager.cleanup_old_documents(
                        self.documents, doc_memory_mb
                    )
                    if cleaned_count > 0:
                        logger.info("메모리 정리로 %d개 문서 제거됨", cleaned_count)

            # 문서 생성 및 추가
            doc = MultimodalDocument(
                content=content, content_type=content_type, metadata=metadata or {}
            )

            self.documents.append(doc)
            self.memory_manager.add_document_memory(doc_memory_mb, id(doc))

            logger.info(
                "문서 추가: %s (%.2fMB, 총 %.2fMB)",
                content_type,
                doc_memory_mb,
                self.memory_manager.current_memory_mb,
            )
            return True

        except (ValueError, TypeError, MemoryError) as e:
            logger.error("문서 추가 실패 (값/타입/메모리 에러): %s", str(e))
            return False
        except Exception as e:
            logger.error("문서 추가 실패 (예상치 못한 에러): %s", str(e))
            return False

    def add_image(self, image_path: str, description: str = "", analyze: bool = True) -> bool:
        """이미지 문서 추가 with vision analysis."""
        try:
            # Process image with multimodal services
            processing_result = self.service_manager.process_image_for_rag(image_path)

            if not processing_result.get("processing_success", False):
                # Fallback: basic image addition
                content = description or f"Image: {image_path}"
                metadata = {"path": image_path, "analyzed": False}
                return self.add_document(content=content, content_type="image", metadata=metadata)

            # Enhanced content with AI analysis
            full_description = description or ""
            if full_description:
                full_description += "\n\n"

            # Add extracted text
            if processing_result.get("extracted_text"):
                full_description += f"[Extracted Text]\n{processing_result['extracted_text']}\n\n"

            # Add AI vision analysis
            if processing_result.get("description"):
                full_description += f"[AI Vision Analysis]\n{processing_result['description']}"

            metadata = {
                "path": image_path,
                "analyzed": True,
                "vision_model": processing_result.get("vision_model"),
                "processing_success": True,
            }

            return self.add_document(
                content=full_description,
                content_type="image",
                metadata=metadata,
            )
        except Exception as e:
            logger.error("Failed to add image: %s", str(e))
            return False

    def add_audio(self, audio_path: str, description: str = "", transcribe: bool = True) -> bool:
        """오디오 문서 추가 with transcription."""
        try:
            # Process audio with multimodal services
            processing_result = self.service_manager.process_audio_for_rag(audio_path)

            if not processing_result.get("processing_success", False):
                # Fallback: basic audio addition
                content = description or f"Audio: {audio_path}"
                metadata = {"path": audio_path, "transcribed": False}
                return self.add_document(content=content, content_type="audio", metadata=metadata)

            # Enhanced content with transcription
            full_description = description or ""
            if full_description:
                full_description += "\n\n"

            # Add transcription
            if processing_result.get("transcription"):
                full_description += f"[Audio Transcription]\n{processing_result['transcription']}"

            metadata = {
                "path": audio_path,
                "transcribed": True,
                "language": processing_result.get("language"),
                "audio_model": processing_result.get("audio_model"),
                "segments_count": processing_result.get("segments_count", 0),
                "processing_success": True,
            }

            return self.add_document(
                content=full_description,
                content_type="audio",
                metadata=metadata,
            )
        except Exception as e:
            logger.error("Failed to add audio: %s", str(e))
            return False

    def search(
        self, query: str, top_k: int = 5, content_types: list[str] | None = None
    ) -> list[MultimodalDocument]:
        """Search for relevant documents."""
        try:
            # Filter by content type if specified
            candidates = self.documents
            if content_types:
                candidates = [d for d in candidates if d.content_type in content_types]

            # Simple keyword matching (would use embeddings in production)
            query_lower = query.lower()
            scored = []
            for doc in candidates:
                score = sum(1 for word in query_lower.split() if word in doc.content.lower())
                if score > 0:
                    scored.append((score, doc))

            # Sort by score and return top_k
            scored.sort(key=lambda x: x[0], reverse=True)
            return [doc for _, doc in scored[:top_k]]
        except (AttributeError, ValueError, IndexError) as e:
            logger.warning("문서 검색 중 에러: %s", str(e))
            return []
        except Exception as e:
            logger.debug("문서 검색 중 예상치 못한 에러: %s", str(e))
            return []

    def get_stats(self) -> dict[str, Any]:
        """엔진 통계 및 메모리 상태 반환"""
        try:
            type_counts: dict[str, int] = {}
            for doc in self.documents:
                type_counts[doc.content_type] = type_counts.get(doc.content_type, 0) + 1

            memory_stats = self.memory_manager.get_stats()

            return {
                "total_documents": len(self.documents),
                "max_documents": self.memory_manager.config["max_documents"],
                "documents_utilization": len(self.documents)
                / self.memory_manager.config["max_documents"],
                "by_type": type_counts,
                "embedding_model": self.embedding_model,
                "memory_stats": memory_stats,
                "service_stats": self.service_manager.get_service_status(),
                "health_status": self._get_health_status(),
            }
        except (AttributeError, ValueError, KeyError) as e:
            logger.warning("통계 수집 실패: %s", str(e))
            return {"total_documents": 0, "error": "stats collection failed"}
        except Exception as e:
            logger.debug("통계 수집 중 예상치 못한 에러: %s", str(e))
            return {"total_documents": 0, "error": "stats collection failed"}

    def _get_health_status(self) -> str:
        """엔진 건강 상태 평가"""
        try:
            doc_util = len(self.documents) / self.memory_manager.config["max_documents"]
            mem_util = (
                self.memory_manager.current_memory_mb / self.memory_manager.config["max_memory_mb"]
            )

            if doc_util > 0.95 or mem_util > 0.95:
                return "critical"
            elif doc_util > 0.8 or mem_util > 0.8:
                return "warning"
            elif doc_util > 0.5 or mem_util > 0.5:
                return "normal"
            else:
                return "healthy"
        except (ZeroDivisionError, ValueError, TypeError) as e:
            logger.warning("건강 상태 평가 실패: %s", str(e))
            return "unknown"
        except Exception as e:
            logger.debug("건강 상태 평가 중 예상치 못한 에러: %s", str(e))
            return "unknown"
