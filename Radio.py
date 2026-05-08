from tkinter import CURRENT
from urllib import response
from cerebras.cloud.sdk import Cerebras
from mutagen.easyid3 import EasyID3
import random
import os
import sys
import platform
import time
import subprocess as SubP
from flask import Flask, Response
from queue import Queue
import threading

def LLM(firstSong, lastSong):
    try :
    
        with open(APIPATH, "r") as f :
            API = f.read().strip()
    
        if not API :
            raise ValueError
    except (FileNotFoundError, ValueError):
        API = input("Input API key").strip()
    
    with open(APIPATH, "w") as f :
        f.write(API)

    client = Cerebras(
        api_key = API
    )
    try :
        chat_completion = client.chat.completions.create(
            messages=[
                {

                    "role": "system",
                    "content": f"You are a Female radio presenter called Emily, The previous 2 songs played were {firstSong} and {lastSong} in that order, do not describe your actions only your words, do not make up what is coming up next you dont know",
                    "name": "listeners"
                }
        ],
            model="llama3.1-8b",
        )
        
        return(chat_completion.choices[0].message.content)
         
    except Exception as e:
        error_code = e.response.status_code
        if error_code == 401:
            
            print("ERROR 401 INVALID API KEY")
    
            API = input("Input API key").strip()

            with open(APIPATH, "w") as f :
                f.write(API)
            
            return(LLM())
        elif error_code == 429:
            return("Cereberus is facing high traffic right now please try again later")

        elif error_code != 200:
            print(f"ERROR CODE : {error_code}")
            return("AN UNKNOWN ERROR OCCURED")

def streamOutput(LOCATION) :
        
    process = SubP.Popen([
        FFMPEGPATH,
        "-re",
        "-i", LOCATION,
        "-map", "0:a:0",    
        "-ar", "44100",        
        "-ac", "2",            
        "-acodec", "libmp3lame",
        "-b:a", "192k",
        "-f", "mp3",         
        "pipe:1"
    ], stdout=SubP.PIPE, stderr=SubP.DEVNULL)

    try:
        while True:
            chunk = process.stdout.read(4096)
            if not chunk:
                break
            yield chunk
    except:
        pass
    finally :
        process.kill()

def main() :
    while True:
        
        musicFiles = [ f for f in os.listdir(MUSICPATH)
                       if  f != ".gitkeep" ]
        if not musicFiles :
            print (f"NO MUSIC FOUND IN {MUSICPATH}")    
            time.sleep(5)
            continue
      
        selectedSong = random.choice(musicFiles)
        selectedSong2 = random.choice(musicFiles)
    
        print(selectedSong)
        print(selectedSong2)
    
        songPlayed = EasyID3(os.path.join(MUSICPATH, selectedSong))
        songPlayed2 = EasyID3(os.path.join(MUSICPATH, selectedSong2))
    
        SONGPATH = os.path.join(MUSICPATH, selectedSong)
        SONGPATH2 = os.path.join(MUSICPATH, selectedSong2)
    
        with open(SCRIPTLOCATION, "w") as f :
            f.write(LLM(songPlayed, songPlayed2))
        
        SubP.Popen([sys.executable, "TTS_Gen.py"])
  
        newCycle = True
        i = 0
        while i <= 1:
            if newCycle :
                yield from streamOutput(SONGPATH)
                newCycle = False
                i += 1
                print(f"\n {i} \n")
            elif not newCycle :
                yield from streamOutput(SONGPATH2)
                newCycle = True
                i += 1
                print(f"\n {i} \n")
        
        yield from streamOutput(SPEECHPATH)

def broadCaster() :
    global currentChunk
    while True:
        print("Broadcast Active")
        for chunk in main():
            currentChunk = chunk
    

def listener(): 
    global currentChunk
    lastChunk = None

    while True:
        if currentChunk != lastChunk :
            lastChunk = currentChunk
            yield currentChunk
            
#driver code

BASEPATH = os.path.dirname(__file__)
MUSICPATH = os.path.join(BASEPATH, "Audio", "Music")
SPEECHPATH = os.path.join(BASEPATH, "Audio", "Speech", "Speech.mp3")
DATAPATH = os.path.join(BASEPATH, "Data")
APIPATH = os.path.join(DATAPATH, "API.txt")
SCRIPTLOCATION = os.path.join(DATAPATH, "scripts", "Script.txt")
if platform.system() == "Windows":
    FFMPEGPATH = os.path.join(BASEPATH, "bin", "FFmpeg", "Windows", "ffmpeg-7.1.1", "bin", "ffmpeg.exe")
else :
    FFMPEGPATH = os.path.join(BASEPATH, "bin", "FFmpeg", "Linux", "ffmpeg-git-20240629-amd84-static", "ffmpeg")

audio_Buffer = Queue(maxsize=200)
currentChunk = b""

app = Flask(__name__)
@app.route("/stream")
def stream() :
    return Response(listener(), mimetype="audio/mpeg")

threading.Thread(target=broadCaster, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)