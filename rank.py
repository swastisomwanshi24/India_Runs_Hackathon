"""
Candidate Ranking System for Redrob Hackathon
Reproduces submission.csv from candidates.jsonl
"""
import os
import gzip
import json
import argparse
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# JOB DESCRIPTION
JOB_DESCRIPTION_TEXT = """
Senior AI Engineer Founding Team. Deep technical depth in modern ML systems: 
embeddings, retrieval, ranking, LLMs, fine-tuning. Backend data hybrid: Python, SQL, Spark, Airflow, infrastructure.
"""
TARGET_CITIES = ['noida', 'pune']


def passes_hard_filters(candidate):
    """Apply hard filters based on job requirements"""
    profile = candidate.get('profile', {}) or {}
    
    # Years of experience: 5-9 years
    try:
        yoe = float(profile.get('years_of_experience', 0) or 0)
    except Exception:
        yoe = 0
    if not (5 <= yoe <= 9):
        return False

    # Location: Pune/Noida or willing to relocate
    loc = str(profile.get('location', '')).strip().lower()
    signals = candidate.get('redrob_signals', {}) or {}
    willing_relocate = (candidate.get('willing_to_relocate', False) or 
                        signals.get('willing_to_relocate', False))

    if loc not in TARGET_CITIES and not willing_relocate:
        return False

    # Filter out non-tech roles with keyword stuffing
    title = str(profile.get('current_title', '')).lower()
    non_tech_keywords = ['marketing', 'sales', 'hr', 'recruiter', 'content writer', 'social media']
    skills = candidate.get('skills', []) or []
    if any(kw in title for kw in non_tech_keywords) and len(skills) > 15:
        return False
    
    return True


def calculate_behavioral_score(candidate):
    """Calculate behavioral engagement score from redrob_signals"""
    signals = candidate.get('redrob_signals', {}) or {}
    if not signals:
        return 0.5
    
    score = 1.0
    
    # Penalize low response rate
    if signals.get('recruiter_response_rate', 1.0) < 0.30:
        score -= 0.3
    
    # Penalize incomplete profiles
    if signals.get('profile_completeness_score', 100.0) < 50.0:
        score -= 0.2
    
    # Penalize long notice periods
    if signals.get('notice_period_days', 0) > 60:
        score -= 0.1
    
    return max(0.0, min(1.0, score))


def tech_stack_booster(row):
    """Calculate tech stack alignment score"""
    skills_data = row.get('skills', []) or []
    skills = [s.get('name', '').lower() for s in skills_data]
    
    # Must-have skills from job description
    must_haves = ['airflow', 'spark', 'python', 'llm', 'embeddings', 'ranking']
    matches = sum(1 for skill in must_haves if skill in skills)
    
    return matches / len(must_haves) if len(must_haves) > 0 else 0


def extract_text(row):
    """Extract text for TF-IDF matching"""
    profile = row.get('profile', {})
    return f"{profile.get('headline', '')} {profile.get('summary', '')}"


def main(candidates_path, output_path):
    """Main ranking pipeline"""
    print(f"Processing candidates from: {candidates_path}")
    print(f"Output will be saved to: {output_path}")
    
    # Determine if file is gzipped
    open_func = gzip.open if candidates_path.endswith('.gz') else open
    
    # Stream and filter candidates
    print("Step 1: Applying hard filters...")
    surviving_candidates = []
    
    with open_func(candidates_path, 'rt', encoding='utf-8', errors='replace') as fh:
        for raw in fh:
            line = raw.strip()
            if not line:
                continue
            try:
                candidate = json.loads(line)
                if passes_hard_filters(candidate):
                    candidate['behavioral_score'] = calculate_behavioral_score(candidate)
                    surviving_candidates.append(candidate)
            except Exception:
                continue
    
    print(f"   {len(surviving_candidates)} candidates passed hard filters")
    
    # Create dataframe
    df_large = pd.DataFrame(surviving_candidates)
    
    if df_large.empty:
        print("ERROR: No candidates passed filters!")
        # Create empty submission
        final_submission = pd.DataFrame(columns=['candidate_id', 'rank', 'score', 'reasoning'])
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        final_submission.to_csv(output_path, index=False)
        return
    
    # Text matching with TF-IDF
    print("Step 2: Computing text match scores...")
    df_large['combined_text'] = df_large.apply(extract_text, axis=1)
    vec = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vec.fit_transform([JOB_DESCRIPTION_TEXT] + df_large['combined_text'].tolist())
    df_large['text_match_score'] = [
        cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[i+1:i+2])[0][0] 
        for i in range(len(df_large))
    ]
    
    # Tech stack scoring
    print("Step 3: Computing tech stack scores...")
    df_large['tech_boost'] = df_large.apply(tech_stack_booster, axis=1)
    
    # Ensure behavioral_score column exists
    if 'behavioral_score' not in df_large.columns:
        df_large['behavioral_score'] = 0.5
    
    # Final weighted score
    print("Step 4: Computing final scores...")
    df_large['score'] = (
        df_large.get('text_match_score', 0.0) * 0.4 +
        df_large.get('tech_boost', 0.0) * 0.3 +
        df_large['behavioral_score'] * 0.3
    )
    
    # Sort with tie-breaker
    print("Step 5: Sorting candidates...")
    if 'candidate_id' in df_large.columns:
        df_sorted = df_large.sort_values(
            by=['score', 'candidate_id'], 
            ascending=[False, True]
        ).reset_index(drop=True)
    else:
        df_sorted = df_large.sort_values(
            by='score', 
            ascending=False
        ).reset_index(drop=True)
    
    # Get top 100
    print("Step 6: Selecting top 100 candidates...")
    df_top100 = df_sorted.head(100).copy()
    
    if len(df_top100) > 0:
        df_top100['rank'] = range(1, len(df_top100) + 1)
    else:
        df_top100['rank'] = []
    
    # Generate reasoning
    print("Step 7: Generating reasoning...")
    df_top100['reasoning'] = df_top100.apply(
        lambda row: f"Strong match with {row.get('tech_boost',0)*100:.0f}% tech stack alignment and high behavioral engagement.",
        axis=1
    ) if not df_top100.empty else []
    
    # Final submission format
    final_submission = df_top100[['candidate_id', 'rank', 'score', 'reasoning']] if not df_top100.empty else pd.DataFrame(columns=['candidate_id', 'rank', 'score', 'reasoning'])
    
    # Save to CSV
    print("Step 8: Saving submission CSV...")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    final_submission.to_csv(output_path, index=False)
    
    print(f"\nSUCCESS! Submission saved to: {output_path}")
    print(f"   Total candidates ranked: {len(final_submission)}")
    if not final_submission.empty:
        print(f"   Top score: {final_submission['score'].iloc[0]:.4f}")
        print(f"   Bottom score: {final_submission['score'].iloc[-1]:.4f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Rank candidates for the Redrob Hackathon'
    )
    parser.add_argument(
        '--candidates',
        required=True,
        help='Path to candidates.jsonl or candidates.jsonl.gz file'
    )
    parser.add_argument(
        '--out',
        required=True,
        help='Path for output submission.csv file'
    )
    
    args = parser.parse_args()
    
    # Validate input file exists
    if not os.path.exists(args.candidates):
        print(f"ERROR: Candidates file not found: {args.candidates}")
        exit(1)
    
    main(args.candidates, args.out)
