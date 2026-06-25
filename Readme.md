# Candidate Ranking System for Redrob Hackathon

## Overview
This system is a high-performance candidate discovery engine designed for the **Redrob Hackathon**. It identifies top-tier AI Engineers by moving beyond keyword matching, incorporating behavioral signals, career integrity checks, and prestige heuristics

### Quick Links
- **Google Colab Notebook**: [Run the Ranker in the Cloud](https://colab.research.google.com/drive/1hAZ3KAsmE1-pmAMmwl3tLYPnC-vufXXc?usp=sharing)
- **Primary Script**: [rank.py](rank.py)
- **Submission Output**: [submission.csv](data/final/submission.csv)

---

## Reproduction Command

To reproduce the top-100 ranking from scratch on a local machine:

```bash
pip install -r requirements.txt

python rank.py --candidates data/raw/candidates.jsonl --out data/final/submission.csv

python validate_submission.py data/final/submission.csv
```

**Constraints Compliance**:
- **Runtime**: ~30-90 seconds (Total scanning of 100k pool)
- **Compute**: CPU only, no GPU required
- **Memory**: ~2.5 GB peak usage
- **Pre-computation**: None (Script runs end-to-end)

---

###  Ranking Methodology
Our system implements a multi-stage pipeline designed to satisfy the "Read between the lines" requirement:

#### Multi-Stage Pipeline
1. **Heuristic Filtering:** Hard DQ filters for candidates with < 4 years of experience or impossible career timelines (honeypots).
2. **Lexical Scoring (TF-IDF):** Initial fast scan of the 100k pool to identify the top 2,000 matches based on JD-specific terms (RAG, Retrieval, Ranking).
3. **Semantic Reranking:** Uses all-MiniLM-L6-v2 to compute cosine similarity between the JD and candidate summaries.
4. **Behavioral Multipliers:**
    - Product Boost (1.25x): Prioritizes candidates from product-based cultures.
    - Service Penalty (0.7x): Down-weights pure service company backgrounds (TCS, Infosys, etc.).
    - Engagement Multiplier: Factors in recruiter_response_rate to prioritize active talent.
    - Notice Boost: Heavy weighting for <= 30 day availability.

#### Anti-Trap Logic
    - **Honeypot Detection:** Detects synthetic candidates by checking for career inflation and title-skill mismatches.
    - **Title Check:** Identifies "Title-chasers" and "LangChain tourists" who lack foundational ML depth.

---

## Ranking Formula

```python
Final Score = (Semantic Similarity × 0.45 + Engagement × 0.25) × Multipliers
```
*Where Multipliers = Prestige × Salary Check × Notice Boost × GitHub Signal × Product Boost.*

---

## File Structure
```
India_Runs_Hackathon/
├── data/
│   ├── raw/           # candidates.jsonl (Gzipped or raw) & extract.txt
│   └── final/         # submission.csv (Final output)
├── models/
│   ├── all-MiniLM-L6-v2/ # Local transformer model
│   └── .env           # HF_TOKEN (Grit-ignored for security)
├── rank.py            # Primary ranking engine
├── validate_submission.py # Spec wrapper for the notebook validator
├── requirements.txt   # Dependencies
└── Readme.md

```

---

## Submission Verification
To verify the output format:
```bash
python rank.py

python validate_submission.py
```

### Thanks for reading

---

#### Author: Shiven Sharma & Swasti Somwanshi
