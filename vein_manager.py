import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import configparser
import os
import subprocess
import threading
import time
import psutil
import json
import urllib.request
import shutil
import sys
import tempfile
import traceback
import ctypes
import re
import random
import glob
import zipfile
import webbrowser
from datetime import datetime, timedelta

# --- High DPI Fix ---
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    pass

if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

# --- CONSTANTS ---
MANAGER_VERSION = "v3.7.0 (The Social Update)"
AUTHOR_NAME = "Wolverinex77"
SERVER_EXECUTABLE = 'VeinServer-Win64-Test.exe'
MANAGER_CONFIG_FILE = os.path.join(application_path, 'manager_config.ini')
HISTORY_FILE = os.path.join(application_path, 'player_history.json')
LOGS_DIR = os.path.join(application_path, 'Manager_Logs')
EVENTS_LOG_FILE = os.path.join(LOGS_DIR, 'Manager_Events.log')
WIZARD_DEBUG_LOG = os.path.join(application_path, 'Wizard_Debug.log')
ICON_FILE = os.path.join(application_path, 'favicon.ico')
VEIN_APP_ID = '2131400'
STEAMCMD_URL = "https://steamcdn-a.akamaihd.net/client/installer/steamcmd.zip"

# --- THE DICTIONARY (Updated Defaults) ---
GAMEPLAY_DEFINITIONS = {
    "General & Limits": [
        ("Max Utility Cabinets", "vein.Placement.MaxUtilityCabinets", "Limit per area to prevent lag (0=Unl).", "str", "Engine", "ConsoleVariables", "0"),
        ("Wire Max Radius", "vein.Wire.MaxRadius", "Electrical wire range.", "str", "Engine", "ConsoleVariables", "2000"),
        ("Scarcity Difficulty", "vein.Scarcity.Difficulty", "Higher Value = Less Loot.", "str", "Engine", "ConsoleVariables", "1.0"),
    ],
    "Survival & Game": [
        ("Hunger Multiplier", "GS_HungerMultiplier", "Higher = Starve Faster.", "str", "Game", "/Script/Vein.ServerSettings", "1.0"),
        ("Thirst Multiplier", "GS_ThirstMultiplier", "Higher = Dehydrate Faster.", "str", "Game", "/Script/Vein.ServerSettings", "1.0"),
        ("3rd Person Dist", "GS_MaxThirdPersonDistance", "Camera max distance.", "str", "Game", "/Script/Vein.ServerSettings", "300"),
        ("Show Badges", "GS_ShowScoreboardBadges", "Show Admin badges.", "bool", "Game", "/Script/Vein.ServerSettings", True),
    ],
    "PvP & Raiding": [
        ("Enable PvP", "vein.PvP", "Player vs Player combat.", "bool", "Engine", "ConsoleVariables", True),
        ("Base Damage", "vein.BaseDamage", "Can bases be damaged?", "bool", "Engine", "ConsoleVariables", True),
        ("Structure Decay", "vein.BuildObjectDecay", "Abandoned structures decay?", "bool", "Engine", "ConsoleVariables", True),
        ("Build Object PvP", "vein.BuildObjectPvP", "Damage objects?", "bool", "Engine", "ConsoleVariables", True),
        ("Allow Raiding", "vein.UtilityCabinet.AllowRaiding", "Cabinet raiding?", "bool", "Engine", "ConsoleVariables", True),
        ("Offline Protection", "vein.OfflineRaidProtection", "Reduce offline dmg.", "bool", "Engine", "ConsoleVariables", True),
        ("Allow Pickpocketing", "vein.AllowPickpocketing", "Steal inventory?", "bool", "Engine", "ConsoleVariables", True),
        ("Headshot Mult", "vein.HeadshotDamageMultiplier", "Dmg Multiplier.", "str", "Engine", "ConsoleVariables", "2.0"),
        ("Vehicle Player Dmg", "vein.Vehicles.Damage.OutgoingPlayerDamage", "Cars hurt players?", "bool", "Engine", "ConsoleVariables", True),
    ],
    "Time & World": [
        ("Time Multiplier", "vein.Time.TimeMultiplier", "Day Speed (16.0 = 90min Day).", "str", "Engine", "ConsoleVariables", "16.0"),
        ("Night Multiplier", "vein.Time.NightTimeMultiplier", "Night Speed (3.0 = Fast Night).", "str", "Engine", "ConsoleVariables", "3.0"),
        ("Start Offset Days", "vein.Time.StartOffsetDays", "Days passed at start.", "str", "Engine", "ConsoleVariables", "0"),
        ("Elec Shutoff Day", "vein.Calendar.ElectricalShutoffTimeDays", "Day grid fails.", "str", "Engine", "ConsoleVariables", "14"),
        ("Water Shutoff Day", "vein.Calendar.WaterShutoffTimeDays", "Day water fails.", "str", "Engine", "ConsoleVariables", "30"),
        ("Allow Remote TV", "vein.TV.Server.AllowRemoteContent", "Stream URLs on TVs.", "bool", "Engine", "ConsoleVariables", True),
    ],
    "Zombies (The Horde)": [
        ("Zombie Health", "vein.Zombies.Health", "Base HP.", "str", "Engine", "ConsoleVariables", "100"),
        ("Can Climb", "vein.Zombies.CanClimb", "Zombies climb walls.", "bool", "Engine", "ConsoleVariables", True),
        ("Always Turn", "vein.AlwaysBecomeZombie", "Players turn on death.", "bool", "Engine", "ConsoleVariables", False),
        ("Infection Chance", "vein.ZombieInfectionChance", "Prob on Hit (0.0-1.0).", "str", "Engine", "ConsoleVariables", "0.05"),
        ("Spawn Cap Mult", "vein.AISpawner.SpawnCapMultiplierZombie", "Density (2.0=Double).", "str", "Engine", "ConsoleVariables", "1.0"),
        ("Walker %", "vein.AISpawner.ZombieWalkerPercentage", "% that walk (0.0-1.0).", "str", "Engine", "ConsoleVariables", "0.85"),
        ("Dmg Multiplier", "vein.Zombies.DamageMultiplier", "Damage Output.", "str", "Engine", "ConsoleVariables", "1.0"),
        ("Hearing Mult", "vein.Zombies.HearingMultiplier", "Detection Range.", "str", "Engine", "ConsoleVariables", "1.0"),
        ("Sight Mult", "vein.Zombies.SightMultiplier", "Vision Range.", "str", "Engine", "ConsoleVariables", "1.0"),
        ("Speed Mult", "vein.Zombies.SpeedMultiplier", "Run Speed.", "str", "Engine", "ConsoleVariables", "1.0"),
        ("Crawl Speed", "vein.Zombies.CrawlSpeedMultiplier", "Crawler Speed.", "str", "Engine", "ConsoleVariables", "1.25"),
        ("Run Speed", "vein.Zombies.RunSpeedMultiplier", "Runner Speed.", "str", "Engine", "ConsoleVariables", "1.1"),
        ("Walk Speed", "vein.Zombies.WalkSpeedMultiplier", "Walker Speed.", "str", "Engine", "ConsoleVariables", "1.1"),
        ("Stagger Chance", "vein.StaggerChance", "Stagger on hit (0.0-1.0).", "str", "Engine", "ConsoleVariables", "0.5"),
        ("Stun Chance", "vein.StunLockChance", "Stun on hit (0.0-1.0).", "str", "Engine", "ConsoleVariables", "0.1"),
        ("Stun Duration", "vein.StunLockDuration", "Seconds stunned.", "str", "Engine", "ConsoleVariables", "1.5"),
    ]
}

class ServerManager:
    def __init__(self, root):
        self.root = root
        self.ensure_logs_directory()
        
        # --- LOCATION GUARD ---
        self.check_unsafe_location()
        # ----------------------
        
        self.log_manager_event("SYSTEM", f"Manager Initializing ({MANAGER_VERSION})...")
        
        self.vcmd = (self.root.register(self.validate_number_input), '%P')
        
        current_folder = os.path.basename(os.path.normpath(application_path))
        if "TEST" in current_folder.upper():
            self.env_type = "TEST"
            self.text_color = "#3498db" 
            self.header_text = f"TEST ENVIRONMENT ({current_folder})"
        else:
            self.env_type = "LIVE"
            self.text_color = "#e74c3c"
            self.header_text = f"LIVE ENVIRONMENT ({current_folder})"
            
        self.root.title(f"Vein Manager {MANAGER_VERSION} [{self.env_type}]")
        if os.path.exists(ICON_FILE):
            try: self.root.iconbitmap(ICON_FILE)
            except: pass
        
        # State & Vars
        self.server_pid = None
        self.is_checking_status = True
        self.manual_shutdown_requested = False
        self.restart_requested = False
        self.server_was_running = False
        self.is_backing_up = False 
        self.processing_scheduled_restart = False 
        self.is_updating = False
        self.crash_count = 0
        self.current_build_id = "Unknown"
        self.update_loop_prevention = False

        self.keep_alive_var = tk.BooleanVar(value=False)
        self.rcon_enabled_var = tk.BooleanVar(value=False)
        self.http_api_enabled_var = tk.BooleanVar(value=False)
        self.sched_daily_enabled = tk.BooleanVar(value=False)
        self.sched_days_vars = [tk.BooleanVar(value=True) for _ in range(7)] 
        self.sched_interval_enabled = tk.BooleanVar(value=False)
        self.reactive_backup_enabled = tk.BooleanVar(value=True)
        self.backup_on_stop = tk.BooleanVar(value=False)
        
        self.auto_update_enabled = tk.BooleanVar(value=False)
        self.auto_update_passive = tk.BooleanVar(value=True)
        self.steam_branch_var = tk.StringVar(value="public")
        
        # Discord & Social Vars
        self.discord_enabled = tk.BooleanVar(value=False)
        self.discord_webhook_url = tk.StringVar()
        self.community_url = tk.StringVar(value="https://discord.gg/")

        self.player_history = self.load_player_history()
        self.player_filter_var = tk.StringVar(value="Online Now")
        self.last_daily_trigger_time = None
        self.gameplay_vars = {}
        self.gameplay_frames = {} 
        self.menu_buttons = {} 
        
        # Wizard Vars
        self.wizard_install_path = tk.StringVar()
        self.wizard_steamcmd_path = tk.StringVar()
        self.wizard_is_import = False

        # --- THE TRAFFIC COP ---
        config = configparser.ConfigParser()
        config.read(MANAGER_CONFIG_FILE)
        existing_path = config.get('Manager', 'ServerPath', fallback='')
        
        if not existing_path or not os.path.exists(existing_path):
            self.setup_wizard_ui()
        else:
            self.create_menu()
            self.setup_dashboard_ui()
            self.setup_scrollable_area()
            self.start_background_threads()
            self.update_gui_for_state("OFFLINE")
            self.load_manager_config() 
            self.refresh_build_id_display()
            self.scan_for_existing_server()
            self.update_header_title()
            self.append_to_log_viewer(f"--- Manager Started [{self.env_type}] ---\n")

    def check_unsafe_location(self):
        path_str = application_path.lower()
        unsafe = ["downloads", "temp", "appdata"]
        hit = False
        for u in unsafe:
            if u in path_str:
                hit = True
                break
        if hit:
            messagebox.showwarning(
                "Unsafe Run Location Detected",
                f"You are running the Manager from a temporary folder:\n{application_path}\n\n"
                "If you continue, your Manager Logs and Configuration will be saved here.\n"
                "These files might be deleted if you clean your Downloads folder.\n\n"
                "Recommendation: Move this executable to a permanent folder (e.g. C:\\VeinServer) before continuing."
            )

    def start_background_threads(self):
        self.status_thread = threading.Thread(target=self.status_checker_loop, daemon=True)
        self.status_thread.start()
        self.api_thread = threading.Thread(target=self.api_poller_loop, daemon=True)
        self.api_thread.start()
        self.scheduler_thread = threading.Thread(target=self.scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        self.updater_thread = threading.Thread(target=self.auto_updater_loop, daemon=True)
        self.updater_thread.start()

    # ==========================
    # === DISCORD WEBHOOKS ===
    # ==========================
    def send_discord_webhook(self, msg_type, description):
        if not self.discord_enabled.get() or not self.discord_webhook_url.get():
            return
        
        # Prefix for Test Env
        if self.env_type == "TEST":
            description = f"**[TEST ENV]** {description}"

        # Color Codes
        colors = {
            "START": 5763719,  # Green
            "STOP": 15548997,  # Red
            "CRASH": 15158332, # Orange/Red
            "UPDATE": 3447003  # Blue
        }
        color = colors.get(msg_type, 0)
        
        payload = {
            "embeds": [
                {
                    "title": f"Vein Server Manager - {msg_type}",
                    "description": description,
                    "color": color,
                    "footer": {"text": f"v{MANAGER_VERSION}"},
                    "timestamp": datetime.now().isoformat()
                }
            ]
        }
        
        def _send():
            try:
                req = urllib.request.Request(
                    self.discord_webhook_url.get(),
                    data=json.dumps(payload).encode('utf-8'),
                    headers={'Content-Type': 'application/json', 'User-Agent': 'VeinManager/3.7'}
                )
                urllib.request.urlopen(req)
            except Exception as e:
                self.log_manager_event("DISCORD", f"Failed to send webhook: {e}")

        threading.Thread(target=_send, daemon=True).start()

    # ==========================
    # === INSTALL WIZARD UI ===
    # ==========================
    # (Wizard Code Omitted for brevity - same as previous version but uses defaults from GAMEPLAY_DEFINITIONS)
    # Re-pasting critical sections for context
    def log_wizard_debug(self, msg):
        try:
            with open(WIZARD_DEBUG_LOG, 'a') as f:
                f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
        except: pass

    def setup_wizard_ui(self):
        self.wizard_frame = tk.Frame(self.root, padx=20, pady=20)
        self.wizard_frame.pack(fill='both', expand=True)
        
        self.wiz_step_frames = {}
        for i in range(1, 5):
            f = tk.Frame(self.wizard_frame)
            self.wiz_step_frames[i] = f
        
        self.show_wizard_step(1)

    def show_wizard_step(self, step_num):
        for f in self.wiz_step_frames.values(): f.pack_forget()
        frame = self.wiz_step_frames[step_num]
        frame.pack(fill='both', expand=True)
        for widget in frame.winfo_children(): widget.destroy()
        
        tk.Label(frame, text=f"Setup Wizard - Step {step_num}/4", font=("Segoe UI", 10), fg="grey").pack(anchor='w')
        if step_num == 1: self.build_wiz_step_1(frame)
        elif step_num == 2: self.build_wiz_step_2(frame)
        elif step_num == 3: self.build_wiz_step_3(frame)
        elif step_num == 4: self.build_wiz_step_4(frame)

    def build_wiz_step_1(self, parent):
        tk.Label(parent, text="Welcome to Vein Manager", font=("Segoe UI", 16, "bold"), fg="#e67e22").pack(pady=10)
        tk.Label(parent, text="Let's choose where your server files will live.\nIf you have an existing server, select its folder.", justify='center').pack(pady=5)
        tk.Label(parent, text="Install Location:", font=("bold")).pack(anchor='w', pady=(20, 5))
        e = tk.Entry(parent, textvariable=self.wizard_install_path, width=50)
        e.pack(fill='x', pady=5)
        if not self.wizard_install_path.get(): self.wizard_install_path.set("C:\\VeinServer")
        btn_frame = tk.Frame(parent)
        btn_frame.pack(fill='x', pady=5)
        tk.Button(btn_frame, text="Browse...", command=self.wiz_browse_install).pack(side='right')
        self.wiz_status_lbl = tk.Label(parent, text="", fg="blue")
        self.wiz_status_lbl.pack(pady=10)
        nav = tk.Frame(parent)
        nav.pack(side='bottom', fill='x', pady=10)
        tk.Button(nav, text="Next >", bg="#ddffdd", command=self.wiz_validate_step_1).pack(side='right')

    def wiz_browse_install(self):
        d = filedialog.askdirectory()
        if d: 
            self.wizard_install_path.set(d)
            self.wiz_check_import_status()

    def wiz_check_import_status(self):
        path = self.wizard_install_path.get()
        exe = os.path.join(path, 'Vein', 'Binaries', 'Win64', SERVER_EXECUTABLE)
        if os.path.exists(exe):
            self.wizard_is_import = True
            self.wiz_status_lbl.config(text="✅ Existing Installation Detected! (Import Mode)", fg="green")
        else:
            self.wizard_is_import = False
            self.wiz_status_lbl.config(text="New Installation will be created.", fg="black")

    def wiz_validate_step_1(self):
        if not self.wizard_install_path.get():
            messagebox.showerror("Error", "Please select a folder.")
            return
        self.wiz_check_import_status() 
        self.show_wizard_step(2)

    def build_wiz_step_2(self, parent):
        tk.Label(parent, text="Steam Console Client (Required)", font=("Segoe UI", 14, "bold")).pack(pady=10)
        tk.Label(parent, text="We need SteamCMD to download/update the server.", justify='center').pack(pady=5)
        self.wiz_steam_choice = tk.StringVar(value="auto")
        pot_steam_local = os.path.join(self.wizard_install_path.get(), "SteamCMD", "steamcmd.exe")
        pot_steam_c = "C:\\steamCMD\\steamcmd.exe"
        if os.path.exists(pot_steam_local):
            self.wizard_steamcmd_path.set(pot_steam_local)
            self.wiz_steam_choice.set("manual")
        elif os.path.exists(pot_steam_c):
            self.wizard_steamcmd_path.set(pot_steam_c)
            self.wiz_steam_choice.set("manual")
        elif not self.wizard_steamcmd_path.get():
            self.wizard_steamcmd_path.set(pot_steam_c)
        tk.Radiobutton(parent, text="Download & Install SteamCMD automatically", variable=self.wiz_steam_choice, value="auto", command=self.wiz_toggle_steam_ui).pack(anchor='w', pady=5)
        tk.Radiobutton(parent, text="I already have SteamCMD", variable=self.wiz_steam_choice, value="manual", command=self.wiz_toggle_steam_ui).pack(anchor='w', pady=5)
        self.wiz_steam_manual_frame = tk.Frame(parent)
        self.wiz_steam_manual_frame.pack(fill='x', padx=20)
        tk.Entry(self.wiz_steam_manual_frame, textvariable=self.wizard_steamcmd_path).pack(side='left', fill='x', expand=True)
        tk.Button(self.wiz_steam_manual_frame, text="Browse...", command=self.wiz_browse_steam).pack(side='left', padx=5)
        nav = tk.Frame(parent)
        nav.pack(side='bottom', fill='x', pady=10)
        tk.Button(nav, text="< Back", command=lambda: self.show_wizard_step(1)).pack(side='left')
        self.wiz_step2_next_btn = tk.Button(nav, text="Next >", bg="#ddffdd", command=self.wiz_process_step_2)
        self.wiz_step2_next_btn.pack(side='right')
        self.wiz_toggle_steam_ui()

    def wiz_toggle_steam_ui(self):
        if self.wiz_steam_choice.get() == "manual":
            self.wiz_step2_next_btn.config(text="Next >")
            for child in self.wiz_steam_manual_frame.winfo_children(): child.configure(state='normal')
        else:
            self.wiz_step2_next_btn.config(text="Download & Install >")
            for child in self.wiz_steam_manual_frame.winfo_children(): child.configure(state='normal')

    def wiz_browse_steam(self):
        f = filedialog.askopenfilename(filetypes=[("Executable", "steamcmd.exe")])
        if f: self.wizard_steamcmd_path.set(f)

    def wiz_process_step_2(self):
        if self.wiz_steam_choice.get() == "manual":
            if not os.path.exists(self.wizard_steamcmd_path.get()):
                messagebox.showerror("Error", "SteamCMD executable not found at specified path.")
                return
            self.show_wizard_step(3)
        else:
            threading.Thread(target=self.wiz_download_steamcmd, daemon=True).start()

    def wiz_download_steamcmd(self):
        self.wiz_step2_next_btn.config(state='disabled', text="Downloading...")
        try:
            target_exe = self.wizard_steamcmd_path.get()
            target_dir = os.path.dirname(target_exe)
            os.makedirs(target_dir, exist_ok=True)
            zip_path = os.path.join(target_dir, "steamcmd.zip")
            urllib.request.urlretrieve(STEAMCMD_URL, zip_path)
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(target_dir)
            os.remove(zip_path)
            if os.path.exists(target_exe):
                self.root.after(0, lambda: self.wiz_step2_next_btn.config(text="Initializing SteamCMD..."))
                subprocess.run([target_exe, "+quit"], creationflags=subprocess.CREATE_NO_WINDOW)
                self.root.after(0, lambda: self.show_wizard_step(3))
            else:
                messagebox.showerror("Error", "SteamCMD extraction failed (Exe not found).")
                self.root.after(0, lambda: self.wiz_step2_next_btn.config(state='normal', text="Try Again"))
        except Exception as e:
            messagebox.showerror("Error", f"Download failed: {e}")
            self.root.after(0, lambda: self.wiz_step2_next_btn.config(state='normal', text="Try Again"))

    def build_wiz_step_3(self, parent):
        tk.Label(parent, text="Server Files", font=("Segoe UI", 14, "bold")).pack(pady=10)
        tk.Label(parent, text="⚠ Note: The server is approximately 12GB. Please be patient.", fg="#e67e22", font=("Segoe UI", 9, "bold")).pack(pady=5)
        self.wiz_console = tk.Text(parent, height=15, bg="black", fg="#00ff00", font=("Courier New", 9))
        self.wiz_console.pack(fill='both', expand=True, padx=10)
        nav = tk.Frame(parent)
        nav.pack(side='bottom', fill='x', pady=10)
        if self.wizard_is_import:
            self.wiz_console.insert(tk.END, ">>> Import Mode Detected.\n>>> Existing files found.\n>>> Skipping Download.\n")
            tk.Button(nav, text="Next >", bg="#ddffdd", command=lambda: self.show_wizard_step(4)).pack(side='right')
        else:
            self.wiz_console.insert(tk.END, ">>> Ready to download Vein Server (AppID 2131400).\n>>> Click 'Start Download' to begin.\n")
            self.wiz_dl_btn = tk.Button(nav, text="Start Download", bg="#3498db", fg="white", command=self.wiz_start_download)
            self.wiz_dl_btn.pack(side='right')

    def wiz_start_download(self):
        self.wiz_dl_btn.config(state='disabled')
        self.wiz_console.insert(tk.END, ">>> Initializing SteamCMD... Please Wait...\n")
        self.wiz_console.insert(tk.END, ">>> Connecting to Valve Servers...\n")
        try: os.makedirs(self.wizard_install_path.get(), exist_ok=True)
        except: pass
        threading.Thread(target=self.wiz_run_download, daemon=True).start()

    def wiz_run_download(self):
        steam_exe = self.wizard_steamcmd_path.get()
        install_dir = self.wizard_install_path.get()
        args = [steam_exe, '+force_install_dir', install_dir, '+login', 'anonymous', '+app_update', VEIN_APP_ID, '+quit']
        try:
            process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, creationflags=subprocess.CREATE_NO_WINDOW, encoding='utf-8', errors='ignore')
            for line in iter(process.stdout.readline, ''):
                self.root.after(0, self.wiz_append_console, line)
            process.wait()
            if process.returncode == 0: self.root.after(0, self.wiz_download_complete)
            else:
                self.root.after(0, self.wiz_append_console, "\nERROR: Download Failed.\n")
                self.root.after(0, lambda: self.wiz_dl_btn.config(state='normal'))
        except Exception as e:
            self.root.after(0, self.wiz_append_console, f"\nCRITICAL: {e}\n")

    def wiz_append_console(self, text):
        self.wiz_console.insert(tk.END, text)
        self.wiz_console.see(tk.END)

    def wiz_download_complete(self):
        self.wiz_append_console("\n>>> SUCCESS! Download Complete.\n")
        self.wiz_dl_btn.config(text="Next >", bg="#ddffdd", fg="black", command=lambda: self.show_wizard_step(4), state='normal')

    def build_wiz_step_4(self, parent):
        tk.Label(parent, text="Server Identity", font=("Segoe UI", 14, "bold")).pack(pady=10)
        tk.Label(parent, text="Configure the basics. You can change these later.", justify='center').pack(pady=5)
        form = tk.Frame(parent)
        form.pack(pady=10)
        tk.Label(form, text="Server Name:").grid(row=0, column=0, sticky='w', pady=5)
        self.wiz_name = tk.Entry(form, width=40)
        self.wiz_name.grid(row=0, column=1, pady=5)
        tk.Label(form, text="Session Name (Save File):").grid(row=1, column=0, sticky='w', pady=5)
        self.wiz_session = tk.Entry(form, width=40)
        self.wiz_session.insert(0, "Server")
        self.wiz_session.grid(row=1, column=1, pady=5)
        tk.Label(form, text="(Keep as 'Server' to prevent wipes)", font=("Arial", 8), fg="red").grid(row=2, column=1, sticky='w')
        tk.Label(form, text="Max Players:").grid(row=3, column=0, sticky='w', pady=5)
        self.wiz_players = tk.Entry(form, width=10)
        self.wiz_players.insert(0, "16")
        self.wiz_players.grid(row=3, column=1, sticky='w', pady=5)
        tk.Label(form, text="Password (Optional):").grid(row=4, column=0, sticky='w', pady=5)
        self.wiz_pass = tk.Entry(form, width=30)
        self.wiz_pass.grid(row=4, column=1, sticky='w', pady=5)
        
        if self.wizard_is_import: self.wiz_try_prefill()
        else: self.wiz_name.insert(0, "Vein Server")

        nav = tk.Frame(parent)
        nav.pack(side='bottom', fill='x', pady=10)
        self.wiz_finish_btn = tk.Button(nav, text="Finish & Launch >", bg="#ddffdd", font=("bold"), command=self.wiz_finish)
        self.wiz_finish_btn.pack(side='right')

    def wiz_try_prefill(self):
        try:
            ini_path = os.path.join(self.wizard_install_path.get(), 'Vein', 'Saved', 'Config', 'WindowsServer', 'Game.ini')
            if os.path.exists(ini_path):
                config = configparser.ConfigParser(strict=False)
                config.read(ini_path)
                found_name = None
                for sec in config.sections():
                    if 'VeinGameSession' in sec or 'ServerSettings' in sec:
                        if config.has_option(sec, 'ServerName'): found_name = config.get(sec, 'ServerName')
                        if config.has_option(sec, 'MaxPlayers'): 
                            self.wiz_players.delete(0, tk.END)
                            self.wiz_players.insert(0, config.get(sec, 'MaxPlayers'))
                        if config.has_option(sec, 'Password'): 
                            self.wiz_pass.delete(0, tk.END)
                            self.wiz_pass.insert(0, config.get(sec, 'Password'))
                if found_name: 
                    self.wiz_name.delete(0, tk.END)
                    self.wiz_name.insert(0, found_name)
        except: pass

    def wiz_finish(self):
        self.wiz_finish_btn.config(state='disabled', text="Setting up...")
        self.log_wizard_debug("Wizard Finish Triggered.")
        
        try:
            # Save Manager Config
            config = configparser.ConfigParser(interpolation=None)
            config['Manager'] = {'ServerPath': self.wizard_install_path.get(), 'SteamCMDPath': self.wizard_steamcmd_path.get(), 'KeepAlive': 'False'}
            config['Startup'] = {'Map': '/Game/Vein/Maps/ChamplainValley?listen', 'SessionName': self.wiz_session.get(), 'Port': '7779', 'QueryPort': '27015', 'MaxPlayers': self.wiz_players.get(), 'EnableHTTPAPI': 'False'}
            config['RCON'] = {'Enabled': 'False', 'Port': '27020', 'Password': ''}
            config['Backups'] = {'Format': 'Server_Backup_%Y-%m-%d_%H-%M-%S', 'Retention': '50', 'ReactiveBackupEnabled': 'True', 'BackupOnStop': 'False'}
            config['AutoUpdater'] = {'Enabled': 'False', 'PassiveMode': 'True', 'SteamBranch': 'public'}
            config['Scheduler'] = {'DailyEnabled': 'False', 'DailyDays': '0,1,2,3,4,5,6', 'DailyTime': '00:00, 04:00, 08:00, 12:00, 16:00, 20:00', 'IntervalEnabled': 'False', 'IntervalHours': '4'}
            config['Discord'] = {'Enabled': 'False', 'WebhookURL': '', 'CommunityURL': 'https://discord.gg/'}
            
            with open(MANAGER_CONFIG_FILE, 'w') as f: config.write(f)
            
            # Identity Write
            game_ini = os.path.join(self.wizard_install_path.get(), 'Vein', 'Saved', 'Config', 'WindowsServer', 'Game.ini')
            os.makedirs(os.path.dirname(game_ini), exist_ok=True)
            g_conf = configparser.ConfigParser(strict=False); g_conf.optionxform = str
            try: g_conf.read(game_ini)
            except: pass
            
            if not g_conf.has_section('/Script/Vein.VeinGameSession'): g_conf.add_section('/Script/Vein.VeinGameSession')
            if not g_conf.has_section('/Script/Vein.ServerSettings'): g_conf.add_section('/Script/Vein.ServerSettings')
            if not g_conf.has_section('/Script/Engine.GameSession'): g_conf.add_section('/Script/Engine.GameSession')
            
            g_conf.set('/Script/Vein.VeinGameSession', 'ServerName', self.wiz_name.get())
            g_conf.set('/Script/Vein.ServerSettings', 'ServerName', self.wiz_name.get())
            mp = self.wiz_players.get()
            g_conf.set('/Script/Vein.VeinGameSession', 'MaxPlayers', mp)
            g_conf.set('/Script/Engine.GameSession', 'MaxPlayers', mp)
            pw = self.wiz_pass.get()
            if pw: g_conf.set('/Script/Vein.VeinGameSession', 'Password', pw)
            
            with open(game_ini, 'w', encoding='utf-8') as f: g_conf.write(f, space_around_delimiters=False)
            
            # Engine.ini (Time Defaults)
            eng_ini = os.path.join(self.wizard_install_path.get(), 'Vein', 'Saved', 'Config', 'WindowsServer', 'Engine.ini')
            with open(eng_ini, 'a+') as f:
                f.seek(0); content = f.read()
                if '[ConsoleVariables]' not in content: f.write("\n[ConsoleVariables]\n")
                f.write(f"vein.Characters.Max={mp}\n")
                # Write Defaults from Dictionary
                f.write(f"vein.Time.TimeMultiplier=16.0\n")
                f.write(f"vein.Time.NightTimeMultiplier=3.0\n")
            
            self.wizard_frame.destroy()
            self.create_menu()
            self.setup_dashboard_ui()
            self.setup_scrollable_area()
            self.start_background_threads()
            self.update_gui_for_state("OFFLINE")
            self.load_manager_config() 
            self.refresh_build_id_display()
            self.scan_for_existing_server()
            self.update_header_title()
            self.append_to_log_viewer(f"--- Wizard Complete. Manager Started [{self.env_type}] ---\n")
                
        except Exception as e:
            err = str(e)
            self.log_wizard_debug(f"CRITICAL ERROR: {err}")
            messagebox.showerror("Wizard Error", f"Setup Failed:\n{err}\n\nSee Wizard_Debug.log")
            self.wiz_finish_btn.config(state='normal', text="Finish & Launch >")

    # ==========================
    # === MAIN MANAGER UI ===
    # ==========================
    def purge_manager_logs(self):
        if messagebox.askyesno("Confirm", "Clear the internal Manager Events log?\nThis will not delete game logs."):
            try:
                with open(EVENTS_LOG_FILE, 'w') as f:
                    f.write(f"[{datetime.now()}] [SYSTEM] Log Purged by User.\n")
                self.log_manager_event("SYSTEM", "Logs purged.")
                messagebox.showinfo("Success", "Manager logs cleared.")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def _apply_config_value(self, widget, config, section, key, default_val):
        val = config.get(section, key, fallback=default_val)
        if not val: val = default_val 
        try:
            widget.delete(0, tk.END)
            widget.insert(0, val)
        except: pass

    def validate_number_input(self, P):
        if P == "": return True
        return P.isdigit()

    def scan_for_existing_server(self):
        server_path = self.path_entry.get()
        if not server_path: return
        expected_exe = os.path.join(server_path, 'Vein', 'Binaries', 'Win64', SERVER_EXECUTABLE)
        found_pid = None
        try:
            for proc in psutil.process_iter(['pid', 'name', 'exe']):
                try:
                    if proc.info['name'] == SERVER_EXECUTABLE:
                        if proc.info['exe'] and os.path.normpath(proc.info['exe']).lower() == os.path.normpath(expected_exe).lower():
                            found_pid = proc.info['pid']
                            break
                except: pass
        except: pass
        if found_pid:
            self.server_pid = found_pid
            self.server_was_running = True
            self.update_gui_for_state("ONLINE")
            self.log_manager_event("GUARD", f"Auto-Attached to existing process: {found_pid}")
            self.append_to_log_viewer(f">>> SINGLETON GUARD: Attached to PID {found_pid}\n")
            self.pid_label.config(text=f"PID: {self.server_pid}")

    def ensure_logs_directory(self):
        if not os.path.exists(LOGS_DIR):
            try: os.makedirs(LOGS_DIR)
            except: pass
            
    def log_manager_event(self, category, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(EVENTS_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] [{category}] {message}\n")
        except: pass

    def create_menu(self):
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Save Settings", command=self.save_all_settings)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)
        menubar.add_cascade(label="File", menu=file_menu)
        self.root.config(menu=menubar)

    def setup_dashboard_ui(self):
        top_bar = tk.Frame(self.root, padx=10, pady=5)
        top_bar.pack(fill="x", side="top")
        tk.Label(top_bar, text="Server Path:", font=("Segoe UI", 9)).pack(side="left")
        self.path_entry = tk.Entry(top_bar)
        self.path_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.browse_button = tk.Button(top_bar, text="Browse...", command=self.browse_path)
        self.browse_button.pack(side="left")

        id_frame = tk.Frame(self.root, padx=15, pady=5)
        id_frame.pack(fill="x", side="top")
        self.status_canvas = tk.Canvas(id_frame, width=20, height=20, highlightthickness=0)
        self.status_dot = self.status_canvas.create_oval(2, 2, 18, 18, fill="red", outline="")
        self.status_canvas.pack(side="left", pady=5)
        
        self.header_title_label = tk.Label(id_frame, text="Vein Server", font=("Segoe UI", 14, "bold"), fg="#333")
        self.header_title_label.pack(side="left", padx=10)
        
        self.start_button = tk.Button(id_frame, text="Start", width=10, bg="#ddffdd", command=lambda: self.start_server("USER"))
        self.start_button.pack(side="left", padx=5)
        self.stop_button = tk.Button(id_frame, text="Stop", width=10, bg="#ffdddd", command=self.stop_server)
        self.stop_button.pack(side="left", padx=5)
        self.restart_button = tk.Button(id_frame, text="Restart", width=10, command=self.restart_server)
        self.restart_button.pack(side="left", padx=5)
        self.keep_alive_checkbox = tk.Checkbutton(id_frame, text="Keep Alive", variable=self.keep_alive_var)
        self.keep_alive_checkbox.pack(side="left", padx=10)
        self.save_button = tk.Button(id_frame, text="💾 SAVE", bg="#e1f5fe", command=self.save_all_settings)
        self.save_button.pack(side="right", padx=5)

        info_bar = tk.Frame(self.root, padx=10, pady=2, bg="#e0e0e0", relief="sunken", bd=1)
        info_bar.pack(fill="x", side="top")
        def add_info_label(parent, text, fg="black"):
            lbl = tk.Label(parent, text=text, bg="#e0e0e0", fg=fg, font=("Segoe UI", 9))
            lbl.pack(side="left", padx=10)
            return lbl
        self.status_text_label = add_info_label(info_bar, "Status: OFFLINE", fg="red")
        tk.Label(info_bar, text="|", bg="#e0e0e0", fg="#888").pack(side="left")
        self.pid_label = add_info_label(info_bar, "PID: -")
        tk.Label(info_bar, text="|", bg="#e0e0e0", fg="#888").pack(side="left")
        self.version_label = add_info_label(info_bar, "Build: -")
        tk.Label(info_bar, text="|", bg="#e0e0e0", fg="#888").pack(side="left")
        self.player_count_label = add_info_label(info_bar, "Players: - / -")
        tk.Label(info_bar, text="|", bg="#e0e0e0", fg="#888").pack(side="left")
        self.crash_label = add_info_label(info_bar, "Crashes: 0", fg="#555")
        self.reset_crash_btn = tk.Button(info_bar, text="Reset Count", font=("Arial", 7), command=self.reset_crash_counter)
        self.reset_crash_btn.pack(side="left", padx=2)
        
        # --- AUTHOR LABEL ---
        self.author_label = tk.Label(info_bar, text=f"Dev: {AUTHOR_NAME}", bg="#e0e0e0", fg="#0056b3", font=("Segoe UI", 8, "bold"), cursor="hand2")
        self.author_label.pack(side="right", padx=10)
        self.author_label.bind("<Button-1>", self.open_community_url)
        # --------------------

        self.open_logs_btn = tk.Button(info_bar, text="📂 Logs", font=("Arial", 8), command=self.open_logs_folder)
        self.open_logs_btn.pack(side="right", padx=5)

    def open_community_url(self, event):
        url = self.community_url.get()
        if url: webbrowser.open(url)

    def update_header_title(self):
        name = self.server_name_entry.get()
        if name: self.header_title_label.config(text=name)
        else: self.header_title_label.config(text="Vein Server")

    def setup_scrollable_area(self):
        container = tk.Frame(self.root)
        container.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(container)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.create_tabs(self.scrollable_frame)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def create_tabs(self, parent):
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)
        
        main_settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(main_settings_frame, text="Main Server Settings")
        
        tk.Label(main_settings_frame, text="Map Selection:", anchor="w").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.map_combobox = ttk.Combobox(main_settings_frame, width=57, values=["/Game/Vein/Maps/ChamplainValley?listen"])
        self.map_combobox.grid(row=0, column=1, padx=5, pady=5, columnspan=2)
        
        tk.Label(main_settings_frame, text="Server Name (Display):", anchor="w").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.server_name_entry = tk.Entry(main_settings_frame, width=50)
        self.server_name_entry.grid(row=1, column=1, columnspan=2, sticky="w", padx=5, pady=5)
        
        tk.Label(main_settings_frame, text="Session Name (Save File):", anchor="w").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.session_name_entry = tk.Entry(main_settings_frame, width=50)
        self.session_name_entry.grid(row=2, column=1, columnspan=2, sticky="w", padx=5, pady=5)
        
        tk.Label(main_settings_frame, text="Server Password:", anchor="w").grid(row=3, column=0, sticky="w", padx=10, pady=5)
        self.server_password_entry = tk.Entry(main_settings_frame, width=30, show="*")
        self.server_password_entry.grid(row=3, column=1, sticky="w", padx=5, pady=5)

        tk.Label(main_settings_frame, text="Game Port (UDP):", anchor="w").grid(row=4, column=0, sticky="w", padx=10, pady=5)
        self.port_entry = tk.Entry(main_settings_frame, width=10, validate='key', validatecommand=self.vcmd)
        self.port_entry.grid(row=4, column=1, sticky="w", padx=5, pady=5)
        
        tk.Label(main_settings_frame, text="Query Port (UDP):", anchor="w").grid(row=5, column=0, sticky="w", padx=10, pady=5)
        self.query_port_entry = tk.Entry(main_settings_frame, width=10, validate='key', validatecommand=self.vcmd)
        self.query_port_entry.grid(row=5, column=1, sticky="w", padx=5, pady=5)
        
        tk.Label(main_settings_frame, text="Max Players:", anchor="w").grid(row=6, column=0, sticky="w", padx=10, pady=5)
        self.players_entry = tk.Entry(main_settings_frame, width=10, validate='key', validatecommand=self.vcmd)
        self.players_entry.grid(row=6, column=1, sticky="w", padx=5, pady=5)
        
        ttk.Separator(main_settings_frame, orient='horizontal').grid(row=7, columnspan=4, sticky='ew', pady=10, padx=5)
        self.rcon_checkbox = tk.Checkbutton(main_settings_frame, text="Enable RCON (Not Supported Yet)", variable=self.rcon_enabled_var, fg="grey")
        self.rcon_checkbox.grid(row=8, column=0, columnspan=2, sticky="w", padx=10, pady=5)
        tk.Label(main_settings_frame, text="RCON Port:", anchor="w", fg="grey").grid(row=9, column=0, sticky="w", padx=10, pady=5)
        self.rcon_port_entry = tk.Entry(main_settings_frame, width=10, validate='key', validatecommand=self.vcmd)
        self.rcon_port_entry.grid(row=9, column=1, sticky="w", padx=5, pady=5)
        tk.Label(main_settings_frame, text="RCON Password:", anchor="w", fg="grey").grid(row=10, column=0, sticky="w", padx=10, pady=5)
        self.rcon_password_entry = tk.Entry(main_settings_frame, width=40, show="*")
        self.rcon_password_entry.grid(row=10, column=1, sticky="w", padx=5, pady=5, columnspan=2)
        ttk.Separator(main_settings_frame, orient='horizontal').grid(row=11, columnspan=4, sticky='ew', pady=10, padx=5)
        self.http_api_checkbox = tk.Checkbutton(main_settings_frame, text="Enable HTTP API", variable=self.http_api_enabled_var)
        self.http_api_checkbox.grid(row=12, column=0, columnspan=2, sticky="w", padx=10, pady=5)
        tk.Label(main_settings_frame, text="HTTP Port:", anchor="w").grid(row=13, column=0, sticky="w", padx=10, pady=5)
        self.http_api_port_entry = tk.Entry(main_settings_frame, width=10, validate='key', validatecommand=self.vcmd)
        self.http_api_port_entry.grid(row=13, column=1, sticky="w", padx=5, pady=5)
        ttk.Separator(main_settings_frame, orient='horizontal').grid(row=14, columnspan=4, sticky='ew', pady=15, padx=5)
        tk.Label(main_settings_frame, text="Super Admin SteamIDs:", font=("Helvetica", 9, "bold")).grid(row=15, column=0, sticky="w", padx=10, pady=5)
        self.admin_ids_var = tk.StringVar()
        self.admin_id_entry = tk.Entry(main_settings_frame, textvariable=self.admin_ids_var, width=50)
        self.admin_id_entry.grid(row=15, column=1, columnspan=2, sticky="w", padx=5)
        tk.Label(main_settings_frame, text="(Comma Separated)", fg="grey").grid(row=16, column=1, sticky="w", padx=5)
        
        self.create_gameplay_tab_vertical()
        
        players_frame = ttk.Frame(self.notebook)
        self.notebook.add(players_frame, text="Online Players")
        filter_frame = tk.Frame(players_frame, pady=5)
        filter_frame.pack(fill='x', padx=10)
        tk.Label(filter_frame, text="View Mode:").pack(side='left')
        self.player_filter_menu = ttk.Combobox(filter_frame, textvariable=self.player_filter_var, values=["Online Now", "History (All Time)"], state="readonly")
        self.player_filter_menu.pack(side='left', padx=10)
        self.player_filter_menu.bind("<<ComboboxSelected>>", lambda e: self.refresh_player_list_ui())
        players_list_container = tk.LabelFrame(players_frame, text="Players", padx=10, pady=10)
        players_list_container.pack(fill='both', expand=True, padx=10, pady=10)
        self.players_listbox = tk.Listbox(players_list_container, font=("Helvetica", 10), height=15)
        self.players_listbox.pack(fill='both', expand=True, side='left')
        players_scrollbar = tk.Scrollbar(players_list_container, orient="vertical")
        players_scrollbar.config(command=self.players_listbox.yview)
        players_scrollbar.pack(side="right", fill="y")
        self.players_listbox.config(yscrollcommand=players_scrollbar.set)

        self.create_scheduler_widgets()

        log_frame = ttk.Frame(self.notebook)
        self.notebook.add(log_frame, text="Live Log Viewer")
        log_toolbar = tk.Frame(log_frame)
        log_toolbar.pack(fill='x', padx=5, pady=2)
        tk.Label(log_toolbar, text="Manager Events Log (System Diary)", font=("Segoe UI", 8, "bold"), fg="grey").pack(side='left')
        tk.Button(log_toolbar, text="Purge Manager Logs", font=("Segoe UI", 8), bg="#ffebee", command=self.purge_manager_logs).pack(side='right')
        
        # --- MATRIX MODE (FIXED) ---
        self.log_text = tk.Text(log_frame, state='disabled', wrap='word', bg='black', fg='#00ff00', font=("Courier New", 9), height=20)
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)
        # ---------------------------
        
        steamcmd_frame = ttk.Frame(self.notebook)
        self.notebook.add(steamcmd_frame, text="Server Management")
        steam_path_frame = tk.LabelFrame(steamcmd_frame, text="SteamCMD Path", padx=10, pady=5)
        steam_path_frame.pack(fill='x', padx=10, pady=10)
        self.steamcmd_path_entry = tk.Entry(steam_path_frame)
        self.steamcmd_path_entry.pack(side='left', fill='x', expand=True, padx=5)
        tk.Button(steam_path_frame, text="Browse...", command=self.browse_path).pack(side='left', padx=5)
        
        auto_update_frame = tk.LabelFrame(steamcmd_frame, text="Smart Auto-Updater", padx=10, pady=5, fg="#0056b3")
        auto_update_frame.pack(fill='x', padx=10, pady=5)
        row1 = tk.Frame(auto_update_frame)
        row1.pack(fill='x', pady=2)
        tk.Checkbutton(row1, text="Enable Auto-Updater", variable=self.auto_update_enabled, font=("Helvetica", 9, "bold")).pack(side='left')
        tk.Label(row1, text=" | ").pack(side='left')
        tk.Checkbutton(row1, text="Passive Mode (Wait for 0 Players)", variable=self.auto_update_passive).pack(side='left')
        row2 = tk.Frame(auto_update_frame)
        row2.pack(fill='x', pady=2)
        tk.Label(row2, text="Steam Branch:").pack(side='left')
        tk.Entry(row2, textvariable=self.steam_branch_var, width=15).pack(side='left', padx=5)
        tk.Label(row2, text="(Default: public)").pack(side='left', padx=2)
        self.updater_status_label = tk.Label(row2, text="Status: Idle", fg="grey")
        self.updater_status_label.pack(side='right', padx=10)
        
        steam_actions_frame = tk.Frame(steamcmd_frame)
        steam_actions_frame.pack(fill='x', padx=10, pady=5)
        self.update_button = tk.Button(steam_actions_frame, text="Manual Update", command=self.start_steamcmd_update)
        self.update_button.pack(side='left', padx=5, pady=5)
        self.validate_button = tk.Button(steam_actions_frame, text="Manual Validate", command=self.start_steamcmd_validate)
        self.validate_button.pack(side='left', padx=5, pady=5)

        # --- NOTIFICATIONS (DISCORD) ---
        discord_frame = tk.LabelFrame(steamcmd_frame, text="Notifications & Community (New)", padx=10, pady=5, fg="#7289da")
        discord_frame.pack(fill='x', padx=10, pady=5)
        
        d_row1 = tk.Frame(discord_frame)
        d_row1.pack(fill='x', pady=2)
        tk.Checkbutton(d_row1, text="Enable Discord Webhooks", variable=self.discord_enabled).pack(side='left')
        
        d_row2 = tk.Frame(discord_frame)
        d_row2.pack(fill='x', pady=2)
        tk.Label(d_row2, text="Webhook URL:").pack(side='left')
        tk.Entry(d_row2, textvariable=self.discord_webhook_url).pack(side='left', fill='x', expand=True, padx=5)
        
        d_row3 = tk.Frame(discord_frame)
        d_row3.pack(fill='x', pady=2)
        tk.Label(d_row3, text="Community URL (for Dev Button):").pack(side='left')
        tk.Entry(d_row3, textvariable=self.community_url).pack(side='left', fill='x', expand=True, padx=5)
        # -------------------------------
        
        steam_console_frame = tk.LabelFrame(steamcmd_frame, text="SteamCMD Output", padx=5, pady=5)
        steam_console_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # --- MATRIX MODE (FIXED) ---
        self.steamcmd_console_output = tk.Text(steam_console_frame, state='disabled', wrap='word', bg='black', fg='#00ff00', font=("Courier New", 9), height=15)
        self.steamcmd_console_output.pack(fill='both', expand=True)
        # ---------------------------

        backup_frame = ttk.Frame(self.notebook)
        self.notebook.add(backup_frame, text="Backups")
        backup_settings_frame = tk.LabelFrame(backup_frame, text="Backup Settings", padx=10, pady=5)
        backup_settings_frame.pack(fill='x', padx=10, pady=5)
        tk.Label(backup_settings_frame, text="File Name Format:").pack(side='left')
        self.backup_format_entry = tk.Entry(backup_settings_frame, width=30)
        self.backup_format_entry.pack(side='left', padx=5)
        tk.Label(backup_settings_frame, text="|  Keep Last:").pack(side='left', padx=(10, 2))
        self.backup_retention_spinbox = tk.Spinbox(backup_settings_frame, from_=1, to=100, width=3)
        self.backup_retention_spinbox.pack(side='left')
        auto_backup_frame = tk.LabelFrame(backup_frame, text="Automated Backups", padx=10, pady=5)
        auto_backup_frame.pack(fill='x', padx=10, pady=5)
        tk.Checkbutton(auto_backup_frame, text="Enable Reactive Backups", variable=self.reactive_backup_enabled).pack(side='left')
        tk.Label(auto_backup_frame, text="    |    ").pack(side='left')
        tk.Checkbutton(auto_backup_frame, text="Backup before Stop/Restart", variable=self.backup_on_stop).pack(side='left')
        backup_list_frame = tk.Frame(backup_frame)
        backup_list_frame.pack(fill='both', expand=True, padx=10, pady=5)
        self.backup_list = tk.Listbox(backup_list_frame, bg='#f0f0f0', font=("Courier New", 10), height=10)
        self.backup_list.pack(side='left', fill='both', expand=True)
        backup_actions_frame = tk.Frame(backup_list_frame)
        backup_actions_frame.pack(side='left', fill='y', padx=10)
        self.create_backup_button = tk.Button(backup_actions_frame, text="Create Backup", command=self.start_manual_backup)
        self.create_backup_button.pack(pady=5, fill='x')
        self.open_backup_folder_button = tk.Button(backup_actions_frame, text="Open Folder", command=self.open_backup_folder)
        self.open_backup_folder_button.pack(pady=5, fill='x')

    def create_gameplay_tab_vertical(self):
        gameplay_frame = ttk.Frame(self.notebook)
        self.notebook.add(gameplay_frame, text="Gameplay")
        
        paned = tk.PanedWindow(gameplay_frame, orient=tk.HORIZONTAL)
        paned.pack(fill="both", expand=True)
        
        menu_frame = tk.Frame(paned, width=160, bg="#f0f0f0", relief="sunken", bd=1)
        menu_frame.pack_propagate(False)
        content_frame = tk.Frame(paned, padx=10, pady=10)
        
        paned.add(menu_frame)
        paned.add(content_frame)
        
        first_category = None
        def show_frame(cat_name):
            for name, btn in self.menu_buttons.items():
                if name == cat_name: btn.config(bg="white", relief="sunken")
                else: btn.config(bg="#f0f0f0", relief="flat")
            for f in self.gameplay_frames.values(): f.pack_forget()
            if cat_name in self.gameplay_frames: self.gameplay_frames[cat_name].pack(fill="both", expand=True)

        for category, settings_list in GAMEPLAY_DEFINITIONS.items():
            if not first_category: first_category = category
            btn = tk.Button(menu_frame, text=category, anchor="w", padx=10, pady=8, font=("Segoe UI", 9), command=lambda c=category: show_frame(c))
            btn.pack(fill="x")
            self.menu_buttons[category] = btn
            cat_frame = tk.Frame(content_frame)
            self.gameplay_frames[category] = cat_frame
            tk.Label(cat_frame, text=category, font=("Segoe UI", 12, "bold", "underline")).pack(anchor="w", pady=(0, 15))
            for (label_text, key, tooltip, type_str, file_type, section, default_val) in settings_list:
                row = tk.Frame(cat_frame)
                row.pack(fill="x", pady=2)
                tk.Label(row, text=label_text, width=25, anchor="w").pack(side="left")
                widget = None
                if type_str == "bool":
                    var = tk.BooleanVar(value=default_val)
                    widget = tk.Checkbutton(row, variable=var)
                    widget.pack(side="left")
                else:
                    var = tk.StringVar(value=str(default_val))
                    widget = tk.Entry(row, textvariable=var, width=18)
                    widget.pack(side="left")
                tk.Label(row, text=tooltip, fg="grey", anchor="w", width=50).pack(side="left", padx=10)
                self.gameplay_vars[key] = {'var': var, 'type': type_str, 'file': file_type, 'section': section, 'widget': widget, 'default': default_val}
        
        if first_category: show_frame(first_category)

    def browse_path(self):
        path = filedialog.askdirectory(title="Select your Vein Dedicated Server folder")
        if path: 
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, path)
            self.load_game_ini_settings()
            self.check_prerequisites(path)

    def check_prerequisites(self, server_path):
        if not server_path: return
        dll_dir = os.path.join(server_path, 'Vein', 'Binaries', 'Win64')
        dll_path = os.path.join(dll_dir, 'steamclient64.dll')
        if not os.path.exists(dll_path):
            self.append_to_log_viewer(">> Prerequisite: steamclient64.dll missing. Attempting Auto-Fix...\n")
            steamcmd_exe = self.steamcmd_path_entry.get()
            if steamcmd_exe and os.path.exists(steamcmd_exe):
                source_dll = os.path.join(os.path.dirname(steamcmd_exe), 'steamclient64.dll')
                if os.path.exists(source_dll):
                    try: 
                        shutil.copy(source_dll, dll_path)
                        self.append_to_log_viewer(">> Success: steamclient64.dll copied.\n")
                    except Exception as e: 
                        messagebox.showerror("Auto-Fix Failed", str(e))
                else: messagebox.showwarning("Prerequisite Missing", "steamclient64.dll not found in SteamCMD folder.")
        game_ini_path = os.path.join(server_path, 'Vein', 'Saved', 'Config', 'WindowsServer', 'Game.ini')
        if not os.path.exists(game_ini_path):
            try:
                os.makedirs(os.path.dirname(game_ini_path), exist_ok=True)
                with open(game_ini_path, 'w', encoding='utf-8') as f:
                    f.write("[/Script/Vein.VeinGameSession]\nServerName=Vein Server\n\n[/Script/Vein.ServerSettings]\nServerName=Vein Server\n")
            except: pass

    def create_scheduler_widgets(self):
        sched_frame = ttk.Frame(self.notebook)
        self.notebook.add(sched_frame, text="Restart Schedule")
        daily_group = tk.LabelFrame(sched_frame, text="Fixed Time Schedule", padx=10, pady=10)
        daily_group.pack(fill='x', padx=10, pady=10)
        tk.Checkbutton(daily_group, text="Enable Time Schedule", variable=self.sched_daily_enabled, font=("Helvetica", 9, "bold")).pack(anchor='w')
        days_frame = tk.Frame(daily_group)
        days_frame.pack(fill='x', pady=5)
        for i, name in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]): 
            tk.Checkbutton(days_frame, text=name, variable=self.sched_days_vars[i]).pack(side='left', padx=5)
        time_frame = tk.Frame(daily_group)
        time_frame.pack(fill='x', pady=5)
        tk.Label(time_frame, text="Restart Times (HH:MM):").pack(side='left')
        self.sched_time_entry = tk.Entry(time_frame, width=40)
        self.sched_time_entry.pack(side='left', padx=5)
        interval_group = tk.LabelFrame(sched_frame, text="Uptime Limit", padx=10, pady=10)
        interval_group.pack(fill='x', padx=10, pady=10)
        tk.Checkbutton(interval_group, text="Enable Uptime Limit", variable=self.sched_interval_enabled, font=("Helvetica", 9, "bold")).pack(anchor='w')
        int_input_frame = tk.Frame(interval_group)
        int_input_frame.pack(fill='x', pady=5)
        tk.Label(int_input_frame, text="Restart after").pack(side='left')
        self.sched_interval_entry = tk.Entry(int_input_frame, width=5)
        self.sched_interval_entry.pack(side='left', padx=5)
        tk.Label(int_input_frame, text="hours").pack(side='left')
        info_frame = tk.LabelFrame(sched_frame, text="Scheduler Status", padx=10, pady=10)
        info_frame.pack(fill='both', expand=True, padx=10, pady=10)
        self.sched_status_label = tk.Label(info_frame, text="Waiting...", font=("Courier New", 10), justify="left")
        self.sched_status_label.pack(anchor="w")

    def toggle_inputs(self, state):
        widgets = [
            self.path_entry, self.browse_button, self.map_combobox, 
            self.server_name_entry, self.session_name_entry,
            self.port_entry, self.query_port_entry, 
            self.server_password_entry,
            self.players_entry, self.rcon_checkbox, self.rcon_port_entry, 
            self.rcon_password_entry, self.http_api_checkbox, 
            self.http_api_port_entry, self.admin_id_entry, 
            self.save_button, self.backup_format_entry, 
            self.backup_retention_spinbox
        ]
        for w in widgets:
            try: w.config(state=state)
            except: pass
        for key, data in self.gameplay_vars.items():
            try: data['widget'].config(state=state)
            except: pass

    def append_to_log_viewer(self, text):
        self.log_text.config(state='normal')
        if int(self.log_text.index('end-1c').split('.')[0]) > 2500:
            self.log_text.delete('1.0', '2.0')
        self.log_text.insert(tk.END, text)
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')

    def start_server(self, trigger="USER"):
        self.check_prerequisites(self.path_entry.get())
        if trigger == "USER": self.log_manager_event("USER", "Start Button Clicked.")
        elif trigger == "UPDATER": self.log_manager_event("UPDATER", "Restarting Server after update.")
        
        server_path = self.path_entry.get()
        if server_path:
            log_dir = os.path.join(server_path, 'Vein', 'Saved', 'Logs')
            if os.path.exists(log_dir):
                try:
                    logs = sorted(glob.glob(os.path.join(log_dir, "*.log")), key=os.path.getmtime)
                    if len(logs) > 50:
                        for f in logs[:-50]:
                            try: os.remove(f)
                            except: pass
                except: pass

        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, f"\n=== SERVER START [ {datetime.now().strftime('%H:%M:%S')} ] ===\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
        
        self.update_gui_for_state("STARTING")
        self.save_manager_config()
        self.send_discord_webhook("START", "Server is starting up...") # Discord
        
        exe_path = os.path.join(server_path, 'Vein', 'Binaries', 'Win64', SERVER_EXECUTABLE)
        if not os.path.exists(exe_path): 
            messagebox.showerror("Error", f"{SERVER_EXECUTABLE} not found.")
            self.update_gui_for_state("OFFLINE")
            self.log_manager_event("ERROR", "VeinServer Executable not found.")
            return
        
        self.save_all_settings(silent=True)
        map_string = self.map_combobox.get()
        session_name = self.session_name_entry.get()
        if session_name: map_string += f"?SessionName={session_name}"
        max_players = self.players_entry.get()
        command = [exe_path, map_string]
        if self.port_entry.get(): command.append(f"-Port={self.port_entry.get()}")
        if self.query_port_entry.get(): command.append(f"-QueryPort={self.query_port_entry.get()}")
        if max_players: command.append(f"-MaxPlayers={max_players}")
        if self.rcon_enabled_var.get(): 
            command.extend(["-RconEnabled=true", f"-RconPort={self.rcon_port_entry.get()}", f"-RconPassword={self.rcon_password_entry.get()}"])
        command.append("-log")
        
        try:
            process = subprocess.Popen(command)
            self.server_pid = process.pid
            self.log_manager_event("SYSTEM", f"Process Launched. PID: {process.pid}")
            threading.Thread(target=self.verify_process_stability, daemon=True).start()
            threading.Thread(target=self.log_scanner_task, daemon=True).start()
        except Exception as e: 
            messagebox.showerror("Error", f"Failed to start: {e}")
            self.log_manager_event("ERROR", f"Failed to launch process: {e}")
            self.update_gui_for_state("OFFLINE")
        
    def verify_process_stability(self):
        time.sleep(3)
        if self.server_pid:
            if not psutil.pid_exists(self.server_pid):
                self.root.after(0, self.append_to_log_viewer, ">>> ERROR: Server Process died immediately (Zombie Start).\n")
                self.root.after(0, self.update_gui_for_state, "CRASHED")
                self.log_manager_event("CRASH", "Zombie Process detected (Died immediately).")
                self.server_pid = None
            else: 
                self.root.after(0, self.append_to_log_viewer, ">>> Process Stability Check: PASS\n")

    def browse_steamcmd(self):
        path = filedialog.askopenfilename(title="Select steamcmd.exe", filetypes=[("Executable", "*.exe")])
        if path: 
            self.steamcmd_path_entry.delete(0, tk.END)
            self.steamcmd_path_entry.insert(0, path)

    def start_steamcmd_update(self):
        self.notebook.select(5) 
        self.log_manager_event("USER", "Manual Update Requested.")
        args = ['+login', 'anonymous', '+app_update', VEIN_APP_ID, '-beta', self.steam_branch_var.get(), '+quit']
        thread = threading.Thread(target=self.run_steamcmd_command, args=(args, self.steamcmd_console_output), daemon=True)
        thread.start()

    def start_steamcmd_validate(self):
        self.notebook.select(5) 
        self.log_manager_event("USER", "Manual Validation Requested.")
        args = ['+login', 'anonymous', '+app_update', VEIN_APP_ID, '-beta', self.steam_branch_var.get(), 'validate', '+quit']
        thread = threading.Thread(target=self.run_steamcmd_command, args=(args, self.steamcmd_console_output), daemon=True)
        thread.start()

    def run_steamcmd_command(self, args, output_widget, callback=None):
        self.is_updating = True
        self.root.after(0, self.update_gui_for_state, "UPDATING")
        self.root.after(0, self.root.config, {'cursor': 'wait'}) 
        output_widget.config(state='normal')
        output_widget.delete(1.0, tk.END)
        output_widget.insert(tk.END, ">>> Initializing SteamCMD process...\n")
        output_widget.insert(tk.END, f">>> Target Branch: {self.steam_branch_var.get()}\n")
        output_widget.insert(tk.END, "------------------------------------------------------------\n")
        output_widget.see(tk.END)
        output_widget.config(state='disabled')
        steamcmd_exe = self.steamcmd_path_entry.get()
        if not steamcmd_exe: 
            self.root.after(0, self.update_gui_for_state, "OFFLINE")
            self.root.after(0, self.root.config, {'cursor': ''})
            self.is_updating = False
            return
        install_dir = self.path_entry.get()
        working_dir = os.path.dirname(os.path.abspath(steamcmd_exe))
        command = [steamcmd_exe, '+force_install_dir', install_dir] + args
        success = False
        try:
            self.log_manager_event("UPDATER", "SteamCMD Started.")
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, creationflags=subprocess.CREATE_NO_WINDOW, encoding='utf-8', errors='ignore', cwd=working_dir)
            for line in iter(process.stdout.readline, ''): 
                self.root.after(0, self.append_to_steamcmd_console, line, output_widget)
            process.stdout.close()
            process.wait()
            if process.returncode == 0: success = True
        except Exception as e:
            self.root.after(0, self.append_to_steamcmd_console, f"\nCRITICAL ERROR: {str(e)}\n", output_widget)
            self.log_manager_event("UPDATER", f"SteamCMD Error: {e}")
        finally:
            self.is_updating = False
            self.root.after(0, self.root.config, {'cursor': ''}) 
            if success: self.root.after(0, self.refresh_build_id_display)
            self.log_manager_event("UPDATER", f"SteamCMD Finished. Success={success}")
            if callback: callback(success)
            else:
                self.root.after(0, self.update_gui_for_state, "OFFLINE")
                self.root.after(0, messagebox.showinfo, "SteamCMD", "Process Finished.")

    def append_to_steamcmd_console(self, text, widget):
        widget.config(state='normal')
        widget.insert(tk.END, text)
        widget.see(tk.END)
        widget.config(state='disabled')

    def auto_updater_loop(self):
        time.sleep(10)
        startup_grace_period = 300 
        slept_time = 0
        while slept_time < startup_grace_period:
            time.sleep(10)
            slept_time += 10
        while True:
            jitter = random.randint(0, 60)
            sleep_time = 600 + jitter 
            if not self.keep_alive_var.get() and not self.is_server_running():
                 time.sleep(10)
                 continue
            if self.auto_update_enabled.get() and not self.update_loop_prevention:
                try: self.perform_version_check()
                except: self.updater_status_label.config(text=f"Check Failed")
            time.sleep(sleep_time)

    def get_local_build_id(self):
        server_path = self.path_entry.get()
        if not server_path: return None
        paths_to_check = [
            os.path.join(server_path, 'steamapps', f'appmanifest_{VEIN_APP_ID}.acf'),
            os.path.join(server_path, 'Vein', 'steamapps', f'appmanifest_{VEIN_APP_ID}.acf'), 
            os.path.join(server_path, f'appmanifest_{VEIN_APP_ID}.acf') 
        ]
        found_file = None
        for p in paths_to_check:
            if os.path.exists(p):
                found_file = p
                break
        if not found_file: return None
        try:
            with open(found_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                match = re.search(r'"buildid"\s+"(\d+)"', content)
                if match: return match.group(1)
        except: pass
        return None

    def refresh_build_id_display(self):
        bid = self.get_local_build_id()
        if bid:
            self.current_build_id = bid
            self.version_label.config(text=f"Build: {bid}")

    def get_remote_build_id(self):
        steamcmd_exe = self.steamcmd_path_entry.get()
        if not steamcmd_exe or not os.path.exists(steamcmd_exe): return None
        args = [steamcmd_exe, '+login', 'anonymous', '+app_info_update', '1', '+app_info_print', VEIN_APP_ID, '+quit']
        working_dir = os.path.dirname(os.path.abspath(steamcmd_exe))
        try:
            process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=subprocess.CREATE_NO_WINDOW, encoding='utf-8', errors='ignore', cwd=working_dir)
            stdout, _ = process.communicate()
            branch = self.steam_branch_var.get()
            lines = stdout.splitlines()
            in_branches = False
            in_target_branch = False
            for line in lines:
                clean = line.strip().replace('"', '')
                if "branches" in clean: in_branches = True
                if in_branches:
                    if clean.startswith(branch): in_target_branch = True
                    if in_target_branch:
                        if "buildid" in clean:
                            parts = clean.split()
                            if len(parts) >= 2: return parts[1]
                        if "}" in clean and not "buildid" in clean: 
                            in_target_branch = False
        except: pass
        return None

    def perform_version_check(self):
        self.root.after(0, self.updater_status_label.config, {'text': "Checking..."})
        local = self.get_local_build_id()
        if not local:
            self.root.after(0, self.updater_status_label.config, {'text': "Err: Local ID"})
            return
        remote = self.get_remote_build_id()
        if not remote:
            self.root.after(0, self.updater_status_label.config, {'text': "Err: Remote ID"})
            return
        self.local_build_id = local
        self.remote_build_id = remote
        self.root.after(0, self.version_label.config, {'text': f"Build: {local}"})
        log_msg = f"[Auto-Updater] Check: Local={local} vs Remote={remote}\n"
        self.root.after(0, self.append_to_steamcmd_console, log_msg, self.steamcmd_console_output)
        self.log_manager_event("UPDATER_CHECK", f"Local: {local} | Remote: {remote}")
        if remote != local and remote.isdigit() and local.isdigit():
            if int(remote) > int(local): self.trigger_update_protocol()
            else: self.root.after(0, self.updater_status_label.config, {'text': "Up to Date"})
        else: self.root.after(0, self.updater_status_label.config, {'text': "Up to Date"})

    def trigger_update_protocol(self):
        self.root.after(0, self.updater_status_label.config, {'text': "Update Pending", 'fg': 'orange'})
        if self.auto_update_passive.get():
            current_players = self.get_player_count()
            if current_players > 0:
                self.root.after(0, self.append_to_steamcmd_console, f"[Auto-Updater] Update delayed. {current_players} players online.\n", self.steamcmd_console_output)
                return 
        self.root.after(0, self.append_to_steamcmd_console, f"[Auto-Updater] Starting Update Sequence...\n", self.steamcmd_console_output)
        threading.Thread(target=self.execute_safe_update, daemon=True).start()

    def execute_safe_update(self):
        self.log_manager_event("UPDATER", "Auto-Update triggered.")
        old_local_id = self.get_local_build_id()
        was_running = self.is_server_running()
        if was_running:
            self.root.after(0, self.update_gui_for_state, "STOPPING")
            self.manual_shutdown_requested = True 
            self.initiate_shutdown()
            time.sleep(10) 
        self.create_backup_task(silent=True)
        time.sleep(2)
        self.root.after(0, self.notebook.select, 5) 
        args = ['+login', 'anonymous', '+app_update', VEIN_APP_ID, '-beta', self.steam_branch_var.get(), '+quit']
        
        def on_update_complete(success):
            new_local_id = self.get_local_build_id()
            self.log_manager_event("UPDATER", f"Update process finished. Old ID: {old_local_id} -> New ID: {new_local_id}")
            if success and old_local_id == new_local_id:
                self.update_loop_prevention = True
                self.root.after(0, self.updater_status_label.config, {'text': "Loop Detected", 'fg': 'red'})
                self.root.after(0, self.append_to_steamcmd_console, "\n[UPDATER] WARNING: Build ID did not change. Loop Guard Activated. Auto-updates paused.\n", self.steamcmd_console_output)
                self.log_manager_event("UPDATER", "Loop Guard Activated. Preventing infinite restarts.")
                self.send_discord_webhook("UPDATE", "Update Loop Guard Activated. Auto-updates paused.")
                if was_running:
                    self.root.after(0, self.append_to_steamcmd_console, "[UPDATER] Server was running. Restarting despite failed update...\n", self.steamcmd_console_output)
                    self.root.after(0, lambda: self.start_server("UPDATER"))
            elif success:
                self.root.after(0, self.append_to_steamcmd_console, "[Auto-Updater] Update Success.\n", self.steamcmd_console_output)
                self.send_discord_webhook("UPDATE", f"Server Updated to Build {new_local_id}")
                if was_running:
                    self.root.after(0, self.append_to_steamcmd_console, "[Auto-Updater] Restarting server...\n", self.steamcmd_console_output)
                    self.root.after(0, lambda: self.start_server("UPDATER"))
                else:
                    self.root.after(0, self.append_to_steamcmd_console, "[Auto-Updater] Server was offline. Staying offline.\n", self.steamcmd_console_output)
                self.root.after(0, self.updater_status_label.config, {'text': "Updated", 'fg': 'green'})
            else:
                self.root.after(0, self.append_to_steamcmd_console, "[Auto-Updater] Update FAILED.\n", self.steamcmd_console_output)
                self.root.after(0, self.updater_status_label.config, {'text': "Update Failed", 'fg': 'red'})

        self.root.after(0, lambda: threading.Thread(target=self.run_steamcmd_command, args=(args, self.steamcmd_console_output, on_update_complete), daemon=True).start())

    def get_player_count(self):
        text = self.player_count_label.cget('text')
        try:
            parts = text.split(':')[1].split('/')[0].strip()
            if parts.isdigit(): return int(parts)
        except: pass
        return 0

    def log_scanner_task(self):
        time.sleep(3)
        server_path = self.path_entry.get()
        if not server_path: return
        log_dir = os.path.join(server_path, 'Vein', 'Saved', 'Logs')
        active_log_file = os.path.join(log_dir, 'Vein.log')
        wait_time = 0
        while not os.path.exists(active_log_file) and wait_time < 10: 
            time.sleep(1)
            wait_time += 1
        if not os.path.exists(active_log_file): 
            self.root.after(0, self.append_to_log_viewer, f"Error: '{active_log_file}' not found.\n")
            return
        self.root.after(0, self.append_to_log_viewer, f"--- Tailing: {os.path.basename(active_log_file)} ---\n")
        try:
            with open(active_log_file, 'r', encoding='utf-8', errors='ignore') as f:
                f.seek(0, 2)
                found_golden_line = False
                while self.is_server_running():
                    line = f.readline()
                    if not line: 
                        time.sleep(0.2)
                        continue
                    self.root.after(0, self.append_to_log_viewer, line)
                    if not found_golden_line:
                        if 'avail=OK' in line and 'config=OK' in line:
                            self.root.after(0, self.append_to_log_viewer, "\n--- Server is ONLINE ---\n")
                            self.root.after(0, self.update_gui_for_state, "ONLINE")
                            found_golden_line = True
                    if self.reactive_backup_enabled.get() and "Saved to slot" in line:
                        threading.Thread(target=self.delayed_backup_trigger, daemon=True).start()
        except: pass

    def delayed_backup_trigger(self):
        time.sleep(15.0) 
        if not self.is_backing_up: self.create_backup_task(silent=True)

    def api_poller_loop(self):
        while self.is_checking_status:
            current_status = self.status_text_label.cget('text')
            if ("ONLINE" in current_status or "STARTING" in current_status) and self.http_api_enabled_var.get():
                try:
                    port = self.http_api_port_entry.get() or '8080'
                    url = f"http://127.0.0.1:{port}/status"
                    with urllib.request.urlopen(url, timeout=5) as response:
                        if response.status == 200:
                            if "STARTING" in current_status:
                                self.root.after(0, self.update_gui_for_state, "ONLINE")
                                self.root.after(0, self.append_to_log_viewer, "\n>>> [SYSTEM] API Connection Successful. Forcing ONLINE status.\n")

                            data = json.loads(response.read().decode('utf-8'))
                            players_data = data.get('onlinePlayers', {})
                            player_names = []
                            current_players = []
                            if isinstance(players_data, dict):
                                for key, val in players_data.items():
                                    name = val.get('name', str(key)) if isinstance(val, dict) else str(val)
                                    player_names.append(name)
                                    current_players.append({'id': key, 'name': name})
                            elif isinstance(players_data, list):
                                for p in players_data:
                                    name = p.get('name', 'Unknown') if isinstance(p, dict) else str(p)
                                    player_names.append(name)
                                    current_players.append({'id': name, 'name': name})
                            self.update_player_history(current_players)
                            self.player_count_label.config(text=f"Players: {len(player_names)} / {self.players_entry.get()}", fg="black")
                            self.root.after(0, self.refresh_player_list_ui, player_names)
                except: self.player_count_label.config(text="Players: N/A", fg="red")
            time.sleep(10)

    def load_player_history(self):
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, 'r') as f: return json.load(f)
            except: return {}
        return {}

    def update_player_history(self, current_players):
        updated = False
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for p in current_players:
            pid = str(p['id'])
            name = p['name']
            if pid not in self.player_history:
                self.player_history[pid] = {'name': name, 'first_seen': now_str, 'last_seen': now_str}
                updated = True
            else:
                self.player_history[pid]['last_seen'] = now_str
                if self.player_history[pid]['name'] != name: 
                    self.player_history[pid]['name'] = name 
                updated = True
        if updated:
            try:
                with open(HISTORY_FILE, 'w') as f: json.dump(self.player_history, f, indent=4)
            except: pass

    def refresh_player_list_ui(self, current_online_names=None):
        mode = self.player_filter_var.get()
        self.players_listbox.delete(0, tk.END)
        if mode == "Online Now":
            if current_online_names:
                for name in current_online_names: 
                    self.players_listbox.insert(tk.END, f"• {name}")
                    self.players_listbox.itemconfig(tk.END, {'fg': 'green'})
        else:
            sorted_history = sorted(self.player_history.values(), key=lambda x: x['last_seen'], reverse=True)
            for p in sorted_history:
                self.players_listbox.insert(tk.END, f"{p['name']} (Last: {p['last_seen']})")
                self.players_listbox.itemconfig(tk.END, {'fg': 'black'})

    def scheduler_loop(self):
        while self.is_checking_status:
            if self.is_server_running() and "ONLINE" in self.status_text_label.cget('text'):
                current_time = datetime.now()
                restart_needed = False
                if self.sched_daily_enabled.get():
                    try:
                        time_strings = [t.strip() for t in self.sched_time_entry.get().split(',') if t.strip()]
                        if self.sched_days_vars[current_time.weekday()].get():
                            for t_str in time_strings:
                                try:
                                    target_dt = datetime.strptime(t_str, "%H:%M")
                                    if current_time.hour == target_dt.hour and current_time.minute == target_dt.minute:
                                        should_trigger = True
                                        if self.last_daily_trigger_time and (current_time - self.last_daily_trigger_time).total_seconds() < 65: should_trigger = False
                                        if should_trigger:
                                            self.last_daily_trigger_time = current_time
                                            restart_needed = True
                                            self.processing_scheduled_restart = True
                                except: pass
                    except: pass
                if self.sched_interval_enabled.get() and not restart_needed:
                    try:
                        interval_hours = float(self.sched_interval_entry.get())
                        if self.server_pid:
                            p = psutil.Process(self.server_pid)
                            uptime = current_time - datetime.fromtimestamp(p.create_time())
                            if uptime > timedelta(hours=interval_hours): 
                                restart_needed = True
                                self.processing_scheduled_restart = True
                    except: pass
                self.sched_status_label.config(text="Scheduler Active")
                if restart_needed:
                    self.log_manager_event("SCHEDULER", "Restart triggered by schedule.")
                    self.root.after(0, self.restart_server)
                    time.sleep(30)
                    self.processing_scheduled_restart = False
            else: self.sched_status_label.config(text="Scheduler Paused")
            time.sleep(1)

    def start_manual_backup(self):
        if self.is_backing_up: return
        self.create_backup_button.config(state='disabled', text="Backing up...")
        threading.Thread(target=self.create_backup_task, kwargs={'silent': False}, daemon=True).start()

    def create_backup_task(self, silent=False):
        self.is_backing_up = True
        self.log_manager_event("BACKUP", "Starting backup process...")
        server_path = self.path_entry.get()
        saved_dir = os.path.join(server_path, 'Vein', 'Saved')
        backup_dir = os.path.join(server_path, 'Backups')
        os.makedirs(backup_dir, exist_ok=True)
        try:
            fmt = self.backup_format_entry.get() or "Server_Backup_%Y-%m-%d_%H-%M-%S"
            time_str = datetime.now().strftime(fmt)
            temp_dir = tempfile.mkdtemp()
            temp_save_path = os.path.join(temp_dir, 'Saved')
            cmd = ['robocopy', saved_dir, temp_save_path, '/E', '/ZB', '/COPY:DAT', '/R:1', '/W:1', '/XD', 'Logs', 'Crashes', 'Saved/Logs', '*.log']
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
            shutil.make_archive(os.path.join(backup_dir, time_str), 'zip', temp_save_path)
            shutil.rmtree(temp_dir)
            try:
                retention_limit = int(self.backup_retention_spinbox.get())
                if retention_limit > 0:
                    backups = sorted(glob.glob(os.path.join(backup_dir, "*.zip")), key=os.path.getmtime)
                    if len(backups) > retention_limit:
                        files_to_delete = len(backups) - retention_limit
                        for i in range(files_to_delete):
                            os.remove(backups[i])
            except: pass
            if not silent: messagebox.showinfo("Backup", "Complete")
            self.log_manager_event("BACKUP", "Backup Complete.")
        except Exception as e:
            self.log_manager_event("ERROR", f"Backup Failed: {e}")
        self.is_backing_up = False
        self.root.after(0, self.create_backup_button.config, {'state': 'normal', 'text': 'Create Backup'})

    def open_backup_folder(self):
        server_path = self.path_entry.get()
        if server_path: os.startfile(os.path.join(server_path, 'Backups'))

    def open_logs_folder(self):
        server_path = self.path_entry.get()
        if server_path: 
            log_path = os.path.join(server_path, 'Vein', 'Saved', 'Logs')
            if os.path.exists(log_path): os.startfile(log_path)
            else: messagebox.showerror("Error", "Logs folder not found yet.")

    def stop_server(self): 
        self.log_manager_event("USER", "Stop Button Clicked.")
        self.manual_shutdown_requested = True
        self.send_discord_webhook("STOP", "Server Stop Requested by User.")
        self.initiate_shutdown()
        
    def restart_server(self): 
        self.log_manager_event("USER", "Restart Button Clicked.")
        self.restart_requested = True
        self.send_discord_webhook("STOP", "Server Restart Initiated...")
        self.initiate_shutdown()
    
    def initiate_shutdown(self):
        if not self.is_server_running(): 
            self.update_gui_for_state("OFFLINE")
            return
        if self.backup_on_stop.get():
             self.create_backup_button.config(state='disabled', text="Auto-Backing up...")
             threading.Thread(target=self.shutdown_with_backup_sequence, daemon=True).start()
        else:
             self.update_gui_for_state("RESTARTING" if self.restart_requested else "SHUTTING DOWN...")
             threading.Thread(target=self.shutdown_sequence, daemon=True).start()

    def shutdown_with_backup_sequence(self):
        self.create_backup_task(silent=True)
        self.root.after(0, self.update_gui_for_state, "RESTARTING" if self.restart_requested else "SHUTTING DOWN...")
        self.shutdown_sequence()

    def shutdown_sequence(self):
        try:
            if self.server_pid and psutil.pid_exists(self.server_pid): 
                p = psutil.Process(self.server_pid)
                p.terminate()
                p.wait(timeout=5)
        except: pass
        finally: self.server_pid = None
    
    def status_checker_loop(self):
        time.sleep(5) 
        while self.is_checking_status:
            if self.is_updating:
                time.sleep(2)
                continue 
            is_running = self.is_server_running()
            if is_running:
                self.server_was_running = True
                self.pid_label.config(text=f"PID: {self.server_pid}")
            else:
                self.pid_label.config(text="PID: -")
                if self.processing_scheduled_restart: pass 
                elif self.server_was_running:
                    self.server_was_running = False 
                    if self.restart_requested: 
                        self.restart_requested = False
                        time.sleep(5)
                        self.start_server()
                    elif self.manual_shutdown_requested: 
                        self.manual_shutdown_requested = False
                        self.update_gui_for_state("OFFLINE")
                    elif self.keep_alive_var.get():
                        self.crash_count += 1
                        self.update_crash_counter_ui()
                        self.update_gui_for_state("CRASHED")
                        self.log_manager_event("WATCHDOG", "Crash detected. Keep Alive restarting...")
                        self.send_discord_webhook("CRASH", f"CRASH DETECTED! Auto-restart detected. (Crash Count: {self.crash_count})")
                        time.sleep(15)
                        self.start_server()
                    else: 
                        self.crash_count += 1
                        self.update_crash_counter_ui()
                        self.update_gui_for_state("OFFLINE")
                        self.log_manager_event("WATCHDOG", "Crash detected. Server staying offline.")
                        self.send_discord_webhook("CRASH", "CRASH DETECTED! Server is now OFFLINE.")
                elif self.keep_alive_var.get() and "OFFLINE" in self.status_text_label.cget('text'): 
                    self.start_server()
            time.sleep(5)

    def update_crash_counter_ui(self):
        color = "red" if self.crash_count > 0 else "#555"
        self.crash_label.config(text=f"Crashes: {self.crash_count}", fg=color)

    def reset_crash_counter(self):
        self.crash_count = 0
        self.update_crash_counter_ui()
    
    def get_existing_section_name(self, config_obj, target_section):
        for section in config_obj.sections():
            if section.lower() == target_section.lower(): return section
        return target_section

    def update_engine_ini_raw(self, filepath, updates_dict):
        if not os.path.exists(filepath): return
        with open(filepath, 'r', encoding='utf-8') as f: lines = f.readlines()
        new_lines = []
        in_cvar_section = False
        section_found = False
        keys_written = set()
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('[') and stripped.endswith(']'):
                if stripped.lower() == '[consolevariables]': 
                    in_cvar_section = True
                    section_found = True
                    new_lines.append(line)
                    continue
                else:
                    if in_cvar_section:
                        for key, val in updates_dict.items():
                            if key not in keys_written: 
                                new_lines.append(f"{key}={val}\n")
                                keys_written.add(key)
                    in_cvar_section = False
                    new_lines.append(line)
                    continue
            if in_cvar_section:
                matched_key = None
                for key in updates_dict:
                    if stripped.lower().startswith(key.lower() + "="): 
                        matched_key = key
                        break
                if matched_key: 
                    new_lines.append(f"{matched_key}={updates_dict[matched_key]}\n")
                    keys_written.add(matched_key)
                else: new_lines.append(line)
            else: new_lines.append(line)
        if not section_found: 
            new_lines.append("\n[ConsoleVariables]\n")
            in_cvar_section = True
        if in_cvar_section:
            for key, val in updates_dict.items():
                if key not in keys_written: 
                    new_lines.append(f"{key}={val}\n")
                    keys_written.add(key)
        with open(filepath, 'w', encoding='utf-8') as f: f.writelines(new_lines)
            
    def load_engine_ini_raw(self, filepath, keys):
        if not os.path.exists(filepath): return
        current_values = {}
        in_cvar_section = False
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                stripped = line.strip()
                if stripped.lower() == '[consolevariables]': 
                    in_cvar_section = True
                    continue
                if stripped.startswith('[') and stripped != '[ConsoleVariables]': 
                    in_cvar_section = False
                    continue
                if in_cvar_section and '=' in stripped:
                    parts = stripped.split('=', 1)
                    k = parts[0].strip()
                    v = parts[1].strip()
                    for target_key in keys:
                        if k.lower() == target_key.lower(): current_values[target_key] = v
        for key in keys:
            data = self.gameplay_vars[key] 
            if key in current_values:
                val = current_values[key]
                if data['type'] == 'bool': data['var'].set(val == '1' or val.lower() == 'true')
                else: data['var'].set(val)
            else: data['var'].set(data['default'])

    def load_game_ini_settings(self):
        game_keys = [k for k, v in self.gameplay_vars.items() if v['file'] == 'Game']
        self.load_ini_file_standard("Game.ini", '/Script/Vein.ServerSettings', game_keys)
        engine_keys = [k for k, v in self.gameplay_vars.items() if v['file'] == 'Engine']
        engine_path = self.get_ini_path("Engine.ini")
        if engine_path: self.load_engine_ini_raw(engine_path, engine_keys)
        game_ini = self.get_ini_path("Game.ini")
        if game_ini and os.path.exists(game_ini):
            config = configparser.ConfigParser(strict=False); config.optionxform = str
            try:
                with open(game_ini, 'r', encoding='utf-8') as f: config.read_file(f)
            except: config.read(game_ini)
            actual_section_gs = self.get_existing_section_name(config, '/Script/Vein.VeinGameSession')
            actual_section_settings = self.get_existing_section_name(config, '/Script/Vein.ServerSettings')
            disp_name = config.get(actual_section_settings, 'ServerName', fallback='Vein Server')
            self.server_name_entry.delete(0, tk.END)
            self.server_name_entry.insert(0, disp_name)
            self._apply_config_value(self.session_name_entry, config, 'Startup', 'SessionName', 'Server')
            password_val = config.get(actual_section_gs, 'Password', fallback="")
            self.server_password_entry.delete(0, tk.END)
            self.server_password_entry.insert(0, password_val)
            admin_ids_str = config.get(actual_section_gs, 'SuperAdminSteamIDs', fallback="")
            self.admin_ids_var.set(admin_ids_str)
            http_port = '8080'
            if config.has_option(actual_section_gs, 'HTTPPort'): http_port = config.get(actual_section_gs, 'HTTPPort')
            self.http_api_port_entry.delete(0, tk.END); self.http_api_port_entry.insert(0, http_port)
            loaded_mp = None
            if config.has_option(actual_section_gs, 'MaxPlayers'): loaded_mp = config.get(actual_section_gs, 'MaxPlayers')
            if not loaded_mp:
                eng_gs = self.get_existing_section_name(config, '/Script/Engine.GameSession')
                if config.has_option(eng_gs, 'MaxPlayers'): loaded_mp = config.get(eng_gs, 'MaxPlayers')
            if loaded_mp:
                self.players_entry.delete(0, tk.END)
                self.players_entry.insert(0, loaded_mp)

    def update_ini_file_standard(self, filename, default_section, keys):
        path = self.get_ini_path(filename)
        if not path: return
        config = configparser.ConfigParser(strict=False)
        config.optionxform = str 
        try:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f: config.read_file(f)
        except: config.read(path)
        for key in keys:
            data = self.gameplay_vars[key]
            target_section = data.get('section', default_section)
            actual_section = self.get_existing_section_name(config, target_section)
            if not config.has_section(actual_section): config.add_section(actual_section)
            val = data['var'].get()
            if data['type'] == 'bool': val = "True" if val else "False" 
            config.set(actual_section, key, str(val))
        try:
            with open(path, 'w', encoding='utf-8') as f: config.write(f, space_around_delimiters=False)
        except Exception as e: raise OSError(f"Failed to write to {filename}: {e}")

    def load_ini_file_standard(self, filename, default_section, keys):
        path = self.get_ini_path(filename)
        if not path or not os.path.exists(path): return
        config = configparser.ConfigParser(strict=False); config.optionxform = str
        try:
            with open(path, 'r', encoding='utf-8') as f: config.read_file(f)
        except: config.read(path)
        for key in keys:
            data = self.gameplay_vars[key]
            target_section = data.get('section', default_section)
            actual_section = self.get_existing_section_name(config, target_section)
            if config.has_section(actual_section) and config.has_option(actual_section, key):
                val = config.get(actual_section, key)
                if data['type'] == 'bool': data['var'].set(val == '1' or val.lower() == 'true')
                else: data['var'].set(val)
            else: data['var'].set(data['default'])

    def save_manager_config(self):
        try:
            config = configparser.ConfigParser(interpolation=None)
            config['Manager'] = {'ServerPath': self.path_entry.get(), 'KeepAlive': str(self.keep_alive_var.get()), 'SteamCMDPath': self.steamcmd_path_entry.get()}
            config['Window'] = {'Width': str(self.root.winfo_width()), 'Height': str(self.root.winfo_height()), 'X': str(self.root.winfo_x()), 'Y': str(self.root.winfo_y())}
            config['Startup'] = {'Map': self.map_combobox.get(), 'SessionName': self.session_name_entry.get(), 'Port': self.port_entry.get(), 'QueryPort': self.query_port_entry.get(), 'MaxPlayers': self.players_entry.get(), 'EnableHTTPAPI': str(self.http_api_enabled_var.get())}
            config['RCON'] = {'Enabled': str(self.rcon_enabled_var.get()), 'Port': self.rcon_port_entry.get(), 'Password': self.rcon_password_entry.get()}
            config['Backups'] = {'Format': self.backup_format_entry.get(), 'Retention': self.backup_retention_spinbox.get(), 'ReactiveBackupEnabled': str(self.reactive_backup_enabled.get()), 'BackupOnStop': str(self.backup_on_stop.get())}
            config['AutoUpdater'] = {'Enabled': str(self.auto_update_enabled.get()), 'PassiveMode': str(self.auto_update_passive.get()), 'SteamBranch': self.steam_branch_var.get()}
            days_str = ",".join([str(i) for i,v in enumerate(self.sched_days_vars) if v.get()])
            config['Scheduler'] = {'DailyEnabled': str(self.sched_daily_enabled.get()), 'DailyDays': days_str, 'DailyTime': self.sched_time_entry.get(), 'IntervalEnabled': str(self.sched_interval_enabled.get()), 'IntervalHours': self.sched_interval_entry.get()}
            
            # --- DISCORD SAVE ---
            config['Discord'] = {'Enabled': str(self.discord_enabled.get()), 'WebhookURL': self.discord_webhook_url.get(), 'CommunityURL': self.community_url.get()}
            # --------------------

            with open(MANAGER_CONFIG_FILE, 'w') as configfile: config.write(configfile)
            self.log_manager_event("SYSTEM", "Configuration Saved.")
        except Exception as e: messagebox.showerror("Save Config Error", f"Failed to save manager_config.ini:\n{e}")

    def save_all_settings(self, silent=False):
        try:
            self.update_header_title()
            game_ini_path = self.get_ini_path("Game.ini")
            if game_ini_path: os.makedirs(os.path.dirname(game_ini_path), exist_ok=True)
            game_keys = [k for k, v in self.gameplay_vars.items() if v['file'] == 'Game']
            self.update_ini_file_standard("Game.ini", '/Script/Vein.ServerSettings', game_keys)
            engine_keys = [k for k, v in self.gameplay_vars.items() if v['file'] == 'Engine']
            updates = {}
            for key in engine_keys:
                val = self.gameplay_vars[key]['var'].get()
                if self.gameplay_vars[key]['type'] == 'bool': val = '1' if val else '0' 
                updates[key] = str(val)
            max_players_val = self.players_entry.get()
            if max_players_val: updates['vein.Characters.Max'] = str(max_players_val)
            engine_path = self.get_ini_path("Engine.ini")
            if engine_path:
                os.makedirs(os.path.dirname(engine_path), exist_ok=True)
                self.update_engine_ini_raw(engine_path, updates)
            if game_ini_path:
                config = configparser.ConfigParser(strict=False); config.optionxform = str
                try:
                    if os.path.exists(game_ini_path):
                        with open(game_ini_path, 'r', encoding='utf-8') as f: config.read_file(f)
                except: config.read(game_ini_path)
                section_gamesession = self.get_existing_section_name(config, '/Script/Vein.VeinGameSession')
                section_settings = self.get_existing_section_name(config, '/Script/Vein.ServerSettings')
                section_engine_gs = self.get_existing_section_name(config, '/Script/Engine.GameSession')
                if not config.has_section(section_gamesession): config.add_section(section_gamesession)
                if not config.has_section(section_settings): config.add_section(section_settings)
                if not config.has_section(section_engine_gs): config.add_section(section_engine_gs)
                if max_players_val:
                    config.set(section_gamesession, 'MaxPlayers', max_players_val)
                    config.set(section_engine_gs, 'MaxPlayers', max_players_val)
                config.set(section_settings, 'ServerName', self.server_name_entry.get())
                config.set(section_gamesession, 'ServerName', self.server_name_entry.get())
                password_val = self.server_password_entry.get()
                if password_val: config.set(section_gamesession, 'Password', password_val)
                elif config.has_option(section_gamesession, 'Password'): config.remove_option(section_gamesession, 'Password')
                config.set(section_gamesession, 'SuperAdminSteamIDs', self.admin_ids_var.get())
                if self.http_api_enabled_var.get() and self.http_api_port_entry.get(): config.set(section_gamesession, 'HTTPPort', self.http_api_port_entry.get())
                elif config.has_option(section_gamesession, 'HTTPPort'): config.remove_option(section_gamesession, 'HTTPPort')
                with open(game_ini_path, 'w', encoding='utf-8') as f: config.write(f, space_around_delimiters=False)
            self.save_manager_config()
            if not silent: messagebox.showinfo("Success", "Settings saved successfully!")
        except Exception as e:
            error_trace = traceback.format_exc()
            messagebox.showerror("SAVE FAILED", f"An error occurred while saving:\n{str(e)}\n\nTraceback:\n{error_trace}")

    def on_closing(self):
        try:
            self.save_manager_config()
            self.log_manager_event("SYSTEM", "Manager Closing.")
            if self.is_server_running():
                choice = messagebox.askyesnocancel("Exit Manager", "Server is currently RUNNING.\n\n• Yes: Stop Server and Exit\n• No: Leave Server Running and Exit (Detach)\n• Cancel: Stay Here")
                if choice is None: return 
                if choice: 
                    self.log_manager_event("USER", "Exit with Stop requested.")
                    self.manual_shutdown_requested = True
                    try: psutil.Process(self.server_pid).terminate()
                    except: pass
                else: self.log_manager_event("USER", "Exit (Detach) requested.")
                self.is_checking_status = False
                self.root.destroy()
            else:
                self.is_checking_status = False
                self.root.destroy()
        except: sys.exit(0)

    def get_ini_path(self, filename):
        server_path = self.path_entry.get()
        if not server_path: return None
        return os.path.join(server_path, 'Vein', 'Saved', 'Config', 'WindowsServer', filename)
    
    def is_server_running(self):
        if self.server_pid:
            if psutil.pid_exists(self.server_pid):
                try:
                    if psutil.Process(self.server_pid).status() != psutil.STATUS_ZOMBIE: return True
                except: pass
        server_path = self.path_entry.get()
        if not server_path: return False
        expected_exe = os.path.join(server_path, 'Vein', 'Binaries', 'Win64', SERVER_EXECUTABLE)
        for proc in psutil.process_iter(['pid', 'name', 'exe']):
            try:
                if proc.info['name'] == SERVER_EXECUTABLE:
                    if proc.info['exe'] and os.path.normpath(proc.info['exe']) == os.path.normpath(expected_exe):
                        self.server_pid = proc.info['pid']; return True
            except: pass
        return False

    def update_gui_for_state(self, state):
        color = "green" if state == "ONLINE" else "orange" if "..." in state or state == "UPDATING" else "red"
        self.status_text_label.config(text=f"Status: {state}", fg=color)
        dot_color = "green" if state == "ONLINE" else "blue" if state == "UPDATING" else "orange" if "..." in state else "red"
        try: self.status_canvas.itemconfig(self.status_dot, fill=dot_color)
        except: pass
        if state in ["ONLINE", "STARTING", "STOPPING", "UPDATING"]:
            self.toggle_inputs('disabled')
            if state == "UPDATING":
                self.start_button.config(state="disabled"); self.stop_button.config(state="disabled"); self.restart_button.config(state="disabled"); self.update_button.config(state="disabled"); self.validate_button.config(state="disabled")
            else:
                self.start_button.config(state="disabled"); self.stop_button.config(state="normal"); self.restart_button.config(state="normal"); self.update_button.config(state="disabled"); self.validate_button.config(state="disabled")
        else: 
            self.toggle_inputs('normal')
            self.start_button.config(state="normal"); self.stop_button.config(state="disabled"); self.restart_button.config(state="disabled"); self.update_button.config(state="normal"); self.validate_button.config(state="normal")

    def load_manager_config(self):
        if not os.path.exists(MANAGER_CONFIG_FILE):
            self.backup_format_entry.insert(0, "Server_Backup_%Y-%m-%d_%H-%M-%S")
            self.sched_time_entry.insert(0, "00:00, 04:00, 08:00, 12:00, 16:00, 20:00")
            self.sched_interval_entry.insert(0, "4")
            self.query_port_entry.insert(0, "27015")
            return
        config = configparser.ConfigParser(interpolation=None)
        config.read(MANAGER_CONFIG_FILE)
        self._apply_config_value(self.path_entry, config, 'Manager', 'ServerPath', '')
        self._apply_config_value(self.steamcmd_path_entry, config, 'Manager', 'SteamCMDPath', '')
        self.keep_alive_var.set(config.getboolean('Manager', 'KeepAlive', fallback=False))
        self.map_combobox.set(config.get('Startup', 'Map', fallback='/Game/Vein/Maps/ChamplainValley?listen'))
        self._apply_config_value(self.port_entry, config, 'Startup', 'Port', '7779')
        self._apply_config_value(self.query_port_entry, config, 'Startup', 'QueryPort', '27015') 
        self._apply_config_value(self.players_entry, config, 'Startup', 'MaxPlayers', '20')
        self.http_api_enabled_var.set(config.getboolean('Startup', 'EnableHTTPAPI', fallback=False))
        self._apply_config_value(self.session_name_entry, config, 'Startup', 'SessionName', 'Server')
        self._apply_config_value(self.rcon_port_entry, config, 'RCON', 'Port', '27020')
        self.rcon_enabled_var.set(config.getboolean('RCON', 'Enabled', fallback=False))
        if config.has_section('Backups'):
            self._apply_config_value(self.backup_format_entry, config, 'Backups', 'Format', 'Server_Backup_%Y-%m-%d_%H-%M-%S')
            retention = config.get('Backups', 'Retention', fallback='6')
            self.backup_retention_spinbox.delete(0, tk.END); self.backup_retention_spinbox.insert(0, retention)
            self.reactive_backup_enabled.set(config.getboolean('Backups', 'ReactiveBackupEnabled', fallback=True))
            self.backup_on_stop.set(config.getboolean('Backups', 'BackupOnStop', fallback=False))
        if config.has_section('AutoUpdater'):
            self.auto_update_enabled.set(config.getboolean('AutoUpdater', 'Enabled', fallback=False))
            self.auto_update_passive.set(config.getboolean('AutoUpdater', 'PassiveMode', fallback=True))
            self.steam_branch_var.set(config.get('AutoUpdater', 'SteamBranch', fallback='public'))
        if config.has_section('Scheduler'):
            self.sched_daily_enabled.set(config.getboolean('Scheduler', 'DailyEnabled', fallback=False))
            self._apply_config_value(self.sched_time_entry, config, 'Scheduler', 'DailyTime', '')
            days_str = config.get('Scheduler', 'DailyDays', fallback="0,1,2,3,4,5,6")
            days_indices = [int(x) for x in days_str.split(',') if x.strip().isdigit()]
            for i, var in enumerate(self.sched_days_vars): var.set(i in days_indices)
            self.sched_interval_enabled.set(config.getboolean('Scheduler', 'IntervalEnabled', fallback=False))
            self._apply_config_value(self.sched_interval_entry, config, 'Scheduler', 'IntervalHours', '4')
        
        # --- DISCORD LOAD ---
        if config.has_section('Discord'):
            self.discord_enabled.set(config.getboolean('Discord', 'Enabled', fallback=False))
            self._apply_config_value(self.discord_webhook_url, config, 'Discord', 'WebhookURL', '')
            self._apply_config_value(self.community_url, config, 'Discord', 'CommunityURL', 'https://discord.gg/')
        # --------------------

        server_path = self.path_entry.get()
        if server_path:
            self.load_game_ini_settings()
            self.check_prerequisites(server_path)

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = ServerManager(root)
        root.mainloop()
    except Exception as e:
        error_msg = traceback.format_exc()
        try:
            with open("CRASH_LOG.txt", "w") as f: f.write(error_msg)
            ctypes.windll.user32.MessageBoxW(0, f"Critical Error:\n{e}\n\nSee CRASH_LOG.txt for details.", "Vein Manager Crash", 0x10)
        except: print(f"FATAL ERROR:\n{error_msg}")