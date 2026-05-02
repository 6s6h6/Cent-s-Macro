import json
import threading
import time
from pynput import keyboard, mouse
import tkinter as tk
from tkinter import PhotoImage

CONFIG_FILE = "config.json"
ICON_PATH = "/media/clunte/HDD/cents.png"

APP_VERSION = "v1.0"

# ---------------- CONFIG ----------------
default_config = {
    "start_record": "f6",
    "stop_record": "f7",
    "play_loop": "f8",
    "stop_loop": "f9"
}

try:
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)
except:
    config = default_config.copy()

def save_config():
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

# ---------------- STATE ----------------
recording = False
playing = False
events = []

kb_controller = keyboard.Controller()
mouse_controller = mouse.Controller()

# ---------------- HELPERS ----------------
def key_to_string(key):
    try:
        return key.char
    except:
        return key.name

# ---------------- PLAYBACK ----------------
def play_loop():
    global playing
    while playing:
        if not events:
            return

        start_time = events[0][-1]

        for event in events:
            if not playing:
                break

            etype = event[0]
            delay = event[-1] - start_time
            time.sleep(delay)
            start_time = event[-1]

            try:
                if etype == "key_press":
                    kb_controller.press(event[1])

                elif etype == "key_release":
                    kb_controller.release(event[1])

                elif etype == "mouse_move":
                    x, y = event[1], event[2]
                    mouse_controller.position = (x, y)

                elif etype == "mouse_click":
                    x, y, button, pressed = event[1], event[2], event[3], event[4]
                    mouse_controller.position = (x, y)
                    if pressed:
                        mouse_controller.press(button)
                    else:
                        mouse_controller.release(button)

            except Exception as e:
                print("Playback error:", e)

# ---------------- INPUT LISTENERS ----------------
def on_press(key):
    global recording, playing, events

    key_str = key_to_string(key)

    if key_str == config["start_record"]:
        recording = True
        events.clear()
        status_label.config(text="Recording...")

    elif key_str == config["stop_record"]:
        recording = False
        status_label.config(text="")

    elif key_str == config["play_loop"]:
        if events:
            playing = True
            status_label.config(text="Playing loop...")
            threading.Thread(target=play_loop, daemon=True).start()

    elif key_str == config["stop_loop"]:
        playing = False
        status_label.config(text="")

    elif recording:
        events.append(("key_press", key, time.time()))

def on_release(key):
    if recording:
        events.append(("key_release", key, time.time()))

def on_move(x, y):
    if recording:
        events.append(("mouse_move", x, y, time.time()))

def on_click(x, y, button, pressed):
    if recording:
        events.append(("mouse_click", x, y, button, pressed, time.time()))

# ---------------- GUI ----------------
root = tk.Tk()
root.title("Cent's Macro")
root.geometry("380x460")
root.configure(bg="#0f0f14")
root.resizable(False, False)

# Window icon
try:
    root.iconphoto(True, PhotoImage(file=ICON_PATH))
except:
    print("⚠️ Failed to load icon")

waiting_for_key = None

BG = "#0f0f14"
CARD = "#1a1a22"
ACCENT = "#6c5cff"
HOVER = "#7d6bff"
TEXT = "#e4e4e7"
SUB = "#9aa0a6"

def set_keybind(action):
    global waiting_for_key
    waiting_for_key = action
    status_label.config(text=f"Press key for {action.replace('_',' ')}...")

def gui_key_capture(event):
    global waiting_for_key
    if waiting_for_key:
        key = event.keysym.lower()
        config[waiting_for_key] = key
        save_config()
        update_labels()
        status_label.config(text="")
        waiting_for_key = None

def update_labels():
    start_btn.label.config(text=f"Start Rec: {config['start_record']}")
    stop_btn.label.config(text=f"Stop Rec: {config['stop_record']}")
    play_btn.label.config(text=f"Play Loop: {config['play_loop']}")
    stop_loop_btn.label.config(text=f"Stop Loop: {config['stop_loop']}")

class FancyButton(tk.Frame):
    def __init__(self, master, text, command):
        super().__init__(master, bg=BG)
        self.command = command

        self.container = tk.Frame(self, bg=CARD)
        self.container.pack(fill="both", expand=True, padx=20, pady=6)

        self.label = tk.Label(self.container, text=text, fg=TEXT, bg=CARD, font=("Segoe UI", 11))
        self.label.pack(pady=10)

        for widget in (self.container, self.label):
            widget.bind("<Enter>", self.on_hover)
            widget.bind("<Leave>", self.on_leave)
            widget.bind("<Button-1>", self.on_click)

    def on_hover(self, e):
        self.container.config(bg=HOVER)
        self.label.config(bg=HOVER)

    def on_leave(self, e):
        self.container.config(bg=CARD)
        self.label.config(bg=CARD)

    def on_click(self, e):
        self.container.config(bg=ACCENT)
        self.label.config(bg=ACCENT)
        self.after(120, lambda: self.container.config(bg=HOVER))
        self.after(120, lambda: self.label.config(bg=HOVER))
        self.command()

# ---------------- TOP BAR ----------------
top_frame = tk.Frame(root, bg=BG)
top_frame.pack(fill="x", pady=(10, 5))

# Logo
try:
    logo_img = PhotoImage(file=ICON_PATH)
    logo_img = logo_img.subsample(8, 8)

    logo_label = tk.Label(top_frame, image=logo_img, bg=BG)
    logo_label.pack(side="left", padx=(15, 10))
except:
    print("⚠️ Logo failed to load")

# Title + disclaimer
title_container = tk.Frame(top_frame, bg=BG)
title_container.pack(side="left")

tk.Label(
    title_container,
    text="TinyTask but better",
    fg=TEXT,
    bg=BG,
    font=("Segoe UI", 13, "bold")
).pack(anchor="w")

tk.Label(
    title_container,
    text="Not responsible for any bans",
    fg=SUB,
    bg=BG,
    font=("Segoe UI", 9)
).pack(anchor="w")

# Version
tk.Label(
    root,
    text=f"Version {APP_VERSION}",
    fg=SUB,
    bg=BG,
    font=("Segoe UI", 9)
).pack(pady=(0, 10))

# ---------------- BUTTONS ----------------
start_btn = FancyButton(root, "", lambda: set_keybind("start_record"))
stop_btn = FancyButton(root, "", lambda: set_keybind("stop_record"))
play_btn = FancyButton(root, "", lambda: set_keybind("play_loop"))
stop_loop_btn = FancyButton(root, "", lambda: set_keybind("stop_loop"))

start_btn.pack(fill="x")
stop_btn.pack(fill="x")
play_btn.pack(fill="x")
stop_loop_btn.pack(fill="x")

# Hidden status label (no default text)
status_label = tk.Label(root, text="", fg=SUB, bg=BG)

update_labels()
root.bind("<Key>", gui_key_capture)

# ---------------- LISTENERS ----------------
keyboard.Listener(on_press=on_press, on_release=on_release).start()
mouse.Listener(on_move=on_move, on_click=on_click).start()

root.mainloop()
