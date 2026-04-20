import pennylane as qml
from pennylane import numpy as np

# 1. Define device (2 bits per base = we need 2 'S' wires for the state)
# Total wires: S0, S1 (Alice's Data), A0, A1 (Ancilla), B0, B1 (Bob's Result)
dev = qml.device("default.qubit", wires=6)

# ── DNA to Gray Code Mapping ──────────────────────────────────────────────────

def dna_to_gray_state(base):
    """Maps DNA base to a 2-qubit computational state vector."""
    mapping = {
        'A': [1, 0, 0, 0], # |00>
        'T': [0, 1, 0, 0], # |01>
        'C': [0, 0, 0, 1], # |11> (Gray code order)
        'G': [0, 0, 1, 0]  # |10>
    }
    return np.array(mapping.get(base.upper(), [1, 0, 0, 0]), requires_grad=False)

# ── Quantum Teleportation Logic ───────────────────────────────────────────────

@qml.qnode(dev)
def teleport_dna_base(state_vector):
    # Prepare the 2-qubit state for the DNA base on wires [0, 1]
    qml.StatePrep(state_vector, wires=[0, 1])
    
    # --- Teleportation for Qubit 0 (S0 -> B0) ---
    qml.Hadamard(wires=2)
    qml.CNOT(wires=[2, 4])
    qml.CNOT(wires=[0, 2])
    qml.Hadamard(wires=0)
    m0 = qml.measure(0)
    m1 = qml.measure(2)
    qml.cond(m1, qml.PauliX)(4)
    qml.cond(m0, qml.PauliZ)(4)

    # --- Teleportation for Qubit 1 (S1 -> B1) ---
    qml.Hadamard(wires=3)
    qml.CNOT(wires=[3, 5])
    qml.CNOT(wires=[1, 3])
    qml.Hadamard(wires=1)
    m2 = qml.measure(1)
    m3 = qml.measure(3)
    qml.cond(m3, qml.PauliX)(5)
    qml.cond(m2, qml.PauliZ)(5)

    return qml.density_matrix(wires=[4, 5])

# ── Execution ────────────────────────────────────────────────────────────────

def run_bio_demo(sequence):
    print(f"Sequence to teleport: {sequence}\n")
    
    for base in sequence:
        # Convert base to gray-coded state vector
        state_vec = dna_to_gray_state(base)
        
        # Teleport
        result_dm = teleport_dna_base(state_vec)
        
        # Verification
        expected_dm = qml.math.dm_from_state_vector(state_vec) # type: ignore
        
        if qml.math.allclose(result_dm, expected_dm, atol=1e-5): # type: ignore
            print(f"Base {base}: Teleported successfully as Gray Code.")
        else:
            print(f"Base {base}: Teleportation failed.")

if __name__ == "__main__":
    # Test with a snippet of DNA
    dna_snippet = "ATCG"
    run_bio_demo(dna_snippet)