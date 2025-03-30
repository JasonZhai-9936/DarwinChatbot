@echo off

echo Adding changes (excluding /assets folder)...

REM unstage anything in /assets just in case
git reset assets/

REM 
git add . ":!assets"

