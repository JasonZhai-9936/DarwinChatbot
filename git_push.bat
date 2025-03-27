@echo off
<<<<<<< HEAD
echo Adding changes (excluding /assets folder)...

REM unstage anything in /assets just in case
git reset assets/

REM 
git add . ":!assets"

echo Committing changes...
git add .gitignore
=======
echo Adding changes...
git add .

echo Committing changes...
>>>>>>> 4fa721c10edb1576b1df781e65b0a795d2f89dd3
git commit -m ".bat commit"

echo Pushing to remote...
git push

<<<<<<< HEAD
echo Finished.
=======
echo Finished
>>>>>>> 4fa721c10edb1576b1df781e65b0a795d2f89dd3
