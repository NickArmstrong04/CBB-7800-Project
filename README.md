# Routine Labs to Liver Elastography Referral: A Data-Driven Alternative to FIB-4


CBB 7400 class project.
Clinical decision support for a graduate biomedical informatics class project.
Question: given routine bloodwork and vitals, should a patient be referred for
liver elastography (FibroScan)? The baseline to beat is FIB-4.

Data: NHANES 2017–March 2020 pre-pandemic cycle (public CDC files, prefix `P_`).
Liver elastography (`P_LUX`) defines the population; files join on `SEQN`.

## Download and merge the data

```bash
pip install -r requirements.txt
python merge_lab_liver.py                                   # P_LUX + P_BIOPRO
python merge_lab_liver.py --extra P_CBC P_DEMO              # add CBC + demographics
python merge_lab_liver.py --extra P_CBC P_DEMO P_GHB P_HDL P_HEPBD P_HEPC --how left
```

Raw `.xpt` files are cached in `data/raw/`; the merged CSV is written to
`data/processed/lab_liver.csv`. Data files are git-ignored.

## File counts (unique SEQN)

| File | Participants |
|---|---|
| P_DEMO | 15,560 |
| P_DR1TOT (dietary day 1) | 14,300 |
| P_CBC | 13,772 |
| P_LUX (elastography) | 10,409 |
| P_BIOPRO (biochemistry) | 10,409 |

All 10,409 elastography participants also appear in P_BIOPRO and P_CBC.
Complete elastography exams (`LUAXSTAT = 1`): 9,023.
