import tkinter as tk
from tkinter import scrolledtext, font, messagebox
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
import queue
import threading
import sys
import traceback

class JARVIS:
    def __init__(self, root):
        self.root = root
        self.user_name = "Sir"
        self.ai_enabled = False
        self.running = True  # Flag to control thread execution
        self.command_queue = queue.Queue()
        
        try:
            # Initialize components
            self.configure_window()
            self.setup_gemini()
            self.create_gui()
            self.setup_voice()
            self.setup_responses()
            self.boot_sequence()

            # Start command processing thread
            threading.Thread(target=self.process_queue, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Initialization Error", f"Failed to initialize JARVIS:\n{str(e)}")
            traceback.print_exc()
            self.root.destroy()

    def configure_window(self):
        """Configure main window appearance"""
        self.root.title("JARVIS Protocol")
        self.root.geometry("800x600")
        self.root.configure(bg='#0a0a0a')
        self.root.option_add('*Font', 'Helvetica 12')
        
        # Handle window close properly
        self.root.protocol("WM_DELETE_WINDOW", self.shutdown)

    def shutdown(self):
        """Clean shutdown procedure"""
        self.running = False
        if hasattr(self, 'engine'):
            self.engine.stop()
        self.root.destroy()

    def setup_gemini(self):
        """Initialize Gemini AI with better error handling"""
        try:
            load_dotenv()
            api_key = os.getenv('GEMINI_API_KEY')

            if not api_key:
                print("Gemini API key not found in .env file")
                self.ai_enabled = False
                return

            genai.configure(api_key=api_key)
            
            # Try multiple model versions
            try:
                self.model = genai.GenerativeModel('gemini-1.5-flash')
            except:
                try:
                    self.model = genai.GenerativeModel('gemini-1.0-pro')
                except Exception as e:
                    print(f"Model initialization failed: {e}")
                    self.ai_enabled = False
                    return
            
            # Test connection
            try:
                test_query = self.model.generate_content("Test connection")
                if test_query.text:
                    self.ai_enabled = True
                    print("Gemini AI connected successfully")
                else:
                    raise Exception("Empty response from Gemini")
            except Exception as e:
                print(f"Gemini test failed: {e}")
                self.ai_enabled = False
                
        except Exception as e:
            print(f"Gemini setup error: {e}")
            self.ai_enabled = False

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
        try:
            self.engine = pyttsx3.init()
            voices = self.engine.getProperty('voices')
            for voice in voices:
                if "english" in voice.languages and "male" in voice.name.lower():
                    self.engine.setProperty('voice', voice.id)
                    break
            self.engine.setProperty('rate', 170)
            self.engine.setProperty('volume', 0.95)
        except Exception as e:
            print(f"Voice setup error: {e}")
            self.engine = None

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
        if self.engine:
            try:
                self.engine.say(text)
                self.engine.runAndWait()
            except Exception as e:
                print(f"Speech synthesis error: {e}")

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
            self.shutdown()
            return
            
        # Add command to queue for processing
        self.command_queue.put(command)

    def process_queue(self):
        """Process commands from the queue in a background thread"""
        while self.running:  # Use running flag to control the loop
            try:
                command = self.command_queue.get(timeout=0.1)
                response = self.query_gemini(command)
                self.jarvis_speak(response)
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Command processing error: {e}")

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = JARVIS(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("JARVIS Error", f"A critical error occurred: {str(e)}")
        sys.exit(1)