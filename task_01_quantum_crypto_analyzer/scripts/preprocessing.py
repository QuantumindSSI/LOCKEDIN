#!/usr/bin/env python3
"""
Data preprocessing pipeline for Quantum-Resistant Cryptographic Protocol Analyzer.
Converts raw data into training format for fine-tuning.
"""

import json
import base64
from pathlib import Path
from typing import List, Dict, Tuple
from sklearn.model_selection import train_test_split
import re

class CryptoDataPreprocessor:
    """Preprocesses cryptographic vulnerability data for training."""
    
    def __init__(self, raw_data_dir: str = "data/raw", output_dir: str = "data/processed"):
        self.raw_data_dir = Path(raw_data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def load_raw_data(self) -> List[Dict]:
        """Load raw data from merged file."""
        raw_file = self.raw_data_dir / "merged_crypto_vulnerability_data.json"
        
        with open(raw_file, 'r') as f:
            data = json.load(f)
        
        print(f"Loaded {len(data)} samples from {raw_file}")
        return data
    
    def decode_base64_code(self, encoded_code: str) -> str:
        """Decode base64 encoded code snippets."""
        try:
            return base64.b64decode(encoded_code).decode()
        except:
            return "# Decoding error"
    
    def format_for_training(self, sample: Dict) -> Dict:
        """
        Format a single sample for training.
        Creates instruction-following format for fine-tuning.
        """
        # Decode the implementation code
        code = self.decode_base64_code(sample.get('implementation_code', ''))
        
        # Create instruction
        instruction = (
            "Analyze the following cryptographic implementation and determine if it is "
            "vulnerable to quantum computing attacks. Identify the vulnerability type "
            "and quantum attack vector if applicable."
        )
        
        # Create input
        input_text = (
            f"Protocol: {sample['protocol_description']}\n"
            f"Type: {sample.get('algorithm_type', sample.get('affected_protocol', 'Unknown'))}\n"
            f"Implementation:\n{code}"
        )
        
        # Create output with enhanced information
        output_parts = [
            f"Vulnerability Type: {sample['vulnerability_type']}",
            f"Quantum Attack Vector: {sample['quantum_attack_vector']}",
            f"Severity: {sample['severity']}",
            f"Description: {sample.get('description', 'Cryptographic implementation analysis')}"
        ]
        
        # Add optional metadata if present
        if 'cve_id' in sample:
            output_parts.append(f"CVE Reference: {sample['cve_id']}")
        if 'confidence_score' in sample:
            output_parts.append(f"Confidence: {sample['confidence_score']:.2f}")
        if 'pattern_type' in sample:
            output_parts.append(f"Pattern: {sample['pattern_type']}")
        if 'framework' in sample and sample['framework']:
            output_parts.append(f"Framework: {sample['framework']}")
        
        output_text = "\n".join(output_parts)
        
        # Build enriched sample with metadata
        result = {
            "instruction": instruction,
            "input": input_text,
            "output": output_text,
            "label": 1 if sample['vulnerability_type'] == 'quantum_vulnerable' else 0,
            "metadata": {
                "source": sample.get('source', 'unknown'),
                "confidence_score": sample.get('confidence_score', 0.5),
                "is_negative_example": sample.get('is_negative_example', False),
                "is_adversarial_example": sample.get('is_adversarial_example', False),
                "obfuscation_level": sample.get('obfuscation_level', 'none'),
                "code_length_category": sample.get('code_length_category', 'unknown'),
                "algorithm_type": sample.get('algorithm_type', 'unknown'),
                "severity": sample.get('severity', 'unknown')
            }
        }
        
        return result
    
    def preprocess_dataset(self, data: List[Dict]) -> List[Dict]:
        """Preprocess entire dataset."""
        print("Preprocessing dataset...")
        
        processed_data = []
        for sample in data:
            formatted = self.format_for_training(sample)
            processed_data.append(formatted)
        
        print(f"Preprocessed {len(processed_data)} samples")
        return processed_data
    
    def split_dataset(self, data: List[Dict], 
                      train_ratio: float = 0.8,
                      val_ratio: float = 0.1,
                      test_ratio: float = 0.1) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """Split dataset into train, validation, and test sets."""
        print("Splitting dataset...")
        
        # First split: train + val vs test
        train_val, test = train_test_split(
            data, 
            test_size=test_ratio, 
            random_state=42,
            stratify=[d['label'] for d in data]
        )
        
        # Second split: train vs val
        val_size = val_ratio / (train_ratio + val_ratio)
        train, val = train_test_split(
            train_val,
            test_size=val_size,
            random_state=42,
            stratify=[d['label'] for d in train_val]
        )
        
        print(f"Train: {len(train)} samples")
        print(f"Validation: {len(val)} samples")
        print(f"Test: {len(test)} samples")
        
        return train, val, test
    
    def save_processed_data(self, data: List[Dict], filename: str):
        """Save processed data to file."""
        output_file = self.output_dir / filename
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Saved {len(data)} samples to {output_file}")
    
    def create_huggingface_format(self, data: List[Dict]) -> List[Dict]:
        """
        Convert to Hugging Face dataset format.
        Combine instruction, input, and output into a single text field.
        """
        hf_data = []
        for sample in data:
            # Format as conversation
            text = (
                f"### Instruction:\n{sample['instruction']}\n\n"
                f"### Input:\n{sample['input']}\n\n"
                f"### Response:\n{sample['output']}"
            )
            
            # Include metadata in HuggingFace format
            hf_sample = {
                "text": text,
                "label": sample['label']
            }
            
            # Add metadata if present
            if 'metadata' in sample:
                hf_sample['metadata'] = sample['metadata']
            
            hf_data.append(hf_sample)
        
        return hf_data
    
    def analyze_dataset(self, data: List[Dict]):
        """Analyze dataset statistics with enhanced metrics."""
        print("\n" + "="*60)
        print("PROCESSED DATASET ANALYSIS")
        print("="*60)
        
        # Count labels
        vulnerable_count = sum(1 for d in data if d['label'] == 1)
        resistant_count = sum(1 for d in data if d['label'] == 0)
        
        print(f"\nTotal samples: {len(data)}")
        print(f"Quantum-vulnerable: {vulnerable_count} ({vulnerable_count/len(data)*100:.1f}%)")
        print(f"Quantum-resistant: {resistant_count} ({resistant_count/len(data)*100:.1f}%)")
        
        # Average text length
        avg_length = sum(len(d.get('text', '')) for d in data) / len(data)
        print(f"Average text length: {avg_length:.0f} characters")
        
        # Metadata analysis if available
        samples_with_metadata = [d for d in data if 'metadata' in d]
        if samples_with_metadata:
            print("\n--- Metadata Analysis ---")
            
            # By source
            sources = {}
            for d in samples_with_metadata:
                src = d['metadata'].get('source', 'unknown')
                sources[src] = sources.get(src, 0) + 1
            print("\nBy source:")
            for src, count in sorted(sources.items(), key=lambda x: -x[1])[:5]:
                print(f"  - {src}: {count} samples")
            
            # Confidence score distribution
            confidence_scores = [d['metadata'].get('confidence_score', 0.5) for d in samples_with_metadata]
            if confidence_scores:
                avg_conf = sum(confidence_scores) / len(confidence_scores)
                high_conf = sum(1 for c in confidence_scores if c >= 0.85)
                print(f"\nConfidence scores:")
                print(f"  - Average: {avg_conf:.2f}")
                print(f"  - High confidence (>=0.85): {high_conf} ({high_conf/len(confidence_scores)*100:.1f}%)")
            
            # Special categories
            neg_count = sum(1 for d in samples_with_metadata if d['metadata'].get('is_negative_example', False))
            adv_count = sum(1 for d in samples_with_metadata if d['metadata'].get('is_adversarial_example', False))
            if neg_count > 0:
                print(f"  - Negative examples: {neg_count}")
            if adv_count > 0:
                print(f"  - Adversarial examples: {adv_count}")
        
        print("="*60)
    
    def run_pipeline(self):
        """Run complete preprocessing pipeline."""
        print("Starting preprocessing pipeline...")
        
        # Load raw data
        raw_data = self.load_raw_data()
        
        # Preprocess
        processed_data = self.preprocess_dataset(raw_data)
        
        # Split dataset
        train, val, test = self.split_dataset(processed_data)
        
        # Convert to Hugging Face format
        train_hf = self.create_huggingface_format(train)
        val_hf = self.create_huggingface_format(val)
        test_hf = self.create_huggingface_format(test)
        
        # Save processed data
        self.save_processed_data(train_hf, "train.json")
        self.save_processed_data(val_hf, "validation.json")
        self.save_processed_data(test_hf, "test.json")
        
        # Analyze
        self.analyze_dataset(train_hf)
        
        print("\nPreprocessing pipeline complete!")

def main():
    """Main preprocessing pipeline."""
    preprocessor = CryptoDataPreprocessor()
    preprocessor.run_pipeline()

if __name__ == "__main__":
    main()
