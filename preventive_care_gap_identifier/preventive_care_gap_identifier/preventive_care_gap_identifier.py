"""
Preventive Care Gap Identifier
------------------------------
Finds members who are overdue for recommended preventive services by
comparing member data (age, sex, conditions) against claims history.

Run:  python preventive_care_gap_identifier.py
Input files (auto-generated with sample data if missing):
    members.csv : member_id, name, dob, sex, conditions
    claims.csv  : member_id, service_date, service_code
Output:
    care_gaps.csv  + summary printed to console
"""

import csv
import random
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

AS_OF = date.today()

# ---------------------------------------------------------------------------
# 1. Preventive care rules (simplified, for demonstration only)
#    condition=None means the rule applies to everyone who meets age/sex.
# ---------------------------------------------------------------------------
RULES = [
    {"code": "WELLNESS",    "name": "Annual Wellness Visit",       "sex": None, "min_age": 18, "max_age": 120, "interval_months": 12,  "condition": None},
    {"code": "FLU",         "name": "Flu Vaccine",                 "sex": None, "min_age": 18, "max_age": 120, "interval_months": 12,  "condition": None},
    {"code": "MAMMOGRAM",   "name": "Mammogram",                   "sex": "F",  "min_age": 50, "max_age": 74,  "interval_months": 24,  "condition": None},
    {"code": "PAP",         "name": "Cervical Cancer Screening",   "sex": "F",  "min_age": 21, "max_age": 65,  "interval_months": 36,  "condition": None},
    {"code": "COLORECTAL",  "name": "Colorectal Cancer Screening", "sex": None, "min_age": 45, "max_age": 75,  "interval_months": 120, "condition": None},
    {"code": "LIPID",       "name": "Cholesterol Screening",       "sex": None, "min_age": 40, "max_age": 75,  "interval_months": 60,  "condition": None},
    {"code": "HBA1C",       "name": "HbA1c Test (Diabetes)",       "sex": None, "min_age": 18, "max_age": 75,  "interval_months": 6,   "condition": "diabetes"},
    {"code": "EYE_EXAM",    "name": "Diabetic Eye Exam",           "sex": None, "min_age": 18, "max_age": 75,  "interval_months": 12,  "condition": "diabetes"},
]


# ---------------------------------------------------------------------------
# 2. Helpers
# ---------------------------------------------------------------------------
def calc_age(dob: date, as_of: date) -> int:
    return as_of.year - dob.year - ((as_of.month, as_of.day) < (dob.month, dob.day))


def months_between(earlier: date, later: date) -> int:
    return (later.year - earlier.year) * 12 + later.month - earlier.month - (later.day < earlier.day)


def is_eligible(member: dict, rule: dict) -> bool:
    if rule["sex"] and member["sex"] != rule["sex"]:
        return False
    if not (rule["min_age"] <= member["age"] <= rule["max_age"]):
        return False
    if rule["condition"] and rule["condition"] not in member["conditions"]:
        return False
    return True


# ---------------------------------------------------------------------------
# 3. Data loading
# ---------------------------------------------------------------------------
def load_members(path: str) -> list[dict]:
    members = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            dob = date.fromisoformat(row["dob"])
            members.append({
                "member_id": row["member_id"],
                "name": row["name"],
                "sex": row["sex"].upper(),
                "age": calc_age(dob, AS_OF),
                "conditions": {c.strip().lower() for c in row["conditions"].split(";") if c.strip()},
            })
    return members


def load_claims(path: str) -> dict:
    """Returns {member_id: {service_code: most_recent_service_date}}"""
    latest = defaultdict(dict)
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            d = date.fromisoformat(row["service_date"])
            code = row["service_code"]
            if code not in latest[row["member_id"]] or d > latest[row["member_id"]][code]:
                latest[row["member_id"]][code] = d
    return latest


# ---------------------------------------------------------------------------
# 4. Core logic: find gaps
# ---------------------------------------------------------------------------
def find_gaps(members: list[dict], claims: dict):
    gaps = []
    stats = {r["code"]: {"eligible": 0, "compliant": 0} for r in RULES}

    for m in members:
        for rule in RULES:
            if not is_eligible(m, rule):
                continue
            stats[rule["code"]]["eligible"] += 1

            last = claims.get(m["member_id"], {}).get(rule["code"])
            if last is None:
                status, months_overdue = "Never done", ""
            else:
                months_since = months_between(last, AS_OF)
                if months_since <= rule["interval_months"]:
                    stats[rule["code"]]["compliant"] += 1
                    continue
                status = "Overdue"
                months_overdue = months_since - rule["interval_months"]

            gaps.append({
                "member_id": m["member_id"],
                "name": m["name"],
                "age": m["age"],
                "sex": m["sex"],
                "service": rule["name"],
                "status": status,
                "last_service_date": last.isoformat() if last else "",
                "months_overdue": months_overdue,
            })
    return gaps, stats


# ---------------------------------------------------------------------------
# 5. Reporting
# ---------------------------------------------------------------------------
def write_gaps_csv(gaps: list[dict], path: str):
    if not gaps:
        return
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=gaps[0].keys())
        writer.writeheader()
        writer.writerows(gaps)


def print_summary(members, gaps, stats):
    print(f"\nPreventive Care Gap Report (as of {AS_OF})")
    print("=" * 62)
    print(f"Members analysed : {len(members)}")
    print(f"Total care gaps  : {len(gaps)}")
    print(f"Members with gaps: {len({g['member_id'] for g in gaps})}\n")
    print(f"{'Service':<32}{'Eligible':>9}{'Done':>7}{'Rate':>8}")
    print("-" * 62)
    for rule in RULES:
        s = stats[rule["code"]]
        rate = f"{s['compliant'] / s['eligible'] * 100:.0f}%" if s["eligible"] else "n/a"
        print(f"{rule['name']:<32}{s['eligible']:>9}{s['compliant']:>7}{rate:>8}")

    print("\nTop 5 members by number of gaps:")
    counts = defaultdict(int)
    names = {}
    for g in gaps:
        counts[g["member_id"]] += 1
        names[g["member_id"]] = g["name"]
    for mid, n in sorted(counts.items(), key=lambda x: -x[1])[:5]:
        print(f"  {mid}  {names[mid]:<20} {n} gaps")


# ---------------------------------------------------------------------------
# 6. Sample data generator (so the project runs out of the box)
# ---------------------------------------------------------------------------
def generate_sample_data(members_path: str, claims_path: str, n: int = 200):
    random.seed(42)
    first = ["Asha", "Ravi", "Meera", "Kiran", "Sana", "Arjun", "Priya", "Vikram", "Neha", "Rahul"]
    last = ["Rao", "Sharma", "Khan", "Reddy", "Iyer", "Patel", "Singh", "Das", "Nair", "Gupta"]

    with open(members_path, "w", newline="") as mf, open(claims_path, "w", newline="") as cf:
        mw, cw = csv.writer(mf), csv.writer(cf)
        mw.writerow(["member_id", "name", "dob", "sex", "conditions"])
        cw.writerow(["member_id", "service_date", "service_code"])

        for i in range(1, n + 1):
            mid = f"M{i:04d}"
            age = random.randint(18, 80)
            dob = AS_OF - timedelta(days=age * 365 + random.randint(0, 364))
            sex = random.choice(["F", "M"])
            conditions = "diabetes" if random.random() < 0.15 else ""
            mw.writerow([mid, f"{random.choice(first)} {random.choice(last)}", dob, sex, conditions])

            for rule in RULES:
                if random.random() < 0.6:  # ~60% have had the service at some point
                    days_ago = random.randint(30, rule["interval_months"] * 30 * 2)
                    cw.writerow([mid, AS_OF - timedelta(days=days_ago), rule["code"]])


# ---------------------------------------------------------------------------
# 7. Main
# ---------------------------------------------------------------------------
def main():
    members_path, claims_path = "members.csv", "claims.csv"
    if not (Path(members_path).exists() and Path(claims_path).exists()):
        print("Input files not found - generating sample data...")
        generate_sample_data(members_path, claims_path)

    members = load_members(members_path)
    claims = load_claims(claims_path)
    gaps, stats = find_gaps(members, claims)

    write_gaps_csv(gaps, "care_gaps.csv")
    print_summary(members, gaps, stats)
    print("\nDetailed gap list saved to care_gaps.csv")


if __name__ == "__main__":
    main()
