import os
import hashlib
from collections import defaultdict
import ast
import json
import sys

def get_hash(filepath):
    try:
        with open(filepath, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    except:
        return None

def analyze_workspace(base_dir):
    exact_duplicates = defaultdict(list)
    similar_names = defaultdict(list)
    junk_files = []
    
    # AST signatures for Python files to find structural clones
    py_signatures = defaultdict(list)
    
    for root, dirs, files in os.walk(base_dir):
        if '__pycache__' in dirs:
            dirs.remove('__pycache__')
        if '.venv' in dirs:
            dirs.remove('.venv')
        if 'node_modules' in dirs:
            dirs.remove('node_modules')
            
        for file in files:
            path = os.path.join(root, file)
            size = os.path.getsize(path)
            
            # Junk files
            if file == '.DS_Store' or file.endswith('.bak') or file.endswith('.tmp'):
                junk_files.append(path)
                continue
                
            # Exact duplicates (only for files > 1KB to avoid matching small generic files)
            if size > 1024:
                h = get_hash(path)
                if h:
                    exact_duplicates[h].append(path)
            
            # Similar names (grouping by filename without extension)
            base_name = os.path.splitext(file)[0].lower()
            similar_names[base_name].append(path)
            
            # Structural clones for Python
            if file.endswith('.py') and size < 100000:
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        tree = ast.parse(f.read())
                    # Create a signature based on function and class names
                    sig = tuple(sorted([node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.ClassDef))]))
                    if len(sig) > 2: # Only care if there are a few functions/classes
                        py_signatures[sig].append(path)
                except:
                    pass

    # Filter out singles
    duplicates = [paths for paths in exact_duplicates.values() if len(paths) > 1]
    similar_code = [paths for paths in py_signatures.values() if len(paths) > 1]
    name_clashes = [paths for paths in similar_names.values() if len(paths) > 1 and len(set([os.path.dirname(p) for p in paths])) > 1]

    report = {
        "junk_files_count": len(junk_files),
        "junk_files_sample": junk_files[:10],
        "exact_duplicates": duplicates[:5], # top 5 groups
        "structural_clones_python": similar_code[:5],
        "name_clashes_across_folders": name_clashes[:5]
    }
    
    print(json.dumps(report, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    analyze_workspace(target)
