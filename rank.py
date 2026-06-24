import os
import gzip
import json
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

import argparse

# 1. SETTINGS & PATHS
parser = argparse.ArgumentParser(description="Rank candidates for Senior AI Engineer role.")
parser.add_argument("--candidates", default=os.path.join('data', 'raw', 'candidates.jsonl'), help="Path to candidates.jsonl")
parser.add_argument("--out", default=os.path.join('data', 'final', 'submission.csv'), help="Path to output CSV")
args = parser.parse_args()

CANDIDATES_PATH = args.candidates
OUTPUT_CSV_PATH = args.out

# Fallback for .gz
if not os.path.exists(CANDIDATES_PATH) and os.path.exists(CANDIDATES_PATH + '.gz'):
    CANDIDATES_PATH += '.gz'

CURRENT_DATE = datetime(2026, 6, 25)

SERVICE_COMPANIES = {'tcs', 'infosys', 'wipro', 'accenture', 'cognizant', 'capgemini', 'hcl', 'tech mahindra', 'mindtree'}
PRESTIGE_TIERS = {'tier_1': 1.15, 'tier_2': 1.05, 'tier_3': 1.0}
HIGH_SIGNAL_WORDS = {'recommendation', 'matching', 'recsys', 'information retrieval', 'indexing', 'latency', 'production'}

# 2. ADVANCED HEURISTICS & TRAPS
def detect_ghost_worker(career):
    """Checks for logically impossible overlapping full-time jobs."""
    if not career: return False
    current_jobs = [j for j in career if j.get('is_current')]
    if len(current_jobs) > 1: return True
    return False

def calculate_prestige_boost(edu):
    """Boosts based on college tiering."""
    if not edu: return 1.0
    tiers = [e.get('tier', 'unknown') for e in edu]
    boosts = [PRESTIGE_TIERS.get(t, 0.9) for t in tiers]
    return max(boosts)

def salary_confidence_check(yoe, salary_range):
    """Flags suspicious salary expectations for seniority level."""
    avg_sal = (salary_range.get('min', 0) + salary_range.get('max', 100)) / 2
    if yoe > 5 and avg_sal < 6: return 0.5 # Suspiciously low for 5+ YOE AI Engineer
    if yoe < 3 and avg_sal > 80: return 0.7 # Likely hallucination or junior outlier
    return 1.0

# 3. PROCESSING (STREAMING)
print("Initiating Final Tier Ranker...")
processed = []
open_func = gzip.open if CANDIDATES_PATH.endswith('.gz') else open

with open_func(CANDIDATES_PATH, 'rt', encoding='utf-8') as f:
    for idx, line in enumerate(f):
        try:
            c = json.loads(line)
            profile = c.get('profile', {})
            yoe = float(profile.get('years_of_experience', 0) or 0)
            
            # Pruning
            if yoe < 4 or yoe > 18: continue
            if detect_ghost_worker(c.get('career_history', [])): continue
            
            signals = c.get('redrob_signals', {}) or {}
            
            # Logic multipliers
            prestige = calculate_prestige_boost(c.get('education', []))
            sal_check = salary_confidence_check(yoe, signals.get('expected_salary_range_inr_lpa', {}))
            
            # Notice Buyout logic
            notice = signals.get('notice_period_days', 90)
            notice_mult = 1.2 if notice <= 30 else (0.8 if notice > 60 else 1.0)
            
            # Builder/Shipper Signal (GitHub)
            github = signals.get('github_activity_score', 0)
            github_mult = 1.0 + (github / 200.0) if github > 0 else 0.9

            processed.append({
                'candidate_id': c['candidate_id'],
                'yoe': yoe,
                'text': f"{profile.get('headline','')} {profile.get('summary','')} {profile.get('current_title','')}".lower(),
                'mults': prestige * sal_check * notice_mult * github_mult,
                'engagement': float(signals.get('recruiter_response_rate', 0.5)),
                'top_skills': [s.get('name','') for s in c.get('skills', [])][:5],
                'is_product': not any(sc in str(profile.get('current_company','')).lower() for sc in SERVICE_COMPANIES)
            })
            if idx % 25000 == 0: print(f"Scanned {idx} profiles...")
        except: continue

df = pd.DataFrame(processed)
print(f"Final Rerank Pool: {len(df)}")

# 4. TWO-STAGE SEMANTIC MATCHING
vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1,2))
jd_full = "Senior AI Engineer embedding vector search retrieval ranking infrastructure production LLM fine-tuning NDCG evaluation"
all_text = [jd_full] + df['text'].tolist()
tfidf_matrix = vectorizer.fit_transform(all_text)

df['sim_score'] = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])[0]

# 5. FINAL SCORE & RERANK
df['final_score'] = (df['sim_score'] * 0.45 + df['engagement'] * 0.25) * df['mults']
df.loc[df['is_product'], 'final_score'] *= 1.2

# Re-score for high signal words
def signal_rerank(text):
    return sum(1 for word in HIGH_SIGNAL_WORDS if word in text) * 0.05

df['final_score'] += df['text'].apply(signal_rerank)

# 6. REASONING ENGINE v4
def final_reasoning(row):
    parts = [f"{row['yoe']:.1f}y Senior Engineer"]
    if row['mults'] > 1.2: parts.append("High-prestige build profile")
    if row['is_product']: parts.append("Product-company veteran")
    
    skills = ", ".join(row['top_skills'][:2])
    parts.append(f"Expertise in {skills}")
    
    return ". ".join(parts) + "."

df_top = df.sort_values('final_score', ascending=False).head(100).copy()
df_top['rank'] = range(1, 101)
df_top['reasoning'] = df_top.apply(final_reasoning, axis=1)

df_top[['candidate_id', 'rank', 'final_score', 'reasoning']].rename(columns={'final_score':'score'}).to_csv(OUTPUT_CSV_PATH, index=False)
print(f"SUCCESS: Ultimate Ranking Saved to {OUTPUT_CSV_PATH}")
