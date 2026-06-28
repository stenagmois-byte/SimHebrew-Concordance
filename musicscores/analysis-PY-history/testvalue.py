# Let's test the text parsing logic on the specific string provided by the user.
# The user's string is: "29.1 בַּשָּׁנָה֙"
text_val = "29.1 בַּשָּׁנָה֙"
words = text_val.split()
print("Words split result:", words)
if words:
    first_token = words[0] # Note: the script had a typo `first_token = words` which evaluates to the list!
    print("First token:", first_token)
    print("'.' in first_token:", "." in first_token)
    print("any dig in first_token:", any(char.isdigit() for char in first_token))
