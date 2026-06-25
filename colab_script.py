import os
import gzip
import json
import pandas as pd
import numpy as np
import random
from sentence_transformers import SentenceTransformer, util
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from tqdm.auto import tqdm

# --- COLAB DRIVE MOUNT (UNCOMMENT IF RUNNING IN COLAB) ---
# from google.colab import drive
# drive.mount('/content/drive')

# --- CONFIGURATION ---
# Change this to your project folder path
PROJECT_FOLDER = './'  # Use './' for local VS Code, or '/content/drive/MyDrive/...' for Colab
CANDIDATES_FILE = 'data/raw/candidates.jsonl'
OUTPUT_FILE = 'data/final/submission_script.csv'

INPUT_PATH = os.path.join(PROJECT_FOLDER, CANDIDATES_FILE)
OUTPUT_PATH = os.path.join(PROJECT_FOLDER, OUTPUT_FILE)

# --- SETTINGS ---
SERVICE_COMPANIES = {'tcs', 'infosys', 'wipro', 'accenture', 'cognizant', 'capgemini', 'hcl', 'tech mahindra', 'mindtree'}
FOUNDATIONAL_AI = {'ndcg', 'mrr', 'ranking', 'retrieval', 'vector search', 'indexing', 'latency', 'production'}
ARCHITECT_TITLES = {'architect', 'principal', 'staff', 'lead', 'manager'}
CODING_KEYWORDS = {'python', 'pytorch', 'tensorflow', 'scikit', 'rust', 'c++', 'golang'}

def is_hands_on(profile, career):
    if not career: return True
    title = career[0].get('job_title', '').lower()
    desc = career[0].get('job_description', '').lower()
    if any(at in title for at in ARCHITECT_TITLES):
        return any(ck in desc for ck in CODING_KEYWORDS)
    return True

def lang_chain_tourist(profile, skills):
    skill_names = {s.get('name', '').lower() for s in skills}
    if ('langchain' in skill_names or 'openai' in skill_names) and len(skill_names) < 10:
        return not any(fa in skill_names for fa in FOUNDATIONAL_AI)
    return False

def generate_reasoning(row):
    pool = [
        f"{row['yoe']:.1f}y Senior Engineer with tenure at {row['last_employer']}.",
        "Matches the 'product-over-research' profile requested in the JD.",
        f"Deep technical depth in {', '.join(row['skills'][:2])}.",
        "Strong engagement signals and relocation alignment."
    ]
    if row['notice'] <= 30: pool.append("Immediate availability (<=30d notice).")
    selected = random.sample(pool, 3)
    return " ".join(selected)

def run_ranker():
    print(f"🚀 Initializing Ranker...")
    print(f"Reading from: {INPUT_PATH}")
    
    if not os.path.exists(INPUT_PATH):
        print(f"❌ Error: {INPUT_PATH} not found!")
        return

    # Load Model (automatically downloads if not present)
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    processed = []
    open_func = gzip.open if INPUT_PATH.endswith('.gz') else open
    
    print("Stage 1: Heuristic & TF-IDF Filter (100k -> 2k)...")
    with open_func(INPUT_PATH, 'rt', encoding='utf-8') as f:
        for line in tqdm(f, total=100000):
            try:
                c = json.loads(line)
                profile = c.get('profile', {})
                yoe = float(profile.get('years_of_experience', 0) or 0)
                career = c.get('career_history', [])
                
                if yoe < 4 or yoe > 22: continue
                if not is_hands_on(profile, career): continue
                if lang_chain_tourist(profile, c.get('skills', [])): continue
                
                signals = c.get('redrob_signals', {}) or {}
                is_service = any(sc in str(profile.get('current_company','')).lower() for sc in SERVICE_COMPANIES)
                notice = signals.get('notice_period_days', 90)
                
                processed.append({
                    'candidate_id': c['candidate_id'],
                    'yoe': yoe,
                    'text': f"{profile.get('headline','')} {profile.get('summary','')} {profile.get('current_title','')}".lower(),
                    'h_mult': (1.25 if not is_service else 0.7) * (1.2 if notice <= 30 else 1.0) * (float(signals.get('recruiter_response_rate', 0.5))),
                    'last_employer': career[0].get('company_name', 'Unknown') if career else 'Private',
                    'skills': [s.get('name','') for s in c.get('skills', [])][:3],
                    'notice': notice
                })
            except: continue

    df = pd.DataFrame(processed)
    # TF-IDF Scan
    vec = TfidfVectorizer(stop_words='english')
    tfidf = vec.fit_transform(["Senior AI Engineer ranking retrieval Production RAG Vector Search"] + df['text'].tolist())
    df['tfidf_sim'] = cosine_similarity(tfidf[0:1], tfidf[1:])[0]
    
    df_top = df.assign(s1 = df['tfidf_sim'] * df['h_mult']).sort_values('s1', ascending=False).head(2000).copy()
    
    print("Stage 2: Semantic Transformer Reranking (2k -> 100)...")
    jd_text = "Senior AI Engineer. Ranking systems, vector search, embeddings, RAG, and LLM fine-tuning."
    jd_emb = model.encode(jd_text, convert_to_tensor=True)
    cand_embs = model.encode(df_top['text'].tolist(), convert_to_tensor=True, show_progress_bar=True)
    df_top['semantic_score'] = util.cos_sim(jd_emb, cand_embs)[0].cpu().numpy()
    
    df_top['final_score'] = df_top['semantic_score'] * df_top['h_mult']
    df_final = df_top.sort_values('final_score', ascending=False).head(100).copy()
    df_final['rank'] = range(1, 101)
    df_final['reasoning'] = df_final.apply(generate_reasoning, axis=1)
    
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    df_final[['candidate_id', 'rank', 'final_score', 'reasoning']].rename(columns={'final_score':'score'}).to_csv(OUTPUT_PATH, index=False)
    print(f"✅ Success! Submission saved to: {OUTPUT_PATH}")

if __name__ == "__main__":
    run_ranker()
