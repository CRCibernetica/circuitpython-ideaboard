# Skills: AI reference documents for IdeaBoard projects

These files teach an AI assistant (ChatGPT, Claude, Gemini, Copilot, ...) how the
CRCibernetica boards and their CircuitPython libraries work, so it can write
code for your project that runs first time.

| File | Use it when your project uses... |
|---|---|
| `ideaboard.md` | The IdeaBoard on its own: motors, RGB LED, servos, sensors on the pins, Wi-Fi, buzzer. Always include this one. |
| `ideasense.md` | The IdeaSense Explorer: 5x5 LED matrix, three buttons, temperature/humidity, light, accelerometer/gyro. |
| `sumobotv2.md` | The SumoBot v2 robot: four infrared floor sensors, colour sensor, IMU, plus the IdeaBoard motors. |

## How to use them

1. Open the file(s) for your hardware on GitHub and click **Raw**, or open them in a text editor.
2. Copy the whole contents.
3. Start a new chat with your AI tool and paste the contents as your first message.
   Paste `ideaboard.md` first, then the others if you need them.
4. Then describe your project in your own words, in English or Spanish. For example:

   > Quiero que el robot avance hasta que detecte la línea blanca, retroceda y gire a la izquierda.

   > Make the matrix show a smiley face when the temperature is above 28 degrees.

5. Copy the code the AI gives you into IdeaCode (or Thonny) and run it. If it fails,
   paste the exact error from the console back into the chat.

The documents are written for the AI, not for you, so they are dense. You do not need
to read them. If you are curious about a feature, the `examples/` folder in this
repository has a working script for almost everything mentioned.
