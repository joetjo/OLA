REM pip install pyinstaller
pyinstaller --onefile fakegame.py

copy dist\fakegame.exe jeux\games\Borderland2\Launcher.exe
copy dist\fakegame.exe jeux\games\Borderland2\borderland2.exe
copy dist\fakegame.exe jeux\games\MassEffectDefinitiveAndLastEdition\ME123.exe
copy dist\fakegame.exe jeux\games\TheWitcher3\tw3
copy dist\fakegame.exe jeux\games\AssassinsCreed42\AssassinsCreeds42.exe
copy dist\fakegame.exe jeux\games\TheWitcher2\tw2
copy dist\fakegame.exe jeux\games\RoseOfSegunda\renpy.exe
copy dist\fakegame.exe jeux\games\Control\Control.exe
copy dist\fakegame.exe jeux\games\Dos2\dos2.exe
copy dist\fakegame.exe jeux\games\ALauncher.exe
copy dist\fakegame.exe platforms\steam.exe
copy dist\fakegame.exe platforms\GalaxyClient.exe
copy dist\fakegame.exe platforms\EpicGamesLauncher.exe
copy dist\fakegame.exe platforms\upc.exe
copy dist\fakegame.exe platforms\itch.exe
copy dist\fakegame.exe platforms\Origin.exe

