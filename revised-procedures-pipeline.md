# Master Pipeline Procedures & Maintenance Runbook
**The Hebrew Bible Turned Upside Down / SimHebrew Concordance Project**  
*Author & Editor: D. Robert MacDonald*

---

## 🧭 System Overview & Architecture Tracks

The project comprises two parallel, interrelated production tracks governed by a unified musical and linguistic data model:

1. **Track 1: Print & Digital Publication Pipeline (Calibre & KDP)**
   - Produces the 18-volume print and electronic series *The Music of the Bible* and the complete *SimHebrew Bible*.
   - Master environments: Calibre Library (`C:\Users\Bob\Calibre Library\`), Kindle conversion workspace (`C:\Users\Bob\KindleProject\`), and iCloud distribution backups.
   - Core deliverable formats: High-resolution SVG-based print PDFs and image-optimized Kindle ePubs.

2. **Track 2: Web Concordance, Interactive Audio & Analytical Matrix Pipeline (GitHub)**
   - Powers the live web application at `https://stenagmois-byte.github.io/SimHebrew-Concordance/`.
   - Master environment: Local Git repository (`C:\Users\Bob\GitHub\SimHebrew-Concordance\`).
   - Core deliverable assets: 929 MuseScore (`.mscz`) scores, chapter and verse audio tracks (`.mp3`), interlinear data engines (`.json`), and analytical contour reduction matrices.

---

## 📖 Track 1: Publication Pipeline (Print PDFs & Kindle ePubs)

### 1. Master Source Formats & Hierarchy
* **Master Copy of Record:** The SVG-based ePub in the Calibre Library is the authoritative master.
* **Print PDFs:** Always generated directly from the SVG copy of the ePub.
  - *Single Volume:* Export directly from Calibre.
  - *Batch All Volumes:* Run the automated Python generation script against the ePub SVG files in `C:\Users\Bob\KindleProject\Input\`.
* **Kindle ePubs:** Amazon KDP requires PNG images rather than raw SVGs for fixed-layout fidelity.
  - Run `C:\Users\Bob\KindleProject\svgtopng.py` to convert vector music to PNG.
  - SVG ePubs remain up to 70% smaller, providing better page turns and lower delivery fees where supported.

### 2. Creating the SimHebrew Bible from Scratch
1. **Database Export:** Generate the 24 canonical text files from the Oracle database.
2. **Clean Container:** Open the target master ePub in Calibre and delete the body text of files 1–929.
3. **Import Files:** Import the 24 canonical files.
4. **Filename Sanitation:** Verify and rename any files containing spaces (strictly replace with hyphens or underscores).
5. **Heading & TOC Preparation:**
   - Ensure `<h4 class="chapter-head">` is correctly placed.
   - For single-book files, remove redundant initial heading h4.
   - For composite books containing multiple biblical texts, move the heading h4 after the internal book table of contents.
6. **File Splitting in Calibre:**
   - Right-click and split the file using XPath:
     ```xpath
     //h:h4[re:test(@class, "chapter-head", "i")]
     ```
7. **TOC & Metadata Maintenance:**
   - Rebuild the Table of Contents.
   - Move the `9x` series files to the bottom of the manifest.
   - Log the revision details in the copyright page comments for internal version tracking.

### 3. Updating Text Content in Existing Volumes of The Music of the Bible
1. Edit the master volume inside Calibre Editor.
2. Regenerate the print PDF directly from Calibre.
3. Copy the updated master ePub to `C:\Users\Bob\KindleProject\Input\`.
4. Run `python C:\Users\Bob\KindleProject\svgtopng.py`.
5. Execute the batch copy script in `C:\Users\Bob\KindleProject\Output\` to assemble the Kindle build.
6. Review output and synchronize to iCloud using Beyond Compare against the Calibre Library.

### 4. Adjusting Music Scores & Page Formatting for Print
All prose and poetic music must fit exactly within the printable line budget of the HTML containers. A breath mark or caesura change must never push a single orphaned note onto an overflow line.

1. **Pre-Flight Validation:**
   - Copy master ePub to `C:\Users\Bob\KindleProject\Input\`.
   - Run `check-epub-sequences.py` to audit for missing chapter images or misnumbered sequences.
   - Run `verify-epub-2.py` on the `.mscz` files to verify line feeds.
2. **Layout & Styling in MuseScore:**
   - Load the target score from `C:\Users\Bob\GitHub\SimHebrew-Concordance\musicscores\<Book>\`.
   - Apply the master style sheet: **Format → Load Style → `oneline.mss`** (enforces standardized staff width, margins, and line lengths).
   - **Slur Placement:** Select a slur, click *Select All Similar Elements*, and set placement to **Above**. Inspect high passages (especially near High C) and manually set conflicting slurs to **Below** to ensure lyrics and vowel points remain unobstructed.
   - **Manual Nudging:** For words pushed out of vertical alignment, select the element and nudge with the horizontal (X-axis) arrow keys until the vertical displacement drops into baseline position.
   - **Line Compression:** If a line overflows, compress measures via **Format → Stretch → Decrease Layout Stretch** (`Shift + {`). Alternatively, disable *Auto-placement* on problematic rests.
3. **Export & Injection:**
   - Export adjusted measures as SVG into the book's working directory.
   - Run the chapter batch files in `musicscores\<Book>\` to apply naming standardization.
   - Execute the automated injector:
     ```cmd
     cd C:\Users\Bob\GitHub\SimHebrew-Concordance\musicscores\analysis_scripts
     python stage-svg-injector.py
     ```
     *(Scans `KindleProject\Input\`, matches pending SVGs, and replaces old assets across ePubs in batch).*
4. **Final Verification & Backup:**
   - Inspect the modified ePub in Calibre.
   - Commit the updated `.mscz` files to GitHub Desktop.
   - Regenerate the Kindle PNG package (Steps 3–6 above).

### 5. Special Volume Procedures: The Book of Job
The Book of Job contains comparative performance demonstrations incorporating music from other volumes (e.g., Genesis 1–2, 2 Samuel 1, Isaiah 61:3).
* **Sign-Out Protocol:** When updating Job, copy the ePub to `KindleProject\Input\` as a formal checkout. Do not push intermediate stages to iCloud until cross-volume references are completely verified; maintain local thumb-drive backups during staging.
* **Cross-Volume SVG Renaming:**
  - When re-exporting scores like Isaiah 61:3 or 2 Samuel 1, copy the resulting SVGs to a safe staging directory *before* running batch scripts to prevent collision.
  - Replace legacy two-line score vestiges with updated single-line (`oneline.mss`) SVGs.
* **Spurious File Cleanup:** Delete any temporary or duplicate `.mscz` files created in the Job directory after cross-volume assets are reconciled.

---

## 🌐 Track 2: Web Site, Concordance & Master Data Architecture

### 1. Master Repository Directory Map
Root directory: `C:\Users\Bob\GitHub\SimHebrew-Concordance\`
* `bookseq.json`: Canonical ordering and sequential index for all 39 biblical books.
* `book_map.json`: Maps book prefixes (e.g. `1_SAMUEL`) to physical filesystem volume folders.
* `translation.json`: Textual translation repository and cantillation markers (`HAS_ATNAH`, `HAS_OLE`).
* `interlin.json`: Word-level interlinear alignments, grammatical keys, and lexical roots.
* `chapters/[Book]/[Book]_[Ch].json`: Decomposed chapter gloss arrays consumed by `menu.js`.
* `musicscores/[Volume]/[BOOK]_[CH].json`: 929 chapter-level score synchronization files.
* `musicscores/[Volume]/[BOOK]_[CH].mscz`: 929 master MuseScore notation archives.
* `musicscores/[Volume]/[BOOK]-[CH].mp3`: Rendered full-chapter audio performances.
* `musicscores/audio/[BOOK]/[Book]_[Ch]_[V].mp3`: Rendered individual verse audio tracks.
* `motif_relationship_matrix.json`: Cross-biblical cantillation motif and reduction registry.

### 2. Managing the Interlinear Engine (`interlin.json`)
The interactive gloss popup in `menu.js` (activated by double-click or text selection on matrix and cantillation pages) requires chapter-partitioned data:
1. Update `interlin.json` at the repository root.
2. Run the decomposition script:
   ```cmd
   python split_interlin-v2.py
   ```
   *(Slices the master array into individual chapter JSON files in `/chapters/<Book>/`).*

### 3. Translation Updates & Concordance Synchronization
When an English translation string or liturgical punctuation is revised (e.g., Ezekiel 16:49 pause `הִנֵּה־זֶ֣ה הָיָ֔ה`, Lamentations 1:1):
1. Update the master text in the ePub and recompile the PDF.
2. Re-export `translation.json` from the Oracle database.
3. Update the concordance script in the Oracle GX-LEAF Concord Form.
4. Run the form, move newly generated files from the Downloads folder to the concordance directory, and commit via GitHub Desktop.
5. Recalculate gematria concordances by running:
   ```cmd
   python C:\Users\Bob\Downloads\update_strict_concordance_gematria.py
   python find_verse_matches_json.py
   ```
   *(Note: Translation edits do not alter the musical notation files, as scores contain phonetic Hebrew lyrics only).*

### 4. Whole-Volume HTML Regeneration from Oracle
If all web HTML pages for a biblical volume require rebuilding:
1. Run `workfile.sql` in Oracle SQL Developer, filtering by canonical sequence range (e.g., Lamentations through Ecclesiastes, sequence 30–34):
   ```sql
   select 'OutputResultToFile("select xml_line1 xml_line1 from table (bsadmin.tlmdbook.tlmdbook('
   ||''''||''','''||book_cd||''','''||chapter_cd||''',''001'',''999'',1,''.svg'')) where xml_id in (''HTML'',''item-trans'',''Frame'') order by xml_seq","'
   ||initcap(replace(book_cd,' ','-'))||'-'||to_char(to_number(chapter_cd))||'.html");' from bs_chapters c where
   (select tnk_seq_no from books where book_cd = c.book_cd) between 30 and 34;
   ```
2. Paste the output statements into Script 5 of the Concord Form and execute.
3. Process raw downloads into target ePub/web structures using `replacehtml.py`.

---

## ⚡ Track 3: Surgical Maintenance Workflow (Music Scores, Audio & Matrices)

*Use this streamlined protocol when making small corrections to musical notes, accents, or inclusio cadences (e.g. correcting Psalm 8:10 cadential notes from E4 to A4).*

```
                     ┌─────────────────────────────┐
                     │  Correct Master Score .mscz │
                     │  (MuseScore 4 GUI / Studio) │
                     └──────────────┬──────────────┘
                                    │
           ┌────────────────────────┴────────────────────────┐
           ▼                                                 ▼
┌─────────────────────────────┐           ┌─────────────────────────────────────┐
│  Update Web Display JSON    │           │  Delete Target MP3s & Recompile     │
│  (Hand-edit SYLL_NOTE in    │           │  1. chapter_mp3s.py (Chapter audio) │
│  musicscores/.../[Ch].json) │           │  2. verse_mp3s.py   (Verse audio)   │
└─────────────────────────────┘           └──────────────────┬──────────────────┘
                                                             │
                                                             ▼
┌─────────────────────────────┐           ┌─────────────────────────────────────┐
│  Run Analytical Reductions  │           │  Git Deployment                     │
│  mass_produce_and_log_      │           │  • 1-2 verses: Commit directly      │
│  matrices.py (Reads .mscz)  │           │  • Bulk runs: Run reduce_bitrate.py │
└─────────────────────────────┘           └─────────────────────────────────────┘
```

### Step 1: Master Score Correction (`.mscz`)
1. Open the chapter score in MuseScore 4:  
   `musicscores/[Volume]/[BOOK]_[CH].mscz` (e.g., `musicscores/The Psalms/PSALMS_008.mscz`).
2. Correct the notes (e.g., change verse 10 E4 pitches to A4).
3. Save the `.mscz` file.  
   *(The `.mscz` archive is the master source for both audio compilation and matrix reduction).*

### Step 2: Web Display JSON Update (`[BOOK]_[CH].json`)
The 929 chapter JSON files (`musicscores/[Volume]/[BOOK]_[CH].json`) drive the browser's interactive SVG score and playback cursor.
* **Origin Note:** These files originated from an Oracle SQL simulation export (identifiable by `"type": "VARCHAR2"` / `"NUMBER"` headers). They are **not** generated by Python.
* **Surgical Update:** Open the target chapter JSON in a text editor and update the modified note directly:
  ```json
  "lyric_syll": "-retz", "syll_note": "A4"
  ```
  *(Saves having to re-run full database export jobs for minor corrections).*

### Step 3: Audio Compilation & Skip-Check Protocol
Both `chapter_mp3s.py` and `verse_mp3s.py` include skip-guards (`if mp3_out.exists(): continue`). They will silently skip any file that already exists on disk.

1. **Delete the Target Audio Files First:**
   - Chapter track: Delete `musicscores/[Volume]/[BOOK]-[CH].mp3`
   - Target verse track: Delete `musicscores/audio/[BOOK]/[Book]_[Ch]_[V].mp3` (e.g., `Psalms_8_10.mp3`).  
     *(Do NOT delete other verses in the chapter; the compiler will process only the missing file).*
2. **Compile Chapter Audio:**
   - Run:
     ```cmd
     python chapter_mp3s.py
     ```
   - Automatically unzips `.mscz`, injects agogic pauses (`atnah` = 2.0s, `zaqef_qatan` = 1.0s) into the score XML, and renders the chapter MP3 via headless MuseScore 4.
3. **Compile Verse Audio:**
   - **Environment Check:** Ensure line 12 of `verse_mp3s.py` points to your active Git repository (`C:\Users\Bob\GitHub\SimHebrew-Concordance`), not an archived OneDrive path.
   - Run:
     ```cmd
     python verse_mp3s.py
     ```
   - Slices measures across rests, isolates the missing verse, and renders the single verse MP3.
   - *(Note on Instrument Timbres: Production audio compilers output the default piano sound with structural pauses. Earlier experimental scripts utilized Choir Aahs GM Program 52 and downstream compression).*

### Step 4: Bitrate Management & Git Deployment
* **Surgical Fixes (1–2 Verses):** Uncompressed MP3 exports from MuseScore add minimal footprint (~1–2 MB combined). Commit them directly to GitHub without extra compression.
* **Bulk Re-renders:** When regenerating whole chapters or books, run:
  ```cmd
  python reduce_bitrate.py
  ```
  *(Compresses audio to 64–96 kbps joint-stereo for lightweight streaming).*

### Step 5: Contour Reduction & Matrix Synchronization
Run the reduction engine to refresh relationship matrices and HTML views:
```cmd
python mass_produce_and_log_matrices.py
```
* **Engine Behavior:** Reads directly from the updated `.mscz` notation files (it bypasses the chapter JSONs).
* **Outputs Updated:**
  - `motif_relationship_matrix.json` (updates motif occurrences, e.g. eliminating incorrect `E4,F#4,E4` resolutions).
  - 929 individual chapter contour pages (`[BOOK]_[CH]_matrix.html`).

---

## 📌 Appendix: Reference Tables & Data Contracts

### 1. Oracle JSON Payload Contracts

#### Master Interlinear (`interlin.json`):
```json
{"results":[{"columns":[
  {"name":"K","type":"VARCHAR2"},
  {"name":"H","type":"VARCHAR2"},
  {"name":"R","type":"VARCHAR2"},
  {"name":"E","type":"VARCHAR2"},
  {"name":"D","type":"VARCHAR2"}
],"items":[...]}]}
```
* `K`: Verse/Word key (`01_001_001_01`)
* `H`: Square Hebrew text
* `R`: Lexical root / SimHebrew key
* `E`: English gloss definition
* `D`: Semantic domain

#### Master Translation (`translation.json`):
```json
{"results":[{"columns":[
  {"name":"BOOK_CD","type":"VARCHAR2"},
  {"name":"BOOK_SEQ_NO","type":"NUMBER"},
  {"name":"CHAPTER_CD","type":"VARCHAR2"},
  {"name":"VERSE_CD","type":"VARCHAR2"},
  {"name":"POETRY","type":"VARCHAR2"},
  {"name":"HAS_ATNAH","type":"CHAR"},
  {"name":"HAS_OLE","type":"CHAR"},
  {"name":"ENG_TEXT","type":"VARCHAR2"}
],"items":[...]}]}
```

#### Chapter Music Score (`musicscores/[Volume]/[BOOK]_[CH].json`):
```json
{"results":[{"columns":[
  {"name":"BOOK_CD","type":"VARCHAR2"},
  {"name":"BOOK_SEQ_NO","type":"NUMBER"},
  {"name":"CHAPTER_CD","type":"VARCHAR2"},
  {"name":"VERSE_CD","type":"VARCHAR2"},
  {"name":"MEASURE_NO","type":"NUMBER"},
  {"name":"XML_SEQ","type":"NUMBER"},
  {"name":"LYRIC_SYLL","type":"VARCHAR2"},
  {"name":"SYLL_NOTE","type":"VARCHAR2"},
  {"name":"ORNAMENT_NAME","type":"VARCHAR2"},
  {"name":"ORNAMENT","type":"VARCHAR2"},
  {"name":"POETRY","type":"VARCHAR2"},
  {"name":"HEB_TEXT","type":"VARCHAR2"}
],"items":[...]}]}
```

### 2. Liturgical Punctuation & Performance Notes
* **Punctuation Governs Song:** English translation punctuation reflects liturgical and musical breath pauses dictated by the Hebrew accents.
* **Ezekiel 16:49:** The mid-phrase comma in *"Behold this was, the iniquity of Sodom..."* reflects the critical Zaqef-Qatan pause on `הִנֵּה־זֶ֣ה הָיָ֔ה`, demanding an intentional vocal caesura to summon listener attention.
* **Lamentations 1:1:** Punctuation preserves verse half-divisions dictated by Atnah cadences.
