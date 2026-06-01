#!/usr/bin/env python3
"""
Download base model for Task 01 without CLI authentication.
Uses huggingface_hub library directly.
"""

import os
from pathlib import Path
from huggingface_hub import snapshot_download, login
from transformers import AutoModelForCausalLM, AutoTokenizer

def download_model():
    """Download Phi-3 base model."""
    
    model_name = "microsoft/phi-3-mini-4k-instruct"
    output_dir = Path("models/base")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Downloading {model_name}...")
    print(f"This will take several minutes depending on your connection...")
    
    try:
        # Try downloading without authentication (public model)
        snapshot_download(
            repo_id=model_name,
            local_dir=str(output_dir),
            local_dir_use_symlinks=False,
            resume_download=True
        )
        print(f"Model downloaded successfully to {output_dir}")
        
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
        print(f"Model downloaded successfully to {output_dir}")

def main():
    """Main download function."""
    print("=" * 60)
    print("Task 01: Downloading Base Model")
    print("=" * 60)
    
    download_model()
    
    print("\n" + "=" * 60)
    print("Download complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
