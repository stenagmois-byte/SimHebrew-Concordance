@echo off
setlocal
pushd "%~dp0"
python "%~dp0epubcompare.py" %*
set "RESULT=%ERRORLEVEL%"
if not "%RESULT%"=="0" (
  echo.
  echo Usage: epubcompare.bat "older.epub" "newer.epub" [--output "report.html"]
  echo Put quotes around each full path when it contains spaces.
  echo With no file paths, the two newest EPUBs in this folder are compared.
)
echo.
if "%~1"=="" pause
popd
exit /b %RESULT%
