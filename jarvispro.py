import tkinter as tk
from tkinter import scrolledtext, font
import pyttsx3
import datetime
import random
import subprocess
import webbrowser
import time
import google.generativeai as genai
from dotenv import load_dotenv
import os

class JARVIS:
    def __init__(self, root):
        self.root = root
        self.user_name = "Sir"
        
        # Initialize components
        self.configure_window()
        self.setup_gemini()
        self.create_gui()
        self.setup_voice()
        self.setup_responses()
        self.boot_sequence()

    def configure_window(self):
        """Configure main window appearance"""
        self.root.title("JARVIS Protocol")
        self.root.geometry("800x600")
        self.root.configure(bg='#0a0a0a')
        self.root.option_add('*Font', 'Helvetica 12')


    def setup_gemini(self):
        """Initialize Gemini AI with better error handling"""
        load_dotenv() # Load environment variables from .env file
        api_key = os.getenv('GEMINI_API_KEY') # Get API key from environment variable

        # If API key is not set, prompt user
        if not api_key or api_key.endswith('_error'): # Check if API key is missing or  (ends with _error)
            print("Error: Missing or issue with API key in .env file.")
            api_key = input("Enter your Gemini API key, press Enter to skip, or type ignore to remove error marker: ").strip() 
            
            if api_key.lower() == 'ignore': # If user types ignore, remove the error marker
                # read the .env file and remove the _error suffix from the API key
                with open('.env', 'r+') as f: # open .env file and read the contents
                    lines = f.readlines()
                    f.seek(0)
                    for line in lines: # iterate through each line
                        if line.startswith('GEMINI_API_KEY='): # If line starts with GEMINI_API_KEY=
                            f.write(line.replace('_error', '')) # Remove the _error suffix
                    f.truncate() # Remove any remaining old data
                    
                # Reload .env data
                load_dotenv(override=True) 
                api_key = os.getenv('GEMINI_API_KEY') 

            elif api_key: # If user provides a new API key
                with open('.env', 'w') as f: # open .env file and write the new API key
                    f.write(f'GEMINI_API_KEY={api_key}')
            else: # otherwise, skip Gemini setup
                print("Skipping Gemini API setup. Running in offline mode.")
                self.ai_enabled = False
                return

        try: # Initialize Gemini AI with the provided API key
            genai.configure(api_key=api_key) # Configure the Gemini API with the provided key
            
            try: # Try the newest model first, then fallback
                self.model = genai.GenerativeModel('gemini-2.5-flash')
            except:
                self.model = genai.GenerativeModel('gemini-2.5-pro')
            
            
            # check for network connectivity via a ping test
            try:
                subprocess.check_output(['ping', '-c', '3', '1.1.1.1'], stderr=subprocess.DEVNULL)
            except subprocess.CalledProcessError: # On fail raise exception
                print("Network connectivity issue, running in offline mode.")
                self.ai_enabled = False 
                return
                
            # Check if api key is valid by performing a test query
            query_test = self.model.generate_content(
                "What is the capital of France?"
            )
            if query_test: # If the query returns a response, the API key is valid
                self.ai_enabled = True 
                print("Successfully connected to Gemini API")
            else: # If the query fails, assume the API key is invalid
                raise Exception("Gemini Init Error: Test query failed, invalid API Key or other issue") 
            
        except Exception as e: # Catch any errors during initialization
            print(f"An exception occurred during Gemini initialization: {e}, running in offline mode.")
            self.ai_enabled = False 
            with open('.env', 'w') as f: # open .env file and append with _error at end of file for next program run
                f.write(f'GEMINI_API_KEY={api_key}_error')

    def create_gui(self):
        """Create interface components"""
        # Chat display
        self.chat_area = scrolledtext.ScrolledText(
            self.root,
            wrap=tk.WORD,
            state='disabled',
            font=('Consolas', 12),
            bg='#0a0a0a',
            fg='#ff6600',
            insertbackground='white',
            borderwidth=0,
            highlightthickness=0,
            padx=20,
            pady=20
        )
        self.chat_area.pack(fill=tk.BOTH, expand=True)

        # Input frame
        input_frame = tk.Frame(self.root, bg='#0a0a0a')
        input_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        self.user_input = tk.Entry(
            input_frame,
            font=('Helvetica', 12),
            bg='#1a1a1a',
            fg='white',
            insertbackground='white',
            relief=tk.FLAT
        )
        self.user_input.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5)
        self.user_input.bind('<Return>', self.process_input)
        
        tk.Button(
            input_frame,
            text="ENGAGE",
            command=self.process_input,
            bg='#ff6600',
            fg='black',
            activebackground='#ff8533',
            borderwidth=0,
            font=('Helvetica', 12, 'bold')
        ).pack(side=tk.RIGHT, padx=(10, 0))

    def setup_voice(self):
        """Configure text-to-speech"""
        self.engine = pyttsx3.init()
        voices = self.engine.getProperty('voices')
        for voice in voices:
            if "english" in voice.languages and "male" in voice.name.lower():
                self.engine.setProperty('voice', voice.id)
                break
        self.engine.setProperty('rate', 170)
        self.engine.setProperty('volume', 0.95)

    def setup_responses(self):
        """Set up default responses"""
        hour = datetime.datetime.now().hour
        time_of_day = "morning" if 5 <= hour < 12 else "afternoon" if 12 <= hour < 17 else "evening"
        
        self.responses = {
            "greeting": [f"Systems online. Good {time_of_day}, {self.user_name}."],
            "error": ["I'm experiencing technical difficulties. Please try again later."],
            "offline": ["AI systems offline. Running in limited capacity."]
        }

    def boot_sequence(self):
        """Run startup sequence"""
        messages = [
            "Initializing J.A.R.V.I.S. protocols...",
            "Connecting to Gemini AI...",
            "Systems nominal. JARVIS online."
        ]
        for msg in messages:
            self.update_chat("SYSTEM", msg, 'system')
            time.sleep(0.7)
        self.jarvis_speak(random.choice(self.responses["greeting"]))
        if not self.ai_enabled:
            self.jarvis_speak(self.responses["offline"][0])

    def update_chat(self, speaker, message, tag=None):
        """Update the chat display"""
        self.chat_area.configure(state='normal')
        self.chat_area.insert(tk.END, f"{speaker.upper()}: {message}\n\n", tag or speaker.lower())
        self.chat_area.configure(state='disabled')
        self.chat_area.see(tk.END)

    def jarvis_speak(self, text):
        """Convert text to speech"""
        self.update_chat("JARVIS", text)
        self.engine.say(text)
        self.engine.runAndWait()

    def query_gemini(self, prompt):
        """Get response from Gemini AI"""
        if not self.ai_enabled:
            return random.choice(self.responses["offline"])
        
        try:
            response = self.model.generate_content(
                f"Respond as JARVIS from Iron Man to {self.user_name}. "
                f"Be concise (1-2 sentences), technical, and slightly witty. "
                f"Question: {prompt}"
            )
            return response.text
        except Exception as e:
            print(f"AI Generation Error: {e}")
            return random.choice(self.responses["error"])

    def process_input(self, event=None):
        """Handle user input"""
        command = self.user_input.get().strip()
        if not command:
            return
            
        self.update_chat("YOU", command, 'user')
        self.user_input.delete(0, tk.END)
        
        if command.lower() in ["exit", "quit"]:
            self.root.destroy()
            return
            
        response = self.query_gemini(command)
        self.jarvis_speak(response)

if __name__ == "__main__":
    root = tk.Tk()
    app = JARVIS(root)
    root.mainloop()