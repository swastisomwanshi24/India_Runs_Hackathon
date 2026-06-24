# Redrob Hackathon - Candidate Ranking System Submission

## Quick Start - Reproduce Submission

### Single Command Reproduction

```bash
python rank.py --candidates ./data/raw/candidates.jsonl --out ./data/final/submission.csv
```

This command will:
1. Load 100,000 candidates from `candidates.jsonl`
2. Apply hard filters (experience, location, role type)
3. Compute text matching, tech stack, and behavioral scores
4. Rank top 100 candidates
5. Generate `submission.csv` in the required format

**Expected Runtime**: ~30-60 seconds on a standard laptop (CPU only)


---

## Validation

After generating the submission, validate it:

```bash
python validate_submission.py data/final/submission.csv
```

Expected output:
```
Submission is valid.
```

---

## What the System Does

### 1. Hard Filters (Pass/Fail)
-  **Experience**: 5-9 years
-  **Location**: Pune or Noida (or willing to relocate)
-  **Role Type**: Excludes non-tech roles (marketing, sales, HR) with >15 skills

**Result**: ~9,946 candidates pass filters from 100,000 total

### 2. Scoring System (Weighted Formula)

```
Final Score = (Text Match × 0.4) + (Tech Stack × 0.3) + (Behavioral × 0.3)
```

#### Text Match Score (40% weight)
- Uses TF-IDF vectorization + cosine similarity
- Compares candidate headline & summary against job description
- Looks for: "embeddings", "retrieval", "ranking", "LLMs", "fine-tuning", etc.

#### Tech Stack Score (30% weight)
- Checks for 6 must-have skills:
  - Python
  - Spark
  - Airflow
  - LLM
  - Embeddings
  - Ranking
- Score = (matched skills) / 6

#### Behavioral Score (30% weight)
Based on `redrob_signals`:
- **Recruiter response rate** < 30% → penalty -0.3
- **Profile completeness** < 50% → penalty -0.2
- **Notice period** > 60 days → penalty -0.1

### 3. Ranking & Tie-Breaking
- Sort by `score` (descending)
- Ties broken by `candidate_id` (ascending)
- Select top 100

---

## File Structure

```
India_Runs_Hackathon/
├── rank.py                     # Main ranking script (reproduction command)
├── validate_submission.py      # Wrapper for validator
├── notebook/
│   ├── main.ipynb             # Jupyter notebook version (development)
│   └── validate_submission.py # Actual validator logic
├── data/
│   ├── raw/
│   │   ├── candidates.jsonl   # 100K candidates (input)
│   │   └── extract.txt        # Project requirements
│   └── final/
│       └── submission.csv     # Top 100 ranked candidates (output)
└── README_REPRODUCTION.md     # This file
```

---

## Requirements

### Python Dependencies

```bash
pip install pandas scikit-learn
```

Or use requirements.txt:

```txt
pandas>=1.5.0
scikit-learn>=1.0.0
```

### Python Version
- Python 3.8 or higher

---

## Testing the Reproduction

### Test 1: Run the ranking command
```bash
python rank.py --candidates ./data/raw/candidates.jsonl --out ./data/final/submission.csv
```

**Expected Output**:
```
Processing candidates from: ./data/raw/candidates.jsonl
Output will be saved to: ./data/final/submission.csv
Step 1: Applying hard filters...
   9946 candidates passed hard filters
Step 2: Computing text match scores...
Step 3: Computing tech stack scores...
Step 4: Computing final scores...
Step 5: Sorting candidates...
Step 6: Selecting top 100 candidates...
Step 7: Generating reasoning...
Step 8: Saving submission CSV...

SUCCESS! Submission saved to: ./data/final/submission.csv
   Total candidates ranked: 100
   Top score: 0.5238
   Bottom score: 0.4407
```

### Test 2: Validate the output
```bash
python validate_submission.py data/final/submission.csv
```

**Expected Output**:
```
Submission is valid.
```

### Test 3: Check output format
```bash
head -n 5 data/final/submission.csv
```

**Expected Format**:
```csv
candidate_id,rank,score,reasoning
CAND_0063138,1,0.5238233655272808,Strong match with 33% tech stack alignment and high behavioral engagement.
CAND_0009525,2,0.5168092789016747,Strong match with 33% tech stack alignment and high behavioral engagement.
CAND_0013440,3,0.5133959905186669,Strong match with 33% tech stack alignment and high behavioral engagement.
...
```

---

## Submission Format Compliance

Our output meets all requirements from `submission_spec.md`:

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| Exactly 100 rows | `.head(100)` |
| Ranks 1-100 (each once) | `range(1, 101)` |
| Score non-increasing |  `sort_values(by='score', ascending=False)` |
| Tie-breaker by candidate_id | `sort_values(by=['score', 'candidate_id'], ascending=[False, True])` |
| Valid candidate_id format | Uses IDs from input |
| UTF-8 encoding |  Default pandas CSV writer |
| Required columns | `['candidate_id', 'rank', 'score', 'reasoning']` |

---

## Performance Characteristics

| Metric | Value |
|--------|-------|
| **Runtime** | ~30-60 seconds |
| **Memory Peak** | ~2-3 GB |
| **CPU Only** | Yes (no GPU) |
| **Network Calls** |  None |
| **Disk I/O** | < 500 MB |

**Compute Constraint Compliance** (from submission_spec.md):
- Runtime ≤ 5 minutes
- Memory ≤ 16 GB
- CPU only (no GPU)
- No network calls

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'sklearn'"
**Solution**: Install dependencies
```bash
pip install scikit-learn pandas
```

### Issue: "FileNotFoundError: candidates.jsonl"
**Solution**: Ensure you're running from the project root
```bash
cd India_Runs_Hackathon
python rank.py --candidates ./data/raw/candidates.jsonl --out ./data/final/submission.csv
```

### Issue: "candidates.jsonl.gz not found"
**Solution**: The script auto-detects both `.jsonl` and `.jsonl.gz`. Ensure one exists in `data/raw/`

### Issue: Validation fails with "score must be non-increasing"
**Solution**: This should not happen with the current implementation (it sorts properly). If it does, check for manual edits to submission.csv.

---

## Notes for Reviewers

### Design Decisions

1. **Streaming vs Batch Loading**: We stream candidates line-by-line to reduce memory footprint, even though the full dataset fits in memory.

2. **Tie-breaking by candidate_id**: Required by submission spec to ensure deterministic rankings when scores are equal.

3. **Simple reasoning template**: Currently uses a basic template. Can be enhanced with candidate-specific details (see VERIFICATION_SUMMARY.md for suggestions).

4. **Behavioral signal selection**: Uses 3 of 23 available signals (response rate, completeness, notice period) as these are most directly related to candidate availability.

5. **No honeypot detection**: Current implementation doesn't filter honeypot candidates. This is a known enhancement area.

### Reproducibility Guarantee

The system is **fully deterministic**:
- No random seeds or shuffling
- Same input → same output (always)
- Tie-breaking ensures stable ranking

---

## Contact

For questions about this submission, refer to `submission_metadata.yaml`

---

## Related Files

- `VERIFICATION_SUMMARY.md` - Detailed analysis vs requirements
- `data/raw/extract.txt` - Full project requirements
- `docs/submission_spec.docx` - Official submission specification
- `notebook/main.ipynb` - Development notebook (same logic)
