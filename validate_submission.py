#!/usr/bin/env python3
"""Root-level wrapper for the validator that lives in `notebook/validate_submission.py`.
Run: python validate_submission.py data/final/submission.csv
"""
import runpy
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / 'notebook' / 'validate_submission.py'
if not TARGET.exists():
    print(f"Validator script not found at: {TARGET}")
    sys.exit(2)

# Execute the existing script as __main__ so CLI behaviour remains identical
runpy.run_path(str(TARGET), run_name='__main__')
