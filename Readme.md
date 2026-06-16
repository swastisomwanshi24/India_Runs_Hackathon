# Redrob Hackathon: Intelligent Candidate Discovery & Ranking Challenge

## Project Overview
This project is our submission for the Redrob Hackathon. The objective is to build an intelligent candidate ranking system that evaluates a pool of 100,000 synthetic candidates against a highly specific "Senior AI Engineer" job description.

Rather than simple keyword matching, the challenge emphasizes interpreting real-world hiring constraints: identifying "shippers" over pure researchers, recognizing relevant experience even without modern buzzwords, avoiding "honeypot" profiles (e.g., keyword-stuffed irrelevant titles), and correctly applying behavioral signals (e.g., recent logins, recruiter response rates, notice periods).

## What We Need to Do
1. **Analyze the Job Description & Candidates:** 
   - Parse the `job_description.docx` to extract hard filters (must have: production vector DBs, embedding retrieval, python, eval frameworks) and disqualifiers (pure research, no code in 18 months, only consulting).
   - Evaluate candidates using the data schema and the 23 behavioral signals defined in `redrob_signals_doc.docx`.
2. **Build a Time-and-Resource Efficient Ranker:**
   - **Constraints:** The ranking step must run in under 5 minutes on a CPU-only machine with ≤16GB RAM and NO external network/API calls. Intermediate disk usage must be ≤5GB.
   - Any heavy computation (e.g., generating dense embeddings) must be done in a pre-compute phase. The final ranking step must be rapid and offline.
3. **Handle Traps and Honeypots:**
   - The dataset contains ~80 honeypots (impossible combinations of experience/age). Submissions with >10% honeypots in the top 100 will be disqualified.
   - We must weigh behavioral signals heavily (e.g., if a candidate has a 5% recruiter response rate or hasn't logged in recently, their score must be down-weighted).
4. **Produce the Submission Files:**
   - Generate a single `team_xxx.csv` file containing EXACTLY the top 100 candidates ranked 1-100, including their score and a 1-2 sentence justification/reasoning for each choice.
   - Validate the CSV format using the provided `validate_submission.py`.
   - Prepare the `submission_metadata.yaml` with our details, GitHub repository link, and a sandbox demo link (e.g., Docker, HuggingFace Spaces, or Colab) that can rank a small subset of candidates correctly.

## Our Implementation Plan
1. **Data Preprocessing & Pre-computation:**
   - Build a script to parse `candidates.jsonl.gz`.
   - Extract key features: total relevant experience, product-company presence, keyword flags, and all behavioral signals.
   - Since network API calls are forbidden during evaluation, we will pre-compute any necessary vectors or indices offline or use a fast local heuristics/TF-IDF system combined with strong rule-based filters.
2. **Scoring Logic:**
   - **Base Score:** Match JD technical requirements using BM25/TF-IDF or a lightweight local `sentence-transformers` model.
   - **Multipliers:** Apply boost factors based on `profile_completeness_score`, `last_active_date`, and `recruiter_response_rate`.
   - **Penalties:** Implement hard penalties for "pure research" titles, honeypot properties (e.g. excessive years of experience for recent technologies), and high notice period > 30 days.
3. **Reasoning Generation:**
   - Automatically compile the reasoning string by templating the specific facts extracted from the candidate profile (e.g., "7 years applied ML experience with Pinecone; 90% recruiter response rate").
4. **Final Packaging:**
   - Wrap the solution into a reproducible Python script.
   - Build an easy-to-use Dockerfile or HuggingFace Space to serve as our verifiable "sandbox".
   - Validate the CSV and finalize metadata before the deadline.