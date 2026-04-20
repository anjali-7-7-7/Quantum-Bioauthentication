import pennylane as qml
from pennylane import numpy as np

# 1. Define the device
dev = qml.device("default.qubit", wires=["S", "A", "B"])

# ── Circuit Components ────────────────────────────────────────────────────────

def state_preparation(state):
    """Initializes Alice's qubit 'S' to the state she wants to teleport."""
    qml.StatePrep(state, wires=["S"])

def entangle_qubits():
    """Creates a Bell pair shared between Alice (A) and Bob (B)."""
    qml.Hadamard(wires="A")
    qml.CNOT(wires=["A", "B"])

def basis_rotation():
    """Alice rotates her two qubits back to the computational basis."""
    qml.CNOT(wires=["S", "A"])
    qml.Hadamard(wires="S")

def measure_and_update():
    """
    Alice measures her qubits and Bob updates his based on the results.
    """
    m0 = qml.measure("S")
    m1 = qml.measure("A")
    qml.cond(m1, qml.PauliX)("B")
    qml.cond(m0, qml.PauliZ)("B")

# ── The Complete QNode ────────────────────────────────────────────────────────

@qml.qnode(dev)
def teleport(state):
    state_preparation(state)
    entangle_qubits()
    basis_rotation()
    measure_and_update()
    return qml.density_matrix(wires=["B"])

# ── Verification ──────────────────────────────────────────────────────────────

# Use qml.math to avoid Pylance attribute issues on Lines 53-54
state = np.array([1 / qml.math.sqrt(2) + 0.3j, 0.4 - 0.5j]) # type: ignore
state /= qml.math.norm(state) # type: ignore

def run_demo():
    print(f"Preparing to teleport state: {state}")
    
    # Run the circuit
    bob_density_matrix = teleport(state)
    
    # Use the explicit math module for the density matrix conversion
    # Added # type: ignore because Pylance struggles to resolve the dynamic math registry
    alice_density_matrix = qml.math.dm_from_state_vector(state) # type: ignore
    
    # Use qml.math.allclose for consistent tensor handling
    if qml.math.allclose(bob_density_matrix, alice_density_matrix): # type: ignore
        print("\nSuccess! The state was teleported to Bob.")
        print(f"Bob's Resulting Density Matrix:\n{bob_density_matrix}")
    else:
        print("\nTeleportation failed.")

if __name__ == "__main__":
    run_demo()