# main.py
# The Entry Point & Controller

import tkinter as tk
from tkinter import messagebox, filedialog
import os
import sys
import threading
import time
import json
import psutil
import traceback
import ctypes
import webbrowser
import subprocess
import urllib.request
import zipfile
from datetime import datetime

# --- IMPORT MODULES ---
import constants
import config
import logic
import gui

# --- ERROR LOGGING ---
def log_crash(msg):
    with open("CRASH_LOG.txt", "a") as f:
        f.write(f"[{datetime.now()}] {msg}\n")

class ServerManager:
    def __init__(self, root):
        self.root = root
        self.root.title(constants.APP_TITLE)
        if os.path.exists(constants.ICON_FILE):
            try: self.root.iconbitmap(constants.ICON_FILE)
            except: pass

        # --- VARIABLES ---
        self.server_pid = None
        self.is_checking_status = True
        self.manual_shutdown_requested = False
        self.restart_requested = False
        self.server_was_running = False
        self.is_backing_up = False
        self.crash_count = 0
        self.manager_update_available = False
        self.current_build_id = "Unknown"
        self.update_loop_prevention = False
        
        # Validation
        self.vcmd = (self.root.register(self.validate_number_input), '%P')

        # Configuration Vars
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
        self.discord_enabled = tk.BooleanVar(value=False)
        self.discord_webhook_url = tk.StringVar()
        self.community_url = tk.StringVar(value=constants.LINK_DISCORD_MAIN)
        self.player_filter_var = tk.StringVar(value="Online Now")
        
        # Wizard Vars
        self.wizard_install_path = tk.StringVar()
        self.wizard_steamcmd_path = tk.StringVar()
        self.wizard_is_import = False

        # Gameplay Vars Storage
        self.gameplay_vars = {} 
        self.menu_buttons = {}
        self.gameplay_frames = {}

        # --- ENV CHECK ---
        self.check_environment()
        
        # --- BOOT ---
        self.conf_parser = config.get_manager_config()
        server_path = self.conf_parser.get('Manager', 'ServerPath', fallback='')
        
        if not server_path or not os.path.exists(server_path):
            self.setup_wizard_ui()
        else:
            self.launch_dashboard()

    def check_environment(self):
        current_folder = os.path.basename(os.path.normpath(constants.APPLICATION_PATH))
        if "TEST" in current_folder.upper():
            self.env_type = "TEST"
            self.text_color = "#3498db" 
        else:
            self.env_type = "LIVE"
            self.text_color = "#e74c3c"
        self.root.title(f"{constants.APP_TITLE} [{self.env_type}]")

    def validate_number_input(self, P):
        return P == "" or P.isdigit()

    # ==========================
    # === WIZARD LOGIC ===
    # ==========================
    def setup_wizard_ui(self):
        self.wizard_frame = tk.Frame(self.root, padx=20, pady=20)
        self.wizard_frame.pack(fill='both', expand=True)
        self.wiz_step_frames = {}
        for i in range(1, 5): 
            self.wiz_step_frames[i] = tk.Frame(self.wizard_frame)
        self.show_wizard_step(1)

    def show_wizard_step(self, step_num):
        for f in self.wiz_step_frames.values(): f.pack_forget()
        frame = self.wiz_step_frames[step_num]
        frame.pack(fill='both', expand=True)
        for widget in frame.winfo_children(): widget.destroy()
        
        if step_num == 1: self.build_wiz_step_1(frame)
        elif step_num == 2: self.build_wiz_step_2(frame)
        elif step_num == 3: self.build_wiz_step_3(frame)
        elif step_num == 4: self.build_wiz_step_4(frame)

    def build_wiz_step_1(self, parent):
        tk.Label(parent, text="Welcome to Vein Manager", font=("Segoe UI", 16, "bold")).pack(pady=10)
        tk.Label(parent, text="Select Install Folder:", font=("bold")).pack(anchor='w', pady=(20, 5))
        e = tk.Entry(parent, textvariable=self.wizard_install_path, width=50); e.pack(fill='x')
        if not self.wizard_install_path.get(): self.wizard_install_path.set("C:\\VeinServer")
        tk.Button(parent, text="Browse...", command=self.wiz_browse_install).pack(anchor='e')
        self.wiz_status_lbl = tk.Label(parent, text="", fg="blue"); self.wiz_status_lbl.pack(pady=10)
        tk.Button(parent, text="Next >", bg="#ddffdd", command=lambda: self.show_wizard_step(2)).pack(side='bottom', pady=10)
        self.wiz_check_import_status()

    def wiz_browse_install(self):
        d = filedialog.askdirectory()
        if d: 
            self.wizard_install_path.set(d)
            self.wiz_check_import_status()

    def wiz_check_import_status(self):
        exe = os.path.join(self.wizard_install_path.get(), 'Vein', 'Binaries', 'Win64', constants.SERVER_EXECUTABLE)
        if os.path.exists(exe):
            self.wizard_is_import = True
            self.wiz_status_lbl.config(text="✅ Existing Installation Detected!", fg="green")
        else:
            self.wizard_is_import = False
            self.wiz_status_lbl.config(text="New Installation.", fg="black")

    def build_wiz_step_2(self, parent):
        tk.Label(parent, text="SteamCMD Setup", font=("Segoe UI", 14, "bold")).pack(pady=10)
        if not self.wizard_steamcmd_path.get(): self.wizard_steamcmd_path.set("C:\\steamCMD\\steamcmd.exe")
        tk.Entry(parent, textvariable=self.wizard_steamcmd_path).pack(fill='x')
        tk.Button(parent, text="Browse...", command=self.wiz_browse_steam).pack(anchor='e')
        tk.Button(parent, text="Download SteamCMD", command=self.wiz_dl_steamcmd).pack(pady=5)
        tk.Button(parent, text="Next >", bg="#ddffdd", command=lambda: self.show_wizard_step(3)).pack(side='bottom', pady=10)

    def wiz_browse_steam(self):
        f = filedialog.askopenfilename(filetypes=[("Executable", "*.exe")])
        if f: self.wizard_steamcmd_path.set(f)

    def wiz_dl_steamcmd(self):
        try:
            exe = self.wizard_steamcmd_path.get()
            d = os.path.dirname(exe)
            os.makedirs(d, exist_ok=True)
            urllib.request.urlretrieve(constants.STEAMCMD_URL, os.path.join(d, "steamcmd.zip"))
            with zipfile.ZipFile(os.path.join(d, "steamcmd.zip"), 'r') as z: z.extractall(d)
            messagebox.showinfo("Success", "SteamCMD Downloaded.")
        except Exception as e: messagebox.showerror("Error", str(e))

    def build_wiz_step_3(self, parent):
        tk.Label(parent, text="Server Files", font=("Segoe UI", 14, "bold")).pack(pady=10)
        self.wiz_console = tk.Text(parent, height=10, bg="black", fg="#00ff00"); self.wiz_console.pack(fill='both')
        if self.wizard_is_import:
            self.wiz_console.insert(tk.END, "Import Mode. Skipping Download.")
        else:
            tk.Button(parent, text="Download Server", command=self.wiz_start_download).pack()
        tk.Button(parent, text="Next >", bg="#ddffdd", command=lambda: self.show_wizard_step(4)).pack(side='bottom', pady=10)

    def wiz_start_download(self):
        self.wiz_console.insert(tk.END, "Downloading...\n")
        threading.Thread(target=self.wiz_run_download, daemon=True).start()

    def wiz_run_download(self):
        logic.run_steamcmd(self.wizard_steamcmd_path.get(), self.wizard_install_path.get(), "public", lambda l: self.root.after(0, self.wiz_append_console, l))

    def wiz_append_console(self, t):
        self.wiz_console.insert(tk.END, t); self.wiz_console.see(tk.END)

    def build_wiz_step_4(self, parent):
        tk.Label(parent, text="Configuration", font=("Segoe UI", 14, "bold")).pack(pady=10)
        tk.Label(parent, text="Server Name:").pack()
        self.wiz_name = tk.Entry(parent); self.wiz_name.pack()
        if not self.wizard_is_import: self.wiz_name.insert(0, "Vein Server")
        tk.Button(parent, text="Finish & Launch", bg="#ddffdd", command=self.wiz_finish).pack(side='bottom', pady=20)

    def wiz_finish(self):
        self.conf_parser['Manager'] = {'ServerPath': self.wizard_install_path.get(), 'SteamCMDPath': self.wizard_steamcmd_path.get()}
        self.conf_parser['Startup'] = {'Map': '/Game/Vein/Maps/ChamplainValley?listen', 'SessionName': 'Server', 'Port': '7779', 'QueryPort': '27015', 'MaxPlayers': '16', 'EnableHTTPAPI': 'False'}
        config.save_manager_config(self.conf_parser)
        
        eng_updates = {
            "vein.Time.TimeMultiplier": "15.1",
            "vein.Time.NightTimeMultiplier": "3.2",
            "vein.Zombies.Health": "40"
        }
        config.update_engine_ini_cvar(self.wizard_install_path.get(), eng_updates)
        
        self.wizard_frame.destroy()
        self.launch_dashboard()

    # ==========================
    # === DASHBOARD LOGIC ===
    # ==========================
    def launch_dashboard(self):
        gui.create_main_layout(self)
        self.load_manager_config()
        self.load_game_ini_settings()
        
        threading.Thread(target=self.loop_status, daemon=True).start()
        threading.Thread(target=self.loop_scheduler, daemon=True).start()
        threading.Thread(target=self.loop_updater, daemon=True).start()
        
        logic.check_prerequisites(self.path_entry.get(), self.steamcmd_path_entry.get(), self.append_to_log_viewer)

    # --- ACTIONS ---
    def start_server(self, trigger="USER"):
        self.log_manager_event(trigger, "Start Requested.")
        server_path = self.path_entry.get()
        exe = os.path.join(server_path, 'Vein', 'Binaries', 'Win64', constants.SERVER_EXECUTABLE)
        
        if not os.path.exists(exe):
            messagebox.showerror("Error", "Executable not found.")
            return

        self.save_all_settings(silent=True)
        
        cmd = [exe, self.map_combobox.get()]
        if self.session_name_entry.get(): cmd[1] += f"?SessionName={self.session_name_entry.get()}"
        if self.port_entry.get(): cmd.append(f"-Port={self.port_entry.get()}")
        if self.query_port_entry.get(): cmd.append(f"-QueryPort={self.query_port_entry.get()}")
        if self.players_entry.get(): cmd.append(f"-MaxPlayers={self.players_entry.get()}")
        if self.rcon_enabled_var.get():
             cmd.extend(["-RconEnabled=true", f"-RconPort={self.rcon_port_entry.get()}", f"-RconPassword={self.rcon_password_entry.get()}"])
        cmd.append("-log")

        try:
            proc = subprocess.Popen(cmd)
            self.server_pid = proc.pid
            self.update_gui_for_state("STARTING")
            logic.send_discord_webhook(self.discord_webhook_url.get(), "START", "Server Starting...", self.env_type=="TEST")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def stop_server(self):
        self.manual_shutdown_requested = True
        self.log_manager_event("USER", "Stop Requested.")
        if self.backup_on_stop.get():
            self.create_backup_task(silent=True)
        
        if self.server_pid:
            try: psutil.Process(self.server_pid).terminate()
            except: pass
        self.server_pid = None
        logic.send_discord_webhook(self.discord_webhook_url.get(), "STOP", "Server Stopped.", self.env_type=="TEST")

    def restart_server(self):
        self.restart_requested = True
        self.stop_server()

    # --- IO HANDLERS ---
    def save_all_settings(self, silent=False):
        self.conf_parser['Manager']['ServerPath'] = self.path_entry.get()
        self.conf_parser['Manager']['SteamCMDPath'] = self.steamcmd_path_entry.get()
        self.conf_parser['Manager']['KeepAlive'] = str(self.keep_alive_var.get())
        
        if 'Startup' not in self.conf_parser: self.conf_parser['Startup'] = {}
        self.conf_parser['Startup']['Map'] = self.map_combobox.get()
        self.conf_parser['Startup']['SessionName'] = self.session_name_entry.get()
        self.conf_parser['Startup']['Port'] = self.port_entry.get()
        self.conf_parser['Startup']['QueryPort'] = self.query_port_entry.get()
        self.conf_parser['Startup']['MaxPlayers'] = self.players_entry.get()
        self.conf_parser['Startup']['EnableHTTPAPI'] = str(self.http_api_enabled_var.get())
        
        if 'RCON' not in self.conf_parser: self.conf_parser['RCON'] = {}
        self.conf_parser['RCON']['Enabled'] = str(self.rcon_enabled_var.get())
        self.conf_parser['RCON']['Port'] = self.rcon_port_entry.get()
        self.conf_parser['RCON']['Password'] = self.rcon_password_entry.get()

        if 'Discord' not in self.conf_parser: self.conf_parser['Discord'] = {}
        self.conf_parser['Discord']['Enabled'] = str(self.discord_enabled.get())
        self.conf_parser['Discord']['WebhookURL'] = self.discord_webhook_url.get()
        self.conf_parser['Discord']['CommunityURL'] = self.community_url.get()

        if 'AutoUpdater' not in self.conf_parser: self.conf_parser['AutoUpdater'] = {}
        self.conf_parser['AutoUpdater']['Enabled'] = str(self.auto_update_enabled.get())
        self.conf_parser['AutoUpdater']['PassiveMode'] = str(self.auto_update_passive.get())
        self.conf_parser['AutoUpdater']['SteamBranch'] = self.steam_branch_var.get()

        config.save_manager_config(self.conf_parser)

        g_ini = config.load_game_ini(self.path_entry.get())
        
        for s in ['/Script/Vein.VeinGameSession', '/Script/Vein.ServerSettings', '/Script/Engine.GameSession']:
            if not g_ini.has_section(s): g_ini.add_section(s)
            
        gs = config.get_existing_section_name(g_ini, '/Script/Vein.VeinGameSession')
        ss = config.get_existing_section_name(g_ini, '/Script/Vein.ServerSettings')
        eng = config.get_existing_section_name(g_ini, '/Script/Engine.GameSession')

        g_ini.set(gs, 'ServerName', self.server_name_entry.get())
        g_ini.set(ss, 'ServerName', self.server_name_entry.get())
        g_ini.set(gs, 'ServerDescription', self.server_desc_entry.get())
        g_ini.set(gs, 'MaxPlayers', self.players_entry.get())
        g_ini.set(eng, 'MaxPlayers', self.players_entry.get())
        
        pw = self.server_password_entry.get()
        if pw: g_ini.set(gs, 'Password', pw)
        elif g_ini.has_option(gs, 'Password'): g_ini.remove_option(gs, 'Password')
        
        g_ini.set(gs, 'SuperAdminSteamIDs', self.admin_ids_var.get())
        if self.http_api_enabled_var.get(): g_ini.set(gs, 'HTTPPort', self.http_api_port_entry.get())

        for key, data in self.gameplay_vars.items():
            if data['file'] == 'Game':
                sec = config.get_existing_section_name(g_ini, data['section'])
                if not g_ini.has_section(sec): g_ini.add_section(sec)
                val = data['var'].get()
                if data['type'] == 'bool': val = "True" if val else "False"
                g_ini.set(sec, key, str(val))

        config.save_game_ini(self.path_entry.get(), g_ini)

        engine_updates = {}
        for key, data in self.gameplay_vars.items():
            if data['file'] == 'Engine':
                val = data['var'].get()
                if data['type'] == 'combo_scarcity':
                    raw = data['widget'].get()
                    if "(" in raw: val = raw.split("(")[1].replace(")", "")
                elif data['type'] == 'bool':
                    val = '1' if val else '0'
                engine_updates[key] = str(val)
        
        if self.players_entry.get(): engine_updates['vein.Characters.Max'] = self.players_entry.get()
        
        config.update_engine_ini_cvar(self.path_entry.get(), engine_updates)
        
        self.update_header_title()
        if not silent: messagebox.showinfo("Success", "Settings Saved")

    def load_manager_config(self):
        c = self.conf_parser
        self.path_entry.insert(0, c.get('Manager', 'ServerPath', fallback=''))
        self.steamcmd_path_entry.insert(0, c.get('Manager', 'SteamCMDPath', fallback=''))
        self.keep_alive_var.set(c.getboolean('Manager', 'KeepAlive', fallback=False))
        
        self.map_combobox.set(c.get('Startup', 'Map', fallback='/Game/Vein/Maps/ChamplainValley?listen'))
        self.session_name_entry.insert(0, c.get('Startup', 'SessionName', fallback='Server'))
        self.port_entry.insert(0, c.get('Startup', 'Port', fallback='7779'))
        self.query_port_entry.insert(0, c.get('Startup', 'QueryPort', fallback='27015'))
        self.players_entry.insert(0, c.get('Startup', 'MaxPlayers', fallback='16'))
        self.http_api_enabled_var.set(c.getboolean('Startup', 'EnableHTTPAPI', fallback=False))
        
        if c.has_section('RCON'):
            self.rcon_enabled_var.set(c.getboolean('RCON', 'Enabled', fallback=False))
            self.rcon_port_entry.insert(0, c.get('RCON', 'Port', fallback='27020'))
            self.rcon_password_entry.insert(0, c.get('RCON', 'Password', fallback=''))
            
        if c.has_section('Discord'):
            self.discord_enabled.set(c.getboolean('Discord', 'Enabled', fallback=False))
            self.discord_webhook_url.set(c.get('Discord', 'WebhookURL', fallback=''))
            self.community_url.set(c.get('Discord', 'CommunityURL', fallback=constants.LINK_DISCORD_MAIN))

        if c.has_section('AutoUpdater'):
            self.auto_update_enabled.set(c.getboolean('AutoUpdater', 'Enabled', fallback=False))
            self.auto_update_passive.set(c.getboolean('AutoUpdater', 'PassiveMode', fallback=True))
            self.steam_branch_var.set(c.get('AutoUpdater', 'SteamBranch', fallback='public'))

    def load_game_ini_settings(self):
        g_ini = config.load_game_ini(self.path_entry.get())
        gs = config.get_existing_section_name(g_ini, '/Script/Vein.VeinGameSession')
        ss = config.get_existing_section_name(g_ini, '/Script/Vein.ServerSettings')
        
        self.server_name_entry.delete(0, tk.END); self.server_name_entry.insert(0, g_ini.get(ss, 'ServerName', fallback='Vein Server'))
        self.server_desc_entry.delete(0, tk.END); self.server_desc_entry.insert(0, g_ini.get(gs, 'ServerDescription', fallback=''))
        self.server_password_entry.delete(0, tk.END); self.server_password_entry.insert(0, g_ini.get(gs, 'Password', fallback=''))
        self.http_api_port_entry.delete(0, tk.END); self.http_api_port_entry.insert(0, g_ini.get(gs, 'HTTPPort', fallback='8080'))
        self.admin_ids_var.set(g_ini.get(gs, 'SuperAdminSteamIDs', fallback=''))
        
        for key, data in self.gameplay_vars.items():
            if data['file'] == 'Game':
                sec = config.get_existing_section_name(g_ini, data['section'])
                if g_ini.has_option(sec, key):
                    val = g_ini.get(sec, key)
                    if data['type'] == 'bool': data['var'].set(val == 'True')
                    else: data['var'].set(val)
        
        # FIX: Call the NEW config function to read Engine.ini
        eng_path = config.get_engine_ini_path(self.path_entry.get())
        cvar_data = config.load_engine_ini_raw(eng_path, list(self.gameplay_vars.keys()))

        # Update Variables from CVAR Data
        for key, data in self.gameplay_vars.items():
            if key in cvar_data:
                val = cvar_data[key]
                if data['type'] == 'bool':
                    data['var'].set(val == '1' or val.lower() == 'true')
                else:
                    data['var'].set(val)

        if "vein.Scarcity.Difficulty" in self.gameplay_vars:
            d = self.gameplay_vars["vein.Scarcity.Difficulty"]
            try:
                v = float(d['var'].get())
                if v == 2.0: d['widget'].set("Standard (2.0)")
                elif v == 1.0: d['widget'].set("More Loot (1.0)")
                elif v == 3.0: d['widget'].set("Less Loot (3.0)")
                elif v == 0.0: d['widget'].set("Infinite (0.0)")
                elif v == 4.0: d['widget'].set("Impossible (4.0)")
            except: pass

    # --- UI HELPERS ---
    def browse_path(self):
        d = filedialog.askdirectory()
        if d: 
            self.path_entry.delete(0, tk.END); self.path_entry.insert(0, d)
            logic.check_prerequisites(d, self.steamcmd_path_entry.get(), self.append_to_log_viewer)
            self.load_game_ini_settings()

    def browse_steamcmd(self):
        f = filedialog.askopenfilename(filetypes=[("Executable", "*.exe")])
        if f: self.steamcmd_path_entry.delete(0, tk.END); self.steamcmd_path_entry.insert(0, f)

    def update_header_title(self):
        self.header_title_label.config(text=self.server_name_entry.get() or "Vein Server")

    def update_gui_for_state(self, state):
        self.status_text_label.config(text=f"Status: {state}", fg="green" if state == "ONLINE" else "red")
        try: self.status_canvas.itemconfig(self.status_dot, fill="green" if state == "ONLINE" else "red")
        except: pass
        
        s = "disabled" if state in ["ONLINE", "STARTING", "UPDATING"] else "normal"
        self.start_button.config(state=s)
        self.stop_button.config(state="normal" if state == "ONLINE" else "disabled")
        self.restart_button.config(state="normal" if state == "ONLINE" else "disabled")
        
        for w in [self.path_entry, self.map_combobox, self.port_entry, self.players_entry]:
            w.config(state=s)

    def append_to_log_viewer(self, text):
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, text)
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')

    def open_logs_folder(self):
        p = os.path.join(self.path_entry.get(), 'Vein', 'Saved', 'Logs')
        if os.path.exists(p): os.startfile(p)

    def open_backup_folder(self):
        p = os.path.join(self.path_entry.get(), 'Backups')
        if os.path.exists(p): os.startfile(p)

    def purge_manager_logs(self):
        if messagebox.askyesno("Confirm", "Clear logs?"):
            open(constants.EVENTS_LOG_FILE, 'w').close()

    def reset_crash_counter(self):
        self.crash_count = 0
        self.crash_label.config(text="Crashes: 0", fg="#555")

    def refresh_player_list_ui(self, current_online_names=None):
        mode = self.player_filter_var.get()
        self.players_listbox.delete(0, tk.END)
        if mode == "Online Now" and current_online_names:
            for n in current_online_names: self.players_listbox.insert(tk.END, f"• {n}")
        elif mode == "History (All Time)":
            for pid, data in self.player_history.items():
                self.players_listbox.insert(tk.END, f"{data['name']} (Last: {data['last_seen']})")

    def load_player_history(self):
        if os.path.exists(constants.HISTORY_FILE):
            try: 
                with open(constants.HISTORY_FILE, 'r') as f: return json.load(f)
            except: return {}
        return {}

    def log_manager_event(self, cat, msg):
        try:
            with open(constants.EVENTS_LOG_FILE, "a") as f:
                f.write(f"[{datetime.now()}] [{cat}] {msg}\n")
        except: pass

    # --- THREAD LOOPS ---
    def loop_status(self):
        while True:
            time.sleep(5)
            if self.server_pid:
                if logic.is_process_running(self.server_pid):
                    # Online
                    self.root.after(0, lambda: self.update_gui_for_state("ONLINE"))
                    self.root.after(0, lambda: self.pid_label.config(text=f"PID: {self.server_pid}"))
                    self.server_was_running = True
                else:
                    # Offline / Crashed
                    self.server_pid = None
                    self.root.after(0, lambda: self.update_gui_for_state("OFFLINE"))
                    self.root.after(0, lambda: self.pid_label.config(text="PID: -"))
                    
                    if self.server_was_running and not self.manual_shutdown_requested and not self.restart_requested:
                        self.crash_count += 1
                        self.root.after(0, lambda: self.crash_label.config(text=f"Crashes: {self.crash_count}", fg="red"))
                        self.log_manager_event("WATCHDOG", "Crash Detected.")
                        logic.send_discord_webhook(self.discord_webhook_url.get(), "CRASH", "Server Process Terminated Unexpectedly.", self.env_type=="TEST")
                        
                        if self.keep_alive_var.get():
                            self.root.after(0, lambda: self.start_server("WATCHDOG"))
                    
                    self.server_was_running = False
                    self.manual_shutdown_requested = False
                    self.restart_requested = False
            elif self.keep_alive_var.get() and self.server_was_running:
                 # Catch stuck state
                 self.root.after(0, lambda: self.start_server("WATCHDOG"))

    def loop_scheduler(self):
        while True:
            time.sleep(60)
            # Placeholder for future scheduler expansion
            pass

    def loop_updater(self):
        # 1. Check Manager Update
        try:
            req = urllib.request.Request(constants.GITHUB_API_URL, headers={'User-Agent': 'VeinManager'})
            with urllib.request.urlopen(req) as r:
                data = json.loads(r.read().decode())
                tag = data.get('tag_name')
                if tag and tag != constants.MANAGER_VERSION:
                    self.root.after(0, lambda: self.update_notify_btn.pack(side="left", padx=10))
                    self.root.after(0, lambda: self.update_notify_btn.config(text=f"⬇ Update Available! ({tag})"))
        except: pass
        time.sleep(3600) 

    def api_poller_loop(self):
        while True:
            time.sleep(10)
            pass

    def start_manual_backup(self):
        if not self.is_backing_up:
            self.create_backup_task()

    def create_backup_task(self, silent=False):
        self.is_backing_up = True
        self.create_backup_button.config(state='disabled', text="Backing up...")
        
        def _bak():
            fmt = self.backup_format_entry.get()
            ret = self.backup_retention_spinbox.get()
            logic.create_backup(self.path_entry.get(), fmt, ret)
            self.is_backing_up = False
            self.root.after(0, lambda: self.create_backup_button.config(state='normal', text="Create Backup"))
            if not silent: messagebox.showinfo("Backup", "Complete")
            
        threading.Thread(target=_bak, daemon=True).start()

    def start_steamcmd_update(self):
        self.notebook.select(5)
        self.steamcmd_console_output.config(state='normal')
        self.steamcmd_console_output.insert(tk.END, "Starting Update...\n")
        
        def _upd():
            logic.run_steamcmd(self.steamcmd_path_entry.get(), self.path_entry.get(), self.steam_branch_var.get(), 
                               lambda t: self.root.after(0, self.update_console, t))
            self.root.after(0, lambda: messagebox.showinfo("SteamCMD", "Finished."))
            
        threading.Thread(target=_upd, daemon=True).start()
    
    def start_steamcmd_validate(self):
        self.start_steamcmd_update() 

    def update_console(self, text):
        self.steamcmd_console_output.insert(tk.END, text)
        self.steamcmd_console_output.see(tk.END)

    def on_closing(self):
        self.save_manager_config()
        self.root.destroy()
        sys.exit(0)

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = ServerManager(root)
        root.mainloop()
    except Exception as e:
        log_crash(traceback.format_exc())