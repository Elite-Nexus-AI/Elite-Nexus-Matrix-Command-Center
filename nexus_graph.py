#!/usr/bin/env python3
# Matrix OS Nexus Codebase Graph Builder
# Maps the repo as a node graph for Claude Code navigation
import os, json, ast, re
from pathlib import Path

REPO = Path.home() / 'Downloads/files/matrix-hud-perfect'
OUTPUT = REPO / 'nexus_graph.json'

SKIP_DIRS = {'.git','.venv','node_modules','__pycache__','.mypy_cache'}
SKIP_EXT = {'.pyc','.pyo','.jpg','.png','.webp','.ico','.onnx','.bin','.safetensors'}

def get_python_imports(filepath):
    imports = []
    try:
        src = Path(filepath).read_text(errors='ignore')
        for line in src.split('\n'):
            line = line.strip()
            if line.startswith('import ') or line.startswith('from '):
                imports.append(line[:80])
    except: pass
    return imports[:10]

def get_js_imports(filepath):
    imports = []
    try:
        src = Path(filepath).read_text(errors='ignore')
        for line in src.split('\n')[:50]:
            if 'import ' in line or 'require(' in line:
                imports.append(line.strip()[:80])
    except: pass
    return imports[:10]

def build_graph():
    nodes = []
    edges = []
    file_map = {}
    node_id = 0

    for root, dirs, files in os.walk(REPO):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fname in files:
            fpath = Path(root) / fname
            if fpath.suffix in SKIP_EXT: continue
            if fpath.stat().st_size > 500000: continue
            rel = str(fpath.relative_to(REPO))
            size = fpath.stat().st_size
            ext = fpath.suffix

            # Determine node type and color
            if fname == 'bridge.py': ntype,color = 'core','#00e5ff'
            elif fname == 'index.html': ntype,color = 'core','#ff00ff'
            elif fname == 'llm_router.py': ntype,color = 'router','#ffd700'
            elif ext == '.py': ntype,color = 'python','#00ff88'
            elif ext in ('.html','.css'): ntype,color = 'frontend','#ff8800'
            elif ext == '.sh': ntype,color = 'shell','#aa44ff'
            elif ext == '.json': ntype,color = 'config','#0088ff'
            elif ext == '.md': ntype,color = 'docs','#ffffff'
            else: ntype,color = 'other','#444444'

            imports = []
            if ext == '.py': imports = get_python_imports(fpath)
            elif ext == '.html': imports = get_js_imports(fpath)

            node = {'id': node_id, 'label': fname, 'path': rel,
                    'type': ntype, 'color': color, 'size': size,
                    'imports': imports}
            nodes.append(node)
            file_map[fname] = node_id
            file_map[rel] = node_id
            node_id += 1

    # Build edges based on known relationships
    key_edges = [
        ('bridge.py','llm_router.py'),('bridge.py','index.html'),
        ('bridge.py','wake_word.py'),('bridge.py','global_hotkey.py'),
        ('start-matrix.sh','bridge.py'),('start-matrix.sh','start_vllm.sh'),
        ('start_wake.sh','wake_word.py'),('start_wake.sh','global_hotkey.py'),
    ]
    eid = 0
    for src,tgt in key_edges:
        if src in file_map and tgt in file_map:
            edges.append({'id':eid,'source':file_map[src],'target':file_map[tgt],'color':'#00e5ff22'})
            eid += 1

    graph = {'nodes':nodes,'edges':edges,'repo':str(REPO),'total_files':len(nodes),'total_edges':len(edges)}
    OUTPUT.write_text(json.dumps(graph, indent=2))
    print(f'Nexus graph: {len(nodes)} nodes, {len(edges)} edges -> {OUTPUT}')
    return graph

if __name__ == '__main__':
    build_graph()