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

    const PITCH_NAMES = {
        "c": "Darga",
        "d": "Tevir/Galgal",
        "e": "Silluq",
        "f": "Mercha",
        "g": "Tifha/D'khi",
        "A": "Atnah",
        "B": "Munach",
        "C": "Mahpach/Yetiv"
    };

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

                if (entry.decimal) {
                    this.byDecimal.set(Number(entry.decimal), entry);
                }

                if (entry.name_translit) {
                    const slug = this._normalizeSlug(entry.name_translit);
                    this.bySlug.set(slug, entry);
                }

                if (entry.name_hebrew) {
                    this.byHebrew.set(entry.name_hebrew.trim(), entry);
                    const unpointed = entry.name_hebrew.replace(/[\u0591-\u05C7]/g, '').trim();
                    if (unpointed) {
                        this.byHebrew.set(unpointed, entry);
                    }
                }
            }
        }

        _normalizeSlug(str) {
            let s = String(str).toLowerCase().trim();
            s = s.replace(/\bz-qatan\b/g, 'zaqefqatan')
                 .replace(/\bz-gadol\b/g, 'zaqefgadol')
                 .replace(/\bt-gedola\b/g, 'telishagedola')
                 .replace(/\bt-gedolah\b/g, 'telishagedola')
                 .replace(/\bt-qetana\b/g, 'telishaqetana')
                 .replace(/\bzqatan\b/g, 'zaqefqatan')
                 .replace(/\bzgadol\b/g, 'zaqefgadol')
                 .replace(/\btgedola\b/g, 'telishagedola')
                 .replace(/\btqetana\b/g, 'telishaqetana');
            return s.replace(/[^a-z0-9]/g, '');
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
            let found = this.bySlug.get(slug) || null;
            if (found) return found;

            const parts = name.split(/[-_\s]+/);
            if (parts.length > 1) {
                const matchedParts = parts.map(p => this.getByName(p)).filter(Boolean);
                if (matchedParts.length > 0) {
                    return {
                        hex: matchedParts.map(m => m.hex).join('+'),
                        symbol: matchedParts.map(m => m.symbol).join(''),
                        symbol_on_aleph: 'א' + matchedParts.map(m => m.symbol).join(''),
                        name_hebrew: matchedParts.map(m => m.name_hebrew).join(' / '),
                        name_translit: matchedParts.map(m => m.name_translit).join(' / '),
                        pitch_or_interval: matchedParts.map(m => m.pitch_or_interval).join('\n')
                    };
                }
            }
            return null;
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
                        symbolOnAleph: accent.symbol_on_aleph || ('א' + accent.symbol),
                        pitchOrInterval: accent.pitch_or_interval
                    });
                }
            }
            return results;
        }

        stripNiqqud(text) {
            if (!text || typeof text !== 'string') return '';
            return text.replace(/[\u05B0-\u05BC\u05C1\u05C2\u05C4\u05C5\u05C7]/g, '');
        }

        calculateGematria(text) {
            if (!text || typeof text !== 'string') return { total: 0, factorsStr: '', weightsStr: '' };
            const gematriaMap = {
                'א':1, 'ב':2, 'ג':3, 'ד':4, 'ה':5, 'ו':6, 'ז':7, 'ח':8, 'ט':9,
                'י':10, 'כ':20, 'ך':20, 'ל':30, 'מ':40, 'ם':40, 'נ':50, 'ן':50,
                'ס':60, 'ע':70, 'פ':80, 'ף':80, 'צ':90, 'ץ':90, 'ק':100, 'ר':200,
                'ש':300, 'ת':400
            };
            const words = text.trim().split(/\s+/);
            const wordWeightsRTL = [];
            let total = 0;

            for (let w = words.length - 1; w >= 0; w--) {
                let wSum = 0;
                for (const char of words[w]) {
                    if (gematriaMap[char]) wSum += gematriaMap[char];
                }
                wordWeightsRTL.push(wSum);
                total += wSum;
            }

            const factors = [];
            let d = 2;
            let temp = total;
            while (temp >= 2) {
                if (temp % d === 0) {
                    factors.push(d);
                    temp = Math.floor(temp / d);
                } else {
                    d++;
                    if (d * d > temp) {
                        if (temp > 1) factors.push(temp);
                        break;
                    }
                }
            }

            return {
                total: total,
                factorsStr: factors.length > 0 ? factors.join(', ') : String(total),
                weightsStr: wordWeightsRTL.join(' + ')
            };
        }

        isPoeticContext(book, c, v) {
            const b = String(book || '').trim();
            const cNum = parseInt(c) || 0;
            const vNum = parseInt(v) || 0;
            if (b === 'Psalms' || b === 'Proverbs') return true;
            if (b === 'Job') {
                if (cNum > 3 && cNum < 42) return true;
                if (cNum === 3 && vNum >= 2) return true;
                if (cNum === 42 && vNum <= 6) return true;
            }
            return false;
        }

        getTrimmedPitch(accent, book, c, v) {
            if (!accent) return '';
            const isPoetic = this.isPoeticContext(book, c, v);
            const slug = accent.nameTranslit ? accent.nameTranslit.toLowerCase() : (accent.name_translit ? accent.name_translit.toLowerCase() : '');
            
            if (slug.includes('revia') && !slug.includes('mugrash')) {
                return isPoetic ? '-1+0' : '-0-1';
            }
            if (slug.includes('tifha') || slug.includes('dkhi')) {
                return isPoetic ? 'g#' : 'g';
            }
            if (slug.includes('mercha') && !slug.includes('kefula')) {
                return isPoetic ? 'f#' : 'f';
            }
            return (accent.pitchOrInterval || accent.pitch_or_interval || '').split('\n')[0].trim();
        }

        renderOrnamentRecords(containerSelector, indexData, ornParam, pitchParam, urlBookParam = '') {
            const container = typeof containerSelector === 'string' ? document.querySelector(containerSelector) : containerSelector;
            if (!container || !indexData) return;

            const targetSlug = this._normalizeSlug(ornParam);
            let matchedKey = Object.keys(indexData).find(k => this._normalizeSlug(k) === targetSlug);
            if (!matchedKey) {
                matchedKey = Object.keys(indexData).find(k => k.toLowerCase() === ornParam.toLowerCase());
            }

            const pitchHebrewName = PITCH_NAMES[pitchParam] || pitchParam;
            const accent = this.getByName(ornParam);
            const displayName = accent ? accent.name_translit : (ornParam ? ornParam.charAt(0).toUpperCase() + ornParam.slice(1) : 'Ornament');

            let allRecords = [];
            if (matchedKey && indexData[matchedKey] && indexData[matchedKey][pitchParam]) {
                allRecords = indexData[matchedKey][pitchParam];
            }

            // Collect unique book names from records
            const uniqueBooksSet = new Set();
            allRecords.forEach(r => { if (r.b) uniqueBooksSet.add(r.b.trim()); });

            // Sort available books in CANONICAL order
            const availableBooks = [];
            CANONICAL_BOOKS.forEach(b => {
                if (uniqueBooksSet.has(b)) availableBooks.push(b);
            });
            uniqueBooksSet.forEach(b => {
                if (!availableBooks.includes(b)) availableBooks.push(b);
            });

            // Determine default selected book:
            // 1. If urlBookParam is passed and present in availableBooks -> use it
            // 2. Otherwise default to first available canonical book (availableBooks[0])
            // 3. Fallback to 'ALL' if no books exist
            let defaultBook = 'ALL';
            if (urlBookParam && availableBooks.includes(urlBookParam)) {
                defaultBook = urlBookParam;
            } else if (availableBooks.length > 0) {
                defaultBook = availableBooks[0];
            }

            let html = `
                <div class="records-header-box" style="margin-bottom: 20px;">
                    <!-- LINE 2: Header Title -->
                    <h2 style="margin: 0 0 12px 0; color: #800000; font-family: sans-serif; font-size: 1.5rem; font-weight: normal;">
                        ${displayName} on Recitation Pitch: ${pitchParam} (${pitchHebrewName})
                    </h2>

                    <!-- LINE 3: Controls & Canonical Book Filter Toolbar -->
                    <div class="controls-toolbar" style="display: flex; flex-wrap: wrap; gap: 18px; align-items: center; font-family: sans-serif; font-size: 0.9rem; color: #444; background: #f3f0e8; padding: 10px 14px; border-radius: 4px;">
                        <label style="display: flex; align-items: center; gap: 6px; cursor: pointer;">
                            <input type="checkbox" id="toggle-niqqud" style="cursor: pointer;">
                            <strong>Show vowel points (niqqud)</strong>
                        </label>
                        <label style="display: flex; align-items: center; gap: 6px; cursor: pointer;">
                            <input type="checkbox" id="toggle-descriptions" style="cursor: pointer;">
                            <strong>Show extended description</strong>
                        </label>
                        <div style="display: flex; align-items: center; gap: 6px; margin-left: auto;">
                            <strong>Filter by Book:</strong>
                            <select id="book-filter-select" style="padding: 4px 8px; border: 1px solid #ccc; border-radius: 3px; font-family: sans-serif; cursor: pointer;">
                                <option value="ALL">All Books (${allRecords.length} records)</option>
                                ${availableBooks.map(b => {
                                    const cnt = allRecords.filter(r => r.b === b).length;
                                    return `<option value="${b}">${b} (${cnt} records)</option>`;
                                }).join('')}
                            </select>
                        </div>
                    </div>
                </div>

                <div id="verse-cards-container"></div>
            `;

            container.innerHTML = html;

            const selectEl = container.querySelector('#book-filter-select');
            if (selectEl) {
                selectEl.value = defaultBook;
            }

            const renderCards = (selectedBook) => {
                const cardsContainer = container.querySelector('#verse-cards-container');
                if (!cardsContainer) return;

                let filtered = allRecords;
                if (selectedBook && selectedBook !== 'ALL') {
                    filtered = allRecords.filter(r => r.b === selectedBook);
                }

                if (filtered.length === 0) {
                    cardsContainer.innerHTML = `<div style="padding: 30px; background: #fff; border: 1px solid #e2ddd0; border-radius: 6px; color: #800000; font-style: italic;">No records found for the selected book filter.</div>`;
                    return;
                }

                // Guard against browser freeze if ALL is chosen for high-frequency ornaments
                const MAX_CARDS = 250;
                const countToRender = Math.min(filtered.length, MAX_CARDS);
                let cardsHtml = '';

                if (filtered.length > MAX_CARDS && selectedBook === 'ALL') {
                    cardsHtml += `
                        <div style="padding: 10px 14px; background: #fff8e7; border: 1px solid #e0c975; border-radius: 4px; margin-bottom: 15px; font-family: sans-serif; font-size: 0.88rem; color: #7a5e00;">
                            Showing first <strong>${MAX_CARDS}</strong> of <strong>${filtered.length}</strong> records across All Books. Select a specific book above to view all its records.
                        </div>
                    `;
                }

                for (let i = 0; i < countToRender; i++) {
                    const rec = filtered[i];
                    const rawText = rec.t || '';
                    const strippedText = this.stripNiqqud(rawText);

                    // Parse verse accents for inline single-line RTL sequence
                    const verseAccents = this.parseVerseText(rawText);
                    const extDescItems = verseAccents.map(acc => {
                        const sym = acc.symbolOnAleph || ('א' + acc.char);
                        const pStr = this.getTrimmedPitch(acc, rec.b, rec.c, rec.v);
                        return `<span style="white-space: nowrap;"><span style="font-family: 'SBL Hebrew', serif; color: #800000; font-size: 1.1rem;">${sym}</span> <strong>${acc.nameTranslit}</strong> <span style="font-family: monospace; color: #1a5276;">(${pStr})</span></span>`;
                    });

                    const extDescHtml = extDescItems.length > 0 ? extDescItems.join('&nbsp;&nbsp;&bull;&nbsp;&nbsp;') : '';

                    cardsHtml += `
                        <div class="verse-card" style="margin-bottom: 22px; padding: 16px 20px; background: #ffffff; border: 1px solid #e2ddd0; border-radius: 6px; box-shadow: 0 1px 4px rgba(0,0,0,0.03); max-width: 100%; box-sizing: border-box; white-space: normal;">
                            <!-- HEADER LINE: Book Chapter:Verse Link + Inline Audio Player -->
                            <div class="verse-header-line" style="display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #f2eee5; padding-bottom: 8px; margin-bottom: 12px;">
                                <span class="verse-title" style="font-family: sans-serif; font-size: 1.1rem; font-weight: bold;">
                                    <a href="ornament_chapter.html?book=${encodeURIComponent(rec.b)}&chapter=${encodeURIComponent(rec.c)}" style="color: #800000; text-decoration: none;">
                                        ${rec.b} ${rec.c}:${rec.v} 📖
                                    </a>
                                </span>
                                <div class="verse-audio-box">
                                    <audio controls style="height: 30px; vertical-align: middle;">
                                        <source src="./musicscores/audio/${encodeURIComponent(rec.b)}/${encodeURIComponent(rec.b)}_${rec.c}_${rec.v}.mp3" type="audio/mpeg">
                                        <source src="./musicscores/audio/${encodeURIComponent(rec.b)}_${rec.c}_${rec.v}.mp3" type="audio/mpeg">
                                    </audio>
                                </div>
                            </div>

                            <!-- VERSE HEBREW TEXT -->
                            <div class="verse-text" data-raw="${this._escapeAttr(rawText)}" data-stripped="${this._escapeAttr(strippedText)}" style="direction: rtl; text-align: right; font-family: 'SBL Hebrew', 'Ezra SIL', serif; font-size: 1.55rem; line-height: 1.9; color: #111; margin-bottom: 8px;">
                                ${rawText}
                            </div>

                            <!-- EXTENDED DESCRIPTION: SINGLE-LINE RTL INLINE ACCENT SEQUENCE -->
                            <div class="verse-ext-desc" style="display: block; direction: rtl; text-align: right; margin-top: 8px; padding-top: 8px; border-top: 1px dashed #e5dfd3; font-family: sans-serif; font-size: 0.88rem; color: #333; width: 100%; max-width: 100%; box-sizing: border-box; white-space: normal !important; word-break: break-word !important;">
                                ${extDescHtml}
                            </div>
                        </div>
                    `;
                }

                cardsContainer.innerHTML = cardsHtml;
                applyToggles();
            };

            const applyToggles = () => {
                const niqqudCb = container.querySelector('#toggle-niqqud');
                const descCb = container.querySelector('#toggle-descriptions');

                if (niqqudCb) {
                    const showNiqqud = niqqudCb.checked;
                    container.querySelectorAll('.verse-text').forEach(el => {
                        el.textContent = showNiqqud ? el.dataset.raw : el.dataset.stripped;
                    });
                }

                if (descCb) {
                    const showDesc = descCb.checked;
                    container.querySelectorAll('.verse-ext-desc').forEach(el => {
                        el.style.display = showDesc ? 'block' : 'none';
                    });
                }
            };

            // Event Listeners for controls
            const niqqudCb = container.querySelector('#toggle-niqqud');
            const descCb = container.querySelector('#toggle-descriptions');
            if (niqqudCb) niqqudCb.addEventListener('change', applyToggles);
            if (descCb) descCb.addEventListener('change', applyToggles);

            if (selectEl) {
                selectEl.addEventListener('change', (e) => {
                    renderCards(e.target.value);
                });
            }

            // Initial render using defaultBook!
            renderCards(defaultBook);
        }

        _escapeAttr(str) {
            return String(str)
                .replace(/&/g, '&amp;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#39;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;');
        }
    }

    global.HebrewAccentParser = HebrewAccentParser;
})(typeof window !== 'undefined' ? window : this);
