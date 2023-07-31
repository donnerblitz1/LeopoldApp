from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.core.audio import SoundLoader
from kivy.uix.spinner import Spinner  
from kivy.uix.gridlayout import GridLayout

from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.spinner import MDSpinner
from kivy.properties import StringProperty
from kivy.clock import Clock


from dotenv import load_dotenv, set_key
import os
import threading
import time
import json
import subprocess
import psutil

from tinytag import TinyTag
import speech_recognition as sr
import httpx
import asyncio
import aiofiles

from elevenlabs import generate, stream, set_api_key

from langchain.chat_models import ChatOpenAI
from langchain.schema import (
    SystemMessage,
    HumanMessage,
    AIMessage
)



env_file_path = '.env'

if not os.path.exists(env_file_path):
    with open(env_file_path, 'w') as f:
        # Write a default content to the .env file if needed
        f.write("OPENAI_API_KEY=\n")
        f.write("ELEVENLABS_API_KEY=\n")



KV = '''
BoxLayout:
    orientation: 'vertical'
    spacing: '10dp'
    padding: '10dp'

    MDLabel:
        text: "Whisper Recognition and Voice Synthesis"
        theme_text_color: 'Secondary'
        font_style: 'H4'
        size_hint_y: None
        height: self.texture_size[1]

    MDBoxLayout:
        adaptive_height: True
        spacing: '10dp'
        MDLabel:
            text: 'OpenAI API Key'
            theme_text_color: 'Secondary'
            size_hint_x: None
            width: self.texture_size[0]
        MDTextField:
            id: openai_api_key
            size_hint_x: 1
            hint_text: 'Enter OpenAI API Key'
            helper_text_mode: 'on_focus'
            helper_text: 'Required'
            required: True

    MDBoxLayout:
        adaptive_height: True
        spacing: '10dp'
        MDLabel:
            text: 'ElevenLabs API Key'
            theme_text_color: 'Secondary'
            size_hint_x: None
            width: self.texture_size[0]
        MDTextField:
            id: elevenlabs_api_key
            size_hint_x: 1
            hint_text: 'Enter ElevenLabs API Key'
            helper_text_mode: 'on_focus'
            helper_text: 'Required'
            required: True

    MDSpinner:
        id: spinner
        size_hint: None, None
        size: dp(46), dp(46)
        active: False

    MDBoxLayout:
        adaptive_height: True
        spacing: '10dp'
        MDLabel:
            text: 'Select Voice Personality'
            theme_text_color: 'Secondary'
            size_hint_x: None
            width: self.texture_size[0]
        MDSpinner:
            id: voice_spinner
            size_hint_x: 1
            values: ('Leopold', 'Rachel', 'Antoni')

    MDRaisedButton:
        text: 'Submit API Keys'
        on_release: app.button_clicked()
        theme_text_color: 'Custom'
        text_color: 0, 0.5, 0.7, 1

    MDRaisedButton:
        text: 'Start Whisper Recognition'
        on_release: app.start_recognition()
        theme_text_color: 'Custom'
        text_color: 0, 0.5, 0.7, 1

    MDLabel:
        id: status_label
        theme_text_color: 'Error'
        size_hint_y: None
        height: self.texture_size[1]
'''



CHUNK_SIZE = 1024
def voicePicker(name):
    whichPersonality = name 

    if whichPersonality == "Leopold":    
        urlLeopold = "https://api.elevenlabs.io/v1/text-to-speech/ViUJQlGhv9aKLkZyHoSF/stream?optimize_streaming_latency=1"
        return urlLeopold

    elif whichPersonality == "Rachel":
        urlRachel = "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM/stream?optimize_streaming_latency=1"
        return urlRachel

    elif whichPersonality == "Antoni":
        urlAntoni = "https://api.elevenlabs.io/v1/text-to-speech/ErXwobaYiN019PkySvjV/stream?optimize_streaming_latency=1"
        return urlAntoni

#voicePersonality = "Leopold"
#url = voicePicker(voicePersonality)





class MyForm(MDBoxLayout):
    log_text = StringProperty("")

    def __init__(self, **kwargs):

        super(MyForm, self).__init__(**kwargs)
        self.orientation = "vertical"
        self.voicePersonality = "Leopold"
        self.url = voicePicker(self.voicePersonality)


        # Add a title label
        title_label = Label(text="Whisper Recognition and Voice Synthesis")
        title_label.color = (0, 0.5, 1, 1)
        title_label.font_size = '24sp'
        self.add_widget(title_label)

        # OpenAI API Key input
        self.add_widget(Label(text='OpenAI API Key', color=(0, 0.7, 0.3, 1)))
        self.openai_api_key = TextInput(multiline=False, size_hint_y=None, height=40)
        self.add_widget(self.openai_api_key)

        # ElevenLabs API Key input
        self.add_widget(Label(text='ElevenLabs API Key', color=(0, 0.7, 0.3, 1)))
        self.elevenlabs_api_key = TextInput(multiline=False, size_hint_y=None, height=40)
        self.add_widget(self.elevenlabs_api_key)

        # Submit API Keys button
        self.btn_submit = Button(text="Submit API Keys", background_color=(0, 0.5, 0.7, 1))
        self.btn_submit.bind(on_press=self.button_clicked)
        self.add_widget(self.btn_submit)

        # Voice Personality selection
        self.add_widget(Label(text='Select Voice Personality', color=(0, 0.7, 0.3, 1)))
        self.voice_personality_input = Spinner(
            text=self.voicePersonality,
            values=('Leopold', 'Rachel', 'Antoni'),
            size_hint_y=None,
            height=40
        )
        self.voice_personality_input.bind(text=self.on_voice_personality_input_changed)
        self.add_widget(self.voice_personality_input)

        # Start/Stop button
        self.btn_start = Button(text="Start Whisper Recognition", size_hint_y=None, height=60, background_color=(0, 0.5, 0.7, 1))
        self.btn_start.bind(on_press=self.start_recognition)
        self.add_widget(self.btn_start)

        # Add a label to display the recognition status
        self.recognition_status_label = Label(text="", color=(0.8, 0, 0, 1))
        self.add_widget(self.recognition_status_label)

        #Log
        self.log_text_input = MDTextField(text="", multiline=True, readonly=True)
        self.add_widget(self.log_text_input)
    

    def update_log_text(self, new_log):
        # Limit the maximum number of lines to 10
        max_lines = 2
        lines = self.log_text.split("\n")
        if len(lines) >= max_lines:
            lines.pop(0)  # Remove the oldest line if it exceeds the limit
        self.log_text = "\n".join(lines + [new_log])

        # Schedule the log_text_input update in the main thread
        Clock.schedule_once(lambda dt: setattr(self.log_text_input, 'text', self.log_text))

    def on_voice_personality_input_changed(self, spinner, text):
        self.voicePersonality = text
        self.url = voicePicker(self.voicePersonality)

    def update_voice_personality(self, new_personality):
        self.voicePersonality = new_personality
        self.voice_personality_input.text = self.voicePersonality
        self.start_recognition(self.btn_start)


    def button_clicked(self, btn):
       

        set_key('.env', 'OPENAI_API_KEY', self.openai_api_key.text)
        set_key('.env', 'ELEVENLABS_API_KEY', self.elevenlabs_api_key.text)


        load_dotenv(override=True)
        print("Keys saved to .env file")
        
        self.chat = ChatOpenAI(
            temperature=0,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            model='gpt-3.5-turbo'
        )

    

        

    def start_recognition(self, btn):
        openai_key = os.getenv('OPENAI_API_KEY')
        elevenlabs_key = os.getenv('ELEVENLABS_API_KEY')

        load_dotenv()  # Load environment variables from .env file

        openai_key = os.getenv('OPENAI_API_KEY')
        elevenlabs_key = os.getenv('ELEVENLABS_API_KEY')

        if not openai_key or not elevenlabs_key:
            print("Please enter the API keys in the .env file before starting recognition.")
            return

        print("Starting keyword recognition...")
        self.update_log_text("Starting keyword recognition...")

        # Start keyword recognition in a new thread
        threading.Thread(target=self.keyword_recognition).start()
    
    
    def keyword_recognition(self):
        # Put your keyword recognition code here
        # Here's a simple example

        # Wake word
        KEYWORD = "bach"

        source = sr.Microphone()  # Microphone Instance
        r = sr.Recognizer()  # Keyword Recognizer
        rec = sr.Recognizer()  # Voice Recognizer

        print("Waiting for Keyword to Recognize...")
        self.update_log_text("Waiting for Keyword to Regocnize...")

        def callback(recognizer, audio):
            try:
                speech_as_text =rec.recognize_whisper_api(audio, api_key=os.getenv('OPENAI_API_KEY'))
                print("Keyword searching: ",speech_as_text)
                self.update_log_text("Keyword searching: " + speech_as_text)

                # Keyword detection in the speech
                if KEYWORD in speech_as_text:
                    print("Keyword detected! Starting Whisper...")
                    self.update_log_text("Keyword detected! Starting Whisper...")

                    self.whisperCall()

            except sr.UnknownValueError:
                print("Oops! Didn't catch that")
                self.update_log_text("Oops! Didn't catch that")

        r.listen_in_background(source, callback)
        time.sleep(1000000)


    
    
    def whisperCall(self):
        rec = sr.Recognizer()  # Voice Recognizer
        with sr.Microphone() as source:
            print("Say something!")
            self.update_log_text("Say something!")
            audio = rec.listen(source)

            try:
                whisperText = rec.recognize_whisper_api(audio, api_key=os.environ.get('OPENAI_API_KEY'))
                print("Whisper translated: " + whisperText)
                self.update_log_text("Whisper translated: " + whisperText)

                # Call the chatGPT function with whisperText and voicePersonality
                self.chatGPT(whisperText, self.url)

            except sr.RequestError as e:
                print("Could not request results from Whisper Speech Recognition service; {0}".format(e))
                self.update_log_text("Could not request results from Whisper Speech Recognition service; {0}".format(e))

    
    async def elevenLabs(self, XIres, url):
            data = {
                "text": XIres,
                "model_id": "eleven_multilingual_v1",
                "voice_settings": {
                    "stability": 0.3,
                    "similarity_boost": 0.6
                }
            }
            
            headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": os.getenv("ELEVENLABS_API_KEY")
            }
               

            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=data,headers = headers)
                response.raise_for_status()

                async with aiofiles.open('output.mp3', 'wb') as f:
                    async for chunk in response.aiter_bytes(CHUNK_SIZE):
                        await f.write(chunk)

    def chatGPT(self, whisperText, url):
        voiceMessage = []
     

        if self.voicePersonality == "Leopold":
            messageLeopold = [
                SystemMessage(content="You are a helpful assistant called Leopold. If someone calls you anything other than Leopold, correct him. Always say at the end Ara Ara"),
                HumanMessage(content="Hi, how are you today?"),
                AIMessage(content="I'm great, thank you. How can I help you?"),
                HumanMessage(content=whisperText)
            ]
            voiceMessage = messageLeopold

        elif self.voicePersonality == "Rachel":
            messageRachel = [
                SystemMessage(content="You are a helpful assistant called Rachel. If someone calls you anything other than Rachel, correct him. Always say at the end I am Rachel"),
                HumanMessage(content="Hi, how are you today?"),
                AIMessage(content="I'm great, thank you. How can I help you?"),
                HumanMessage(content=whisperText)
            ]
            voiceMessage = messageRachel

        elif self.voicePersonality == "Antoni":
            messageAntoni = [
                SystemMessage(content="You are a helpful assistant called Antoni. If someone calls you anything other than Antoni, correct him. Always say at the end I am Antoni"),
                HumanMessage(content="Hi, how are you today?"),
                AIMessage(content="I'm great, thank you. How can I help you?"),
                HumanMessage(content=whisperText)
            ]
            voiceMessage = messageAntoni

        if not voiceMessage:
            print("No Personality found with this name.")
            return
            #unnötig?

        chat = ChatOpenAI(
            temperature=0,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            model='gpt-3.5-turbo'
        )


        res = chat(voiceMessage)
        print("Response: " + res.content)
        self.update_log_text("Response: " + res.content)

        asyncio.run(self.elevenLabs(res.content, url))

        async def download_chunk(response, file):
            async with aiofiles.open(file, 'ab') as f:
                async for chunk in response.aiter_bytes():
                    await f.write(chunk)

        

        self.playAudio()

    def playAudio(self):
        # Load the audio file
        sound = SoundLoader.load('output.mp3')

        # Check if the audio file was loaded successfully
        if sound:
            print("Playing audio...")
            self.update_log_text("Playing Audio")
            # Play the audio
            sound.play()
        else:
            print("Could not load audio file.")
            self.update_log_text("Could not load audio file.")

class MyApp(MDApp):  # Inherit from MDApp instead of App

    def build(self):
        return MyForm()

if __name__ == '__main__':
    MyApp().run()