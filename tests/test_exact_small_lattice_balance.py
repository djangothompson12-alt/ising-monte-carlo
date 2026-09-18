"""Exact canonical-sector check of the Kawasaki one-attempt transition rule.

This is a small-system verification, not evidence for a late-time growth law.
"""

from itertools import combinations
import unittest

import numpy as np

from model_b import kawasaki_engine as model_b


def full_hamiltonian(spins: np.ndarray, jx: float, jy: float) -> float:
    """Count each horizontal and vertical periodic bond once."""
    return float(-jx * np.sum(spins * np.roll(spins, 1, axis=1))
                 -jy * np.sum(spins * np.roll(spins, 1, axis=0)))


class ExactSmallLatticeBalanceTests(unittest.TestCase):
    def test_3_by_3_fixed_composition_transition_matrix(self):
        L, n_up, jx, jy, beta = 3, 4, 0.7, 1.3, 0.4
        states = []
        for positive in combinations(range(L * L), n_up):
            flat = np.full(L * L, -1, dtype=np.int8)
            flat[list(positive)] = 1
            states.append(flat.reshape(L, L))
        key_to_index = {state.tobytes(): index for index, state in enumerate(states)}
        self.assertEqual(len(states), 126)
        energy = np.array([full_hamiltonian(state, jx, jy) for state in states])
        weights = np.exp(-beta * (energy - energy.min()))
        boltzmann = weights / weights.sum()
        transition = np.zeros((len(states), len(states)))
        proposals = ((0, 1, jx), (0, -1, jx), (1, 0, jy), (-1, 0, jy))
        proposal_probability = 1.0 / (4 * L * L)
        for index, state in enumerate(states):
            for row in range(L):
                for col in range(L):
                    for dr, dc, bond in proposals:
                        other = ((row + dr) % L, (col + dc) % L)
                        if state[row, col] == state[other]:
                            transition[index, index] += proposal_probability
                            continue
                        swapped = state.copy()
                        swapped[row, col], swapped[other] = swapped[other], swapped[row, col]
                        target = key_to_index[swapped.tobytes()]
                        direct_delta = energy[target] - energy[index]
                        local_delta = (2 * state[row, col] *
                                       (model_b._local_field(state, row, col, jx, jy)
                                        - model_b._local_field(state, *other, jx, jy))
                                       + 4 * bond)
                        self.assertAlmostEqual(local_delta, direct_delta, places=12)
                        accepted = min(1.0, np.exp(-beta * local_delta))
                        transition[index, target] += proposal_probability * accepted
                        transition[index, index] += proposal_probability * (1 - accepted)
        np.testing.assert_allclose(transition.sum(axis=1), 1.0, rtol=0, atol=1e-14)
        flow = boltzmann[:, None] * transition
        np.testing.assert_allclose(flow, flow.T, rtol=0, atol=1e-14)
        np.testing.assert_allclose(boltzmann @ transition, boltzmann, rtol=0, atol=1e-14)


if __name__ == "__main__":
    unittest.main()
