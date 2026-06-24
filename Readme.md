# Candidate Ranking System for Redrob Hackathon

## Overview
This is a candidate discovery system designed to identify AI Engineers for the Redrob founding team. The system moves beyond simple keyword matching to incorporate behavioral signals, career integrity checks, and prestige heuristics.

### Quick Links
- **Google Colab Notebook**: [Run the Ranker in the Cloud](https://colab.research.google.com/drive/1hAZ3KAsmE1-pmAMmwl3tLYPnC-vufXXc?usp=sharing)
- **Primary Script**: [rank.py](rank.py)
- **Submission Output**: [submission.csv](data/final/submission.csv)

---

## Reproduction Command

To reproduce the top-100 ranking from scratch on a local machine:

```bash
python rank.py
```

**Constraints Compliance**:
- **Runtime**: ~30-90 seconds (Total scanning of 100k pool)
- **Compute**: CPU only, no GPU required
- **Memory**: ~2.5 GB peak usage
- **Pre-computation**: None (Script runs end-to-end)

---

## What Makes v4 Better?

Our system specifically solves for the "Read between the lines" and "Anti-Trap" requirements in the Hackathon Specification:

### 1. Advanced Honeypot & Trap Detection
Most rankers fail by picking "ghost" candidates or keyword-stuffers. Our system detects:
- **Ghost Workers**: Candidates claiming multiple concurrent full-time roles.
- **Impossible Timelines**: Checks for career inflation beyond graduation dates.
- **Junior "Experts"**: Penalizes experts with < 3 years of experience.
- **Salary Sense-Check**: Identifies synthetic outliers (e.g., 5 LPA for 9 YOE AI Engineer).

### 2. Product-First & Culture Score
Aligning with the "Founding Team" requirement:
- **Product Boost (1.2x)**: Boosts candidates from product-based companies (Apple, Zomato, etc.).
- **Service Penalty (0.5x)**: Penalizes "Pure Service" careers (TCS, Infosys, Wipro) unless product experience exists.
- **Shipper Multiplier**: Weighting for "Founding", "Stealth", and "Production" keywords in career history.

### 3. Prestige & Builder Signals
- **Education Tiering**: Boosting Tier-1 (IIT, NIT, IIIT, BITS) institutions.
- **GitHub Activity**: Incorporates the Redrob `github_activity_score` to prioritize engineers who actively build and ship code.

### 4. Logistics & Buy-out Optimization
- **Notice Period Buyout**: Heavy boost for `<= 30 day` notice (as per JD buyout policy).
- **Relocation Alignment**: Pairs Tier-1 city locations with `willing_to_relocate` flags.

---

## Ranking Formula

```python
Final Score = (Semantic Similarity × 0.45 + Engagement × 0.25) × Multipliers
```
*Where Multipliers = Prestige × Salary Check × Notice Boost × GitHub Signal × Product Boost.*

---

## File Structure
```
India_Runs_Hackathon
|
|-- data
     |-- raw  # candidates.jsonl , sample candidates, raw data
     |-- final # submission.csv
|-- notebook
     |-- main.ipynb # main notebook
     |-- validate_submission.py
|-- docs/
     |--    # Docs given for problem statements
              (Except we don't upload the *candidates.jsonl*)
|-- rank.py
|-- validate_submission.py
|-- requirements.txt
|-- Readme.md
```

---

## Submission Verification
To verify the output format:
```bash
python validate_submission.py
```

### Thanks for reading

---

#### Author: Shiven Sharma & Swasti Somwanshi