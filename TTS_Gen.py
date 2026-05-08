import os
import edge_tts
import asyncio

async def ttsAudioGeneration(text):

    communication = edge_tts.Communicate(text, "en-IE-EmilyNeural", rate="+10%")

    await communication.save(SPEECHPATH)

BASEPATH = os.path.dirname(__file__)
MUSICPATH = os.path.join(BASEPATH, "Audio", "Music")
SPEECHPATH = os.path.join(BASEPATH, "Audio", "Speech", "Speech.mp3")
DATAPATH = os.path.join(BASEPATH, "Data")
APIPATH = os.path.join(DATAPATH, "API.txt")
SCRIPTLOCATION = os.path.join(DATAPATH, "scripts", "Script.txt")

with open(SCRIPTLOCATION, "r") as f :
    script = f.read()

asyncio.run(ttsAudioGeneration(script))