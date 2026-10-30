# DNS Scout Bilingual UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a persisted Simplified Chinese/English UI switch to one Windows x64 portable EXE and publish it as `v0.1.0-preview.3`.

**Architecture:** Add a small localization module for message catalogs, region labels, language detection, and persisted preference. Integrate it into the existing Tkinter `App` so changing language rerenders labels in place while preserving current inputs/results; keep DNS behavior and external provider metadata intact.

**Tech Stack:** Python 3.12, Tkinter, unittest, PowerShell, PyInstaller 6.19.0, Wine-hosted Windows Python for packaging on this Linux host.

**Spec:** `docs/superpowers/specs/2026-10-30-bilingual-dns-scout-design.md`

## Global Constraints

- One EXE must allow switching between `zh-CN` and `en` at runtime.
- Initial language follows the Windows/system UI language; unknown locales default to Simplified Chinese.
- Save the explicit language selection below `%LOCALAPPDATA%\DNSScout`.
- Keep DNS measurement, network configuration, elevation boundaries, and source metadata behavior unchanged.
- The EXE is unsigned; Wine smoke testing does not claim Windows 11 UAC or adapter validation.
- Preserve the pre-existing untracked `.github/workflows/build.yml`.

## Review Focus

- Invalid or unreadable language settings must fall back to system language, then Chinese; test malformed JSON and unsupported language.
- Switching languages must preserve selected region, domain text, DNS fields, and rendered results; add a UI regression test.
- Region translation must map to the same source slug and cache key; test every region in both languages.
- Message formatting must preserve counts, timings, and validation values in both catalogs; test formatted status/error entries.
- CSV headings must follow the selected UI language while data values remain unmodified; test both header sets and formula safety.

---

### Task 1: Localization catalog, language preference, and region mapping

**Files:**
- Create: `scout/i18n.py`
- Test: `tests/test_i18n.py`

**Interfaces:**
- Produces `SUPPORTED_LANGUAGES`, `MESSAGES`, `REGIONS`, `detect_system_language()`, `resolve_language(saved, system)`, `load_language(path, system_language)`, `save_language(path, language)`, `region_labels(language)`, and `format_message(language, key, **values)`.
- `load_language` returns a supported locale; missing/corrupt settings use system language, then `zh-CN`.
- `REGIONS` maps stable region IDs to existing `scout.source.PAGES` keys; each ID has Chinese and English display labels.

- [ ] **Step 1: Write failing localization tests** for region parity/source mapping, locale fallback, settings round-trip/corrupt JSON, and formatted message lookup.
- [ ] **Step 2: Run** `python -m unittest tests.test_i18n -v`; confirm failures identify missing localization behavior.
- [ ] **Step 3: Implement** the immutable Chinese/English catalogs, locale normalization, JSON persistence, and region-label mapping in `scout/i18n.py`.
- [ ] **Step 4: Run** `python -m unittest tests.test_i18n -v`; confirm all localization tests pass.

### Task 2: Live language switching throughout the Tkinter UI

**Files:**
- Modify: `scout/app.py`
- Modify: `scout/source.py`
- Modify: `tests/test_ui.py`
- Modify: `tests/test_core.py`

**Interfaces:**
- `App` owns `self.language`, `self.t(key, **values)`, and `self.set_language(language)`.
- The selector displays the supported language names. Changing it persists the selection and refreshes widget labels and table headings without clearing user state.
- `fetch_servers(region, cache_dir)` returns `(servers, FetchSummary)` where `FetchSummary` contains a stable mode (`live` or `cache`), source URL, cache age, and optional fetch error; the UI formats it through the active catalog.

- [ ] **Step 1: Add a failing UI regression test** that switches zh-CN → en → zh-CN and checks translated headings/buttons while input values, selected region ID, DNS fields, selection, and result rows remain intact.
- [ ] **Step 2: Run** `python -m unittest tests.test_ui -v`; confirm the new test fails because the selector/in-place update is absent.
- [ ] **Step 3: Implement** a language-neutral `FetchSummary` in `scout/source.py`, with tests proving region selection retains existing URL/cache behavior. Localize the window title, labels, controls, fetch/progress/result statuses, validation and confirmation dialogs, backend errors, and Treeview headings. Keep stable region IDs separate from translated labels and localize CSV headings from the active language.
- [ ] **Step 4: Run** `python -m unittest tests.test_ui -v`; confirm switching preserves application state.

### Task 3: Documentation and preview release metadata

**Files:**
- Modify: `README.md`
- Modify: `RELEASE_NOTES.md`

- [ ] **Step 1: Document** the language selector, initial system-language choice, preference location, and portable EXE steps in Chinese and English.
- [ ] **Step 2: Update** preview release notes to `v0.1.0-preview.3`, describing bilingual UI and verification limits.
- [ ] **Step 3: Review** docs against the implemented control labels and actual build output names.

### Task 4: Full verification, Windows EXE build, and publication

**Files:**
- Build output: `dist/DNSScout.exe`, `dist/DNSScout-win11-x64.zip`, `dist/SHA256SUMS.txt`
- Release: GitHub `v0.1.0-preview.3`

- [ ] **Step 1: Run** `python -m unittest discover -s tests -v`; confirm all tests pass (use a display server for Tk tests).
- [ ] **Step 2: Run** the isolated PowerShell DNS configuration regression and syntax parse from `scripts/build-windows.ps1` / `docs/windows-build.yml`.
- [ ] **Step 3: Build** with Windows Python/PyInstaller 6.19.0 under Wine, including `scout/configure.ps1`; confirm a PE32+ x86-64 executable is produced.
- [ ] **Step 4: Smoke test** `DNSScout.exe --smoke-test` under Wine and verify it exits successfully; calculate SHA256 and create the distributable ZIP with README and LICENSE.
- [ ] **Step 5: Publish** `DNSScout.exe`, ZIP, and SHA256 file as GitHub pre-release `v0.1.0-preview.3`; verify the release page and uploaded asset names.

---

**Commit boundaries:** Commit localization tests/catalog, UI integration, then documentation as independently reviewable changes before the release tag. Do not stage or modify the pre-existing untracked workflow file.
