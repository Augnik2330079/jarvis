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

# === API KEYS ===
WEATHER_API_KEY = "ff80fe49f6d921cb7686df6917015a51"
NEWS_API_KEY = "f9adae143f4a4e738932ce3122d7ff31"

engine = pyttsx3.init()
engine.setProperty('rate', 180)

SILENT_MODE = False
WHISPER_MODE = False

# Cache for installed applications
INSTALLED_APPS_CACHE = []
CACHE_TIMESTAMP = 0
CACHE_DURATION = 3600  # 1 hour cache

def speak(text):
    global SILENT_MODE, WHISPER_MODE
    if SILENT_MODE:
        return
    if WHISPER_MODE:
        engine.setProperty('volume', 0.3)
    else:
        engine.setProperty('volume', 1.0)
    print(f"🔊: {text}")
    engine.say(text)
    engine.runAndWait()

def wish_user():
    hour = datetime.datetime.now().hour
    if 0 <= hour < 12:
        greet = "Good morning"
    elif 12 <= hour < 18:
        greet = "Good afternoon"
    else:
        greet = "Good evening"
    speak(f"{greet}, Sir. System ready and listening.")

def take_command():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎤 Listening...")
        recognizer.pause_threshold = 1
        audio = recognizer.listen(source, phrase_time_limit=5)
    try:
        query = recognizer.recognize_google(audio, language='en-in')
        print(f"You said: {query}")
    except sr.UnknownValueError:
        speak("Sorry, I didn't catch that.")
        return ""
    return query.lower()

def parse_alarm_time(alarm_str):
    import re
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

def set_alarm(alarm_time_str):
    parsed = parse_alarm_time(alarm_time_str)
    if not parsed:
        speak("Invalid time format. Please use format like '7:44 PM' or '19:44'")
        return
    hour, minute = parsed
    now = datetime.datetime.now()
    alarm_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if alarm_time <= now:
        alarm_time += datetime.timedelta(days=1)
    speak(f"Alarm set for {alarm_time.strftime('%I:%M %p')}")
    while True:
        if datetime.datetime.now() >= alarm_time:
            # playsound('alarm.mp3')  # Uncomment if you have alarm.mp3
            speak("Wake up! This is your alarm.")
            break
        time.sleep(1)

# ---------------------- UNIVERSAL APP LAUNCHER ----------------------

def get_installed_apps():
    """Get list of installed applications with display names and commands"""
    global INSTALLED_APPS_CACHE, CACHE_TIMESTAMP
    if time.time() - CACHE_TIMESTAMP < CACHE_DURATION and INSTALLED_APPS_CACHE:
        return INSTALLED_APPS_CACHE
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
                        except Exception:
                            pass
                        if not cmd:
                            try:
                                cmd = winreg.QueryValueEx(subkey, "UninstallString")[0]
                            except Exception:
                                continue
                        apps.append({
                            "name": name.lower().strip(),
                            "command": cmd,
                            "raw_name": name
                        })
                    except Exception:
                        continue
            except Exception:
                continue
    # Add common system apps not in registry
    apps.extend([
        {"name": "notepad", "command": "notepad.exe", "raw_name": "Notepad"},
        {"name": "calculator", "command": "calc.exe", "raw_name": "Calculator"},
        {"name": "paint", "command": "mspaint.exe", "raw_name": "Paint"},
        {"name": "cmd", "command": "cmd.exe", "raw_name": "Command Prompt"}
    ])
    INSTALLED_APPS_CACHE = apps
    CACHE_TIMESTAMP = time.time()
    return apps

def find_application(target):
    """Find best matching application using fuzzy search"""
    target = target.lower().strip()
    apps = get_installed_apps()
    # First pass: exact match
    for app in apps:
        if app["name"] == target:
            return app
    # Second pass: contains match
    for app in apps:
        if target in app["name"]:
            return app
    # Third pass: ratio-based fuzzy match
    from difflib import SequenceMatcher
    matches = []
    for app in apps:
        ratio = SequenceMatcher(None, target, app["name"]).ratio()
        if ratio > 0.6:
            matches.append((ratio, app))
    if matches:
        return max(matches, key=lambda x: x[0])[1]
    return None

def open_application(app_name):
    """Open any installed application by name"""
    app = find_application(app_name)
    if not app:
        speak(f"Application '{app_name}' not found")
        return
    try:
        cmd = app["command"]
        if " " in cmd and not cmd.startswith('"'):
            cmd = f'"{cmd}"'
        # Extract exe from uninstall strings
        if "uninstall" in cmd.lower():
            if "msiexec" in cmd.lower():
                import re
                match = re.search(r'\{(.*?)\}', cmd)
                if match:
                    cmd = f'msiexec /x {{{match.group(1)}}}'
            else:
                exe = cmd.split(" ")[0]
                if os.path.exists(exe):
                    cmd = exe
        subprocess.Popen(cmd, shell=True)
        speak(f"Opening {app['raw_name']}")
    except Exception as e:
        print(f"Error opening {app['raw_name']}: {str(e)}")
        speak(f"Failed to open {app['raw_name']}")

# ---------------------- END UNIVERSAL APP LAUNCHER ----------------------

def handle_command(query):
    global SILENT_MODE, WHISPER_MODE
    if "wikipedia" in query:
        try:
            search = query.replace("search wikipedia for", "").strip()
            result = wikipedia.summary(search, sentences=2, auto_suggest=False)
            speak(result)
        except wikipedia.exceptions.DisambiguationError as e:
            options = e.options[:3]
            speak(f"Multiple matches. Did you mean: {', '.join(options)}?")
        except wikipedia.exceptions.PageError:
            speak("No Wikipedia page found for that query.")
        except Exception as e:
            print(f"Wikipedia error: {e}")
            speak("Error accessing Wikipedia.")

    elif "youtube" in query:
        search = query.replace("search youtube for", "").strip()
        speak(f"Searching YouTube for {search}")
        search_url = f"https://www.youtube.com/results?search_query={search.replace(' ', '+')}"
        webbrowser.open(search_url)

    elif "calculate" in query:
        expression = query.replace("calculate", "").strip()
        try:
            result = eval(expression)
            speak(f"The result is {result}")
        except:
            speak("Invalid calculation expression.")

    elif "weather" in query:
        speak("Which city?")
        city = take_command()
        if not city:
            speak("I didn't catch the city name.")
            return
        api_key = WEATHER_API_KEY
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
            response = requests.get(url).json()
            if response["cod"] == 200:
                temp = response["main"]["temp"]
                desc = response["weather"][0]["description"]
                speak(f"The temperature in {city} is {temp}°C with {desc}")
            else:
                speak(f"Could not retrieve weather data for {city}.")
        except Exception as e:
            print(f"Weather API error: {e}")
            speak("Failed to fetch weather information.")

    elif "news" in query:
        api_key = NEWS_API_KEY
        try:
            url = f"https://newsapi.org/v2/top-headlines?country=in&apiKey={api_key}"
            data = requests.get(url).json()
            articles = data.get("articles", [])[:5]
            if articles:
                speak("Top headlines:")
                for article in articles:
                    speak(article.get("title", "Untitled article"))
            else:
                speak("No current news available.")
        except Exception as e:
            print(f"News API error: {e}")
            speak("Couldn't fetch news updates.")

    elif "open" in query:
        app = query.replace("open", "").strip()
        open_application(app)

    elif "create folder" in query:
        name = query.replace("create folder", "").strip() or "New Folder"
        create_folder(name)

    elif "delete temporary" in query:
        clear_temp()

    elif "check internet speed" in query:
        check_speed()

    elif "system information" in query:
        get_system_info()

    elif "battery status" in query:
        get_battery_status()

    elif "remind me" in query:
        task = query.replace("remind me to", "").strip()
        remind(task)

    elif "play rock paper scissors" in query:
        play_rps()

    elif "play quiz" in query:
        play_quiz()

    elif "alarm" in query:
        speak("Please say the alarm time (e.g., '7:30 PM' or '19:30').")
        alarm_time = take_command()
        set_alarm(alarm_time)

    elif "silent mode" in query:
        SILENT_MODE = True
        speak("Silent mode activated.")

    elif "whisper mode" in query:
        WHISPER_MODE = True
        speak("Whisper mode activated.")

    elif "normal mode" in query:
        SILENT_MODE = False
        WHISPER_MODE = False
        speak("Normal mode activated.")

    elif "exit" in query or "stop" in query:
        speak("Goodbye!")
        sys.exit()

    else:
        speak("Command not recognized. Please try again.")

def check_speed():
    try:
        st = speedtest.Speedtest()
        speak("Measuring internet speed...")
        download = st.download() / 1_000_000
        upload = st.upload() / 1_000_000
        speak(f"Download: {download:.2f} Mbps, Upload: {upload:.2f} Mbps")
    except Exception as e:
        print(f"Speedtest error: {e}")
        speak("Failed to check internet speed.")

def play_rps():
    choices = ["rock", "paper", "scissors"]
    speak("Choose: Rock, Paper, or Scissors?")
    user_choice = take_command().lower()
    comp_choice = random.choice(choices)
    if user_choice not in choices:
        speak("Invalid choice. Please try again.")
        return
    speak(f"I chose {comp_choice}")
    if user_choice == comp_choice:
        speak("It's a tie!")
    elif (user_choice == "rock" and comp_choice == "scissors") or \
         (user_choice == "paper" and comp_choice == "rock") or \
         (user_choice == "scissors" and comp_choice == "paper"):
        speak("You win!")
    else:
        speak("I win!")

def play_quiz():
    questions = {
        "What is 15 plus 27?": "42",
        "Square root of 144?": "12",
        "5 factorial equals?": "120",
        "2 to the power of 10?": "1024",
        "Which built-in function can get information from the user?": "input",
        "Which keyword do you use to loop over a given list of elements?": "for",
        "What's the name of Python's sorting algorithm?": "timsort",
        "What does dict.get(key) return if key isn't found in dict?": "none",
        "How do you iterate over both indices and elements in an iterable?": "enumerate(iterable)",
        "What's the official name of the := operator?": "assignment expression",
        "What's one effect of calling random.seed(42)?": "the random numbers are reproducible",
        "When does __name__ == '__main__' equal true in a Python file?": "when the file is run as a script",
        "What is the primary role of a virtual assistant?": "to assist clients remotely with tasks",
        "Which of the following tasks is commonly handled by a virtual assistant?": "social media management",
        "What is the typical employment status of a virtual assistant?": "independent contractor or self-employed",
        "How do clients usually pay virtual assistants for their services?": "through online payment platforms or bank transfers",
        "What skill set is essential for a virtual assistant?": "strong communication and organizational skills",
        "What is the primary purpose of a virtual assistant providing email management?": "to organize and prioritize incoming emails for the client",
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

def get_system_info():
    try:
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory().percent
        speak(f"CPU usage: {cpu}%, Memory usage: {mem}%")
    except Exception as e:
        print(f"System info error: {e}")
        speak("Couldn't retrieve system information.")

def get_battery_status():
    try:
        battery = psutil.sensors_battery()
        if battery:
            status = "charging" if battery.power_plugged else "not charging"
            speak(f"Battery at {battery.percent}% ({status})")
        else:
            speak("Battery information unavailable")
    except Exception as e:
        print(f"Battery error: {e}")
        speak("Failed to check battery status.")

def clear_temp():
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
        print(f"Temp clear error: {e}")
        speak("Failed to clear temporary files")

def create_folder(folder_name):
    try:
        path = os.path.join(os.path.expanduser("~"), folder_name)
        os.makedirs(path, exist_ok=True)
        speak(f"Created folder: {folder_name}")
    except Exception as e:
        print(f"Folder error: {e}")
        speak("Failed to create folder")

def remind(task):
    try:
        with open("reminders.txt", "a") as f:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            f.write(f"{timestamp} - {task}\n")
        speak("Reminder set successfully")
    except Exception as e:
        print(f"Reminder error: {e}")
        speak("Failed to set reminder")

def run_voice_assistant():
    wish_user()
    while True:
        query = take_command()
        if query:
            handle_command(query)

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
    if password == "1234":
        speak("Authentication successful")
        run_voice_assistant()
    else:
        speak("Access denied")
        sys.exit()

if __name__ == "__main__":
    create_gui()
