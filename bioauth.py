import os
import json
import hashlib
import argparse
import secrets
from pathlib import Path
import pennylane as qml
from pennylane import numpy as np

# ── Config ────────────────────────────────────────────────────────────────────
DB_PATH              = Path("bio_auth_db.json")
FIDELITY_THRESHOLD   = 0.82    
dev = qml.device("default.qubit", wires=3)

GRAY_ENC = {"A": "00", "C": "01", "T": "11", "G": "10"}
GRAY_DEC = {v: k for k, v in GRAY_ENC.items()}
BASES    = list(GRAY_ENC.keys())

# ── Quantum Teleportation Logic ───────────────────────────────────────────────

@qml.qnode(dev)
def teleport_circuit(bit_val, eavesdrop=False):
    # 1. State Prep
    if bit_val == "1":
        qml.PauliX(wires=0)
    
    # 2. Entanglement
    qml.Hadamard(wires=1)
    qml.CNOT(wires=[1, 2])
    
    # 3. Eavesdrop Simulation
    if eavesdrop:
        qml.measure(1) 
    
    # 4. Alice's Bell Measurement
    qml.CNOT(wires=[0, 1])
    qml.Hadamard(wires=0)
    
    m0 = qml.measure(0)
    m1 = qml.measure(1)
    
    # 5. Bob's Conditional Corrections
    qml.cond(m1, qml.PauliX)(2)
    qml.cond(m0, qml.PauliZ)(2)
    
    return qml.density_matrix(wires=2)

def teleport_base(base: str, eavesdrop: bool = False) -> tuple[str, float]:
    bits = GRAY_ENC.get(base.upper(), "00")
    decoded_bits = ""
    fidelities = []

    for bit in bits:
        res_dm = teleport_circuit(bit, eavesdrop=eavesdrop)
        expected_idx = 1 if bit == "1" else 0
        fid = float(qml.math.float(res_dm[expected_idx, expected_idx]))
        
        recv_bit = "1" if fid > 0.5 else "0"
        decoded_bits += recv_bit
        fidelities.append(fid)

    return GRAY_DEC.get(decoded_bits, "?"), sum(fidelities)/len(fidelities)

# ── Classical Helpers ─────────────────────────────────────────────────────────

def hash_dna_key(dna: str, salt: bytes) -> str:
    return hashlib.pbkdf2_hmac("sha256", dna.upper().encode(), salt, iterations=100_000).hex()

def load_db(): 
    return json.loads(DB_PATH.read_text()) if DB_PATH.exists() else {}

def save_db(db): 
    DB_PATH.write_text(json.dumps(db, indent=2))

# ── Enrollment & Auth Logic ───────────────────────────────────────────────────

def enroll(username, dna_key):
    print(f"[ENROLL] Registering user: {username}")
    salt = secrets.token_bytes(32)
    key_hash = hash_dna_key(dna_key, salt)
    
    # Calibration
    _, fid = teleport_base(dna_key[0])
    
    db = load_db()
    db[username] = {
        "key_hash": key_hash, 
        "salt": salt.hex(), 
        "dna_length": len(dna_key), 
        "baseline_fidelity": float(fid)
    }
    save_db(db)
    print(f"Successfully enrolled {username}. Baseline fidelity: {fid*100:.1f}%")

def authenticate(username, dna_key, eavesdrop=False):
    db = load_db()
    if username not in db:
        print(f"Error: User '{username}' not found.")
        return False
    
    record = db[username]
    if hash_dna_key(dna_key, bytes.fromhex(record["salt"])) != record["key_hash"]:
        print("Authentication Failed: DNA Key Mismatch!")
        return False
    
    # Random position challenge
    pos = secrets.SystemRandom().randint(0, len(dna_key)-1)
    target = dna_key[pos]
    
    decoded, fid = teleport_base(target, eavesdrop=eavesdrop)
    
    print(f"\n--- Quantum Challenge ---")
    print(f"Pos {pos} | Sent: {target} | Recv: {decoded} | Fidelity: {fid*100:.1f}%")
    
    success = (decoded == target) and (fid >= FIDELITY_THRESHOLD)
    print(f"Final Result: {'[ACCESS GRANTED]' if success else '[ACCESS DENIED]'}")
    if eavesdrop and not success:
        print("Notice: Significant fidelity drop detected. Possible eavesdropping.")
    return success

# ── Main CLI ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Quantum DNA Authentication CLI")
    parser.add_argument("command", choices=["enroll", "auth", "attack"], help="Operation to perform")
    parser.add_argument("user", help="Username")
    parser.add_argument("--dna", help="DNA sequence (e.g., ATCG)")

    args = parser.parse_args()

    # DNA logic: Enrollment requires it, auth/attack can generate or use provided
    if args.command == "enroll" and not args.dna:
        dna_input = "".join(secrets.choice(BASES) for _ in range(8))
        print(f"[*] Generating random DNA for enrollment: {dna_input}")
    else:
        dna_input = args.dna if args.dna else "AAAA" # Default fallback

    if args.command == "enroll":
        enroll(args.user, dna_input)
    elif args.command == "auth":
        authenticate(args.user, dna_input, eavesdrop=False)
    elif args.command == "attack":
        authenticate(args.user, dna_input, eavesdrop=True)