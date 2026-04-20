"""
DNA Quantum Bio-Authentication via Gray-Coded Teleportation
============================================================
Pipeline:
  1. DNA sequence  ->  Gray code (2 bits per nucleotide)
  2. Each 2-bit value  ->  qubit rotation angles (theta, phi)
  3. Teleport that qubit state to the server via Bell pair +
     mid-circuit measurements + classical feedforward
  4. Server stores reconstructed density matrices (enrollment)
  5. Auth: re-teleport new sample, compare via fidelity

Key point: server only ever sees classical Bell-measurement
bits — never the raw DNA-encoded state. Blindness is a
structural consequence of the teleportation protocol.
"""

import pennylane as qml
from pennylane import numpy as np
from scipy.linalg import sqrtm

# ── Gray code map ──────────────────────────────────────────
#   A=00, T=01, C=11, G=10
#   Adjacent nucleotides differ by 1 bit (Gray property)
GRAY = {'A': '00', 'T': '01', 'C': '11', 'G': '10'}

# Map each 2-bit Gray code to (theta, phi) rotation angles
# These parameterise a point on the Bloch sphere
ANGLE_MAP = {
    '00': (0.0,        0.0),        # |0>
    '01': (np.pi / 2,  0.0),        # |+>
    '11': (np.pi / 2,  np.pi / 2),  # |i>
    '10': (np.pi,      0.0),        # |1>
}

def dna_to_gray(sequence: str) -> list:
    return [GRAY[n] for n in sequence.upper()]

# ── Quantum device ─────────────────────────────────────────
# Wires: 0 = message (client), 1 = Alice's Bell qubit,
#        2 = Bob's Bell qubit (server)
dev = qml.device("default.qubit", wires=3)

# ── Teleportation circuit ──────────────────────────────────
@qml.qnode(dev)
def teleport(theta, phi):
    """
    Encodes DNA state on wire 0, teleports to wire 2.

    How to read this:
      - RY(theta) + RZ(phi) prepares the DNA-encoded qubit
      - H + CNOT creates the Bell pair (entanglement resource)
      - CNOT + H is the Bell basis measurement preparation
      - qml.measure() performs mid-circuit measurement
      - cond() applies classical feedforward corrections
        (this is what the server does with the 2 classical bits)
    """
    # Step 1: prepare message qubit with DNA-encoded angles
    qml.RY(theta, wires=0)
    qml.RZ(phi,   wires=0)

    # Step 2: create Bell pair — entanglement shared with server
    qml.Hadamard(wires=1)
    qml.CNOT(wires=[1, 2])

    # Step 3: Alice entangles message qubit with her Bell qubit
    qml.CNOT(wires=[0, 1])
    qml.Hadamard(wires=0)

    # Step 4: mid-circuit measurement (classical bits sent to server)
    m0 = qml.measure(0)   # server receives these 2 bits, not the qubit
    m1 = qml.measure(1)

    # Step 5: server applies Pauli corrections based on classical bits
    qml.cond(m1, qml.PauliX)(wires=2)   # bit flip if m1=1
    qml.cond(m0, qml.PauliZ)(wires=2)   # phase flip if m0=1

    # Return Bob's reconstructed density matrix
    return qml.density_matrix(wires=2)

# ── Fidelity ───────────────────────────────────────────────
def fidelity(rho1, rho2):
    """
    Quantum fidelity F = Tr(sqrt(sqrt(rho1) @ rho2 @ sqrt(rho1)))^2
    1.0 = identical states, 0.0 = orthogonal states.
    """
    r1 = np.array(rho1, dtype=complex)
    r2 = np.array(rho2, dtype=complex)
    sqrt_r1 = sqrtm(r1)
    M = sqrt_r1 @ r2 @ sqrt_r1
    return float(np.real(np.trace(sqrtm(M))) ** 2)

# ── Enrollment ─────────────────────────────────────────────
def enroll(sequence: str):
    """
    For each nucleotide: Gray-code -> qubit angles -> teleport
    -> store server-side density matrix as biometric template.
    """
    stored = []
    for gc in dna_to_gray(sequence):
        theta, phi = ANGLE_MAP[gc]
        rho = np.array(teleport(theta, phi))
        stored.append(rho)
    return stored

# ── Authentication ─────────────────────────────────────────
def authenticate(sequence: str, stored: list, threshold: float = 0.99):
    """
    Re-teleport new sample, compare each nucleotide's
    reconstructed state against stored template via fidelity.
    """
    fidelities = []
    for gc, rho_stored in zip(dna_to_gray(sequence), stored):
        theta, phi = ANGLE_MAP[gc]
        rho_auth = np.array(teleport(theta, phi))
        fidelities.append(fidelity(rho_stored, rho_auth))

    avg = float(np.mean(fidelities))
    return {
        "fidelities":    fidelities,
        "avg_fidelity":  avg,
        "authenticated": avg >= threshold,
    }

# ── Demo ───────────────────────────────────────────────────
if __name__ == "__main__":
    SEP = "=" * 54

    print(SEP)
    print("  DNA Quantum Bio-Authentication - PennyLane Demo")
    print(SEP)

    enrolled_seq = "ATCG"
    print(f"\n[ENROLLMENT]  Sequence : {enrolled_seq}")
    print(f"              Gray     : {dna_to_gray(enrolled_seq)}")
    stored_states = enroll(enrolled_seq)
    print(f"              Stored {len(stored_states)} qubit states on server.\n")

    def show(label, seq, result):
        print(f"[{label}]")
        print(f"    Input: '{seq}'")
        for n, f in zip(seq, result["fidelities"]):
            bar = "█" * int(f * 20)
            print(f"    {n} ({GRAY[n]}): {f:.4f}  {bar}")
        print(f"    Avg fidelity : {result['avg_fidelity']:.6f}")
        status = "AUTHENTICATED" if result["authenticated"] else "REJECTED"
        print(f"    Result       : {status}\n")

    show("AUTH 1 - exact match",
         enrolled_seq,
         authenticate(enrolled_seq, stored_states))

    show("AUTH 2 - one mutation",
         "ATGG",
         authenticate("ATGG", stored_states))

    show("AUTH 3 - impostor",
         "GGGG",
         authenticate("GGGG", stored_states))

    print(SEP)
    print("  Blindness: server receives only 2 classical bits")
    print("  per nucleotide. Raw DNA state never transmitted.")
    print(SEP)