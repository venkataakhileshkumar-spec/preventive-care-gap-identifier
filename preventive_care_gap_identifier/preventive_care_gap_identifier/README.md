# Preventive Care Gap Identifier

Finds members who are overdue for recommended preventive services by comparing
member data (age, sex, conditions) against claims history.

## Structure
- `preventive_care_gap_identifier.py` - main script (Python 3.9+, no dependencies)
- `data/members.csv`, `data/claims.csv` - sample input data
- `output/care_gaps.csv`, `output/summary.txt` - sample output

## Run
    python preventive_care_gap_identifier.py

The script reads `members.csv` and `claims.csv` from the current folder and
generates sample data if they are missing. To use the bundled sample data, copy
the two files from `data/` next to the script, or delete them to regenerate.

## Input format
- members.csv: member_id, name, dob (YYYY-MM-DD), sex (F/M), conditions (separate with ;)
- claims.csv: member_id, service_date (YYYY-MM-DD), service_code

Valid service codes: WELLNESS, FLU, MAMMOGRAM, PAP, COLORECTAL, LIPID, HBA1C, EYE_EXAM

## Note
Screening rules are simplified for demonstration and are not clinical guidance.
