# Implementation Guide: Task 01 - Quantum-Resistant Cryptographic Protocol Analyzer

## Overview
This guide provides step-by-step instructions for implementing the Quantum-Resistant Cryptographic Protocol Analyzer, the highest-priority fine-tuning task for QuantumIndSSI.

## Prerequisites

### Hardware Requirements
- **Training**: NVIDIA RTX 3060 or equivalent (8GB+ VRAM)
- **Deployment**: Victron edge hardware (4GB+ RAM)
- **Storage**: 20GB available space

### Software Requirements
- Python 3.8+
- CUDA 11.8+ (for GPU training)
- Git

## Step-by-Step Implementation

### Step 1: Environment Setup

```bash
# Navigate to project directory
cd task_01_quantum_crypto_analyzer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Data Collection

```bash
# Run data collection pipeline
python scripts/data_collection.py
```

**Expected Output:**
- `data/raw/nist_pqc_submissions.json` - 800 NIST PQC samples
- `data/raw/cve_cryptographic_vulnerabilities.json` - 150 CVE samples
- `data/raw/quantum_cryptanalysis_papers.json` - 90 quantum attack samples
- `data/raw/merged_crypto_vulnerability_data.json` - 1,040 total samples

### Step 3: Data Preprocessing

```bash
# Run preprocessing pipeline
python scripts/preprocessing.py
```

**Expected Output:**
- `data/processed/train.json` - 832 training samples
- `data/processed/validation.json` - 104 validation samples
- `data/processed/test.json` - 104 test samples

### Step 4: Download Base Model

```bash
# Download Phi-3 model
huggingface-cli download microsoft/phi-3-mini-4k-instruct --local-dir models/base
```

**Alternative:**
```python
from huggingface_hub import snapshot_download
snapshot_download(repo_id="microsoft/phi-3-mini-4k-instruct", local_dir="models/base")
```

### Step 5: Training

```bash
# Run training script
python scripts/train.py
```

**Training Parameters:**
- Epochs: 3
- Batch size: 4
- Learning rate: 2e-4
- LoRA rank: 16
- LoRA alpha: 32

**Expected Training Time:**
- With RTX 3060: ~2-3 hours
- With RTX 4090: ~45-60 minutes

**Output:**
- `models/checkpoints/` - Training checkpoints
- `models/final/` - Final fine-tuned model
- `models/final/eval_results.json` - Evaluation metrics

### Step 6: Evaluation

```bash
# Run evaluation script
python scripts/evaluate.py
```

**Expected Metrics:**
- Accuracy: > 90%
- Precision: > 85%
- Recall: > 88%
- F1 Score: > 86%
- Latency: < 500ms
- Memory: < 4GB

### Step 7: Victron Deployment

```bash
# Run deployment script
python scripts/deploy.py
```

**Output:**
- `models/victron_deployment/quantized/` - 4-bit quantized model
- `models/victron_deployment/onnx/` - ONNX exported model
- `models/victron_deployment/deployment_package/` - Complete deployment package

### Step 8: Hugging Face Upload

```bash
# Login to Hugging Face
huggingface-cli login

# Run upload script
python scripts/upload_to_huggingface.py
```

**Output:**
- Model uploaded to: https://huggingface.co/quantumindssi/01_quantum_resistant_crypto_analyzer
- Model card with comprehensive documentation
- Evaluation results included

## Configuration Files

### LoRA Configuration (`configs/lora_config.yaml`)
- Rank: 16
- Alpha: 32
- Target modules: q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj
- Dropout: 0.05

### Training Arguments (`configs/training_args.yaml`)
- Output directory: ./models/checkpoints
- Epochs: 3
- Batch size: 4
- Learning rate: 2e-4
- Warmup steps: 100
- FP16: enabled

### Model Configuration (`configs/model_config.yaml`)
- Base model: microsoft/phi-3-mini-4k-instruct
- Quantization: 4-bit NF4
- Target latency: 500ms
- Target memory: 4GB

## Troubleshooting

### Out of Memory Error
**Solution:** Reduce batch size in `configs/training_args.yaml` or use gradient checkpointing.

### Slow Training
**Solution:** Enable mixed precision (FP16) and increase batch size if GPU memory allows.

### Poor Evaluation Metrics
**Solution:** 
- Increase training epochs
- Adjust learning rate
- Add more training data
- Review data quality

### Deployment Issues
**Solution:** Use QLoRA (4-bit quantization) for edge deployment to reduce memory footprint.

## Next Steps

After completing Task 01, proceed to:
1. **Task 02**: Post-Quantum Key Migration Advisor
2. **Task 17**: Sovereign Threat Intelligence Analyzer
3. **Task 08**: HIPAA-Compliant Clinical Note Summarizer

## Success Criteria

Task 01 is considered successful when:
- ✓ Accuracy > 90% on NIST PQC vulnerability detection
- ✓ Latency < 500ms per analysis
- ✓ Memory < 4GB
- ✓ Model uploaded to Hugging Face
- ✓ Victron deployment package created
- ✓ Comprehensive documentation completed

## Contact

For questions or issues:
- Email: contact@quantumindssi.com
- GitHub: https://github.com/QuantumindSSI
- Website: https://quantumindssi.com

---

**QuantumIndSSI Ltd · The Sovereign AI Lab**
*London · United Kingdom · Intelligence Without Compromise*
