#!/bin/bash
# AFO Kingdom Samahwi (30B) MLX QLoRA Optimization Script (眞/善/美/孝/永)
# Usage: ./tune_samahwi_qlora.sh
# Prerequisites: pip install mlx-lm mlx-cuda

# 1. Environment (永: Persistent Settings)
export MLX_OPTIMIZE=true
export MLX_DEVICE=gpu

echo "👑 [Samahwi] Starting QLoRA Fine-tuning Optimization..."

# 2. QLoRA Tuning (Goodness: Stability via Overfitting Prevention)
# - Learning Rate: 1e-4 (Optimal for >13B)
# - Scheduler: Cosine with Warmup (Prevents divergence)
# - Patience: Encapsulated via manual monitoring (steps-per-eval)

python3 -m mlx_lm.lora \
  --model ./mlx_sama_hui \
  --train \
  --data ./data \
  --quantize \
  --batch-size 1 \
  --iters 300 \
  --learning-rate 1e-4 \
  --lr-scheduler cosine \
  --warmup-ratio 0.03 \
  --steps-per-eval 50 \
  --adapter-path ./qlora_adapters \
  --rank 8 \
  --alpha 16 \
  --dropout 0.1 \
  --max-seq-length 4096 \
  --grad-checkpoint

echo "✅ [Samahwi] Tuning Complete. To fuse: python3 -m mlx_lm.fuse --model ./mlx_sama_hui --adapter-path ./qlora_adapters --save-path ./fused_sama_hui"
