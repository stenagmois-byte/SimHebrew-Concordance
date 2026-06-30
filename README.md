# SimHebrew Concordance & The Music of the Bible

An open-source database and toolkit dedicated to reconstructing the comprehensive musical footprint of the Hebrew Bible text.

## 🚀 Getting Started
1. **Browse the Concordance**: Open `index.html` via GitHub Pages to explore the [Letter-Pair Root Matrix](https://stenagmois-byte.github.io/SimHebrew-Concordance/).
2. **Analyze the Melodies**: Clone the repository to access the full `/Music Scores` directory containing 929 chapter files in MuseScore (`.mscz`) and analysis-ready `.xml` formats.
3. **Run Scripts**: Review the python workspace to experiment with sequence and motif parsing algorithms.

## 🎓 Academic Endorsements
> "Bob MacDonald offers us here a controversial but extensively considered answer, psalm by psalm, to the familiar question: 'So what did the music of the ancient psalms sound like?' This is a bold and engaging work."
> — *Professor Susan Gillingham DD, Emeritus Professor of the Hebrew Bible, Worcester College, Oxford*

## 📜 License
This project is open-source. Please attribute data and musical reconstructions to the 18-volume series *The Music of the Bible* (Bob MacDonald, 2026).

These pages contain a full concordance to the Tanach, the five books of Moses (torh) Instruction / Law, the prophets (nbiaim) from Joshua to Malachi, and the writings (ctubim) from Psalms to Chronicles. I update the pages occasionally. Updates are complete as of April 29, 2026.

In these pages every word in the Tanach is present and every place that it used. In the full set of posts referenced on the Index page, each word is listed with:
its root.
its semantic domain, (a hierarchical categorizing of every root and word to help distinguish homonyms and other word differences for words with the same root consonants).
the word in SimHebrew. (SimHebrew is essentially a slight vocalization for the unpointed text.)
the vowel pattern for this word-form (fit the SimHebrew consonants into the blanks in the vowel pattern).
schwa, ':',
hatef-segol, ':e', 
hatef-patah, ':a-', 
hatef-qamats, ':a',
hiriq, 'i',
tsere, 'ei',
segol, 'e'.
patah, 'a-',
qamats, 'a',
holam, 'o',
qubuts, 'u'.
the count of the occurrences of this root and word-form.
the fully pointed word in square text, so you can sing the text.
the gloss in my translation, 2006-2025.
the immediately preceding word in the verse to see the pairs of words used together.
and every reference where that gloss and preceding root is used, book, chapter, verse, and Hebrew word sequence.
The sequence of each page is by root in the SimHebrew Letter sequence. The Latin letters can be read left to right and correspond each in its place to the square text read from right to left. Within the list for each root, the sequence is further subdivided by Semantic Domain. Within Domain, the sequence is then by SimHebrew word. References are in the traditional order of Tanach.

Each word appears only once in the concordance. I use a cascading rule to determine the root under which the word appears: first priority is the tri-literal root from which the word is derived, stand alone pronouns may appear by themselves. A word that is a combination of prefix + suffix is listed under the prefix. Note then that the sections on individual prefixes will contain only these words that are otherwise without a main root.

Note: The following chapters and verses are Aramaic. Everything else is Hebrew. Daniel, chapter 2 from verse 4 on, chapters 3, 4, 5, 6, and 7, Ezra chapter 4 from verse 8 on, chapters 5, and 6 where the verse is less than 18, and chapter 7, verses between 12 and 26, and Jeremiah chapter 10 verse 10.

In the Glossary page (available here glossary.html), English users may track down the usage of a gloss and the corresponding Hebrew root(s) used for this gloss. The sequence of this table is by Domain, and within Domain, the SimHebrew word. 

My name is Bob MacDonald. I am a retired musician, business owner and database designer. I translated the Hebrew Scriptures beginning at age 60 in the period from 2006 to 2025. Many people helped me learn in this period: Gidi Nashon of Congregation Emanu-El, Victoria BC, provided my first steps in Hebrew. Jonathan Orr-Stav answered many questions and we continue our collaboration with the SimHebrew Bible. Many fellows at the University of Victoria Centre for Studies in Religion and Society were supportive of my learning Hebrew and taught me something of how to avoid conversational pitfalls. Susan Gillingham of Oxford and David Mitchell of Brussels introduced me to the music in 2010 and along with James McGrath of Butler University have been very supportive of my subsequent efforts.

The history of my translation and the books that resulted are on my blog, Dust. All the content in this concordance and the SimHebrew Bible are generated from my translation database. I began my translation to restore recurring sounds that are evident as a technique in the poetry of the Psalms through the use of recurring Hebrew roots. Secondarily, the translation was extended to the whole of the Tanach for the sake of the music of the accents. At every stage, considerable care is taken to preserve similar English glosses for recurring similar words in the Tanach. 

Meaning?

A note on the commonplace phrase 'literal meaning'. You will understand that words have usage. They do not have meaning. I avoid both the idea of literal and of meaning as if there were just one sense that can be drawn from a text. This text is a word about our humanity to us. It is frequently unpleasant. 
We can distinguish three phrases. 
What does it say? 
What sense do I draw from it today? and 
What does it mean?
The mean is the mid-value of a series of numbers. It does not tell us about the series. It is mean in the sense of stingy with information. Today I may draw a sense from the text for me. Tomorrow I will hear it in another sense, perhaps for many of us or on behalf of someone else. Meaning, in other words, has its own context. Judgment may mean satisfaction to me today and fear tomorrow.

My concentration as a translator has been to deliver the English as close to the Hebrew as I was able, to reflect what the text says. I have sometimes loosened the grip of my algorithms on my thought process. And there are times when my wording is too awkward or I have omitted a grammatical issue that I should not have left out. I will fix what I find. There are times when I cannot find words.

Music Scores, Data extracts and analysis
These are in the directory .\musicscores they are organized by volume of the published books. User requires Musescore to read them.
Although the database is Oracle, there are some direct extracts that allow for pattern recognition in a simple spreadsheet file.
