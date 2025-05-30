import sys
if not hasattr(sys.stdout, "fileno"):
    import io
    sys.stdout = io.StringIO()
if not hasattr(sys.stderr, "fileno"):
    import io
    sys.stderr = io.StringIO()

import os
import sys
import time
import pyttsx3
import speech_recognition as sr
import datetime
import webbrowser
import wikipedia
import pyautogui
import psutil
import subprocess
import shutil
import requests
import random
import speedtest
import tkinter as tk
import winreg
from tkinter import simpledialog, messagebox
from PIL import ImageGrab, Image
import pyperclip
import re
import traceback
from threading import Timer
from difflib import SequenceMatcher

# === API KEYS ===
WEATHER_API_KEY = "ff80fe49f6d921cb7686df6917015a51"
NEWS_API_KEY = "f9adae143f4a4e738932ce3122d7ff31"

PASSWORD = os.getenv("JARVIS_PASSWORD", "1234")
USER_NAME = "Sir"
NOTES_FOLDER = "Jarvis_Notes"
TODO_FILE = "todo.txt"
REMINDERS_FILE = "reminders.txt"
SLEEP_MODE = False
SILENT_MODE = False
WHISPER_MODE = False
# === JARVIS FEATURE FUNCTIONS ===

import threading

def set_volume(level):  # 0-100
    import ctypes
    ctypes.windll.winmm.waveOutSetVolume(0, int(level * 65535 / 100) * 0x10001)

def mute_volume():
    pyautogui.press('volumemute')

def volume_up():
    pyautogui.press('volumeup')

def volume_down():
    pyautogui.press('volumedown')

def set_brightness(level):  # 0-100
    try:
        import screen_brightness_control as sbc
        sbc.set_brightness(level)
    except ImportError:
        speak("Install screen_brightness_control for brightness commands.")

def open_app(exe_path):
    try:
        subprocess.Popen(exe_path)
    except Exception:
        speak("Could not open application.")

def close_app(process_name):
    os.system(f"taskkill /f /im {process_name}")

recording = False

def start_screen_recording(filename="recording.avi", duration=10):
    global recording
    recording = True
    import cv2
    import numpy as np
    screen_size = pyautogui.size()
    fourcc = cv2.VideoWriter_fourcc(*"XVID")
    out = cv2.VideoWriter(filename, fourcc, 20.0, screen_size)
    start_time = time.time()
    while recording and (time.time() - start_time < duration):
        img = pyautogui.screenshot()
        frame = np.array(img)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        out.write(frame)
    out.release()

def stop_screen_recording():
    global recording
    recording = False

def read_text_file(filepath):
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        speak(content)
    except Exception:
        speak("Could not read the file.")

def write_text_file(filepath, text):
    try:
        with open(filepath, 'a') as f:
            f.write(text + '\n')
        speak("Text added to file.")
    except Exception:
        speak("Could not write to the file.")

def countdown_timer(seconds):
    def timer():
        time.sleep(seconds)
        speak("Time's up!")
    threading.Thread(target=timer).start()

stopwatch_start_time = None

def start_stopwatch():
    global stopwatch_start_time
    stopwatch_start_time = time.time()
    speak("Stopwatch started.")

def stop_stopwatch():
    global stopwatch_start_time
    if stopwatch_start_time is not None:
        elapsed = time.time() - stopwatch_start_time
        mins, secs = divmod(int(elapsed), 60)
        speak(f"Stopwatch stopped at {mins} minutes, {secs} seconds.")
        stopwatch_start_time = None
    else:
        speak("Stopwatch was not started.")

def inches_to_cm(inches):
    return inches * 2.54

def cm_to_inches(cm):
    return cm / 2.54

def celsius_to_fahrenheit(c):
    return (c * 9/5) + 32

def fahrenheit_to_celsius(f):
    return (f - 32) * 5/9

def move_mouse(x, y):
    pyautogui.moveTo(x, y)

def click_mouse():
    pyautogui.click()

def type_text(text):
    pyautogui.write(text)

def add_to_startup():
    try:
        script_path = os.path.abspath(sys.argv[0])
        startup_folder = os.path.join(
            os.environ["APPDATA"],
            r"Microsoft\Windows\Start Menu\Programs\Startup"
        )
        os.makedirs(startup_folder, exist_ok=True)
        bat_path = os.path.join(startup_folder, "Jarvis_Assistant.bat")
        bat_content = f'@echo off\npythonw "{script_path}"\n'
        if not os.path.exists(bat_path) or open(bat_path).read() != bat_content:
            with open(bat_path, "w") as bat_file:
                bat_file.write(bat_content)
            print(f"Startup file created: {bat_path}")
        return True
    except Exception as e:
        print(f"Failed to configure startup: {str(e)}")
        return False

engine = pyttsx3.init()
engine.setProperty('rate', 180)
voices = engine.getProperty('voices')
if voices:
    engine.setProperty('voice', voices[1].id if len(voices) > 1 else voices[0].id)

def speak(text):
    global SILENT_MODE, WHISPER_MODE, SLEEP_MODE
    if SILENT_MODE or SLEEP_MODE:
        return
    engine.setProperty('volume', 0.3 if WHISPER_MODE else 1.0)
    print(f"🔊: {text}")
    try:
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print("Speech error:", e)

def wish_user():
    hour = datetime.datetime.now().hour
    greeting = "Good morning" if 5 <= hour < 12 else "Good afternoon" if 12 <= hour < 18 else "Good evening"
    speak(f"{greeting}, {USER_NAME}. System operational.")

def take_command():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Calibrating microphone for ambient noise...")
        recognizer.adjust_for_ambient_noise(source, duration=1.0)  # Shorter, more responsive
        recognizer.energy_threshold = 250  # Lowered for better sensitivity
        recognizer.dynamic_energy_threshold = True
        recognizer.pause_threshold = 0.8   # Faster end-of-speech detection
        recognizer.phrase_threshold = 0.3
        recognizer.operation_timeout = 5   # Faster timeout if no speech detected
        print("🔍 Listening...")
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
            query = recognizer.recognize_google(audio, language='en-in').lower()
            print(f"🗣️ User: {query}")
            return query
        except sr.WaitTimeoutError:
            print("No speech detected. Please try again.")
            return ""
        except sr.UnknownValueError:
            if not SLEEP_MODE:
                speak("Sorry, I didn't catch that. Please repeat.")
            return ""
        except Exception as e:
            print("Recognition error:", e)
            return ""




def get_installed_apps():
    apps = []
    reg_paths = [
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
        r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
    ]
    for hive in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
        for path in reg_paths:
            try:
                key = winreg.OpenKey(hive, path)
                for i in range(0, winreg.QueryInfoKey(key)[0]):
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        subkey = winreg.OpenKey(key, subkey_name)
                        name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                        cmd = None
                        try:
                            cmd = winreg.QueryValueEx(subkey, "DisplayIcon")[0]
                            if "," in cmd:
                                cmd = cmd.split(",", 1)[0]
                        except:
                            pass
                        if not cmd:
                            try:
                                cmd = winreg.QueryValueEx(subkey, "UninstallString")[0]
                            except:
                                continue
                        apps.append({
                            "name": name.lower().strip(),
                            "command": cmd,
                            "raw_name": name
                        })
                    except:
                        continue
            except:
                continue
    apps.extend([
        {"name": "notepad", "command": "notepad.exe", "raw_name": "Notepad"},
        {"name": "calculator", "command": "calc.exe", "raw_name": "Calculator"},
        {"name": "paint", "command": "mspaint.exe", "raw_name": "Paint"},
        {"name": "cmd", "command": "cmd.exe", "raw_name": "Command Prompt"}
    ])
    return apps

def find_application(target):
    target = target.lower().strip()
    apps = get_installed_apps()
    for app in apps:
        if app["name"] == target:
            return app
    for app in apps:
        if target in app["name"]:
            return app
    matches = []
    for app in apps:
        ratio = SequenceMatcher(None, target, app["name"]).ratio()
        if ratio > 0.75:
            matches.append((ratio, app))
    return max(matches, key=lambda x: x[0])[1] if matches else None

def parse_alarm_time(alarm_str):
    alarm_str = alarm_str.strip().lower().replace(' ', '')
    match = re.match(r'(\d{1,2})(:?(\d{2}))?(am|pm)?', alarm_str)
    if not match:
        return None
    hour_part, _, minute_part, meridian = match.groups()
    hour = int(hour_part)
    minute = int(minute_part) if minute_part else 0
    if meridian:
        if meridian == 'pm' and hour != 12:
            hour += 12
        elif meridian == 'am' and hour == 12:
            hour = 0
    return hour, minute

def alarm_trigger():
    try:
        from playsound import playsound
        playsound('alarm.mp3')
    except Exception:
        speak("Wake up! This is your alarm.")

def handle_command(query):
    global SILENT_MODE, WHISPER_MODE, USER_NAME, SLEEP_MODE

    if "sleep" in query:
        speak("Going to sleep. Say 'wake up' to activate me.")
        SLEEP_MODE = True
        return

    if "wake up" in query:
        SLEEP_MODE = False
        speak("I'm awake and ready!")
        speak("ok.")
        return

    # ... more commands, all indented at this level ...






    # Name Change
    if "call me" in query:
        new_name = query.replace("call me", "").strip().title()
        USER_NAME = new_name
        speak(f"Okay, I'll call you {USER_NAME} from now on.")
        return

    # Greetings/Jokes
    if "how are you" in query:
        speak("I'm always ready to help you!")
        return
    if "tell me a joke" in query:
        jokes = [
            "Why did the computer show up at work late? It had a hard drive!",
            "Why do programmers prefer dark mode? Because light attracts bugs.",
            "Why did the PowerPoint Presentation cross the road? To get to the other slide!"
        ]
        speak(random.choice(jokes))
        return

    # System Control
    if "lock" in query:
        try:
            import ctypes
            ctypes.windll.user32.LockWorkStation()
            speak("System locked")
        except:
            speak("Locking failed")
        return
    if "shutdown" in query:
        speak("Initiating shutdown in 10 seconds")
        os.system("shutdown /s /t 10")
        return
    if "system info" in query:
        try:
            cpu = psutil.cpu_percent()
            mem = psutil.virtual_memory().percent
            disk = psutil.disk_usage('/').percent
            speak(f"CPU: {cpu}%, Memory: {mem}%, Disk: {disk}%")
        except:
            speak("System stats unavailable")
        return
    if "battery status" in query:
        try:
            battery = psutil.sensors_battery()
            if battery:
                status = "charging" if battery.power_plugged else "not charging"
                speak(f"Battery at {battery.percent}% ({status})")
            else:
                speak("Battery information unavailable")
        except:
            speak("Failed to check battery status.")
        return
    if "screenshot" in query:
        screenshot = ImageGrab.grab()
        filename = f"screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        screenshot.save(filename)
        speak(f"Screenshot saved as {filename}")
        return
    if "type clipboard" in query:
        text = pyperclip.paste()
        pyautogui.write(text)
        speak("Clipboard content typed")
        return

    # File Management
    if "create note" in query:
        speak("Note title?")
        title = take_command().replace(" ", "_")
        speak("Note content?")
        content = take_command()
        try:
            os.makedirs(NOTES_FOLDER, exist_ok=True)
            with open(f"{NOTES_FOLDER}/{title}.txt", "w") as f:
                f.write(content)
            speak("Note saved successfully")
        except:
            speak("Note saving failed")
        return
    if "search files" in query:
        speak("What file are you looking for?")
        filename = take_command()
        result = []
        for root, dirs, files in os.walk(os.path.expanduser("~")):
            if filename in files:
                result.append(os.path.join(root, filename))
        if result:
            speak(f"Found {len(result)} matches. The first is {result[0]}")
        else:
            speak("No files found")
        return
    if "create folder" in query:
        name = query.replace("create folder", "").strip() or "New Folder"
        path = os.path.join(os.path.expanduser("~"), name)
        try:
            os.makedirs(path, exist_ok=True)
            speak(f"Created folder: {name}")
        except Exception as e:
            speak("Failed to create folder")
        return
    if "delete temporary" in query:
        try:
            temp_dir = os.environ.get('TEMP')
            deleted = 0
            for entry in os.listdir(temp_dir):
                path = os.path.join(temp_dir, entry)
                try:
                    if os.path.isfile(path):
                        os.unlink(path)
                        deleted += 1
                    elif os.path.isdir(path):
                        shutil.rmtree(path)
                        deleted += 1
                except Exception:
                    continue
            speak(f"Cleared {deleted} temporary items")
        except Exception as e:
            speak("Failed to clear temporary files")
        return

    # Productivity
    if "to-do list" in query:
        if not os.path.exists(TODO_FILE):
            open(TODO_FILE, "w").close()
        with open(TODO_FILE, "r") as f:
            items = f.readlines()
            if not items:
                speak("No items in your to-do list")
                return
            speak("Your to-do list:")
            for i, item in enumerate(items, 1):
                speak(f"{i}. {item.strip()}")
        return
    if "add to-do" in query:
        speak("What should I add to your to-do list?")
        task = take_command()
        with open(TODO_FILE, "a") as f:
            f.write(f"{task}\n")
        speak("Task added to your to-do list")
        return
    if "remind me" in query:
        task = query.replace("remind me to", "").strip()
        with open(REMINDERS_FILE, "a") as f:
            f.write(f"{datetime.datetime.now()} - {task}\n")
        speak("Reminder set successfully")
        return

    # Media Control
    if any(word in query for word in ["play", "pause", "volume", "next", "previous"]):
        key_map = {
            "play": "playpause",
            "pause": "playpause",
            "volume up": "volumeup",
            "volume down": "volumedown",
            "next": "nexttrack",
            "previous": "prevtrack"
        }
        pyautogui.press(key_map.get(query.split()[-1], "playpause"))
        speak(f"Media {query.split()[-1]}")
        return

    # Security
    if "generate password" in query:
        chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890!@#$%^&*()"
        password = ''.join(random.choice(chars) for _ in range(12))
        pyperclip.copy(password)
        speak("Generated password copied to clipboard")
        return

    # Universal App Launcher
    if "open" in query:
        app_name = query.replace("open", "").strip()
        app = find_application(app_name)
        if app:
            try:
                subprocess.Popen(app["command"], shell=True)
                speak(f"Opening {app['raw_name']}")
            except:
                speak("Failed to launch application")
        else:
            speak("Application not found")
        return

    # Alarm
    if "alarm" in query:
        speak("Please say the alarm time (e.g., '7:30 PM' or '19:30').")
        alarm_time = take_command()
        parsed = parse_alarm_time(alarm_time)
        if not parsed:
            speak("Invalid time format.")
            return
        hour, minute = parsed
        now = datetime.datetime.now()
        alarm_time_dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if alarm_time_dt <= now:
            alarm_time_dt += datetime.timedelta(days=1)
        speak(f"Alarm set for {alarm_time_dt.strftime('%I:%M %p')}")
        delay = (alarm_time_dt - datetime.datetime.now()).total_seconds()
        Timer(delay, alarm_trigger).start()
        return

    # Quiz
    if "play quiz" in query:
        questions = {
            "What is 15 plus 27?": "42",
            "Square root of 144?": "12",
            "5 factorial equals?": "120",
            "2 to the power of 10?": "1024",
            "What is the capital of France?": "paris",
            "Who wrote 'Romeo and Juliet'?": "shakespeare",
            "What is the chemical symbol for water?": "h2o",
            "What is the largest planet in our solar system?": "jupiter",
            "What year did World War II end?": "1945",
            "What is the value of Pi (to 2 decimal places)?": "3.14"
        }
        selected = random.sample(list(questions.items()), 5)
        score = 0
        for q, ans in selected:
            speak(q)
            user_ans = take_command()
            if user_ans is None:
                speak("No answer detected.")
                continue
            if user_ans.strip().lower() == str(ans).strip().lower():
                speak("Correct!")
                score += 1
            else:
                speak(f"Incorrect. The correct answer is {ans}.")
        speak(f"Quiz complete! You scored {score} out of 5.")
        return

    # WhatsApp
    from tkinter import simpledialog

    if "whatsapp" in query or "send message" in query or "send whatsapp message" in query:
        try:
            speak("Please enter the phone number with country code (e.g., +9198xxxxxxx).")
            root = tk.Tk()
            root.withdraw()  # Hide the main window
            number = simpledialog.askstring("WhatsApp", "Enter phone number with country code (e.g., +9198xxxxxxx):")
            root.destroy()
            if not number:
                speak("No number entered. Cancelling WhatsApp message.")
                return
            number = number.replace(" ", "")
            if not re.match(r"^\+\d{10,15}$", number):
                speak("Invalid number format. Please try again.")
                return
            speak("What should I say?")
            message = take_command()
            import pywhatkit
            try:
                webbrowser.get('chrome')
                pywhatkit.sendwhatmsg_instantly(number, message, tab_close=True)
            except webbrowser.Error:
                speak("Chrome browser not available")
                return
            speak("WhatsApp message sent.")
            speak("Ok.")
        except Exception as e:
            speak(f"Failed to send message: {str(e)}")
        return



    # Speed Test
    if "check internet speed" in query:
        try:
            st = speedtest.Speedtest()
            speak("Checking internet speed...")
            download = st.download() / 1_000_000
            upload = st.upload() / 1_000_000
            speak(f"Download: {download:.2f} Mbps, Upload: {upload:.2f} Mbps")
        except Exception as e:
            speak("Could not check internet speed.")
        return

    # Wikipedia
    if "wikipedia" in query:
        try:
            search = query.replace("search wikipedia for", "").strip()
            result = wikipedia.summary(search, sentences=2, auto_suggest=False)
            speak(result)
        except Exception as e:
            speak("Sorry, I couldn't find that on Wikipedia.")
        return

    # YouTube
    if "youtube" in query:
        search = query.replace("search youtube for", "").strip()
        speak(f"Searching YouTube for {search}")
        webbrowser.open(f"https://www.youtube.com/results?search_query={search.replace(' ', '+')}")
        return

    # Google Search
    if "search google for" in query:
        search = query.replace("search google for", "").strip()
        speak(f"Searching Google for {search}")
        webbrowser.open(f"https://www.google.com/search?q={search.replace(' ', '+')}")
        return

    # Weather
    if "weather" in query:
        speak("Which city?")
        city = take_command()
        if not city:
            return
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
            response = requests.get(url).json()
            if response["cod"] == 200:
                temp = response["main"]["temp"]
                desc = response["weather"][0]["description"]
                speak(f"The temperature in {city} is {temp}°C with {desc}")
            else:
                speak("City not found.")
        except Exception as e:
            speak("Failed to fetch weather information.")
        return

    # News
    if "news" in query:
        try:
            url = f"https://newsapi.org/v2/top-headlines?country=in&apiKey={NEWS_API_KEY}"
            data = requests.get(url).json()
            articles = data.get("articles", [])[:5]
            if articles:
                speak("Top headlines:")
                for article in articles:
                    speak(article.get("title", "Untitled article"))
            else:
                speak("No current news available.")
        except Exception as e:
            speak("Couldn't fetch news updates.")
        return

    # Calculator
    if "calculate" in query:
        expression = query.replace("calculate", "").strip()
        try:
            result = eval(expression)
            speak(f"The result is {result}")
        except:
            speak("Invalid calculation expression.")
        return

    # Voice Modes
    if "silent mode" in query:
        SILENT_MODE = True
        speak("Silent mode activated.")
        return
    if "whisper mode" in query:
        WHISPER_MODE = True
        speak("Whisper mode activated.")
        return
    if "normal mode" in query:
        SILENT_MODE = False
        WHISPER_MODE = False
        speak("Normal mode activated.")
        return

    # Time/Date
    if "what time is it" in query or "current time" in query:
        now = datetime.datetime.now().strftime("%I:%M %p")
        speak(f"The current time is {now}")
        return
    if "what date is it" in query or "current date" in query:
        today = datetime.datetime.now().strftime("%A, %d %B %Y")
        speak(f"Today's date is {today}")
        return
        # === JARVIS FEATURE COMMANDS ===


    # Volume and Brightness
    if "set volume to" in query:
        try:
            level = int(re.search(r"set volume to (\d+)", query).group(1))
            set_volume(level)
            speak(f"Volume set to {level} percent.")
            return
        except:
            speak("Please specify a volume between 0 and 100.")
            return

    if "mute volume" in query:
        mute_volume()
        speak("Volume muted.")
        return

    if "volume up" in query:
        volume_up()
        speak("Volume increased.")
        return

    if "volume down" in query:
        volume_down()
        speak("Volume decreased.")
        return

    if "set brightness to" in query:
        try:
            level = int(re.search(r"set brightness to (\d+)", query).group(1))
            set_brightness(level)
            speak(f"Brightness set to {level} percent.")
            return
        except:
            speak("Please specify a brightness between 0 and 100.")
            return

    # Open/Close Applications
    if query.startswith("open "):
        app = query.replace("open ", "").strip()
        open_app(app + ".exe")
        speak(f"Opening {app}.")
        return

    if query.startswith("close "):
        app = query.replace("close ", "").strip()
        close_app(app + ".exe")
        speak(f"Closed {app}.")
        return

    # Screen Recording
    if "start screen recording" in query:
        duration = 10  # default duration
        match = re.search(r"for (\d+) seconds", query)
        if match:
            duration = int(match.group(1))
        threading.Thread(target=start_screen_recording, args=("recording.avi", duration)).start()
        speak(f"Screen recording started for {duration} seconds.")
        return

    if "stop screen recording" in query:
        stop_screen_recording()
        speak("Screen recording stopped.")
        return

    # Text File Reading and Writing
    if "read file" in query:
        speak("Please say the filename.")
        filename = take_command()
        read_text_file(filename)
        return

    if "write to file" in query:
        speak("Please say the filename.")
        filename = take_command()
        speak("What should I write?")
        text = take_command()
        write_text_file(filename, text)
        return

    # Countdown Timer
    if "set timer for" in query:
        match = re.search(r"set timer for (\d+) (seconds|minutes)", query)
        if match:
            value = int(match.group(1))
            unit = match.group(2)
            seconds = value * 60 if "minute" in unit else value
            countdown_timer(seconds)
            speak(f"Timer set for {value} {unit}.")
            return
        else:
            speak("Please specify the timer duration.")
            return

    # Stopwatch
    if "start stopwatch" in query:
        start_stopwatch()
        return

    if "stop stopwatch" in query:
        stop_stopwatch()
        return

    # Unit Conversion
    if "convert" in query:
        match = re.search(r"convert (\d+(\.\d+)?) (\w+) to (\w+)", query)
        if match:
            value = float(match.group(1))
            from_unit = match.group(3)
            to_unit = match.group(4)
            result = None
            if from_unit == "inches" and to_unit == "cm":
                result = inches_to_cm(value)
            elif from_unit == "cm" and to_unit == "inches":
                result = cm_to_inches(value)
            elif from_unit == "celsius" and to_unit == "fahrenheit":
                result = celsius_to_fahrenheit(value)
            elif from_unit == "fahrenheit" and to_unit == "celsius":
                result = fahrenheit_to_celsius(value)
            if result is not None:
                speak(f"{value} {from_unit} is {result:.2f} {to_unit}.")
                return
            else:
                speak("Sorry, I can't convert those units yet.")
                return

    # Desktop Automation
    if "move mouse to" in query:
        match = re.search(r"move mouse to (\d+),? ?(\d+)", query)
        if match:
            x, y = int(match.group(1)), int(match.group(2))
            move_mouse(x, y)
            speak(f"Mouse moved to {x}, {y}.")
            return

    if "click mouse" in query:
        click_mouse()
        speak("Mouse clicked.")
        return

    if "type" in query and "on screen" in query:
        text = query.replace("type", "").replace("on screen", "").strip()
        type_text(text)
        speak("Typed the text.")
        return

    # Exit
    if "bye" in query or "goodbye" in query:
        speak("Goodbye!")
        sys.exit()
        
    
    speak("Command not recognized.")

def run_voice_assistant():
    wish_user()
    while True:
        try:
            if SLEEP_MODE:
                # Give feedback when entering sleep mode
                speak("Going to sleep. Say 'wake up' to activate me.")
                while SLEEP_MODE:
                    query = take_command()
                    if "wake up" in query:
                        handle_command(query)  # This will set SLEEP_MODE = False
                        break
                    else:
                        speak("I'm asleep. Say 'wake up' to activate me.")
            else:
                query = take_command()
                if query:
                    handle_command(query)
        except Exception as e:
            print("Error:", e)
            import traceback
            traceback.print_exc()
            with open("jarvis_errors.log", "a") as f:
                import datetime
                f.write(f"{datetime.datetime.now()} - {str(e)}\n")
            speak("Error detected. Restarting...")
            import time
            time.sleep(5)


def create_gui():
    window = tk.Tk()
    window.title("JARVIS 2.0")
    window.geometry("400x300")
    window.configure(bg="#000000")
    
    tk.Label(window, text="JARVIS 2.0", font=("Helvetica", 24), 
            bg="#000000", fg="#00FFFF").pack(pady=15)
    
    status_label = tk.Label(window, text="Status: Ready", font=("Arial", 12), 
                          bg="#000000", fg="#00FF00")
    status_label.pack(pady=10)
    
    def start_assistant():
        window.withdraw()
        authenticate(window)
    
    button_frame = tk.Frame(window, bg="#000000")
    button_frame.pack(pady=20)
    
    tk.Button(button_frame, text="Start", command=start_assistant,
             bg="#00AA00", fg="white", width=15).pack(pady=5)
    
    tk.Button(button_frame, text="Exit", command=window.quit,
             bg="#AA0000", fg="white", width=15).pack(pady=5)
    
    window.mainloop()

def authenticate(parent_window):
    password = simpledialog.askstring("Authentication", 
                                    "Enter access code:", 
                                    parent=parent_window,
                                    show="*")
    if password == PASSWORD:
        speak("Authentication successful")
        if add_to_startup():
            speak("24/7 operation configured")
        else:
            speak("Warning: Could not configure auto-start")
        run_voice_assistant()
    else:
        speak("Access denied")
        
        
        sys.exit()

if __name__ == "__main__":
    os.makedirs(NOTES_FOLDER, exist_ok=True)
    create_gui()

