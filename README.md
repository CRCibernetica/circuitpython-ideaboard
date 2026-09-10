# CRCibernetica IdeaBoard
[The documentation has moved to the WIKI!](https://github.com/CRCibernetica/circuitpython-ideaboard/wiki)

The IdeaBoard is an educational robotics development board created by CRCibernetica.com in Costa Rica.

## AI helpers for students
The `skills/` folder has markdown reference documents to paste into an AI assistant so it can write CircuitPython for the IdeaBoard, IdeaSense Explorer and SumoBot v2. See `skills/README.md`.

## Command-line access
The IdeaBoard has no USB drive; `tools/ibserial.py` lists, copies, and runs files on the board over the serial REPL from any OS (needs only Python and `pyserial`). Run it with no arguments for the commands.
