#!/usr/bin/env python3
"""Index the EchoGrid Python codebase into ruflo (claude-flow) memory.

Walks the source tree, extracts per-file structure (module docstring,
classes + methods, function signatures, imports) with Python's ``ast``,
and stores one semantic-search entry per file in the ``echogrid-code``
memory namespace.

Run after significant code changes to refresh the index:

    python3 scripts/reindex_memory.py

Then search it (note the lower threshold — code-summary similarity scores
run ~0.35-0.5, well below the CLI default of 0.7):

    npx @claude-flow/cli@latest memory search \\
        -q "how are echo items generated" -n echogrid-code --threshold 0.3

Embeddings note: ``memory import`` does NOT regenerate vectors, so this
script stores each entry with ``--vector --upsert`` instead, which builds
the actual HNSW-indexed embedding. The ONNX model reloads per call; for a
few dozen files that is fine.
"""
import argparse
import ast
import os
import subprocess
import sys

# Repo root is the parent of this script's directory.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGETS = ["src", "app.py"]
SKIP_DIRS = {".venv", "_old", "__pycache__", ".git", "node_modules", "site", "data"}
NAMESPACE = "echogrid-code"
TAGS = "echogrid,python,code-index"
CLI = ["npx", "@claude-flow/cli@latest"]


def iter_py_files():
    for t in TARGETS:
        p = os.path.join(ROOT, t)
        if os.path.isfile(p) and p.endswith(".py"):
            yield p
        elif os.path.isdir(p):
            for dirpath, dirnames, filenames in os.walk(p):
                dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
                for fn in filenames:
                    if fn.endswith(".py"):
                        yield os.path.join(dirpath, fn)


def sig(node):
    """Render a def/method signature as ``name(arg1, arg2, *args, **kw)``."""
    a = node.args
    parts = [arg.arg for arg in a.posonlyargs + a.args]
    if a.vararg:
        parts.append("*" + a.vararg.arg)
    if a.kwonlyargs:
        if not a.vararg:
            parts.append("*")
        parts.extend(k.arg for k in a.kwonlyargs)
    if a.kwarg:
        parts.append("**" + a.kwarg.arg)
    return "{}({})".format(node.name, ", ".join(parts))


def summarize(path):
    """Return (rel_path, loc, summary_text) for one source file."""
    rel = os.path.relpath(path, ROOT)
    with open(path, "r", encoding="utf-8") as f:
        source = f.read()
    loc = source.count("\n") + 1
    try:
        tree = ast.parse(source, filename=rel)
    except SyntaxError as e:
        return rel, loc, "File: {} ({} LOC) — unparseable: {}".format(rel, loc, e)

    doc = ast.get_docstring(tree) or ""
    classes, funcs, imports = [], [], []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            methods = [sig(n) for n in node.body
                       if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
            cdoc = (ast.get_docstring(node) or "").strip().split("\n")[0]
            classes.append((node.name, cdoc, methods))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            fdoc = (ast.get_docstring(node) or "").strip().split("\n")[0]
            funcs.append((sig(node), fdoc))
        elif isinstance(node, ast.Import):
            imports.extend(n.name for n in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or ".")

    lines = ["File: {} ({} LOC)".format(rel, loc)]
    if doc:
        lines.append("Purpose: " + " ".join(doc.strip().split())[:600])
    if classes:
        lines.append("Classes:")
        for name, cdoc, methods in classes:
            lines.append("  - {}".format(name) + (": " + cdoc if cdoc else ""))
            if methods:
                lines.append("    methods: " + ", ".join(methods))
    if funcs:
        lines.append("Functions:")
        for s, fdoc in funcs:
            lines.append("  - {}".format(s) + (" — " + fdoc if fdoc else ""))
    if imports:
        lines.append("Imports: " + ", ".join(sorted(set(imports))))
    return rel, loc, "\n".join(lines)


def store(key, value, dry_run):
    cmd = CLI + [
        "memory", "store",
        "-k", key,
        "--value", value,
        "-n", NAMESPACE,
        "--tags", TAGS,
        "--vector", "--upsert",
    ]
    if dry_run:
        return True
    r = subprocess.run(cmd, capture_output=True, text=True)
    if "stored successfully" in r.stdout:
        return True
    sys.stderr.write((r.stdout[-300:] + r.stderr[-300:]).strip() + "\n")
    return False


def main():
    ap = argparse.ArgumentParser(description="Index EchoGrid code into ruflo memory.")
    ap.add_argument("--dry-run", action="store_true",
                    help="Print what would be indexed without calling the CLI.")
    args = ap.parse_args()

    files = sorted(iter_py_files())
    if not files:
        sys.exit("No Python files found under {}".format(TARGETS))

    ok = total_loc = 0
    for i, path in enumerate(files, 1):
        rel, loc, value = summarize(path)
        total_loc += loc
        success = store("code/" + rel, value, args.dry_run)
        ok += success
        print("[{:2}/{}] {} code/{}".format(
            i, len(files), "OK " if success else "ERR", rel), flush=True)

    print("\nFiles: {}/{} indexed | LOC: {} | namespace: {}{}".format(
        ok, len(files), total_loc, NAMESPACE,
        "  (dry run, nothing stored)" if args.dry_run else ""))
    sys.exit(0 if ok == len(files) else 1)


if __name__ == "__main__":
    main()
