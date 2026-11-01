# Python Requirements Collector & Installer

Two Python scripts for Windows. The first scans a folder full of Python projects and finds every library they need, from the requirements files and from the `import` lines in the code. The second installs all of those libraries and gives you a checklist of what worked and what didn't.

Both run with a **double-click**, so they still work on machines where the terminal (CMD / PowerShell / VS Code terminal) is blocked.

---

## Why

Over time, a projects folder collects dozens of repositories. Some have a `requirements.txt`, some don't, some have one that's out of date, and some only list half of what the code imports. Setting up a new machine, or one shared environment, from that is slow and error-prone.

This tool:

1. Finds **every** library your projects use, including the ones missing from `requirements.txt`.
2. Installs them all in one run, without stopping at the first failure.
3. Tells you exactly which libraries are installed, which import correctly, and which failed and why.

---

## Features

### `collect_requirements.py` (scanner)

- **Read-only.** It never changes, moves or deletes anything in your projects.
- Finds requirements files by common names and typos: `requirements.txt`, `requirement.txt`, `requirments.txt`, `requirements-dev.txt`, `*.in`.
- Parses every `.py` file (using Python's `ast` module) and every Jupyter notebook (`.ipynb`) for `import` / `from ... import` statements.
- Leaves out the standard library, relative imports and each project's own local modules.
- Converts import names to pip package names (`cv2` → `opencv-python`, `sklearn` → `scikit-learn`, `PIL` → `Pillow`, `yaml` → `PyYAML`, and 90+ more).
- Skips virtual environments (`venv`, `.venv`, any folder containing `pyvenv.cfg`), `node_modules`, `vendor`, build and cache folders.
- Handles UTF-8, UTF-16 (from `pip freeze` in PowerShell) and legacy encodings.
- Report includes:
  - a per-project summary, with libraries **missing** from each project's requirements
  - the libraries found only in code, with the projects that use them
  - one combined, de-duplicated list of everything needed

### `install_requirements.py` (installer)

- Installs packages **one at a time**, so one failure doesn't block the rest.
- **Live `tqdm` progress bar** with the current package, percentage, elapsed and remaining time, and running success/failure counts. It installs tqdm itself, and falls back to a built-in bar if it can't.
- Two-stage check for every package:
  - is it **installed**? (via `importlib.metadata`)
  - does `import` **actually work**? (in a separate process, so a crashing library can't take down the run)
- Writes a clear checklist with `[OK]` / `[!]` / `[X]` and the reason for every failure.
- Runs `pip check` at the end to report version conflicts.
- Installs packages with problematic old pins (e.g. `hazm`, `parsivar`) with `--no-deps`, so they don't downgrade NumPy and break the rest of your stack.
- Supports a custom PyPI mirror (`INDEX_URL`) for slow or restricted networks.
- Saves the full pip output to a log file for troubleshooting.

---

## Requirements

- Windows 10/11 (also works on Linux/macOS)
- Python **3.10+** (3.12 recommended)
- Internet access to PyPI, or a mirror, for the installer

The scanner uses only the Python standard library.

---

## Usage

### 1. Scan your projects

Set the folder to scan at the top of `collect_requirements.py`:

```python
ROOT = r"D:\==Local-Projects"
```

Then **double-click** `collect_requirements.py`, or run:

```bash
python collect_requirements.py
python collect_requirements.py "D:\path\to\other\folder"
```

The report is printed and saved as **`all_reqs.txt`** next to the script.

### 2. Review the package list

Open `install_requirements.py` and check the `PACKAGES` list against your report. Each entry looks like this:

```python
(["pip", "install", "args"], "distribution-name", "import_name", "note")
```

Add, remove or adjust entries as needed. Packages that are intentionally not installed go in `SKIPPED`, with a reason.

### 3. Install and verify

**Double-click** `install_requirements.py`, or run:

```bash
python install_requirements.py
python install_requirements.py --only numpy,pandas,torch    # install a subset
```

Output files, saved next to the script:

| File | Contents |
|---|---|
| `install_checklist.txt` | Final checklist and summary |
| `install_log.txt` | Full pip output, to see *why* something failed |

### Example output

```
Installing torch            42%|████████████▌      | 44/105 [12:30<17:10] ok=42 failed=2

     PACKAGE                   VERSION         NOTE
------------------------------------------------------------------------------
[OK] fastapi                   0.141.1
[OK] pandas                    3.0.5
[!]  pywhispercpp              1.3.0           may need C++ build tools
         reason: ImportError: DLL load failed while importing _pywhispercpp
[X]  lkh                       NOT INSTALLED   also needs the LKH program to solve
         reason: ERROR: Failed building wheel for lkh

SUMMARY
[OK] installed and working : 101
[!]  installed, import fails: 1    -> pywhispercpp
[X]  not installed          : 1    -> lkh
```

| Mark | Meaning |
|---|---|
| `[OK]` | Installed and imports correctly |
| `[!]` | Installed, but `import` fails (missing system dependency, DLL, etc.) |
| `[X]` | Not installed (see the reason) |

---

## Configuration

| Setting | File | Description |
|---|---|---|
| `ROOT` | `collect_requirements.py` | Folder to scan |
| `SKIP_DIRS` | `collect_requirements.py` | Folder names to ignore |
| `IMPORT_TO_PIP` | `collect_requirements.py` | Import name → pip name mapping |
| `PACKAGES` | `install_requirements.py` | Packages to install and verify |
| `SKIPPED` | `install_requirements.py` | Packages deliberately left out, with reasons |
| `INDEX_URL` | `install_requirements.py` | Optional PyPI mirror |

---

## Notes and limitations

- **One environment, many projects.** Different projects often pin different versions of the same library. The installer installs unpinned, compatible versions into a single environment. For exact reproducibility, use one virtual environment per project.
- **Import names are matched, not guaranteed.** Libraries the scanner finds only in code are mapped from their import name. Uncommon packages may need a manual check.
- **Some packages need system software** that pip can't install: Tesseract (`pytesseract`), ffmpeg (`pydub`), the Microsoft ODBC driver (`pyodbc`), the LKH solver (`lkh`), C++ build tools (some source-only packages).
- **Linux-only packages** (`uvloop`, `triton`, `gunicorn` as a server, NVIDIA CUDA wheels) are skipped or flagged on Windows.
- PyTorch installs the **CPU build** by default. For GPU support, install it from the [PyTorch index](https://pytorch.org/get-started/locally/).

---

## Project structure

```
.
├── collect_requirements.py   # read-only scanner -> all_reqs.txt
├── install_requirements.py   # installer + verifier -> install_checklist.txt
├── .gitignore
├── LICENSE
└── README.md
```

---

## License

MIT. See [LICENSE](LICENSE).
