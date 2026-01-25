# Trinity Score: 90.0 (Established by Chancellor)
# packages/afo-core/alignment/advanced_dpo.py
# (고급 DPO - LoRA 효율화 상세)
# 🧭 Trinity Score: 眞95% 善99% 美95% 孝100% (Efficiency)

import logging
import os

from datasets import load_dataset
from peft import LoraConfig, TaskType
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
from trl import DPOTrainer

logger = logging.getLogger(__name__)


def run_advanced_dpo(
    model_name: str = "gpt2",
    data_path: str = "data/alignment/preference_dataset.json",
    output_dir: str = "artifacts/models/advanced_dpo",
) -> None:
    """Executes Advanced DPO Training using QLoRA/LoRA for parameter efficiency.
    Optimized for resource constrained environments (keeping Serenity/Eternity pillars).

    Args:
        model_name: Base model ID
        data_path: Path to preference dataset
        output_dir: Directory to save the adapter

    """
    logger.info(f"🚀 [Advanced DPO] Initializing LoRA Strategy for: {model_name}")

    # 1. Load Model & Tokenizer
    model = AutoModelForCausalLM.from_pretrained(model_name, revision="main")  # nosec B615
    tokenizer = AutoTokenizer.from_pretrained(model_name, revision="main")  # nosec B615
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # 2. Configure PEFT (LoRA)
    # Using specific target modules is key for DPO performance
    peft_config = LoraConfig(
        r=16,  # Rank
        lora_alpha=32,  # Alpha
        lora_dropout=0.05,
        bias="none",
        task_type=TaskType.CAUSAL_LM,
        target_modules=[
            "q_proj",
            "v_proj",
            "k_proj",
            "o_proj",
        ],  # Target Attention layers
    )

    # 3. Load Data
    if not os.path.exists(data_path):
        logger.warning(f"⚠️ Data file {data_path} not found.")
        return
    dataset = load_dataset("json", data_files=data_path, revision="main")  # nosec B615
    if "test" not in dataset:
        dataset = dataset["train"].train_test_split(test_size=0.1)

    # 4. Define Advanced Training Arguments
    # Adjusted for LoRA stability
    training_args = TrainingArguments(
        output_dir=output_dir,
        # Strategy
        num_train_epochs=5,  # More epochs for LoRA convergence
        per_device_train_batch_size=8,  # Higher batch allowed due to LoRA
        per_device_eval_batch_size=8,
        gradient_accumulation_steps=2,
        # Optimization
        learning_rate=5e-5,  # Higher LR typical for LoRA (vs 1e-5 for full fine-tune)
        weight_decay=0.005,
        optim="adamw_torch_fused",  # Fused optimizer for speed
        max_grad_norm=0.5,  # Tighter clipping
        warmup_ratio=0.03,  # Shorter warmup
        lr_scheduler_type="cosine",  # Cosine scheduler for better convergence
        # Logistics
        logging_steps=5,
        save_strategy="steps",
        save_steps=50,
        evaluation_strategy="steps",
        eval_steps=25,
        load_best_model_at_end=True,
        metric_for_best_model="loss",  # Use eval_loss if available from DPO
        greater_is_better=False,
        # System
        report_to="tensorboard",
        remove_unused_columns=False,
        run_name="afo_dpo_lora_advanced",
    )

    # 5. Initialize DPO Trainer with PEFT Config
    trainer = DPOTrainer(
        model=model,
        ref_model=None,  # DPO Trainer handles disabling adapters for ref_model implicitly
        args=training_args,
        beta=0.1,
        train_dataset=dataset["train"],
        eval_dataset=dataset["test"],
        tokenizer=tokenizer,
        peft_config=peft_config,  # Pass LoRA config directly
        max_length=1024,  # Longer context
        max_prompt_length=512,
    )

    # 6. Execute Training
    logger.info("⚔️ [Advanced DPO] Starting LoRA-DPO Optimization...")
    trainer.train()

    # 7. Save Adapter
    trainer.save_model(output_dir)
    logger.info(f"✅ [Advanced DPO] Adapter saved to {output_dir}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Running Advanced DPO Module...")
    # run_advanced_dpo_lora()
