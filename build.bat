Remove-Item -Path client\dist -Force -Recurse  
Remove-Item -Path client\build -Force -Recurse  

pyinstaller -F -n BattleBots --distpath client\dist --workpath client\build --icon client\app_icon.ico client\main.py
robocopy client\robots client\dist\robots
copy client\settings.json client\dist

pyinstaller -F -n BattleBots_Server --distpath server\dist --workpath server\build --icon client\app_icon.ico server\main.py