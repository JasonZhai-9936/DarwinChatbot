@echo off
echo Adding changes...
git add .

echo Committing changes...
git commit -m "batch commit"

echo Pushing to remote...
git push

echo Done!
pause
