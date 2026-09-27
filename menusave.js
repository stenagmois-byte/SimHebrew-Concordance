// ==========================================
// menu.js - Universal Navigation & Interlinear Gloss Pipeline
// ==========================================

// Global 39-book sequence mapping (book_seq_no padded to 2 digits)
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

/**
 * Normalizes book names to standard uppercase underscore format.
 * Examples: "1 Samuel", "1%20Samuel", "1_SAMUEL" -> "1_SAMUEL"
 */
function normalizeBookName(raw) {
    if (!raw) return "GENESIS";
    const decoded = decodeURIComponent(raw).trim().toUpperCase();
    return decoded.replace(/%20/g, ' ').replace(/\s+/g, '_').replace(/_+/g, '_');
}

/**
 * Formats directory book keys into clean display titles.
 * Examples: "1_SAMUEL" -> "1 Samuel", "JOB" -> "Job"
 */
function formatDisplayTitle(bookKey) {
    const clean = normalizeBookName(bookKey);
    const parts = clean.split('_');
    return parts.map(p => {
        if (p.match(/^\d+$/)) return p;
        return p.charAt(0) + p.slice(1).toLowerCase();
    }).join(' ');
}

/**
 * Extracts pure consonantal Hebrew text by stripping HTML entities, niqqud, and cantillation marks.
 */
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

// 📥 GLOBAL CHAPTER DATA STORE
let interlinDataList = [];

/**
 * Fetches individual chapter JSON file (e.g. chapters/ESTHER/ESTHER_001.json)
 */
function loadChapterInterlinear(book, chap) {
    const isGitHubPages = window.location.hostname.includes('github.io');
    const basePath = isGitHubPages ? '/SimHebrew-Concordance' : '';
    const cleanBook = normalizeBookName(book);
    const padCh = String(chap || 1).padStart(3, '0');
    const chapterJsonPath = `${basePath}/chapters/${cleanBook}/${cleanBook}_${padCh}.json`;
    const customBuster = "?cb=" + new Date().getTime();

    console.log(`📥 [CHAPTER FETCH] Fetching chapter interlinear: ${chapterJsonPath}`);

    fetch(chapterJsonPath + customBuster)
        .then(response => {
            if (!response.ok) throw new Error(`HTTP ${response.status} when fetching ${chapterJsonPath}`);
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
            console.log(`✅ [CHAPTER DATA MOUNTED] Loaded ${interlinDataList.length} items for ${cleanBook} Chapter ${padCh}.`);
        })
        .catch(err => {
            console.warn(`⚠️ [CHAPTER FETCH FALLBACK] Could not load ${chapterJsonPath}:`, err);
            interlinDataList = [];
        });
}

// Bind globally for immediate availability
window.loadChapterInterlinear = loadChapterInterlinear;

document.addEventListener("DOMContentLoaded", function() {
    // ---------------------------------------------------------
    // PHASE 1: GLOBAL HAMBURGER MENU (Runs on EVERY screen)
    // ---------------------------------------------------------
    console.log("Initializing global hamburger menu components...");

    try {
        if (!document.querySelector('meta[charset]') && !document.querySelector('meta[http-equiv="Content-Type"]')) {
            const metaCharset = document.createElement('meta');
            metaCharset.setAttribute('charset', 'utf-8');
            document.head.insertBefore(metaCharset, document.head.firstChild);
        }

        if (!document.querySelector('meta[name="viewport"]')) {
            const metaViewport = document.createElement('meta');
            metaViewport.name = 'viewport';
            metaViewport.content = 'width=device-width, initial-scale=1.0';
            document.head.appendChild(metaViewport);
        }
    } catch (e) {
        console.warn("Header injection skipped:", e);
    }

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
            height: 40px !important;
            background: #800000 !important; 
            z-index: 999999 !important;
            font-family: Arial, sans-serif !important;
            display: flex !important;
            align-items: center !important;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2) !important;
            padding: 0 10px !important;
            box-sizing: border-box !important;
        }
        .menu-trigger-btn {
            background: #600000 !important; 
            color: #fcfcf9 !important;     
            border: 1px solid #400000 !important;
            padding: 8px 16px !important;  
            border-radius: 4px !important; 
            cursor: pointer !important;
            font-weight: bold !important;
            font-size: 18px !important;
            display: flex !important;
            align-items: center !important;
            gap: 8px !important;
            line-height: 1 !important;
        }
        .menu-trigger-btn:hover { background: #400000 !important; }
        .menu-dropdown-content {
            display: none;
            position: absolute;
            top: 48px !important;
            left: 15px !important; 
            background: #ffffff !important;
            border: 1px solid #ddd !important;
            border-radius: 6px !important;
            width: 300px !important;
            box-shadow: 0 6px 20px rgba(0,0,0,0.15) !important;
            padding: 12px !important;
        }
        .menu-dropdown-content.active { display: block !important; }
        .menu-group-title {
            font-size: 13px !important;
            text-transform: uppercase !important;
            letter-spacing: 0.05em !important;
            color: #566573 !important;     
            margin: 10px 0 6px 4px !important;
            font-weight: 700 !important;
        }
        .menu-item-link {
            display: block !important;
            padding: 8px 10px !important;
            color: #222 !important;
            text-decoration: none !important;
            border-radius: 4px !important;
            font-size: 16px !important;
            font-weight: normal !important;
            transition: background 0.15s !important;
        }
        .menu-item-link:hover { 
            background: #f3f0e8 !important; 
            color: #800000 !important;      
        }
        .menu-divider { border-top: 1px solid #eee !important; margin: 8px 0 !important; }

        body {
            padding-top: 60px !important;
            max-width: none !important; 
            margin: 0 auto !important;
        }
        :target { scroll-margin-top: 60px !important; }
    `;
    document.head.appendChild(style);

    const isGitHubPages = window.location.hostname.includes("github.io");
    const repoPath = isGitHubPages ? "/SimHebrew-Concordance" : "";
    const baseUrl = `${window.location.origin}${repoPath}`;
    const wordPath = isGitHubPages ? '/SimHebrew-Concordance/' : '/';

    navWrapper.innerHTML = `
        <button class="menu-trigger-btn" onclick="document.getElementById('menu-dropdown').classList.toggle('active')">
            <span>☰</span><span class="menu-btn-text"> Menu</span>
        </button>
        <div id="menu-dropdown" class="menu-dropdown-content">
            <div class="menu-group-title">🎼 Scores and Contours</div>
            <a href="${baseUrl}/musicscores/index.html" class="menu-item-link">📁 Volume Index (929 Contours)</a>
            
            <div class="menu-divider"></div>
            
            <div class="menu-group-title">📐 Tropes & Ornaments</div>
            <a href="${baseUrl}/ornament_usage_by_pitch.html" class="menu-item-link">📊 Usage Matrix by Pitch</a>
            <a href="#" id="contextual-ornament-records" class="menu-item-link">🔍 Chapter Ornaments</a>
            
            <div class="menu-divider"></div>
            
            <div class="menu-group-title">🔤 Textual Lexicons</div>
            <a href="${baseUrl}/matrix.html" class="menu-item-link">⌨️ SimHebrew Word Matrix</a>
            <a href="${baseUrl}/gematria_verse_twins.html" class="menu-item-link">🔢 Gematria Verse Weights</a>
        </div>
    `;
    document.body.appendChild(navWrapper);

    // ---------------------------------------------------------
    // PHASE 2: CONDITIONAL GUARD (Determines screen type)
    // ---------------------------------------------------------
    const currentUrl = window.location.href;
    const isChapterScreen = currentUrl.includes('ornament_chapter.html');
    const isMatrixScreen = currentUrl.includes('_matrix.html');

    if (!isChapterScreen && !isMatrixScreen) {
        console.log("Standard screen verified. Exiting gloss initialization.");
        return;
    }

    // ---------------------------------------------------------
    // PHASE 3: INTERLINEAR GLOSS POPUPS (Only Matrix / Chapter)
    // ---------------------------------------------------------
    console.log("Matrix or Chapter screen detected. Resolving book & chapter context...");

    let cleanBook = "GENESIS";
    let chapterNum = "1";

    try {
        const urlParams = new URLSearchParams(window.location.search);
        const rawBookParam = urlParams.get('book');
        const rawChapterParam = urlParams.get('chapter');

        if (rawBookParam) {
            cleanBook = normalizeBookName(rawBookParam);
            if (rawChapterParam && rawChapterParam.match(/\d+/)) {
                chapterNum = parseInt(rawChapterParam.match(/\d+/), 10).toString();
            }
        } else {
            const path = window.location.pathname;
            const fileSegment = path.split('/').pop() || "";
            const matrixMatch = fileSegment.match(/^([A-Z0-9_]+)_(\d{3})_/i);

            if (matrixMatch) {
                cleanBook = normalizeBookName(matrixMatch[1]);
                chapterNum = parseInt(matrixMatch[2], 10).toString();
            } else {
                const parts = fileSegment.split('_');
                if (parts.length > 0 && parts[0]) {
                    cleanBook = normalizeBookName(parts[0]);
                }
            }
        }

        const displayTitle = formatDisplayTitle(cleanBook);
        console.log(`📍 [CONTEXT RESOLVED] Active Book: "${cleanBook}" (${displayTitle}), Chapter: ${chapterNum}`);

        const dynamicOrnamentUrl = `${baseUrl}/ornament_chapter.html?book=${encodeURIComponent(displayTitle)}&chapter=${chapterNum}`;
        const recordBtn = document.getElementById("contextual-ornament-records");
        if (recordBtn) {
            recordBtn.href = dynamicOrnamentUrl;
            recordBtn.innerHTML = " Chapter Ornaments: " + displayTitle + " " + chapterNum;
        }

        loadChapterInterlinear(cleanBook, chapterNum);

    } catch (e) {
        console.warn("Context tracking skipped outside contour paths:", e);
    }

    // ---------------------------------------------------------
    // CONTEXTUAL POPUP BOX SETUP
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

    /**
     * Contextual lookup resolver triggered on word selection / right-click
     */
    const resolveContextAddress = (e) => {
        const rawSelection = window.getSelection().toString().trim();
        if (rawSelection.length === 0) return;

        const cleanHebrew = stripHebrew(rawSelection);
        if (!cleanHebrew) return;

        e.preventDefault();

        let padBook = bookSequenceMap[cleanBook] || "01";
        let padCh = String(chapterNum || 1).padStart(3, '0');

        // Locate closest verse container element
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
        console.log(`🎯 [VERSE SCOPE BOUND] Scanning matrix for verse key prefix: "${currentVersePrefix}" with selection: "${cleanHebrew}"`);

        // 🍇 TIERED WORD RESOLVER LOGIC
        // Tier 1: Exact consonantal text match in current verse
        // Tier 2: Prefix-tolerant consonantal match in current verse
        // Tier 3: Exact consonantal text match in entire chapter
        // Tier 4: Prefix-tolerant match in entire chapter
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

        // Render popup inside Oxford Maroon container
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

    // Attach listeners
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

    window.addEventListener("click", (e) => {
        if (!navWrapper.contains(e.target)) {
            const drop = document.getElementById('menu-dropdown');
            if (drop) drop.classList.remove('active');
        }
    });
});
