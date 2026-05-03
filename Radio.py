import random
from cerebras.cloud.sdk import Cerebras
from mutagen.easyid3 import EasyID3
import os
import sys
import time
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
import pygame
import subprocess as SubP

def Music (PLAYTHIS):
    pygame.mixer.music.load( os.path.join(MUSICPATH, PLAYTHIS))
    pygame.mixer.music.play()
    
    while pygame.mixer.music.get_busy():
        time.sleep(0.5)

def ttsPlay():

 
    pygame.mixer.music.load(SPEECHPATH)
    pygame.mixer.music.play()

    pygame.mixer.Sound(SPEECHPATH)

    while pygame.mixer.music.get_busy():
        time.sleep(0.5)

def LLM(lastSong):
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
                    "role": "user",
                    "content": f"You are a Female radio presenter called Emily, The previous song played was {lastSong}",
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


#driver code
while True:
    
    pygame.mixer.init()
    
    BASEPATH = os.path.dirname(__file__)
    MUSICPATH = os.path.join(BASEPATH, "Audio", "Music")
    SPEECHPATH = os.path.join(BASEPATH, "Audio", "Speech", "Speech.mp3")
    DATAPATH = os.path.join(BASEPATH, "Data")
    APIPATH = os.path.join(DATAPATH, "API.txt")
    SCRIPTLOCATION = os.path.join(DATAPATH, "scripts", "Script.txt")
        
    
    musicFiles = [ f for f in os.listdir(MUSICPATH)
                   if  f != ".gitkeep" ]
    
    selectedSong = random.choice(musicFiles)

    songPlayed = EasyID3(os.path.join(MUSICPATH, selectedSong))

    with open(SCRIPTLOCATION, "w") as f :
        f.write(LLM(songPlayed))
    
    SubP.Popen([sys.executable, "TTS_Gen.py"])
    
    Music(selectedSong)
    
    ttsPlay()