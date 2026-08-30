"""Reconstruct all results in results/mine from the parquet spike files.

Builds:
  - per-experiment firing rates (auto-detects n_run per experiment)
  - dose-response table
  - silencing screen table (slnc_ = 100 Hz drive, slnc50_ = drive used in the 50-series)
  - inference of which neurons were silenced in pair/quint (silencing cuts a
    neuron's *outgoing* synapses, so we match downstream rate-change signatures)
  - saves a machine-readable summary to analysis/summary.json
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

RES = Path('results/mine')
OUT = Path('analysis')
OUT.mkdir(exist_ok=True)

ID_MN9 = 720575940660219265
NEU_SUGAR = [
    720575940624963786, 720575940630233916, 720575940637568838,
    720575940638202345, 720575940617000768, 720575940630797113,
    720575940632889389, 720575940621754367, 720575940621502051,
    720575940640649691, 720575940639332736, 720575940616885538,
    720575940639198653, 720575940620900446, 720575940617937543,
    720575940632425919, 720575940633143833, 720575940612670570,
    720575940628853239, 720575940629176663, 720575940611875570,
]
T_RUN = 1.0


def load_rates(path):
    df = pd.read_parquet(path)
    n_run = int(df['trial'].max()) + 1
    counts = df.groupby('flywire_id').size()
    rates = counts / (T_RUN * n_run)
    return rates, n_run


def main():
    summary = {}

    # ---- collect every experiment -------------------------------------
    exps = {}
    for p in sorted(RES.glob('*.parquet')):
        exps[p.stem] = load_rates(p)

    # ---- dose-response --------------------------------------------------
    rates_hz = [10, 25, 50, 100, 200]
    dose = {}
    for r in rates_hz:
        e = exps[f'sugarR_{r}Hz']
        dose[r] = {
            'mn9': float(e[0].get(ID_MN9, 0)),
            'grn_mean': float(e[0].reindex(NEU_SUGAR).fillna(0).mean()),
            'n_run': e[1],
        }
    summary['dose_response'] = dose

    # ---- 100 Hz screen (slnc_*) ----------------------------------------
    base100 = exps['sugarR_100Hz'][0]
    screen100 = {}
    for name, (rates, n_run) in exps.items():
        if name.startswith('slnc_'):
            sid = int(name.split('_')[1])
            screen100[sid] = {
                'mn9': float(rates.get(ID_MN9, 0)),
                'ratio': float(rates.get(ID_MN9, 0) / base100.get(ID_MN9, np.nan)),
                'n_run': n_run,
            }
    summary['screen_100hz'] = {
        'baseline_mn9': float(base100.get(ID_MN9)),
        'singles': screen100,
    }

    # ---- 50-series ------------------------------------------------------
    base50 = exps['slnc50_none'][0]
    rep2 = exps['slnc50_none_rep2'][0]
    # noise floor: MN9 rate difference between the two identical baselines
    common = base50.index.union(rep2.index)
    noise = (base50.reindex(common).fillna(0) - rep2.reindex(common).fillna(0)).abs()
    summary['series50'] = {
        'baseline_mn9': float(base50.get(ID_MN9)),
        'rep2_mn9': float(rep2.get(ID_MN9)),
        'grn_mean': float(base50.reindex(NEU_SUGAR).fillna(0).mean()),
        'n_run': exps['slnc50_none'][1],
        'noise_floor_mn9_absdiff': float(abs(base50.get(ID_MN9, 0) - rep2.get(ID_MN9, 0))),
        'noise_floor_median_absdiff_all_neurons': float(noise.median()),
        'noise_floor_p90_absdiff_all_neurons': float(noise.quantile(0.9)),
    }
    screen50 = {}
    for name, (rates, n_run) in exps.items():
        if name.startswith('slnc50_720'):
            sid = int(name.split('_')[1])
            screen50[sid] = {
                'mn9': float(rates.get(ID_MN9, 0)),
                'ratio': float(rates.get(ID_MN9, 0) / base50.get(ID_MN9, np.nan)),
                'n_run': n_run,
            }
    summary['series50']['singles'] = screen50
    for k in ['slnc50_pair', 'slnc50_quint']:
        r, n = exps[k]
        summary['series50'][k] = {
            'mn9': float(r.get(ID_MN9, 0)),
            'ratio': float(r.get(ID_MN9, 0) / base50.get(ID_MN9, np.nan)),
            'n_run': n,
        }

    # ---- infer silenced sets in pair/quint ------------------------------
    # Silencing cuts outgoing synapses; the silenced cell keeps spiking but its
    # targets lose input. Match the downstream rate-change signature.
    gidx = base50.index
    for sid in screen50:
        gidx = gidx.union(exps[f'slnc50_{sid}'][0].index)
    for k in ['slnc50_pair', 'slnc50_quint']:
        gidx = gidx.union(exps[k][0].index)
    gidx = gidx.drop(ID_MN9, errors='ignore')

    def delta(sig):
        return (sig.reindex(gidx).fillna(0) - base50.reindex(gidx).fillna(0))

    d_singles = {sid: delta(exps[f'slnc50_{sid}'][0]) for sid in screen50}
    d_pair = delta(exps['slnc50_pair'][0])
    d_quint = delta(exps['slnc50_quint'][0])

    def best_match(target, sizes):
        from itertools import combinations
        ids = list(d_singles)
        best = {}
        for k in sizes:
            best_score, best_combo = -np.inf, None
            for combo in combinations(ids, k):
                pred = sum(d_singles[i] for i in combo)
                score = np.corrcoef(pred.values, target.values)[0, 1]
                if score > best_score:
                    best_score, best_combo = score, combo
            best[k] = {'combo': list(best_combo), 'corr': float(best_score)}
        return best

    summary['pair_quint_inference'] = {
        'pair': best_match(d_pair, [2]),
        'quint': best_match(d_quint, [2, 3, 4, 5, 6]),
    }

    with open(OUT / 'summary.json', 'w') as f:
        json.dump(summary, f, indent=1, default=str)

    # ---- console report ---------------------------------------------------
    print('== DOSE RESPONSE (n_run=5 each) ==')
    print(f"{'drive':>6} {'GRN mean':>9} {'MN9':>7}")
    for r in rates_hz:
        d = dose[r]
        print(f"{r:>6} {d['grn_mean']:>9.1f} {d['mn9']:>7.1f}")

    print("\n== 100 Hz SCREEN (baseline MN9 = %.1f) ==" % summary['screen_100hz']['baseline_mn9'])
    for sid, d in sorted(screen100.items(), key=lambda kv: kv[1]['mn9']):
        tag = ' <MN9 itself>' if sid == ID_MN9 else ''
        print(f"{sid}  MN9={d['mn9']:6.1f}  ratio={d['ratio']:5.2f}{tag}")

    print("\n== 50-SERIES (baseline MN9 = %.1f, rep2 = %.1f, GRN mean = %.1f) ==" % (
        summary['series50']['baseline_mn9'], summary['series50']['rep2_mn9'], summary['series50']['grn_mean']))
    for sid, d in sorted(screen50.items(), key=lambda kv: kv[1]['mn9']):
        tag = ' <MN9 itself>' if sid == ID_MN9 else ''
        print(f"{sid}  MN9={d['mn9']:6.1f}  ratio={d['ratio']:5.2f}{tag}")
    for k in ['slnc50_pair', 'slnc50_quint']:
        print(f"{k:>14}: MN9={summary['series50'][k]['mn9']:6.1f}  ratio={summary['series50'][k]['ratio']:5.2f}")

    print('\n== INFERRED SILENCED SETS ==')
    print('pair :', summary['pair_quint_inference']['pair'])
    print('quint:', json.dumps(summary['pair_quint_inference']['quint'], indent=1))


if __name__ == '__main__':
    main()
