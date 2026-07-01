# Text-to-Speech (TTS) Dataset Preparation Pipeline

A unified Python CLI utility to convert PDF books into normalized, sentence-split audio datasets using Microsoft Edge's high-quality Neural TTS.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [How to Run the Pipeline](#how-to-run-the-pipeline)
  - [1. Single-Command (Full Pipeline)](#1-single-command-full-pipeline)
  - [2. Step-by-Step Individual Commands](#2-step-by-step-individual-commands)
- [Project Structure](#project-structure)
- [Technical Details](#technical-details)
  - [Audio Merging Utilities](#audio-merging-utilities)
- [References & Dependencies](#references--dependencies)

---

## Prerequisites

1. **Python 3.12+**
2. **FFmpeg** (Required for merging audio files)
   - Ensure `ffmpeg` is installed on your system and added to your system's PATH.

---

## Installation

Using [uv](https://github.com/astral-sh/uv) (recommended):
```bash
uv init
uv add -r requirements.txt
```

---

## How to Run the Pipeline

The main entry point is `pipeline.py`.

### 1. Single-Command (Full Pipeline)
To run all steps sequentially (Convert PDF → Normalize Text → Split Sentences → Run TTS audio generation & Merge):
```bash
uv run pipeline.py all raw.pdf --tts
```
- By default, this will:
  - Extract text to `input.txt`
  - Normalize text to `input_normalized.txt`
  - Split sentences into `extracted/`
  - Generate speech into `mp3/` and merge into `mp3/merged.mp3` using the Tamil voice `ta-IN-PallaviNeural`.

### 2. Step-by-Step Individual Commands

#### **Step A: Convert PDF to Plain Text**
```bash
uv run pipeline.py pdf2txt <input.pdf> <output.txt>
```
*Example:* `uv run pipeline.py pdf2txt raw.pdf raw.txt`

#### **Step B: Normalize Text for TTS**
Cleans abbreviations, removes header artifacts, standalone digits, and structures paragraphs.
```bash
uv run pipeline.py normalize <input.txt> <output.txt>
```
*Example:* `uv run pipeline.py normalize raw.txt raw_normalized.txt`

#### **Step C: Split into Sentence Files**
Splits text into individual sentence files for granular speech processing.
```bash
uv run pipeline.py split <input.txt> -n 1 -o <output_dir> -p <filename_prefix>
```
*Example:* `uv run pipeline.py split raw_normalized.txt -n 1 -o ./extracted -p sentence`

#### **Step D: Run Batch Text-to-Speech**
Converts all sentence text files into MP3 audio files.
```bash
uv run pipeline.py batch -i <input_dir> -o <output_dir> -v <voice_name>
```
*Example:* `uv run pipeline.py batch -i ./extracted -o ./mp3 -v "ta-IN-PallaviNeural"`

#### **Step E: Merge Audio Files**
Merges multiple MP3 files into a single file with custom silence gaps.
```bash
uv run pipeline.py merge -i <input_dir> -o <output_file> -s <silence_ms>
```
*Example:* `uv run pipeline.py merge -i ./mp3 -o ./mp3/merged.mp3 -s 500`

---

## Project Structure

```
Text2Audio/
│
├── pipeline.py                 # Unified command-line entrypoint
├── requirements.txt            # Python dependencies
├── README.md                   # Project documentation
├── .gitignore                  # Git ignore rules
│
├── scripts/                    # Core script modules
│   ├── __init__.py             # Exposes script functions
│   ├── pdf2txt.py              # PDF extraction script
│   ├── normalize_for_tts.py    # Text cleaning & normalizing
│   ├── split_sentences.py      # Sentence splitting utility
│   ├── batch_process.py        # Core Edge TTS batch engine
│   ├── run_batch.py            # Batch driver with merge option
│   └── merge_mp3.py            # Audio merging via Pydub
│
└── mp3/                        # Output folder
    └── merge.py                # Standalone FFmpeg-only merge script
```

---

## Technical Details

### Audio Merging Utilities
There are two ways to merge your generated MP3s:
1. **Via `pydub` (used automatically in `pipeline.py`):**
   Requires the Python package `pydub` and works by loading segments into memory, appending them, and injecting custom silent intervals.
2. **Via Direct FFmpeg (`mp3/merge.py`):**
   A super-fast, memory-efficient command-line merging utility. Switch to the `mp3/` directory and run:
   ```bash
   cd mp3
   uv run merge.py
   ```

---

## References & Dependencies

* **[edge-tts](https://github.com/rany2/edge-tts)**: Interface to Microsoft Edge's online TTS service.
* **[pdfplumber](https://github.com/jasonmc/pdfplumber)**: Plumbs PDF files to extract detailed information on text, characters, and pages.
* **[pydub](https://github.com/jiaaro/pydub)**: Easy-to-use high-level audio interface.
* **[FFmpeg](https://ffmpeg.org/)**: The cross-platform solution to record, convert and stream audio and video.
