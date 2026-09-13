import os

# List all files and directories in the current workspace
files = os.listdir('.')
for file in files:
    print(file)
