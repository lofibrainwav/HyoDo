# Trinity Score: 90.0 (Established by Chancellor)
"""MlxSage Adapter for AFO Kingdom
Integrates Apple's MLX framework for native optimization of DeepSeek-R1 (Jwaja)
"""

import logging
from typing import Any

# Setup logging
logger = logging.getLogger("afo.scholars.mlx")


class MlxSage:
    """[MLX Sage] Generic MLX Adapter for AFO Kingdom
    Supports dynamic loading of models (Jwaja, Samahwi, etc.) on Apple Silicon.
    Philosophy: 眞(Truth) & 善(Goodness) via Native Performance
    """

    def __init__(self, model_id: str, sage_name: str = "MLX Sage") -> None:
        self.model: Any | None = None
        self.tokenizer: Any | None = None
        self.model_path = model_id
        self.sage_name = sage_name
        self._is_loaded = False

    def load_model(self) -> None:
        """Loads the model into memory. This is heavy operation."""
        if self._is_loaded:
            return

        try:
            from mlx_lm import load

            logger.info(f"🍎 [MLX] Loading native model for {self.sage_name}: {self.model_path}...")
            # Trust remote code is sometimes needed for new architectures, but keeping safe default
            # Validated: load() returns model, tokenizer (and config sometimes?) - Handle extra values
            loaded = load(self.model_path)
            if len(loaded) >= 2:
                self.model = loaded[0]
                self.tokenizer = loaded[1]
            else:
                raise ValueError("Unexpected return from mlx_lm.load")
            self._is_loaded = True
            logger.info(f"✅ [MLX] {self.sage_name} Model loaded successfully.")
        except ImportError:
            logger.error("❌ [MLX] mlx-lm package not found. Please install: pip install mlx-lm")
            raise
        except Exception as e:
            logger.error(f"❌ [MLX] Failed to load model for {self.sage_name}: {e}")
            raise

    def unload_model(self) -> None:
        """Unsets references to allow GC to reclaim memory (if needed)"""
        if not self._is_loaded:
            return

        self.model = None
        self.tokenizer = None
        self._is_loaded = False
        import gc

        gc.collect()
        logger.info(f"🗑️ [MLX] {self.sage_name} Model unloaded.")

    def generate(
        self,
        prompt: str,
        system: str | None = None,
        max_tokens: int = 4096,
        temp: float = 0.6,
    ) -> Any:
        """Generates response using MLX"""
        if not self._is_loaded:
            self.load_model()

        try:
            from mlx_lm import generate
            from mlx_lm.sample_utils import make_sampler

            # Construct full prompt with system instruction if provided
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            # Check if tokenizer has chat template
            if self.tokenizer is not None and hasattr(self.tokenizer, "apply_chat_template"):
                input_prompt = self.tokenizer.apply_chat_template(
                    messages, tokenize=False, add_generation_prompt=True
                )
            else:
                if system:
                    input_prompt = f"System: {system}\nUser: {prompt}\nAssistant:"
                else:
                    input_prompt = f"User: {prompt}\nAssistant:"

            logger.info(f"⚡ [MLX({self.sage_name})] Generating with temp={temp}...")

            # Create sampler
            sampler = make_sampler(temp=temp)

            if self.model is None or self.tokenizer is None:
                raise ValueError("Model or tokenizer not initialized")

            response = generate(
                self.model,
                self.tokenizer,
                prompt=input_prompt,
                max_tokens=max_tokens,
                sampler=sampler,
                verbose=False,
            )
            return response

        except Exception as e:
            logger.error(f"❌ [MLX] Generation failed: {e}")
            return f"MLX Error: {e}"


# Global Instances & Configuration
JWAJA_MODEL_ID = "mlx-community/DeepSeek-R1-Distill-Qwen-14B-4bit"
SAMAHWI_MLX_PATH = (
    "mlx-community/Qwen2.5-Coder-32B-Instruct-4bit"  # [Recruited] Python Expert Model
)

# Default setup
jwaja_sage = MlxSage(JWAJA_MODEL_ID, "Jwaja")
samahwi_sage = MlxSage(SAMAHWI_MLX_PATH, "Samahwi")
