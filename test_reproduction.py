#!/usr/bin/env python3
"""
Test script to verify the reproduction command works correctly
Run: python test_reproduction.py
"""
import subprocess
import os
import csv
import sys
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a shell command and return output"""
    print(f"Running: {cmd}")
    result = subprocess.run(
        cmd,
        shell=True,
        cwd=cwd,
        capture_output=True,
        text=True
    )
    return result

def test_reproduction():
    """Test the full reproduction pipeline"""
    print("=" * 70)
    print("REPRODUCTION TEST - Redrob Hackathon")
    print("=" * 70)
    
    root = Path(__file__).parent
    candidates_file = root / "data" / "raw" / "candidates.jsonl"
    output_file = root / "data" / "final" / "submission_test.csv"
    
    # Test 1: Check input file exists
    print("\n[TEST 1] Checking input file exists...")
    if not candidates_file.exists():
        print(f"FAIL: {candidates_file} not found")
        return False
    print(f"PASS: Found {candidates_file}")
    
    # Test 2: Run ranking command
    print("\n[TEST 2] Running ranking command...")
    cmd = f"python rank.py --candidates {candidates_file} --out {output_file}"
    result = run_command(cmd, cwd=root)
    
    if result.returncode != 0:
        print(f"FAIL: Command failed with exit code {result.returncode}")
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        return False
    print("PASS: Ranking command completed successfully")
    print("\nOutput:")
    print(result.stdout)
    
    # Test 3: Check output file was created
    print("\n[TEST 3] Checking output file was created...")
    if not output_file.exists():
        print(f"FAIL: {output_file} was not created")
        return False
    print(f"PASS: Found {output_file}")
    
    # Test 4: Check output format
    print("\n[TEST 4] Checking output format...")
    try:
        with open(output_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            # Check row count
            if len(rows) != 100:
                print(f"FAIL: Expected 100 rows, got {len(rows)}")
                return False
            
            # Check columns
            expected_cols = ['candidate_id', 'rank', 'score', 'reasoning']
            if list(rows[0].keys()) != expected_cols:
                print(f"❌ FAIL: Expected columns {expected_cols}, got {list(rows[0].keys())}")
                return False
            
            # Check ranks are 1-100
            ranks = [int(row['rank']) for row in rows]
            if ranks != list(range(1, 101)):
                print(f"❌ FAIL: Ranks are not 1-100 in order")
                return False
            
            # Check scores are non-increasing
            scores = [float(row['score']) for row in rows]
            for i in range(len(scores) - 1):
                if scores[i] < scores[i + 1]:
                    print(f"FAIL: Scores are not non-increasing (rank {i+1}: {scores[i]} < rank {i+2}: {scores[i+1]})")
                    return False
            
            # Check candidate_id format
            import re
            cand_pattern = re.compile(r'^CAND_\d{7}$')
            for row in rows:
                if not cand_pattern.match(row['candidate_id']):
                    print(f"FAIL: Invalid candidate_id format: {row['candidate_id']}")
                    return False
            
            print("PASS: Output format is correct")
            print(f"   - 100 rows")
            print(f"   - Ranks 1-100")
            print(f"   - Scores non-increasing ({scores[0]:.4f} → {scores[-1]:.4f})")
            print(f"   - All candidate_ids valid")
            
    except Exception as e:
        print(f"FAIL: Error reading output file: {e}")
        return False
    
    # Test 5: Run validator
    print("\n[TEST 5] Running official validator...")
    cmd = f"python validate_submission.py {output_file}"
    result = run_command(cmd, cwd=root)
    
    if result.returncode != 0:
        print(f"FAIL: Validator failed")
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        return False
    
    if "Submission is valid" not in result.stdout:
        print(f"FAIL: Validator did not confirm validity")
        print("STDOUT:", result.stdout)
        return False
    
    print("PASS: Official validator confirms submission is valid")
    
    # Cleanup test file
    if output_file.exists():
        output_file.unlink()
        print(f"\n🧹 Cleaned up test file: {output_file}")
    
    return True

def main():
    print("\n" + "STARTING REPRODUCTION TESTS".center(70, "="))
    
    success = test_reproduction()
    
    print("\n" + "=" * 70)
    if success:
        print("ALL TESTS PASSED!")
        print("=" * 70)
        print("\nThe reproduction command is working correctly!")
        print("\nTo generate your final submission, run:")
        print("  python rank.py --candidates ./data/raw/candidates.jsonl --out ./data/final/submission.csv")
        print("\nThen validate with:")
        print("  python validate_submission.py data/final/submission.csv")
        sys.exit(0)
    else:
        print("TESTS FAILED")
        print("=" * 70)
        print("\nPlease review the errors above and fix any issues.")
        sys.exit(1)

if __name__ == "__main__":
    main()
