1. The Unicode Inversion Trap
In traditional Masoretic grammar and manuscripts:
In the 21 Prose Books: The accent called Zarqa (זַרְקָא) is strictly postpositive. Because Hebrew reads right-to-left, "postpositive" means it must appear at the end of the word—hanging over the far left edge of the final consonant (or off its left shoulder)
.
In the 3 Poetic Books (Sifrei Emet): The mark called Tsinnor (צִנּוֹר) or Tsinnorit (צִנּוֹרִית)—sometimes called poetic zarqa—is centered directly over the consonant of the accented syllable
.
When the Unicode Consortium originally encoded Hebrew cantillation in the 1990s, they swapped the behavior and names
:
U+0598 was given the name HEBREW ACCENT ZARQA, but Unicode assigned it Canonical Combining Class 230 (Above—centered over the letter)
.
U+05AE was given the name HEBREW ACCENT ZINOR, but Unicode assigned it Canonical Combining Class 228 (Above_Left—postpositive on the left)
.
Because the Unicode Consortium operates under a strict Character Name Stability Policy, once a character name is published, it can never be changed or renamed. As a result:
U+0598 is permanently stuck with the name ZARQA, even though typographically and historically its centered glyph belongs to poetic tsinnorit
.
U+05AE is permanently stuck with the name ZINOR, even though typographically its left-aligned postpositive placement is what prose zarqa actually requires
.
The Unicode standard eventually added alias annotations to the specification (acknowledging 0598 = tsinorit, zinor), but digital databases (including the Westminster Leningrad Codex, Michigan-Claremont, and tanach.us) had to make tricky engineering choices about which code point to store for which accent.
2. Why You Can't Reproduce It in the Dialogue Box
The reason it is impossible to see the difference in a standard browser text box or chat input comes down to font engines:
Standard operating system UI fonts (Segoe UI on Windows, SF Pro on macOS, Roboto on Android) only have basic Hebrew alphabet support. They lack the advanced OpenType GPOS (Glyph Positioning) anchor tables needed for biblical diacritics.
In a plain dialogue box, the browser's text shaper treats both U+0598 and U+05AE as generic non-spacing combining marks. It simply averages their bounding boxes and dumps both glyphs smack in the center of the letter (or awkwardly collides them with the consonant), erasing the distinction between centered and postpositive-left.
Only specialized biblical fonts with full Masoretic OpenType kerning—like SBL Hebrew, Ezra SIL, or Taamey Frank CL—will actually shift U+05AE over to the far left shoulder of the Alef while keeping U+0598 dead-center.
3. How This Impacts the Music and Your Concordance
In your Genesis publication (Brief Notes on the Music, pp. 272–273, 275), you documented this exact anomaly
:
זַרְקָא zarqa** (U+0598 / 1432): a turn over the centre of the letter, with musical contour formula (-1+1-0), confined to poetry
. In Aleppo, the prose occurrences drop to zero
.
צִנּוֹר tsinnor (U+05AE / 1454): a turn over the left side of the letter, with musical contour formula (-0-1+1)
.
Because the deciphering key assigns different melodic ornaments to the centered turn versus the postpositive left turn, this is one of the rare places where Unicode’s swapped naming could cause genuine musical confusion if someone trusts the character names rather than the actual manuscript placement
!
In your HTML table for ornament_usage_by_pitch.html, maintaining them as two distinct rows:
TSINNOR (U+05AE / א֮) — dominant across the canon (1,204 occurrences)
ZARQA (U+0598 / א֘) — poetic centered turn (144 occurrences)
...preserves the exact distinction that Unicode's naming convention confused
.