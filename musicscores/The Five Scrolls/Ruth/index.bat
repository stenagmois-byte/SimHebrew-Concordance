@echo off
setlocal enabledelayedexpansion

echo ^<html^> > index.html
echo ^<head^>^<meta charset="UTF-8"^>^<title^>Index^</title^>^</head^> >> index.html
echo ^<body^> >> index.html

echo ^<h1^>Ruth^</h1^> >> index.html
echo ^<ul^> >> index.html

for %%f in (*.mscz) do (
    set "name=%%~nf"
    set "chap=!name:~-3!"
    echo ^<li^>^<a href="%%f"^>Ruth !chap!^</a^>^</li^> >> index.html
)

echo ^</ul^> >> index.html
echo ^<p^>^<a href="../index.html"^>Back^</a^>^</p^> >> index.html

echo ^</body^>^</html^> >> index.html
