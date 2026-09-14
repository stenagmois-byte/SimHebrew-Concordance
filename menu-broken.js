// =========================================================================
// 1. DATA TRANSFORMATION MODULES (Isolated Deterministic Utilities)
// =========================================================================

/**
 * Transliterates clean consonantal Hebrew text into Latin SimHebrew equivalents.
 * Acts as a precise 1:1 character translation table.
 */
function translateHebrewToSimHebrew(text) {
    const translationTable = {
        'א': 'a', 'ב': 'b', 'ג': 'g', 'ד': 'd', 'ה': 'h', 
        'ו': 'v', 'ז': 'z', 'ח': 'k', 'ט': 'T', 'י': 'i', 
        'כ': 'c', 'ל': 'l', 'מ': 'm', 'נ': 'n', 'ס': 's', 
        'ע': 'y', 'פ': 'p', 'צ': 'x', 'ק': 'q', 'ר': 'r', 
        'ש': 'w', 'ת': 't',
        'ך': 'c', 'ם': 'm', 'ן': 'n', 'ף': 'p', 'ץ': 'x'
    };

    let latinResult = "";
    for (let char of text) {
        latinResult += translationTable[char] || char; // Preserves Maqaf '־' or unmapped markers
    }
    return latinResult;
}

/**
 * Strips all te'amim (accents) and niqqud (vowels).
 * Safely preserves the Maqaf hyphen to maintain database alignment.
 */
function stripHebrewAccents(text) {
    return text.replace(/[\u0591-\u05BD\u05BF-\u05C7]/g, "").trim();
}

/**
 * Decodes Oracle VARCHAR2 HTML entity string representations back into literal glyphs.
 */
function decodeHtmlEntities(str) {
    const txt = document.createElement("textarea");
    txt.innerHTML = str;
    return txt.value;
}


// =========================================================================
// 2. MAIN EXECUTION PIPELINE (Triggers once browser finishes DOM assembly)
// =========================================================================
document.addEventListener("DOMContentLoaded", () => {
    console.log("🚀 [SYSTEM INIT] menu.js loaded smoothly.");

    // ---------------------------------------------------------------------
    // A. ENVIRONMENT PATH RESOLUTION (Calculated exactly once)
    // ---------------------------------------------------------------------
    const isGitHubPages = window.location.hostname.includes('github.io');
    const basePath = isGitHubPages ? '/SimHebrew-Concordance/' : '/';
    const baseUrl = `${window.location.origin}${basePath}`;

    console.log(`🌍 [PATH CONFIG] Base environment reference anchor point: ${baseUrl}`);

    // ---------------------------------------------------------------------
    // B. UI STYLE INJECTION MAPPING
    // ---------------------------------------------------------------------
    const style = document.createElement("style");
    style.textContent = `
        #oracle-root-linker {
            display: none;
            position: absolute;
            z-index: 100000;
            background: #111111;
            border: 2px solid #d4af37;
            border-radius: 6px;
            padding: 8px 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.5);
        }
        #canonical-nav-menu {
            position: fixed;
            top: 15px;
            right: 15px;
            z-index: 99999;
            font-family: system-ui, -apple-system, sans-serif;
        }
        .menu-trigger-btn {
            background: rgba(17, 17, 17, 0.75);
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            color: #fff;
            border: 1px solid rgba(212, 175, 55, 0.4);
            padding: 10px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 600;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .menu-dropdown-content {
            display: none;
            position: absolute;
            top: 45px;
            right: 0;
            background: #ffffff;
            border: 1px solid #dddddd;
            border-radius: 8px;
            width: 280px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.15);
            padding: 12px;
        }
        .menu-dropdown-content.active { display: block; }
        .menu-group-title {
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #666;
            margin: 8px 0 4px 4px;
            font-weight: 700;
        }
        .menu-item-link {
            display: block;
            padding: 8px;
            color: #222;
            text-decoration: none;
            border-radius: 4px;
            font-size: 0.9rem;
            transition: background 0.2s;
        }
        .menu-item-link:hover { background: #f5f5f7; color: #0066cc; }
        .menu-divider { border-top: 1px solid #eee; margin: 8px 0; }

        /* SCROLL MARGIN TARGET OFFSET RULE */
        :target {
            scroll-margin-top: 75px !important;
        }
    `;
    document.head.appendChild(style);

    // ---------------------------------------------------------------------
    // C. DOM STRUCTURE GENERATION
    // ---------------------------------------------------------------------
    const contextBox = document.createElement("div");
    contextBox.id = "oracle-root-linker";
    document.body.appendChild(contextBox);

    const navWrapper = document.createElement("nav");
    navWrapper.id = "canonical-nav-menu";
    navWrapper.innerHTML = `
        <button class="menu-trigger-btn" onclick="document.getElementById('menu-dropdown').classList.toggle('active')">
            \uD83C\uDFB5 Concordance Menu
        </button>
        <div id="menu-dropdown" class="menu-dropdown-content">
            <div class="menu-group-title">🎼 Score Maps</div>
            <a href="${baseUrl}musicscores/index.html" class="menu-item-link">\uD83D\uDCC1 Volume Index (929 Contours)</a>
            <div class="menu-divider"></div>
            <div class="menu-group-title">📐 Tropes & Ornaments</div>
            <a href="${baseUrl}ornament_usage_by_pitch.html" class="menu-item-link">\uD83D\uDCCA Usage Matrix by Pitch</a>
            <a href="#" id="contextual-ornament-records" class="menu-item-link">\uD83D\uDCD6 View Chapter Ornaments</a>
            <div class="menu-divider"></div>
            <div class="menu-group-title">🔤 Textual Lexicons</div>
            <a href="${baseUrl}matrix.html" class="menu-item-link">\u2328\uFE0F SimHebrew Word Matrix</a>
            <a href="${baseUrl}gematria_verse_twins.html" class="menu-item-link">\uD83D\uDD22 Gematria Verse Weights</a>
        </div>
    `;
    document.body.appendChild(navWrapper);

    // ---------------------------------------------------------------------
    // D. DICTIONARY LOOKUP FETCHING & MEMORY CACHING
    // ---------------------------------------------------------------------
    let wordRootMap = null;

    fetch(`${baseUrl}word_to_root.json`)
        .then(response => {
            if (!response.ok) throw new Error(`HTTP error status: ${response.status}`);
            return response.json();
        })
        .then(data => {
            wordRootMap = {};
            if (data?.results?.items) {
                data.results.items.forEach(item => {
                    wordRootMap[item.h] = item.r;
                });
                console.log(`✅ [CACHE INIT] Successfully mapped ${Object.keys(wordRootMap).length} dictionary keys.`);
            }
        })
        .catch(err => console.error("❌ [CACHE FATAL] Initialization aborted:", err));

    // ---------------------------------------------------------------------
    // E. CURRENT ACTIVE LOCATION TRACKING
    // ---------------------------------------------------------------------
    try {
        const match = window.location.pathname.match(/\/([^/]+)\/([^/.]+)\.html$/); 
        if (match) {
            const bookName = match[1];
            const chapterNum = match[2].replace(/^\D+/g, ''); 
            
            const recordBtn = document.getElementById("contextual-ornament-records");
            if (recordBtn) {
                recordBtn.href = `${baseUrl}ornament_chapter.html?book=${bookName}&chapter=${chapterNum}`;
                recordBtn.innerHTML = `\uD83D\uDCD6 Trope Study: ${bookName} ${chapterNum}`;
            }
        }
    } catch (e) {
        console.warn("[TRAFFIC CONTEXT] Page outside sequential contour path maps.");
    }

    // ---------------------------------------------------------------------
    // F. SELECTION ADDRESS ROUTING EVENT HANDLER
    // ---------------------------------------------------------------------
    const resolveContextAddress = (e) => {
        const rawSelection = window.getSelection().toString().trim();
        
        if (rawSelection.length > 0 && wordRootMap) {
            const cleanHebrew = stripHebrewAccents(rawSelection);
            const simHebrewKey = translateHebrewToSimHebrew(cleanHebrew);
            const rootCode = wordRootMap[simHebrewKey];

            if (rootCode) {
                e.preventDefault();

                const targetHash = rootCode.replace(/f/g, 'T');
                const rawPrefix = rootCode.substring(0, 2); 
                const computedUrl = `${baseUrl}${rawPrefix}.html#${targetHash}`;

                contextBox.innerHTML = `
                    <a href="${computedUrl}" style="color: #ffffff; text-decoration: none; font-size: 13px; font-family: system-ui, sans-serif; display: flex; align-items: center; gap: 6px;" target="_blank">
                        🔍 Concordance Root View: <strong style="color: #d4af37;">${targetHash}</strong>
                    </a>
                `;

                const pageX = e.pageX || (e.touches ? e.touches.pageX : 0);
                const pageY = e.pageY || (e.touches ? e.touches.pageY : 0);
                
                contextBox.style.left = `${pageX + 10}px`;
                contextBox.style.top = `${pageY + 10}px`;
                contextBox.style.display = "block";
            }
        }
    };

    // ---------------------------------------------------------------------
    // G. SYSTEM INPUT EVENT LISTENERS
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

