import json
import threading
import time
import os

from pynput import keyboard, mouse
import tkinter as tk
from tkinter import PhotoImage

# ---------------- PATHS ----------------
CONFIG_FILE = "config.json"
ICON_PATH = "assets/cents.png"

APP_VERSION = "v1.0"

# ---------------- DEFAULT CONFIG ----------------
default_config = {
    "start_record": "f6",
    "stop_record": "f7",
    "play_loop": "f8",
    "stop_loop": "f9"
}

# ---------------- LOAD CONFIG ----------------
if os.path.exists(CONFIG_FILE):
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
    except:
        config = default_config.copy()
else:
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

waiting_for_key = None

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
            time.sleep(max(0, delay))
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
        root.after(0, lambda: status_label.config(text="Recording..."))

    elif key_str == config["stop_record"]:
        recording = False
        root.after(0, lambda: status_label.config(text=""))

    elif key_str == config["play_loop"]:
        if events:
            playing = True
            root.after(0, lambda: status_label.config(text="Playing..."))
            threading.Thread(target=play_loop, daemon=True).start()

    elif key_str == config["stop_loop"]:
        playing = False
        root.after(0, lambda: status_label.config(text=""))

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

# Icon
try:
    root.iconphoto(True, PhotoImage(file=ICON_PATH))
except:
    print("⚠️ Icon failed to load")

BG = "#0f0f14"
CARD = "#1a1a22"
ACCENT = "#6c5cff"
HOVER = "#7d6bff"
TEXT = "#e4e4e7"
SUB = "#9aa0a6"

# ---------------- KEY BIND EDIT ----------------
def set_keybind(action):
    global waiting_for_key
    waiting_for_key = action
    status_label.config(text=f"Press key for {action}...")

def gui_key_capture(event):
    global waiting_for_key

    if waiting_for_key:
        key = event.keysym.lower()
        config[waiting_for_key] = key
        save_config()
        update_labels()
        status_label.config(text="")
        waiting_for_key = None

# ---------------- UI BUTTON ----------------
class FancyButton(tk.Frame):
    def __init__(self, master, text, command):
        super().__init__(master, bg=BG)
        self.command = command

        self.container = tk.Frame(self, bg=CARD)
        self.container.pack(fill="both", expand=True, padx=20, pady=6)

        self.label = tk.Label(self.container, text=text, fg=TEXT, bg=CARD, font=("Segoe UI", 11))
        self.label.pack(pady=10)

        for w in (self.container, self.label):
            w.bind("<Enter>", self.hover)
            w.bind("<Leave>", self.leave)
            w.bind("<Button-1>", self.click)

    def hover(self, e):
        self.container.config(bg=HOVER)
        self.label.config(bg=HOVER)

    def leave(self, e):
        self.container.config(bg=CARD)
        self.label.config(bg=CARD)

    def click(self, e):
        self.container.config(bg=ACCENT)
        self.label.config(bg=ACCENT)
        self.after(120, lambda: self.container.config(bg=HOVER))
        self.after(120, lambda: self.label.config(bg=HOVER))
        self.command()

# ---------------- TOP ----------------
top = tk.Frame(root, bg=BG)
top.pack(fill="x", pady=(10, 5))

title = tk.Label(
    top,
    text="Cent's Macro",
    fg=TEXT,
    bg=BG,
    font=("Segoe UI", 14, "bold")
)
title.pack()

tk.Label(
    top,
    text=f"Version {APP_VERSION}",
    fg=SUB,
    bg=BG,
    font=("Segoe UI", 9)
).pack()

# ---------------- STATUS ----------------
status_label = tk.Label(root, text="", fg=SUB, bg=BG)
status_label.pack(pady=5)

# ---------------- LABEL UPDATE ----------------
def update_labels():
    start_btn.label.config(text=f"Start: {config['start_record']}")
    stop_btn.label.config(text=f"Stop: {config['stop_record']}")
    play_btn.label.config(text=f"Play: {config['play_loop']}")
    stop_loop_btn.label.config(text=f"Stop: {config['stop_loop']}")

# ---------------- BUTTONS ----------------
start_btn = FancyButton(root, "", lambda: set_keybind("start_record"))
stop_btn = FancyButton(root, "", lambda: set_keybind("stop_record"))
play_btn = FancyButton(root, "", lambda: set_keybind("play_loop"))
stop_loop_btn = FancyButton(root, "", lambda: set_keybind("stop_loop"))

start_btn.pack(fill="x")
stop_btn.pack(fill="x")
play_btn.pack(fill="x")
stop_loop_btn.pack(fill="x")

update_labels()
root.bind("<Key>", gui_key_capture)

# ---------------- LISTENERS ----------------
keyboard.Listener(on_press=on_press, on_release=on_release).start()
mouse.Listener(on_move=on_move, on_click=on_click).start()

# ---------------- RUN ----------------
if __name__ == "__main__":
    root.mainloop()
