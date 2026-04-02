# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Project Overview
AstroVision is a PyQt5 desktop application for astronomical data exploration 
and visualization, powered by SDSS (Sloan Digital Sky Survey) DR18. It 
provides a modular tabbed interface for searching, retrieving, and visualizing 
astronomical images and spectra. This is a portfolio project being revamped 
for professional presentation and public distribution.

## Running the Application
```bash
# From the repo root
python src/AV.py
```

## Setup
```bash
python -m venv AV-env
AV-env\Scripts\activate
pip install -r requirements.txt
```

## Finalized Folder Structure
This is the target structure for the revamp. Do not deviate from it:
```
src/
├── AV.py                  # Entry point + QMainWindow (combined, not split)
├── theme.py               # Color constants, fonts, global QSS, apply_theme()
├── signals.py             # AppSignals singleton + global app_signals instance
├── utilities.py           # SDSS API helpers — untouched, stays in src/ root
├── modules/
│   ├── home.py            # HomeTab + ModuleCard (home screen)
│   ├── search.py
│   ├── quick_look.py
│   ├── fits_retrieval.py
│   ├── composite_creation.py
│   ├── image_enhancement.py
│   └── spectrogram_inspector.py
└── widgets/
    └── star_field.py      # Animated star field background widget
```

## Architecture
**Entry point:** `src/AV.py` — QMainWindow with QTabWidget. Home tab is 
permanent (not closable). Each module opens in a new closable tab via the 
app_signals signal bus.

**Signal bus:** `src/signals.py` exports a global `app_signals` instance. 
Modules emit `app_signals.open_module(name)` to request navigation. 
`AV.py` listens and instantiates the correct module. Modules never import 
each other directly.

**Theme:** `src/theme.py` is the single source of truth for all visual 
styling. No hardcoded color or style strings anywhere else in the codebase. 
`apply_theme(app)` is called once at startup in `AV.py`.

**Module pattern:** Each module is a self-contained QWidget subclass. 
Helper classes (e.g. QThread subclasses) live in the same file as the 
module that uses them — they do not get their own file unless multiple 
unrelated modules need them.

**Threading:** Long I/O operations must use QThread. Never block the main 
thread with network calls. Existing threading:
- `ImageFetcher` in `search.py`
- `FITSDownloadThread` in `fits_retrieval.py`
- All other modules need async threading added in Phase 3

**Data flow:** User input → `utilities.validate_ra_dec()` → SDSS HTTP API 
→ display in PyQt5 widgets. Downloaded FITS files stored under `data/`.

## Visual Identity — Critical
- **Star field:** The animated twinkling star field on the home screen is 
  the most important visual element of the app. It must always be preserved 
  and must animate correctly.
- **Color palette:** Dark backgrounds (near-black, `#0D1117` family), teal 
  accent (`#55AA99`). These are non-negotiable.
- **Font:** Segoe UI throughout.
- **`#7C3AED` is never used under any circumstances.**
- **QPushButton default style:** Neutral (dark surface, subtle border). 
  Filled teal is opt-in only via `setProperty("accent", True)`. Never make 
  all buttons teal by default — it breaks module UIs.
- **Tab close button:** Hover state is red (`#FF6B6B`), not teal. This is 
  standard close button convention.

## Constraints — Non-Negotiable
- No overengineering. Every decision favors simplicity and readability.
- No new dependencies without explicit discussion.
- No abstract base classes, no config files, no plugin architecture.
- A widget only gets its own file if multiple unrelated modules need it. 
  Otherwise it lives in the file that uses it.
- `utilities.py` is untouched unless adding a new SDSS API integration.
- Do not modify module logic during structural or theming phases.

## Phased Roadmap
- **Phase 1 — Foundation:** Restructure folders, create theme.py, 
  signals.py, star_field.py, home.py, refactor AV.py ✅
- **Phase 2 — Home screen polish:** Animation fix, title size, card 
  proportions, icons, tab styling
- **Phase 3 — Module polish:** Apply theme, fix async threading, wire 
  inter-module signals — one module at a time
- **Phase 4 — Deployment:** Landing page, PyInstaller packaging, 
  GitHub Releases

## Key Conventions
- RA range 0–360°, DEC range −90–90°. Always validate with 
  `utilities.validate_ra_dec()`
- All SDSS base URLs defined in `utilities.py`. New integrations go there.
- Data source: SDSS only. No additional catalogs until v2.
- Git: work on `revamp` branch. `main` stays stable until revamp is complete.