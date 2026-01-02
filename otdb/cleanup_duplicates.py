#!/usr/bin/env python3
"""
Cleanup script to merge duplicate category files and remove duplicate questions.

This script:
1. Identifies duplicate category files (same category, different filenames)
2. Merges them into a single file
3. Removes duplicate questions across all files
4. Normalizes category names
"""
import json
import os
import shutil
from collections import defaultdict
from pathlib import Path


def normalize_category_name(category):
    """Normalize category name for consistent comparison."""
    # Convert to lowercase, remove extra spaces
    normalized = category.lower().strip()
    # Replace common variations
    normalized = normalized.replace('&', 'and')
    normalized = normalized.replace('amp;', 'and')
    # Remove special characters except spaces
    normalized = ''.join(c if c.isalnum() or c.isspace() else ' ' for c in normalized)
    # Normalize spaces
    normalized = ' '.join(normalized.split())
    return normalized


def get_category_from_file(filepath):
    """Get the actual category name from a JSON file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if data and isinstance(data, list) and len(data) > 0:
                if 'category' in data[0]:
                    return data[0]['category']
    except:
        pass
    return None


def load_all_questions(data_dir):
    """Load all questions from all JSON files."""
    all_questions = {}  # question_text -> (category, question_data)
    file_questions = defaultdict(list)  # filename -> list of questions
    
    for filename in os.listdir(data_dir):
        if not filename.endswith('_questions.json'):
            continue
        
        filepath = os.path.join(data_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for q in data:
                    question_text = q.get('question', '').strip()
                    if question_text:
                        file_questions[filename].append(q)
                        # Track by normalized question text
                        normalized_q = question_text.lower().strip()
                        if normalized_q not in all_questions:
                            all_questions[normalized_q] = (q.get('category'), q)
        except Exception as e:
            print(f"Error reading {filename}: {e}")
    
    return all_questions, file_questions


def merge_category_files(data_dir, dry_run=True):
    """Merge duplicate category files."""
    print("=== Step 1: Finding duplicate category files ===")
    
    # Group files by normalized category name
    category_groups = defaultdict(list)
    
    for filename in os.listdir(data_dir):
        if not filename.endswith('_questions.json'):
            continue
        
        filepath = os.path.join(data_dir, filename)
        category = get_category_from_file(filepath)
        
        if category:
            normalized = normalize_category_name(category)
            category_groups[normalized].append((filename, filepath, category))
    
    # Find duplicates
    duplicates = {k: v for k, v in category_groups.items() if len(v) > 1}
    
    if not duplicates:
        print("✓ No duplicate category files found")
        return {}
    
    print(f"Found {len(duplicates)} categories with duplicate files:\n")
    
    merge_plan = {}
    for normalized, files in duplicates.items():
        print(f"Category: {files[0][2]}")
        for filename, filepath, cat in files:
            size = os.path.getsize(filepath)
            print(f"  - {filename} ({size} bytes)")
        
        # Choose the file with most questions as the target
        file_sizes = [(f[0], os.path.getsize(f[1])) for f in files]
        target_file = max(file_sizes, key=lambda x: x[1])[0]
        source_files = [f[0] for f in files if f[0] != target_file]
        
        merge_plan[normalized] = {
            'target': target_file,
            'sources': source_files,
            'category': files[0][2]
        }
        print(f"  → Will merge into: {target_file}")
        print()
    
    if dry_run:
        print("(DRY RUN - no files modified)")
        return merge_plan
    
    # Actually merge
    print("\n=== Step 2: Merging files ===")
    merged_count = 0
    
    for normalized, plan in merge_plan.items():
        target_path = os.path.join(data_dir, plan['target'])
        
        # Load target file
        with open(target_path, 'r', encoding='utf-8') as f:
            target_questions = {q.get('question', '').strip(): q for q in json.load(f)}
        
        # Load and merge source files
        for source_file in plan['sources']:
            source_path = os.path.join(data_dir, source_file)
            with open(source_path, 'r', encoding='utf-8') as f:
                source_questions = json.load(f)
            
            added = 0
            for q in source_questions:
                q_text = q.get('question', '').strip()
                if q_text and q_text not in target_questions:
                    target_questions[q_text] = q
                    added += 1
            
            print(f"Merged {source_file}: added {added} new questions")
        
        # Save merged file
        questions_list = list(target_questions.values())
        with open(target_path, 'w', encoding='utf-8') as f:
            json.dump(questions_list, f, indent=4, ensure_ascii=False)
        
        # Delete source files
        for source_file in plan['sources']:
            source_path = os.path.join(data_dir, source_file)
            os.remove(source_path)
            print(f"Deleted {source_file}")
        
        merged_count += 1
    
    print(f"\n✓ Merged {merged_count} category groups")
    return merge_plan


def remove_duplicate_questions(data_dir, dry_run=True):
    """Remove duplicate questions across all files."""
    print("\n=== Step 3: Removing duplicate questions ===")
    
    all_questions, file_questions = load_all_questions(data_dir)
    
    # Track which questions we've seen
    seen_questions = {}
    duplicates_found = 0
    
    for filename, questions in file_questions.items():
        filepath = os.path.join(data_dir, filename)
        unique_questions = []
        
        for q in questions:
            question_text = q.get('question', '').strip()
            normalized_q = question_text.lower().strip()
            
            if normalized_q in seen_questions:
                duplicates_found += 1
                if dry_run:
                    print(f"Duplicate in {filename}: '{question_text[:60]}...'")
            else:
                seen_questions[normalized_q] = filename
                unique_questions.append(q)
        
        if not dry_run and len(unique_questions) < len(questions):
            # Save deduplicated file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(unique_questions, f, indent=4, ensure_ascii=False)
            print(f"  {filename}: removed {len(questions) - len(unique_questions)} duplicates")
    
    print(f"\nTotal duplicate questions found: {duplicates_found}")
    if dry_run:
        print("(DRY RUN - no files modified)")
    else:
        print("✓ Duplicate questions removed")
    
    return duplicates_found


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Clean up duplicate category files and questions')
    parser.add_argument('--data-dir', default='data', help='Data directory (default: data)')
    parser.add_argument('--execute', action='store_true', help='Actually perform the cleanup (default: dry run)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.data_dir):
        print(f"Error: Directory '{args.data_dir}' does not exist")
        return
    
    print("=" * 60)
    print("Category File Cleanup Script")
    print("=" * 60)
    print(f"Data directory: {args.data_dir}")
    print(f"Mode: {'EXECUTE' if args.execute else 'DRY RUN'}")
    print()
    
    # Step 1: Merge duplicate category files
    merge_plan = merge_category_files(args.data_dir, dry_run=not args.execute)
    
    # Step 2: Remove duplicate questions
    if args.execute or not merge_plan:
        remove_duplicate_questions(args.data_dir, dry_run=not args.execute)
    
    if not args.execute:
        print("\n" + "=" * 60)
        print("This was a DRY RUN. Use --execute to actually perform cleanup.")
        print("=" * 60)


if __name__ == "__main__":
    main()

