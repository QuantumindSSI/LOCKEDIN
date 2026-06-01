#!/usr/bin/env python3
"""
Download quantized models for Task 01 - optimized for Victron edge deployment.
Supports GGUF format (4-bit, 5-bit, 8-bit quantization) for minimal memory footprint.
"""

import os
from pathlib import Path
from huggingface_hub import hf_hub_download, list_repo_files
from typing import List, Optional

class QuantizedModelDownloader:
    """Download quantized models in GGUF format for edge deployment."""
    
    def __init__(self):
        self.output_dir = Path("models/base_quantized")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def list_available_quantized_models(self) -> dict:
        """List available quantized model options."""
        return {
            "tiny-4bit": {
                "repo": "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF",
                "file": "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
                "size": "~650MB",
                "bits": 4,
                "description": "TinyLlama 4-bit - Fastest inference, smallest size"
            },
            "tiny-5bit": {
                "repo": "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF",
                "file": "tinyllama-1.1b-chat-v1.0.Q5_K_M.gguf",
                "size": "~800MB",
                "bits": 5,
                "description": "TinyLlama 5-bit - Better quality, still small"
            },
            "tiny-8bit": {
                "repo": "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF",
                "file": "tinyllama-1.1b-chat-v1.0.Q8_0.gguf",
                "size": "~1.1GB",
                "bits": 8,
                "description": "TinyLlama 8-bit - Best quality, larger size"
            },
            "phi3-4bit": {
                "repo": "bartowski/Phi-3-mini-4k-instruct-GGUF",
                "file": "Phi-3-mini-4k-instruct-Q4_K_M.gguf",
                "size": "~2.3GB",
                "bits": 4,
                "description": "Phi-3 4-bit - Good balance for Victron"
            },
            "gemma2-4bit": {
                "repo": "bartowski/gemma-2-2b-it-GGUF",
                "file": "gemma-2-2b-it-Q4_K_M.gguf",
                "size": "~1.6GB",
                "bits": 4,
                "description": "Gemma 2 2B 4-bit - Google's efficient model"
            }
        }
    
    def download_model(self, model_key: str) -> Optional[Path]:
        """Download a specific quantized model."""
        models = self.list_available_quantized_models()
        
        if model_key not in models:
            print(f"❌ Invalid model key: {model_key}")
            print(f"Available: {', '.join(models.keys())}")
            return None
        
        model_info = models[model_key]
        repo_id = model_info["repo"]
        filename = model_info["file"]
        
        print(f"\n📥 Downloading {model_key}")
        print(f"   Model: {repo_id}")
        print(f"   File: {filename}")
        print(f"   Size: {model_info['size']}")
        print(f"   Quantization: {model_info['bits']}-bit")
        print()
        
        try:
            # Download the GGUF file
            downloaded_path = hf_hub_download(
                repo_id=repo_id,
                filename=filename,
                local_dir=str(self.output_dir),
                local_dir_use_symlinks=False,
                resume_download=True
            )
            
            output_file = self.output_dir / f"{model_key}.gguf"
            Path(downloaded_path).rename(output_file)
            
            print(f"✅ Downloaded successfully: {output_file}")
            print(f"   Size: {output_file.stat().st_size / 1024 / 1024:.1f} MB")
            
            return output_file
            
        except Exception as e:
            print(f"❌ Error downloading model: {e}")
            return None
    
    def download_for_victron(self) -> Path:
        """Download the recommended model for Victron edge deployment."""
        print("=" * 60)
        print("Victron Edge Deployment - Quantized Model Download")
        print("=" * 60)
        print()
        print("Recommended for Victron:")
        print("  → tiny-4bit: Best for memory-constrained edge devices")
        print("  → phi3-4bit: Best balance of quality and size")
        print()
        
        # Try recommended model first
        model_path = self.download_model("phi3-4bit")
        if model_path:
            return model_path
        
        # Fallback to tiny
        print("\n⚠️  Phi-3 download failed, trying TinyLlama...")
        model_path = self.download_model("tiny-4bit")
        return model_path
    
    def create_model_info_file(self, model_key: str, model_path: Path):
        """Create info file about the downloaded model."""
        models = self.list_available_quantized_models()
        model_info = models[model_key]
        
        info_file = self.output_dir / "model_info.json"
        import json
        
        info = {
            "model_key": model_key,
            "repo_id": model_info["repo"],
            "filename": model_info["file"],
            "quantization_bits": model_info["bits"],
            "size_mb": model_path.stat().st_size / 1024 / 1024,
            "format": "GGUF",
            "vram_requirements": {
                "4bit": "~4GB VRAM",
                "5bit": "~5GB VRAM",
                "8bit": "~8GB VRAM"
            }
        }
        
        with open(info_file, 'w') as f:
            json.dump(info, f, indent=2)
        
        print(f"📄 Model info saved: {info_file}")

def main():
    """Main download function."""
    downloader = QuantizedModelDownloader()
    
    print("=" * 60)
    print("Task 01: Downloading Quantized Model (GGUF)")
    print("=" * 60)
    print()
    
    # Show available models
    models = downloader.list_available_quantized_models()
    print("Available quantized models:")
    for key, info in models.items():
        print(f"  {key:12} - {info['size']:>8} ({info['bits']}-bit) - {info['description']}")
    print()
    
    # Get user choice
    print("For Victron edge deployment, 'tiny-4bit' or 'phi3-4bit' are recommended.")
    choice = input("Enter model choice [default: phi3-4bit]: ").strip().lower()
    if not choice:
        choice = "phi3-4bit"
    
    # Download
    model_path = downloader.download_model(choice)
    
    if model_path:
        downloader.create_model_info_file(choice, model_path)
        
        print("\n" + "=" * 60)
        print("✅ Download complete!")
        print("=" * 60)
        print(f"\nModel location: {model_path}")
        print(f"\nFor inference with llama.cpp or similar:")
        print(f"  ./main -m {model_path} -p \"Your prompt here\"")
        print(f"\nFor fine-tuning, use the regular (non-quantized) model.")
        print("This quantized model is for inference/deployment only.")
    else:
        print("\n❌ Download failed. Please try a different model.")

if __name__ == "__main__":
    main()
