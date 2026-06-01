#!/usr/bin/env python3
"""
Training script using Unsloth for 2x faster training and 70% less memory.
Unsloth is optimized for fast LoRA fine-tuning on consumer GPUs.
"""

import json
import torch
from pathlib import Path
from typing import Dict, List
from datasets import Dataset
from transformers import TrainingArguments
from trl import SFTTrainer

# Unsloth imports
try:
    from unsloth import FastLanguageModel
    from unsloth import is_bfloat16_supported
    UNSLOTH_AVAILABLE = True
except ImportError:
    print("Unsloth not installed. Install with: pip install unsloth")
    print("Falling back to standard training...")
    UNSLOTH_AVAILABLE = False
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import LoraConfig, get_peft_model

class UnslothTrainer:
    """Fast training using Unsloth library."""
    
    def __init__(
        self,
        model_name: str = "unsloth/tinyllama-bnb-4bit",  # Pre-quantized by Unsloth
        max_seq_length: int = 2048,
        dtype=None,  # Auto-detect
        load_in_4bit: bool = True
    ):
        self.model_name = model_name
        self.max_seq_length = max_seq_length
        self.dtype = dtype
        self.load_in_4bit = load_in_4bit
        
        # Default LoRA config for Unsloth (optimized)
        self.lora_config = {
            "r": 16,
            "target_modules": [
                "q_proj", "k_proj", "v_proj", "o_proj",
                "gate_proj", "up_proj", "down_proj",
            ],
            "lora_alpha": 16,
            "lora_dropout": 0,
            "bias": "none",
            "use_gradient_checkpointing": True,
            "random_state": 3407,
            "use_rslora": False,  # Use rank-stabilized LoRA
            "loftq_config": None,
        }
    
    def load_model(self):
        """Load model with Unsloth optimizations."""
        print(f"Loading model with Unsloth: {self.model_name}")
        
        if not UNSLOTH_AVAILABLE:
            # Fallback to standard loading
            return self._load_standard()
        
        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=self.model_name,
            max_seq_length=self.max_seq_length,
            dtype=self.dtype,
            load_in_4bit=self.load_in_4bit,
            token=None,  # Add HF token if using gated models
        )
        
        return model, tokenizer
    
    def _load_standard(self):
        """Fallback standard loading."""
        model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True
        )
        tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
            trust_remote_code=True
        )
        
        # Apply LoRA
        lora_config = LoraConfig(
            r=self.lora_config["r"],
            lora_alpha=self.lora_config["lora_alpha"],
            target_modules=self.lora_config["target_modules"],
            lora_dropout=self.lora_config["lora_dropout"],
            bias=self.lora_config["bias"],
            task_type="CAUSAL_LM"
        )
        model = get_peft_model(model, lora_config)
        
        return model, tokenizer
    
    def apply_lora(self, model):
        """Apply LoRA adapters with Unsloth."""
        if not UNSLOTH_AVAILABLE:
            return model
        
        model = FastLanguageModel.get_peft_model(
            model,
            r=self.lora_config["r"],
            target_modules=self.lora_config["target_modules"],
            lora_alpha=self.lora_config["lora_alpha"],
            lora_dropout=self.lora_config["lora_dropout"],
            bias=self.lora_config["bias"],
            use_gradient_checkpointing=self.lora_config["use_gradient_checkpointing"],
            random_state=self.lora_config["random_state"],
            use_rslora=self.lora_config["use_rslora"],
            loftq_config=self.lora_config["loftq_config"],
        )
        
        return model
    
    def format_prompt(self, examples):
        """Format dataset for training."""
        texts = []
        for example in examples["text"]:
            # Unsloth uses specific chat template format
            text = f"""Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
Analyze the following cryptographic implementation and determine if it is vulnerable to quantum computing attacks.

### Input:
{example}

### Response:
"""
            texts.append(text)
        return {"text": texts}
    
    def load_dataset(self, data_path: str = "data/processed/train.json") -> Dataset:
        """Load and format dataset."""
        print(f"Loading dataset from {data_path}")
        
        with open(data_path, 'r') as f:
            data = json.load(f)
        
        dataset = Dataset.from_list(data)
        
        # Format for training
        dataset = dataset.map(self.format_prompt, batched=True)
        
        print(f"Loaded {len(dataset)} training samples")
        return dataset
    
    def train(
        self,
        output_dir: str = "models/unsloth_finetuned",
        num_train_epochs: int = 3,
        per_device_train_batch_size: int = 2,
        gradient_accumulation_steps: int = 4,
        learning_rate: float = 2e-4,
        warmup_steps: int = 5,
        max_steps: int = -1,
        logging_steps: int = 1,
        save_steps: int = 50,
    ):
        """Train the model with Unsloth."""
        
        # Load model
        model, tokenizer = self.load_model()
        model = self.apply_lora(model)
        
        # Load dataset
        train_dataset = self.load_dataset("data/processed/train.json")
        
        # Training arguments optimized for Unsloth
        # Fix: use either max_steps OR num_train_epochs, not both
        if max_steps > 0:
            # Use max_steps
            training_args = TrainingArguments(
                per_device_train_batch_size=per_device_train_batch_size,
                gradient_accumulation_steps=gradient_accumulation_steps,
                warmup_steps=warmup_steps,
                max_steps=max_steps,
                learning_rate=learning_rate,
                fp16=not is_bfloat16_supported() if UNSLOTH_AVAILABLE else True,
                bf16=is_bfloat16_supported() if UNSLOTH_AVAILABLE else False,
                logging_steps=logging_steps,
                optim="adamw_8bit" if UNSLOTH_AVAILABLE else "adamw_torch",
                weight_decay=0.01,
                lr_scheduler_type="linear",
                seed=3407,
                output_dir=output_dir,
                save_steps=save_steps,
                save_total_limit=2,
                report_to="none",
            )
        else:
            # Use num_train_epochs
            training_args = TrainingArguments(
                per_device_train_batch_size=per_device_train_batch_size,
                gradient_accumulation_steps=gradient_accumulation_steps,
                warmup_steps=warmup_steps,
                num_train_epochs=num_train_epochs,
                learning_rate=learning_rate,
                fp16=not is_bfloat16_supported() if UNSLOTH_AVAILABLE else True,
                bf16=is_bfloat16_supported() if UNSLOTH_AVAILABLE else False,
                logging_steps=logging_steps,
                optim="adamw_8bit" if UNSLOTH_AVAILABLE else "adamw_torch",
                weight_decay=0.01,
                lr_scheduler_type="linear",
                seed=3407,
                output_dir=output_dir,
                save_steps=save_steps,
                save_total_limit=2,
                report_to="none",
            )
        
        # Tokenize dataset for training
        def tokenize_function(examples):
            return tokenizer(
                examples["text"],
                truncation=True,
                max_length=self.max_seq_length,
                padding="max_length",
            )
        
        train_dataset = train_dataset.map(tokenize_function, batched=True)
        
        # Data collator
        from transformers import DataCollatorForLanguageModeling
        data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)
        
        # Initialize trainer (newer trl API uses data collator)
        try:
            # Try new API signature
            trainer = SFTTrainer(
                model=model,
                args=training_args,
                train_dataset=train_dataset,
                data_collator=data_collator,
            )
        except Exception as e1:
            print(f"New API failed: {e1}")
            try:
                # Try with tokenizer/processing_class
                trainer = SFTTrainer(
                    model=model,
                    args=training_args,
                    train_dataset=train_dataset,
                    tokenizer=tokenizer,
                    max_seq_length=self.max_seq_length,
                )
            except Exception as e2:
                print(f"Fallback 1 failed: {e2}")
                # Final fallback - basic Trainer
                from transformers import Trainer
                trainer = Trainer(
                    model=model,
                    args=training_args,
                    train_dataset=train_dataset,
                    data_collator=data_collator,
                )
        
        # Train
        print("\n" + "="*60)
        print("Starting training with Unsloth optimizations")
        print("="*60)
        
        # Show GPU stats
        gpu_stats = torch.cuda.get_device_properties(0)
        start_gpu_memory = round(torch.cuda.max_memory_reserved() / 1024 / 1024 / 1024, 3)
        print(f"GPU: {gpu_stats.name}")
        print(f"Max memory: {round(gpu_stats.total_memory / 1024 / 1024 / 1024, 3)} GB")
        print(f"Reserved memory: {start_gpu_memory} GB")
        print()
        
        trainer_stats = trainer.train()
        
        # Show training stats
        used_memory = round(torch.cuda.max_memory_reserved() / 1024 / 1024 / 1024, 3)
        used_memory_for_lora = round(used_memory - start_gpu_memory, 3)
        print(f"\nTraining completed!")
        print(f"Peak memory usage: {used_memory} GB")
        print(f"Memory used for training: {used_memory_for_lora} GB")
        print(f"Training time: {trainer_stats.metrics['train_runtime']} seconds")
        
        # Save model
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        if UNSLOTH_AVAILABLE:
            # Unsloth optimized saving
            model.save_pretrained_merged(
                str(output_path / "merged"),
                tokenizer,
                save_method="merged_16bit",
            )
            model.save_pretrained_merged(
                str(output_path / "gguf"),
                tokenizer,
                save_method="merged_4bit_forced",
            )
            model.save_pretrained_gguf(
                str(output_path / "model"),
                tokenizer,
                quantization_method="q4_k_m",
            )
        else:
            # Standard saving
            model.save_pretrained(output_path)
            tokenizer.save_pretrained(output_path)
        
        print(f"\nModel saved to: {output_path}")
        
        return model, tokenizer

def main():
    """Main training function."""
    print("=" * 60)
    print("Task 01: Training with Unsloth (2x Faster)")
    print("=" * 60)
    
    # Check Unsloth availability
    if UNSLOTH_AVAILABLE:
        print("✓ Unsloth available - using optimized training")
    else:
        print("⚠ Unsloth not available - using standard training")
        print("Install Unsloth for 2x faster training:")
        print("  pip install unsloth")
    
    print()
    
    # Model options for Unsloth
    print("Available Unsloth models (pre-quantized):")
    print("  1. unsloth/tinyllama-bnb-4bit (1.1B, fastest)")
    print("  2. unsloth/Phi-3-mini-4k-instruct (3.8B, best quality)")
    print("  3. unsloth/gemma-2-2b-it (2B, balanced)")
    print()
    
    # Default to tiny for fast iteration
    model_name = "unsloth/tinyllama-bnb-4bit"
    
    # Initialize trainer
    trainer = UnslothTrainer(
        model_name=model_name,
        max_seq_length=2048,
        dtype=None,
        load_in_4bit=True
    )
    
    # Train
    model, tokenizer = trainer.train(
        output_dir="models/unsloth_finetuned",
        num_train_epochs=3,
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        learning_rate=2e-4,
    )
    
    print("\n" + "=" * 60)
    print("Training complete!")
    print("=" * 60)
    
    if UNSLOTH_AVAILABLE:
        print("\nOutput files:")
        print("  - models/unsloth_finetuned/merged/ (16-bit merged model)")
        print("  - models/unsloth_finetuned/model-Q4_K_M.gguf (4-bit GGUF for Victron)")
        print("\nThe GGUF file is ready for Victron deployment!")
    else:
        print("\nRun convert_to_gguf.py to create Victron deployment package")

if __name__ == "__main__":
    main()
