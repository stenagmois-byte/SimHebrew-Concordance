# Data and Script Catalog

First-pass inventory of the production, review, and working files in:

- `C:\Users\Bob\KindleProject`
- `C:\Users\Bob\Downloads`
- `C:\Users\Bob\GitHub\SimHebrew-Concordance`

Prepared 2026-11-21. This is a read-only inventory; no scripts were run and no source files were changed to produce it. Descriptions are based on the existing pipeline runbook, filenames, source docstrings, and function names. A filename or folder label is evidence of likely purpose, not proof that a file is safe to remove.

## Scope at a glance

| Location | Python files | JSON files | What the inventory shows |
|---|---:|---:|---|
| `KindleProject` | 19 | 0 | EPUB/PDF/SVG production and checking tools, including working copies in `Input` and `Output` |
| `Downloads` | 84 | 21 | 9 top-level scripts, 75 scripts under `history_analysis_scripts`, Oracle extracts, active translation-review files, and 2 legacy OpenSheetMusicDisplay metadata files |
| `SimHebrew-Concordance` | 144 | 1,869 | 21 root scripts, production copies, test/history folders, 3 video utilities; 11 root JSONs plus 929 interlinear chapter shards and 929 score-level JSONs |
| **Total physical files** | **247** | **1,890** | Files counted by location; byte-identical copies remain separate entries |

The repository's 1,869 JSON files divide into 11 root-level project datasets, 929 files under `chapters/`, and 929 score export JSONs under `musicscores/`. KindleProject currently has no JSON files. Downloads has 19 root-level JSONs plus 2 under `opensheetmusicdisplay/build/`.

## Status labels

- **Runbook production**: explicitly part of the documented workflow in `revised-procedures-pipeline.MD`.
- **Backup shelf**: stored in `developer-tools/Current_production_copies`; owner confirms these are intentional backups of GitHub copies and should be retained for convenient local recovery.
- **Review/support**: supports translation review, validation, or an occasional production check.
- **Archive/experiment**: located in a folder named history, tests, music tools, or contains a trial/debug/patch name. This does not by itself establish that the script is obsolete.
- **Unconfirmed**: needs owner/context review before use or cleanup.

## Production and review workflows identified

| Workflow | Python files | Inputs and outputs (from code/runbook) | Status |
|---|---|---|---|
| Interlinear decomposition | `split_interlin-v2.py` | Reads root `interlin.json` and `bookseq.json`; writes per-book/per-chapter JSONs under `chapters/`. | Runbook production |
| Master syllable decomposition | `split_master_syllables.py` | Reads `syllables_master.json`; writes chapter/volume score-level data used by ornament and score workflows. | Runbook production |
| Ornament index/page | `generate_ornament_pitch_table.py` | Reads JSON score exports under `musicscores/`; writes `ornament_chapters.json`, `ornament_index.json`, and `ornament_usage_by_pitch.html`. | Runbook production |
| Score contour matrices | `mass_produce_and_log_matrices.py` | Reads MuseScore `.mscz` files and book mapping; writes chapter matrix HTML and the motif relationship data. The runbook says it also runs reconciliation generation. | Runbook production |
| Reconciliation matrix | `generate_reconciliation_matrix.py` | Builds the reconciliation matrix view and occurrence data from score/contour inputs. | Runbook production |
| Translation punctuation review | `check_zaqef_atnah.py`, `check_zaqef_atnah-v2.py`, `punctuation_audit.py`, `punctuation_audit_v2.py`, `developer-tools/analysis-PY-history/find-z-q-errors.py` | For the database's word-level accent export (`k`, `h`, `atnah`, `z_q`, `e`, `lemma`, `e_t`), use `punctuation_audit_v2.py` for alignment-aware boundary review and compare its output with the preserved `punctuation_audit.py` baseline. Both emit a review report and candidate SQL; neither edits source or executes SQL. The `check_zaqef_atnah` variants instead take separate interlinear and translation files. `find-z-q-errors.py` reads `translation.json` and `ornament_index.json`. | Review/support; compare V2 before adoption |
| Concordance/gematria refresh | `update_strict_concordance_gematria.py` | Adds gematria to word concordance HTML generated from Oracle. Owner confirms this is the one critical production Python script in Downloads and remains in use because the Oracle alternative is inconvenient. | **Keep: active production** |
| Other verse-match/gematria tools | `find_verse_matches_json.py`, `create_verse_matches_json.py` | Build/search verse-match and gematria outputs. Their present use should be reviewed separately from the active HTML updater. | Unconfirmed/support |
| Audio compilation | `chapter_agogic_compiler.py`, `verse_agogic_compiler.py`, `reduce_bitrate.py`, `reduce_bitrate_chapters.py` | Compiles score audio and compresses chapter/audio outputs; compilers read `.mscz` and book mapping. | Runbook production |
| EPUB/print pipeline | See the KindleProject inventory below. | EPUB validation, SVG processing/injection, PNG conversion, EPUB comparison, PDF margin and packaging scripts. | Procedure-referenced or requires version choice |

#### Database punctuation review

Run from PowerShell in the repository root. `punctuation_audit_v2.py` accepts an `items` array (including the Oracle export fragment that begins with `"items":`) and writes a text review plus a candidate SQL sidecar. Keep `punctuation_audit.py` as the baseline when comparing a new audit version. Example for a Genesis-through-Samuel export:

```powershell
Set-Location C:\Users\Bob\GitHub\SimHebrew-Concordance
python .\punctuation_audit_v2.py `
  "C:\Users\Bob\Downloads\GenToSam.json" `
  "C:\Users\Bob\Downloads\GenToSam_punctuation_review.txt" `
  --checks-only `
  --sql-output "C:\Users\Bob\Downloads\GenToSam_candidate_updates.sql"
```

The text report lists only `CHECK`/`REVIEW` boundaries and retains their verse context. Treat each as a review prompt: accent boundaries do not determine English punctuation, and exact gloss matching can miss reordering or inflection. The SQL file is only a set of candidates; inspect it and the text report before considering any database update.

## Root-level project JSONs

| File | First-pass role / provenance | Likely consumer or regeneration path |
|---|---|---|
| `book_map.json` | Hand-maintained mapping from canonical book IDs to filesystem volume folders. | Score/audio/compiler scripts and the site. |
| `bookseq.json` | Canonical book ordering/sequence data. | Interlinear splitting and book ordering. |
| `gematria_verse_twins.json` | Generated or curated verse-match/gematria result set; exact producer not confirmed in this pass. | Verse-twin concordance page/scripts. |
| `hebrew_accent_dictionary.json` | Extendible accent metadata dictionary; includes mark codepoints, names, and descriptive/music fields. Some entries are interpretive/estimated. | `hebrew_accent_parser.js`, accent/ornament pages. |
| `interlin.json` | Oracle-origin master interlinear export (keys, Hebrew, root, English gloss, domain), as documented in the runbook. | `split_interlin-v2.py`, then `chapters/` shards and site UI. |
| `motif_relationship_matrix.json` | Generated analytical motif/reduction registry. | Motif/matrix pages; refreshed through the score reduction workflow. |
| `ornament_chapters.json` | Generated chapter-first ornament/pitch index. | `ornament_chapter.html`; regenerated by `generate_ornament_pitch_table.py`. |
| `ornament_index.json` | Generated ornament/pitch-to-verse lookup index. | `ornament_records.html`; regenerated by `generate_ornament_pitch_table.py`. |
| `reconciliation_occurrences.json` | Generated reconciliation occurrence data. | Reconciliation matrix/page workflow; producer relationship should be confirmed against the runbook/code. |
| `syllables_master.json` | Oracle-derived master syllable/recitation source, with manual corrections possible. | `split_master_syllables.py`, then score-level outputs. |
| `translation.json` | Oracle-origin verse translation and punctuation/poetry flags, per the runbook. | Concordance, ornament records, punctuation review, translation pages. |

## Downloads JSONs

The six `*_DATA_TABLE.json` files are Oracle-named extracts by filename. Their exact refresh SQL, encoding, and downstream use should be recorded when those workflows are reviewed:

| File | First-pass identification |
|---|---|
| `BOOKS_DATA_TABLE.json` | Oracle books table export. |
| `CHAPTERS_DATA_TABLE.json` | Oracle chapters table export. |
| `DGMKWD_DATA_TABLE.json` | Large Oracle keyword/word data export. |
| `DGMTEXT_DATA_TABLE.json` | Large Oracle text data export. |
| `RECITATIONS_DATA_TABLE.json` | Large Oracle recitation/syllable export; likely upstream of `syllables_master.json`. |
| `ROOTS_DATA_TABLE.json` | Oracle roots table export. |

Other top-level files are translation/punctuation working sets or variants by filename. The owner confirms that translation-review working files are critical and currently in use; retain them while their individual review roles are documented. Do not treat variant names or older timestamps as evidence that a review file is disposable:

`ezekielto_thetwelve2_commas.json`, `ezekieltomalachi_commas.json`, `fivescrolls2.json`, `fivescrolls_commas.json`, `Is_je__commas.json`, `joshua_judges_commas-2.json`, `joshua_judges_commas.json`, `num261.json`, `tnc.json`, `tnc_commas.json`, `tnc_commas1.json`, `torah2_commas.json`, `torah_commas.json`.

`opensheetmusicdisplay/build/osmd_block.json` and `pbdeeplink_block.json` are bundled metadata from a roughly two-year-old OpenSheetMusicDisplay site experiment, not Oracle project datasets. The owner considers this display approach obsolete: it creates a visual conflict with the books and would involve roughly 34,000 score images for about 23,000 verses. Mark these as **obsolete legacy artifacts / removal candidates**, but do not remove them as part of this documentation pass.

## Python inventory

The list below is exhaustive for the three requested folders as scanned on 2026-11-21. The first-pass purpose is taken from a docstring when present, otherwise from the filename and top-level function names. **Exact duplicate** means byte-identical at scan time; it is a cleanup lead, not a removal instruction. See the status and duplicate notes after the inventory.

### KindleProject (19 files)

| File | First-pass purpose | Status |
|---|---|---|
| `Check_epub_sequences.py` | Checks EPUB sequence/order and missing chapter assets. | Procedure-referenced |
| `check_word_alignment.py` | Scans score/EPUB word alignment and caesura collisions. | Validation/support |
| `epubcompare.py` | Compares verse text between EPUBs and writes comparison output. | Procedure-referenced |
| `extract_manifest_svgs.py` | Reads EPUB manifest/SVG names and writes SQL update statements. | Production support |
| `extract_svgs.py` | Exports SVG from MuseScore files. | Production support; exact active copy to verify |
| `modify_pdf_gutter.py` | Adjusts/mirrors PDF book margins. | Production support |
| `pdf-complex.py` | Generates custom paperback PDFs from EPUB inputs. | Exact duplicate in several folders; version choice needed |
| `pdf-temp.py` | Alternate/custom paperback PDF generator. | Exact duplicate of repository `developer-tools/pdf-temp.py`; version choice needed |
| `production_audit.py` | Audits EPUB production assets. | Exact duplicate in archive copies |
| `replace_simhebrew_html.py` | Splits canonical SimHebrew HTML and can update EPUB entries. | Production workflow candidate; document invocation and target paths |
| `replacehtml.py` | Synchronizes HTML/heading content into EPUBs. | Procedure-referenced |
| `stage-svg-injector-3.py` | Stages and injects SVG assets into EPUBs. | Procedure-referenced version; exact duplicate copies exist |
| `svgtopng-dupcss-error.py` | Experimental/alternate SVG-to-PNG EPUB converter. | Error/variant copy; compare before cleanup |
| `svgtopng.py` | Converts SVG assets to PNG and packages EPUB. | Procedure-referenced; exact duplicate copies exist |
| `validate_svgs.py` | Audits SVG/cadence integrity in EPUBs. | Validation/support; exact duplicate copies exist |
| `verify_epub-2.py` | Verifies EPUB score/lyric sequences. | Versioned validation tool; compare with `verify_epub.py` |
| `verify_epub.py` | Verifies EPUB score/lyric sequences. | Validation support; exact duplicate repository copy exists |
| `Input\h2h3h4update_css.py` | Updates EPUB header/CSS content. | Working-input utility; inspect target behavior before reuse |
| `Output\deduplicate_epub_css.py` | Deduplicates CSS inside EPUBs. | Output-stage utility |

### Downloads (84 files)

#### Top-level Downloads scripts (9)

| File | First-pass purpose | Status |
|---|---|---|
| `analyse_chapter.py` | Analyzes one Oracle JSON chapter and reports syllable/ornament patterns. | Working analysis; exact duplicate under `history_analysis_scripts/` differs, compare |
| `analyse_isa_40.py` | Focused analysis of Isaiah 40 Oracle JSON. | One-off analysis candidate |
| `analyse_job.py` | Inspects Job score/EPUB XML structure. | Exact duplicate in repository Test-Scripts |
| `analyse_tanach.py` | Analyzes complete Tanach JSON data and writes a report. | One-off analysis candidate |
| `detail_chapter.py` | Detailed analysis report for a selected JSON chapter. | One-off analysis candidate |
| `drone_trial.py` | MuseScore drone/arrangement trial. | Music experiment |
| `job-pitch.py` | Small `music21` pitch experiment. | Exact duplicate in repository Test-Scripts |
| `split_chapters.py` | Splits a JSON dataset into book/chapter pieces. | Working utility; source/output contract needs confirmation |
| `update_strict_concordance_gematria.py` | Updates gematria annotations in concordance HTML. | Exact duplicate at repository root and production-copy folder |

#### `Downloads\history_analysis_scripts` (75)

Folder contains retained working/history scripts. Some files may support the owner's active translation review; the folder name alone does not make them obsolete. `update_strict_concordance_gematria.py` in Downloads root is confirmed as the active production script. Other Downloads scripts remain **owner-review required** until their relationship to active review work is clear. Individual candidate-purpose signals:

`analyse-strophes.py` (strophe-shape analysis); `analyse_chapter.py` (chapter/passage analysis); `analyse_e-major-motif.py` (E-major motif scan); `analyse_job.py` (Job score analysis); `analyse_tanach-bob.py` (Tanach analysis); `analyze_motifs.py` (motif extraction); `append-musicstats.py` (extracts/records score statistics); `apply_breath_patch.py` (patches breath/word-end notes); `book_map_test.py` (tests book-map resolution); `chapter_mp3s.py` (chapter audio compilation variant); `chapter_refrains.py` (refrain extraction); `checksvgs.py`, `checksvgsall.py` (SVG dimension checks); `compare_systems.py` (compares MusicXML melody systems); `compare96-1chr16.py` (ornament comparison); `compile_sequence_log.py` (builds a sequence/cadence log); `debug_Obadiah-1.py`, `debug_Obadiah.py` (Obadiah-specific diagnostics); `discovery_engine.py` (passage discovery); `drone_trial-2.py`, `drone_trial-3.py`, `drone_trial.py` (audio/MuseScore experiments); `explore_genesis.py`, `explore_psalms-78.py`, `explore_pulses-bookch.py` (book/chapter investigations; `explore_pulses-bookch.py` currently has a Python syntax error); `extract_svgs.py` (MuseScore SVG export); `filecompare.py` (EPUB workspace size comparison); `Finalscan-lostconv.py` (lost-conversion diagnostic); `Find_rare_verses.py` (rare verse identification); `find_verse_matches_json.py` (verse/gematria match page); `find-z-q-errors.py` (read-only zaqef punctuation review queue; writes reports); `fix_css_paths.py`, `fix_css_scope.py` (targeted CSS repairs); `fixisaiahmargins.py` (Isaiah EPUB margin repair); `generate_book_indices.py` (HTML book indices); `generate_melodic_matrix-A.py` (melodic matrix generation variant); `generate_ornament_pitch_table.py` (ornament/pitch report generation variant); `generate_ornament_with_extras.py` (ornament records page variant); `generate_reconciliation_matrix.py` (reconciliation page generation); `global_source_repair.py` (global source text repair); `inspect_musescore_structure.py` (MSCZ internal XML inspector); `job-pitch.py` (pitch experiment); `json_validation.py` (JSON validator); `jsonl.py` (small JSONL helper); `list-notebook.py` (notebook/file listing helper); `mass_produce_and_log_matrices.py`, `mass_produce_matrices.py` (contour/matrix generation versions); `motif-concordance-e-g-b-1.py`, `motif-concordance.py` (motif scans); `mp3_test.py`, `trial_mp3.py` (audio trials); `ornament_comparison.py` (ornament comparison); `patch_highlights.py` (patches HTML highlighting); `patch_obadiah.py` (Obadiah-specific score patch); `pdf.py` (PDF generator); `peek_xml.py` (XML inspection); `production_audit.py` (EPUB audit); `remove_json_links.py` (HTML link removal); `scan_for_missing_breath.py` (breath-placement diagnostic); `simulation.py` (small simulation); `split_by_verse.py` (splits MuseScore by verse); `stage-svg-injector.py`, `stage-svg-injector-2.py`, `stage-svg-injector-3.py` (SVG injection iterations); `suite_of_functions.py` (analysis helpers); `svgtopng.py` (SVG-to-PNG EPUB conversion); `test-directory.py`, `test_split_by_verse.py`, `test_verse_mp3s.py` (test helpers); `update_strict_concordance_gematria-v1.py`, `update_strict_concordance_gematria.py` (gematria updater versions); `validate_svgs.py` (SVG audit); `verify_epub.py` (EPUB verification); `verifymargins.py` (margin/viewBox audit); `verse_mp3s.py` (verse audio compiler).

### SimHebrew-Concordance (144 files)

#### Repository root (21)

| File | First-pass purpose | Status |
|---|---|---|
| `analyse_psalms_guilds.py` | Analyzes score cohorts/guilds in Psalms. | Analysis/support |
| `batch_git_push.py` | Runs a scripted Git command sequence. | Operational; inspect exact branches/files before use |
| `batch_git_push_volumes.py` | Batch Git operations by volume using `book_map.json`. | Operational; inspect exact branches/files before use |
| `chapter_agogic_compiler.py` | Compiles chapter audio with agogic/ornament handling. | Runbook production |
| `check_zaqef_atnah.py` | Audits translation punctuation against accent boundaries. | Review/support; compare with `-v2` |
| `check_zaqef_atnah-v2.py` | Updated audit variant for zaqef/atnah punctuation. | Review/support; version choice needed |
| `create_verse_matches_json.py` | Builds verse-match/gematria concordance output. | Production/support; exact output files to confirm |
| `find_verse_matches_json.py` | Builds/searches verse-match/gematria output. | Exact duplicate root-history copy; confirm relationship to `create_...` |
| `generate_book_indices.py` | Generates book index pages from chapter data. | Production/support |
| `generate_ornament_pitch_table.py` | Generates ornament pitch HTML plus chapter and occurrence JSON indexes. | Runbook production |
| `generate_reconciliation_matrix.py` | Generates reconciliation matrix/occurrence output. | Runbook production |
| `json_validation.py` | Validates concordance JSON. | Validation/support |
| `mass_produce_and_log_matrices.py` | Generates chapter contour/motif matrix views from score files. | Runbook production |
| `punctuation_audit.py` | Creates conservative punctuation-review reports without editing source. | Translation review support |
| `punctuation_audit_v2.py` | Alignment-aware review variant that checks reordered phrase boundaries and atnah line placement; keeps the same report/SQL format for comparison. | Review against `punctuation_audit.py` before adoption |
| `reduce_bitrate.py` | Compresses audio output. | Runbook production |
| `reduce_bitrate_chapters.py` | Compresses chapter audio output. | Runbook production |
| `split_interlin-v2.py` | Splits `interlin.json` into `/chapters/` shards. | Runbook production |
| `split_master_syllables.py` | Splits master syllable data into score-level chapter data. | Runbook production |
| `update_strict_concordance_gematria.py` | Injects gematria data into concordance HTML. | Keep: owner-confirmed active production |
| `verse_agogic_compiler.py` | Compiles individual verse audio. | Runbook production |
| `video_maker.py` | Builds video output from EPUB imagery and audio. | Production/support; separate media workflow |

#### `developer-tools\Current_production_copies` (20)

Intentional local backup shelf of current-use scripts. The hash scan found all 20 byte-identical to root counterparts. The owner confirms this redundancy is useful because GitHub is not always the most convenient backup source. **Keep this shelf; do not flag these copies for cleanup.**

`batch_git_push.py`, `batch_git_push_volumes.py`, `chapter_agogic_compiler.py`, `check_zaqef_atnah.py`, `check_zaqef_atnah-v2.py`, `create_verse_matches_json.py`, `find_verse_matches_json.py`, `generate_book_indices.py`, `generate_ornament_pitch_table.py`, `generate_reconciliation_matrix.py`, `json_validation.py`, `mass_produce_and_log_matrices.py`, `punctuation_audit.py`, `reduce_bitrate.py`, `reduce_bitrate_chapters.py`, `split_interlin-v2.py`, `split_master_syllables.py`, `update_strict_concordance_gematria.py`, `verse_agogic_compiler.py`, `video_maker.py`.

#### `developer-tools\analysis-PY-history` (42)

Historical/analysis scripts, not part of the documented main pipeline unless separately noted above:

`analyze_motifs.py`, `apply_breath_patch.py`, `chapter_mp3s.py`, `check_json_names.py`, `check_text_alignment.py`, `compact_json_data.py`, `compare_systems.py`, `decode_html_entities.py`, `drone_trial.py`, `explore_psalms-78.py`, `extract_svgs.py`, `find-z-q-errors.py`, `global_linear_patch_engine.py`, `global_mscz_patch_engine.py`, `inject_script.py`, `inspect_genesis.py`, `jsonl.py`, `list-notebook.py`, `motif-concordance.py`, `ornament_comparison.py`, `patch_obadiah.py`, `pdf.py`, `peek_xml.py`, `probe_svg.py`, `production_audit.py`, `scan_for_missing_breath.py`, `schema_dump.py`, `stage-svg-injector-3.py`, `svgtopng.py`, `test1.py`, `testmusic21.py`, `testvalue.py`, `trace_mscz.py`, `trace_mscz2.py`, `trace_syntax.py`, `update_strict_concordance_gematria-v1.py`, `validate_svgs.py`, `verify_epub.py`, `verify_hebrew-text-alignment.py`, `verify_rest.py`, `verify_upper_hebrew.py`, `verse_mp3s.py`.

#### `developer-tools\Test-Scripts` (33)

Test/experiment folder; exact duplicate copies of many Downloads scripts occur here:

`analyse-strophes.py`, `analyse_chapter.py`, `analyse_e-major-motif.py`, `analyse_job.py`, `analyse_tanach-bob.py`, `append-musicstats.py`, `book_map_test.py`, `chapter_refrains.py`, `compare96-1chr16.py`, `compile_sequence_log.py`, `discovery_engine.py`, `explore_pulses-bookch.py`, `Find_rare_verses.py`, `fix_css_paths.py`, `fix_css_scope.py`, `generate_melodic_matrix-A.py`, `generate_ornament_with_extras.py`, `global_source_repair.py`, `inspect_musescore_structure.py`, `job-pitch.py`, `mass_produce_matrices.py`, `motif-concordance-e-g-b-1.py`, `motif-concordance.py`, `mp3_test.py`, `patch_highlights.py`, `remove_json_links.py`, `simulation.py`, `split_by_verse.py`, `suite_of_functions.py`, `test-directory.py`, `test_split_by_verse.py`, `test_verse_mp3s.py`, `trial_mp3.py`.

#### Other repository tools (28)

- `developer-tools\Check_epub_sequences.py`, `developer-tools\check_word_alignment.py`, `developer-tools\epubcompare.py`, `developer-tools\extract_manifest_svgs.py`, `developer-tools\extract_svgs.py`, `developer-tools\fix_epub_paragraph_structure.py`, `developer-tools\modify_pdf_gutter.py`, `developer-tools\pdf-complex.py`, `developer-tools\pdf-temp.py`, `developer-tools\production_audit.py`, `developer-tools\replacehtml.py`, `developer-tools\stage-svg-injector-3.py`, `developer-tools\svgtopng-dupcss-error.py`, `developer-tools\svgtopng.py`, `developer-tools\validate_svgs.py`, `developer-tools\verify_epub-2.py`, `developer-tools\verify_epub.py`: EPUB/PDF/SVG production and checking utilities; some are exact copies of KindleProject or root scripts.
- `developer-tools\PYforProduction-tests\checksvgs.py`, `checksvgsall.py`, `filecompare.py`, `fixisaiahmargins.py`, `pdf.py`, `verifymargins.py`: production-adjacent checks/repairs retained in a test-named folder.
- `developer-tools\music-tools\drone_trial-2.py`, `drone_trial-3.py`: MuseScore/audio experiments.
- `VideoPlus\build_directory.py`, `generate_html.py`, `trimvideo.py`: build video directory metadata, HTML listing, and trim video/audio.

## Exact duplicate-content findings

The 247 files contain 138 distinct byte contents: **87 byte-identical groups account for 109 extra copies**. Many repeated copies live in `Downloads\history_analysis_scripts`, `developer-tools\analysis-PY-history`, or `developer-tools\Test-Scripts`. Exact duplication is useful cleanup evidence for those locations, but a duplicate's location can still matter if a procedure invokes that exact path. Before removal, search runbooks, batch files, shortcuts, and current commands for the path. `developer-tools\Current_production_copies` is explicitly retained as the owner's backup shelf, not a cleanup target.

High-priority duplicate families to review first:

- `svgtopng.py`, `stage-svg-injector-3.py`, `extract_svgs.py`, `validate_svgs.py`, `production_audit.py`, and EPUB verification/PDF scripts have copies across KindleProject, Downloads, and the repository.
- Several root production files have byte-identical copies under `developer-tools\Current_production_copies`.
- Gematria updater and verse-match scripts have copies in Downloads/history and repository locations.
- Many Test-Scripts and history files are byte-identical to Downloads/history copies.

## Cleanup guidance

This catalog does not designate files for deletion. The safest next review is to confirm the exact invocation path for runbook production scripts, then decide which duplicate copy is canonical. Keep the Downloads gematria updater and the owner's active translation-review scripts/data together. Do not infer that a Downloads file is inactive from its location. Record the chosen canonical location before removing duplicate copies.

## Follow-up items

1. Confirm exact Oracle SQL/export steps and owners for each Downloads `*_DATA_TABLE.json` and punctuation working set.
2. Keep `developer-tools\Current_production_copies` as the intentional backup shelf; document when a workflow uses a particular copy path.
3. Review version pairs (`check_zaqef_atnah.py`/`-v2`, `verify_epub.py`/`-2`, `svgtopng.py`/`svgtopng-dupcss-error.py`, SVG injector revisions) and mark the chosen version.
4. Inspect unconfirmed small utilities (`jsonl.py`, `list-notebook.py`, `test-directory.py`, `num261.json`) with their owner/context before cleanup.
