import json

# 1. Build the internal analysis as a perfectly clean, normal dictionary
internal_analysis = {
    "verse": "Proverbs 8:23",
    "hebrew_text": "מֵ֭עוֹלָם נִסַּ֥כְתִּי מֵרֹ֗אשׁ מִקַּדְמֵי־אָֽרֶץ",
    "tonal_contour": {
        "description": "A three-note descending scale executing a musical and theological pouring out.",
        "scale_progression": ["Mediant", "Supertonic", "Tonic"]
    },
    "concordant_translation": "From everlasting I have offered libation from the beginning..."
}

# 2. Package it into the official OpenAI Chat Fine-Tuning Spec
# json.dumps() handles all the escaping and \n insertions for you!
training_line = {
    "messages": [
        {
            "role": "system", 
            "content": "You are an AI textual architect analyzing the Hebrew Bible as a musical score."
        },
        {
            "role": "user", 
            "content": "Analyze Proverbs 8:23"
        },
        {
            "role": "assistant", 
            "content": json.dumps(internal_analysis, indent=2, ensure_ascii=False)
        }
    ]
}

# 3. Write it out to your file. It will look exactly like the tricky spec!
print(json.dumps(training_line, ensure_ascii=False))
