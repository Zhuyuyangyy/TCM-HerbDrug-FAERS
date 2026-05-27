"""Generate synthetic FAERS-like data for testing."""
import json
import random
import os

random.seed(42)

DRUGS = ["warfarin", "clopidogrel", "digoxin", "cyclosporine",
         "simvastatin", "metformin", "omeprazole", "metoprolol",
         "aspirin", "lisinopril", "atorvastatin", "amlodipine"]

HERBS = ["丹参", "甘草", "当归", "黄芩", "大黄", "黄连", "红曲", "圣约翰草"]

EVENTS = ["bleeding", "hepatotoxicity", "hypokalemia", "rash",
          "dizziness", "nausea", "renal_impairment", "cardiac_arrhythmia",
          "thrombocytopenia", "elevated_INR", "myopathy", "GI_hemorrhage"]

# Known high-risk pairs (more reports)
HIGH_RISK = [
    ("warfarin", "丹参", "bleeding", 0.3),
    ("warfarin", "丹参", "elevated_INR", 0.25),
    ("digoxin", "甘草", "cardiac_arrhythmia", 0.2),
    ("cyclosporine", "圣约翰草", "hepatotoxicity", 0.15),
    ("clopidogrel", "丹参", "bleeding", 0.12),
    ("simvastatin", "红曲", "myopathy", 0.1),
]

def generate(n_records=5000):
    records = []
    for i in range(n_records):
        drug = random.choice(DRUGS)
        event = random.choice(EVENTS)
        # Boost co-occurrence for known pairs
        for d, h, e, prob in HIGH_RISK:
            if random.random() < prob and drug == d:
                records.append({"primaryid": i, "caseid": i,
                                "drugname": d, "pt": e, "role_cod": "PS"})
                break
        else:
            records.append({"primaryid": i, "caseid": i,
                            "drugname": drug, "pt": event, "role_cod": "SS"})
    return records

if __name__ == "__main__":
    records = generate(5000)
    out_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "synthetic_faers.csv")
    import csv
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["primaryid", "caseid", "drugname", "pt", "role_cod"])
        writer.writeheader()
        writer.writerows(records)
    print(f"Generated {len(records)} records -> {out_path}")
