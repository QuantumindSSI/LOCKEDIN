#!/usr/bin/env python3
"""
Evaluation script for Quantum-Resistant Cryptographic Protocol Analyzer.
Computes accuracy, precision, recall, F1, and edge deployment metrics.
"""

import json
import torch
import time
import yaml
from pathlib import Path
from typing import Dict, List, Tuple
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix
import numpy as np

class CryptoModelEvaluator:
    """Evaluates the fine-tuned crypto vulnerability detection model."""
    
    def __init__(self, model_path: str = "models/final"):
        self.model_path = Path(model_path)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Load model and tokenizer
        print(f"Loading model from {model_path}...")
        self.tokenizer = AutoTokenizer.from_pretrained(
            "microsoft/phi-3-mini-4k-instruct",
            trust_remote_code=True
        )
        
        base_model = AutoModelForCausalLM.from_pretrained(
            "microsoft/phi-3-mini-4k-instruct",
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True
        )
        
        self.model = PeftModel.from_pretrained(base_model, model_path)
        self.model = self.model.merge_and_unload()
        self.model.eval()
        
        print("Model loaded successfully")
    
    def load_test_data(self, data_path: str = "data/processed/test.json") -> List[Dict]:
        """Load test dataset."""
        with open(data_path, 'r') as f:
            data = json.load(f)
        print(f"Loaded {len(data)} test samples")
        return data
    
    def predict_vulnerability(self, text: str) -> Tuple[str, float]:
        """
        Predict if a cryptographic implementation is quantum-vulnerable.
        Returns: (prediction, confidence)
        """
        # Tokenize input
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=2048
        ).to(self.device)
        
        # Generate response
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=200,
                temperature=0.7,
                top_p=0.9,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        # Decode response
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract prediction from response
        if "quantum_vulnerable" in response.lower():
            prediction = "quantum_vulnerable"
        elif "quantum_resistant" in response.lower():
            prediction = "quantum_resistant"
        else:
            prediction = "unknown"
        
        # Simple confidence based on response length (placeholder)
        confidence = min(1.0, len(response) / 100.0)
        
        return prediction, confidence
    
    def evaluate_classification(self, test_data: List[Dict]) -> Dict:
        """Evaluate classification performance."""
        print("\nEvaluating classification performance...")
        
        predictions = []
        true_labels = []
        
        for sample in test_data:
            # Get true label
            true_label = "quantum_vulnerable" if sample['label'] == 1 else "quantum_resistant"
            true_labels.append(true_label)
            
            # Get prediction
            pred, _ = self.predict_vulnerability(sample['text'])
            predictions.append(pred)
        
        # Compute metrics
        accuracy = accuracy_score(true_labels, predictions)
        precision, recall, f1, _ = precision_recall_fscore_support(
            true_labels, predictions, average='weighted'
        )
        
        # Confusion matrix
        cm = confusion_matrix(true_labels, predictions, labels=["quantum_resistant", "quantum_vulnerable"])
        
        results = {
            "accuracy": float(accuracy),
            "precision": float(precision),
            "recall": float(recall),
            "f1": float(f1),
            "confusion_matrix": cm.tolist()
        }
        
        print(f"Accuracy: {accuracy:.4f}")
        print(f"Precision: {precision:.4f}")
        print(f"Recall: {recall:.4f}")
        print(f"F1 Score: {f1:.4f}")
        print(f"Confusion Matrix:\n{cm}")
        
        return results
    
    def evaluate_edge_metrics(self, test_data: List[Dict], num_samples: int = 100) -> Dict:
        """Evaluate edge deployment metrics (latency, memory, energy)."""
        print("\nEvaluating edge deployment metrics...")
        
        # Latency
        latencies = []
        for i, sample in enumerate(test_data[:num_samples]):
            start = time.time()
            self.predict_vulnerability(sample['text'])
            latency = time.time() - start
            latencies.append(latency)
        
        avg_latency = np.mean(latencies) * 1000  # Convert to ms
        p95_latency = np.percentile(latencies, 95) * 1000
        p99_latency = np.percentile(latencies, 99) * 1000
        
        # Memory usage
        if torch.cuda.is_available():
            memory_allocated = torch.cuda.memory_allocated() / 1024**3  # GB
            memory_reserved = torch.cuda.memory_reserved() / 1024**3  # GB
        else:
            import psutil
            process = psutil.Process()
            memory_allocated = process.memory_info().rss / 1024**3  # GB
            memory_reserved = memory_allocated
        
        results = {
            "latency_avg_ms": float(avg_latency),
            "latency_p95_ms": float(p95_latency),
            "latency_p99_ms": float(p99_latency),
            "memory_allocated_gb": float(memory_allocated),
            "memory_reserved_gb": float(memory_reserved)
        }
        
        print(f"Average Latency: {avg_latency:.2f} ms")
        print(f"P95 Latency: {p95_latency:.2f} ms")
        print(f"P99 Latency: {p99_latency:.2f} ms")
        print(f"Memory Allocated: {memory_allocated:.2f} GB")
        print(f"Memory Reserved: {memory_reserved:.2f} GB")
        
        return results
    
    def check_success_criteria(self, classification_results: Dict, edge_results: Dict) -> Dict:
        """Check if model meets success criteria."""
        print("\n=== Success Criteria Check ===")
        
        # Load target metrics from config
        with open("configs/model_config.yaml", 'r') as f:
            config = yaml.safe_load(f)
        
        eval_config = config['evaluation']
        edge_config = config['edge_deployment']
        
        criteria = {
            "accuracy": {
                "target": eval_config['target_accuracy'],
                "actual": classification_results['accuracy'],
                "passed": classification_results['accuracy'] >= eval_config['target_accuracy']
            },
            "precision": {
                "target": eval_config['target_precision'],
                "actual": classification_results['precision'],
                "passed": classification_results['precision'] >= eval_config['target_precision']
            },
            "recall": {
                "target": eval_config['target_recall'],
                "actual": classification_results['recall'],
                "passed": classification_results['recall'] >= eval_config['target_recall']
            },
            "f1": {
                "target": eval_config['target_f1'],
                "actual": classification_results['f1'],
                "passed": classification_results['f1'] >= eval_config['target_f1']
            },
            "latency": {
                "target": edge_config['target_latency_ms'],
                "actual": edge_results['latency_avg_ms'],
                "passed": edge_results['latency_avg_ms'] <= edge_config['target_latency_ms']
            },
            "memory": {
                "target": edge_config['target_memory_gb'],
                "actual": edge_results['memory_allocated_gb'],
                "passed": edge_results['memory_allocated_gb'] <= edge_config['target_memory_gb']
            }
        }
        
        for metric, result in criteria.items():
            status = "✓ PASSED" if result['passed'] else "✗ FAILED"
            print(f"{metric.upper()}: {result['actual']:.4f} (target: {result['target']}) {status}")
        
        all_passed = all(c['passed'] for c in criteria.values())
        print(f"\nOverall: {'✓ ALL CRITERIA PASSED' if all_passed else '✗ SOME CRITERIA FAILED'}")
        
        return criteria
    
    def run_evaluation(self):
        """Run complete evaluation pipeline."""
        print("Starting evaluation pipeline...")
        
        # Load test data
        test_data = self.load_test_data()
        
        # Evaluate classification
        classification_results = self.evaluate_classification(test_data)
        
        # Evaluate edge metrics
        edge_results = self.evaluate_edge_metrics(test_data)
        
        # Check success criteria
        criteria = self.check_success_criteria(classification_results, edge_results)
        
        # Save results
        results = {
            "classification": classification_results,
            "edge_deployment": edge_results,
            "success_criteria": criteria
        }
        
        output_file = self.model_path / "evaluation_results.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\nEvaluation results saved to {output_file}")
        
        return results

def main():
    """Main evaluation pipeline."""
    evaluator = CryptoModelEvaluator()
    results = evaluator.run_evaluation()

if __name__ == "__main__":
    main()
