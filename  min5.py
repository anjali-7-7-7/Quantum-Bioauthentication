"""
Quantum Fidelity Fingerprint Verification Demo
-----------------------------------------------
Uses Gray-coded angular encoding of fingerprint minutiae
into multi-qubit quantum states, verified via state fidelity.
  - Encodes ALL minutiae into a single multi-qubit state
  - Realistic noise (8% jitter, not 1.5%)
  - Genuine vs Impostor test (the real demo)
  - Fidelity threshold tuned to realistic separation
"""

import pennylane as qml
from pennylane import numpy as pnp
import numpy as np
import pandas as pd

# ─────────────────────────────────────────────
# 1. ENCODING: Minutia angle → Gray-coded qubit phase
# ─────────────────────────────────────────────

def angle_to_gray(theta_deg):
    """
    Convert a minutia angle (0–359°) to a Gray-coded 8-bit integer,
    then map to a qubit rotation angle in [0, π].
    
    Gray coding ensures adjacent angles differ by 1 bit — 
    making small sensor variations produce close quantum states.
    """
    # Discretize to 8-bit (0–255)
    quantized = int((theta_deg % 360) / 360 * 255)
    # Gray encode: G(n) = n XOR (n >> 1)
    gray = quantized ^ (quantized >> 1)
    # Map to rotation angle in [0, π]
    phi = (gray / 255.0) * np.pi
    return phi, gray


# ─────────────────────────────────────────────
# 2. QUANTUM ENGINE: Multi-qubit state from minutiae set
# ─────────────────────────────────────────────

def build_circuit(n_minutiae):
    dev = qml.device("default.qubit", wires=n_minutiae)

    @qml.qnode(dev)
    def encode_fingerprint(phis):
        """
        Encode N minutiae into an N-qubit entangled state.
        Each qubit carries one minutia's Gray-coded angle via RY.
        CNOT chain entangles them — making the state holistic,
        so a single matching minutia alone cannot pass.
        """
        # Encode each minutia into its qubit
        for i, phi in enumerate(phis):
            qml.RY(float(phi), wires=i)
        # Entangle sequentially — full fingerprint becomes one state
        for i in range(n_minutiae - 1):
            qml.CNOT(wires=[i, i + 1])
        return qml.state()

    return encode_fingerprint


def calculate_fidelity(state_a, state_b):
    """Quantum state overlap. 1.0 = identical, 0.0 = orthogonal."""
    return float(np.abs(np.vdot(state_a, state_b))**2)


# ─────────────────────────────────────────────
# 3. DATASET: Enrolled fingerprint templates
# ─────────────────────────────────────────────

# Two different people's fingerprints (minutiae angles)
ENROLLED_USER_A = {
    'name': 'User A (Enrolled)',
    'minutiae_angles': [45, 120, 175, 230]   # 4 minutiae points
}

ENROLLED_USER_B = {
    'name': 'User B (Impostor)',
    'minutiae_angles': [60, 95, 200, 310]    # Different person
}


def add_sensor_noise(angles, jitter_pct=0.08):
    """
    Simulate realistic fingerprint sensor noise.
    8% jitter models real-world finger placement variation.
    (v1 used 1.5% — far too clean to be meaningful)
    """
    noisy = []
    for a in angles:
        noise = a * jitter_pct * (2 * np.random.rand() - 1)
        noisy.append(a + noise)
    return noisy


# ─────────────────────────────────────────────
# 4. PIPELINE
# ─────────────────────────────────────────────

def encode_user(angles, circuit_fn, label=""):
    """Encode a set of minutiae angles into a quantum state."""
    phis = [angle_to_gray(a)[0] for a in angles]
    state = circuit_fn(phis)
    print(f"  [{label}] Gray-coded phases: {[f'{p:.3f}' for p in phis]}")
    return state


def run_verification(enrolled_angles, probe_angles, circuit_fn, label):
    """Compare enrolled template vs probe scan."""
    print(f"\n  Enrolled template → quantum state")
    enrolled_state = encode_user(enrolled_angles, circuit_fn, "Enrolled")
    
    print(f"  Live scan → quantum state")
    probe_state = encode_user(probe_angles, circuit_fn, "Probe  ")
    
    fidelity = calculate_fidelity(enrolled_state, probe_state)
    
    THRESHOLD = 0.92   # Tuned for 8% noise tolerance
    verdict = " PASS — Identity Verified" if fidelity >= THRESHOLD else " FAIL — Identity Rejected"
    
    print(f"\n  Fidelity Score : {fidelity:.6f}  (threshold: {THRESHOLD})")
    print(f"  Verdict        : {verdict}")
    return fidelity


def run_demo():
    np.random.seed(42)
    n = len(ENROLLED_USER_A['minutiae_angles'])
    circuit = build_circuit(n)

    print("=" * 65)
    print("  QUANTUM FIDELITY FINGERPRINT VERIFICATION")
    print(f"  {n}-minutia Gray-coded encoding | PennyLane simulation")
    print("=" * 65)

    # ── TEST 1: Genuine match (same user, noisy rescan) ──────────
    print("\n[TEST 1] GENUINE MATCH — Same user, sensor noise applied")
    print("-" * 65)
    enrolled = ENROLLED_USER_A['minutiae_angles']
    noisy_rescan = add_sensor_noise(enrolled, jitter_pct=0.08)
    print(f"  Original angles : {enrolled}")
    print(f"  Noisy rescan    : {[f'{a:.1f}' for a in noisy_rescan]}")
    f1 = run_verification(enrolled, noisy_rescan, circuit, "Genuine")

    # ── TEST 2: Impostor attack (different user) ──────────────────
    print("\n[TEST 2] IMPOSTOR ATTACK — Different user's fingerprint")
    print("-" * 65)
    impostor = ENROLLED_USER_B['minutiae_angles']
    print(f"  Enrolled (User A) : {enrolled}")
    print(f"  Impostor (User B) : {impostor}")
    f2 = run_verification(enrolled, impostor, circuit, "Impostor")

    # ── TEST 3: Partial match (only 2 of 4 minutiae match) ───────
    print("\n[TEST 3] PARTIAL MATCH — Only first 2 minutiae match")
    print("-" * 65)
    partial = enrolled[:2] + ENROLLED_USER_B['minutiae_angles'][2:]
    print(f"  Enrolled : {enrolled}")
    print(f"  Partial  : {partial}")
    f3 = run_verification(enrolled, partial, circuit, "Partial")

    # ── Summary ───────────────────────────────────────────────────
    print("\n" + "=" * 65)
    print("  RESULTS SUMMARY")
    print("=" * 65)
    rows = [
        ("Genuine (noisy rescan)", f1, "PASS" if f1 >= 0.92 else " FAIL"),
        ("Impostor (diff. user)", f2, "  PASS" if f2 >= 0.92 else " FAIL"),
        ("Partial match (2/4)",   f3, " PASS" if f3 >= 0.92 else " FAIL"),
    ]
    print(f"  {'Scenario':<28} {'Fidelity':>10}   {'Result'}")
    print(f"  {'-'*55}")
    for name, score, result in rows:
        print(f"  {name:<28} {score:>10.6f}   {result}")

    print(f"\n  Fidelity gap (genuine vs impostor): {f1 - f2:.4f}")
    print(f"  {'→ Strong separation ' if (f1 - f2) > 0.3 else '→ Weak separation   — review encoding'}")
    print("=" * 65)


if __name__ == "__main__":
    run_demo()