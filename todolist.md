# Ranker Improvement Todo List

This document outlines the roadmap to upgrade the candidate ranking system to meet the "Senior AI Engineer" JD requirements and avoid hackathon disqualification traps.

## 🚀 Phase 1: Robustness & Trap Detection (Anti-Disqualification)
These tasks ensure the system isn't disqualified by the "Honeypot" or "Templated Reasoning" rules.

- [ ] **Implement Honeypot Detection**
    - [ ] Add logic to check for impossible career timelines (e.g., total YOE > age or years since graduation).
    - [ ] Flag profiles with "expert" status in too many unrelated technologies (keyword stuffers).
    - [ ] Check if years of experience at a company exceed the company's age (if data allows).
- [ ] **Dynamic Reasoning Engine (Anti-Template)**
    - [ ] Create a rule-based reasoning generator that pulls *specific* candidate facts (e.g., "Matches JD with [Skill A] and [Skill B], plus high engagement").
    - [ ] Ensure no two reasoning strings in the top 100 are identical.
    - [ ] Include "Honest Concerns" (e.g., "Strong fit but has a 90-day notice period").

## 🧠 Phase 2: "Smarter" Ranking Logic
Aligning the code with the "Read between the lines" instructions in the JD.

- [ ] **Product vs. Service Company Weighting**
    - [ ] Create a list of disqualifier keywords (TCS, Infosys, Wipro, etc.).
    - [ ] Create a "Product Signal" list (SaaS, Startup, Product-based, B2B/B2C).
    - [ ] Apply a multiplier (e.g., 1.2x for Product, 0.5x for Service).
- [ ] **Soft Filtering (YOE)**
    - [ ] Change the hard `5 <= yoe <= 9` filter to a "Success Bell Curve".
    - [ ] Give max points to 6-8 years, slight penalties for 5 and 9, and heavier penalties further out.
- [ ] **Behavioral Signal Integration**
    - [ ] Increase weight of `recruiter_response_rate` and `last_active_date`.
    - [ ] Down-weight candidates who haven't logged in for 3+ months (even if they are "perfect on paper").

## 🔍 Phase 3: Technical Enhancements
Upgrading the core matching engine while staying within compute limits.

- [ ] **Upgrade Semantic Matching**
    - [ ] Replace TF-IDF with a local, CPU-friendly embedding model (e.g., `sentence-transformers/all-MiniLM-L6-v2`).
    - [ ] Strategy: Pre-compute embeddings for candidates (pre-computation is allowed) and only compute the JD embedding at runtime.
- [ ] **Title/Headline Sensitivity**
    - [ ] Give higher weight to the `current_title` and `headline` compared to the general `summary`.
    - [ ] Penalize "Management" or "Marketing" titles even if they contain AI keywords.

## ⚡ Phase 4: Compliance & Performance
Finalizing for the submission constraints.

- [ ] **Performance Audit (CPU Budget)**
    - [ ] Ensure the ranking loop for 100k candidates runs in under 4 minutes on a single core.
    - [ ] Use `numpy` or `pandas` vectorized operations for final score calculation.
- [ ] **Submission Validation**
    - [ ] Run `validate_submission.py` to check for rank ordering and formatting.
    - [ ] Ensure `candidate_id` format is exact.

## 📝 Final Review Checklist
- [ ] Honeypot rate in Top 100 is < 10%.
- [ ] All top 100 scores are non-increasing.
- [ ] Reasoning is unique and specific to each candidate.
- [ ] Zero external API calls (OpenAI, etc.).
