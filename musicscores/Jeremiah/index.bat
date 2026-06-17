@echo off
setlocal enabledelayedexpansion

echo ^<html^> > index.html
echo ^<head^>^<meta charset="UTF-8"^>^<title^>Index^</title^>^</head^> >> index.html
echo ^<body^> >> index.html

for %%I in (.) do set "CurrentDir=%%~nxI"
echo ^<h1^>%CurrentDir%^</h1^> >> index.html

echo ^<h2^>MSCZ^</h2^> >> index.html
echo ^<ul^> >> index.html

for %%f in (*.mscz) do (
    set "name=%%~nf"
    set "chap=!name:~-3!"
    echo ^<li^>^<a href="%%f" download^>Chapter !chap!^</a^>^</li^> >> index.html
)

echo ^</ul^> >> index.html
echo ^<h2^>Compressed MusicXML (.mxl)^</h2^> >> index.html
echo ^<ul^> >> index.html

for %%f in (*.mxl) do (
    set "name=%%~nf"
    set "chap=!name:~-3!"
    echo ^<li^>^<a href="%%f" download^>Chapter !chap!^</a^>^</li^> >> index.html
)

echo ^</ul^> >> index.html
echo ^<p^>^<a href="../index.html"^>Back^</a^>^</p^> >> index.html

echo ^</body^>^</html^> >> index.html
