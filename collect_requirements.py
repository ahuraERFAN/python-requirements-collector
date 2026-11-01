"""
collect_requirements.py

READ-ONLY scanner for D:\\==Local-Projects

It does two things:
  1. Reads every requirements file (requirements.txt, requirments.txt, ...)
  2. Reads every .py and .ipynb file and finds what they `import`
     -> so libraries that are used in code but NOT written in
        requirements.txt are also found.

It NEVER writes, renames, moves or deletes anything in your projects.
The only file it creates is the report "all_reqs.txt" NEXT TO THIS SCRIPT.

Run: double-click this file, or `python collect_requirements.py [folder]`
"""

import ast
import json
import os
import re
import sys

ROOT = r"D:\==Local-Projects"

# Folders to ignore (virtualenvs, caches, Go vendor folders, build output ...)
SKIP_DIRS = {
    ".git", ".hg", ".svn", "node_modules", "__pycache__",
    "venv", ".venv", "env", ".env", "virtualenv", "vendor",
    "site-packages", "dist-packages", ".tox", ".mypy_cache", ".pytest_cache",
    ".idea", ".vscode", ".ipynb_checkpoints", "build", "dist", ".eggs",
}

REQ_FILE_RE = re.compile(r"^(requ?i?re?ments?|reqs?)([\-_.].*)?\.(txt|in)$", re.IGNORECASE)
NAME_RE = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._\-]*)")

# import name  ->  pip install name (only where they are different)
IMPORT_TO_PIP = {
    "cv2": "opencv-python", "PIL": "Pillow", "sklearn": "scikit-learn",
    "skimage": "scikit-image", "yaml": "PyYAML", "dotenv": "python-dotenv",
    "jose": "python-jose", "jwt": "PyJWT", "bs4": "beautifulsoup4",
    "dateutil": "python-dateutil", "multipart": "python-multipart",
    "psycopg2": "psycopg2-binary", "psycopg": "psycopg[binary]",
    "Levenshtein": "Levenshtein", "fitz": "PyMuPDF", "docx": "python-docx",
    "pptx": "python-pptx", "serial": "pyserial", "Crypto": "pycryptodome",
    "OpenSSL": "pyOpenSSL", "magic": "python-magic", "osgeo": "GDAL",
    "torch_geometric": "torch-geometric", "pydantic_settings": "pydantic-settings",
    "pydantic_core": "pydantic-core", "dependency_injector": "dependency-injector",
    "prometheus_client": "prometheus-client", "huggingface_hub": "huggingface-hub",
    "langchain_core": "langchain-core", "langchain_ollama": "langchain-ollama",
    "langchain_community": "langchain-community", "langchain_openai": "langchain-openai",
    "persian_tools": "persian-tools", "convert_numbers": "convert-numbers",
    "google": "protobuf / google-* (check)", "win32api": "pywin32",
    "win32com": "pywin32", "pythoncom": "pywin32", "pywintypes": "pywin32",
    "attr": "attrs", "speech_recognition": "SpeechRecognition",
    "sentence_transformers": "sentence-transformers", "telegram": "python-telegram-bot",
    "jdatetime": "jdatetime", "hazm": "hazm", "Bio": "biopython",
    "mpl_toolkits": "matplotlib", "pkg_resources": "setuptools",
    "setuptools": "setuptools", "elasticsearch": "elasticsearch",
    "jalali_core": "jalali-core", "num2fawords": "num2fawords",
    "rtree": "Rtree", "osmium": "osmium", "lkh": "lkh",
    "ortools": "ortools", "xlsxwriter": "XlsxWriter", "streamlit": "streamlit",
    "typing_extensions": "typing-extensions", "et_xmlfile": "et-xmlfile",
    "socketio": "python-socketio", "engineio": "python-engineio",
    "redis": "redis", "aioredis": "aioredis", "motor": "motor",
    "bson": "pymongo", "gridfs": "pymongo", "pymongo": "pymongo",
    "geopandas": "geopandas", "shapely": "shapely", "pyproj": "pyproj",
    "faiss": "faiss-cpu", "tensorflow": "tensorflow", "keras": "keras",
    "ultralytics": "ultralytics", "easyocr": "easyocr", "paddleocr": "paddleocr",
    "pytesseract": "pytesseract", "vosk": "vosk", "pydub": "pydub",
    "noisereduce": "noisereduce", "librosa": "librosa", "soundfile": "soundfile",
    "sounddevice": "sounddevice", "pyaudio": "PyAudio", "whisper": "openai-whisper",
}

# Fallback stdlib list for old Pythons (3.10+ has sys.stdlib_module_names)
STDLIB = set(getattr(sys, "stdlib_module_names", ())) | {
    "__future__", "typing", "dataclasses", "asyncio", "concurrent", "importlib",
    "os", "sys", "re", "json", "time", "datetime", "math", "random", "logging",
    "collections", "itertools", "functools", "pathlib", "subprocess", "threading",
    "multiprocessing", "socket", "uuid", "hashlib", "base64", "csv", "io", "enum",
    "abc", "copy", "glob", "shutil", "tempfile", "traceback", "unittest", "urllib",
    "http", "email", "sqlite3", "pickle", "string", "struct", "warnings", "contextlib",
    "argparse", "configparser", "decimal", "statistics", "zipfile", "tarfile", "gzip",
    "queue", "signal", "platform", "getpass", "secrets", "hmac", "textwrap", "pprint",
    "inspect", "ast", "types", "weakref", "heapq", "bisect", "operator", "ssl", "select",
    "xml", "html", "ctypes", "unicodedata", "locale", "calendar", "zoneinfo", "fractions",
    "numbers", "array", "codecs", "difflib", "fnmatch", "mimetypes", "smtplib", "tkinter",
    "timeit", "cProfile", "pdb", "doctest", "builtins", "gc", "atexit", "errno", "stat",
    "winreg", "msvcrt", "_thread", "token", "tokenize", "dis", "venv", "ensurepip",
    "distutils", "lib2to3", "graphlib", "selectors", "shlex", "sched", "wave", "audioop",
}


def norm(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def read_text(path):
    """Read a file in read-only mode; handles UTF-8, UTF-16 and others."""
    with open(path, "rb") as f:
        raw = f.read()
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        return raw.decode("utf-16", errors="replace")
    for enc in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def parse_requirements(text):
    reqs = []
    for line in text.splitlines():
        line = line.split(" #")[0].strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        reqs.append(line)
    return reqs


IMPORT_LINE_RE = re.compile(r"^[ \t]*(?:from[ \t]+([A-Za-z_][\w.]*)[ \t]+import|import[ \t]+([A-Za-z_][\w. \t,]*))", re.M)


def imports_from_source(source):
    """Return top-level module names imported in Python source."""
    names = set()
    try:
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    names.add(a.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.level == 0 and node.module:   # skip relative "from . import x"
                    names.add(node.module.split(".")[0])
    except SyntaxError:
        # file has errors (or old Python 2) -> fall back to simple text search
        for m in IMPORT_LINE_RE.finditer(source):
            if m.group(1):
                names.add(m.group(1).split(".")[0])
            else:
                for part in m.group(2).split(","):
                    part = part.strip().split(" ")[0]
                    if part:
                        names.add(part.split(".")[0])
    return names


def notebook_source(text):
    """Get Python code from a Jupyter notebook (skips !pip / %magic lines)."""
    try:
        nb = json.loads(text)
    except Exception:
        return ""
    lines = []
    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        src = cell.get("source", "")
        src = "".join(src) if isinstance(src, list) else src
        for line in src.splitlines():
            if line.lstrip().startswith(("!", "%")):
                continue
            lines.append(line)
    return "\n".join(lines)


def walk(root):
    """Yield (dirpath, filenames) while skipping venvs and junk folders."""
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            d for d in dirnames
            if d.lower() not in SKIP_DIRS
            and not os.path.exists(os.path.join(dirpath, d, "pyvenv.cfg"))  # any venv
        ]
        yield dirpath, filenames


def project_of(path, root):
    rel = os.path.relpath(path, root)
    first = rel.split(os.sep)[0]
    return first if first != rel else "(root)"


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else ROOT
    if not os.path.isdir(root):
        print(f"Folder not found: {root}")
        return

    projects = {}   # name -> {"req_files": [], "reqs": [], "imports": {mod: [files]}, "local": set()}

    def proj(name):
        return projects.setdefault(name, {"req_files": [], "reqs": [], "imports": {}, "local": set()})

    errors = []
    for dirpath, filenames in walk(root):
        p = proj(project_of(os.path.join(dirpath, "x"), root))
        if any(f.endswith(".py") for f in filenames):
            p["local"].add(os.path.basename(dirpath))          # local package folder
        for name in filenames:
            path = os.path.join(dirpath, name)
            low = name.lower()
            try:
                if REQ_FILE_RE.match(name):
                    p["req_files"].append(os.path.relpath(path, root))
                    p["reqs"].extend(parse_requirements(read_text(path)))
                elif low.endswith(".py"):
                    p["local"].add(name[:-3])                   # local module
                    for mod in imports_from_source(read_text(path)):
                        p["imports"].setdefault(mod, []).append(os.path.relpath(path, root))
                elif low.endswith(".ipynb"):
                    for mod in imports_from_source(notebook_source(read_text(path))):
                        p["imports"].setdefault(mod, []).append(os.path.relpath(path, root))
            except Exception as e:
                errors.append(f"{path}: {e}")

    all_reqs = {}        # norm name -> set of requirement lines
    all_missing = {}     # pip name -> set of projects

    print("=" * 70)
    print(f"Scanned: {root}")
    print("=" * 70)

    for name in sorted(projects, key=str.lower):
        p = projects[name]
        req_names = set()
        for r in p["reqs"]:
            m = NAME_RE.match(r)
            key = norm(m.group(1)) if m else r
            req_names.add(key)
            all_reqs.setdefault(key, set()).add(r)

        third_party = {}
        for mod, files in p["imports"].items():
            if mod in STDLIB or mod.startswith("_") or mod in p["local"]:
                continue
            third_party[mod] = files

        missing = {}
        for mod, files in third_party.items():
            pip_name = IMPORT_TO_PIP.get(mod, mod)
            if norm(pip_name.split(" ")[0].split("[")[0]) not in req_names and norm(mod) not in req_names:
                missing[pip_name] = files

        if not p["reqs"] and not third_party:
            continue  # folder with no Python at all

        print(f"\n### PROJECT: {name}")
        print(f"    requirement files: {', '.join(p['req_files']) or 'NONE'}")
        print(f"    libraries imported in code: {len(third_party)}")
        if missing:
            print(f"    MISSING from requirements ({len(missing)}):")
            for pip_name in sorted(missing, key=str.lower):
                example = missing[pip_name][0]
                print(f"      - {pip_name:<30} (e.g. {example})")
                all_missing.setdefault(pip_name, set()).add(name)
        else:
            print("    nothing missing")

    # ---- final combined list --------------------------------------------
    final = {}
    for key, lines in all_reqs.items():
        final[key] = sorted(lines)
    for pip_name in all_missing:
        key = norm(pip_name.split(" ")[0].split("[")[0])
        final.setdefault(key, [pip_name + "   <- found only in imports"])

    print("\n" + "=" * 70)
    print(f"LIBRARIES FOUND ONLY IN CODE (not in any requirements file): {len(all_missing)}")
    print("=" * 70)
    for pip_name in sorted(all_missing, key=str.lower):
        print(f"{pip_name:<32} used in: {', '.join(sorted(all_missing[pip_name]))}")

    print("\n" + "=" * 70)
    print(f"ALL REQUIRED LIBRARIES (requirements files + imports): {len(final)}")
    print("=" * 70)
    for key in sorted(final):
        print(" | ".join(final[key]))

    if errors:
        print("\n" + "=" * 70)
        print(f"FILES THAT COULD NOT BE READ: {len(errors)}")
        print("=" * 70)
        for e in errors:
            print(e)

    print("\nNOTE: names 'found only in imports' are guesses from the import name.")
    print("A few may be your own local modules from another folder - send me the report and I'll check.")


class Tee:
    def __init__(self, *streams):
        self.streams = [s for s in streams if s is not None]

    def write(self, data):
        for s in self.streams:
            s.write(data)

    def flush(self):
        for s in self.streams:
            s.flush()


if __name__ == "__main__":
    report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "all_reqs.txt")
    with open(report_path, "w", encoding="utf-8") as report:
        sys.stdout = Tee(sys.__stdout__, report)
        try:
            main()
        finally:
            sys.stdout = sys.__stdout__
    print(f"\nReport saved to: {report_path}")
    try:
        input("Press Enter to close...")
    except Exception:
        pass
