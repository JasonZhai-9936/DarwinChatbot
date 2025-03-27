@echo off
echo Adding changes (excluding /assets folder)...

REM unstage anything in /assets just in case
git reset assets/

REM 
git add . ":!assets"

echo Committing changes...
git add .gitignore
git commit -m ".bat commit"

echo Pushing to remote...
git push

echo Finished.
