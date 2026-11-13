/**
 * Hebrew Accent Parser -- supports ornament_records.html
 * Project: SimHebrew Concordance / The Hebrew Bible as Music 
 * assisted by AI -- somewhat randomly
 */

(function(global) {
    'use strict';

    const CANONICAL_BOOKS = [
        "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy",
        "Joshua", "Judges", "1 Samuel", "2 Samuel", "1 Kings", "2 Kings",
        "Isaiah", "Jeremiah", "Ezekiel", "Hosea", "Joel", "Amos", "Obadiah",
        "Jonah", "Micah", "Nahum", "Habakkuk", "Zephaniah", "Haggai",
        "Zechariah", "Malachi", "Psalms", "Proverbs", "Job", "Song",
        "Ruth", "Lamentations", "Qohelet", "Esther", "Daniel", "Ezra",
        "Nehemiah", "1 Chronicles", "2 Chronicles"
    ];

const PITCH_NAMES = {
        "c": "darga",
        "d": "tevir/galgal",
        "e": "silluq",
        "f": "mercha",
        "g": "tifha/d'khi",
        "A": "atnah",
        "B": "munach",
        "C": "mahpach/yetiv"
    };

    class HebrewAccentParser {
        constructor() {
            this.dictionary = {};
            this.translations = {};
            this.byDecimal = new Map();
            this.byHex = new Map();
            this.bySlug = new Map();
            this.byHebrew = new Map();
            this.isLoaded = false;
        }

        async init(dataOrUrl = './hebrew_accent_dictionary.json') {
            if (typeof dataOrUrl === 'string') {
                try {
                    const response = await fetch(dataOrUrl);
                    this.dictionary = await response.json();
                } catch (err) {
                    console.error('Failed to load accent dictionary:', err);
                }
            } else if (typeof dataOrUrl === 'object' && dataOrUrl !== null) {
                this.dictionary = dataOrUrl;
            }

            try {
                const transResp = await fetch('./translation.json');
                if (transResp.ok) {
                    const rawTrans = await transResp.json();
                    this._buildTranslationMap(rawTrans);
                }
            } catch(e) {
                this.translations = {};
            }

            this._buildIndexes();
            this.isLoaded = true;
            return true;
        }

        _buildTranslationMap(rawTrans) {
            this.translations = {};
            if (!rawTrans) return;

            const items = Array.isArray(rawTrans) ? rawTrans : (rawTrans.results?.[0]?.items || rawTrans.items || []);

            items.forEach(item => {
                const rawBook = String(item.book_cd || item.BOOK_CD || item.b || '').replace(/_/g, ' ').trim();
                if (!rawBook) return;

                const titleBook = rawBook.split(/\s+/)
                    .map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
                    .join(' ');
                
                const underscoreTitle = titleBook.replace(/\s+/g, '_');
                const underscoreRaw = rawBook.replace(/\s+/g, '_');

                const ch = String(item.chapter_cd || item.CHAPTER_CD || item.c || '').replace(/^0+/, '');
                const v = String(item.verse_cd || item.VERSE_CD || item.v || '').replace(/^0+/, '');
                const text = item.eng_text || item.ENG_TEXT || item.text || item.t || '';

                if (ch && v && text) {
                    this.translations[`${titleBook}_${ch}_${v}`] = text;
                    this.translations[`${underscoreTitle}_${ch}_${v}`] = text;
                    this.translations[`${rawBook}_${ch}_${v}`] = text;
                    this.translations[`${underscoreRaw}_${ch}_${v}`] = text;
                    this.translations[`${titleBook}|${ch}|${v}`] = text;
                    this.translations[`${titleBook} ${ch}:${v}`] = text;
                }
            });
        }

        _buildIndexes() {
            this.byDecimal.clear();
            this.byHex.clear();
            this.bySlug.clear();
            this.byHebrew.clear();

            for (const [key, entry] of Object.entries(this.dictionary)) {
                const hexNormalized = String(entry.hex || '').toUpperCase();
                const hexRaw = String(entry.hex_raw || '').toUpperCase();
                if (hexNormalized) this.byHex.set(hexNormalized, entry);
                if (hexRaw) this.byHex.set(hexRaw, entry);

                if (entry.decimal !== undefined) {
                    this.byDecimal.set(String(entry.decimal), entry);
                    if (typeof entry.decimal === 'number') {
                        this.byDecimal.set(entry.decimal, entry);
                    }
                }

                if (entry.name_translit) {
                    const slug = this._normalizeSlug(entry.name_translit);
                    this.bySlug.set(slug, entry);
                }

                if (entry.name_hebrew) {
                    this.byHebrew.set(entry.name_hebrew.trim(), entry);
                    const unpointed = entry.name_hebrew.replace(/[\u0591-\u05C7]/g, '').trim();
                    if (unpointed) this.byHebrew.set(unpointed, entry);
                }
            }
        }

        _normalizeSlug(str) {
            return String(str).toLowerCase().replace(/[^a-z0-9]/g, '');
        }

        getByDecimal(dec) {
            return this.byDecimal.get(String(dec)) || this.byDecimal.get(Number(dec)) || null;
        }

        getByHex(hex) {
            let formatted = String(hex).toUpperCase().trim();
            if (!formatted.startsWith('U+')) {
                formatted = 'U+' + formatted.padStart(4, '0');
            }
            return this.byHex.get(formatted) || this.byHex.get(formatted.replace('U+', '')) || null;
        }

        getByName(name) {
            if (!name) return null;
            const slug = this._normalizeSlug(name);
            return this.bySlug.get(slug) || null;
        }

        parseVerseText(text) {
            if (!text || typeof text !== 'string') return [];
            const results = [];
            for (let i = 0; i < text.length; i++) {
                const char = text[i];
                const dec = char.codePointAt(0);
                const accent = this.getByDecimal(dec);
                if (accent) {
                    results.push({
                        char: char,
                        decimal: dec,
                        hex: accent.hex,
                        nameHebrew: accent.name_hebrew,
                        nameTranslit: accent.name_translit,
                        category: accent.category,
                        pitchOrInterval: accent.pitch_or_interval,
                        symbolOnAleph: accent.symbol_on_aleph
                    });
                }
            }
            return results;
        }

        /**
         * Render Ornament Records (ornament_records.html)
         */
        renderOrnamentRecords(containerSelector, indexData, targetOrn, targetPitch) {
            const container = typeof containerSelector === 'string' ? document.querySelector(containerSelector) : containerSelector;
            if (!container) return;
            const pitchHebrewName = PITCH_NAMES[targetPitch] || targetPitch;
            const accent = this.getByName(targetOrn);
/*            const displayName = accent ? accent.name_translit : (targetOrn ? targetOrn.charAt(0).toUpperCase() + targetOrn.slice(1) : 'Ornament');
*/
            const ornKey = this._normalizeSlug(targetOrn || '');
            const pitchKey = String(targetPitch || '').trim();

            // Find matching entries in indexData
            let rawRecords = [];
            if (indexData) {
                for (const [oKey, pitchMap] of Object.entries(indexData)) {
                    if (this._normalizeSlug(oKey) === ornKey) {
                        for (const [pKey, list] of Object.entries(pitchMap)) {
                            if (pKey.toLowerCase() === pitchKey.toLowerCase()) {
                                rawRecords = list;
                                break;
                            }
                        }
                    }
                }
            }

            // Deduplicate records by verse
            const seenVerses = new Set();
            const allRecords = rawRecords.filter(r => {
                const vKey = `${r.b}_${r.c}_${r.v}`;
                if (seenVerses.has(vKey)) return false;
                seenVerses.add(vKey);
                return true;
            });

            if (allRecords.length === 0) {
                container.innerHTML = `
                    <div style="padding: 30px; background: #fff; border: 1px solid #e2ddd0; border-radius: 6px; font-family: sans-serif;">
                        <h3 style="color: #800000; margin-top:0;">No Records Found</h3>
                        <p>No occurrences found for ornament <strong>${targetOrn || '—'}</strong> on reciting pitch <strong>${targetPitch || '—'}</strong>.</p>
                    </div>`;
                return;
            }

            // Find target ornament codepoints/symbols for word-level highlighting
            const accentEntry = this.getByName(targetOrn);
            const targetSymbols = [];
            const targetDecimals = [];
            if (accentEntry) {
                if (accentEntry.symbol) targetSymbols.push(accentEntry.symbol);
                if (accentEntry.decimal) targetDecimals.push(Number(accentEntry.decimal));
            }

            // Group records by Book & count
            const bookCounts = {};
            allRecords.forEach(r => {
                bookCounts[r.b] = (bookCounts[r.b] || 0) + 1;
            });
            //const bookNames = Object.keys(bookCounts);
// 1. Extract unique books present in allRecords
            const uniqueBooksSet = new Set(allRecords.map(r => r.b ? r.b.trim() : ''));

// 2. YOUR RESTORED CANONICAL SORTING LOGIC
           const availableBooks = [];
           CANONICAL_BOOKS.forEach(b => {
              if (uniqueBooksSet.has(b)) availableBooks.push(b);
           });
           uniqueBooksSet.forEach(b => {
              if (!availableBooks.includes(b)) availableBooks.push(b);
           });

// 3. YOUR RESTORED DEFAULT BOOK SELECTION LOGIC
           const urlParams = new URLSearchParams(window.location.search);
           const urlBookParam = urlParams.get('book');

           let defaultBook = 'ALL';
               if (urlBookParam && availableBooks.includes(urlBookParam)) {
                   defaultBook = urlBookParam;
               } else if (availableBooks.length > 0) {
                   defaultBook = availableBooks[0]; // Defaults to Genesis (or first canonical)
               }

// 4. SUTURE VARIABLE NAMES FOR YOUR HTML TEMPLATE
          const bookNames = availableBooks;
          const selectedBook = defaultBook;

// 5. FILTER THE RECORDS FOR RENDERING
          const filteredRecords = selectedBook === 'ALL' 
            ? allRecords 
            : allRecords.filter(r => r.b && r.b.trim() === selectedBook);
            // AUTO-SELECT FIRST CANONICAL BOOK WITH RECORDS (Prevents browser freeze on 13,000 records)
            //let selectedBook = bookNames.length > 0 ? bookNames[0] : 'ALL';

            const self = this;

            function getAudioUrl(rawBookCode, chNum, vsNum) {
                if (!rawBookCode) return '';

                   const folderName = String(rawBookCode).trim().replace(/_/g, ' ').toUpperCase();
                   const properBook = folderName.toLowerCase().split(/\s+/).map(w => w.charAt(0).toUpperCase() + w.slice(1)).join('_');
                   const c = String(chNum).replace(/^0+/, '') || '1';
                   const v = String(vsNum).replace(/^0+/, '') || '1';
                   const audioFileName = `${properBook}_${c}_${v}.mp3`;

                   return `./musicscores/audio/${encodeURIComponent(folderName)}/${audioFileName}`;
}
            function renderView() {
                const filteredRecords = selectedBook === 'ALL' 
                    ? allRecords 
                    : allRecords.filter(r => r.b === selectedBook);

                let htmlStr = `
                <div class="ornament-records-view">
                    <div class="filter-bar" style="margin-bottom: 20px; padding: 15px 20px; background: #f9f6f0; border: 1px solid #e2ddd0; border-radius: 6px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px;">
                        <div>
                            <h2 style="font-family: sans-serif; color: #800000; margin: 0 0 4px 0; font-size: 1.4rem;">
                                ${targetOrn} on recitation pitch: ${targetPitch} (${pitchHebrewName})
                            </h2>
                            <span style="font-size: 0.88rem; color: #666;">
                                Showing ${filteredRecords.length} of ${allRecords.length} records (Total: ${allRecords.length})
                            </span>
                        </div>
                        
                        <div style="display: flex; align-items: center; gap: 15px; flex-wrap: wrap;">
                            <div style="display: flex; align-items: center; gap: 10px; font-family: sans-serif; font-size: 0.85rem; color: #444;">
                                <label style="cursor: pointer; display: flex; align-items: center; gap: 4px;">
                                    <input type="checkbox" id="toggle-vowels"> Show vowel points (niqqud)
                                </label>
                                <label style="cursor: pointer; display: flex; align-items: center; gap: 4px;">
                                    <input type="checkbox" id="toggle-ext-desc"> Show extended description
                                </label>
                            </div>

                            <div style="display: flex; align-items: center; gap: 8px; font-family: sans-serif; font-size: 0.9rem;">
                                <label for="book-filter-select" style="font-weight: bold; color: #800000;">Filter by Book:</label>
                                <select id="book-filter-select" style="padding: 5px 10px; border-radius: 4px; border: 1px solid #c8c0b0; font-family: sans-serif; background: #fff; cursor: pointer;">
                                    <option value="ALL" ${selectedBook === 'ALL' ? 'selected' : ''}>All Books (${allRecords.length})</option>
                                    ${bookNames.map(b => `<option value="${b}" ${b === selectedBook ? 'selected' : ''}>${b} (${bookCounts[b]})</option>`).join('')}
                                </select>
                            </div>
                        </div>
                    </div>

                    <div class="records-cards-container">
                `;

                filteredRecords.forEach(rec => {
                    const verseKey = `${rec.b}_${rec.c}_${rec.v}`;
                    const transText = self.translations[verseKey] || self.translations[`${rec.b}|${rec.c}|${rec.v}`] || self.translations[`${rec.b} ${rec.c}:${rec.v}`] || '';
                    
                    const rawText = rec.t || '';
                    const strippedText = rawText.replace(/[\u05B0-\u05BC\u05BF\u05C1\u05C2\u05C4\u05C5\u05C7]/g, '');

                    // Highlight target words
                    function highlightWords(txt) {
                        if (!txt) return '';
                        if (targetSymbols.length === 0 && targetDecimals.length === 0) return txt;
                        
                        return txt.split(/\s+/).map(w => {
                            const hasSym = targetSymbols.some(s => s && w.includes(s));
                            const hasDec = targetDecimals.some(d => Array.from(w).some(c => c.codePointAt(0) === d));
                            if (hasSym || hasDec) {
                                return `<span class="highlight-word" style="background-color: #fff2cc; border-bottom: 2px dashed #d99600; padding: 0 4px; border-radius: 3px; display: inline-block;">${w}</span>`;
                            }
                            return w;
                        }).join(' ');
                    }

                    const rawHighlighted = highlightWords(rawText);
                    const strippedHighlighted = highlightWords(strippedText);

                    const audioSrc = getAudioUrl(rec.b, rec.c, rec.v);
                    const parseAccents = self.parseVerseText(rawText);

                    htmlStr += `
                        <div class="verse-card" style="margin-bottom: 22px; padding: 16px 20px; background: #ffffff; border: 1px solid #e2ddd0; border-radius: 6px; box-shadow: 0 1px 4px rgba(0,0,0,0.03); max-width: 100%; box-sizing: border-box; white-space: normal;">
                            <div class="verse-header-line" style="display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #f2eee5; padding-bottom: 8px; margin-bottom: 12px;">
                                <span class="verse-title" style="font-family: sans-serif; font-size: 1.1rem; font-weight: bold;">
                                    <a href="ornament_chapter.html?book=${encodeURIComponent(rec.b)}&chapter=${rec.c}" style="color: #800000; text-decoration: none;">
                                        ${rec.b} ${rec.c}:${rec.v} 📖
                                    </a>
                                </span>
                                <div class="verse-audio-box">
                                    <audio controls style="height: 30px; vertical-align: middle;">
                                        <source src="${audioSrc}" type="audio/mpeg">
                                    </audio>
                                </div>
                            </div>

                            <div class="verse-text" title="${transText.replace(/"/g, '&quot;')}" data-raw="${rawHighlighted.replace(/"/g, '&quot;')}" data-stripped="${strippedHighlighted.replace(/"/g, '&quot;')}" style="direction: rtl; text-align: right; font-family: 'SBL Hebrew', 'Ezra SIL', serif; font-size: 1.55rem; line-height: 1.9; color: #111; margin-bottom: 8px;">
                                ${strippedHighlighted}
                            </div>

                            <div class="verse-ext-desc" style="display: none; direction: rtl; text-align: right; margin-top: 8px; padding-top: 8px; border-top: 1px dashed #e5dfd3; font-family: sans-serif; font-size: 0.88rem; color: #333; width: 100%; max-width: 100%; box-sizing: border-box; white-space: normal !important; word-break: break-word !important;">
                                ${parseAccents.map(a => `
                                    <span style="white-space: nowrap;">
                                        <span style="font-family: 'SBL Hebrew', serif; color: #800000; font-size: 1.1rem;">${a.symbolOnAleph || ('א' + a.char)}</span>
                                        <strong>${a.nameTranslit}</strong>
                                        <span style="font-family: monospace; color: #1a5276;">(${a.pitchOrInterval})</span>
                                    </span>
                                `).join('&nbsp;&nbsp;&bull;&nbsp;&nbsp;')}
                            </div>
                        </div>
                    `;
                });

                htmlStr += `</div></div>`;
                container.innerHTML = htmlStr;

                // Bind Event Listeners
                const bookSelect = container.querySelector('#book-filter-select');
                if (bookSelect) {
                    bookSelect.addEventListener('change', (e) => {
                        selectedBook = e.target.value;
                        renderView();
                    });
                }

                const toggleVowels = container.querySelector('#toggle-vowels');
                const toggleExtDesc = container.querySelector('#toggle-ext-desc');

                function applyToggles() {
                    const showVowels = toggleVowels ? toggleVowels.checked : false;
                    const showExt = toggleExtDesc ? toggleExtDesc.checked : false;

                    container.querySelectorAll('.verse-text').forEach(el => {
                        el.innerHTML = showVowels ? el.dataset.raw : el.dataset.stripped;
                    });

                    container.querySelectorAll('.verse-ext-desc').forEach(el => {
                        el.style.display = showExt ? 'block' : 'none';
                    });
                }

                if (toggleVowels) toggleVowels.addEventListener('change', applyToggles);
                if (toggleExtDesc) toggleExtDesc.addEventListener('change', applyToggles);
            }

            renderView();
        }

        
    }

    global.HebrewAccentParser = HebrewAccentParser;
})(typeof window !== 'undefined' ? window : this);
