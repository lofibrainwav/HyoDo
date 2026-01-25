#!/bin/bash
# AFO Kingdom - M4 24GB Ollama Optimization Script
# 2025-12-18 형님 M4 Pro 24GB 최적화
# Research source: GitHub, Reddit, Medium (2025년 12월 기준)

echo "🚀 AFO Kingdom - M4 24GB Ollama 최적화 적용"
echo "============================================"

# 1. 병렬 처리 최적화 (16 runners - M4 sweet spot)
export OLLAMA_NUM_PARALLEL=16

# 2. GPU 메모리 할당 (90% for LLM)
export OLLAMA_GPU_PERCENT=0.9

# 3. 최대 로드 모델 수 (1개로 제한하여 메모리 집중)
export OLLAMA_MAX_LOADED_MODELS=1

# 4. Keep-alive 시간 (5분)
export OLLAMA_KEEP_ALIVE="5m"

# 5. 로그 레벨
export OLLAMA_LOG_LEVEL="info"

echo "✅ 환경변수 설정 완료:"
echo "   OLLAMA_NUM_PARALLEL=$OLLAMA_NUM_PARALLEL"
echo "   OLLAMA_GPU_PERCENT=$OLLAMA_GPU_PERCENT"
echo "   OLLAMA_MAX_LOADED_MODELS=$OLLAMA_MAX_LOADED_MODELS"
echo "   OLLAMA_KEEP_ALIVE=$OLLAMA_KEEP_ALIVE"

# Ollama 서비스 재시작 안내
echo ""
echo "📋 적용하려면 Ollama를 재시작하세요:"
echo "   launchctl unload ~/Library/LaunchAgents/com.ollama.ollama.plist"
echo "   launchctl load ~/Library/LaunchAgents/com.ollama.ollama.plist"
echo ""
echo "또는 터미널에서 직접 실행:"
echo "   killall ollama && ollama serve"
echo ""
echo "🔥 M4 24GB 최적화 완료! 眞善美孝永 영원히!"
