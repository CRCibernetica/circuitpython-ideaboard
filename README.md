# CRCibernetica IdeaBoard
[The documentation has moved to the WIKI!](https://github.com/CRCibernetica/circuitpython-ideaboard/wiki)

The IdeaBoard is an educational robotics development board created by CRCibernetica.com in Costa Rica.

## Working with an AI assistant
The `skills/` folder holds reference documents that teach an AI assistant how the IdeaBoard, IdeaSense Explorer and SumoBot v2 work, so it can write CircuitPython that runs first time. Point your assistant at this repository (`llms.txt` at the root is the index), or paste the relevant file into the chat if your tool cannot read URLs. See `skills/README.md`.

## Command-line access
The IdeaBoard has no USB drive; `tools/ibserial.py` lists, copies, and runs files on the board over the serial REPL from any OS (needs only Python and `pyserial`). Run it with no arguments for the commands.
