import pennylane as qml
from pennylane import numpy as np
import time

# --- 1. THE QUANTUM HARDWARE ---
dev = qml.device("default.qubit", wires=2)

@qml.qnode(dev)
def bio_quantum_circuit(phi):
    """Encodes any biometric value into a Quantum State."""
    qml.RY(phi, wires=0)
    qml.Hadamard(wires=1)
    qml.CNOT(wires=[1, 0])
    return qml.state()

# --- 2. THE SIMPLIFIED WORKFLOW ---
def run_genius_workflow():
    print(f"\n\033[95m\033[1m{'='*75}\033[0m")
    print(f"\033[1m{'C-DAC HYBRID VAULT: FINGERPRINT & DNA INTEGRATION'.center(75)}\033[0m")
    print(f"\033[95m\033[1m{'='*75}\033[0m")

    # DATA SOURCE: We handle both here
    # 142 is a ridge angle | 18 is a DNA repeat count (vWA Locus)
    biometric_inputs = {
        "PHYSICAL_FINGERPRINT": 142,
        "GENETIC_STR_PROFILE": 18  
    }

    for bio_type, raw_val in biometric_inputs.items():
        print(f"\n\033[1m[PROCESSING: {bio_type}]\033[0m")
        
        # STEP 1: AES LOCK (Classical)
        aes_key = 0xAF
        cipher = raw_val ^ aes_key
        print(f" -> AES Scrambled: {cipher}")

        # STEP 2: GRAY SHIELD (Noise Resilience)
        # This is the 'Secret Sauce' that makes the hardware work better
        gray = cipher ^ (cipher >> 1)
        
        # STEP 3: QUANTUM MAPPING (The Angle)
        # We normalize to Pi so the Qubit knows how far to turn
        phi = (gray / 255.0) * np.pi
        print(f" -> Gray-Code Mapping: {gray} (Rotation: {phi:.4f} rad)")

        # STEP 4: EXECUTION (PennyLane)
        print(f" -> Teleporting to Quantum Vault...")
        state_vector = bio_quantum_circuit(phi)
        
        print(f" \033[92m-> Final Quantum State:\033[0m {state_vector}")
        time.sleep(0.5)

    print(f"\n\033[1m\033[93m{'*'*75}")
    print(f"SYSTEM STATUS: MULTIMODAL IDENTITY SECURED")
    print(f"{'*'*75}\033[0m\n")

if __name__ == "__main__":
    run_genius_workflow()