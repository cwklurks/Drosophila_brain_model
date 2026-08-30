"""The leftover experiments: close the loop on the premotor trio.

Runs (50 Hz sugar drive, n_run=10, matching the slnc50 series):
  slnc50_trio : silence the 3 premotor interneurons -> is MN9 floored?
  slnc50_sept : silence relays + all 5 marginals (7 neurons) -> full 1st layer
  slnc50_dec  : silence those 7 + the trio (10 neurons) -> everything found
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from brian2 import Hz

from model import run_exp, default_params as params

config = {
    'path_res': './results/mine',
    'path_comp': './2023_03_23_completeness_630_final.csv',
    'path_con': './2023_03_23_connectivity_630_final.parquet',
    'n_proc': 1,
}

neu_sugar = [
    720575940624963786, 720575940630233916, 720575940637568838,
    720575940638202345, 720575940617000768, 720575940630797113,
    720575940632889389, 720575940621754367, 720575940621502051,
    720575940640649691, 720575940639332736, 720575940616885538,
    720575940639198653, 720575940620900446, 720575940617937543,
    720575940632425919, 720575940633143833, 720575940612670570,
    720575940628853239, 720575940629176663, 720575940611875570,
]

RELAYS = [720575940620874757, 720575940629888530]
MARGINALS = [720575940623352063, 720575940632047890, 720575940615671106,
             720575940619973712, 720575940638103349]
TRIO = [720575940619853515, 720575940623211725, 720575940632252743]

p50 = dict(params)
p50['r_poi'] = 50 * Hz
p50['n_run'] = 10

run_exp(exp_name='slnc50_trio', neu_exc=neu_sugar, neu_slnc=TRIO,
        params=p50, **config)
run_exp(exp_name='slnc50_sept', neu_exc=neu_sugar, neu_slnc=RELAYS + MARGINALS,
        params=p50, **config)
run_exp(exp_name='slnc50_dec', neu_exc=neu_sugar,
        neu_slnc=RELAYS + MARGINALS + TRIO, params=p50, **config)
