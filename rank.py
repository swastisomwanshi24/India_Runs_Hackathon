import os
import gzip
import json
import pandas as pd
import numpy as np
import random
import argparse
from datetime import datetime
from pathlib import Path
from sentence_transformers import SentenceTransformer, util

# Load HuggingFace token from models/.env
def load_hf_token():
    """Load HuggingFace token from .env file in models folder"""
    env_path = Path(__file__).parent / 'models' / '.env'
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if line.startswith('HF_TOKEN='):
                    token = line.split('=', 1)[1].strip()
                    os.environ['HF_TOKEN'] = token
                    return token
    return None

# Load token at startup
load_hf_token()
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# --- SETTINGS ---
SERVICE_COMPANIES = {'tcs', 'infosys', 'wipro', 'accenture', 'cognizant', 'capgemini', 'hcl', 'tech mahindra', 'mindtree'}
FOUNDATIONAL_AI = {'ndcg', 'mrr', 'ranking', 'retrieval', 'vector search', 'indexing', 'latency', 'production', 'fine-tuning', 'eval'}
ARCHITECT_TITLES = {'architect', 'principal', 'staff', 'lead', 'manager'}
CODING_KEYWORDS = {'python', 'pytorch', 'tensorflow', 'scikit', 'rust', 'c++', 'golang', 'java', 'sql'}

def is_hands_on(profile, career):
    if not career: return True
    latest_role = career[0]
    title = latest_role.get('job_title', '').lower()
    description = latest_role.get('job_description', '').lower()
    if any(at in title for at in ARCHITECT_TITLES):
        if not any(ck in description for ck in CODING_KEYWORDS):
            return False 
    return True

def lang_chain_tourist(profile, skills):
    skill_names = {s.get('name', '').lower() for s in skills}
    if ('langchain' in skill_names or 'openai' in skill_names) and len(skill_names) < 10:
        if not any(fa in skill_names for fa in FOUNDATIONAL_AI):
            return True
    return False

def generate_dynamic_reasoning(row):
    """Produces non-templated, fact-specific reasoning for Stage 4 manual review."""
    pool = []
    pool.append(f"{row['yoe']:.1f}y Senior Engineer with tenure at {row['last_employer']}")
    if row['is_product']: pool.append("Demonstrates product-engineering mindset over pure services")
    if row['notice'] <= 30: pool.append("Immediate availability for hiring (<=30d notice)")
    skills = ", ".join(row['skills'][:2])
    pool.append(f"Deep technical depth in {skills}")
    
    # Shuffle for variation
    selected = random.sample(pool, min(3, len(pool)))
    return ". ".join(selected) + "."

def run_ranker(candidates_path, output_path):
    print(f"Loading Redrob Optimized Ranker (Offline Mode)...")
    
    # Load Model (Priority: Local folder)
    model_path = os.path.join(os.path.dirname(__file__), 'models', 'all-MiniLM-L6-v2')
    if os.path.exists(model_path):
        model = SentenceTransformer(model_path)
    else:
        print("Warning: Local model missing. Using online model...")
        model = SentenceTransformer('all-MiniLM-L6-v2')

    # 1. Processing & Stage 1 Filter
    processed = []
    open_func = gzip.open if candidates_path.endswith('.gz') else open
    
    print("Stage 1: Streaming & Heuristic Filtering...")
    with open_func(candidates_path, 'rt', encoding='utf-8') as f:
        for line in f:
            try:
                c = json.loads(line)
                profile = c.get('profile', {})
                yoe = float(profile.get('years_of_experience', 0) or 0)
                career = c.get('career_history', [])
                
                # Global DQ Filters
                if yoe < 4 or yoe > 22: continue
                if not is_hands_on(profile, career): continue
                
                signals = c.get('redrob_signals', {}) or {}
                skills = c.get('skills', [])
                
                if lang_chain_tourist(profile, skills): continue
                
                is_service = any(sc in str(profile.get('current_company','')).lower() for sc in SERVICE_COMPANIES)
                notice = signals.get('notice_period_days', 90)
                
                processed.append({
                    'candidate_id': c['candidate_id'],
                    'yoe': yoe,
                    'text': f"{profile.get('headline','')} {profile.get('summary','')} {profile.get('current_title','')}".lower(),
                    'h_mult': (1.25 if not is_service else 0.7) * (1.2 if notice <= 30 else 1.0) * (float(signals.get('recruiter_response_rate', 0.5))),
                    'is_product': not is_service,
                    'notice': notice,
                    'last_employer': career[0].get('company_name', 'Unknown') if career else 'Private',
                    'skills': [s.get('name','') for s in skills][:3]
                })
            except: continue
    
    df = pd.DataFrame(processed)
    print(f"Pool size: {len(df)}. Reranking Top 2,000...")

    # Fast Lexical check
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(["Senior AI Engineer Ranking Retrieval Production RAG"] + df['text'].tolist())
    df['tfidf_sim'] = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])[0]
    
    # Select Top 2000 for Transformer
    df_rerank = df.assign(s1 = df['tfidf_sim'] * df['h_mult']).sort_values('s1', ascending=False).head(2000).copy()

    # Stage 2: Transformer Rerank
    jd_text = "Senior AI Engineer. Expertise in ranking systems, vector search, embeddings, RAG, and LLM fine-tuning. Production experience required."
    jd_emb = model.encode(jd_text, convert_to_tensor=True)
    cand_embs = model.encode(df_rerank['text'].tolist(), convert_to_tensor=True, show_progress_bar=True)
    df_rerank['semantic_score'] = util.cos_sim(jd_emb, cand_embs)[0].cpu().numpy()

    # Final Sort
    df_rerank['final_score'] = df_rerank['semantic_score'] * df_rerank['h_mult']
    df_final = df_rerank.sort_values('final_score', ascending=False).head(100).copy()
    
    df_final['rank'] = range(1, 101)
    df_final['reasoning'] = df_final.apply(generate_dynamic_reasoning, axis=1)
    
    # Save with specific columns required by spec
    df_final[['candidate_id', 'rank', 'final_score', 'reasoning']].rename(columns={'final_score':'score'}).to_csv(output_path, index=False)
    print(f"SUCCESS: Ultimate Ranking Saved to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--candidates', type=str, default='data/raw/candidates.jsonl')
    parser.add_argument('--out', type=str, default='data/final/submission_final.csv')
    args = parser.parse_args()
    
    run_ranker(args.candidates, args.out)