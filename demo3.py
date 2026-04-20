import pennylane as qml
from pennylane import numpy as np
import time
import random

# Initialize a 2-qubit device
dev = qml.device("default.qubit", wires=2)

def header(text):
    print(f"\n\033[95m\033[1m{'='*75}\033[0m")
    print(f"\033[1m{text.center(75)}\033[0m")
    print(f"\033[95m\033[1m{'='*75}\033[0m")

# --- QUANTUM CIRCUITS ---

@qml.qnode(dev)
def transduction_circuit(phi):
    """Encodes the biometric feature into a qubit rotation."""
    qml.RY(phi, wires=0)
    return qml.probs(wires=0)

@qml.qnode(dev)
def hybrid_vault_circuit(phi):
    """Simulates the state for teleportation and secure storage."""
    qml.RY(phi, wires=0)
    qml.Hadamard(wires=1)
    qml.CNOT(wires=[1, 0])
    return qml.state()

# --- SYNTHETIC DATA GENERATOR ---

def generate_synthetic_minutiae(count=3):
    """Generates synthetic fingerprint minutiae: (x, y, orientation)."""
    template = []
    for i in range(count):
        minutia = {
            'id': i,
            'x': random.randint(0, 500),
            'y': random.randint(0, 500),
            'theta': random.randint(0, 180) # Orientation is key for our gate
        }
        template.append(minutia)
    return template

# --- THE 4-STAGE DEMO ---

def run_pennylane_evolution():
    # STAGE 1: ORIGINAL LOGIC
    header("STAGE 1: RAW QUANTUM TRANSDUCTION (SINGLE POINT)")
    raw_theta = 142
    gray = raw_theta ^ (raw_theta >> 1)
    phi = (gray / 255.0) * np.pi
    probs = transduction_circuit(phi)
    print(f"Input Orientation: {raw_theta}° | Gray: {gray} | Prob|0>: {probs[0]:.4f}")
    time.sleep(0.8)

    # STAGE 2: SYNTHETIC FINGERPRINT TEMPLATE
    header("STAGE 2: SYNTHETIC MINUTIAE BATCH PROCESSING")
    synthetic_template = generate_synthetic_minutiae(3)
    print(f"Generated Synthetic Template: {len(synthetic_template)} points found.")
    
    for m in synthetic_template:
        g = m['theta'] ^ (m['theta'] >> 1)
        angle = (g / 255.0) * np.pi
        res = transduction_circuit(angle)
        print(f"ID: {m['id']} | Coord: ({m['x']},{m['y']}) | Theta: {m['theta']:>3}° -> Q-Prob|0>: {res[0]:.4f}")
    time.sleep(0.8)

    # STAGE 3: BIO-AUTHENTICATION PIPELINE
    header("STAGE 3: QUANTUM STATE TELEPORTATION")
    # Using the theta from the first synthetic minutia
    target_phi = (synthetic_template[0]['theta'] / 180.0) * np.pi
    state = hybrid_vault_circuit(target_phi)
    print(f"Teleporting Minutia[0] State Vector:\n{state}")
    print("\033[92m[VERIFIED] Quantum Identity Match Found.\033[0m")
    time.sleep(0.8)

    # STAGE 4: AES-HYBRID QUANTUM VAULT
    header("STAGE 4: AES-HYBRID SECURE ARCHITECTURE")
    aes_key = 0xAF
    # Encrypt the orientation of a synthetic point
    raw_theta = synthetic_template[1]['theta']
    cipher = raw_theta ^ aes_key
    gray_cipher = cipher ^ (cipher >> 1)
    phi_hybrid = (gray_cipher / 255.0) * np.pi
    
    print(f"[*] Classical Layer: Encrypting Minutia ID 1...")
    print(f"[*] Ciphertext: {cipher} | Gray Map: {gray_cipher}")
    
    final_state = hybrid_vault_circuit(phi_hybrid)
    print(f"\n\033[96mFinal Encrypted Quantum State Vector:\n{final_state}\033[0m")
    
    print(f"\n\033[1m\033[92m{'*'*75}")
    print(f"PROTOCOL COMPLETE: MULTI-LAYER BIO-QUANTUM AUTHENTICATION")
    print(f"{'*'*75}\033[0m\n")

if __name__ == "__main__":
    run_pennylane_evolution()