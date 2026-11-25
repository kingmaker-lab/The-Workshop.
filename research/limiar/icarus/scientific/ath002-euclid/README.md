# EUCLID-01 | bounded verification
Run on the existing Linux machine. Python standard library and existing C compiler. No data downloads, large training, external load or sudo. ARGOS safety checks (256 MiB available, 80 C) during checks; compiler separate, check memory before building. One process at a time. Do not bypass guard. No benchmark claim.
```sh
free -h
nice -n 10 cc -std=c11 -O2 -Wall -Wextra -Werror -fPIC -shared -ffp-contract=off native_probe.c -o libeuclid.so -lm
nice -n 10 python3 euclid.py > euclid-local.json.tmp && mv euclid-local.json.tmp euclid-local.json
```
Tests use original C rank_batch, METIS select and ARGOS extend, no engine modifications. Native probe reconstructs selected indices through label toggles; read PROOFS.md for assumptions. Bounded exhaustive n<=8 and exact rational HT n<=6, larger native differential n<=256. Output only on success. Assertions must be enabled. No claimed run before local verification. Compiler output not included in JSON; preserve compiler version/flags and revision with result. Review and ARCHIMEDES still pending.
