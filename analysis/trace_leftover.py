"""Trace where MN9's remaining drive comes from under each lesion condition.

Uses the connectivity matrix (v630, matching the runs) together with the
observed firing rates in slnc50_{none,pair,quint} to compute each synapse's
contribution (weight x presynaptic rate) onto MN9. Also wires up the circuit:
who feeds the relays, who feeds the brake, and what the brake inhibits.
"""
import json
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

RES = Path('results/mine')
ID_MN9 = 720575940660219265
RELAYS = [720575940620874757, 720575940629888530]
BRAKE = 720575940615041430
MARGINALS = [720575940623352063, 720575940632047890, 720575940615671106,
             720575940619973712, 720575940638103349]
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


def load_rates(name):
    df = pd.read_parquet(RES / f'{name}.parquet')
    n = df['trial'].max() + 1
    return df.groupby('flywire_id').size() / (T_RUN * n)


def main():
    SCREEN_IDS = [720575940612906518, 720575940615041430, 720575940615671106,
                  720575940618165019, 720575940619973712, 720575940620274085,
                  720575940620874757, 720575940622695448, 720575940623352063,
                  720575940626191306, 720575940627383685, 720575940629778554,
                  720575940629888530, 720575940630868793, 720575940632047890,
                  720575940632648612, 720575940633277209, 720575940638103349,
                  720575940652580086, 720575940660219265]
    rates = {k: load_rates(k) for k in ['slnc50_none', 'slnc50_none_rep2',
                                        'slnc50_pair', 'slnc50_quint']}
    for sid in SCREEN_IDS:
        rates[sid] = load_rates(f'slnc50_{sid}')

    df_comp = pd.read_csv('2023_03_23_completeness_630_final.csv', index_col=0)
    fly2i = {f: i for i, f in enumerate(df_comp.index)}
    df_con = pd.read_parquet('2023_03_23_connectivity_630_final.parquet')
    i2fly = pd.Series(df_comp.index)

    def synapses_into(fly_id):
        i = fly2i[fly_id]
        sub = df_con[df_con['Postsynaptic_Index'] == i]
        sub = sub.copy()
        sub['pre_id'] = i2fly[sub['Presynaptic_Index']].values
        return sub[['pre_id', 'Excitatory x Connectivity']]

    def synapses_out_of(fly_id):
        i = fly2i[fly_id]
        sub = df_con[df_con['Presynaptic_Index'] == i].copy()
        sub['post_id'] = i2fly[sub['Postsynaptic_Index']].values
        return sub[['post_id', 'Excitatory x Connectivity']]

    report = {}

    # ---------- MN9 inputs, ranked by contribution in each condition -------
    syn = synapses_into(ID_MN9)
    syn = syn.groupby('pre_id')['Excitatory x Connectivity'].sum().rename('w').reset_index()
    for cond in ['slnc50_none', 'slnc50_pair', 'slnc50_quint']:
        syn[cond] = syn['pre_id'].map(rates[cond]).fillna(0)
    syn['is_grn'] = syn['pre_id'].isin(NEU_SUGAR)
    syn['is_relay'] = syn['pre_id'].isin(RELAYS)
    syn['is_brake'] = syn['pre_id'] == BRAKE

    print('== MN9 in-degree: %d presynaptic neurons, net w = %.1f =='
          % (len(syn), syn['w'].sum()))
    for cond in ['slnc50_none', 'slnc50_pair', 'slnc50_quint']:
        syn[f'drive_{cond}'] = syn['w'] * syn[cond]
        pos = syn.loc[syn[f'drive_{cond}'] > 0, f'drive_{cond}']
        print(f"\n-- {cond}: total positive drive {pos.sum():.0f}, "
              f"GRN share {syn.loc[syn.is_grn, f'drive_{cond}'].clip(lower=0).sum()/max(pos.sum(),1e-9):.2f}, "
              f"relay share {syn.loc[syn.is_relay, f'drive_{cond}'].clip(lower=0).sum()/max(pos.sum(),1e-9):.2f}")
        top = syn.sort_values(f'drive_{cond}', ascending=False).head(12)
        for _, r in top.iterrows():
            tag = ('GRN' if r.is_grn else 'RELAY' if r.is_relay else
                   'BRAKE' if r.is_brake else '')
            print(f"  {int(r.pre_id)}  w={r.w:6.1f}  rate={r[cond]:6.1f}  "
                  f"drive={r[f'drive_{cond}']:7.1f}  {tag}")
    report['mn9_inputs'] = syn.to_dict(orient='records')

    # ---------- circuit wiring ---------------------------------------------
    print('\n== WHO FEEDS THE RELAYS (top excitatory, non-GRN) ==')
    for rid in RELAYS:
        s = synapses_into(rid)
        s = s[~s['pre_id'].isin(NEU_SUGAR)].nlargest(5, 'Excitatory x Connectivity')
        print(f'relay {rid} <- ' + ', '.join(f'{int(r.pre_id)}({r["Excitatory x Connectivity"]:.0f})'
                                             for _, r in s.iterrows()))
        s = synapses_into(rid)
        grn_w = s[s['pre_id'].isin(NEU_SUGAR)]['Excitatory x Connectivity'].sum()
        print(f'           total GRN input weight: {grn_w:.0f} over '
              f'{s.pre_id.isin(NEU_SUGAR).sum()} GRNs')

    print('\n== THE BRAKE (%d): outgoing inhibitory synapses ==' % BRAKE)
    out = synapses_out_of(BRAKE)
    neg = out[out['Excitatory x Connectivity'] < 0].nsmallest(10, 'Excitatory x Connectivity')
    for _, r in neg.iterrows():
        tag = ''
        if r.post_id in RELAYS: tag = '<- RELAY'
        if r.post_id == ID_MN9: tag = '<- MN9'
        if r.post_id in MARGINALS: tag = '<- marginal'
        if r.post_id in NEU_SUGAR: tag = '<- GRN'
        print(f"  -> {int(r.post_id)}  w={r['Excitatory x Connectivity']:8.1f} {tag}")
    report['brake_out'] = out.to_dict(orient='records')
    print('\n== WHO DRIVES THE BRAKE (top excitatory inputs) ==')
    inn = synapses_into(BRAKE)
    for _, r in inn.nlargest(8, 'Excitatory x Connectivity').iterrows():
        tag = ('GRN' if r.pre_id in NEU_SUGAR else 'RELAY' if r.pre_id in RELAYS
               else 'marginal' if r.pre_id in MARGINALS else '')
        print(f"  {int(r.pre_id)}  w={r['Excitatory x Connectivity']:8.1f} {tag}")

    # ---------- the premotor trio: who feeds THEM in each condition --------
    TRIO = [720575940619853515, 720575940623211725, 720575940632252743]
    print('\n== PREMOTOR TRIO ==')
    for t in TRIO:
        s = synapses_into(t).groupby('pre_id')['Excitatory x Connectivity'].sum()
        grn_w = s[s.index.isin(NEU_SUGAR)].sum()
        relay_w = s[s.index.isin(RELAYS)].sum()
        marg_w = s[s.index.isin(MARGINALS)].sum()
        brake_w = s.get(BRAKE, 0)
        print(f'{t}: GRN w={grn_w:.0f}, relay w={relay_w:.0f}, '
              f'marginal w={marg_w:.0f}, brake w={brake_w:.0f}, '
              f'rates none/pair/quint = '
              f"{rates['slnc50_none'].get(t,0):.1f}/{rates['slnc50_pair'].get(t,0):.1f}/{rates['slnc50_quint'].get(t,0):.1f}")
        top_in = s.sort_values(ascending=False).head(6)
        for pre, w in top_in.items():
            tag = ('GRN' if pre in NEU_SUGAR else 'RELAY' if pre in RELAYS
                   else 'marginal' if pre in MARGINALS else 'brake' if pre == BRAKE else '')
            r_q = rates['slnc50_quint'].get(pre, 0)
            print(f'   <- {pre}  w={w:6.0f}  quint rate={r_q:5.1f}  {tag}')

    # brake's own rate (why does silencing it matter if only sugar is driven?)
    print(f"\nbrake rate: none={rates['slnc50_none'].get(BRAKE,0):.1f} Hz, "
          f"pair={rates['slnc50_pair'].get(BRAKE,0):.1f}, "
          f"quint={rates['slnc50_quint'].get(BRAKE,0):.1f}")

    # top inhibitory contributors onto MN9 at baseline
    neg = syn[syn['w'] < 0].copy()
    neg['drive_none'] = neg['w'] * neg['slnc50_none']
    print('\n== TOP INHIBITORY INPUTS TO MN9 (baseline) ==')
    for _, r in neg.sort_values('drive_none').head(6).iterrows():
        print(f"  {int(r.pre_id)}  w={r.w:6.1f}  rate={r.slnc50_none:5.1f}  "
              f"drive={r.drive_none:7.1f}")

    # ---------- definitive quint membership --------------------------------
    # targets of each candidate that moved in quint beyond what pair explains
    base = rates['slnc50_none']
    dq = (rates['slnc50_quint'].reindex(rates['slnc50_none'].index).fillna(0) - base).drop(ID_MN9, errors='ignore')
    dp = (rates['slnc50_pair'].reindex(rates['slnc50_none'].index).fillna(0) - base).drop(ID_MN9, errors='ignore')
    extra = (dq - dp)
    print('\n== QUINT MEMBERSHIP (targets of candidate m that dropped extra in quint) ==')
    scores = {}
    others = [m for m in MARGINALS + [720575940620274085, 720575940629778554]]
    for m in others:
        d_m = (rates[m].reindex(rates['slnc50_none'].index).fillna(0) - base).drop(ID_MN9, errors='ignore')
        scores[m] = float(np.corrcoef(d_m.values, extra.values)[0, 1])
    for m, s in sorted(scores.items(), key=lambda kv: -kv[1]):
        print(f'  {m}  corr(delta_single, delta_quint - delta_pair) = {s:+.3f}')
    report['quint_membership_scores'] = scores

    with open('analysis/wiring_report.json', 'w') as f:
        json.dump(report, f, indent=1, default=str)
    syn.to_csv('analysis/mn9_inputs.csv', index=False)


if __name__ == '__main__':
    main()
