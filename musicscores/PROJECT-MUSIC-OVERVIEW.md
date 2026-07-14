# The Music of the Bible: A 20-Year Computational Musicology Project

A complete musical presentation of the full text of the Hebrew Bible, matching an 18-volume, 6,600-page print edition series published via Qualum Publishing.

## 🌟 Project Overview
This repository contains the digital assets, data structures, and raw musical scores resulting from a 20-year interdisciplinary study begun in St Andrews (2006) and Oxford (2010). The goal of this project is to decode, map, and examine the ancient embedded musical cantillation (*te'amim*) of the Hebrew Bible, translating the entire Masoretic corpus into a standardized, open-source musical timeline, based on the deciphereing key of Suzanne Haïk-Vantoura.

## 📂 Digital Assets & Repository Structure
This repository serves as an open-source baseline for developers, researchers, and musicologists to analyze melodic motifs or build automated audio playback engines.

*   **/Music Scores (.xml & .mscz):** 929 verified line-by-line verse scores for each chapter. The `.xml` files provide a fully exposed data tree for rapid processing by external scripts, while the `.mscz` files open directly in MuseScore.
*   **/JSON Data:** A condensed abbreviation map derived from a custom debug trace running on a local Oracle XE processing engine. Optimized for easy querying and automated structural sequence analysis.
*   **/Concordance Matrix:** Analytical links anchoring the musical data directly into the master concordance text layout.

## 🎼 The MusicXML Pipeline Approach
Unlike modern font renderers that try to visually resolve crowded diacritics, the engine behind these files parses the absolute **logical string order of Unicode characters**. 
*   **The Melismatic Reality:** Dual-accent syllables (such as combinations of true accents and phonetic helper tokens like *Meteg/Gaya*) are interpreted as intentional slurs and agogic elongations rather than sterile grammatical anomalies.
*   **The Unicode Challenge Resolved:** The database actively navigates structural quirks, such as the Unicode Consortium's assignment of a single code point (**U+05BD**) for both the phrase-ending *Siluq* and the phonetic *Meteg*, resolving them contextually by verse architecture.

## 🔗 Project Links & Publications
*   **Web Storefront & Concordance:** [SimHebrew Concordance Home](https://github.io)
*   **Analysis & Project History:** [Follow the Project on Substack](https://substack.com)
*   **Print Volumes:** *The Book of Job* (Jan 2026) and *The Psalms* (July 2026) are currently available through Qualum Publishing.

---
*© 2026 D. Robert MacDonald. Open-source data trees are provided for academic and non-commercial development use.*
</details>