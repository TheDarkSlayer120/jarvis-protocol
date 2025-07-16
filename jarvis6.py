import tkinter as tk
from tkinter import scrolledtext, font, messagebox, ttk
import pyttsx3
import datetime
import random
import subprocess
import webbrowser
import time
import google.generativeai as genai
from dotenv import load_dotenv
import os
import platform
import psutil
import socket
import traceback
import speech_recognition as sr
import logging
import threading
import json
import queue
from PIL import Image, ImageTk

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='jarvis.log',
    filemode='a'
)

class JARVIS:
    def __init__(self, root):
        try:
            self.root = root
            self.user_name = "Sir"
            self.system_os = platform.system()
            self.running = True
            self.command_queue = queue.Queue()  # Now this will work
            self.voice_active = False
            self.is_speaking = False
            self.recognizer = sr.Recognizer()
            self.microphone = sr.Microphone()
            self.weather_api_key = os.getenv('WEATHER_API_KEY')
            self.wolfram_app_id = os.getenv('WOLFRAM_APP_ID')
            self.current_theme = 'dark'
            
            # Rest of your initialization code...
            
            # Initialize components
            self.configure_window()
            self.setup_gemini()
            self.create_gui()
            self.setup_voice()
            self.setup_responses()
            self.setup_applications()
            self.boot_sequence()
            
            # Start background threads
            threading.Thread(target=self.voice_listener, daemon=True).start()
        except Exception as e:
            messagebox.showerror("Initialization Error", f"Failed to initialize JARVIS:\n{str(e)}")
            traceback.print_exc()
            self.root.destroy()

    def configure_window(self):
        """Configure main window appearance with modern UI"""
        self.root.title("J.A.R.V.I.S. - Just A Rather Very Intelligent System")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        self.root.configure(bg='#0a0a0a')
        
        # Modern styling
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('TFrame', background='#0a0a0a')
        self.style.configure('TLabel', background='#0a0a0a', foreground='#ff6600')
        self.style.configure('TButton', background='#ff6600', foreground='black')
        self.style.map('TButton', 
                      background=[('active', '#ff8533'), ('pressed', '#cc5200')])

    def setup_gemini(self):
        """Initialize Gemini AI with robust error handling"""
        try:
            load_dotenv()
            api_key = os.getenv('GEMINI_API_KEY')
            
            if not api_key:
                logging.warning("Gemini API key not found in .env file")
                self.ai_enabled = False
                return
                
            genai.configure(api_key=api_key)
            
            # Try multiple model versions
            model_versions = ['gemini-1.5-flash', 'gemini-1.0-pro', 'gemini-pro']
            self.model = None
            
            for version in model_versions:
                try:
                    self.model = genai.GenerativeModel(version)
                    break
                except Exception as e:
                    logging.warning(f"Failed to initialize {version}: {e}")
                    continue
            
            if not self.model:
                raise Exception("No compatible Gemini model found")
            
            # Test connection
            try:
                test_query = self.model.generate_content("Test connection")
                if test_query.text:
                    self.ai_enabled = True
                    logging.info("Gemini AI connected successfully")
                else:
                    raise Exception("Empty response from Gemini")
            except Exception as e:
                logging.error(f"Gemini test failed: {e}")
                self.ai_enabled = False
                
        except Exception as e:
            logging.error(f"Gemini setup error: {e}")
            self.ai_enabled = False

    def setup_applications(self):
        """Configure applications JARVIS can launch"""
        self.applications = {
            "calculator": {
                "windows": "calc.exe",
                "linux": "gnome-calculator",
                "mac": "Calculator"
            },
            "notepad": {
                "windows": "notepad.exe",
                "linux": "gedit",
                "mac": "TextEdit"
            },
            "browser": {
                "windows": "start chrome",
                "linux": "google-chrome",
                "mac": "open -a Safari"
            },
            "spotify": {
                "windows": "spotify",
                "linux": "spotify",
                "mac": "open -a Spotify"
            },
            "terminal": {
                "windows": "cmd.exe",
                "linux": "gnome-terminal",
                "mac": "Terminal"
            },
            "file explorer": {
                "windows": "explorer",
                "linux": "nautilus",
                "mac": "open ."
            }
        }

    def create_gui(self):
        """Create modern interface components"""
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Chat display with modern styling
        self.chat_area = scrolledtext.ScrolledText(
            main_frame,
            wrap=tk.WORD,
            state='disabled',
            font=('Consolas', 12),
            bg='#1a1a1a',
            fg='#ff6600',
            insertbackground='white',
            borderwidth=0,
            highlightthickness=0,
            padx=20,
            pady=20
        )
        self.chat_area.pack(fill=tk.BOTH, expand=True)
        
        # Configure tags for different message types
        self.chat_area.tag_config('user', foreground='#00ff00')
        self.chat_area.tag_config('system', foreground='#ffffff')
        self.chat_area.tag_config('warning', foreground='#ffff00')
        self.chat_area.tag_config('error', foreground='#ff0000')
        self.chat_area.tag_config('jarvis', foreground='#ff6600')

        # Status bar
        self.status_bar = ttk.Label(
            main_frame,
            text="System: Ready | AI: Online | Voice: Off",
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_bar.pack(fill=tk.X, pady=(0, 5))

        # Input frame with modern controls
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        # Voice control button
        self.voice_btn = ttk.Button(
            input_frame,
            text="🎤",
            command=self.toggle_voice_control,
            width=3
        )
        self.voice_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.user_input = ttk.Entry(
            input_frame,
            font=('Helvetica', 12)
        )
        self.user_input.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5)
        self.user_input.bind('<Return>', self.process_input)
        
        ttk.Button(
            input_frame,
            text="SEND",
            command=self.process_input,
            style='Accent.TButton'
        ).pack(side=tk.RIGHT, padx=(10, 0))

    def setup_voice(self):
        """Configure text-to-speech with British accent"""
        try:
            self.engine = pyttsx3.init()
            voices = self.engine.getProperty('voices')
            
            # Try to find a British male voice
            for voice in voices:
                if "english" in voice.languages and "male" in voice.name.lower() and "british" in voice.name.lower():
                    self.engine.setProperty('voice', voice.id)
                    break
            
            self.engine.setProperty('rate', 170)
            self.engine.setProperty('volume', 0.95)
            logging.info("Voice engine initialized successfully")
        except Exception as e:
            logging.error(f"Voice setup error: {e}")
            self.engine = None

    def setup_responses(self):
        """Set up default responses with formal language"""
        hour = datetime.datetime.now().hour
        time_of_day = "morning" if 5 <= hour < 12 else "afternoon" if 12 <= hour < 17 else "evening"
        
        self.responses = {
            "greeting": [
                f"Systems online. Good {time_of_day}, {self.user_name}. How may I assist you today?",
                f"All systems operational. Good {time_of_day}, {self.user_name}. Ready for your commands.",
                f"Initialization complete. Good {time_of_day}, {self.user_name}. How can I be of service?"
            ],
            "farewell": [
                "Shutting down systems. Goodbye, Sir.",
                "Powering off. Until next time, Sir.",
                "Terminating session. It's been a pleasure serving you."
            ],
            "gratitude": [
                "You're most welcome, Sir. Always at your service.",
                "My pleasure, as always, Sir.",
                "Gratitude acknowledged. Happy to assist."
            ],
            "apology": [
                "No need to apologize, Sir. How may I assist you?",
                "All is forgiven, Sir. What can I do for you?",
                "No offense taken, Sir. How may I be of service?"
            ],
            "time": [
                "The current time is {time}.",
                "My internal clock shows {time}.",
                "It is currently {time}."
            ],
            "date": [
                "Today's date is {date}.",
                "According to my calendar, it's {date}.",
                "The date is {date}."
            ],
            "diagnostics": [
                "Running comprehensive diagnostic scan...",
                "Initiating system self-check protocols...",
                "Commencing full diagnostic sequence..."
            ],
            "app_success": [
                "Initializing requested application, {}.",
                "Launching {} as requested.",
                "Opening {} for you."
            ],
            "app_fail": [
                "Failed to launch {}. It may not be installed.",
                "Unable to access {}. Please check system permissions.",
                "Application {} not responding."
            ],
            "wake_word": [
                "Yes, Sir? How may I assist you?",
                "At your service, Sir.",
                "Listening, Sir."
            ]
        }

    def boot_sequence(self):
        """Run startup sequence"""
        messages = [
            "Initializing J.A.R.V.I.S. protocols...",
            f"Detected OS: {self.system_os} {platform.release()}",
            "Loading system modules...",
            "Initializing voice synthesis...",
            "Connecting to Gemini AI...",
            "Establishing secure connection...",
            "Systems nominal. JARVIS online."
        ]
        
        for msg in messages:
            self.update_chat("SYSTEM", msg, 'system')
            time.sleep(0.5)
        
        self.jarvis_speak(random.choice(self.responses["greeting"]))
        if not self.ai_enabled:
            self.jarvis_speak("Warning: AI systems offline. Running in limited capacity.")

    def update_chat(self, speaker, message, tag=None):
        """Update the chat display with timestamp"""
        self.chat_area.configure(state='normal')
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.chat_area.insert(tk.END, f"[{timestamp}] {speaker.upper()}: {message}\n\n", tag or speaker.lower())
        self.chat_area.configure(state='disabled')
        self.chat_area.see(tk.END)

    def jarvis_speak(self, text):
        """Convert text to speech with voice control management"""
        self.update_chat("JARVIS", text)
        if self.engine:
            try:
                # Set speaking flag and disable voice recognition
                self.is_speaking = True
                was_active = self.voice_active
                self.voice_active = False
                self.update_status_bar()
                
                # Speak the text
                self.engine.say(text)
                self.engine.runAndWait()
                
                # Clear speaking flag and restore voice recognition state
                self.is_speaking = False
                if was_active:
                    time.sleep(0.5)  # Brief pause before reactivating
                    self.voice_active = True
                    self.update_status_bar()
                    threading.Thread(target=self.voice_listener, daemon=True).start()
                    
            except Exception as e:
                logging.error(f"Speech synthesis error: {e}")
                self.update_chat("SYSTEM", f"Voice error: {str(e)}", 'error')
                self.is_speaking = False

    def update_status_bar(self):
        """Update the status bar with current system status"""
        ai_status = "Online" if self.ai_enabled else "Offline"
        voice_status = "On (muted)" if self.is_speaking else "On" if self.voice_active else "Off"
        self.status_bar.config(
            text=f"System: Ready | AI: {ai_status} | Voice: {voice_status} | CPU: {psutil.cpu_percent()}% | RAM: {psutil.virtual_memory().percent}%"
        )

    def voice_listener(self):
        """Listen for voice commands when voice control is active"""
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)
            
        while self.voice_active and self.running:
            # Skip listening if JARVIS is currently speaking
            if self.is_speaking:
                time.sleep(0.1)
                continue
                
            try:
                with self.microphone as source:
                    audio = self.recognizer.listen(
                        source, 
                        timeout=3,
                        phrase_time_limit=5
                    )
                
                try:
                    command = self.recognizer.recognize_google(audio).lower()
                    
                    # Check for wake word
                    if "jarvis" in command or "hey jarvis" in command:
                        self.update_chat("YOU", command, 'user')
                        self.jarvis_speak(random.choice(self.responses["wake_word"]))
                        continue
                        
                    self.update_chat("YOU", command, 'user')
                    self.process_voice_command(command)
                    
                except sr.UnknownValueError:
                    continue  # Ignore when no speech is detected
                except sr.RequestError as e:
                    self.update_chat("SYSTEM", f"Voice recognition error: {e}", 'error')
                    self.voice_active = False
                    self.update_status_bar()
                
            except Exception as e:
                logging.error(f"Voice recognition error: {e}")
                self.voice_active = False
                self.update_status_bar()
                self.jarvis_speak("Voice recognition error. Switching to manual mode.")

    def process_voice_command(self, command):
        """Process voice commands"""
        # Handle special cases first
        if any(thanks in command for thanks in ["thank", "thanks"]):
            self.jarvis_speak(random.choice(self.responses["gratitude"]))
            return
            
        if any(sorry in command for sorry in ["sorry", "apologize"]):
            self.jarvis_speak(random.choice(self.responses["apology"]))
            return
            
        if any(greet in command for greet in ["hello", "hi", "hey"]):
            self.jarvis_speak(random.choice(self.responses["greeting"]))
            return
            
        if any(bye in command for bye in ["goodbye", "exit", "quit"]):
            self.jarvis_speak(random.choice(self.responses["farewell"]))
            self.root.after(1000, self.root.destroy)
            return
            
        if "time" in command:
            current_time = datetime.datetime.now().strftime("%H:%M:%S")
            self.jarvis_speak(random.choice(self.responses["time"]).format(time=current_time))
            return
            
        if "date" in command:
            current_date = datetime.datetime.now().strftime("%A, %B %d, %Y")
            self.jarvis_speak(random.choice(self.responses["date"]).format(date=current_date))
            return
            
        if any(diag in command for diag in ["diagnostic", "diagnostics", "system check"]):
            self.run_diagnostics()
            return
            
        if any(cmd in command for cmd in ["open ", "launch ", "start "]):
            for cmd in ["open ", "launch ", "start "]:
                if cmd in command:
                    app_name = command.split(cmd)[1].strip()
                    self.launch_application(app_name)
                    return
        
        # Default to AI response
        response = self.query_gemini(command)
        self.jarvis_speak(response)

    def run_diagnostics(self):
        """Perform and display system diagnostics"""
        self.jarvis_speak(random.choice(self.responses["diagnostics"]))
        
        diagnostics = []
        diagnostics.append("\n=== SYSTEM HEALTH ===")
        diagnostics.append(f"CPU Usage: {psutil.cpu_percent()}%")
        diagnostics.append(f"Memory Usage: {psutil.virtual_memory().percent}%")
        
        diagnostics.append("\n=== NETWORK STATUS ===")
        try:
            host = "8.8.8.8"
            socket.create_connection((host, 53), timeout=2)
            diagnostics.append("Internet Connection: Active")
        except:
            diagnostics.append("Internet Connection: Inactive")
        
        diagnostics.append("\n=== AI SYSTEMS ===")
        diagnostics.append(f"Gemini Connection: {'Active' if self.ai_enabled else 'Inactive'}")
        
        diagnostics.append("\n=== VOICE SYSTEMS ===")
        diagnostics.append(f"TTS Engine: {'Active' if self.engine else 'Inactive'}")
        
        diagnostics.append("\n=== APPLICATION PROTOCOLS ===")
        diagnostics.append(f"Registered Apps: {len(self.applications)}")
        
        diag_results = "\n".join(diagnostics)
        self.update_chat("JARVIS", diag_results, 'system')
        self.jarvis_speak("Diagnostics complete. All systems nominal." if "Inactive" not in diag_results 
                        else "Diagnostics complete. Minor anomalies detected.")

    def launch_application(self, app_name):
        """Launch system applications"""
        app_name = app_name.lower()
        if app_name in self.applications:
            try:
                command = self.applications[app_name].get(self.system_os.lower())
                if command:
                    subprocess.Popen(command, shell=True)
                    self.jarvis_speak(random.choice(self.responses["app_success"]).format(app_name))
                else:
                    raise Exception(f"Unsupported OS for {app_name}")
            except Exception as e:
                logging.error(f"App launch error: {e}")
                self.jarvis_speak(random.choice(self.responses["app_fail"]).format(app_name))
        else:
            self.jarvis_speak(f"Application {app_name} not in my protocol database")

    def query_gemini(self, prompt):
        """Get response from Gemini AI in JARVIS style"""
        if not self.ai_enabled:
            return "AI systems offline. Running in limited capacity."
        
        try:
            response = self.model.generate_content(
                f"Respond as JARVIS from Iron Man to {self.user_name}. "
                f"Be concise (1-2 sentences), technical, and slightly witty. "
                f"Question: {prompt}"
            )
            return response.text
        except Exception as e:
            logging.error(f"AI Generation Error: {e}")
            return "I'm experiencing technical difficulties. Please try again later."

    def toggle_voice_control(self):
        """Toggle voice recognition on/off"""
        if not hasattr(self, 'recognizer') or not hasattr(self, 'microphone'):
            self.jarvis_speak("Voice recognition not available")
            return
            
        self.voice_active = not self.voice_active
        self.update_status_bar()
        
        if self.voice_active:
            self.jarvis_speak("Voice recognition activated. Say 'Jarvis' or 'Hey Jarvis' to get my attention.")
            threading.Thread(target=self.voice_listener, daemon=True).start()
        else:
            self.jarvis_speak("Voice recognition deactivated.")

    def process_input(self, event=None):
        """Handle text input"""
        command = self.user_input.get().strip()
        if not command:
            return
            
        self.update_chat("YOU", command, 'user')
        self.user_input.delete(0, tk.END)
        
        if command.lower() in ["exit", "quit"]:
            self.jarvis_speak(random.choice(self.responses["farewell"]))
            self.root.after(1000, self.root.destroy)
            return
            
        self.process_voice_command(command.lower())

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = JARVIS(root)
        root.mainloop()
    except Exception as e:
        logging.critical(f"Fatal error: {e}")
        messagebox.showerror("JARVIS Error", f"A critical error occurred: {str(e)}")