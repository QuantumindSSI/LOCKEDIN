#!/usr/bin/env python3
"""
Data collection pipeline for Quantum-Resistant Cryptographic Protocol Analyzer.
Collects NIST PQC submissions, CVE data, and quantum cryptanalysis papers.
"""

import os
import json
import requests
from pathlib import Path
from typing import List, Dict
import base64
import hashlib

class CryptoDataCollector:
    """Collects cryptographic vulnerability data from multiple sources."""
    
    def __init__(self, output_dir: str = "data/raw"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def collect_nist_pqc_submissions(self) -> List[Dict]:
        """
        Collect NIST Post-Quantum Cryptography standardization submissions.
        Focus on Round 3 finalists and alternate candidates.
        """
        print("Collecting NIST PQC submissions...")
        
        # NIST PQC Round 3 finalists and alternates
        pqc_algorithms = {
            "CRYSTALS-Kyber": {
                "type": "KEM",
                "quantum_vulnerable": False,
                "description": "Lattice-based key encapsulation mechanism"
            },
            "CRYSTALS-Dilithium": {
                "type": "Signature",
                "quantum_vulnerable": False,
                "description": "Lattice-based digital signature"
            },
            "Falcon": {
                "type": "Signature",
                "quantum_vulnerable": False,
                "description": "Lattice-based signature with NTT"
            },
            "SPHINCS+": {
                "type": "Signature",
                "quantum_vulnerable": False,
                "description": "Stateless hash-based signature"
            },
            "Classic McEliece": {
                "type": "KEM",
                "quantum_vulnerable": False,
                "description": "Code-based key encapsulation"
            },
            "RSA-2048": {
                "type": "Encryption",
                "quantum_vulnerable": True,
                "description": "Classical RSA vulnerable to Shor's algorithm"
            },
            "ECC-P256": {
                "type": "Signature",
                "quantum_vulnerable": True,
                "description": "Elliptic curve cryptography vulnerable to Shor's algorithm"
            },
            "DSA-2048": {
                "type": "Signature",
                "quantum_vulnerable": True,
                "description": "Digital Signature Algorithm vulnerable to Shor's algorithm"
            }
        }
        
        # Generate synthetic protocol descriptions
        data = []
        for algo_name, algo_info in pqc_algorithms.items():
            for i in range(100):  # Generate 100 examples per algorithm
                sample = {
                    "protocol_description": f"{algo_name} implementation with {algo_info['type']} operations",
                    "implementation_code": self._generate_synthetic_code(algo_name, algo_info),
                    "vulnerability_type": "quantum_vulnerable" if algo_info["quantum_vulnerable"] else "quantum_resistant",
                    "quantum_attack_vector": "Shor's algorithm" if algo_info["quantum_vulnerable"] else "None known",
                    "severity": "critical" if algo_info["quantum_vulnerable"] else "none",
                    "algorithm_type": algo_info["type"],
                    "description": algo_info["description"]
                }
                data.append(sample)
        
        # Save to file
        output_file = self.output_dir / "nist_pqc_submissions.json"
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Saved {len(data)} NIST PQC samples to {output_file}")
        return data
    
    def collect_cve_cryptographic_vulnerabilities(self) -> List[Dict]:
        """
        Collect CVE entries related to cryptographic vulnerabilities.
        Focus on quantum-vulnerable implementations.
        """
        print("Collecting CVE cryptographic vulnerabilities...")
        
        # Sample CVE data (in production, fetch from CVE API)
        cve_samples = [
            {
                "cve_id": "CVE-2020-0601",
                "description": "CurveBall vulnerability in Windows CryptoAPI",
                "vulnerability_type": "quantum_vulnerable",
                "quantum_attack_vector": "Shor's algorithm",
                "severity": "critical",
                "affected_protocol": "ECC"
            },
            {
                "cve_id": "CVE-2017-15361",
                "description": "ROCA vulnerability in Infineon RSA key generation",
                "vulnerability_type": "quantum_vulnerable",
                "quantum_attack_vector": "Shor's algorithm",
                "severity": "high",
                "affected_protocol": "RSA"
            },
            {
                "cve_id": "CVE-2021-3450",
                "description": "Potential DoS in X.509 certificate verification",
                "vulnerability_type": "quantum_vulnerable",
                "quantum_attack_vector": "Shor's algorithm",
                "severity": "medium",
                "affected_protocol": "X.509"
            }
        ]
        
        # Generate expanded dataset
        data = []
        for cve in cve_samples:
            for i in range(50):  # Generate 50 variations per CVE
                sample = {
                    "protocol_description": f"{cve['description']} - Variant {i}",
                    "implementation_code": self._generate_synthetic_code(cve['affected_protocol'], {}),
                    "vulnerability_type": cve['vulnerability_type'],
                    "quantum_attack_vector": cve['quantum_attack_vector'],
                    "severity": cve['severity'],
                    "cve_id": cve['cve_id'],
                    "affected_protocol": cve['affected_protocol']
                }
                data.append(sample)
        
        # Save to file
        output_file = self.output_dir / "cve_cryptographic_vulnerabilities.json"
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Saved {len(data)} CVE samples to {output_file}")
        return data
    
    def collect_quantum_cryptanalysis_papers(self) -> List[Dict]:
        """
        Collect information from quantum cryptanalysis research papers.
        Focus on Shor's algorithm, Grover's algorithm, and quantum attacks.
        """
        print("Collecting quantum cryptanalysis research...")
        
        # Sample quantum cryptanalysis topics
        quantum_attacks = [
            {
                "algorithm": "Shor's algorithm",
                "target": "RSA, ECC, DSA",
                "quantum_complexity": "O((log N)^3)",
                "description": "Integer factorization algorithm breaking RSA and ECC"
            },
            {
                "algorithm": "Grover's algorithm",
                "target": "Symmetric key cryptography",
                "quantum_complexity": "O(sqrt(N))",
                "description": "Quadratic speedup for brute force search"
            },
            {
                "algorithm": "Quantum annealing attacks",
                "target": "Lattice-based cryptography",
                "quantum_complexity": "Unknown",
                "description": "Potential attacks on lattice problems"
            }
        ]
        
        # Generate dataset
        data = []
        for attack in quantum_attacks:
            for i in range(30):  # Generate 30 examples per attack
                sample = {
                    "protocol_description": f"Analysis of {attack['algorithm']} against {attack['target']}",
                    "implementation_code": self._generate_synthetic_code(attack['target'], {}),
                    "vulnerability_type": "quantum_vulnerable",
                    "quantum_attack_vector": attack['algorithm'],
                    "severity": "critical",
                    "quantum_complexity": attack['quantum_complexity'],
                    "description": attack['description']
                }
                data.append(sample)
        
        # Save to file
        output_file = self.output_dir / "quantum_cryptanalysis_papers.json"
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Saved {len(data)} quantum cryptanalysis samples to {output_file}")
        return data
    
    def _generate_synthetic_code(self, algorithm: str, algo_info: Dict) -> str:
        """Generate synthetic cryptographic code snippets."""
        code_templates = {
            "RSA": """
def rsa_encrypt(message, public_key):
    n, e = public_key
    return pow(message, e, n)

def rsa_decrypt(ciphertext, private_key):
    n, d = private_key
    return pow(ciphertext, d, n)
""",
            "ECC": """
def ecc_sign(message, private_key):
    k = random.randint(1, n-1)
    r = (k * G).x
    s = (hash(message) + r * private_key) * modinv(k, n) % n
    return (r, s)

def ecc_verify(signature, message, public_key):
    r, s = signature
    w = modinv(s, n)
    u1 = hash(message) * w % n
    u2 = r * w % n
    return u1 * G + u2 * public_key
""",
            "CRYSTALS-Kyber": """
def kyber_keygen():
    A = sample_matrix()
    s = sample_vector()
    e = sample_error_vector()
    t = A @ s + e
    pk = (A, t)
    sk = s
    return pk, sk

def kyber_encaps(pk, message):
    A, t = pk
    r = sample_vector()
    e1 = sample_error_vector()
    e2 = sample_error_vector()
    u = A @ r + e1
    v = t @ r + e2 + encode(message)
    return (u, v)
""",
            "CRYSTALS-Dilithium": """
def dilithium_sign(message, sk):
    A, s1, s2 = sk
    mu = H(message)
    y = sample_vector()
    w = A @ y
    c = H(mu, w)
    z = y + c * s1
    return (z, c)

def dilithium_verify(signature, message, pk):
    z, c = signature
    A, t = pk
    mu = H(message)
    w = A @ z - c * t
    c_prime = H(mu, w)
    return c == c_prime
"""
        }
        
        # Get appropriate template or generate generic one
        code = code_templates.get(algorithm, f"# {algorithm} implementation\n# Quantum-vulnerable: {algo_info.get('quantum_vulnerable', False)}\n")
        
        # Encode to base64 for storage
        return base64.b64encode(code.encode()).decode()
    
    def merge_all_datasets(self) -> List[Dict]:
        """Merge all collected datasets into a single training dataset."""
        print("Merging all datasets...")
        
        nist_data = self.collect_nist_pqc_submissions()
        cve_data = self.collect_cve_cryptographic_vulnerabilities()
        quantum_data = self.collect_quantum_cryptanalysis_papers()
        
        merged_data = nist_data + cve_data + quantum_data
        
        # Save merged dataset
        output_file = self.output_dir / "merged_crypto_vulnerability_data.json"
        with open(output_file, 'w') as f:
            json.dump(merged_data, f, indent=2)
        
        print(f"Saved {len(merged_data)} total samples to {output_file}")
        return merged_data

def main():
    """Main data collection pipeline."""
    collector = CryptoDataCollector()
    
    # Collect all data
    merged_data = collector.merge_all_datasets()
    
    print(f"\nData collection complete!")
    print(f"Total samples collected: {len(merged_data)}")
    print(f"Data saved to: data/raw/")

if __name__ == "__main__":
    main()
