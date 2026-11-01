"""
install_requirements.py

Installs every library found in D:\\==Local-Projects (from all_reqs.txt),
then checks each one and writes a CHECKLIST.

- Packages are installed ONE BY ONE, so if one fails the rest still install.
- It runs pip directly (python -m pip), so it works by double-click
  even if the VS Code / CMD terminal is blocked.
- It does NOT touch your project folders.

Output (saved next to this script):
    install_checklist.txt   <- the checklist  [OK] / [X]
    install_log.txt         <- full pip output, to see WHY something failed

Run: double-click this file   (or: python install_requirements.py)
"""

import datetime
import os
import subprocess
import sys
import time
from importlib import metadata

HERE = os.path.dirname(os.path.abspath(__file__))
CHECKLIST = os.path.join(HERE, "install_checklist.txt")
LOG = os.path.join(HERE, "install_log.txt")

# If PyPI is slow/blocked for you, put a mirror here, e.g.
# INDEX_URL = "https://mirror-pypi.runflare.com/simple"
INDEX_URL = ""

PY = sys.executable

# ---------------------------------------------------------------------------
# (pip install arguments,  distribution name,  import name,  note)
# Versions are NOT pinned: your projects ask for many different versions of
# the same library, which can't all live in one Python. pip picks the newest
# versions that work together.
# Sub-dependencies (pydantic-core, anyio, idna, certifi, ...) are installed
# automatically by pip and are not listed here.
# ---------------------------------------------------------------------------
PACKAGES = [
    # ---- web / API --------------------------------------------------------
    (["fastapi"], "fastapi", "fastapi", ""),
    (["uvicorn[standard]"], "uvicorn", "uvicorn", ""),
    (["gunicorn"], "gunicorn", None, "Linux-only server; on Windows use uvicorn"),
    (["starlette"], "starlette", "starlette", ""),
    (["pydantic"], "pydantic", "pydantic", ""),
    (["pydantic-settings"], "pydantic-settings", "pydantic_settings", ""),
    (["python-multipart"], "python-multipart", "python_multipart", ""),
    (["python-dotenv"], "python-dotenv", "dotenv", ""),
    (["httpx[http2]"], "httpx", "httpx", ""),
    (["requests"], "requests", "requests", ""),
    (["aiohttp"], "aiohttp", "aiohttp", ""),
    (["aiofiles"], "aiofiles", "aiofiles", ""),
    (["dependency-injector"], "dependency-injector", "dependency_injector", ""),
    (["prometheus-client"], "prometheus-client", "prometheus_client", ""),
    (["python-jose[cryptography]"], "python-jose", "jose", ""),
    (["passlib[bcrypt]"], "passlib", "passlib", ""),
    (["cachetools"], "cachetools", "cachetools", ""),
    (["fake-useragent"], "fake-useragent", "fake_useragent", ""),
    (["celery"], "celery", "celery", ""),
    (["PyYAML"], "PyYAML", "yaml", ""),
    (["rich"], "rich", "rich", ""),
    (["tqdm"], "tqdm", "tqdm", ""),
    (["psutil"], "psutil", "psutil", ""),
    (["easydict"], "easydict", "easydict", ""),
    (["addict"], "addict", "addict", ""),

    # ---- databases --------------------------------------------------------
    (["sqlalchemy[asyncio]"], "SQLAlchemy", "sqlalchemy", ""),
    (["alembic"], "alembic", "alembic", ""),
    (["asyncpg"], "asyncpg", "asyncpg", ""),
    (["psycopg2-binary"], "psycopg2-binary", "psycopg2", ""),
    (["pyodbc"], "pyodbc", "pyodbc", "needs Microsoft ODBC Driver for SQL Server to connect"),
    (["redis"], "redis", "redis", ""),
    (["pymongo"], "pymongo", "pymongo", ""),
    (["motor"], "motor", "motor", ""),
    (["elasticsearch>=8.0.0,<9.0.0"], "elasticsearch", "elasticsearch", "kept on v8 to match your ES server"),

    # ---- data -------------------------------------------------------------
    (["numpy"], "numpy", "numpy", ""),
    (["pandas"], "pandas", "pandas", ""),
    (["pyarrow"], "pyarrow", "pyarrow", ""),
    (["openpyxl"], "openpyxl", "openpyxl", ""),
    (["XlsxWriter"], "XlsxWriter", "xlsxwriter", ""),
    (["scipy"], "scipy", "scipy", ""),
    (["sympy"], "sympy", "sympy", ""),
    (["networkx"], "networkx", "networkx", ""),
    (["joblib"], "joblib", "joblib", ""),
    (["matplotlib"], "matplotlib", "matplotlib", ""),
    (["seaborn"], "seaborn", "seaborn", ""),
    (["plotly"], "plotly", "plotly", ""),
    (["streamlit"], "streamlit", "streamlit", ""),

    # ---- machine learning -------------------------------------------------
    (["scikit-learn"], "scikit-learn", "sklearn", ""),
    (["imbalanced-learn"], "imbalanced-learn", "imblearn", ""),
    (["lightgbm"], "lightgbm", "lightgbm", ""),
    (["torch", "torchvision"], "torch", "torch", "CPU version (see notes for GPU)"),
    (["torchvision"], "torchvision", "torchvision", ""),
    (["torch-geometric"], "torch-geometric", "torch_geometric", ""),
    (["transformers"], "transformers", "transformers", ""),
    (["huggingface-hub"], "huggingface-hub", "huggingface_hub", ""),
    (["datasets"], "datasets", "datasets", ""),
    (["evaluate"], "evaluate", "evaluate", ""),
    (["sentence-transformers"], "sentence-transformers", "sentence_transformers", ""),
    (["einops"], "einops", "einops", ""),
    (["tensorflow"], "tensorflow", "tensorflow", "large download"),
    (["scikeras"], "scikeras", "scikeras", ""),
    (["fasttext-wheel"], "fasttext-wheel", "fasttext", "pre-built fasttext for Windows"),
    (["albumentations"], "albumentations", "albumentations", ""),
    (["langchain-core"], "langchain-core", "langchain_core", ""),
    (["langchain-ollama"], "langchain-ollama", "langchain_ollama", ""),

    # ---- images / OCR / GUI -----------------------------------------------
    (["opencv-python"], "opencv-python", "cv2", ""),
    (["Pillow"], "Pillow", "PIL", ""),
    (["pytesseract"], "pytesseract", "pytesseract", "also needs the Tesseract program installed"),
    (["PyQt5"], "PyQt5", "PyQt5", ""),

    # ---- audio ------------------------------------------------------------
    (["vosk"], "vosk", "vosk", ""),
    (["pydub"], "pydub", "pydub", "also needs ffmpeg installed"),
    (["noisereduce"], "noisereduce", "noisereduce", ""),
    (["pywhispercpp"], "pywhispercpp", "pywhispercpp", "may need C++ build tools"),

    # ---- text / Persian ---------------------------------------------------
    (["rapidfuzz"], "rapidfuzz", "rapidfuzz", ""),
    (["Levenshtein"], "Levenshtein", "Levenshtein", ""),
    (["regex"], "regex", "regex", ""),
    (["symspellpy"], "symspellpy", "symspellpy", ""),
    (["pyahocorasick"], "pyahocorasick", "ahocorasick", ""),
    (["nltk"], "nltk", "nltk", ""),
    (["num2fawords"], "num2fawords", "num2fawords", ""),
    (["convert-numbers"], "convert-numbers", "convert_numbers", ""),
    (["persian-tools"], "persian-tools", "persian_tools", ""),
    (["jdatetime"], "jdatetime", "jdatetime", ""),
    (["arabic-reshaper"], "arabic-reshaper", "arabic_reshaper", ""),
    (["python-bidi"], "python-bidi", "bidi", ""),
    (["python-crfsuite"], "python-crfsuite", "pycrfsuite", "needed by hazm"),

    # ---- maps / geo / routing ---------------------------------------------
    (["shapely"], "shapely", "shapely", ""),
    (["Rtree"], "Rtree", "rtree", ""),
    (["pyproj"], "pyproj", "pyproj", ""),
    (["folium"], "folium", "folium", ""),
    (["geopy"], "geopy", "geopy", ""),
    (["haversine"], "haversine", "haversine", ""),
    (["h3"], "h3", "h3", ""),
    (["simplekml"], "simplekml", "simplekml", ""),
    (["osmium"], "osmium", "osmium", ""),
    (["ortools"], "ortools", "ortools", ""),
    (["lkh"], "lkh", "lkh", "also needs the LKH program to solve"),

    # ---- installed last WITHOUT their pinned dependencies -----------------
    # hazm and parsivar pin very old versions (e.g. numpy 1.24) that would
    # break pandas/torch, so they are installed with --no-deps.
    (["--no-deps", "hazm"], "hazm", "hazm", "installed with --no-deps (old pins)"),
    (["--no-deps", "parsivar"], "parsivar", "parsivar", "installed with --no-deps (old pins)"),
]

# Listed in your projects but intentionally NOT installed
SKIPPED = [
    ("asyncio==4.0.0", "built into Python already; the pip package is an old copy that breaks things"),
    ("uvloop", "does not support Windows (uvicorn works without it)"),
    ("triton", "Linux only"),
    ("nvidia-* / cuda-*", "Linux GPU files; torch on Windows handles this itself"),
    ("codespell", "only in Go vendor folders, not your code"),
    ("google (in handwritten_ocr_v2/train_crnn.ipynb)", "almost certainly google.colab - only works on Google Colab"),
]


class Out:
    """Print to screen and to a file at the same time."""
    def __init__(self, path):
        self.f = open(path, "w", encoding="utf-8")

    def __call__(self, text=""):
        print(text)
        self.f.write(text + "\n")
        self.f.flush()

    def close(self):
        self.f.close()


def run(cmd, log, timeout=None, tick=None):
    """Run a command; call tick() about every second while it runs
    (keeps the progress bar's timer moving during long downloads)."""
    import tempfile
    log.write("\n$ " + " ".join(cmd) + "\n")
    log.flush()
    try:
        with tempfile.TemporaryFile(mode="w+", encoding="utf-8", errors="replace") as tmp:
            p = subprocess.Popen(cmd, stdout=tmp, stderr=subprocess.STDOUT,
                                 text=True, encoding="utf-8", errors="replace")
            start = time.time()
            while p.poll() is None:
                if timeout and time.time() - start > timeout:
                    p.kill()
                    log.write("TIMEOUT\n")
                    return -1, "TIMEOUT"
                if tick:
                    tick()
                time.sleep(1)
            tmp.seek(0)
            output = tmp.read()
        log.write(output)
        log.flush()
        return p.returncode, output
    except Exception as e:
        log.write(f"ERROR: {e}\n")
        return -1, str(e)


def last_error_line(output):
    for line in reversed(output.strip().splitlines()):
        line = line.strip()
        if line.startswith("ERROR") or "error" in line.lower():
            return line[:110]
    return (output.strip().splitlines() or ["unknown error"])[-1][:110]


def pip_args():
    args = [PY, "-m", "pip", "install", "--disable-pip-version-check",
            "--retries", "5", "--timeout", "60"]
    if INDEX_URL:
        args += ["-i", INDEX_URL]
    return args


def installed_version(dist):
    try:
        return metadata.version(dist)
    except metadata.PackageNotFoundError:
        return None


class SimpleBar:
    """Fallback progress bar, used only if tqdm can't be installed."""
    def __init__(self, total, desc="", **kw):
        self.total, self.n, self.desc, self.post = total, 0, desc, ""
        self.start = time.time()
        self._draw()

    def _draw(self):
        width = 30
        done = int(width * self.n / max(self.total, 1))
        mins = int(time.time() - self.start) // 60
        line = f"\r{self.desc[:28]:<28} |{'#' * done}{'.' * (width - done)}| {self.n}/{self.total} {mins}min {self.post}"
        sys.stdout.write(line[:150].ljust(150))
        sys.stdout.flush()

    def refresh(self):
        self._draw()

    def set_description(self, desc):
        self.desc = desc
        self._draw()

    def set_postfix_str(self, s):
        self.post = s
        self._draw()

    def update(self, n=1):
        self.n += n
        self._draw()

    @staticmethod
    def write(text):
        sys.stdout.write("\r" + " " * 150 + "\r" + text + "\n")
        sys.stdout.flush()

    def close(self):
        sys.stdout.write("\n")


def get_progress_bar(log):
    """Use tqdm (install it first if needed); otherwise the simple bar."""
    try:
        from tqdm import tqdm
        return tqdm
    except ImportError:
        pass
    print("Installing tqdm for the progress bar ...")
    run(pip_args() + ["tqdm"], log)
    try:
        import importlib
        importlib.invalidate_caches()
        from tqdm import tqdm
        return tqdm
    except ImportError:
        print("tqdm not available - using a simple progress bar instead.")
        return SimpleBar


def main():
    only = None
    if "--only" in sys.argv:                      # e.g. --only numpy,pandas
        only = {n.lower() for n in sys.argv[sys.argv.index("--only") + 1].split(",")}
    packages = [p for p in PACKAGES if only is None or p[1].lower() in only]

    log = open(LOG, "w", encoding="utf-8")
    out = Out(CHECKLIST)
    start = time.time()

    out("=" * 78)
    out(f"INSTALL CHECKLIST   {datetime.datetime.now():%Y-%m-%d %H:%M}")
    out(f"Python: {sys.version.split()[0]}   ({PY})")
    out("=" * 78)

    # 1) upgrade pip itself first
    print("\nUpgrading pip ...")
    run(pip_args() + ["--upgrade", "pip", "setuptools", "wheel"], log)

    Bar = get_progress_bar(log)
    bar_fmt = "{desc:<32} {percentage:3.0f}%|{bar:30}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}] {postfix}"
    print("\n(big packages like torch / tensorflow can sit on one step for several minutes - that's normal)\n")

    # 2) install one by one
    results = {}
    n_ok = n_fail = 0
    bar = Bar(total=len(packages), desc="Installing", bar_format=bar_fmt, dynamic_ncols=True)
    for args, dist, imp, note in packages:
        bar.set_description(f"Installing {dist}")
        code, output = run(pip_args() + args, log, tick=bar.refresh)
        results[dist] = (code == 0, "" if code == 0 else last_error_line(output))
        if code == 0:
            n_ok += 1
            bar.write(f"  [OK] {dist}")
        else:
            n_fail += 1
            bar.write(f"  [X]  {dist}  ->  {results[dist][1]}")
        bar.set_postfix_str(f"ok={n_ok} failed={n_fail}")
        bar.update(1)
    bar.set_description("Installing - done")
    bar.close()

    # 3) check every package: is it installed, and does `import` work?
    print("\nChecking every package ...\n")
    rows = []
    n_ok = n_bad = 0
    bar = Bar(total=len(packages), desc="Checking", bar_format=bar_fmt, dynamic_ncols=True)
    for dist_args, dist, imp, note in packages:
        bar.set_description(f"Checking {dist}")
        ver = installed_version(dist)
        if ver and imp:
            code, output = run([PY, "-c", f"import {imp}"], log, timeout=600, tick=bar.refresh)
            imp_ok = code == 0
            err = "" if imp_ok else last_error_line(output)
        else:
            imp_ok, err = (ver is not None), ""
            if not ver:
                err = results.get(dist, (False, ""))[1]
        rows.append((dist, ver, imp_ok, err, note))
        if ver and imp_ok:
            n_ok += 1
        else:
            n_bad += 1
        bar.set_postfix_str(f"working={n_ok} problems={n_bad}")
        bar.update(1)
    bar.set_description("Checking - done")
    bar.close()

    ok = [r for r in rows if r[1] and r[2]]
    broken = [r for r in rows if r[1] and not r[2]]
    missing = [r for r in rows if not r[1]]

    out("")
    out(f"{'':5}{'PACKAGE':<26}{'VERSION':<16}NOTE")
    out("-" * 78)
    for dist, ver, imp_ok, err, note in rows:
        mark = "[OK]" if ver and imp_ok else ("[!]" if ver else "[X]")
        out(f"{mark:<5}{dist:<26}{(ver or 'NOT INSTALLED'):<16}{note}")
        if err:
            out(f"{'':9}reason: {err}")

    out("")
    out("=" * 78)
    out("SUMMARY")
    out("=" * 78)
    out(f"[OK] installed and working : {len(ok)}")
    out(f"[!]  installed, import fails: {len(broken)}" + ("   -> " + ", ".join(r[0] for r in broken) if broken else ""))
    out(f"[X]  not installed          : {len(missing)}" + ("   -> " + ", ".join(r[0] for r in missing) if missing else ""))
    out(f"Total: {len(rows)}   Time: {int(time.time() - start) // 60} min")

    out("")
    out("Intentionally skipped:")
    for name, why in SKIPPED:
        out(f"   - {name}: {why}")

    out("")
    out("Conflicts between installed packages (pip check):")
    code, output = run([PY, "-m", "pip", "check"], log)
    for line in output.strip().splitlines() or ["none"]:
        out("   " + line)

    out("")
    out(f"Full pip output: {LOG}")
    out.close()
    log.close()
    print(f"\nChecklist saved to: {CHECKLIST}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nUnexpected error: {e}")
    try:
        input("\nPress Enter to close...")
    except Exception:
        pass
