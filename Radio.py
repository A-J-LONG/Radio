from mutagen.id3 import ID3NoHeaderError
from cerebras.cloud.sdk import Cerebras
from mutagen.easyid3 import EasyID3
from mutagen.flac import FLAC
from flask import Flask, Response
from waitress import serve
from queue import Queue
import subprocess as SubP
import threading
import edge_tts
import platform
import asyncio
import random
import time
import stat
import sys
import os

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
                    "content": f"You are a Female radio presenter called Emily, The previous 2 songs played were {firstSong} and {lastSong}(this has already been played) in that order, do not describe your actions only your words, do not make up what is coming up next you dont know. Title, album or artist will say Unknow Artist/Title/Album if its unknow, anmything else and that is the name of the title/artist/album"
                     
                }
        ],
            model="llama3.1-8b",
        )
        return(chat_completion.choices[0].message.content)
        
         
    except Exception as e:

        try:
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
        except :
                print(f"Error Code Type : {type(e)}")
                print(f"Error Details : {e}")
                return("AN ERROR OCCURED")

async def ttsAudioGeneration(text):

    communication = edge_tts.Communicate(text, "en-IE-EmilyNeural", rate="+15%")

    await communication.save(SPEECHPATH)

def streamOutput(LOCATION, Metadata) :

    song_title = Metadata.get("title", ["Unknown"])[0]
    song_artist = Metadata.get("artist", ["Unknown"])[0]

    process = SubP.Popen([
        FFMPEGPATH,
        "-re",
        "-i", LOCATION,
        "-map", "0:a:0",        
        "-ar", "44100",        
        "-ac", "2",            
        "-c:a", "mp3",
        "-q:a", "2",
        "-metadata", f"title={song_title}",
        "-metadata", f"album={song_artist}",
        "-f", "mp3",         
        "pipe:1"
    ], stdout=SubP.PIPE)

    try:
        while process.poll() is None:
            chunk = process.stdout.read(4096)
            
            if chunk:
                yield chunk
    finally :
        process.kill()
        process.wait()

def main() :
    while True:

        if not activeMusicList :
            print (f"NO MUSIC FOUND IN {MUSICPATH}")    
            time.sleep(5)
            continue
      
        selectedSong = random.choice(activeMusicList)
        selectedSong2 = random.choice(activeMusicList)

        while selectedSong2 == selectedSong :
            selectedSong2 = random.choice(activeMusicList)

        if selectedSong.endswith(".mp3"):
            path = os.path.join(MUSICPATH, selectedSong)
            try :
                songPlayed = EasyID3(path)
            except ID3NoHeaderError :
                EasyID3().save(path)
                songPlayed = EasyID3(path)
                if not songPlayed.get("title") :
                    songPlayed["title"] =  "Unknown Title"
                if not songPlayed.get("album") :
                    songPlayed["album"] =  "Unknown Album"
                if not songPlayed.get("artist") :
                    songPlayed["artist"] =  "Unknown Artist"

                songPlayed.save(path)
        elif selectedSong.endswith(".flac"):
            path = os.path.join(MUSICPATH, selectedSong)

            songPlayed = FLAC(path)
            if not songPlayed.get("title") :
                songPlayed["title"] =  "Unknown Title"
            if not songPlayed.get("album") :
                songPlayed["album"] =  "Unknown Album"
            if not songPlayed.get("artist") :
                songPlayed["artist"] =  "Unknown Artist"

            songPlayed.save(path)

        if selectedSong2.endswith(".mp3"):
            path = os.path.join(MUSICPATH, selectedSong2)
            try :
                songPlayed2 = EasyID3(path)
            except ID3NoHeaderError :
                EasyID3().save(path)
                songPlayed2 = EasyID3(path)
                if not songPlayed2.get("title") :
                    songPlayed2["title"] =  "Unknown Title"
                if not songPlayed2.get("album") :
                    songPlayed2["album"] =  "Unknown Album"
                if not songPlayed2.get("artist") :
                    songPlayed2["artist"] =  "Unknown Artist"

                songPlayed2.save(path)
        elif selectedSong2.endswith(".flac") :
            path = os.path.join(MUSICPATH, selectedSong2)

            songPlayed2 = FLAC(path)
            if not songPlayed2.get("title") :
                songPlayed2["title"] =  "Unknown Title"
            if not songPlayed2.get("album") :
                songPlayed2["album"] =  "Unknown Album"
            if not songPlayed2.get("artist") :
                songPlayed2["artist"] =  "Unknown Artist"

            songPlayed2.save(path)



        speechPlayed = {
                        "artist": "Emily",
                        "album": "Edge_tts",
                        "title": "Speech Broadcast"
                        }                    

        SONGPATH = os.path.join(MUSICPATH, selectedSong)
        SONGPATH2 = os.path.join(MUSICPATH, selectedSong2)

        print(f"Now Playing : {songPlayed.get("title",["Unknown"])[0]}")
        print(f"Up Next : {songPlayed2.get("title",["Unknown"])[0]}")


        script = (LLM(songPlayed, songPlayed2))
        
        threading.Thread(target=lambda: asyncio.run(ttsAudioGeneration(script)),daemon=True).start()
  
        newCycle = True
        i = 0
        while i <= 1:
            if newCycle :
                yield from streamOutput(SONGPATH, songPlayed)
                newCycle = False
                i += 1
            elif not newCycle :
                yield from streamOutput(SONGPATH2,songPlayed2)
                newCycle = True
                i += 1
        
        yield from streamOutput(SPEECHPATH, speechPlayed)

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

if getattr(sys, 'frozen', False):
    BASEPATH = os.path.dirname(sys.executable)
    BASEPATH = os.path.join(BASEPATH, "..", "..","..")
else :
    BASEPATH = os.path.dirname(__file__)

MUSICPATH = os.path.join(BASEPATH, "Audio", "Music")
SPEECHPATH = os.path.join(BASEPATH, "Audio", "Speech", "Speech.mp3")
DATAPATH = os.path.join(BASEPATH, "Data")
APIPATH = os.path.join(DATAPATH, "API.txt")
SCRIPTLOCATION = os.path.join(DATAPATH, "scripts", "Script.txt")
if platform.system() == "Windows":
    FFMPEGPATH = os.path.join(BASEPATH, "bin", "FFmpeg", "Windows", "ffmpeg-7.1.1", "bin", "ffmpeg.exe")
else :
    FFMPEGPATH = os.path.join(BASEPATH, "bin", "FFmpeg", "Linux", "ffmpeg-git-20240629-amd64-static", "ffmpeg")

    try:
        os.chmod(FFMPEGPATH,os.stat(FFMPEGPATH).st_mode | stat.S_IEXEC)
    except Exception:
        raise RuntimeError(f"FFMPEG IS NOT EXECUTABLE PLEASE RUN : chmod +x {FFMPEGPATH}")

with open(os.path.join(DATAPATH, "Port.txt"), "r") as f :
    PORT = f.read().strip()

    activeMusicList = []
for root, _, files  in os.walk(MUSICPATH):
    for f in files:
        if f.endswith((".flac", ".mp3")):
             activeMusicList.append(os.path.join(root, f))

audio_Buffer = Queue(maxsize=200)
currentChunk = b""

app = Flask(__name__)
@app.route("/stream")
def stream() :
    return Response(listener(), mimetype="audio/mpeg")

threading.Thread(target=broadCaster, daemon=True).start()

if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=PORT)
