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
            padding-top: 65px !important;
            max-width: none !important; 
            margin: 0 auto !important;
        }
    `;
    document.head.appendChild(style);

    // 3. DYNAMIC PATH CALCULATION (Handles Local vs GitHub Pages)
    const isGitHubPages = window.location.hostname.includes("github.io");
    const repoPath = isGitHubPages ? "/SimHebrew-Concordance" : "";
    const baseUrl = `${window.location.origin}${repoPath}`;

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

    // 5. ADVANCED CONTEXT RESOLVER
    try {
        const path = window.location.pathname;
        if (path.includes('_matrix')) {
            const fileSegment = path.split('/').pop() || "";
            const chapterMatch = fileSegment.match(/\d+/);
            const rawChapter = chapterMatch ? chapterMatch[0] : "1";
            const chapterNum = parseInt(rawChapter, 10).toString();

            const bookLookup = {
                "HOSEA_": "Hosea", "JOEL_": "Joel", "AMOS_": "Amos", "OBADIAH_": "Obadiah",
                "JONAH_": "Jonah", "MICAH_": "Micah", "NAHUM_": "Nahum", "HABAKKUK_": "Habakkuk",
                "ZEPHANIAH_": "Zephaniah", "HAGGAI_": "Haggai", "ZECHARIAH_": "Zechariah", "MALACHI_": "Malachi",
                "RUTH_": "Ruth", "ESTHER_": "Esther", "ECCLESIASTES_": "Ecclesiastes", "LAMENTATIONS_": "Lamentations",
                "SONG_": "Song%20of%20Songs", "1_CHRONICLES_": "1%20Chronicles", "2_CHRONICLES_": "2%20Chronicles",
                "1_KINGS_": "1%20Kings", "2_KINGS_": "2%20Kings", "1_SAMUEL_": "1%20Samuel", "2_SAMUEL_": "2%20Samuel",
                "DANIEL_": "Daniel", "EZRA_": "Ezra", "NEHEMIAH_": "Nehemiah"
            };

            let bookParam = "Genesis"; 
            let displayTitle = "Genesis";
            const upperFile = fileSegment.toUpperCase();

            for (const key in bookLookup) {
                if (upperFile.startsWith(key)) {
                    bookParam = bookLookup[key];
                    displayTitle = decodeURIComponent(bookLookup[key]);
                    break;
                }
            }

            const dynamicOrnamentUrl = `${baseUrl}/ornament_chapter.html?book=${bookParam}&chapter=${chapterNum}`;
            const recordBtn = document.getElementById("contextual-ornament-records");
            if (recordBtn) {
                recordBtn.href = dynamicOrnamentUrl;
                recordBtn.innerHTML = " Chapter Ornaments: " + displayTitle + " " + chapterNum;
            }
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
