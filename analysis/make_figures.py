"""Generate all figures for the sugar-circuit story + a names lookup CSV."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

RES = Path('results/mine')
FIG = Path('analysis/figures')
FIG.mkdir(parents=True, exist_ok=True)

ID_MN9 = 720575940660219265
NEU_SUGAR = [720575940624963786, 720575940630233916, 720575940637568838,
             720575940638202345, 720575940617000768, 720575940630797113,
             720575940632889389, 720575940621754367, 720575940621502051,
             720575940640649691, 720575940639332736, 720575940616885538,
             720575940639198653, 720575940620900446, 720575940617937543,
             720575940632425919, 720575940633143833, 720575940612670570,
             720575940628853239, 720575940629176663, 720575940611875570]
RELAYS = [720575940620874757, 720575940629888530]
BRAKE = 720575940615041430
MARGINALS = [720575940623352063, 720575940632047890, 720575940615671106,
             720575940619973712, 720575940638103349]
TRIO = [720575940619853515, 720575940623211725, 720575940632252743]


def rates(name):
    df = pd.read_parquet(RES / f'{name}.parquet')
    return df.groupby('flywire_id').size() / (1.0 * (df.trial.max() + 1))


def short(i):
    return '…' + str(i)[-6:]


# ---------------- names CSV ----------------
ann = pd.read_csv('/tmp/ann.tsv', sep='\t', low_memory=False)
ann = ann.drop_duplicates('root_id').set_index('root_id')
sez = pickle.load(open('sez_neurons.pickle', 'rb')) if False else None
import pickle
sez = pickle.load(open('sez_neurons.pickle', 'rb'))
sez_names = {}
for nm, ids in sez.items():
    for i in ids:
        sez_names.setdefault(i, nm)

rows = []
for role, ids in [('output', [ID_MN9]), ('relay', RELAYS), ('brake', [BRAKE]),
                  ('marginal', MARGINALS), ('premotor_trio', TRIO)] + \
                 [('sugar_grn', [i]) for i in NEU_SUGAR]:
    for i in ids:
        if i in ann.index:
            r = ann.loc[i]
            ct, nt, sc, side = r['cell_type'], r['top_nt'], r['super_class'], r['side']
        else:
            ct = nt = sc = side = '(unannotated)'
        rows.append({'flywire_id': i, 'role': role, 'cell_type': ct,
                     'seu_pickle_name': sez_names.get(i, ''),
                     'nt': nt, 'class': sc, 'side': side})
pd.DataFrame(rows).to_csv('analysis/names.csv', index=False)

# ---------------- fig 1: dose-response ----------------
drives = [10, 25, 50, 100, 200]
r = {k: rates(f'sugarR_{k}Hz') for k in drives}
grn_mean = [r[k].reindex(NEU_SUGAR).fillna(0).mean() for k in drives]
mn9 = [r[k].get(ID_MN9, 0) for k in drives]

fig, ax = plt.subplots(figsize=(5.2, 3.8))
ax.plot(drives, grn_mean, 'o--', color='#888', label='GRN delivered (mean)')
ax.plot(drives, mn9, 'o-', color='#c0392b', lw=2, label='MN9 (CB0701)')
ax.set_xscale('log')
ax.set_xlabel('sugar GRN activation rate (Hz, log)')
ax.set_ylabel('firing rate (Hz)')
ax.set_title('Dose–response: threshold, then rise')
ax.legend()
ax.grid(alpha=.3)
fig.tight_layout()
fig.savefig(FIG / 'fig1_dose_response.png', dpi=150)

# ---------------- fig 2: lesion ladder ----------------
base50 = rates('slnc50_none')
b = base50.get(ID_MN9, 0)
conds = [('none', 'slnc50_none'), ('pair', 'slnc50_pair'),
         ('quint', 'slnc50_quint'),
         ('sept', 'slnc50_sept'),
         ('trio\nonly', 'slnc50_trio'),
         ('all 10', 'slnc50_dec')]
vals = [rates(n).get(ID_MN9, 0) for _, n in conds]
noise = 1.9

fig, ax = plt.subplots(figsize=(7, 3.8))
bars = ax.bar([c for c, _ in conds], vals,
              color=['#2c3e50', '#2980b9', '#2980b9', '#2980b9', '#27ae60', '#8e44ad'])
ax.axhline(noise, color='crimson', ls='--', lw=1, label=f'noise floor ({noise} Hz)')
for rect, v in zip(bars, vals):
    ax.text(rect.get_x() + rect.get_width() / 2, v + .4, f'{v/b*100:.0f}%',
            ha='center', fontsize=9)
ax.set_ylabel('MN9 rate (Hz)')
ax.set_title(f'Lesion ladder at 50 Hz drive (baseline MN9 = {b:.1f} Hz)')
ax.legend()
fig.tight_layout()
fig.savefig(FIG / 'fig2_lesion_ladder.png', dpi=150)

# ---------------- fig 3: screen, 50 Hz series ----------------
singles = {}
for p in RES.glob('slnc50_720*.parquet'):
    sid = int(p.stem.split('_')[1])
    singles[sid] = rates(p.stem).get(ID_MN9, 0)
names_map = dict(zip(
    [720575940620874757, 720575940629888530, 720575940615041430],
    ['G2N (CB0616)', 'CB0192', 'brake (unnamed)']))
srt = sorted(singles.items(), key=lambda kv: kv[1])
fig, ax = plt.subplots(figsize=(6.5, 6.5))
labels, vals, cols = [], [], []
for sid, v in srt:
    lab = names_map.get(sid, short(sid))
    if sid == ID_MN9:
        lab += ' (MN9)'
    labels.append(lab)
    vals.append(v)
    if sid in RELAYS:
        cols.append('#27ae60')
    elif sid == BRAKE:
        cols.append('#e67e22')
    elif v > b:
        cols.append('#c0392b')
    else:
        cols.append('#95a5a6')
ax.barh(labels, vals, color=cols)
ax.axvline(b, color='#2c3e50', lw=1, ls=':', label=f'baseline {b:.1f}')
ax.axvline(noise, color='crimson', ls='--', lw=1, label='noise floor')
ax.set_xlabel('MN9 rate after silencing one neuron (Hz)')
ax.set_title('Single-neuron silencing screen (50 Hz drive, n=10)')
ax.legend()
fig.tight_layout()
fig.savefig(FIG / 'fig3_screen.png', dpi=150)

# ---------------- fig 4: circuit schematic ----------------
fig, ax = plt.subplots(figsize=(8.6, 5))
ax.axis('off')
ax.set_xlim(0, 10)
ax.set_ylim(0, 6)

def box(x, y, w, h, label, color='#dfe6e9', fs=9):
    ax.add_patch(plt.Rectangle((x, y), w, h, facecolor=color,
                               edgecolor='#2d3436', lw=1.2, zorder=2))
    ax.text(x + w / 2, y + h / 2, label, ha='center', va='center',
            fontsize=fs, zorder=3)

def arrow(x0, y0, x1, y1, color='#2d3436', ls='-', lw=1.6):
    ax.annotate('', xy=(x1, y1), xytext=(x0, y0),
                arrowprops=dict(arrowstyle='->', color=color, lw=lw, ls=ls))

box(0.2, 3.8, 1.7, 1.6, '21 sugar GRNs\n(LB3, labellum)\n100% drive', '#ffeaa7')
box(2.9, 4.9, 2.6, 0.85, 'G2N / CB0616  (relay 1)', '#55efc4')
box(2.9, 3.8, 2.6, 0.85, 'CB0192  (relay 2)', '#55efc4')
box(2.9, 2.6, 2.6, 1.05, 'marginals: CB0393,\nDNge059, CB0118,\nCB0911, rattle/CB0499', '#b2bec3')
box(6.1, 3.3, 1.9, 2.2, '2nd-order layer\nCB0824, kitty/CB0759,\nCB0051, CB0467,\nroundup/CB0553-R …', '#a29bfe')
box(6.1, 1.4, 1.9, 1.3, 'premotor trio\nCB0553-L (roundup),\nCB0493, unnamed', '#fd79a8')
box(8.6, 1.4, 1.2, 1.3, 'MN9\nCB0701\n(motor)', '#ff7675')
box(4.3, 0.1, 3.0, 0.8, 'brake (unnamed)\n41.8 Hz at baseline', '#e17055')

arrow(1.9, 4.6, 2.9, 5.3)
arrow(1.9, 4.4, 2.9, 4.25)
arrow(1.9, 4.2, 2.9, 3.2)
arrow(5.5, 5.3, 6.1, 5.0)
arrow(5.5, 4.2, 6.1, 4.6)
arrow(5.5, 3.1, 6.1, 3.9)
arrow(8.0, 3.5, 8.9, 2.8)
arrow(8.0, 2.0, 8.6, 2.0)
ax.text(8.25, 2.9, '×', fontsize=12, color='#2d3436')
ax.annotate('', xy=(6.7, 1.4), xytext=(5.9, 0.9),
            arrowprops=dict(arrowstyle='-|>', color='#d63031', lw=2))
ax.text(3.1, 1.15, 'inhibits trio (w = −100 onto CB0553-L)', fontsize=8, color='#d63031')

ax.set_title('Sugar → proboscis pathway as dissected (all names from FlyWire v630 typing)')
fig.tight_layout()
fig.savefig(FIG / 'fig4_circuit.png', dpi=150)
print('figures written to', FIG)
print(open('analysis/names.csv').read()[:600])
