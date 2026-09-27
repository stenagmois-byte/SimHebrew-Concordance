// ==========================================
// menu.js - Universal Navigation & Interlinear Gloss Pipeline
// ==========================================

const bookSequenceMap = {
    "GENESIS": "01", "EXODUS": "02", "LEVITICUS": "03", "NUMBERS": "04", "DEUTERONOMY": "05",
    "JOSHUA": "06", "JUDGES": "07", "1_SAMUEL": "08", "2_SAMUEL": "09", "1_KINGS": "10",
    "2_KINGS": "11", "ISAIAH": "12", "JEREMIAH": "13", "EZEKIEL": "14", "HOSEA": "15",
    "JOEL": "16", "AMOS": "17", "OBADIAH": "18", "JONAH": "19", "MICAH": "20",
    "NAHUM": "21", "HABAKKUK": "22", "ZEPHANIAH": "23", "HAGGAI": "24", "ZECHARIAH": "25",
    "MALACHI": "26", "PSALMS": "27", "PROVERBS": "28", "JOB": "29", "SONG": "30",
    "RUTH": "31", "LAMENTATIONS": "32", "QOHELET": "33", "ESTHER": "34", "DANIEL": "35",
    "EZRA": "36", "NEHEMIAH": "37", "1_CHRONICLES": "38", "2_CHRONICLES": "39"
};

function normalizeBookName(raw) {
    if (!raw) return "";
    const decoded = decodeURIComponent(raw).trim().toUpperCase();
    return decoded.replace(/%20/g, ' ').replace(/\s+/g, '_').replace(/_+/g, '_');
}

function formatDisplayTitle(bookKey) {
    const clean = normalizeBookName(bookKey);
    if (!clean) return "";
    const parts = clean.split('_');
    return parts.map(p => {
        if (p.match(/^\d+$/)) return p;
        return p.charAt(0) + p.slice(1).toLowerCase();
    }).join(' ');
}

function stripHebrew(str) {
    if (!str) return "";
    const decoded = decodeHtmlEntities(str);
    return decoded.replace(/[\u0591-\u05C7]/g, "").trim();
}

function decodeHtmlEntities(str) {
    if (!str) return "";
    const txt = document.createElement("textarea");
    txt.innerHTML = str;
    return txt.value;
}

let interlinDataList = [];

function loadChapterInterlinear(book, chap) {
    if (!book || !chap) return;
    const isGitHubPages = window.location.hostname.includes('github.io');
    const basePath = isGitHubPages ? '/SimHebrew-Concordance' : '';
    const cleanBook = normalizeBookName(book);
    const padCh = String(chap || 1).padStart(3, '0');
    const chapterJsonPath = `${basePath}/chapters/${cleanBook}/${cleanBook}_${padCh}.json`;
    const customBuster = "?cb=" + new Date().getTime();

    console.log(`📥 [CHAPTER FETCH] Fetching interlinear JSON: ${chapterJsonPath}`);

    fetch(chapterJsonPath + customBuster)
        .then(response => {
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return response.json();
        })
        .then(data => {
            if (data && data.results && Array.isArray(data.results) && data.results[0] && data.results[0].items) {
                interlinDataList = data.results[0].items;
            } else if (data && data.results && data.results.items) {
                interlinDataList = data.results.items;
            } else if (Array.isArray(data)) {
                interlinDataList = data;
            } else {
                interlinDataList = [];
            }
            console.log(`✅ [CHAPTER DATA MOUNTED] Loaded ${interlinDataList.length} items for ${cleanBook} Ch ${padCh}.`);
        })
        .catch(err => {
            console.warn(`⚠️ [CHAPTER FETCH FALLBACK] Could not load ${chapterJsonPath}:`, err);
            interlinDataList = [];
        });
}

window.loadChapterInterlinear = loadChapterInterlinear;

document.addEventListener("DOMContentLoaded", function() {
    // ---------------------------------------------------------
    // PHASE 1: TOP BUTTON MENU BAR
    // ---------------------------------------------------------
    const navWrapper = document.createElement("nav");
    navWrapper.id = "canonical-nav-menu";
    navWrapper.setAttribute("aria-label", "Tanach Music Concordance Navigator");

    const style = document.createElement("style");
    style.textContent = `
        #canonical-nav-menu {
            position: fixed;
            top: 0;
            left: 0;
            width: 100% !important;
            height: 48px !important;
            background: #800000 !important; 
            z-index: 999999 !important;
            font-family: Arial, sans-serif !important;
            display: flex !important;
            align-items: center !important;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2) !important;
            padding: 0 8px !important;
            box-sizing: border-box !important;
        }
        .top-nav-bar {
            display: flex !important;
            flex-direction: row !important;
            align-items: center !important;
            gap: 6px !important;
            width: 100% !important;
            overflow-x: auto !important;
            scrollbar-width: thin !important;
        }
        .top-nav-btn {
            background: #600000 !important; 
            color: #fcfcf9 !important;     
            border: 1px solid #a03030 !important;
            padding: 3px 10px !important;  
            border-radius: 4px !important; 
            cursor: pointer !important;
            text-decoration: none !important;
            display: flex !important;
            flex-direction: column !important;
            justify-content: center !important;
            align-items: center !important;
            text-align: center !important;
            min-width: 110px !important;
            height: 38px !important;
            box-sizing: border-box !important;
            transition: background 0.15s, border-color 0.15s !important;
            flex-shrink: 0 !important;
        }
        .top-nav-btn:hover { 
            background: #400000 !important; 
            border-color: #d4af37 !important;
            color: #ffd700 !important;
        }
        .top-nav-btn.is-hidden {
            display: none !important;
        }
        .btn-line1 {
            font-size: 11px !important;
            font-weight: bold !important;
            line-height: 1.1 !important;
            white-space: nowrap !important;
        }
        .btn-line2 {
            font-size: 10px !important;
            font-weight: normal !important;
            color: #e0d0c0 !important;
            line-height: 1.1 !important;
            white-space: nowrap !important;
        }
        body {
            padding-top: 58px !important;
            max-width: none !important; 
            margin: 0 auto !important;
        }
        :target { scroll-margin-top: 58px !important; }
    `;
    document.head.appendChild(style);

    const isGitHubPages = window.location.hostname.includes("github.io");
    const repoPath = isGitHubPages ? "/SimHebrew-Concordance" : "";
    const baseUrl = `${window.location.origin}${repoPath}`;
    const wordPath = isGitHubPages ? '/SimHebrew-Concordance/' : '/';

    navWrapper.innerHTML = `
        <div class="top-nav-bar">
            <a href="${baseUrl}/index.html" class="top-nav-btn">
                <span class="btn-line1">🏠 Home</span>
                <span class="btn-line2">The Print Edition</span>
            </a>
            <a href="${baseUrl}/musicscores/index.html" class="top-nav-btn">
                <span class="btn-line1">📁 Hebrew Bible</span>
                <span class="btn-line2">Scores and Contours</span>
            </a>
            <a href="${baseUrl}/ornament_usage_by_pitch.html" class="top-nav-btn">
                <span class="btn-line1">📊 Ornaments</span>
                <span class="btn-line2">by Pitch</span>
            </a>
            <a href="#" id="contextual-ornament-records" class="top-nav-btn is-hidden">
                <span class="btn-line1">🔍 Full Trope</span>
                <span class="btn-line2" id="chapter-btn-label">by Chapter</span>
            </a>
            <a href="${baseUrl}/matrix.html" class="top-nav-btn">
                <span class="btn-line1">⌨️ Word Matrix</span>
                <span class="btn-line2">SimHebrew</span>
            </a>
            <a href="${baseUrl}/gematria_verse_twins.html" class="top-nav-btn">
                <span class="btn-line1">🔢 Gematria</span>
                <span class="btn-line2">Verse Twins</span>
            </a>
        </div>
    `;
    document.body.appendChild(navWrapper);

    // ---------------------------------------------------------
    // PHASE 2: CONTEXT RESOLUTION (929 CONTOUR PAGES & CANTILLATION SCREEN)
    // ---------------------------------------------------------
    const recordBtn = document.getElementById("contextual-ornament-records");
    const labelSpan = document.getElementById("chapter-btn-label");

    let cleanBook = null;
    let chapterNum = null;

    const urlParams = new URLSearchParams(window.location.search);
    const rawBookParam = urlParams.get('book');
    const rawChapterParam = urlParams.get('chapter');

    const pathSegments = window.location.pathname.split('/');
    const filename = pathSegments[pathSegments.length - 1] || "";

    // Case 1: URL Query Parameters (e.g. ornament_chapter.html?book=Isaiah&chapter=5)
    if (rawBookParam) {
        const candidateBook = normalizeBookName(rawBookParam);
        if (bookSequenceMap[candidateBook]) {
            cleanBook = candidateBook;
            if (rawChapterParam && rawChapterParam.match(/\d+/)) {
                chapterNum = parseInt(rawChapterParam.match(/\d+/), 10).toString();
            }
        }
    }
    // Case 2: Filename pattern matching (e.g. ISAIAH_005_matrix.html)
    else {
        const contourMatch = filename.match(/^([A-Z0-9_]+)_(\d{1,3})_matrix\.html$/i);
        if (contourMatch) {
            const candidateBook = normalizeBookName(contourMatch[1]);
            if (bookSequenceMap[candidateBook]) {
                cleanBook = candidateBook;
                chapterNum = parseInt(contourMatch[2], 10).toString();
            }
        }
    }

    // Mount chapter data & update top menu button state
    if (cleanBook && chapterNum && bookSequenceMap[cleanBook]) {
        const displayTitle = formatDisplayTitle(cleanBook);
        const dynamicOrnamentUrl = `${baseUrl}/ornament_chapter.html?book=${encodeURIComponent(displayTitle)}&chapter=${chapterNum}`;

        // Load chapter JSON for concordance popups on both matrix & cantillation screens
        loadChapterInterlinear(cleanBook, chapterNum);

        // Show "Cantillation [Book] [Ch]" button ONLY when on a 929 contour page (_matrix.html)
        if (filename.includes('_matrix.html')) {
            if (recordBtn && labelSpan) {
                recordBtn.href = dynamicOrnamentUrl;
                labelSpan.textContent = `${displayTitle} ${chapterNum}`;
                recordBtn.classList.remove("is-hidden");
            }
        } else {
            if (recordBtn) recordBtn.classList.add("is-hidden");
        }
    } else {
        if (recordBtn) recordBtn.classList.add("is-hidden");
    }

    // ---------------------------------------------------------
    // PHASE 3: INTERLINEAR GLOSS POPUP & CONCORDANCE LINKER
    // ---------------------------------------------------------
    const contextBox = document.createElement("div");
    contextBox.id = "oracle-root-linker";
    contextBox.style.cssText = `
        display: none;
        position: absolute;
        z-index: 100000;
        background: #800000;
        border: 2px solid #d4af37;
        border-radius: 6px;
        padding: 8px 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.5);
    `;
    document.body.appendChild(contextBox);

    const resolveContextAddress = (e) => {
        const rawSelection = window.getSelection().toString().trim();
        if (rawSelection.length === 0) return;

        const cleanHebrew = stripHebrew(rawSelection);
        if (!cleanHebrew) return;

        e.preventDefault();

        let padBook = cleanBook ? (bookSequenceMap[cleanBook] || "01") : "01";
        let padCh = String(chapterNum || 1).padStart(3, '0');

        const verseWrapper = e.target.closest('[id]') || e.target.closest('.verse') || e.target.closest('[data-verse]') || e.target.closest('p');
        let parsedVerseNum = "001";
        if (verseWrapper) {
            const rawId = verseWrapper.id || verseWrapper.getAttribute('data-verse') || "1";
            let numericId = parseInt(rawId.replace(/\D/g, ""), 10);
            if (!isNaN(numericId)) {
                if (numericId > 1000) numericId = numericId % 1000;
                parsedVerseNum = String(numericId).padStart(3, '0');
            }
        }

        const currentVersePrefix = `${padBook}_${padCh}_${parsedVerseNum}_`;

        const databaseRowMatch = interlinDataList.find(item => {
            if (!item.h || !item.k) return false;
            if (!item.k.startsWith(currentVersePrefix)) return false;
            return stripHebrew(item.h) === cleanHebrew;
        }) || interlinDataList.find(item => {
            if (!item.h || !item.k) return false;
            if (!item.k.startsWith(currentVersePrefix)) return false;
            const itemClean = stripHebrew(item.h);
            const itemNoprefix = itemClean.replace(/^[ובמהל]/, '');
            const selNoprefix = cleanHebrew.replace(/^[ובמהל]/, '');
            return itemNoprefix === selNoprefix && selNoprefix.length > 1;
        }) || interlinDataList.find(item => {
            if (!item.h) return false;
            return stripHebrew(item.h) === cleanHebrew;
        }) || interlinDataList.find(item => {
            if (!item.h) return false;
            const itemClean = stripHebrew(item.h);
            const itemNoprefix = itemClean.replace(/^[ובמהל]/, '');
            const selNoprefix = cleanHebrew.replace(/^[ובמהל]/, '');
            return itemNoprefix === selNoprefix && selNoprefix.length > 1;
        });

        let localGloss = "Explore branches";
        let localDomain = "General Lexicon";
        let targetRoot = "cli";

        if (databaseRowMatch) {
            if (databaseRowMatch.e) localGloss = databaseRowMatch.e;
            if (databaseRowMatch.d) localDomain = databaseRowMatch.d;
            if (databaseRowMatch.r) targetRoot = databaseRowMatch.r;
        }

        const targetHash = targetRoot.replace(/f/g, 'T');
        const rawPrefix = targetRoot.substring(0, 2);
        const computedUrl = `${wordPath}${rawPrefix}.html#${targetHash}`;

        contextBox.innerHTML = `
            <div style="color: #f0f0f0; font-size: 11px; font-family: system-ui, sans-serif; font-style: italic; border-bottom: 1px solid rgba(255,255,255,0.2); padding-bottom: 6px; margin-bottom: 6px; width: 100%;">
                Gloss: <strong style="color: #ffd700; font-style: normal; font-size: 12px;">"${localGloss}"</strong> 
                <span style="color: #ffffff; font-size: 10px; margin-left: 6px; font-style: normal; text-transform: uppercase; font-weight: bold; background: rgba(0,0,0,0.3); padding: 2px 5px; border-radius: 2px;">[${localDomain}]</span>
            </div>
            <a href="${computedUrl}" style="color: #fff; text-decoration: none; font-size: 13px; font-family: system-ui, sans-serif; display: flex; align-items: center; gap: 6px;" target="_blank">
                🔍 Concordance Root View: <strong>${targetHash}</strong>
            </a>
        `;

        const pageX = e.pageX || (e.touches ? e.touches.pageX : 0);
        const pageY = e.pageY || (e.touches ? e.touches.pageY : 0);

        contextBox.style.left = `${pageX + 10}px`;
        contextBox.style.top = `${pageY + 10}px`;
        contextBox.style.display = "block";
    };

    document.body.addEventListener("contextmenu", resolveContextAddress);
    document.body.addEventListener("touchend", (e) => {
        setTimeout(() => {
            if (window.getSelection().toString().trim().length > 0) resolveContextAddress(e);
        }, 150);
    });
    document.addEventListener("mousedown", (e) => {
        if (!contextBox.contains(e.target)) {
            contextBox.style.display = "none";
        }
    });
});
