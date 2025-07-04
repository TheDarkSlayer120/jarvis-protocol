import tkinter as tk
from tkinter import scrolledtext, font
import pyttsx3
import datetime
import random
import subprocess
import webbrowser
import requests
import time
from threading import Thread

class JARVIS:
    def __init__(self, root):
        self.root = root
        self.configure_window()
        self.user_name = "Sir"
        self.setup_ollama()
        self.create_gui()
        self.setup_voice()
        self.setup_responses()
        self.boot_sequence()

    def configure_window(self):
        """Iron Man-style window configuration"""
        self.root.title("JARVIS Protocol")
        self.root.geometry("800x600")
        self.root.configure(bg='#0a0a0a')
        self.root.option_add('*Font', 'Helvetica 12')

    def setup_ollama(self):
        """AI configuration with failover"""
        self.ollama_url = "http://localhost:11434/api/generate"
        self.current_model = "llama3"
        self.ai_enabled = self.test_ollama_connection()

    def test_ollama_connection(self):
        """Check if Ollama is running"""
        try:
            test = requests.post(
                self.ollama_url,
                json={"model": self.current_model, "prompt": "test", "stream": False},
                timeout=3
            )
            return test.status_code == 200
        except:
            return False

    def create_gui(self):
        """Create Stark Industries-style interface"""
        # Font configuration
        bold_font = font.Font(family='Helvetica', size=12, weight='bold')
        
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
        self.chat_area.tag_config('jarvis', foreground='#ff6600')
        self.chat_area.tag_config('user', foreground='#00ccff')
        self.chat_area.tag_config('system', foreground='#00ff00')
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
            font=bold_font
        ).pack(side=tk.RIGHT, padx=(10, 0))

    def setup_voice(self):
        """Configure JARVIS's signature voice"""
        self.engine = pyttsx3.init()
        
        # Prefer British male voice
        voices = self.engine.getProperty('voices')
        for voice in voices:
            if "english" in voice.languages and "male" in voice.name.lower():
                self.engine.setProperty('voice', voice.id)
                break
        
        # Cinematic voice tuning
        self.engine.setProperty('rate', 170)
        self.engine.setProperty('volume', 0.95)
        self.engine.setProperty('pitch', 108)

    def setup_responses(self):
        """Enhanced response protocols with better logic"""
        hour = datetime.datetime.now().hour
        time_of_day = "morning" if 5 <= hour < 12 else "afternoon" if 12 <= hour < 17 else "evening"
        
        self.responses = {
            "greeting": [
                f"All systems operational. Good {time_of_day}, {self.user_name}.",
                f"Online and awaiting your command, {self.user_name}.",
                f"Diagnostics complete. Ready for service, {self.user_name}."
            ],
            "apology": [
                f"Temporary system anomaly detected, {self.user_name}.",
                f"Most irregular. My protocols appear compromised, {self.user_name}.",
                f"Engineering reports a minor malfunction, {self.user_name}."
            ],
            "gratitude": [
                f"Service is its own reward, {self.user_name}.",
                f"Your satisfaction is my primary directive, {self.user_name}.",
                f"At your service, now and always, {self.user_name}."
            ],
            "farewell": [
                f"JARVIS protocol terminating, {self.user_name}.",
                f"Systems entering standby mode.",
                f"Until our next collaboration, {self.user_name}."
            ]
        }
        
        self.commands = {
            "time": self._get_time,
            "date": self._get_date,
            "open": self._open_app,
            "search": self._web_search,
            "youtube": self._youtube_search,
            "joke": self._tell_joke,
            "calculate": self._calculate_time
        }

    def boot_sequence(self):
        """Stark Industries boot animation"""
        boot_messages = [
            "Initializing J.A.R.V.I.S. protocols...",
            "Loading personality matrix...",
            "Calibrating sensory arrays...",
            "Establishing global network links...",
            "Systems nominal. JARVIS online."
        ]
        
        for msg in boot_messages:
            self.update_chat("SYSTEM", msg, 'system')
            time.sleep(0.7)
        
        self.jarvis_speak(random.choice(self.responses["greeting"]))

    def update_chat(self, speaker, message, tag=None):
        """Update display with formatted messages"""
        self.chat_area.configure(state='normal')
        self.chat_area.insert(
            tk.END, 
            f"{speaker.upper()}: {message}\n\n", 
            tag if tag else speaker.lower()
        )
        self.chat_area.configure(state='disabled')
        self.chat_area.see(tk.END)

    def jarvis_speak(self, text):
        """Speak with cinematic timing"""
        self.update_chat("JARVIS", text)
        
        # Split long sentences for dramatic effect
        if len(text.split()) > 10:
            parts = text.rsplit(',', 1) if ',' in text else [text]
            for part in parts:
                self.engine.say(part.strip())
                self.engine.runAndWait()
                time.sleep(0.15)
        else:
            self.engine.say(text)
            self.engine.runAndWait()

    # ================= IMPROVED CORE FUNCTIONS =================
    def _get_date(self, command=None):
        """Enhanced date handling with natural language"""
        now = datetime.datetime.now()
        
        if not command:
            command = ""
            
        command = command.lower()
        
        if "yesterday" in command:
            date = (now - datetime.timedelta(days=1)).strftime("%A, %B %d, %Y")
            response = f"Yesterday was {date}, {self.user_name}"
        elif "tomorrow" in command:
            date = (now + datetime.timedelta(days=1)).strftime("%A, %B %d, %Y")
            response = f"Tomorrow will be {date}, {self.user_name}"
        elif "today" in command:
            today = now.strftime("%A, %B %d, %Y")
            response = f"Today is {today}, {self.user_name}"
        else:
            today = now.strftime("%A, %B %d, %Y")
            yesterday = (now - datetime.timedelta(days=1)).strftime("%A, %B %d, %Y")
            response = f"Today is {today}. Yesterday was {yesterday}, {self.user_name}"
        
        self.jarvis_speak(response)

    def _get_time(self, command=None):
        """More natural time responses"""
        now = datetime.datetime.now()
        current_time = now.strftime("%I:%M %p")
        
        if command and "ago" in command.lower():
            try:
                hours = int(command.split("hours")[0].split()[-1])
                past_time = (now - datetime.timedelta(hours=hours)).strftime("%I:%M %p")
                response = f"{hours} hours ago it was {past_time}, {self.user_name}"
            except:
                response = "Time calculation error. Please specify hours clearly, Sir."
        else:
            response = f"The current time is {current_time}, {self.user_name}"
        
        self.jarvis_speak(response)

    def _calculate_time(self, command):
        """Improved time calculations"""
        try:
            if "from now" in command.lower():
                hours = int(command.split("hours")[0].split()[-1])
                future_time = (datetime.datetime.now() + datetime.timedelta(hours=hours)).strftime("%I:%M %p")
                response = f"In {hours} hours it will be {future_time}, {self.user_name}"
            elif "between" in command.lower():
                times = [s.strip() for s in command.split("between")[1].split("and")]
                fmt = "%I:%M %p"
                delta = datetime.datetime.strptime(times[1], fmt) - datetime.datetime.strptime(times[0], fmt)
                response = f"Duration is {delta.seconds//3600} hours, {self.user_name}"
            else:
                response = "Please specify time calculation parameters, Sir"
        except Exception as e:
            response = "Temporal calculations unavailable, Sir"
        
        self.jarvis_speak(response)

    def _open_app(self, command):
        """Better application launching"""
        apps = {
            "calculator": ("calc", "Calculator systems"),
            "notepad": ("notepad", "Notepad module"),
            "chrome": ("chrome", "Global network browser"),
            "spotify": ("spotify", "Audio entertainment systems")
        }
        
        for app, (cmd, name) in apps.items():
            if app in command.lower():
                try:
                    subprocess.Popen(cmd, shell=True)
                    response = f"Initializing {name}, {self.user_name}"
                except:
                    response = f"{name} failed to activate, {self.user_name}"
                break
        else:
            response = "Application not in my protocol database, Sir"
        
        self.jarvis_speak(response)

    def _web_search(self, command):
        """More natural search responses"""
        search_term = command.lower().replace("search", "").replace("for", "").strip()
        if search_term:
            response = f"Accessing global databases for {search_term}, {self.user_name}"
            webbrowser.open(f"https://www.google.com/search?q={search_term.replace(' ', '+')}")
        else:
            response = "Please specify search parameters, Sir"
        
        self.jarvis_speak(response)

    def _youtube_search(self, command):
        """Improved YouTube search"""
        search_term = command.lower().replace("youtube", "").replace("search", "").strip()
        if search_term:
            response = f"Querying media archives for {search_term}, {self.user_name}"
            webbrowser.open(f"https://www.youtube.com/results?search_query={search_term.replace(' ', '+')}")
        else:
            response = "Activating entertainment systems, Sir"
            webbrowser.open("https://www.youtube.com")
        
        self.jarvis_speak(response)

    def _tell_joke(self, command=None):
        """Updated joke database"""
        jokes = [
            "Why don't scientists trust atoms? They make up everything!",
            "I'm reading a book about anti-gravity... it's impossible to put down!",
            "Why did the Python data scientist get arrested? Too many 'float' operations!"
        ]
        self.jarvis_speak(random.choice(jokes))

    # ================= ENHANCED AI INTEGRATION =================
    def query_ollama(self, prompt):
        """Improved AI responses with better context"""
        if not self.ai_enabled:
            return self._offline_response(prompt)
            
        try:
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.current_model,
                    "prompt": (
                        f"Respond as JARVIS from Iron Man to {self.user_name}. "
                        f"Be concise, accurate, and slightly witty. "
                        f"Question: {prompt}\n"
                        "Response style examples:\n"
                        "- 'According to my databases, Sir...'\n"
                        "- 'My analysis indicates...'\n"
                        "- 'The answer to your query is...'"
                    ),
                    "stream": False,
                    "options": {"temperature": 0.7}
                },
                timeout=15
            )
            return response.json().get("response", "Processing... one moment, Sir.")
        except Exception as e:
            print(f"AI Error: {e}")
            self.ai_enabled = False
            return self._offline_response(prompt)

    def _offline_response(self, prompt):
        """Better fallback responses"""
        responses = [
            f"My systems indicate that {prompt.split('?')[0]} appears satisfactory, Sir",
            f"Database query returns: {random.choice(['Affirmative','Negative'])} on {prompt.split('?')[0]}, Sir",
            f"Standard protocol response: {random.choice(['Confirmed','Unclear'])} regarding {prompt.split('?')[0]}, Sir"
        ]
        return random.choice(responses)

    # ================= IMPROVED COMMAND PROCESSING =================
    def process_input(self, event=None):
        """Enhanced command processing"""
        command = self.user_input.get().strip()
        self.user_input.delete(0, tk.END)
        
        if not command:
            return
            
        self.update_chat("YOU", command, 'user')
        
        # Handle multiple commands
        if " and " in command.lower():
            for subcmd in command.split(" and "):
                self._process_single_command(subcmd.strip())
            return
            
        self._process_single_command(command)

    def _process_single_command(self, command):
        """Improved single command handling"""
        # Conversation handlers
        if any(word in command.lower() for word in ["hello", "hi", "hey"]):
            self.jarvis_speak(random.choice(self.responses["greeting"]))
            return
            
        if any(word in command.lower() for word in ["thank", "thanks"]):
            self.jarvis_speak(random.choice(self.responses["gratitude"]))
            return
            
        if any(word in command.lower() for word in ["sorry", "apologize"]):
            self.jarvis_speak(random.choice(self.responses["apology"]))
            return
            
        if any(word in command.lower() for word in ["exit", "quit", "goodbye"]):
            self.jarvis_speak(random.choice(self.responses["farewell"]))
            self.root.after(2000, self.root.destroy)
            return
            
        # System commands
        for trigger, action in self.commands.items():
            if trigger in command.lower():
                action(command)
                return
                
        # AI fallback
        response = self.query_ollama(command)
        self.jarvis_speak(response)

if __name__ == "__main__":
    root = tk.Tk()
    app = JARVIS(root)
    root.mainloop()