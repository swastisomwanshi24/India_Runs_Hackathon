from sentence_transformers import SentenceTransformer
import os
from pathlib import Path

def load_hf_token():
    """Load HuggingFace token from .env file"""
    env_path = Path(__file__).parent / 'models' / '.env'
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if line.startswith('HF_TOKEN='):
                    token = line.split('=', 1)[1].strip()
                    os.environ['HF_TOKEN'] = token
                    return token
    return None

def download():
    # Load HF token before downloading
    load_hf_token()
    
    model_name = 'all-MiniLM-L6-v2'
    save_path = os.path.join('models', model_name)
    
    print(f"Downloading {model_name}...")
    model = SentenceTransformer(model_name)
    
    if not os.path.exists('models'):
        os.makedirs('models')
        
    model.save(save_path)
    print(f"Model saved to {save_path}. You can now run the ranker without internet.")

if __name__ == "__main__":
    download()
