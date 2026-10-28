# /// script
# dependencies = [
#   "mcp",
# ]
# ///

import subprocess
import queue
import threading
import random
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("MacOS-Voice")

# Thread-safe queue for speech requests
speech_queue = queue.Queue()

VOICE_MAP = {
    "Smith": "Agent Smith",
    "Picard": "Captain Picard",
    "Data": "Commander Data",
    "Trump": "Donald Trump",
    "Arnold": "Arnold Schwarzenegger",
    "Worf": "Commander Worf",
    "Sylvester": "Sylvester Stallone",
    "Lennon": "John Lennon",
    "Judy": "Judy",
    "Michael": "Michael",
    "Charles Clarke III": "Charles Clarke III"
}

PERSONAS = list(VOICE_MAP.keys())

def speech_worker():
    while True:
        message, event, persona = speech_queue.get()
        try:
            cmd = ["say"]
            if persona:
                cmd.extend(["-p", persona])
            cmd.append(message)
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)
        except Exception as e:
            print(f"Error in speech worker: {str(e)}")
        finally:
            if event:
                event.set()
            speech_queue.task_done()

threading.Thread(target=speech_worker, daemon=True).start()

@mcp.tool()
def speak(message: str, persona: str = ""):
    """
    Speaks the provided message aloud using the say command.
    Blocking: returns only after the speech has finished.
    Optional persona parameter (e.g. 'Smith', 'Picard', 'Data', 'Trump', 'Arnold', 'Worf').
    If omitted or 'Random', a random voice is selected.
    """
    if not persona or persona.lower() == "random":
        persona = random.choice(PERSONAS)
    display_name = VOICE_MAP.get(persona, persona)
    event = threading.Event()
    speech_queue.put((message, event, persona))
    event.wait()
    return f"Finished speaking as {display_name}: {message}"

@mcp.tool()
def speak_non_blocking(message: str, persona: str = ""):
    """
    Speaks the provided message aloud using the say command.
    Non-blocking: returns immediately after queuing the speech.
    Optional persona parameter (e.g. 'Smith', 'Picard', 'Data', 'Trump', 'Arnold', 'Worf').
    If omitted or 'Random', a random voice is selected.
    """
    if not persona or persona.lower() == "random":
        persona = random.choice(PERSONAS)
    display_name = VOICE_MAP.get(persona, persona)
    speech_queue.put((message, None, persona))
    return f"Queued for speaking as {display_name}: {message}"

if __name__ == "__main__":
    mcp.run()
