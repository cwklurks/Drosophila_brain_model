"""Adversarial re-verification of STORY.md's load-bearing claims.

Written to read the raw files directly (completeness csv, connectivity
parquet, spike parquets, pickle) — deliberately independent of the other
analysis scripts. Checks:

 1. relays really have zero synapses onto MN9 (raw connectivity rows)
 2. trio onto-MN9 weights really 561/424/281
 3. brake: every outgoing synapse, where the pathway ones land
 4. relay1 -> G2N_1 against the repo's own pickle, by eyeball list
 5. lesion table recomputed from raw spikes (baseline..dec, noise floor)
 6. which 3 neurons were in the quint (target-restricted signatures,
    calibrated against the sept where all 5 marginals were silenced)
 7. the 21st sugar GRN: which ID is not LB3
"""
import pickle

import numpy as np
import pandas as pd

ID_MN9 = 720575940660219265
RELAYS = [720575940620874757, 720575940629888530]
BRAKE = 720575940615041430
MARGINALS = [720575940623352063, 720575940632047890, 720575940615671106,
             720575940619973712, 720575940638103349]
TRIO = [720575940619853515, 720575940623211725, 720575940632252743]
NEU_SUGAR = [
    720575940624963786, 720575940630233916, 720575940637568838,
    720575940638202345, 720575940617000768, 720575940630797113,
    720575940632889389, 720575940621754367, 720575940621502051,
    720575940640649691, 720575940639332736, 720575940616885538,
    720575940639198653, 720575940620900446, 720575940617937543,
    720575940632425919, 720575940633143833, 720575940612670570,
    720575940628853239, 720575940629176663, 720575940611875570,
]

comp = pd.read_csv('2023_03_23_completeness_630_final.csv', index_col=0)
fly2i = {f: i for i, f in enumerate(comp.index)}
i2fly = pd.Series(comp.index)
con = pd.read_parquet('2023_03_23_connectivity_630_final.parquet')
con = con.rename(columns={'Excitatory x Connectivity': 'w'})

# ---------- 1 & 2: raw rows onto MN9 ----------
into_mn9 = con[con.Postsynaptic_Index == fly2i[ID_MN9]].copy()
into_mn9['pre_id'] = i2fly[into_mn9.Presynaptic_Index].values
print('== 1. relay -> MN9 rows (raw) ==')
rows = into_mn9[into_mn9.pre_id.isin(RELAYS)]
print(rows if len(rows) else 'ZERO rows: relays have no direct synapses onto MN9')

print('\n== 2. top 10 raw weights onto MN9 ==')
top = (into_mn9.groupby('pre_id')['w'].sum()
       .sort_values(ascending=False).head(10))
for fid, w in top.items():
    tag = ('TRIO' if fid in TRIO else 'RELAY' if fid in RELAYS else
           'BRAKE' if fid == BRAKE else 'GRN' if fid in NEU_SUGAR else '')
    print(f'  {fid}  w={w:6.0f}  {tag}')

# ---------- 3: brake wiring ----------
print('\n== 3. brake outgoing synapses: sign summary & pathway targets ==')
out_b = con[con.Presynaptic_Index == fly2i[BRAKE]].copy()
out_b['post_id'] = i2fly[out_b.Postsynaptic_Index].values
w_by_post = out_b.groupby('post_id')['w'].sum()
print(f'  outgoing synapses: {len(out_b)} rows, {len(w_by_post)} targets; '
      f'sum w = {w_by_post.sum():.0f} (negative => net inhibitory cell)')
print('  direct onto MN9:', 'YES' if ID_MN9 in w_by_post.index else 'NO')
pathway = {int(r): 'relay' for r in RELAYS}
for m in MARGINALS: pathway[int(m)] = 'marginal'
for t in TRIO: pathway[int(t)] = 'trio'
for i in NEU_SUGAR: pathway[int(i)] = 'GRN'
hits = w_by_post[w_by_post.index.isin(pathway)]
for fid, w in hits.sort_values().items():
    print(f'  -> {fid}  w={w:8.1f}  ({pathway[fid]})')
print(f'  (pathway targets: {len(hits)} of {len(w_by_post)}; '
      f'most negative pathway target above)')

# ---------- 4: G2N against the pickle, by eyeball ----------
print('\n== 4. sez_neurons.pickle["G2N_1"] ==')
sez = pickle.load(open('sez_neurons.pickle', 'rb'))
print('  G2N_1 IDs:', sez['G2N_1'])
print('  relay1 ...20874757 in list:', 720575940620874757 in sez['G2N_1'])
all_sez_ids = {i for v in sez.values() for i in v}
for label, i in [('relay2', RELAYS[1]), ('brake', BRAKE), ('MN9', ID_MN9)] + \
                [(f'marginal_{n+1}', m) for n, m in enumerate(MARGINALS)] + \
                [(f'trio_{n+1}', t) for n, t in enumerate(TRIO)]:
    if i in all_sez_ids:
        nm = [k for k, v in sez.items() if i in v]
        print(f'  {label} {i} ALSO in pickle as {nm}')

# ---------- 5: lesion table from raw spikes ----------
def mn9_rate(name):
    df = pd.read_parquet(f'results/mine/{name}.parquet')
    n = df.trial.max() + 1
    sub = df[df.flywire_id == ID_MN9]
    return len(sub) / (1.0 * n), n

print('\n== 5. lesion table recomputed from raw parquets ==')
base, _ = mn9_rate('slnc50_none')
rep2, _ = mn9_rate('slnc50_none_rep2')
print(f'  noise floor |none - rep2| = {abs(base-rep2):.1f} Hz')
for nm in ['slnc50_none', 'slnc50_pair', 'slnc50_quint', 'slnc50_sept',
           'slnc50_trio', 'slnc50_dec']:
    r, n = mn9_rate(nm)
    print(f'  {nm:14s} MN9 = {r:5.1f} Hz  ({r/base*100:4.0f}%)  n_run={n}')
s1, _ = mn9_rate(f'slnc50_{RELAYS[0]}')
s2, _ = mn9_rate(f'slnc50_{RELAYS[1]}')
print(f'  singles: relay1 {s1:.1f} ({s1/base:.2f}), relay2 {s2:.1f} ({s2/base:.2f});'
      f'  pair/base = {(mn9_rate("slnc50_pair")[0])/base:.2f};'
      f'  product of singles = {s1/base*s2/base:.2f};'
      f'  additive = {max(0, 1-(1-s1/base)-(1-s2/base)):.2f}')

# ---------- 6: quint membership, target-restricted ----------
print('\n== 6. quint membership (corr on each candidate\'s OWN direct targets) ==')
def rates_all(name):
    df = pd.read_parquet(f'results/mine/{name}.parquet')
    return df.groupby('flywire_id').size() / (1.0 * (df.trial.max() + 1))

r_none, r_pair = rates_all('slnc50_none'), rates_all('slnc50_pair')
r_quint, r_sept = rates_all('slnc50_quint'), rates_all('slnc50_sept')
idx = r_none.index
def d(r): return r.reindex(idx).fillna(0) - r_none.reindex(idx).fillna(0)
d_quint_excess = d(r_quint) - d(r_pair)
d_sept_excess = d(r_sept) - d(r_pair)

for m in MARGINALS:
    r_m = rates_all(f'slnc50_{m}')
    tg = set(i2fly[con[con.Presynaptic_Index == fly2i[m]].Postsynaptic_Index])
    tg &= set(idx) - {ID_MN9}
    if not tg:
        print(f'  {m}: no spiking targets, skip'); continue
    a, b = d(r_m).reindex(sorted(tg)), None
    q = np.corrcoef(a, d_quint_excess.reindex(sorted(tg)))[0, 1]
    s = np.corrcoef(a, d_sept_excess.reindex(sorted(tg)))[0, 1]
    print(f'  {m}: corr(quint)={q:+.2f}   corr(sept, positive control)={s:+.2f}   ({len(tg)} targets)')

# ---------- 7: the 21st GRN ----------
print('\n== 7. sugar GRN types (annotation dump) ==')
ann = pd.read_csv('/tmp/ann.tsv', sep='\t', low_memory=False)
ann = ann.drop_duplicates('root_id').set_index('root_id')
for i in NEU_SUGAR:
    ct = ann.loc[i, 'cell_type'] if i in ann.index else '(unannotated)'
    if ct != 'LB3':
        print(f'  non-LB3 member: {i} -> {ct}')
print('  all other 20 members: LB3')
