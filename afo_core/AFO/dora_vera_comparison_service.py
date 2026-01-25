"""
DoRA-VeRA Comparison Service for AFO Kingdom
Implements DoRA (Weight-Decomposed Low-Rank Adaptation) and VeRA (Vector-based Random Matrix Adaptation)
with comprehensive benchmarking against existing QLoRA-AdaLoRA hybrid
"""

import logging
import time
from typing import Any

logger = logging.getLogger(__name__)

import psutil
import torch
from peft import DoRAConfig, VeraConfig, get_peft_model
from transformers import AutoModelForCausalLM


class DoRAVeRAComparisonService:
    """Comprehensive comparison service for DoRA and VeRA techniques"""

    def __init__(self, model_name: str = "llama3.1-8b") -> None:
        self.model_name = model_name
        self.base_model: Any = None
        self.dora_model: Any = None
        self.vera_model: Any = None
        self.qlora_adalora_model: Any = None  # For comparison
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def load_base_model(self) -> dict[str, Any]:
        """Load base model and measure memory usage"""
        logger.info("Loading base model for DoRA-VeRA comparison...")

        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024

        self.base_model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            device_map="auto",
            trust_remote_code=True,
            torch_dtype=torch.float16,
        )

        load_time = time.time() - start_time
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024
        memory_delta = end_memory - start_memory

        gpu_memory = 0
        if torch.cuda.is_available():
            gpu_memory = torch.cuda.memory_allocated() / 1024**3

        logger.info(f"Base model loaded in {load_time:.2f}s")
        logger.info(f"Memory delta: {memory_delta:.1f}MB")
        if torch.cuda.is_available():
            logger.info(f"GPU memory: {gpu_memory:.2f}GB")

        return {
            "load_time": load_time,
            "memory_delta": memory_delta,
            "gpu_memory": gpu_memory,
            "total_params": sum(p.numel() for p in self.base_model.parameters()),
        }

    def apply_dora(self, r: int = 16, alpha: int = 32) -> dict[str, Any]:
        """Apply DoRA optimization"""
        if self.base_model is None:
            raise ValueError("Base model must be loaded first")

        logger.info(f"Applying DoRA with r={r}, alpha={alpha}...")

        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024

        dora_config = DoRAConfig(
            r=r,
            lora_alpha=alpha,
            target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
            lora_dropout=0.05,
            bias="none",
            task_type="CAUSAL_LM",
        )

        self.dora_model = get_peft_model(self.base_model, dora_config)

        apply_time = time.time() - start_time
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024
        memory_delta = end_memory - start_memory

        trainable_params = sum(p.numel() for p in self.dora_model.parameters() if p.requires_grad)
        total_params = sum(p.numel() for p in self.dora_model.parameters())
        efficiency = 100 * trainable_params / total_params

        logger.info(f"Algorithm applied in {apply_time:.2f}s")
        logger.info(f"Memory delta: {memory_delta:.1f}MB")
        logger.info(f"Trainable params: {trainable_params:,} ({efficiency:.2f}%)")

        return {
            "apply_time": apply_time,
            "memory_delta": memory_delta,
            "trainable_params": trainable_params,
            "total_params": total_params,
            "efficiency": efficiency,
        }

    def apply_vera(self, r: int = 8, alpha: int = 16) -> dict[str, Any]:
        """Apply VeRA optimization"""
        if self.base_model is None:
            raise ValueError("Base model must be loaded first")

        logger.info(f"Applying VeRA with r={r}, alpha={alpha}...")

        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024

        vera_config = VeraConfig(
            r=r,
            alpha=alpha,
            target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
            dora_alpha=alpha,  # DoRA compatibility
            task_type="CAUSAL_LM",
        )

        self.vera_model = get_peft_model(self.base_model, vera_config)

        apply_time = time.time() - start_time
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024
        memory_delta = end_memory - start_memory

        trainable_params = sum(p.numel() for p in self.vera_model.parameters() if p.requires_grad)
        total_params = sum(p.numel() for p in self.vera_model.parameters())
        efficiency = 100 * trainable_params / total_params

        logger.info(f"Algorithm applied in {apply_time:.2f}s")
        logger.info(f"Memory delta: {memory_delta:.1f}MB")
        logger.info(f"Trainable params: {trainable_params:,} ({efficiency:.2f}%)")

        return {
            "apply_time": apply_time,
            "memory_delta": memory_delta,
            "trainable_params": trainable_params,
            "total_params": total_params,
            "efficiency": efficiency,
        }

    def load_qlora_adalora_for_comparison(self) -> dict[str, Any]:
        """Load existing QLoRA-AdaLoRA hybrid for comparison"""
        try:
            from .qlora_adalora_hybrid_service import QLoRAAdaLoRAHybridService

            service = QLoRAAdaLoRAHybridService(self.model_name)
            service.load_base_model()
            hybrid_stats = service.apply_hybrid_optimization()

            self.qlora_adalora_model = service.hybrid_model

            return {
                "success": True,
                "trainable_params": hybrid_stats.get("trainable_params", 0),
                "efficiency": hybrid_stats.get("efficiency", 0),
            }
        except Exception as e:
            logger.info(f"Failed to load QLoRA-AdaLoRA for comparison: {e}")
            return {"success": False, "error": str(e)}

    def benchmark_generation(
        self, prompt: str = "Hello, tell me about AI:", max_length: int = 50
    ) -> dict[str, Any]:
        """Benchmark text generation across all models"""
        results = {}

        for name, model in [
            ("DoRA", self.dora_model),
            ("VeRA", self.vera_model),
            ("QLoRA-AdaLoRA", self.qlora_adalora_model),
        ]:
            if model is None:
                results[name] = {"error": "Model not initialized"}
                continue

            try:
                inputs = model.tokenizer(prompt, return_tensors="pt").to(self.device)

                start_time = time.time()
                with torch.no_grad():
                    outputs = model.generate(
                        **inputs,
                        max_length=max_length,
                        num_return_sequences=1,
                        temperature=0.7,
                        do_sample=True,
                    )
                gen_time = time.time() - start_time

                generated_text = model.tokenizer.decode(outputs[0], skip_special_tokens=True)

                results[name] = {
                    "success": True,
                    "generation_time": gen_time,
                    "output_length": len(generated_text),
                    "generated_text": (
                        generated_text[:100] + "..."
                        if len(generated_text) > 100
                        else generated_text
                    ),
                }

            except Exception as e:
                results[name] = {"error": str(e)}

        return results

    def comprehensive_benchmark(self) -> dict[str, Any]:
        """Run comprehensive benchmark comparing all techniques"""
        logger.info("=" * 80)
        logger.info("DoRA-VeRA Comprehensive Benchmark vs QLoRA-AdaLoRA")
        logger.info("=" * 80)

        results = {
            "timestamp": time.time(),
            "model_name": self.model_name,
            "device": str(self.device),
        }

        # Load base model
        logger.info("1. Loading base model...")
        results["base_model"] = self.load_base_model()

        # Apply optimizations
        logger.info("\n2. Applying DoRA...")
        results["dora"] = self.apply_dora()

        logger.info("\n3. Applying VeRA...")
        results["vera"] = self.apply_vera()

        logger.info("\n4. Loading QLoRA-AdaLoRA for comparison...")
        results["qlora_adalora_comparison"] = self.load_qlora_adalora_for_comparison()

        # Benchmark generation
        logger.info("\n5. Benchmarking text generation...")
        results["generation_benchmark"] = self.benchmark_generation()

        # Summary
        logger.info("\n" + "=" * 80)
        logger.info("BENCHMARK SUMMARY")
        logger.info("=" * 80)

        for technique in ["dora", "vera"]:
            if technique in results and "efficiency" in results[technique]:
                logger.info(
                    f"{technique.upper()}: {results[technique]['efficiency']:.2f}% efficiency"
                )

        qlora_comparison = results.get("qlora_adalora_comparison", {})
        if qlora_comparison.get("success"):
            logger.info(f"QLoRA-AdaLoRA: {qlora_comparison.get('efficiency', 0):.2f}% efficiency")

        logger.info("\n✅ Benchmark completed successfully!")

        return results


# Convenience functions
def compare_dora_vera_techniques(model_name: str = "llama3.1-8b") -> dict[str, Any]:
    """Compare DoRA and VeRA techniques"""
    service = DoRAVeRAComparisonService(model_name)
    return service.comprehensive_benchmark()


def get_dora_service(model_name: str = "llama3.1-8b") -> DoRAVeRAComparisonService:
    """Get DoRA-VeRA comparison service instance"""
    return DoRAVeRAComparisonService(model_name)
