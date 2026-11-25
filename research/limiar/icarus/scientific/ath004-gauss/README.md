# GAUSS-01 | validation
Read [locked protocol](PROTOCOL.md) before data collection. From this folder:
```sh
free -h
cc --version | head -1
nice -n 10 cc -std=c11 -O2 -Wall -Wextra -Werror -fPIC -shared -ffp-contract=off ../ath003-lever/lever.c -o ../ath003-lever/liblever.so -lm
python3 -m unittest -v
nice -n 10 python3 gauss.py run --session 0 --checkpoint .gauss-smoke --output gauss-smoke.json
# Only after successful smoke. Run each session separately, not a loop.
nice -n 10 python3 gauss.py run --session 1 --checkpoint .gauss-s01 --output gauss-s01.json
```
Repeat separately in fresh measurement sessions for 2,3,4,5, with matching checkpoint/output suffixes. Do not pull/recompile between sessions. Resume same command after safety stop; retain logs. When all five complete:
```sh
python3 gauss.py analyze gauss-s01.json gauss-s02.json gauss-s03.json gauss-s04.json gauss-s05.json --output gauss-confirmation.json
```
Do not use smoke in inference. Preserve full files, compiler info and checkpoint logs. Report all results including failures. Tests prepared, local execution pending.
