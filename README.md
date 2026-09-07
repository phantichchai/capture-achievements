# Capture Genshin Impact Achievements

A Windows desktop utility for tracking Genshin Impact achievements. The current application loads the complete achievement catalogue and an account export, splits achievements into completed and uncompleted lists, and provides a searchable Tkinter interface for reviewing and updating progress.

![Application interface](docs/source/img/application.png)

## Current features

- Loads the catalogue from `all_achievements.json` and account achievement data from `achievements.json`.
- Determines completion by matching account `title` values to catalogue `Achievement` values and checking whether `progress` starts with `Completed`.
- Displays separate Completed and Uncompleted tabs with live counts and an overall percentage.
- Filters the table by achievement, description, requirements, hidden status, type, or version.
- Supports multi-selection, copying achievement names, opening the source wiki link, and moving achievements between the two lists.
- Saves the edited lists in `json_data/completed.json` and `json_data/uncompleted.json`, and offers to reload them on the next startup.

The repository also contains a capture/OCR pipeline. It includes popup detection from video, PaddleOCR region extraction, fuzzy title matching, achievement catalogue scraping from the Genshin Impact Fandom MediaWiki API, and screen/window recording. The main GUI exposes the catalogue refresh and video-processing actions directly.

## Project structure

```text
.
├── main.py                    # Application entry point
├── achievements.json          # Account OCR/export data: title, description, reward, progress
├── all_achievements.json      # Achievement catalogue and wiki metadata
├── template.png               # Popup template used by the capture pipeline
├── requirements.txt           # Runtime dependencies
├── build.bat                  # Local PyInstaller build command
├── gui/
│   ├── achievement.py         # Active tracker window and persistence
│   └── view/
│       ├── table.py           # Searchable achievement table and transfer actions
│       └── __init__.py
├── process/
│   ├── achievement_detector.py       # Template matching and popup extraction
│   ├── achievement_title_matcher.py  # OCR title normalization/fuzzy matching
│   ├── image_processor.py             # PaddleOCR extraction from popup regions
│   ├── media_wiki.py                  # Achievement catalogue scraper
│   ├── processor.py                   # Older processing orchestration/CLI
│   ├── recorder.py                    # Screen and window recording helpers
│   ├── text_processor.py              # Catalogue generation script
│   └── video_processor.py             # OCR-aware video processor
├── resources/icon.ico
├── docs/source/img/application.png
├── debug/                    # Generated OCR/debug images; ignored by Git
├── detected/                 # Generated popup crops; ignored by Git
└── json_data/                # Generated tracker/processing JSON; ignored by Git
```

## Setup

The project is Python-based and the build workflow targets Windows with Python 3.13. A Python installation with Tk support is required for the desktop UI.

From PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The OCR/video modules use PaddleOCR, PaddlePaddle, OpenCV, MSS, and PyGetWindow. The active tracker UI itself uses the Python standard library (Tkinter plus JSON/file handling), but installing the full requirements file keeps the repository ready for the processing modules. The MediaWiki scraper additionally imports `requests`; install it separately if you use that script and it is not already available in your environment:

```powershell
python -m pip install requests
```

## Run the tracker

Ensure `achievements.json` and `all_achievements.json` are in the repository root, then run:

```powershell
python main.py
```

On first launch, the application creates `json_data/`, calculates the two lists from the root JSON files, and writes the saved lists there. On later launches, it asks whether to load the saved lists or recalculate them from the root data. Use **Save Progress** after moving rows between tabs.

To refresh only the local achievement catalogue and exit without opening the UI or processing video, run:

```powershell
python main.py fetch
```

The command reports added, updated, unchanged, and locally retained achievements that are missing from the remote catalogue. It only rewrites `all_achievements.json` when additions or updates are found; locally missing entries are not deleted. A fetch/update failure returns a non-zero exit code in this mode. The same refresh runs automatically before the OCR-aware video processor starts; failures there are warnings and processing continues with the existing catalogue.

The JSON files are expected to use these fields:

- Account data: `title` and `progress` (with optional `description` and `reward`).
- Catalogue data: `Achievement`, `Achievement_link`, `Description`, `Requirements`, `Hidden?`, `Type`, `Version`, and optional `Primogem`.

## Capture/OCR utilities

These are standalone development utilities rather than the default application workflow:

```powershell
# Generate/update all_achievements.json from the Fandom MediaWiki page
python -m process.text_processor

# Detect achievement popups and write crops to detected/ and overlays to debug/
python process/achievement_detector.py

# Record the primary monitor; press q in the preview window to stop
python process/recorder.py
```

`process/image_processor.py` can run OCR against the sample screenshot when invoked directly. `process/video_processor.py` exposes the shared `process_video_file()` function used by both the GUI and command-line processing paths.

## Build

For a local Windows executable, run:

```powershell
.\build.bat
```

This invokes PyInstaller in windowless mode, includes `resources/*`, and applies `resources/icon.ico`. The generated `build/` and `dist/` directories are ignored. GitHub Actions performs the same build on pushes to `main` and via manual dispatch, then uploads the contents of `dist/` as the `built-exe` artifact.

## Development workflow

There is currently no test suite or formatter configuration in the repository. A practical development loop is:

1. Work from the repository root so the relative JSON, template, resource, `debug/`, and `detected/` paths resolve correctly.
2. Make a focused change in `gui/` or `process/` and keep generated files out of commits.
3. Launch `python main.py` to smoke-test the tracker UI and its persistence/transfer behavior.
4. Exercise a relevant standalone processing script if changing OCR, detection, scraping, or recording code.
5. Run the PyInstaller build when validating packaging changes.

The GitHub build workflow is defined in `.github/workflows/build.yaml` and is the repository’s current automated validation; it installs dependencies and verifies that `main.py` can be packaged.

## License

See [LICENSE](LICENSE).
