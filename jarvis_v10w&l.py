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
import urllib.parse
import sys
import shutil

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
            self.user_name = "Sir"  # Default name
            self.system_os = platform.system().lower()
            self.running = True
            self.command_queue = queue.Queue()
            self.voice_active = False
            self.is_speaking = False
            self.weather_api_key = os.getenv('WEATHER_API_KEY')
            self.wolfram_app_id = os.getenv('WOLFRAM_APP_ID')
            self.current_theme = 'dark'
            
            # Initialize voice recognition with error handling
            try:
                self.recognizer = sr.Recognizer()
                self.microphone = sr.Microphone()
                # Test microphone immediately
                with self.microphone as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=1)
                logging.info("Microphone initialized successfully")
            except Exception as e:
                logging.error(f"Microphone initialization failed: {e}")
                messagebox.showwarning("Microphone Error", 
                                    "Could not initialize microphone. Voice control will be disabled.")
                self.microphone = None
                self.voice_active = False

            # Initialize user memory system
            self.user_memory = {
                'personal_info': {},  # For storing personal information
                'custom_lists': {},   # For user-created lists
                'custom_dicts': {}     # For user-created dictionaries
            }
            
            # Try to load saved memory
            self.load_memory()

            # Initialize components
            self.configure_window()
            self.setup_gemini()
            self.create_gui()
            self.setup_voice()
            self.setup_responses()
            self.setup_applications()
            self.boot_sequence()
            
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
        """Configure applications JARVIS can launch with cross-platform support"""
        self.applications = {
            "calculator": {
                "windows": "calc.exe",
                "linux": "gnome-calculator" if self.check_command_exists("gnome-calculator") else "kcalc",
                "mac": "Calculator"
            },
            "notepad": {
                "windows": "notepad.exe",
                "linux": "gedit" if self.check_command_exists("gedit") else "nano",
                "mac": "TextEdit"
            },
            "browser": {
                "windows": "start chrome",
                "linux": "xdg-open https://www.google.com",
                "mac": "open -a Safari"
            },
            "spotify": {
                "windows": "spotify",
                "linux": "spotify" if self.check_command_exists("spotify") else "xdg-open https://open.spotify.com",
                "mac": "open -a Spotify"
            },
            "terminal": {
                "windows": "cmd.exe",
                "linux": "gnome-terminal" if self.check_command_exists("gnome-terminal") else "x-terminal-emulator",
                "mac": "Terminal"
            },
            "file explorer": {
                "windows": "explorer",
                "linux": "nautilus" if self.check_command_exists("nautilus") else "xdg-open .",
                "mac": "open ."
            }
        }

    def check_command_exists(self, cmd):
        """Check if a command exists on Linux systems"""
        if self.system_os != 'linux':
            return False
        return shutil.which(cmd) is not None

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
            text=f"System: Ready | OS: {platform.system()} | AI: {'Online' if self.ai_enabled else 'Offline'} | Voice: Off",
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
            preferred_voices = {
                'windows': 'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_EN-GB_DAVID_11.0',
                'linux': 'english_rp',
                'mac': 'com.apple.speech.synthesis.voice.daniel'
            }
            
            # Set voice based on OS
            if self.system_os in preferred_voices:
                try:
                    self.engine.setProperty('voice', preferred_voices[self.system_os])
                except:
                    # Fallback to any English male voice
                    for voice in voices:
                        if "english" in voice.languages and "male" in voice.name.lower():
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
                f"Systems online. Good {time_of_day} {self.user_name}. How may I assist you today?",
                f"All systems operational. Good {time_of_day} {self.user_name}. Ready for your commands.",
                f"Initialization complete. Good {time_of_day} {self.user_name}. How can I be of service?"
            ],
            "farewell": [
                "Shutting down systems. Goodbye Sir.",
                "Powering off. Until next time Sir.",
                "Terminating session. It's been a pleasure serving you."
            ],
            "gratitude": [
                "You're most welcome Sir. Always at your service.",
                "My pleasure, as always Sir.",
                "Gratitude acknowledged. Happy to assist."
            ],
            "apology": [
                "No need to apologize Sir. How may I assist you?",
                "All is forgiven Sir. What can I do for you?",
                "No offense taken Sir. How may I be of service?"
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
                "Yes Sir? How may I assist you?",
                "At your service Sir.",
                "Listening Sir."
            ],
            "memory": [
                "I've stored that information for you.",
                "Consider it remembered.",
                "Added to my memory banks."
            ],
            "translation": [
                "The translation is: {}",
                "In the requested language: {}",
                "Translated: {}"
            ],
            "app_list": [
                "Here are the applications I can launch: {}",
                "Registered applications: {}",
                "Available apps: {}"
            ],
            "search": [
                "Searching for '{}'...",
                "Looking up '{}'...",
                "Querying '{}'..."
            ]
        }

    def boot_sequence(self):
        """Run startup sequence"""
        messages = [
            "Initializing J.A.R.V.I.S. protocols...",
            f"Detected OS: {platform.system()} {platform.release()}",
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
            text=f"System: Ready | OS: {platform.system()} | AI: {ai_status} | Voice: {voice_status} | CPU: {psutil.cpu_percent()}% | RAM: {psutil.virtual_memory().percent}%"
        )

    def voice_listener(self):
        """Listen for voice commands when voice control is active"""
        try:
            # Test microphone availability
            if not hasattr(self, 'microphone') or self.microphone is None:
                self.root.after(0, lambda: self.jarvis_speak("Microphone not available"))
                self.voice_active = False
                self.root.after(0, self.update_status_bar)
                return

            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                logging.info("Microphone initialized successfully")
                
            while self.voice_active and self.running:
                if self.is_speaking:
                    time.sleep(0.1)
                    continue
                    
                try:
                    with self.microphone as source:
                        logging.info("Listening for voice command...")
                        audio = self.recognizer.listen(
                            source, 
                            timeout=5,  # Increased timeout
                            phrase_time_limit=8  # Increased phrase limit
                        )
                    
                    try:
                        command = self.recognizer.recognize_google(audio).lower()
                        logging.info(f"Recognized command: {command}")
                        
                        # Process command in main thread to avoid GUI issues
                        self.root.after(0, lambda cmd=command: self.process_voice_command(cmd))
                        
                    except sr.UnknownValueError:
                        logging.info("No speech detected")
                        continue
                    except sr.RequestError as e:
                        logging.error(f"Voice recognition service error: {e}")
                        self.root.after(0, lambda: self.update_chat("SYSTEM", f"Voice recognition error: {e}", 'error'))
                        self.voice_active = False
                        self.root.after(0, self.update_status_bar)
                    
                except Exception as e:
                    logging.error(f"Error during listening: {e}")
                    self.voice_active = False
                    self.root.after(0, self.update_status_bar)
                    self.root.after(0, lambda: self.jarvis_speak("Voice recognition error. Switching to manual mode."))
                    break
                    
        except Exception as e:
            logging.critical(f"Voice listener error: {e}")
            self.voice_active = False
            self.root.after(0, self.update_status_bar)
            self.root.after(0, lambda: self.jarvis_speak("Voice system error. Please check your microphone."))

    def process_voice_command(self, command):
        """Process voice commands with enhanced capabilities"""
        # Handle memory-related commands first
        if "my name is" in command:
            name = command.split("my name is")[1].strip()
            self.store_personal_info('name', name)
            self.user_name = name  # Update current session name
            self.jarvis_speak(f"Understood, I'll call you {name} from now on.")
            return
            
        if "remember that" in command:
            try:
                # Extract key-value pair (e.g., "remember that my birthday is June 5th")
                parts = command.split("remember that")[1].strip().split(" is ")
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip()
                    self.store_personal_info(key, value)
                    self.jarvis_speak(random.choice(self.responses["memory"]))
                else:
                    self.jarvis_speak("Please specify what to remember in the format: 'remember that [key] is [value]'")
            except Exception as e:
                self.jarvis_speak("I couldn't process that memory request. Please try again.")
            return
            
        if "what is my" in command:
            key = command.split("what is my")[1].strip()
            value = self.recall_personal_info(key)
            if value:
                self.jarvis_speak(f"Your {key} is {value}")
            else:
                self.jarvis_speak(f"I don't have information about your {key}")
            return
            
        if "create a list called" in command:
            list_name = command.split("create a list called")[1].strip()
            self.create_custom_list(list_name)
            self.jarvis_speak(f"I've created a new list called {list_name}. You can add items by saying 'add [item] to {list_name}'")
            return
            
        if "add" in command and "to" in command and "list" in command:
            try:
                parts = command.split("add")[1].split("to")
                item = parts[0].strip()
                list_name = parts[1].replace("list", "").strip()
                self.add_to_custom_list(list_name, item)
                self.jarvis_speak(f"Added {item} to {list_name}")
            except Exception as e:
                self.jarvis_speak("I couldn't process that list addition. Please try again.")
            return
            
        if "show me the" in command and "list" in command:
            list_name = command.split("show me the")[1].replace("list", "").strip()
            self.show_custom_list(list_name)
            return
            
        if "create a dictionary called" in command:
            dict_name = command.split("create a dictionary called")[1].strip()
            self.create_custom_dict(dict_name)
            self.jarvis_speak(f"I've created a new dictionary called {dict_name}. You can add entries by saying 'add [key] is [value] to {dict_name}'")
            return
            
        if "add" in command and "is" in command and "to" in command and "dictionary" in command:
            try:
                # Format: "add [key] is [value] to [dict_name] dictionary"
                parts = command.split("add")[1].split("is")
                key_part = parts[0].strip()
                value_part = parts[1].split("to")[0].strip()
                dict_name = parts[1].split("to")[1].replace("dictionary", "").strip()
                self.add_to_custom_dict(dict_name, key_part, value_part)
                self.jarvis_speak(f"Added {key_part} as {value_part} to {dict_name} dictionary")
            except Exception as e:
                self.jarvis_speak("I couldn't process that dictionary addition. Please try again.")
            return
            
        if "show me the" in command and "dictionary" in command:
            dict_name = command.split("show me the")[1].replace("dictionary", "").strip()
            self.show_custom_dict(dict_name)
            return

        # New feature: Google Search
        if any(cmd in command for cmd in ["search google for ", "google ", "look up "]):
            query = command.split("for ")[-1] if "for " in command else command.split("google ")[-1]
            self.google_search(query)
            return

        # New feature: YouTube Search
        if any(cmd in command for cmd in ["search youtube for ", "youtube ", "play "]):
            query = command.split("for ")[-1] if "for " in command else command.split("youtube ")[-1]
            self.youtube_search(query)
            return

        # New feature: Translation
        if any(cmd in command for cmd in ["translate ", "how do you say "]):
            parts = command.split("translate ")[-1].split(" to ")
            if len(parts) == 2:
                text, lang = parts
                self.translate_text(text.strip(), lang.strip())
            else:
                self.jarvis_speak("Please specify text and target language (e.g., 'translate hello to Spanish').")
            return

        # New feature: List Registered Apps
        if any(cmd in command for cmd in ["list apps", "what apps can you open", "available applications"]):
            self.list_registered_apps()
            return

        # Handle special cases
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
        
        diagnostics.append("\n=== MEMORY SYSTEMS ===")
        diagnostics.append(f"Personal Info Items: {len(self.user_memory['personal_info'])}")
        diagnostics.append(f"Custom Lists: {len(self.user_memory['custom_lists'])}")
        diagnostics.append(f"Custom Dictionaries: {len(self.user_memory['custom_dicts'])}")
        
        diag_results = "\n".join(diagnostics)
        self.update_chat("JARVIS", diag_results, 'system')
        self.jarvis_speak("Diagnostics complete. All systems nominal." if "Inactive" not in diag_results 
                        else "Diagnostics complete. Minor anomalies detected.")

    def launch_application(self, app_name):
        """Launch system applications with cross-platform support"""
        app_name = app_name.lower()
        if app_name in self.applications:
            try:
                command = self.applications[app_name].get(self.system_os)
                if command:
                    if self.system_os == 'windows':
                        subprocess.Popen(command, shell=True)
                    else:
                        # Handle Linux/Mac commands
                        if command.startswith("xdg-open") or command.startswith("open"):
                            subprocess.Popen(command.split())
                        else:
                            subprocess.Popen([command])
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
        if not hasattr(self, 'recognizer') or not hasattr(self, 'microphone') or self.microphone is None:
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

    # Memory System Methods
    def store_personal_info(self, key, value):
        """Store personal information about the user"""
        self.user_memory['personal_info'][key.lower()] = value
        self.save_memory()
        
    def recall_personal_info(self, key):
        """Retrieve stored personal information"""
        return self.user_memory['personal_info'].get(key.lower())
    
    def create_custom_list(self, list_name):
        """Create a new custom list"""
        if list_name not in self.user_memory['custom_lists']:
            self.user_memory['custom_lists'][list_name] = []
            self.save_memory()
            
    def add_to_custom_list(self, list_name, item):
        """Add an item to a custom list"""
        if list_name in self.user_memory['custom_lists']:
            self.user_memory['custom_lists'][list_name].append(item)
            self.save_memory()
        else:
            self.jarvis_speak(f"I couldn't find a list named {list_name}")
            
    def show_custom_list(self, list_name):
        """Display the contents of a custom list"""
        if list_name in self.user_memory['custom_lists']:
            items = self.user_memory['custom_lists'][list_name]
            if items:
                list_str = "\n".join(f"- {item}" for item in items)
                self.update_chat("JARVIS", f"Contents of {list_name} list:\n{list_str}", 'system')
                self.jarvis_speak(f"Here's your {list_name} list with {len(items)} items")
            else:
                self.jarvis_speak(f"The {list_name} list is currently empty")
        else:
            self.jarvis_speak(f"I couldn't find a list named {list_name}")
            
    def create_custom_dict(self, dict_name):
        """Create a new custom dictionary"""
        if dict_name not in self.user_memory['custom_dicts']:
            self.user_memory['custom_dicts'][dict_name] = {}
            self.save_memory()
            
    def add_to_custom_dict(self, dict_name, key, value):
        """Add a key-value pair to a custom dictionary"""
        if dict_name in self.user_memory['custom_dicts']:
            self.user_memory['custom_dicts'][dict_name][key] = value
            self.save_memory()
        else:
            self.jarvis_speak(f"I couldn't find a dictionary named {dict_name}")
            
    def show_custom_dict(self, dict_name):
        """Display the contents of a custom dictionary"""
        if dict_name in self.user_memory['custom_dicts']:
            items = self.user_memory['custom_dicts'][dict_name]
            if items:
                dict_str = "\n".join(f"- {k}: {v}" for k, v in items.items())
                self.update_chat("JARVIS", f"Contents of {dict_name} dictionary:\n{dict_str}", 'system')
                self.jarvis_speak(f"Here's your {dict_name} dictionary with {len(items)} entries")
            else:
                self.jarvis_speak(f"The {dict_name} dictionary is currently empty")
        else:
            self.jarvis_speak(f"I couldn't find a dictionary named {dict_name}")
    
    def save_memory(self):
        """Save user memory to a file"""
        try:
            with open('jarvis_memory.json', 'w') as f:
                json.dump(self.user_memory, f)
        except Exception as e:
            logging.error(f"Error saving memory: {e}")
    
    def load_memory(self):
        """Load user memory from a file"""
        try:
            if os.path.exists('jarvis_memory.json'):
                with open('jarvis_memory.json', 'r') as f:
                    self.user_memory = json.load(f)
                # Update user name if stored
                if 'name' in self.user_memory['personal_info']:
                    self.user_name = self.user_memory['personal_info']['name']
        except Exception as e:
            logging.error(f"Error loading memory: {e}")

    # --- New Methods for Advanced Features ---
    def google_search(self, query):
        """Open a browser with Google search results"""
        search_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
        self.jarvis_speak(random.choice(self.responses["search"]).format(query))
        if self.system_os == 'windows':
            webbrowser.open(search_url)
        else:
            subprocess.Popen(['xdg-open', search_url])

    def youtube_search(self, query):
        """Open a browser with YouTube search results"""
        search_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
        self.jarvis_speak(f"Searching YouTube for {query}...")
        if self.system_os == 'windows':
            webbrowser.open(search_url)
        else:
            subprocess.Popen(['xdg-open', search_url])

    def translate_text(self, text, target_lang):
        """Translate text using Gemini AI (fallback to basic if offline)"""
        if self.ai_enabled:
            try:
                response = self.model.generate_content(
                    f"Translate '{text}' to {target_lang}. Return only the translation."
                )
                translation = response.text.strip()
                self.jarvis_speak(random.choice(self.responses["translation"]).format(translation))
            except Exception as e:
                logging.error(f"Translation error: {e}")
                self.jarvis_speak("AI translation failed. Using basic fallback...")
                self.basic_translation(text, target_lang)
        else:
            self.basic_translation(text, target_lang)

    def basic_translation(self, text, target_lang):
        """Fallback translation for common phrases (expand as needed)"""
        translations = {
            "hello": {
                "spanish": "hola",
                "french": "bonjour",
                "german": "hallo"
            },
            "goodbye": {
                "spanish": "adiós",
                "french": "au revoir",
                "german": "auf wiedersehen"
            }
        }
        
        text_lower = text.lower()
        lang_lower = target_lang.lower()
        
        if text_lower in translations and lang_lower in translations[text_lower]:
            self.jarvis_speak(random.choice(self.responses["translation"]).format(
                translations[text_lower][lang_lower]
            ))
        else:
            self.jarvis_speak(f"I don't have a translation for '{text}' to {target_lang} in my database.")

    def list_registered_apps(self):
        """List all registered applications JARVIS can launch"""
        apps = ", ".join(self.applications.keys())
        self.jarvis_speak(random.choice(self.responses["app_list"]).format(apps))
        self.update_chat("JARVIS", f"Registered Applications:\n- " + "\n- ".join(self.applications.keys()), 'system')

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = JARVIS(root)
        root.mainloop()
    except Exception as e:
        logging.critical(f"Fatal error: {e}")
        messagebox.showerror("JARVIS Error", f"A critical error occurred: {str(e)}")
