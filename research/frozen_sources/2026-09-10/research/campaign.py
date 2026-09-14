"""Resumable Model B finite-size study. Run: python -m research.campaign --help.

Completed replicas are immutable NPZ files. Interrupted replicas are restarted
from their stored seed, not continued with an unrecorded random-number state.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import time

import numpy as np
from model_b import kawasaki_engine as engine

ROOT = Path(__file__).resolve().parents[1]


def utc():
    return datetime.now(timezone.utc).isoformat()


def atomic_json(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    temporary.replace(path)


def one_replica(config, deadline=float('inf')):
    """Use the unchanged engine kernels and retain correlations and snapshots."""
    t = engine._log_time_checkpoints(config.max_sweeps, config.n_time_samples)
    lattice = engine._seed_and_init_lattice(config.L, config.seed, config.concentration)
    magnetization = int(lattice.sum())
    engine._run_n_sweeps(lattice, 1 / config.T_initial, config.Jx, config.Jy, config.eq_sweeps_initial)
    correlations, lengths, energies, interfaces, snapshots = [], [], [], [], []
    previous = 0
    for sweep in t:
        # Check every <=500 sweeps so the wall-time budget is respected.
        delta = 0.
        remaining = int(sweep) - previous
        while remaining:
            if time.monotonic() >= deadline:
                raise TimeoutError('Wall-time budget reached; current replica can be restarted.')
            chunk = min(500, remaining)
            delta += engine._run_n_sweeps_with_heat(lattice, 1 / config.T_final, config.Jx, config.Jy, chunk)
            remaining -= chunk
        if int(lattice.sum()) != magnetization:
            raise RuntimeError('Conservation check failed.')
        cx, cy = engine._axis_correlation_xy(lattice, config.L // 2)
        correlations.append([cx, cy])
        lengths.append([engine.domain_size_from_correlation(cx), engine.domain_size_from_correlation(cy)])
        energies.append(delta)
        interfaces.append(sum(np.count_nonzero(lattice != np.roll(lattice, 1, axis)) for axis in (0, 1)) / (2 * lattice.size))
        snapshots.append(lattice.copy())
        previous = int(sweep)
    return dict(t=t, correlations=np.asarray(correlations), lengths=np.asarray(lengths),
                delta_energy=np.asarray(energies), interfaces=np.asarray(interfaces),
                snapshots=np.asarray(snapshots), magnetization=magnetization,
                realized_concentration=(magnetization / lattice.size + 1) / 2,
                config=json.dumps(asdict(config)))


def run(args):
    plan = json.loads(args.plan.read_text())
    if plan['replicas'] < 2 or min(plan['sizes']) < 4 or plan['max_sweeps'] < 10:
        raise ValueError('Need >=2 replicas, L>=4 and >=10 sweeps.')
    if len(set(plan['sizes'])) != len(plan['sizes']) or len(set(plan['concentrations'])) != len(plan['concentrations']):
        raise ValueError('Duplicate sizes or concentrations.')
    if not all(0 < c < 1 for c in plan['concentrations']):
        raise ValueError('Concentration must lie in (0, 1).')
    out = args.output
    out.mkdir(parents=True, exist_ok=True)
    source_hashes = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                     for name in ('model_b/kawasaki_engine.py', 'research/campaign.py')}
    versions = {p: importlib.metadata.version(p) for p in ('numpy', 'scipy', 'numba')}
    identity = dict(plan=plan, sources=source_hashes, versions=versions, python=platform.python_version())
    manifest = out / 'manifest.json'
    if manifest.exists():
        old = json.loads(manifest.read_text())
        if old['identity'] != identity:
            raise ValueError('Plan, source or environment changed. Use a new output directory.')
    else:
        atomic_json(manifest, dict(identity=identity, created_utc=utc(),
                    git_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                    git_status=subprocess.check_output(['git', 'status', '--short'], cwd=ROOT, text=True),
                    description='Prospective finite-size study; hypotheses are not conclusions.'))
    lock = out / 'RUNNING.lock'
    try:
        lock_fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        raise RuntimeError('Campaign is already running or has a stale RUNNING.lock; inspect before restarting.')
    os.write(lock_fd, str(os.getpid()).encode())
    os.close(lock_fd)
    jobs = [(rep, ci, c, li, L) for rep in range(plan['replicas'])
            for ci, c in enumerate(plan['concentrations']) for li, L in enumerate(plan['sizes'])]
    deadline = time.monotonic() + args.hours * 3600
    completed = 0
    try:
        for rep, ci, c, li, L in jobs:
            seed = int(np.random.SeedSequence([plan['seed'], rep, ci, li]).generate_state(1)[0])
            path = out / f'c{ci}_L{L}_rep{rep:03d}.npz'
            if path.exists():
                with np.load(path, allow_pickle=False) as data:
                    if int(data['t'][-1]) != plan['max_sweeps']:
                        raise ValueError(f'Incomplete result: {path}')
                completed += 1
                continue
            config = engine.KawasakiConfig(L=L, Jx=plan['Jx'], Jy=plan['Jy'],
                      concentration=c, n_replicas=1, max_sweeps=plan['max_sweeps'],
                      n_time_samples=plan['time_samples'], eq_sweeps_initial=plan['equilibration'], seed=seed)
            atomic_json(out / 'status.json', dict(state='running', completed=completed, total=len(jobs),
                        current=path.name, updated_utc=utc()))
            started = time.monotonic()
            data = one_replica(config, deadline)
            temporary = path.with_suffix('.tmp')
            with temporary.open('wb') as stream:
                np.savez_compressed(stream, **data)
            temporary.replace(path)
            completed += 1
            print(f'{completed}/{len(jobs)} {path.name}: {time.monotonic()-started:.1f}s', flush=True)
        state = 'complete'
    except TimeoutError:
        state = 'budget_exhausted'
        print('Budget reached. Completed replicas retained; rerun the same command to continue.', flush=True)
    except BaseException:
        atomic_json(out / 'status.json', dict(state='interrupted_or_failed', completed=completed,
                    total=len(jobs), updated_utc=utc()))
        raise
    finally:
        lock.unlink(missing_ok=True)
    atomic_json(out / 'status.json', dict(state=state, completed=completed, total=len(jobs), updated_utc=utc()))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, default=Path('research/plans/pilot.json'))
    parser.add_argument('--output', type=Path, default=Path('research/runs/pilot'))
    parser.add_argument('--hours', type=float, default=2., help='Wall-time limit, checked inside each replica')
    args = parser.parse_args()
    if args.hours <= 0:
        parser.error('--hours must be positive')
    run(args)
