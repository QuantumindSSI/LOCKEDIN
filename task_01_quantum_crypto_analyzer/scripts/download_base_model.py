#!/usr/bin/env python3
"""
Download base model for Task 01 without CLI authentication.
Uses huggingface_hub library directly.
"""

import os
from pathlib import Path
from huggingface_hub import snapshot_download, login
from transformers import AutoModelForCausalLM, AutoTokenizer

def download_model(model_choice="tiny"):
    """Download base model."""
    
    # Model options for different sizes
    models = {
        "tiny": {
            "name": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
            "size": "1.1B",
            "description": "Fastest training, smallest memory footprint"
        },
        "small": {
            "name": "google/gemma-2b-it",
            "size": "2B",
            "description": "Good balance between size and capability"
        },
        "medium": {
            "name": "microsoft/phi-3-mini-4k-instruct",
            "size": "3.8B",
            "description": "Best accuracy, requires more GPU memory"
        }
    }
    
    if model_choice not in models:
        print(f"Invalid choice. Available options: {', '.join(models.keys())}")
        return
    
    model_info = models[model_choice]
    model_name = model_info["name"]
    output_dir = Path(f"models/base_{model_choice}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\nSelected model: {model_name} ({model_info['size']})")
    print(f"Description: {model_info['description']}")
    print(f"Output directory: {output_dir}")
    print(f"\nDownloading {model_name}...")
    print(f"This will take several minutes depending on your connection...")
    
    try:
        # Try downloading without authentication (public model)
        snapshot_download(
            repo_id=model_name,
            local_dir=str(output_dir),
            local_dir_use_symlinks=False,
            resume_download=True
        )
        print(f"✓ Model downloaded successfully to {output_dir}")
        
    except Exception as e:
        print(f"Error downloading model: {e}")
        print("\nTrying alternative method with transformers...")
        
        # Alternative: Use transformers to download
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            cache_dir=str(output_dir),
            trust_remote_code=True
        )
        tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            cache_dir=str(output_dir),
            trust_remote_code=True
        )
        
        # Save to output directory
        model.save_pretrained(output_dir)
        tokenizer.save_pretrained(output_dir)
        print(f"✓ Model downloaded successfully to {output_dir}")

def main():
    """Main download function."""
    print("=" * 60)
    print("Task 01: Downloading Base Model")
    print("=" * 60)
    
    print("\nAvailable model options:")
    print("  1. tiny  - TinyLlama-1.1B (1.1B params) - Fastest training")
    print("  2. small - Gemma-2B (2B params) - Good balance")
    print("  3. medium - Phi-3-mini (3.8B params) - Best accuracy")
    print()
    
    # Get user choice
    choice = input("Enter model choice (tiny/small/medium) [default: tiny]: ").strip().lower()
    if not choice:
        choice = "tiny"
    
    download_model(choice)
    
    print("\n" + "=" * 60)
    print("Download complete!")
    print("=" * 60)
    print(f"\nNext steps:")
    print(f"  1. Update configs/model_config.yaml to use models/base_{choice}")
    print(f"  2. Run: python scripts/train.py")

if __name__ == "__main__":
    main()
