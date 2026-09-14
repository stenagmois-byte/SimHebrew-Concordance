document.addEventListener("DOMContentLoaded", () => {
    // ==========================================================================
    // ENCODING & VIEWPORT FIXES FOR LEGACY PAGES
    // ==========================================================================
    try {
        // 1. Force UTF-8 Encoding to stop characters from shattering into garbled text
        if (!document.querySelector('meta[charset]') && !document.querySelector('meta[http-equiv="Content-Type"]')) {
            const metaCharset = document.createElement('meta');
            metaCharset.setAttribute('charset', 'utf-8');
            document.head.insertBefore(metaCharset, document.head.firstChild);
        }

        // 2. Force normal page scaling
        if (!document.querySelector('meta[name="viewport"]')) {
            const metaViewport = document.createElement('meta');
            metaViewport.name = 'viewport';
            metaViewport.content = 'width=device-width, initial-scale=1.0';
            document.head.appendChild(metaViewport);
        }
    } catch (e) {
        console.warn("Header injection skipped:", e);
    }

    // 1. Create wrapper container for a full-width top bar
    const navWrapper = document.createElement("nav");
    navWrapper.id = "canonical-nav-menu";
    navWrapper.setAttribute("aria-label", "Tanach Music Concordance Navigator");

    // 2. Inject CSS (Switched completely to explicit PIXELS [px] to force large visibility)
    const style = document.createElement("style");
    style.textContent = `
        #canonical-nav-menu {
            position: fixed;
            top: 0;
            left: 0;
            width: 100% !important;
            height: 50px !important; /* Made thicker for clarity */
            background: #800000 !important; 
            z-index: 999999 !important; /* Keep above everything else */
            font-family: Arial, sans-serif !important;
            display: flex !important;
            align-items: center !important;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2) !important;
            padding: 0 15px !important;
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
            font-size: 18px !important; /* Explicit pixels overrides the tiny document shrink bug */
            display: flex !important;
            align-items: center !important;
            gap: 8px !important;
            line-height: 1 !important;
        }

        .menu-trigger-btn:hover {
            background: #400000 !important;
        }
        .menu-dropdown-content {
            display: none;
            position: absolute;
            top: 48px !important;
            left: 15px !important; 
            background: #ffffff !important;
            border: 1px solid #ddd !important;
            border-radius: 6px !important;
            width: 300px !important; /* Made slightly wider for text layout clearance */
            box-shadow: 0 6px 20px rgba(0,0,0,0.15) !important;
            padding: 12px !important;
        }
        .menu-dropdown-content.active { display: block !important; }
        
        .menu-group-title {
            font-size: 13px !important; /* Sharp, clean pixel setting */
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
            font-size: 16px !important; /* Large, highly visible item links */
            font-weight: normal !important;
            transition: background 0.15s !important;
        }
        .menu-item-link:hover { 
            background: #f3f0e8 !important; 
            color: #800000 !important;      
        }
        .menu-divider { border-top: 1px solid #eee !important; margin: 8px 0 !important; }

        /* Forces full-width real estate and clears room for the menu bar */
        body {
            padding-top: 60px !important;
            max-width: none !important; 
            margin: 0 auto !important;
        }
        :target {
            scroll-margin-top: 60px !important;
        }
    `;
    document.head.appendChild(style);

    // 3. DYNAMIC PATH CALCULATION (Handles Local vs GitHub Pages)
    const isGitHubPages = window.location.hostname.includes("github.io");
    const repoPath = isGitHubPages ? "/SimHebrew-Concordance" : "";
    const baseUrl = `${window.location.origin}${repoPath}`;
    const basePath = isGitHubPages ? '/SimHebrew-Concordance/' : '/';

    // 4. Build UI Markup (Swapped broken emojis for clean, universal text markers)
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

    // 5. ADVANCED CONTEXT RESOLVER (Handles Overlapping Book Names & Query Parameters)
    try {
        const path = window.location.pathname;
        const fullUrl = window.location.href.toUpperCase(); // Scans the absolute complete string parameters
        const fileSegment = path.split('/').pop() || "";

        // 1. COMPREHENSIVE DICTIONARY MAP (Expanded to include Major Prophets)
        const bookLookup = {
            "EXODUS": "Exodus", "LEVITICUS": "Leviticus", "NUMBERS": "Numbers", "DEUTERONOMY": "Deuteronomy",
            "JOSHUA": "Joshua", "JUDGES": "Judges", "PSALMS": "Psalms", "PROVERBS": "Proverbs", "JOB": "Job", 
            "EZEKIEL": "Ezekiel", "ISAIAH": "Isaiah", "JEREMIAH": "Jeremiah",
            "HOSEA": "Hosea", "JOEL": "Joel", "AMOS": "Amos", "OBADIAH": "Obadiah",
            "JONAH": "Jonah", "MICAH": "Micah", "NAHUM": "Nahum", "HABAKKUK": "Habakkuk",
            "ZEPHANIAH": "Zephaniah", "HAGGAI": "Haggai", "ZECHARIAH": "Zechariah", "MALACHI": "Malachi",
            "RUTH": "Ruth", "ESTHER": "Esther", "ECCLESIASTES": "Ecclesiastes", "LAMENTATIONS": "Lamentations",
            "SONG": "Song", "QOHELET": "Qohelet",
            "1_CHRONICLES": "1%20Chronicles", "2_CHRONICLES": "2%20Chronicles", 
            "1 CHRONICLES": "1%20Chronicles", "2 CHRONICLES": "2%20Chronicles",
            "1_KINGS": "1%20Kings", "2_KINGS": "2%20Kings", "1 KINGS": "1%20Kings", "2 KINGS": "2%20Kings",
            "1_SAMUEL": "1%20Samuel", "2_SAMUEL": "2%20Samuel", "1 SAMUEL": "1%20Samuel", "2 SAMUEL": "2%20Samuel",
            "NEHEMIAH": "Nehemiah", "EZRA": "Ezra", "DANIEL": "Daniel"
        };

        // 2. Default fallback variables
        let bookParam = "Genesis"; 
        let displayTitle = "Genesis";

        // 3. PRIORITY MATCHING: We check the filename first to avoid multi-book folder conflicts
        let foundMatch = false;
        const upperFile = fileSegment.toUpperCase();

        for (const key in bookLookup) {
            if (upperFile.includes(key)) {
                bookParam = bookLookup[key];
                displayTitle = decodeURIComponent(bookLookup[key]);
                foundMatch = true;
                break;
            }
        }

        // 4. SECONDARY MATCHING: If filename doesn't contain a key, we scan query parameters safely
        // Checking for strict bounded query formats like "=EZRA" prevents folder names from cross-contaminating keys
        if (!foundMatch) {
            for (const key in bookLookup) {
                if (fullUrl.includes("=" + key) || fullUrl.includes("_" + key) || fullUrl.includes(key + "_")) {
                    bookParam = bookLookup[key];
                    displayTitle = decodeURIComponent(bookLookup[key]);
                    break;
                }
            }
        }

        // 5. Extract and clean the chapter digits out of the location
        let chapterNum = "1";
        if (path.includes('_matrix')) {
            const chapterMatch = fileSegment.match(/\d+/);
            const rawChapter = chapterMatch ? chapterMatch[0] : "1";
            chapterNum = parseInt(rawChapter, 10).toString();
        } else {
            const urlParams = new URLSearchParams(window.location.search);
            const chapterQuery = urlParams.get('chapter') || urlParams.get('book'); // Checks backup selectors
            if (chapterQuery && chapterQuery.match(/\d+/)) {
                const chapterMatch = chapterQuery.match(/\d+/);
                chapterNum = parseInt(chapterMatch[0], 10).toString();
            }
        }

        // 6. Assemble the pristine final URL target
        const dynamicOrnamentUrl = `${baseUrl}/ornament_chapter.html?book=${bookParam}&chapter=${chapterNum}`;
        
        const recordBtn = document.getElementById("contextual-ornament-records");
        if (recordBtn) {
            recordBtn.href = dynamicOrnamentUrl;
            recordBtn.innerHTML = " Chapter Ornaments: " + displayTitle + " " + chapterNum;
        }
    } catch (e) {
        console.warn("Context tracking skipped outside contour paths:", e);
    }

    window.addEventListener("click", (e) => {
        if (!navWrapper.contains(e.target)) {
            const drop = document.getElementById('menu-dropdown');
            if (drop) drop.classList.remove('active');
        }
    });
});
document.addEventListener("DOMContentLoaded", () => {
    console.log("🚀 [DEBUG] Global navigation pipeline script successfully loaded!");

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

    let wordRootMap = null;

    // Fetch the Oracle-generated JSON dictionary file
    const isGitHubPages = window.location.hostname.includes('github.io');
    const jsonPath = isGitHubPages ? '/SimHebrew-Concordance/word_to_root.json' : '/word_to_root.json';
    const wordPath = isGitHubPages ? '/SimHebrew-Concordance/' : '/';
    fetch(jsonPath)
        .then(response => response.json())
        .then(data => {
            console.log("📥 [DEBUG] word_to_root.json successfully fetched from root directory.");
            wordRootMap = {};
            
            // ORACLE PATH REPAIR:
            // Drill down into the first element [0] of the results array to reach "items"
            if (data && data.results && data.results[0] && data.results[0].items) {
                const itemsList = data.results[0].items;
                
                itemsList.forEach(item => {
                    const decodedHebrew = decodeHtmlEntities(item.h);
                    wordRootMap[decodedHebrew] = item.r;
                });
                console.log(`✅ [DEBUG] Successfully mapped ${Object.keys(wordRootMap).length} dictionary entries into memory cache.`);
            } else {
                console.error("❌ [ERROR] JSON structure did not match expected Oracle format (results[0].items missing).");
            }
        })
        .catch(err => {
            console.error("❌ [ERROR] Failed to load or decode word_to_root.json layout template:", err);
        });
    // Main processing routine triggered on right-click or long-press
    const resolveContextAddress = (e) => {
        const rawSelection = window.getSelection().toString().trim();
        
        if (rawSelection.length > 0 && wordRootMap) {
            
            // 1. Strip vowels/accents first (leaving only consonants and Maqaf)
            const cleanHebrew = rawSelection.replace(/[\u0591-\u05BD\u05BF-\u05C7]/g, "").trim();
            
            // 2. Transliterate to Latin SimHebrew script! (e.g., "מזמור" -> "mzmur")
            const simHebrewKey = translateHebrewToSimHebrew(cleanHebrew);
            console.log(`🔤 [SIMHEBREW KEY] Converted selection to: "${simHebrewKey}"`);

            // 3. Query your simplified JSON using the pure Latin string key
            const rootCode = wordRootMap[simHebrewKey];

            if (rootCode) {
                e.preventDefault();
                console.log(`🎯 [MATCH FOUND] Found root code: "${rootCode}"`);

                // Structural anchor normalization (f -> T) for hashes
                const targetHash = rootCode.replace(/f/g, 'T');

                // Preserve 'f' for file prefix to prevent case collisions with 't' (Taf)
                const rawPrefix = rootCode.substring(0, 2); 
                const computedUrl = `${wordPath}${rawPrefix}.html#${targetHash}`;

                contextBox.innerHTML = `
                    <a href="${computedUrl}" style="color: #fff; text-decoration: none; font-size: 13px; font-family: system-ui, sans-serif; display: flex; align-items: center; gap: 6px;" target="_blank">
                        🔍 Concordance Root View: <strong>${targetHash}</strong>
                    </a>
`;

                const pageX = e.pageX || (e.touches ? e.touches.pageX : 0);
                const pageY = e.pageY || (e.touches ? e.touches.pageY : 0);
                
                contextBox.style.left = `${pageX + 10}px`;
                contextBox.style.top = `${pageY + 10}px`;
                contextBox.style.display = "block";
            } else {
                console.warn(`🔍 [NO MATCH] The SimHebrew key "${simHebrewKey}" does not exist in your JSON database.`);
            }
        }
    };

    // Attach standard context listeners
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

function stripHebrewAccents(text) {
    return text.replace(/[\u0591-\u05BD\u05BF-\u05C7]/g, "").trim();
}

function decodeHtmlEntities(str) {
    const txt = document.createElement("textarea");
    txt.innerHTML = str;
    return txt.value;
}
/**
 * Transliterates clean consonantal Hebrew text into your Latin SimHebrew equivalent.
 * Maps both standard and final (Sofit) variants to their correct keys.
 */
function translateHebrewToSimHebrew(text) {
    const translationTable = {
        // Standard Characters
        'א': 'a', 'ב': 'b', 'ג': 'g', 'ד': 'd', 'ה': 'h', 
        'ו': 'v', 'ז': 'z', 'ח': 'k', 'ט': 'T', 'י': 'i', 
        'כ': 'c', 'ל': 'l', 'מ': 'm', 'נ': 'n', 'ס': 's', 
        'ע': 'y', 'פ': 'p', 'צ': 'x', 'ק': 'q', 'ר': 'r', 
        'ש': 'w', 'ת': 't',
        
        // Final (Sofit) Characters
        'ך': 'c', 'ם': 'm', 'ן': 'n', 'ף': 'p', 'ץ': 'x'
    };

    let latinResult = "";
    for (let char of text) {
        // If it's a character in our dictionary table, convert it; 
        // Otherwise, keep it as-is (like the Maqaf hyphen '־')
        if (translationTable[char]) {
            latinResult += translationTable[char];
        } else {
            latinResult += char;
        }
    }
    return latinResult;
}

