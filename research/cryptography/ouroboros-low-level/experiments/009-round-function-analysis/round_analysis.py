from __future__ import annotations
import argparse, csv, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP008 = HERE.parent / "008-reduced-feistel"
sys.path.insert(0, str(EXP008))
from feistel16 import SBOX4, P8, permute8, substitute8, round_function

N = 256

def parity(x: int) -> int:
    return x.bit_count() & 1

def round_core(x: int) -> int:
    return permute8(substitute8(x))

def build_tables(function):
    ddt = [[0] * N for _ in range(N)]
    outputs = [function(x) for x in range(N)]
    for alpha in range(N):
        for x in range(N):
            ddt[alpha][outputs[x] ^ outputs[x ^ alpha]] += 1
    lat = [[0] * N for _ in range(N)]
    for b in range(N):
        column = [1 if parity(b & outputs[x]) == 0 else -1 for x in range(N)]
        step = 1
        while step < N:
            for base in range(0, N, step * 2):
                for j in range(base, base + step):
                    u, v = column[j], column[j + step]
                    column[j], column[j + step] = u + v, u - v
            step *= 2
        for a, value in enumerate(column):
            lat[a][b] = value
    return ddt, lat

def analyze():
    ddt, lat = build_tables(round_core)
    nonzero_ddt = [(a,b,v) for a in range(1,N) for b,v in enumerate(ddt[a]) if v]
    ddt_max = max(v for _,_,v in nonzero_ddt)
    ddt_cells = [(a,b,v) for a,b,v in nonzero_ddt if v == ddt_max]
    lat_nontrivial = [(a,b,lat[a][b]) for a in range(1,N) for b in range(1,N)]
    lat_max = max(abs(w) for _,_,w in lat_nontrivial)
    lat_cells = [(a,b,w) for a,b,w in lat_nontrivial if abs(w)==lat_max]
    nonzero_weights = sorted({v for _,_,v in nonzero_ddt})
    lat_abs_hist = {}
    for _,_,w in lat_nontrivial:
        lat_abs_hist[str(abs(w))] = lat_abs_hist.get(str(abs(w)),0)+1
    assert all(sum(row)==N for row in ddt)
    assert ddt[0][0] == N and sum(ddt[0][1:]) == 0
    assert all(sum(ddt[a])==N for a in range(1,N))
    assert len({round_core(x) for x in range(N)}) == N
    key_invariance_checks = []
    for key in (0x00, 0x5A, 0xFF):
        keyed_ddt, keyed_lat = build_tables(lambda x, k=key: round_function(x, k))
        ddt_same = keyed_ddt == ddt
        lat_abs_same = [[abs(v) for v in row] for row in keyed_lat] == [[abs(v) for v in row] for row in lat]
        assert ddt_same and lat_abs_same
        key_invariance_checks.append({"round_key":f"0x{key:02X}","ddt_counts_identical_by_input_translation":ddt_same,"lat_absolute_walsh_identical_by_sign_factor":lat_abs_same})
    summary = {
      "experiment":"OUROBOROS-009",
      "target":"EXP-008 round function F(R,K)=P8(S(R XOR K))",
      "analysis_reduction":"G(x)=P8(S(x)); fixed-key XOR input translation preserves DDT counts and LAT absolute values",
      "domain_bits":8,
      "enumerated_inputs_per_table":N,
      "ddt":{"input_differences":N,"output_differences":N,"max_count_nonzero_input_difference":ddt_max,"max_probability":ddt_max/N,"max_cells_count":len(ddt_cells),"max_cells_first_32":[{"input_delta":a,"output_delta":b,"count":v} for a,b,v in ddt_cells[:32]],"nonzero_entry_values":nonzero_weights,"row_sum_min":min(map(sum,ddt)),"row_sum_max":max(map(sum,ddt))},
      "lat":{"nontrivial_mask_pairs":(N-1)*(N-1),"max_abs_walsh_nontrivial":lat_max,"max_abs_correlation":lat_max/N,"max_abs_bias":lat_max/2,"max_cells_count":len(lat_cells),"max_cells_first_32":[{"input_mask":a,"output_mask":b,"walsh":w} for a,b,w in lat_cells[:32]],"absolute_walsh_histogram":lat_abs_hist},
      "permutation":True,
      "fixed_round_key_invariance_checks":key_invariance_checks,
      "scope":"Exact round-function component analysis only; not full 8-round cipher security or a security proof."
    }
    return summary,ddt,lat

def write(out: Path, summary, ddt, lat):
    out.mkdir(parents=True,exist_ok=True)
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    for name, table in [('ddt.csv',ddt),('lat_walsh.csv',lat)]:
      with (out/name).open('w',newline='') as f:
        w=csv.writer(f); w.writerow(['mask']+[f'{i:02X}' for i in range(N)])
        for i,row in enumerate(table): w.writerow([f'{i:02X}']+row)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--output',type=Path,default=Path('results'))
    a=p.parse_args()
    summary,ddt,lat=analyze()
    write(a.output,summary,ddt,lat)
    print(json.dumps(summary,indent=2))
    print('Saved',a.output.resolve())

if __name__=='__main__':
    main()
