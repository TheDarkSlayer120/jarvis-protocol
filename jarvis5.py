import tkinter as tk
from tkinter import scrolledtext, font, ttk, messagebox
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
import threading
import queue
import requests
import json
import speech_recognition as sr
import wikipedia
import wolframalpha
import pygame
import socket
import psutil
from PIL import Image, ImageTk
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='jarvis.log',
    filemode='a'
)

class JARVIS:
    def __init__(self, root):
        self.root = root
        self.user_name = "Sir"
        self.system_os = platform.system()
        self.running = True
        self.command_queue = queue.Queue()
        self.voice_active = False
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.weather_api_key = os.getenv('WEATHER_API_KEY')
        self.wolfram_app_id = os.getenv('WOLFRAM_APP_ID')
        self.current_theme = 'dark'
        
        # Initialize components
        self.configure_window()
        self.setup_gemini()
        self.create_gui()
        self.setup_voice()
        self.setup_responses()
        self.setup_applications()
        self.setup_commands()
        self.boot_sequence()
        
        # Start background threads
        threading.Thread(target=self.process_queue, daemon=True).start()
        threading.Thread(target=self.system_monitor, daemon=True).start()

    def configure_window(self):
        """Configure main window appearance"""
        self.root.title("J.A.R.V.I.S. - Just A Rather Very Intelligent System")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        self.root.configure(bg='#0a0a0a')
        self.root.option_add('*Font', 'Helvetica 12')
        
        # Set window icon
        try:
            icon_path = os.path.join(os.path.dirname(__file__), 'jarvis_icon.png')
            if os.path.exists(icon_path):
                self.root.iconphoto(False, tk.PhotoImage(file=icon_path))
        except Exception as e:
            logging.error(f"Error loading icon: {e}")

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

    def setup_commands(self):
        """Setup custom commands and their handlers"""
        self.command_handlers = {
            "time": self.get_current_time,
            "date": self.get_current_date,
            "weather": self.get_weather,
            "search": self.web_search,
            "wikipedia": self.wikipedia_search,
            "calculate": self.wolfram_calculate,
            "system info": self.get_system_info,
            "ip address": self.get_ip_address,
            "cpu": self.get_cpu_usage,
            "memory": self.get_memory_usage,
            "network": self.get_network_info,
            "clear": self.clear_chat,
            "theme": self.toggle_theme,
            "voice": self.toggle_voice_control,
            "help": self.show_help
        }

    def create_gui(self):
        """Create interface components"""
        # Main frame
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Chat display
        self.chat_area = scrolledtext.ScrolledText(
            self.main_frame,
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
        
        # Configure tags for different message types
        self.chat_area.tag_config('user', foreground='#00ff00')
        self.chat_area.tag_config('system', foreground='#ffffff')
        self.chat_area.tag_config('warning', foreground='#ffff00')
        self.chat_area.tag_config('error', foreground='#ff0000')
        self.chat_area.tag_config('jarvis', foreground='#ff6600')

        # Status bar
        self.status_bar = ttk.Label(
            self.main_frame,
            text="System: Ready | AI: Online | Voice: Off",
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_bar.pack(fill=tk.X, pady=(0, 5))

        # Input frame
        input_frame = ttk.Frame(self.main_frame)
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
            text="ENGAGE",
            command=self.process_input,
            style='Accent.TButton'
        ).pack(side=tk.RIGHT, padx=(10, 0))
        
        # Configure styles
        self.style = ttk.Style()
        self.style.configure('Accent.TButton', background='#ff6600', foreground='black')
        self.style.map('Accent.TButton',
                      background=[('active', '#ff8533'), ('pressed', '#cc5200')])

    def setup_voice(self):
        """Configure text-to-speech"""
        try:
            self.engine = pyttsx3.init()
            voices = self.engine.getProperty('voices')
            
            # Try to find a British male voice first, then any male voice
            preferred_voices = [
                ("english", "male", "british"),
                ("english", "male", ""),
                ("english", "", "")
            ]
            
            for lang, gender, accent in preferred_voices:
                for voice in voices:
                    if (lang in voice.languages and 
                        (not gender or gender in voice.name.lower()) and
                        (not accent or accent in voice.name.lower())):
                        self.engine.setProperty('voice', voice.id)
                        logging.info(f"Selected voice: {voice.name}")
                        break
                if self.engine.getProperty('voice'):
                    break
            
            self.engine.setProperty('rate', 170)
            self.engine.setProperty('volume', 0.95)
            logging.info("Voice engine initialized successfully")
        except Exception as e:
            logging.error(f"Voice setup error: {e}")
            self.engine = None

    def setup_responses(self):
        """Set up default responses"""
        hour = datetime.datetime.now().hour
        time_of_day = "morning" if 5 <= hour < 12 else "afternoon" if 12 <= hour < 17 else "evening"
        
        self.responses = {
            "greeting": [
                f"Systems online. Good {time_of_day}, {self.user_name}.",
                f"All systems operational. Good {time_of_day}, {self.user_name}.",
                f"Boot sequence complete. Good {time_of_day}, {self.user_name}."
            ],
            "error": [
                "I'm experiencing technical difficulties. Please try again later.",
                "System malfunction detected. Attempting recovery.",
                "Connection error. Switching to local protocols."
            ],
            "offline": [
                "AI systems offline. Running in limited capacity.",
                "Gemini connection unavailable. Local functions only.",
                "Advanced AI features currently unavailable."
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
            "voice_on": [
                "Voice recognition activated. I'm listening.",
                "Audio sensors online. Ready for voice commands.",
                "Voice control enabled. Speak now."
            ],
            "voice_off": [
                "Voice recognition deactivated.",
                "Audio sensors offline.",
                "Voice control disabled."
            ],
            "unknown": [
                "I don't understand that command. Please rephrase.",
                "Command not recognized. Try 'help' for available commands.",
                "That request is beyond my current protocols."
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
            self.jarvis_speak(self.responses["offline"][0])
        
        self.update_status_bar()

    def update_chat(self, speaker, message, tag=None):
        """Update the chat display"""
        self.chat_area.configure(state='normal')
        
        # Add timestamp
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.chat_area.insert(tk.END, f"[{timestamp}] ", 'timestamp')
        
        # Add message with appropriate tag
        self.chat_area.insert(tk.END, f"{speaker.upper()}: {message}\n\n", tag or speaker.lower())
        self.chat_area.configure(state='disabled')
        self.chat_area.see(tk.END)

    def jarvis_speak(self, text):
        """Convert text to speech"""
        self.update_chat("JARVIS", text)
        if self.engine:
            try:
                self.engine.say(text)
                self.engine.runAndWait()
            except Exception as e:
                logging.error(f"Speech synthesis error: {e}")
                self.update_chat("SYSTEM", f"Voice error: {str(e)}", 'error')

    def update_status_bar(self):
        """Update the status bar with current system status"""
        ai_status = "Online" if self.ai_enabled else "Offline"
        voice_status = "On" if self.voice_active else "Off"
        self.status_bar.config(
            text=f"System: Ready | AI: {ai_status} | Voice: {voice_status} | CPU: {psutil.cpu_percent()}% | RAM: {psutil.virtual_memory().percent}%"
        )
        self.root.after(5000, self.update_status_bar)

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
            logging.error(f"AI Generation Error: {e}")
            return random.choice(self.responses["error"])

    def process_input(self, event=None):
        """Handle user input"""
        command = self.user_input.get().strip()
        if not command:
            return
            
        self.update_chat("YOU", command, 'user')
        self.user_input.delete(0, tk.END)
        
        # Add command to queue for processing
        self.command_queue.put(command)

    def process_queue(self):
        """Process commands from the queue in a background thread"""
        while self.running:
            try:
                command = self.command_queue.get(timeout=0.1)
                self.handle_command(command)
            except queue.Empty:
                continue
            except Exception as e:
                logging.error(f"Command processing error: {e}")
                self.update_chat("SYSTEM", f"Error processing command: {e}", 'error')

    def handle_command(self, command):
        """Handle the actual command processing"""
        command_lower = command.lower()
        
        # System commands
        if command_lower in ["exit", "quit", "shutdown"]:
            self.shutdown()
            return
        
        # Application launch commands
        if any(cmd in command_lower for cmd in ["open ", "launch ", "start "]):
            for cmd in ["open ", "launch ", "start "]:
                if cmd in command_lower:
                    app_name = command_lower.split(cmd)[1].strip()
                    self.launch_application(app_name)
                    return
        
        # Check for registered commands
        for cmd, handler in self.command_handlers.items():
            if command_lower.startswith(cmd):
                handler(command[len(cmd):].strip())
                return
        
        # Default to AI query
        response = self.query_gemini(command)
        self.jarvis_speak(response)

    def toggle_voice_control(self):
        """Toggle voice recognition on/off"""
        if not hasattr(self, 'recognizer') or not hasattr(self, 'microphone'):
            self.jarvis_speak("Voice recognition not available")
            return
            
        self.voice_active = not self.voice_active
        self.update_status_bar()
        
        if self.voice_active:
            self.jarvis_speak(random.choice(self.responses["voice_on"]))
            threading.Thread(target=self.listen_for_voice, daemon=True).start()
        else:
            self.jarvis_speak(random.choice(self.responses["voice_off"]))

    def listen_for_voice(self):
        """Listen for voice commands when voice control is active"""
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)
            
        while self.voice_active and self.running:
            try:
                with self.microphone as source:
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                
                try:
                    command = self.recognizer.recognize_google(audio)
                    self.update_chat("YOU", command, 'user')
                    self.command_queue.put(command)
                except sr.UnknownValueError:
                    self.update_chat("SYSTEM", "Could not understand audio", 'warning')
                except sr.RequestError as e:
                    self.update_chat("SYSTEM", f"Voice recognition error: {e}", 'error')
                    self.voice_active = False
                    self.update_status_bar()
                
            except Exception as e:
                logging.error(f"Voice recognition error: {e}")
                self.voice_active = False
                self.update_status_bar()
                self.jarvis_speak("Voice recognition error. Switching to manual mode.")

    # Command handlers
    def get_current_time(self, _=None):
        """Return the current time"""
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        self.jarvis_speak(f"The current time is {current_time}")

    def get_current_date(self, _=None):
        """Return the current date"""
        current_date = datetime.datetime.now().strftime("%A, %B %d, %Y")
        self.jarvis_speak(f"Today is {current_date}")

    def get_weather(self, location):
        """Get weather for specified location"""
        if not self.weather_api_key:
            self.jarvis_speak("Weather API key not configured")
            return
            
        try:
            base_url = "http://api.openweathermap.org/data/2.5/weather?"
            complete_url = f"{base_url}q={location}&appid={self.weather_api_key}&units=metric"
            
            response = requests.get(complete_url)
            data = response.json()
            
            if data["cod"] != "404":
                main = data["main"]
                weather = data["weather"][0]
                
                temp = main["temp"]
                pressure = main["pressure"]
                humidity = main["humidity"]
                description = weather["description"]
                
                weather_report = (
                    f"Weather in {location}: {description}. "
                    f"Temperature: {temp}°C, Humidity: {humidity}%, Pressure: {pressure}hPa"
                )
                self.jarvis_speak(weather_report)
            else:
                self.jarvis_speak(f"Weather data not found for {location}")
                
        except Exception as e:
            logging.error(f"Weather API error: {e}")
            self.jarvis_speak("Unable to retrieve weather data at this time")

    def web_search(self, query):
        """Perform a web search"""
        try:
            url = f"https://www.google.com/search?q={query}"
            webbrowser.open(url)
            self.jarvis_speak(f"Searching the web for {query}")
        except Exception as e:
            logging.error(f"Web search error: {e}")
            self.jarvis_speak("Unable to perform web search")

    def wikipedia_search(self, query):
        """Search Wikipedia"""
        try:
            result = wikipedia.summary(query, sentences=2)
            self.jarvis_speak(f"According to Wikipedia: {result}")
        except wikipedia.exceptions.DisambiguationError as e:
            self.jarvis_speak(f"Multiple results found. Please be more specific: {e.options[:3]}")
        except wikipedia.exceptions.PageError:
            self.jarvis_speak("No Wikipedia page found for that query")
        except Exception as e:
            logging.error(f"Wikipedia search error: {e}")
            self.jarvis_speak("Unable to access Wikipedia at this time")

    def wolfram_calculate(self, query):
        """Perform calculations using Wolfram Alpha"""
        if not self.wolfram_app_id:
            self.jarvis_speak("Wolfram Alpha API not configured")
            return
            
        try:
            client = wolframalpha.Client(self.wolfram_app_id)
            res = client.query(query)
            
            if res['@success'] == 'true':
                answer = next(res.results).text
                self.jarvis_speak(f"The result is: {answer}")
            else:
                self.jarvis_speak("Unable to compute that expression")
                
        except Exception as e:
            logging.error(f"Wolfram Alpha error: {e}")
            self.jarvis_speak("Calculation service unavailable")

    def get_system_info(self, _=None):
        """Display system information"""
        try:
            info = [
                f"System: {platform.system()} {platform.release()}",
                f"Processor: {platform.processor()}",
                f"Python: {platform.python_version()}",
                f"CPU Cores: {psutil.cpu_count()}",
                f"Total RAM: {round(psutil.virtual_memory().total / (1024**3), 2)} GB"
            ]
            
            self.jarvis_speak("System information: " + ". ".join(info))
        except Exception as e:
            logging.error(f"System info error: {e}")
            self.jarvis_speak("Unable to retrieve system information")

    def get_ip_address(self, _=None):
        """Get the system's IP address"""
        try:
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
            self.jarvis_speak(f"Your IP address is {ip_address}")
        except Exception as e:
            logging.error(f"IP address error: {e}")
            self.jarvis_speak("Unable to determine IP address")

    def get_cpu_usage(self, _=None):
        """Get current CPU usage"""
        try:
            usage = psutil.cpu_percent(interval=1)
            self.jarvis_speak(f"Current CPU usage: {usage}%")
        except Exception as e:
            logging.error(f"CPU usage error: {e}")
            self.jarvis_speak("Unable to check CPU usage")

    def get_memory_usage(self, _=None):
        """Get current memory usage"""
        try:
            mem = psutil.virtual_memory()
            self.jarvis_speak(
                f"Memory usage: {mem.percent}% (Used: {round(mem.used / (1024**3), 2)}GB, "
                f"Available: {round(mem.available / (1024**3), 2)}GB)"
            )
        except Exception as e:
            logging.error(f"Memory usage error: {e}")
            self.jarvis_speak("Unable to check memory usage")

    def get_network_info(self, _=None):
        """Get network information"""
        try:
            net_io = psutil.net_io_counters()
            info = [
                f"Bytes Sent: {round(net_io.bytes_sent / (1024**2), 2)} MB",
                f"Bytes Received: {round(net_io.bytes_recv / (1024**2), 2)} MB"
            ]
            self.jarvis_speak("Network statistics: " + ", ".join(info))
        except Exception as e:
            logging.error(f"Network info error: {e}")
            self.jarvis_speak("Unable to retrieve network information")

    def clear_chat(self, _=None):
        """Clear the chat window"""
        self.chat_area.configure(state='normal')
        self.chat_area.delete(1.0, tk.END)
        self.chat_area.configure(state='disabled')
        self.jarvis_speak("Chat history cleared")

    def toggle_theme(self, _=None):
        """Toggle between dark and light themes"""
        if self.current_theme == 'dark':
            self.current_theme = 'light'
            self.chat_area.configure(bg='white', fg='black')
            self.status_bar.configure(background='#f0f0f0', foreground='black')
        else:
            self.current_theme = 'dark'
            self.chat_area.configure(bg='#0a0a0a', fg='#ff6600')
            self.status_bar.configure(background='#1a1a1a', foreground='white')
        
        self.jarvis_speak(f"Switched to {self.current_theme} theme")

    def show_help(self, _=None):
        """Display help information"""
        help_text = """
Available commands:
- time: Show current time
- date: Show current date
- weather [location]: Get weather for specified location
- search [query]: Perform a web search
- wikipedia [query]: Search Wikipedia
- calculate [expression]: Perform calculations
- system info: Display system information
- ip address: Show system IP address
- cpu: Show CPU usage
- memory: Show memory usage
- network: Show network statistics
- open/launch [app]: Launch an application
- clear: Clear chat history
- theme: Toggle between dark/light themes
- voice: Toggle voice control
- help: Show this help message
- exit/quit: Shutdown JARVIS
"""
        self.update_chat("HELP", help_text.strip(), 'system')

    def system_monitor(self):
        """Monitor system resources in the background"""
        while self.running:
            try:
                cpu = psutil.cpu_percent()
                mem = psutil.virtual_memory().percent
                
                if cpu > 90 or mem > 90:
                    warning = f"Warning: High system load (CPU: {cpu}%, RAM: {mem}%)"
                    self.update_chat("SYSTEM", warning, 'warning')
                
                time.sleep(10)
            except Exception as e:
                logging.error(f"System monitor error: {e}")
                time.sleep(30)

    def shutdown(self):
        """Clean shutdown procedure"""
        self.running = False
        self.jarvis_speak("Initiating shutdown sequence. Goodbye.")
        time.sleep(1)
        
        if self.engine:
            self.engine.stop()
        
        self.root.destroy()

def __init__(self, root):
    try:
        self.root = root
        self.user_name = "Sir"
        self.system_os = platform.system()
        
        # Initialize components
        self.configure_window()
        self.setup_gemini()
        self.create_gui()
        self.setup_voice()
        self.setup_responses()
        self.setup_applications()
        self.boot_sequence()
    except Exception as e:
        print(f"Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")  # Keeps window open to see error


if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = JARVIS(root)
        
        # Handle window close
        root.protocol("WM_DELETE_WINDOW", app.shutdown)
        
        # Set window icon if available
        try:
            if platform.system() == "Windows":
                root.iconbitmap(default='jarvis.ico')
        except:
            pass
        
        root.mainloop()
    except Exception as e:
        logging.critical(f"Fatal error: {e}")
        messagebox.showerror("JARVIS Error", f"A critical error occurred: {str(e)}")