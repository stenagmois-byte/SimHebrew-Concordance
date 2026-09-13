# Project Manifest: The Hebrew Bible Turned Upside Down (The Hebrew Bible as Music)

## 🌐 1. Digital Footprint & Architecture
* **Live Website URL:** https://stenagmois-byte.github.io/SimHebrew-Concordance/index.html
* **GitHub Repository:** Hosted via `stenagmois-byte.github.io` / `SimHebrew-Concordance`
* **Data Structure Profile:** Interdisciplinary 20-year project (St Andrews 2006, Oxford 2010) mapping Masoretic *te'amim* back to Second Temple musical structures.
* **Core Output Formats:** 929 `.mscz` (MuseScore) files, accompanying `.xml` files, and dynamic data engines like JSON directories.

## 📂 2. GitHub JSON & Assets Directory
* **Data Sources for Research:** GitHub repositories containing raw data mappings for parsing and structural tracking.
* **Volume/File Tracking Layout:**
  * `Music Scores` Directory - Holds the core scores and `.xml` formatted contours.
  * `manifest.json` / Configuration JSONs - Manage structural reading orders.
  * Volume Assets - 18-volume structure spanning 6,600 pages (e.g., Job, Psalms, The Five Scrolls).
* `translation.json` - Core file used across multiple pages for textual translations.
* `book_map.json` - Map configurations and base structural parameters for the books.
* `bookseq.json` - Controls the structural layout, sequencing, and book ordering.
* `interlin.json` - Core data driving the interlinear parallel text alignments.
* `motif_relationship_matrix.json` - Generated matrix asset (created by mass_produce_and_log_matrices.py).
* `ornament_chapters.json` - Indexing schema for specific cantillation attributes by chapter.
* `ornament_idex.json` - Indexing schema for specific structural musical ornaments.
* `musicscores/[Volume_Subdirectories]/[Book].json` - Individual book JSON arrays nested by volume to dynamically populate your colour-coded musical contour pages.

* **File Name:** `mass_produce_and_log_matrices.py`
  * **Role:** Automation engine responsible for mass-producing and logging the musical matrices.
  * **Outputs:** Generates the `motif_relationship_matrix.json` file and handles the processing workflow for the 929 individual volume-sorted music contour files.

## 🔄 3. Core "Upside Down" Assumptions & Rules
* **The "Upside Down" Paradigm:** Reversing, shifting, or re-evaluating traditional textual reading/structures to unlock the original embedded music.
* **Masoretic Te'amim Bridge:** Historical tracking back to the Second Temple of Jerusalem via the Elders of Bathyra.
* **Concordance of Contours:** Colour-coded data tracking visual and audio shapes in the musical contour of the Hebrew text.

## 🔢 4. Critical Hebrew & Schema Tables
* **SimHebrew Translation Key:** Mappings that translate canonical Hebrew characters into a programmatic schema (SimHebrew platform).
* **Musical Deciphering Key:** The algorithmic or structural rule sets that turn specific Hebrew characters/accents into direct musical notes, verses, or data fields.
