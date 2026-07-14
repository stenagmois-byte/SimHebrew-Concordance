# 🎼 Tanach Cantillation Musicology Lab: Sequence & Modal Analysis

Welcome to the open-source laboratory for the computational analysis of the ancient musical scores embedded within the Hebrew Bible. 

This directory contains data matrices, full-chapter **MusicXML scores**, and automated Python tools designed to study the cantillation marks (*ta'amim*) not merely as grammatical punctuation, but as a sophisticated musical system mapping the sense, emotion, and structural syntax of the text.

---

## 🔍 The Project Pillars & Datasets

This project provides two distinct, canonical data pipelines spanning all 39 books of the Tanach:

1. **`MUSICSTATS.xlsx` (The Fixed-Interval Baseline)**: This data matrix captures every verse with its raw text-accent abbreviations and clean note equivalents. The entire dataset is mapped in the default fixed modes popularized by Suzanne Haïk-Vantoura (SHV): the `f -> g#` interval system for the 21 prose books, and the `f# -> g` system for the 3 poetic books (Psalms, Proverbs, Job).
2. **MusicXML Archive (The Dynamic Modal Traces)**: A comprehensive library of raw MusicXML files extracted directly from our database. Unlike the static baseline, this archive incorporates variable modal shifts chosen specifically to match the structural, strophic, and emotional demands of the text—particularly across the Psalms.

### 🧩 The Ultimate Deep Puzzle: Decrypting the Ancient Modes
By providing both a fixed baseline and a fluid modal trace, this lab invites researchers to tackle a generational question: **Is there an acoustic fingerprint embedded in the sequence lines or strophes that hints at the exact musical mode the ancients were using?** Using Python, we can search for the unique interval patterns that mathematically signal a shift in the ancient musical key.

---

## 🚀 Quick Start: Running Your First Analysis

This workspace is engineered with relative path logic. You can clone this repository and run analysis scripts locally on your PC without needing to hardcode file paths or change any configuration settings.

### Prerequisites
Make sure you have Python installed, then install the required data analysis libraries via your terminal:
```bash
pip install pandas openpyxl
```

### Executing the Genesis 1 Sequence Test
1. Clone this repository to your computer.
2. Navigate into the script directory using your Command Prompt or Terminal:
   ```bash
   cd musicscores/analysis_scripts
   ```
3. Run the automated explorer script:
   ```bash
   python explore_genesis.py
   ```

The script will look up into the parent folder, process `MUSICSTATS.xlsx`, and output a mathematical breakdown of the top repeating musical phrases (n-grams), cleanly isolating the inner structural architecture of the chapter (such as the 3-note building blocks of the famous Creation Refrain).

---

## 🤝 Open Invitation for Collaboration
This framework is a stimulus designed to spark cross-disciplinary research:
* **Biblical Scholars**: Search for cross-verse structural echoes—identifying where entirely different books share an identical musical-emotional fingerprint.
* **Musicians & Vocalists**: Track the *tessitura* (pitch curves) of ancient poetry to understand how the music drop into quiet interludes or peaks into high-intensity caps (like the high `C` via the *mahpakh* accent).
* **Composers**: Leverage the raw MusicXML data as a foundational framework for modern arrangements and choral soundscapes derived directly from the canonical text.

---

## ✍️ Dive Deeper
* **Read the Commentary**: For deep thematic breakdowns, musicological analysis, and historical context, follow the ongoing publication journey at [Bob MacDonald’s Substack](https://substack.com).
* **Academic Reference**: This digital laboratory serves as the computational companion to the 18-volume print research corpus prepared for publication.
* **See also [Project Music Overview](./PROJECT-MUSIC-OVERVIEW.md).
