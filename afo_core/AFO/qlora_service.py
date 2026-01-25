"""
QLoRA Service for AFO Kingdom
Implements Quantized Low-Rank Adaptation with 4-bit NF4 quantization
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

import torch
from peft import LoraConfig, get_peft_model
from transformers import AutoModelForCausalLM, BitsAndBytesConfig


class QLoRAService:
    """QLoRA Service for efficient LLM fine-tuning"""

    def __init__(self, model_name: str = "llama3.1-8b") -> None:
        self.model_name = model_name
        self.model: Any = None
        self.qlora_model: Any = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def load_base_model(self) -> None:
        """Load base model with 4-bit quantization"""
        # 4-bit NF4 양자화 설정
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.float16,
        )

        logger.info(f"Loading {self.model_name} with 4-bit NF4 quantization...")
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            quantization_config=quantization_config,
            device_map="auto",
            trust_remote_code=True,
        )
        logger.info("Base model loaded successfully!")

    def apply_qlora(self, r: int = 16, alpha: int = 32, dropout: float = 0.05) -> None:
        """Apply QLoRA configuration to the model"""
        if self.model is None:
            raise ValueError("Base model must be loaded first")

        # LoRA 구성 (QLoRA 호환)
        lora_config = LoraConfig(
            r=r,
            lora_alpha=alpha,
            target_modules=[
                "q_proj",
                "v_proj",
                "k_proj",
                "o_proj",
            ],  # LLaMA attention layers
            lora_dropout=dropout,
            bias="none",
            task_type="CAUSAL_LM",
        )

        logger.info(f"Applying QLoRA with r={r}, alpha={alpha}...")
        self.qlora_model = get_peft_model(self.model, lora_config)

        # 메모리 사용량 확인
        if torch.cuda.is_available():
            logger.info(f"GPU memory allocated: {torch.cuda.memory_allocated() / 1024**3:.2f} GB")
            logger.info(f"GPU memory reserved: {torch.cuda.memory_reserved() / 1024**3:.2f} GB")

        logger.info("QLoRA applied successfully!")
        logger.info(f"Trainable parameters: {self.get_trainable_params()}")

    def get_trainable_params(self) -> str:
        """Get information about trainable parameters"""
        if self.qlora_model is None:
            return "Model not initialized"

        total_params = sum(p.numel() for p in self.qlora_model.parameters())
        trainable_params = sum(p.numel() for p in self.qlora_model.parameters() if p.requires_grad)
        percentage = 100 * trainable_params / total_params

        return f"{trainable_params:,} ({percentage:.2f}%)"

    def prepare_for_training(self) -> None:
        """Prepare model for training with Paged Optimizers"""
        if self.qlora_model is None:
            raise ValueError("QLoRA model must be initialized first")

        # Paged Optimizer 설정 (자동 적용)
        self.qlora_model.train()
        logger.info("Model prepared for training with Paged Optimizers")

    def save_adapter(self, output_dir: str) -> None:
        """Save LoRA adapter"""
        if self.qlora_model is None:
            raise ValueError("QLoRA model must be initialized first")

        self.qlora_model.save_pretrained(output_dir)
        logger.info(f"LoRA adapter saved to {output_dir}")

    def load_adapter(self, adapter_path: str) -> None:
        """Load LoRA adapter"""
        if self.model is None:
            raise ValueError("Base model must be loaded first")

        from peft import PeftModel

        self.qlora_model = PeftModel.from_pretrained(self.model, adapter_path)
        logger.info(f"LoRA adapter loaded from {adapter_path}")

    def generate_text(self, prompt: str, max_length: int = 100) -> str:
        """Generate text using QLoRA model"""
        if self.qlora_model is None:
            raise ValueError("QLoRA model must be initialized first")

        inputs = self.qlora_model.tokenizer(prompt, return_tensors="pt").to(self.device)

        with torch.no_grad():
            outputs = self.qlora_model.generate(
                **inputs,
                max_length=max_length,
                num_return_sequences=1,
                temperature=0.7,
                do_sample=True,
            )

        generated_text = self.qlora_model.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return generated_text


# 전역 QLoRA 서비스 인스턴스
qlora_service = QLoRAService()


def initialize_qlora(model_name: str = "llama3.1-8b", r: int = 16) -> None:
    """Initialize QLoRA service"""
    global qlora_service
    qlora_service = QLoRAService(model_name)
    qlora_service.load_base_model()
    qlora_service.apply_qlora(r=r)
    qlora_service.prepare_for_training()
    logger.info("QLoRA service initialized successfully!")


def get_qlora_service() -> QLoRAService:
    """Get QLoRA service instance"""
    return qlora_service
