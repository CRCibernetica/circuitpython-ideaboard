# CRCibernetica IdeaBoard
[The documentation has moved to the WIKI!](https://github.com/CRCibernetica/circuitpython-ideaboard/wiki)

The IdeaBoard is an educational robotics development board created by CRCibernetica.com in Costa Rica.

## Working with an AI assistant
The `skills/` folder holds reference documents that teach an AI assistant how the IdeaBoard, IdeaSense Explorer, SumoBot and SumoBot v2 work, so it can write CircuitPython that runs first time. Point your assistant at this repository (`llms.txt` at the root is the index), or paste the relevant file into the chat if your tool cannot read URLs. See `skills/README.md`.

### Suggested first prompt
With an IdeaBoard and IdeaSense Explorer plugged in over USB, give an agent that can run commands (Claude Code, Codex, Cursor, ...) this prompt to check that everything works end to end:

> Read https://github.com/CRCibernetica/circuitpython-ideaboard/blob/master/llms.txt and the IdeaBoard and IdeaSense Explorer reference docs it links to. I have an IdeaBoard with an IdeaSense Explorer plugged in over USB. Download tools/ibserial.py into this folder, install pyserial if needed, find my board's serial port, and list the files on the board. Then write a tiny program that scrolls "HI" on the 5x5 matrix, run it on the board, and tell me what you did in simple steps.

## Layout
`lib/` and `examples/` are copied to the board as they are. `root/` holds the files that sit in the board's root folder on a freshly flashed IdeaBoard: `boot.py`, `code.py` and `settings.toml`.

## Command-line access
The IdeaBoard has no USB drive; `tools/ibserial.py` lists, copies, and runs files on the board over the serial REPL from any OS (needs only Python and `pyserial`). Run it with no arguments for the commands.
