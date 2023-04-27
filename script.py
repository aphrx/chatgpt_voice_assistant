# Imports
import openai
import os
import io
import pygame
import sys
import time
import random
import math

import speech_recognition as sr

from gtts import gTTS
from dotenv import load_dotenv
from multiprocessing import Process, Value

# Load OpenAI API Key
load_dotenv()
openai.api_key = os.environ["OPENAI_API_KEY"]

messages = [
    {"role": "system", "content": "You are a friendly and helpful assistant"},
]

# Transcribe from Microphone and return transcription
def transcribe_prompt():
    print("Listening")
    r = sr.Recognizer()
    with sr.Microphone() as source:
        audio = r.listen(source)
        try:
            res = r.recognize_google(audio)
            print(res)
            return res
        except sr.UnknownValueError:
            print("Google Speech Recognition could not understand audio")
            return False
        except sr.RequestError as e:
            print("Could not request results from Google Speech Recognition service; {0}".format(e))
            return False

# Send prompt to ChatGPT and return response
def openai_response(prompt):
    messages.append({"role": "user", "content": prompt})
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    messages.append({"role": "assistant", "content": response['choices'][0]['message']['content']})
    return response['choices'][0]['message']['content']

# Speak text out using Pygame Mixer and gTTS
def speak_text_with_pygame(response):
    with io.BytesIO() as f:
        gTTS(text=response, lang='en').write_to_fp(f)
        f.seek(0)
        pygame.mixer.init()
        pygame.mixer.music.load(f)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            continue

# PyGame GUI
def gui(status):
    pygame.init()
    clock = pygame.time.Clock()

    surf = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    pygame.fastevent.init()
    w, h = pygame.display.get_surface().get_size()

    offset = 0
    while True:

        clock.tick(60)
        surf.fill((0, 0, 0))

        e = pygame.fastevent.poll()
        if e.type == pygame.KEYDOWN and e.unicode == 'q':
            return

        pygame.draw.circle(surf, (255,255,255), ((w/3 * 2), h/3), 100, 10)
        pygame.draw.circle(surf, (255,255,255), (w - (w/3 * 2), h/3), 100, 10)


        points = []  # <--- clear it

        # Draw Sine Wave
        for i in range(500):
            n = int(math.sin((i+offset) / 500 * 4 * math.pi) * 50 + (h/3 * 2))
            if status.value == 2 or status.value == 0:
                n = (h/3 * 2)
            points.append([i + w/2 - 250, n])

        offset += 5

        pygame.draw.lines(surf, (255, 255, 255), False, points, 10)

        pygame.display.flip()

# Logic and Change Status Value inbetween
def logic(status):
    while(True):
        status.value = 1
        prompt = transcribe_prompt()
        if prompt:
            status.value = 2
            response = openai_response(prompt)
            status.value = 3
            speak_text_with_pygame(response)
            status.value = 0
            time.sleep(1)

if __name__ == '__main__':
    # Variable to communicate status of assistant between Logic and GUI
    status = Value('i',0)
    # 0 - Static
    # 1 - Listening
    # 2 - Processing
    # 3 - Talking

    # Run 2 Processes for PyGame GUI and Logic
    p1 = Process(target = gui, args=(status,))
    p2 = Process(target = logic, args=(status,))

    p1.start()
    p2.start()

    p1.join()
    p2.join()