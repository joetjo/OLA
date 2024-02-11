
# Obsidian Launcher Assistant

| ![splash](res/splash-small.png "Last sessions launched tab") | Use Obsidian https://obsidian.md/ to manage your tools and mostly games :-) you are using Use tag to classify them within obsidian |
|-|--|

> WARNING : usage without an "already done setup" may not work at all. This is done for private use and shared because there is nothing confidential in it.
> Mandatory tag to use in Obsidian are also not documented "here" ( globally ``#PLAY/IN_PROGRESS`` and ``#TYPE/<type>`` )

Then this Assistant will help you to
- start usual stuff
- generate reports from obsidian

It includes my previous project:
- SBSGL Simple But Smart Game Launcher
- Markdown Helpers ( Generate md report from markdown file hierarchy like Obsidian vault )

Why not an obsidian plugin ?
- because obsidian is a web application that do not deal in the bast way to local process execution for security concerns.
Python allows to do more easily.
and Obsidian is a great tool ! but it should do what it handles the best.

# Issues :
- No user documentation at all currently 
- Fresh start without existing SBSGL / Markdown config will probably failed 
- Emulator not managed ( LEGUI for example - popup menu added by empty, is this the right way to do it )
- Excluded game not managed ( tab added but not implemented )
- Stop scanning game while report generation is in progress ( access to VAULT my be invalid )
- About panel and third party references

_Version 2024.02.11a:_ 

![ola Assistant](screen1.png "Obsidian file tag 'In Progress'")
![ola session](screen2.png "Last sessions launched tab")

# Dev corner  

Not documented currently

## Interesting external Sources :

- PySide6 tutorial : https://www.pythonguis.com/pyside6-tutorial/
- Thread : https://www.pythonguis.com/tutorials/multithreading-pyside6-applications-qthreadpool/
- Process : https://www.pythonguis.com/tutorials/pyside6-qprocess-external-programs/
- style: https://doc.qt.io/qt-6/stylesheet-reference.html
- ---
- Logging : https://docs.pyhon.org/3/howto/logging.html ( detail : https://docs.python.org/3/library/logging.html )
---
- resources : https://icons8.com/icons
---
Obsidian link:
https://help.obsidian.md/Extending+Obsidian/Obsidian+URI

``obsidian://open?path=%2Fhome%2Fuser%2Fmy%20vault%2Fpath%2Fto%2Fmy%20note``

This will look for any vault that contains the path /home/user/my vault/path/to/my note. Then, the rest of the path is passed to the file parameter. For example, if a vault exists at /home/user/my vault, then this would be equivalent to file parameter set to path/to/my note.