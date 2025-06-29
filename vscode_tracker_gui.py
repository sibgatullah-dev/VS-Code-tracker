import psutil
import time
import threading
import os
import csv
from datetime import datetime, timedelta
from collections import defaultdict
import tkinter as tk
from tkinter import messagebox, scrolledtext

LOG_FILE = "vscode_usage_log.csv"
tracking = False
tracker_thread = None

def parse_duration(s):
    try:
        h, m, s = map(int, s.split(":"))
        return timedelta(hours=h, minutes=m, seconds=s)
    except:
        return timedelta()

def load_daily_total(date_str):
    if not os.path.exists(LOG_FILE):
        return timedelta()

    with open(LOG_FILE, newline='') as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            if row[0] == date_str:
                return parse_duration(row[1])
    return timedelta()

def save_daily_total(date_str, total_duration):
    lines = []
    found = False

    if not os.path.exists(LOG_FILE):
        lines.append(["Date", "Total Time"])
    else:
        with open(LOG_FILE, newline='') as f:
            reader = csv.reader(f)
            lines = list(reader)
            if lines and lines[0][0] != "Date":
                lines.insert(0, ["Date", "Total Time"])

    for i, row in enumerate(lines):
        if row[0] == date_str:
            lines[i] = [date_str, str(total_duration).split(".")[0]]
            found = True
            break

    if not found:
        lines.append([date_str, str(total_duration).split(".")[0]])

    with open(LOG_FILE, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(lines)

def is_vscode_running():
    for proc in psutil.process_iter(['name']):
        try:
            if 'code' in proc.info['name'].lower():
                return True
        except:
            continue
    return False

def track_usage():
    global tracking
    start_time = None
    current_date = datetime.now().date().isoformat()
    accumulated_today = load_daily_total(current_date)

    while tracking:
        if is_vscode_running():
            if start_time is None:
                start_time = datetime.now()
        else:
            if start_time:
                end_time = datetime.now()
                session_time = end_time - start_time
                accumulated_today += session_time
                save_daily_total(current_date, accumulated_today)
                start_time = None
        time.sleep(5)

    if start_time:
        end_time = datetime.now()
        session_time = end_time - start_time
        accumulated_today += session_time
        save_daily_total(current_date, accumulated_today)

def start_tracking():
    global tracking, tracker_thread
    if tracking:
        messagebox.showinfo("Already Running", "Tracking is already active.")
        return
    tracking = True
    tracker_thread = threading.Thread(target=track_usage, daemon=True)
    tracker_thread.start()
    messagebox.showinfo("Started", "Tracking started!")

def stop_tracking():
    global tracking
    if tracking:
        tracking = False
        messagebox.showinfo("Stopped", "Tracking stopped.")
    else:
        messagebox.showinfo("Not Running", "Tracking was not active.")

def view_stats():
    if not os.path.exists(LOG_FILE):
        messagebox.showwarning("No Data", "No log file found yet.")
        return

    daily_totals = defaultdict(timedelta)
    try:
        with open(LOG_FILE, newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    daily_totals[row['Date']] = parse_duration(row['Total Time'])
                except:
                    continue
    except Exception as e:
        messagebox.showerror("Error Reading Log", f"Error: {e}")
        return

    today = datetime.now().date().isoformat()
    stats = f"-> Time Spent Today ({today}): {daily_totals.get(today, timedelta())}\n\n"
    stats += "<.> Time Spent in Last 7 Days:\n"

    for day in sorted(daily_totals.keys())[-7:]:
        duration = daily_totals[day]
        bar = "█" * (duration.seconds // 600)
        stats += f"{day}: {duration} {bar}\n"

    stat_box.delete("1.0", tk.END)
    stat_box.insert(tk.END, stats)

def create_gui():
    global stat_box
    root = tk.Tk()
    root.title("VS Code Time Tracker")
    root.geometry("500x400")
    root.resizable(False, False)

    tk.Label(root, text="VS Code Tracker", font=("Helvetica", 16, "bold")).pack(pady=10)

    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=10)

    tk.Button(btn_frame, text="▶ Start Tracking", width=15, command=start_tracking).pack(side=tk.LEFT, padx=5)
    tk.Button(btn_frame, text="■ Stop Tracking", width=15, command=stop_tracking).pack(side=tk.LEFT, padx=5)
    tk.Button(root, text="||| View Stats", width=48, command=view_stats).pack(pady=10)

    stat_box = scrolledtext.ScrolledText(root, height=12, width=60, font=("Courier", 10))
    stat_box.pack(padx=10, pady=5)

    root.mainloop()

if __name__ == "__main__":
    create_gui()
