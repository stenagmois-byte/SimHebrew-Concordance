@echo off
setlocal enabledelayedexpansion

echo ^<html^> > index.html
echo ^<head^>^<meta charset="UTF-8"^>^<title^>Index^</title^>^</head^> >> index.html
echo ^<body^> >> index.html

for %%I in (.) do set "CurrentDir=%%~nxI"
echo ^<h1^>%CurrentDir%^</h1^> >> index.html

echo ^<h2^>Python scripts^</h2^> >> index.html
echo ^<ul^> >> index.html

for %%f in (*.py) do (
    set "name=%%~nf"
    echo ^<li^>^<a href="%%f" download^>!name!^</a^>^</li^> >> index.html
)

echo ^</ul^> >> index.html
echo ^<p^>^<a href="../index.html"^>Back^</a^>^</p^> >> index.html

echo ^</body^>^</html^> >> index.html
