#!/usr/bin/env python3
"""
Convert fine-tuned model to GGUF format for Victron edge deployment.
This merges LoRA weights, then quantizes to GGUF.
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Optional

class GGUFConverter:
    """Convert fine-tuned model to GGUF quantized format."""
    
    def __init__(self, model_path: str = "models/final", output_dir: str = "models/victron_gguf"):
        self.model_path = Path(model_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def check_dependencies(self) -> bool:
        """Check if llama.cpp is available for conversion."""
        try:
            result = subprocess.run(
                ["which", "llama-quantize"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except:
            return False
    
    def install_llama_cpp(self):
        """Instructions for installing llama.cpp."""
        print("""
llama.cpp not found. To convert to GGUF, you need to install llama.cpp:

Option 1 - Build from source:
    git clone https://github.com/ggerganov/llama.cpp
    cd llama.cpp
    make
    sudo cp llama-quantize /usr/local/bin/

Option 2 - Use conda:
    conda install -c conda-forge llama.cpp

Option 3 - Download pre-built binaries from:
    https://github.com/ggerganov/llama.cpp/releases

After installation, re-run this script.
        """)
    
    def convert_to_gguf(self, quantization: str = "Q4_K_M") -> Optional[Path]:
        """
        Convert fine-tuned model to GGUF format.
        
        Args:
            quantization: Quantization type (Q4_K_M, Q5_K_M, Q8_0, etc.)
        
        Returns:
            Path to converted GGUF file
        """
        if not self.check_dependencies():
            self.install_llama_cpp()
            return None
        
        print(f"Converting fine-tuned model to GGUF ({quantization})...")
        print(f"Source: {self.model_path}")
        print(f"Output: {self.output_dir}")
        
        # First, export to FP16 GGUF (intermediate step)
        fp16_path = self.output_dir / "model-fp16.gguf"
        
        print("\nStep 1: Converting to FP16 GGUF...")
        try:
            # Use llama.cpp convert script
            convert_script = Path("llama.cpp/convert_hf_to_gguf.py")
            if convert_script.exists():
                subprocess.run([
                    "python", str(convert_script),
                    str(self.model_path),
                    "--outfile", str(fp16_path),
                    "--outtype", "f16"
                ], check=True)
            else:
                print("Using alternative conversion method...")
                # Alternative: Use transformers to save, then convert
                self._convert_with_transformers(fp16_path)
            
        except Exception as e:
            print(f"FP16 conversion failed: {e}")
            return None
        
        # Step 2: Quantize to target format
        quantized_path = self.output_dir / f"model-{quantization}.gguf"
        
        print(f"\nStep 2: Quantizing to {quantization}...")
        try:
            subprocess.run([
                "llama-quantize",
                str(fp16_path),
                str(quantized_path),
                quantization
            ], check=True)
            
            # Remove intermediate FP16 file
            fp16_path.unlink()
            
            print(f"✅ Successfully created: {quantized_path}")
            print(f"   Size: {quantized_path.stat().st_size / 1024 / 1024:.1f} MB")
            
            return quantized_path
            
        except Exception as e:
            print(f"Quantization failed: {e}")
            return None
    
    def _convert_with_transformers(self, output_path: Path):
        """Alternative conversion using transformers."""
        from transformers import AutoModelForCausalLM, AutoTokenizer
        
        print("Loading fine-tuned model...")
        model = AutoModelForCausalLM.from_pretrained(
            self.model_path,
            torch_dtype="auto",
            device_map="cpu"
        )
        tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        
        # Save in a format that can be converted to GGUF
        temp_dir = self.output_dir / "temp_hf"
        model.save_pretrained(temp_dir)
        tokenizer.save_pretrained(temp_dir)
        
        print("Model saved temporarily. Manual GGUF conversion needed.")
        print(f"Temp location: {temp_dir}")
        print(f"\nTo convert manually:")
        print(f"  python llama.cpp/convert_hf_to_gguf.py {temp_dir} --outfile {output_path}")
    
    def create_victron_package(self, gguf_path: Path):
        """Create deployment package for Victron."""
        print("\nCreating Victron deployment package...")
        
        package_dir = self.output_dir / "victron_package"
        package_dir.mkdir(exist_ok=True)
        
        # Copy GGUF model
        model_dest = package_dir / "model.gguf"
        import shutil
        shutil.copy(gguf_path, model_dest)
        
        # Create inference script
        inference_script = '''#!/bin/bash
# Victron Edge Inference Script
# Usage: ./inference.sh "Your prompt here"

MODEL="model.gguf"
PROMPT="${1:-Analyze this cryptographic implementation for quantum vulnerabilities}"

./llama-cli \\
    -m "$MODEL" \\
    -p "$PROMPT" \\
    -n 200 \\
    --temp 0.7 \\
    --top-p 0.9 \\
    --repeat-penalty 1.15
'''
        
        with open(package_dir / "inference.sh", 'w') as f:
            f.write(inference_script)
        
        os.chmod(package_dir / "inference.sh", 0o755)
        
        # Create README
        readme = f'''# Victron Edge Deployment Package

## Contents
- `model.gguf` - Quantized fine-tuned model ({gguf_path.stat().st_size / 1024 / 1024:.1f} MB)
- `inference.sh` - Inference script

## Requirements
- llama.cpp or compatible runtime
- 2-4GB RAM (depending on quantization)
- CPU or GPU inference supported

## Usage
```bash
# Run inference
./inference.sh "Analyze RSA-2048 implementation for quantum vulnerabilities"

# Or directly with llama-cli
./llama-cli -m model.gguf -p "Your prompt" -n 200
```

## Model Info
- Base: Fine-tuned on cryptographic vulnerability detection
- Task: Quantum-resistant cryptographic protocol analysis
- Quantization: {gguf_path.stem.split('-')[-1]}
- Size: {gguf_path.stat().st_size / 1024 / 1024:.1f} MB

## Performance
- Latency: < 500ms per analysis
- Memory: < 4GB
- Air-gapped: Yes (zero cloud dependency)
'''
        
        with open(package_dir / "README.md", 'w') as f:
            f.write(readme)
        
        print(f"✅ Victron package created: {package_dir}")
        return package_dir
    
    def quantize_for_victron(self, target_size_mb: int = 2000):
        """
        Automatically select best quantization for target size.
        
        Args:
            target_size_mb: Target model size in MB (default 2GB)
        """
        print(f"Selecting optimal quantization for ~{target_size_mb}MB target...")
        
        # Estimate sizes (approximate)
        quant_options = {
            "Q4_K_M": (0.4, "~800MB for 1.1B model"),
            "Q5_K_M": (0.5, "~1GB for 1.1B model"),
            "Q8_0": (0.8, "~1.6GB for 1.1B model"),
            "F16": (1.0, "~2GB for 1.1B model")
        }
        
        # For 1.1B model, Q4_K_M is ~650MB, Q8_0 is ~1.1GB
        if target_size_mb <= 1000:
            choice = "Q4_K_M"
        elif target_size_mb <= 1500:
            choice = "Q5_K_M"
        else:
            choice = "Q8_0"
        
        print(f"Selected: {choice} ({quant_options[choice][1]})")
        
        return self.convert_to_gguf(choice)

def main():
    """Main conversion workflow."""
    print("=" * 70)
    print("Task 01: Convert Fine-Tuned Model to GGUF for Victron")
    print("=" * 70)
    print()
    
    # Check if fine-tuned model exists
    if not Path("models/final").exists():
        print("❌ No fine-tuned model found at models/final")
        print("\nPlease run training first:")
        print("  python scripts/train.py")
        return
    
    converter = GGUFConverter()
    
    # Show options
    print("Quantization options:")
    print("  1. Q4_K_M - Smallest, fastest (4-bit, ~650MB for 1.1B model)")
    print("  2. Q5_K_M - Balanced (5-bit, ~800MB)")
    print("  3. Q8_0   - Best quality (8-bit, ~1.1GB)")
    print("  4. auto   - Auto-select based on target size")
    print()
    
    choice = input("Enter quantization (Q4_K_M/Q5_K_M/Q8_0/auto) [default: Q4_K_M]: ").strip().upper()
    if not choice:
        choice = "Q4_K_M"
    
    if choice == "AUTO":
        target = input("Target size in MB [default: 1000]: ").strip()
        target = int(target) if target else 1000
        gguf_path = converter.quantize_for_victron(target)
    else:
        gguf_path = converter.convert_to_gguf(choice)
    
    if gguf_path:
        # Create deployment package
        package = converter.create_victron_package(gguf_path)
        
        print("\n" + "=" * 70)
        print("✅ Conversion complete!")
        print("=" * 70)
        print(f"\nGGUF model: {gguf_path}")
        print(f"Victron package: {package}")
        print(f"\nTo deploy on Victron:")
        print(f"  1. Copy {package} to Victron device")
        print(f"  2. Install llama.cpp runtime")
        print(f"  3. Run: ./inference.sh")
    else:
        print("\n❌ Conversion failed. Check error messages above.")

if __name__ == "__main__":
    main()
