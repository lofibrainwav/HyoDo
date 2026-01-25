"""
QLoRA-AdaLoRA Hybrid Service for AFO Kingdom
Combines QLoRA (4-bit quantization) with AdaLoRA (adaptive rank allocation)
"""

from typing import Any

import torch
from peft import AdaLoraConfig, get_peft_model
from transformers import AutoModelForCausalLM, BitsAndBytesConfig


class QLoRAAdaLoRAHybridService:
    """Hybrid service combining QLoRA and AdaLoRA for optimal efficiency"""

    def __init__(self, model_name: str = "llama3.1-8b") -> None:
        self.model_name = model_name
        self.model: Any = None
        self.hybrid_model: Any = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def load_base_model(self) -> None:
        """Load base model with 4-bit quantization (QLoRA)"""
        # 4-bit NF4 양자화 설정
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.float16,
        )

        print(f"Loading {self.model_name} with 4-bit NF4 quantization (QLoRA)...")
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            quantization_config=quantization_config,
            device_map="auto",
            trust_remote_code=True,
        )
        print("Base model loaded successfully!")

    def apply_hybrid_optimization(
        self, init_r: int = 12, target_r: int = 8, alpha: int = 32
    ) -> None:
        """Apply QLoRA + AdaLoRA hybrid configuration"""
        if self.model is None:
            raise ValueError("Base model must be loaded first")

        # AdaLoRA 구성 (QLoRA 기반)
        adalora_config = AdaLoraConfig(
            init_r=init_r,  # 초기 랭크
            target_r=target_r,  # 목표 랭크 (동적 조정)
            lora_alpha=alpha,
            target_modules=[
                "q_proj",
                "v_proj",
                "k_proj",
                "o_proj",
            ],  # LLaMA attention layers
            lora_dropout=0.05,
            bias="none",
            task_type="CAUSAL_LM",
            # AdaLoRA 특정 파라미터
            beta1=0.85,
            beta2=0.85,
            orth_reg_weight=0.5,
        )

        print(f"Applying QLoRA-AdaLoRA hybrid with init_r={init_r}, target_r={target_r}...")
        self.hybrid_model = get_peft_model(self.model, adalora_config)

        # 메모리 사용량 확인
        if torch.cuda.is_available():
            print(f"GPU memory allocated: {torch.cuda.memory_allocated() / 1024**3:.2f} GB")
            print(f"GPU memory reserved: {torch.cuda.memory_reserved() / 1024**3:.2f} GB")

        print("QLoRA-AdaLoRA hybrid applied successfully!")
        print(f"Trainable parameters: {self.get_trainable_params()}")

    def get_trainable_params(self) -> str:
        """Get information about trainable parameters"""
        if self.hybrid_model is None:
            return "Model not initialized"

        total_params = sum(p.numel() for p in self.hybrid_model.parameters())
        trainable_params = sum(p.numel() for p in self.hybrid_model.parameters() if p.requires_grad)
        percentage = 100 * trainable_params / total_params

        return f"{trainable_params:,} ({percentage:.2f}%)"

    def prepare_for_training(self) -> None:
        """Prepare model for training with adaptive optimization"""
        if self.hybrid_model is None:
            raise ValueError("Hybrid model must be initialized first")

        self.hybrid_model.train()
        print("Model prepared for training with QLoRA-AdaLoRA hybrid!")

    def update_and_allocate(self, global_step: int) -> None:
        """AdaLoRA: Update rank allocation based on importance scores"""
        if hasattr(self.hybrid_model, "update_and_allocate"):
            self.hybrid_model.update_and_allocate(global_step)
            print(f"AdaLoRA rank updated at step {global_step}")

    def save_adapter(self, output_dir: str) -> None:
        """Save hybrid adapter"""
        if self.hybrid_model is None:
            raise ValueError("Hybrid model must be initialized first")

        self.hybrid_model.save_pretrained(output_dir)
        print(f"QLoRA-AdaLoRA hybrid adapter saved to {output_dir}")

    def load_adapter(self, adapter_path: str) -> None:
        """Load hybrid adapter"""
        if self.model is None:
            raise ValueError("Base model must be loaded first")

        from peft import PeftModel

        self.hybrid_model = PeftModel.from_pretrained(self.model, adapter_path)
        print(f"QLoRA-AdaLoRA hybrid adapter loaded from {adapter_path}")

    def generate_text(self, prompt: str, max_length: int = 100) -> str:
        """Generate text using hybrid model"""
        if self.hybrid_model is None:
            raise ValueError("Hybrid model must be initialized first")

        inputs = self.hybrid_model.tokenizer(prompt, return_tensors="pt").to(self.device)

        with torch.no_grad():
            outputs = self.hybrid_model.generate(
                **inputs,
                max_length=max_length,
                num_return_sequences=1,
                temperature=0.7,
                do_sample=True,
            )

        generated_text = self.hybrid_model.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return generated_text


# 전역 하이브리드 서비스 인스턴스
hybrid_service = QLoRAAdaLoRAHybridService()


def initialize_hybrid_qlora_adalora(
    model_name: str = "llama3.1-8b", init_r: int = 12, target_r: int = 8
) -> None:
    """Initialize QLoRA-AdaLoRA hybrid service"""
    global hybrid_service
    hybrid_service = QLoRAAdaLoRAHybridService(model_name)
    hybrid_service.load_base_model()
    hybrid_service.apply_hybrid_optimization(init_r=init_r, target_r=target_r)
    hybrid_service.prepare_for_training()
    print("QLoRA-AdaLoRA hybrid service initialized successfully!")


def get_hybrid_service() -> QLoRAAdaLoRAHybridService:
    """Get hybrid service instance"""
    return hybrid_service
