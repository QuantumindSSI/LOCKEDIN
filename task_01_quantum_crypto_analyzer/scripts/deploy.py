#!/usr/bin/env python3
"""
Victron edge deployment script for Quantum-Resistant Cryptographic Protocol Analyzer.
Optimizes model for edge deployment with quantization and ONNX export.
"""

import torch
import yaml
from pathlib import Path
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig
)
from peft import PeftModel
from optimum.onnxruntime import ORTModelForCausalLM
import shutil

class VictronDeployer:
    """Deploys fine-tuned model to Victron edge hardware."""
    
    def __init__(self, model_path: str = "models/final"):
        self.model_path = Path(model_path)
        self.output_dir = Path("models/victron_deployment")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load config
        with open("configs/model_config.yaml", 'r') as f:
            self.config = yaml.safe_load(f)
    
    def quantize_model(self) -> Path:
        """
        Quantize model to 4-bit for edge deployment.
        Uses BitsAndBytesConfig for efficient quantization.
        """
        print("Quantizing model for edge deployment...")
        
        # Quantization configuration
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True
        )
        
        # Load base model with quantization
        print("Loading base model with quantization...")
        model = AutoModelForCausalLM.from_pretrained(
            "microsoft/phi-3-mini-4k-instruct",
            quantization_config=quantization_config,
            device_map="auto",
            trust_remote_code=True
        )
        
        # Load LoRA adapter
        print("Loading LoRA adapter...")
        model = PeftModel.from_pretrained(model, self.model_path)
        model = model.merge_and_unload()
        
        # Save quantized model
        quantized_path = self.output_dir / "quantized"
        quantized_path.mkdir(parents=True, exist_ok=True)
        
        print(f"Saving quantized model to {quantized_path}...")
        model.save_pretrained(quantized_path)
        
        # Save tokenizer
        tokenizer = AutoTokenizer.from_pretrained(
            "microsoft/phi-3-mini-4k-instruct",
            trust_remote_code=True
        )
        tokenizer.save_pretrained(quantized_path)
        
        print(f"Quantized model saved to {quantized_path}")
        return quantized_path
    
    def export_to_onnx(self) -> Path:
        """
        Export model to ONNX format for Victron deployment.
        ONNX provides better performance on edge hardware.
        """
        print("Exporting model to ONNX format...")
        
        onnx_path = self.output_dir / "onnx"
        onnx_path.mkdir(parents=True, exist_ok=True)
        
        # Load model
        print("Loading model for ONNX export...")
        model = ORTModelForCausalLM.from_pretrained(
            self.model_path,
            export=True
        )
        
        # Save ONNX model
        print(f"Saving ONNX model to {onnx_path}...")
        model.save_pretrained(onnx_path)
        
        # Save tokenizer
        tokenizer = AutoTokenizer.from_pretrained(
            "microsoft/phi-3-mini-4k-instruct",
            trust_remote_code=True
        )
        tokenizer.save_pretrained(onnx_path)
        
        print(f"ONNX model saved to {onnx_path}")
        return onnx_path
    
    def create_deployment_package(self) -> Path:
        """
        Create complete deployment package for Victron hardware.
        Includes model, tokenizer, and inference script.
        """
        print("Creating deployment package...")
        
        package_path = self.output_dir / "deployment_package"
        package_path.mkdir(parents=True, exist_ok=True)
        
        # Copy quantized model
        quantized_path = self.output_dir / "quantized"
        if quantized_path.exists():
            shutil.copytree(quantized_path, package_path / "model", dirs_exist_ok=True)
        
        # Create inference script
        inference_script = """#!/usr/bin/env python3
\"\"\"
Inference script for Quantum-Resistant Cryptographic Protocol Analyzer.
Optimized for Victron edge deployment.
\"\"\"

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import sys

class CryptoAnalyzer:
    def __init__(self, model_path="./model"):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_path,
            trust_remote_code=True
        )
        
        # Load model
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True
        )
        self.model.eval()
    
    def analyze(self, protocol_description, implementation_code):
        \"\"\"Analyze cryptographic implementation for quantum vulnerabilities.\"\"\"
        
        # Format input
        input_text = f\"\"\"
Protocol: {protocol_description}
Implementation:
{implementation_code}

Analyze this cryptographic implementation for quantum computing vulnerabilities.
\"\"\"
        
        # Tokenize
        inputs = self.tokenizer(
            input_text,
            return_tensors="pt",
            truncation=True,
            max_length=2048
        ).to(self.device)
        
        # Generate
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=200,
                temperature=0.7,
                top_p=0.9,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        # Decode
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return response

if __name__ == "__main__":
    analyzer = CryptoAnalyzer()
    
    # Example usage
    protocol = "RSA-2048 encryption"
    code = "def rsa_encrypt(message, public_key): return pow(message, e, n)"
    
    result = analyzer.analyze(protocol, code)
    print(result)
"""
        
        with open(package_path / "inference.py", 'w') as f:
            f.write(inference_script)
        
        # Create requirements file
        requirements = """torch>=2.0.0
transformers>=4.30.0
peft>=0.5.0
accelerate>=0.20.0
bitsandbytes>=0.41.0
"""
        
        with open(package_path / "requirements.txt", 'w') as f:
            f.write(requirements)
        
        # Create README
        readme = """# Quantum-Resistant Cryptographic Protocol Analyzer - Victron Deployment

## Installation
```bash
pip install -r requirements.txt
```

## Usage
```bash
python inference.py
```

## System Requirements
- RAM: 4GB minimum
- Storage: 8GB
- GPU: Optional (CPU inference supported)
"""
        
        with open(package_path / "README.md", 'w') as f:
            f.write(readme)
        
        print(f"Deployment package created at {package_path}")
        return package_path
    
    def optimize_for_victron(self):
        """
        Complete optimization pipeline for Victron edge deployment.
        """
        print("Starting Victron optimization pipeline...")
        
        # Step 1: Quantize model
        quantized_path = self.quantize_model()
        
        # Step 2: Export to ONNX
        onnx_path = self.export_to_onnx()
        
        # Step 3: Create deployment package
        package_path = self.create_deployment_package()
        
        print("\n=== Victron Optimization Complete ===")
        print(f"Quantized model: {quantized_path}")
        print(f"ONNX model: {onnx_path}")
        print(f"Deployment package: {package_path}")
        
        return {
            "quantized": str(quantized_path),
            "onnx": str(onnx_path),
            "package": str(package_path)
        }

def main():
    """Main deployment pipeline."""
    deployer = VictronDeployer()
    results = deployer.optimize_for_victron()

if __name__ == "__main__":
    main()
