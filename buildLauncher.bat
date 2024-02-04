REM pip install pyinstaller
pyinstaller --onefile --icon=joystick.ico ola.py --add-data "./base;./base"  --add-data "./resources;./resources" --add-data "./res;./res"  --add-data "./diskAnalyser;./diskAnalyser"  --add-data "./markdownHelper;./markdownHelper"  --add-data "./sbsgl;./sbsgl" --hidden-import=PySide6 --hidden-import=psutil  --hidden-import=json  --hidden-import=logging
move dist\ola.exe dist\ola-debug.exe
pyinstaller --onefile --noconsole --icon=joystick.ico ola.py --add-data "./base;./base"  --add-data "./resources;./resources" --add-data "./res;./res"  --add-data "./diskAnalyser;./diskAnalyser"  --add-data "./markdownHelper;./markdownHelper"  --add-data "./sbsgl;./sbsgl" --hidden-import=PySide6 --hidden-import=psutil  --hidden-import=json  --hidden-import=logging
REM