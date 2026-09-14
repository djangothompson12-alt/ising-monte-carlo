"""Ideal isolated-string predictions and WAV frequency measurements (SI units).

Not an Ising model or a calibrated racket-stringbed tension meter. Sources and
the prospective protocol are in experiments/PROTOCOL.md. Run with --help.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.io import wavfile
from scipy.signal import find_peaks


def positive(**values):
    if any(not np.isfinite(v) or v <= 0 for v in values.values()):
        raise ValueError(f'Finite positive SI values required: {list(values)}')


def predict_frequency(force_N, length_m, linear_density_kg_m):
    """f1 = sqrt(F/mu)/(2 L), assuming flexible uniform string, fixed ends."""
    positive(force=force_N, length=length_m, density=linear_density_kg_m)
    return float(np.sqrt(force_N / linear_density_kg_m) / (2 * length_m))


def infer_tension(frequency_Hz, length_m, linear_density_kg_m):
    """Conditional on the frequency being the fundamental of an isolated span."""
    positive(frequency=frequency_Hz, length=length_m, density=linear_density_kg_m)
    return float(4 * linear_density_kg_m * length_m**2 * frequency_Hz**2)


def tension_uncertainty(frequency_Hz, length_m, linear_density_kg_m,
                        u_frequency_Hz, u_length_m, u_linear_density_kg_m):
    """First-order standard uncertainty; independent inputs only, not model error."""
    force = infer_tension(frequency_Hz, length_m, linear_density_kg_m)
    errors = np.array([u_frequency_Hz, u_length_m, u_linear_density_kg_m])
    if not np.all(np.isfinite(errors)) or np.any(errors < 0):
        raise ValueError('Standard uncertainties must be finite and nonnegative.')
    relative = np.array([2*u_frequency_Hz/frequency_Hz, 2*u_length_m/length_m,
                         u_linear_density_kg_m/linear_density_kg_m])
    return float(force * np.linalg.norm(relative))


def spectrum_peak(samples, sample_rate, low_Hz, high_Hz):
    """Windowed FFT peak. The loudest peak is NOT automatically the fundamental.

    No zero-padding presented as improved resolution. Three-bin interpolation
    reduces bin quantization; bin spacing is NOT a measurement uncertainty.
    """
    positive(sample_rate=sample_rate, low=low_Hz, high=high_Hz)
    if not low_Hz < high_Hz < sample_rate / 2:
        raise ValueError('Need 0 < low < high < Nyquist frequency.')
    x = np.asarray(samples, dtype=float)
    if x.ndim == 2:
        # Use first channel, rather than averaging potentially phase-inverted channels.
        x = x[:, 0]
    if x.ndim != 1 or len(x) / sample_rate < .25 or not np.all(np.isfinite(x)):
        raise ValueError('Need at least 0.25 s of finite mono/stereo audio.')
    x = x - np.mean(x)
    if np.max(np.abs(x)) <= np.finfo(float).eps:
        raise ValueError('Audio is silent.')
    magnitude = np.abs(np.fft.rfft(x * np.hanning(len(x))))
    frequencies = np.fft.rfftfreq(len(x), 1 / sample_rate)
    peaks, _ = find_peaks(magnitude)
    peaks = peaks[(frequencies[peaks] >= low_Hz) & (frequencies[peaks] <= high_Hz)]
    if not len(peaks):
        raise ValueError('No internal spectral peak in selected band; inspect the band/audio.')
    ranked = peaks[np.argsort(magnitude[peaks])[::-1]]
    i = ranked[0]
    a, b, c = np.log(np.maximum(magnitude[i-1:i+2], np.finfo(float).tiny))
    denominator = a - 2*b + c
    delta = .5*(a-c)/denominator if denominator != 0 else 0.
    frequency = (i + np.clip(delta, -.5, .5)) * sample_rate / len(x)
    candidates = [dict(frequency_Hz=float(frequencies[j]), relative_amplitude=float(magnitude[j]/magnitude[i])) for j in ranked[:5]]
    warnings = ['Peak identity must be checked: inspect lower modes and integer harmonics.']
    if len(ranked) > 1 and magnitude[ranked[1]] / magnitude[i] > .5:
        warnings.append('Multiple strong peaks; fundamental assignment is ambiguous.')
    return dict(peak_Hz=float(frequency), duration_s=len(x)/sample_rate,
                fft_bin_spacing_Hz=sample_rate/len(x), candidates=candidates,
                warnings=warnings, fundamental_automatically_verified=False)


def compare_records(records):
    """No fitting: predict measured frequencies from independently measured force.

    Each record is one sample/load condition, using the mean of repeated plucks.
    Validation results are aggregated within specimen, then across specimens.
    """
    if not isinstance(records, list) or not records:
        raise ValueError('Add real measurement records first; the template is intentionally empty.')
    results = []
    identifiers = set()
    for r in records:
        if r['record_id'] in identifiers:
            raise ValueError('Duplicate record_id.')
        identifiers.add(r['record_id'])
        if r['role'] not in ('pilot', 'validation'):
            raise ValueError('role must be pilot or validation, assigned before measurement.')
        if not r.get('fundamental_confirmed', False):
            raise ValueError('Every fundamental must be manually checked before comparison.')
        observed = np.asarray(r['frequency_repeats_Hz'], dtype=float)
        if observed.ndim != 1 or len(observed) < 3 or not np.all(np.isfinite(observed)) or np.any(observed <= 0):
            raise ValueError('Need >=3 positive measured frequency repeats per condition.')
        predicted = predict_frequency(r['reference_force_N'], r['loaded_length_m'], r['loaded_linear_density_kg_m'])
        mean = float(observed.mean())
        inferred = infer_tension(mean, r['loaded_length_m'], r['loaded_linear_density_kg_m'])
        results.append(dict(record_id=r['record_id'], specimen_id=r['specimen_id'], role=r['role'],
                            predicted_frequency_Hz=predicted, observed_frequency_Hz=mean,
                            pluck_SD_Hz=float(observed.std(ddof=1)), inferred_force_N=inferred,
                            reference_force_N=r['reference_force_N'],
                            force_relative_error=(inferred/r['reference_force_N']-1)))
    pilot_ids = {r['specimen_id'] for r in results if r['role'] == 'pilot'}
    validation_ids = {r['specimen_id'] for r in results if r['role'] == 'validation'}
    if pilot_ids & validation_ids:
        raise ValueError('Hold out whole specimens; pilot and validation IDs must be disjoint.')
    errors = [np.mean([abs(r['force_relative_error']) for r in results if r['role'] == 'validation' and r['specimen_id'] == sid]) for sid in sorted(validation_ids)]
    return dict(method='Unfitted ideal-string baseline; no real-world validation implied by software tests.',
                records=results, validation_specimens=len(errors),
                validation_specimen_weighted_mean_absolute_relative_force_error=float(np.mean(errors)) if errors else None,
                limitations='Repeat-pluck SD is not total uncertainty; model bias and force/density errors remain.')


def plot_comparison(result, output):
    """Plot only supplied measurements; never manufacture an experimental curve."""
    import os
    os.environ.setdefault('MPLCONFIGDIR', str(Path(__file__).resolve().parents[1] / '.mplconfig'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    output = Path(output)
    if output.exists():
        raise FileExistsError('Choose a new plot name to preserve the previous analysis.')
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5), layout='constrained')
    records = result['records']
    for role, marker in [('pilot', 'x'), ('validation', 'o')]:
        selected = [r for r in records if r['role'] == role]
        if not selected:
            continue
        axes[0].scatter([r['reference_force_N'] for r in selected], [r['inferred_force_N'] for r in selected], marker=marker,label=role)
        axes[1].scatter([r['reference_force_N'] for r in selected], [100*r['force_relative_error'] for r in selected], marker=marker,label=role)
    maximum = max(max(r['reference_force_N'],r['inferred_force_N']) for r in records) * 1.05
    axes[0].plot([0,maximum],[0,maximum],':',color='black',label='Ideal agreement')
    axes[0].set(xlabel='Independent reference force (N)',ylabel='Acoustic force estimate (N)')
    axes[1].axhline(0,color='black',ls=':')
    axes[1].set(xlabel='Independent reference force (N)',ylabel='Signed relative force error (%)')
    for ax in axes:
        ax.grid(alpha=.2)
        ax.legend()
    fig.suptitle('Isolated-string test: unfitted ideal-string baseline')
    output.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(output,dpi=180)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    predict = commands.add_parser('predict', help='Make a prediction before measuring sound')
    predict.add_argument('--force-N', type=float, required=True)
    predict.add_argument('--length-m', type=float, required=True)
    predict.add_argument('--density-kg-m', type=float, required=True)
    wav = commands.add_parser('audio', help='Measure a candidate peak, not automatically a fundamental')
    wav.add_argument('wav', type=Path)
    wav.add_argument('--start-s', type=float, default=0.)
    wav.add_argument('--end-s', type=float)
    wav.add_argument('--low-Hz', type=float, required=True)
    wav.add_argument('--high-Hz', type=float, required=True)
    compare = commands.add_parser('compare', help='Compare real measurements with unfitted predictions')
    compare.add_argument('measurements', type=Path)
    compare.add_argument('--output', type=Path, required=True)
    compare.add_argument('--plot', type=Path, help='Optional measured-versus-predicted figure')
    args = parser.parse_args()
    if args.command == 'predict':
        result = dict(predicted_fundamental_Hz=predict_frequency(args.force_N, args.length_m, args.density_kg_m),
                      scope='Isolated, uniform, flexible string; loaded density and vibrating span length.')
    elif args.command == 'audio':
        rate, x = wavfile.read(args.wav)
        end = args.end_s if args.end_s is not None else len(x)/rate
        if not 0 <= args.start_s < end <= len(x)/rate:
            raise ValueError('Crop must lie inside the audio recording.')
        result = spectrum_peak(x[int(args.start_s*rate):int(end*rate)], rate, args.low_Hz, args.high_Hz)
        result.update(source=str(args.wav), sha256=hashlib.sha256(args.wav.read_bytes()).hexdigest(), start_s=args.start_s, end_s=end)
    else:
        result = compare_records(json.loads(args.measurements.read_text()))
        result['input_sha256'] = hashlib.sha256(args.measurements.read_bytes()).hexdigest()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        if args.output.exists():
            raise FileExistsError('Use a new output name to preserve the earlier analysis.')
        if args.plot:
            plot_comparison(result,args.plot)
        args.output.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
