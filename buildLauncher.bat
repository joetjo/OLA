@ECHO OFF
REM pip install pyinstaller
pyinstaller --onefile --icon=joystick.ico ola-sbsgl-debug.py --add-data "./ola;./ola" --add-data "./base;./base"  --add-data "./resources;./resources" --add-data "./res;./res"  --add-data "./diskAnalyser;./diskAnalyser"  --add-data "./markdownHelper;./markdownHelper"  --add-data "./sbsgl;./sbsgl" --hidden-import=PySide6 --hidden-import=psutil  --hidden-import=json  --hidden-import=logging
pyinstaller --onefile --noconsole --icon=joystick.ico ola-sbsgl.py --add-data "./ola;./ola" --add-data "./base;./base"  --add-data "./resources;./resources" --add-data "./res;./res"  --add-data "./diskAnalyser;./diskAnalyser"  --add-data "./markdownHelper;./markdownHelper"  --add-data "./sbsgl;./sbsgl" --hidden-import=PySide6 --hidden-import=psutil  --hidden-import=json  --hidden-import=logging
REM
echo ---
echo Generation DONE
echo ---
echo "Dont forget to tag: git tag <tag> select tag with PyCharm on push Window."