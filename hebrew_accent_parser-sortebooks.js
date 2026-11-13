/**
 * Hebrew Accent Parser & Musical Concordance Enhancer
 * Project: SimHebrew Concordance / Hebrew Bible Site Pipeline
 * Author: D. Robert MacDonald & Gemini Notebook
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

    class HebrewAccentParser {
        constructor() {
            this.dictionary = {};
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
                    console.error('Failed to load accent dictionary from URL:', err);
                    return false;
                }
            } else if (typeof dataOrUrl === 'object' && dataOrUrl !== null) {
                this.dictionary = dataOrUrl;
            } else {
                console.error('Invalid data or URL provided to HebrewAccentParser');
                return false;
            }

            this._buildIndexes();
            this.isLoaded = true;
            return true;
        }

        _buildIndexes() {
            this.byDecimal.clear();
            this.byHex.clear();
            this.bySlug.clear();
            this.byHebrew.clear();

            for (const [key, entry] of Object.entries(this.dictionary)) {
                const hexNormalized = String(entry.hex).toUpperCase();
                const hexRaw = String(entry.hex_raw).toUpperCase();
                this.byHex.set(hexNormalized, entry);
                this.byHex.set(hexRaw, entry);

                if (Array.isArray(entry.decimal)) {
                    this.byDecimal.set(entry.decimal.join('+'), entry);
                } else {
                    this.byDecimal.set(Number(entry.decimal), entry);
                }

                if (entry.name_translit) {
                    const mainSlug = this._normalizeSlug(entry.name_translit);
                    this.bySlug.set(mainSlug, entry);

                    if (entry.name_translit.includes('/')) {
                        const parts = entry.name_translit.split('/');
                        parts.forEach(p => {
                            const ps = this._normalizeSlug(p);
                            if (ps) this.bySlug.set(ps, entry);
                        });
                    }

                    if (mainSlug.includes('gedolah')) {
                        this.bySlug.set(mainSlug.replace('gedolah', 'gedola'), entry);
                    } else if (mainSlug.includes('gedola')) {
                        this.bySlug.set(mainSlug.replace('gedola', 'gedolah'), entry);
                    }
                }

                if (entry.name_hebrew) {
                    this.byHebrew.set(entry.name_hebrew.trim(), entry);
                    const unpointed = entry.name_hebrew.replace(/[\u0591-\u05C7]/g, '').trim();
                    if (unpointed) {
                        this.byHebrew.set(unpointed, entry);
                    }
                }
            }

            const aliasMap = {
                'geresh': 'U+059D',
                'gereshmuqdam': 'U+059D',
                'geresh-muqdam': 'U+059D',
                'reviamugrash': 'U+059D_REVIA_MUGRASH',
                'revia-mugrash': 'U+059D_REVIA_MUGRASH',
                'gerishrevia': 'U+059D_REVIA_MUGRASH',
                'gerish-revia': 'U+059D_REVIA_MUGRASH',
                'zarqa': 'U+0598',
                'tsinnoret': 'U+0598',
                'tarsin': 'U+059E',
                'gershaim': 'U+059E',
                'telishagedola': 'U+05A0',
                'telisha-gedola': 'U+05A0',
                'telisha-gedolah': 'U+05A0',
                'zaqefqatan': 'U+0594',
                'zaqef-qatan': 'U+0594',
                'zaqefgadol': 'U+0595',
                'zaqef-gadol': 'U+0595'
            };

            for (const [alias, entryKey] of Object.entries(aliasMap)) {
                if (this.dictionary[entryKey]) {
                    this.bySlug.set(this._normalizeSlug(alias), this.dictionary[entryKey]);
                }
            }
        }

        _normalizeSlug(str) {
            return String(str)
                .toLowerCase()
                .replace(/[^a-z0-9]/g, '');
        }

        getByDecimal(dec) {
            return this.byDecimal.get(Number(dec)) || null;
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
            let match = this.bySlug.get(slug);
            if (match) return match;

            const parts = name.split(/[\s\-_\/]+/);
            if (parts.length > 1) {
                const matchedParts = parts.map(p => this.getByName(p)).filter(Boolean);
                if (matchedParts.length === parts.length) {
                    return {
                        hex: matchedParts.map(m => m.hex).join('+'),
                        symbol: matchedParts.map(m => m.symbol).join(''),
                        symbol_on_aleph: 'א' + matchedParts.map(m => m.symbol).join(''),
                        name_hebrew: matchedParts.map(m => m.name_hebrew).join(' / '),
                        name_translit: matchedParts.map(m => m.name_translit).join('-'),
                        category: 'compound',
                        pitch_or_interval: matchedParts.map(m => m.pitch_or_interval).join('\n'),
                        description: 'Composite accent pair'
                    };
                }
            }
            return null;
        }

        /**
         * Resolves the precise audio path for verse MP3s across multi-word books.
         * Handles folder name (UPPERCASE with spaces, e.g. "1 CHRONICLES") and
         * file name (Proper Case with underscores, e.g. "1_Chronicles_1_28.mp3").
         */
        getAudioUrl(rawBookCode, chNum, vsNum) {
            if (!rawBookCode) return '';
            
            // 1. Convert "1_CHRONICLES" -> "1 CHRONICLES" for web directory
            const folderName = String(rawBookCode).trim().replace(/_/g, ' ');

            // 2. Ensure Proper Case with underscores for file name ("1_Chronicles")
            const properBookName = folderName
                .toLowerCase()
                .split(/\s+/)
                .map(w => w.charAt(0).toUpperCase() + w.slice(1))
                .join('_');

            // 3. Strip leading zeros from chapter and verse numbers
            const c = String(chNum).replace(/^0+/, '') || '1';
            const v = String(vsNum).replace(/^0+/, '') || '1';

            const audioFileName = `${properBookName}_${c}_${v}.mp3`;

            // 4. Encode folder spaces (%20) while keeping proper-cased filename
            return `./musicscores/audio/${encodeURIComponent(folderName)}/${audioFileName}`;
        }

        /**
         * Render concordance records onto ornament_records.html
         */
        renderOrnamentRecords(targetSelector, indexData, ornParam = '', pitchParam = '') {
            const container = typeof targetSelector === 'string' ? document.querySelector(targetSelector) : targetSelector;
            if (!container) return;

            const ornKey = ornParam.toLowerCase();
            const pitchKey = pitchParam;

            let records = [];
            if (indexData[ornKey] && indexData[ornKey][pitchKey]) {
                records = indexData[ornKey][pitchKey];
            }

            // Extract unique books and sort canonically
            const uniqueBooksSet = new Set(records.map(r => r.b.trim()));
            const availableBooks = CANONICAL_BOOKS.filter(b => uniqueBooksSet.has(b));

            // URL parameter parsing for book filter
            const urlParams = new URLSearchParams(window.location.search);
            const defaultBook = availableBooks[0] || 'ALL';
            const selectedBook = urlParams.get('book') || defaultBook;

            const filteredRecords = selectedBook === 'ALL'
                ? records
                : records.filter(r => r.b.trim() === selectedBook);

            // Build toolbar HTML with canonical book ordering
            let toolbarHtml = `
                <div style="margin-bottom: 20px; padding: 15px; background: #f3f0e8; border-radius: 6px; display: flex; align-items: center; gap: 15px; font-family: sans-serif;">
                    <label style="font-weight: bold; color: #800000;">Filter by Book:</label>
                    <select id="book-filter-select" style="padding: 6px 12px; font-size: 0.95rem; border-radius: 4px; border: 1px solid #ccc;">
                        <option value="ALL" ${selectedBook === 'ALL' ? 'selected' : ''}>All Books (${records.length} records)</option>
            `;

            availableBooks.forEach(b => {
                const count = records.filter(r => r.b.trim() === b).length;
                toolbarHtml += `<option value="${b}" ${selectedBook === b ? 'selected' : ''}>${b} (${count})</option>`;
            });

            toolbarHtml += `
                    </select>
                </div>
            `;

            // Render Verse Cards
            let cardsHtml = toolbarHtml;

            if (filteredRecords.length === 0) {
                cardsHtml += `<p style="font-style: italic; color: #666;">No concordance records found for this selection.</p>`;
            } else {
                filteredRecords.forEach(rec => {
                    const audioUrl = this.getAudioUrl(rec.b, rec.c, rec.v);

                    cardsHtml += `
                        <div class="verse-card">
                            <div class="verse-header-line">
                                <span class="verse-title">${rec.b} ${rec.c}:${rec.v}</span>
                                <div class="verse-audio-box">
                                    <audio controls style="height: 30px; vertical-align: middle;">
                                        <source src="${audioUrl}" type="audio/mpeg">
                                    </audio>
                                </div>
                            </div>
                            <div class="verse-text">${rec.t || ''}</div>
                        </div>
                    `;
                });
            }

            container.innerHTML = cardsHtml;

            // Attach event listener to book filter select dropdown
            const selectEl = document.getElementById('book-filter-select');
            if (selectEl) {
                selectEl.addEventListener('change', (e) => {
                    urlParams.set('book', e.target.value);
                    window.location.search = urlParams.toString();
                });
            }
        }
    }

    global.HebrewAccentParser = HebrewAccentParser;

})(typeof window !== 'undefined' ? window : this);
