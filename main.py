# --- VERSION & IDENTITY ---
# MANAGER_VERSION = "v4.4.5 (Stable Release)"

# main.py
import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
import os
import sys
import ctypes
import traceback
import subprocess
import threading
import time
import json
import glob             
import urllib.request   
import webbrowser       
from datetime import datetime, timedelta

# --- SAFE IMPORTS ---
try:
    import constants
    import config
    import logger
    import logic
    import gui
except ImportError as e:
    ctypes.windll.user32.MessageBoxW(0, f"Critical Import Error: {e}", "Boot Failed", 0x10)
    sys.exit(1)
except Exception as e:
    ctypes.windll.user32.MessageBoxW(0, f"Boot Error: {e}", "Boot Failed", 0x10)
    sys.exit(1)

class ServerManager:
    def __init__(self, root):
        logger.debug("Initializing ServerManager UI...")
        self.root = root
        self.root.title(constants.APP_TITLE)
        if os.path.exists(constants.ICON_FILE):
            try: 
                self.root.iconbitmap(constants.ICON_FILE)
            except: 
                pass

        # VARIABLES
        self.server_pid = None
        self.is_checking_status = True
        self.manual_shutdown_requested = False
        self.restart_requested = False
        self.server_was_running = False
        self.is_backing_up = False
        self.is_save_active = False # Sentinel Flag
        self.crash_count = 0
        self.manager_update_available = False
        self.current_build_id = "Unknown"
        self.log_reader_active = False
        self.scheduler_warning_level = 0
        self.player_history = {} 
        self.vcmd = (self.root.register(self.validate_number_input), '%P')

        # CONFIG VARS
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
        self.admin_ids_var = tk.StringVar()
        self.profile_var = tk.StringVar()
        self.theme_var = tk.StringVar(value="Standard (Blue)")
        self.theme_codes = { "Standard (Blue)": "#3498db", "PvP (Orange)": "#e67e22", "Hardcore (Purple)": "#9b59b6", "Eco (Green)": "#2ecc71", "Test (Grey)": "#95a5a6" }
        self.wizard_install_path = tk.StringVar()
        self.wizard_steamcmd_path = tk.StringVar()
        self.wizard_is_import = False
        self.gameplay_vars = {} 
        self.menu_buttons = {}
        self.gameplay_frames = {}

        self.check_environment()
        
        # BOOT
        logger.debug("Loading Player History...")
        self.player_history = self.load_player_history()
        self.conf_parser = config.get_manager_config()
        geo = self.conf_parser.get('Manager', 'WindowGeometry', fallback='')
        if geo:
            try: 
                self.root.geometry(geo)
            except: 
                self.root.geometry("1100x750")
        else:
            self.root.geometry("1100x750")

        server_path = self.conf_parser.get('Manager', 'ServerPath', fallback='')
        
        if not server_path or not os.path.exists(server_path):
            logger.debug("Server Path missing, starting Wizard.")
            self.setup_wizard_ui()
        else:
            logger.debug("Server Path found, launching Dashboard.")
            self.launch_dashboard()

    def check_environment(self):
        self.env_type = "LIVE" 
        if "TEST" in os.path.basename(constants.APPLICATION_PATH).upper():
            self.env_type = "TEST"
        logger.debug(f"Environment Detected: {self.env_type}")

    def validate_number_input(self, P):
        return P == "" or P.isdigit()

    # --- WIZARD ---
    def setup_wizard_ui(self):
        self.wizard_frame = tk.Frame(self.root, padx=20, pady=20)
        self.wizard_frame.pack(fill='both', expand=True)
        self.wiz_step_frames = {}
        for i in range(1, 5): self.wiz_step_frames[i] = tk.Frame(self.wizard_frame)
        self.show_wizard_step(1)
    def show_wizard_step(self, n):
        for f in self.wiz_step_frames.values(): f.pack_forget()
        f = self.wiz_step_frames[n]; f.pack(fill='both', expand=True)
        for w in f.winfo_children(): w.destroy()
        if n==1: self.b_w1(f)
        elif n==2: self.b_w2(f)
        elif n==3: self.b_w3(f)
        elif n==4: self.b_w4(f)
    def b_w1(self,p):
        tk.Label(p,text="Welcome").pack(); tk.Entry(p,textvariable=self.wizard_install_path).pack()
        tk.Button(p,text="Next",command=lambda:self.show_wizard_step(2)).pack()
    def b_w2(self,p):
        tk.Label(p,text="SteamCMD").pack(); tk.Entry(p,textvariable=self.wizard_steamcmd_path).pack()
        tk.Button(p,text="Next",command=lambda:self.show_wizard_step(3)).pack()
    def b_w3(self,p):
        tk.Button(p,text="Download",command=self.wiz_finish).pack()
    def b_w4(self,p): pass
    def wiz_finish(self):
        self.conf_parser['Manager'] = {'ServerPath':self.wizard_install_path.get(),'SteamCMDPath':self.wizard_steamcmd_path.get()}
        config.save_manager_config(self.conf_parser)
        self.wizard_frame.destroy()
        self.launch_dashboard()

    # --- DASHBOARD ---
    def launch_dashboard(self):
        gui.create_main_layout(self)
        self.load_manager_config()
        self.apply_theme_selection(None)
        self.load_game_ini_settings()
        self.refresh_backup_list()
        self.refresh_profile_list()
        
        # Initial PID Search (Attach to existing)
        found_pid = logic.find_server_pid(self.path_entry.get())
        if found_pid:
            self.server_pid = found_pid
            self.append_to_log_viewer(f">> System: Attached to running server (PID: {found_pid})")
            self.update_gui_for_state("ONLINE")
            logger.debug(f"Attached to PID {found_pid}")
        
        # Start Threads using Logger Wrapper
        logger.start_safe_thread(self.loop_status, "StatusLoop")
        logger.start_safe_thread(self.loop_scheduler, "SchedulerLoop")
        logger.start_safe_thread(self.loop_updater, "UpdaterLoop")
        
        logic.check_prerequisites(self.path_entry.get(), self.steamcmd_path_entry.get(), self.append_to_log_viewer)

    # --- ACTIONS ---
    def disable_controls(self):
        self.stop_button.config(state="disabled")
        self.restart_button.config(state="disabled")

    def start_server(self, trigger="USER"):
        logger.event(trigger, "Start Requested.")
        server_path = self.path_entry.get()
        
        # Check if already running (Duplicate Prevention)
        existing_pid = logic.find_server_pid(server_path)
        if existing_pid:
            self.server_pid = existing_pid
            self.update_gui_for_state("ONLINE")
            messagebox.showinfo("Info", f"Server is already running (PID: {existing_pid}). Attached to it.")
            return

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
            logger.debug(f"Executing: {cmd}")
            proc = subprocess.Popen(cmd)
            self.server_pid = proc.pid
            self.update_gui_for_state("STARTING")
            logic.send_discord_webhook(self.discord_webhook_url.get(), "START", "Server Starting...", self.env_type=="TEST")
            if not self.log_reader_active:
                logger.start_safe_thread(self.loop_log_reader, "LogReader")
        except Exception as e: messagebox.showerror("Error", str(e))

    def stop_server(self):
        self.disable_controls() # LOCKDOWN
        self.manual_shutdown_requested = True
        logger.event("USER", "Stop Requested.")
        
        if self.backup_on_stop.get():
            self.stop_button.config(text="Backing up...")
            logger.start_safe_thread(self.shutdown_with_backup_sequence, "ShutdownBackup")
        else:
            self.update_gui_for_state("SHUTTING DOWN...")
            logger.start_safe_thread(self.shutdown_sequence, "Shutdown")

    def restart_server(self):
        self.disable_controls() # LOCKDOWN
        self.restart_requested = True
        logger.event("USER", "Restart Requested.")
        self.stop_server() 

    def shutdown_with_backup_sequence(self):
        # Run backup synchronously in this thread
        fmt = self.backup_format_entry.get()
        ret = self.backup_retention_spinbox.get()
        logic.create_backup(self.path_entry.get(), fmt, ret)
        self.root.after(0, self.refresh_backup_list)
        # Proceed to shutdown
        self.shutdown_sequence()

    def shutdown_sequence(self):
        # --- THE SAVE SENTINEL (Safety Check) ---
        timeout = 0
        max_timeout = 60 # wait max 60 seconds
        
        while timeout < max_timeout:
            # Check 1: Log Sentinel
            is_saving_log = self.is_save_active
            
            # Check 2: Disk I/O (Backup Sentinel)
            is_disk_busy = False
            if self.server_pid:
                is_disk_busy = logic.check_disk_activity(self.server_pid)
            
            if not is_saving_log and not is_disk_busy:
                break # Safe to kill
                
            # Log verbose info for user
            msg = f"⏳ SENTINEL: Waiting for Save... (Log: {is_saving_log} | Disk: {is_disk_busy}) - {timeout}s"
            self.root.after(0, lambda m=msg: self.append_to_log_viewer(m))
            time.sleep(1)
            timeout += 1

        if timeout >= max_timeout:
             self.root.after(0, lambda: self.append_to_log_viewer("⚠️ SENTINEL: Timeout reached. Forcing Shutdown."))
             logger.event("SENTINEL", "Force Shutdown due to Timeout.")

        # 1. Kill SPECIFIC Process ID
        if self.server_pid:
            logic.kill_server_by_pid(self.server_pid)

        # 4. Cleanup UI
        self.server_pid = None
        self.server_was_running = False # <--- CRITICAL FIX: Tell Loop we are done
        self.is_save_active = False 
        self.root.after(0, lambda: self.update_gui_for_state("OFFLINE"))
        self.root.after(0, lambda: self.pid_label.config(text="PID: -"))
        logic.send_discord_webhook(self.discord_webhook_url.get(), "STOP", "Server Stopped.", self.env_type=="TEST")
        
        # 5. Handle Restart if requested
        if self.restart_requested:
            self.root.after(3000, lambda: self.start_server("RESTART"))
            self.restart_requested = False
        else:
            # Explicitly reset flag if no restart
            self.manual_shutdown_requested = False

    def apply_theme_selection(self, event):
        selection = self.theme_var.get()
        color = self.theme_codes.get(selection, "#3498db")
        try: self.accent_line.config(bg=color)
        except: pass

    def reset_gameplay_to_vanilla(self):
        if self.server_pid is not None:
             messagebox.showwarning("Lockdown", "Cannot reset settings while server is running.")
             return
        if not messagebox.askyesno("Confirm Reset", "Are you sure?"): return
        for category, settings_list in constants.GAMEPLAY_DEFINITIONS.items():
            for (label, key, tooltip, type_str, file_type, section, default_val) in settings_list:
                if key in self.gameplay_vars:
                    data = self.gameplay_vars[key]
                    if type_str == "combo_scarcity": data['widget'].set("Standard (2.0)")
                    else: data['var'].set(default_val)
        messagebox.showinfo("Reset Complete", "Settings reverted. Click SAVE.")

    def refresh_profile_list(self):
        profs = logic.get_profile_list()
        self.profile_combobox['values'] = profs
        self.profile_combobox.update_idletasks()
        if profs and not self.profile_combobox.get():
            self.profile_combobox.current(0)
    
    # --- QUICK SAVE ---
    def update_active_profile(self):
        name = self.profile_var.get()
        if not name:
            messagebox.showwarning("Warning", "No active profile selected.\nUse 'Save As...' to create one first.")
            return

        if not messagebox.askyesno("Confirm Overwrite", f"Overwrite profile '{name}' with current settings?"):
            return

        self.save_all_settings(silent=True) 
        files = { 
            'Game': config.get_game_ini_path(self.path_entry.get()), 
            'Engine': config.get_engine_ini_path(self.path_entry.get()) 
        }
        success, msg = logic.save_profile(name, files)
        if success:
            messagebox.showinfo("Success", f"Profile '{name}' updated successfully.")
        else:
            messagebox.showerror("Error", msg)

    def save_new_profile(self):
        name = simpledialog.askstring("Save Profile", "Enter Profile Name:")
        if name:
            self.save_all_settings(silent=True) 
            files = { 'Game': config.get_game_ini_path(self.path_entry.get()), 'Engine': config.get_engine_ini_path(self.path_entry.get()) }
            success, msg = logic.save_profile(name, files)
            if success:
                messagebox.showinfo("Success", msg)
                self.refresh_profile_list()
                self.profile_var.set(name)
                self.save_all_settings(silent=True)
            else: messagebox.showerror("Error", msg)

    def load_selected_profile(self):
        # DO NOT CLEAR FIELDS HERE
        name = self.profile_var.get()
        if not name: return
        if self.server_pid:
            if not messagebox.askyesno("Warning", "Server will restart to apply profile. Continue?"): return
            self.stop_server()
            time.sleep(2)
        files = { 'Game': config.get_game_ini_path(self.path_entry.get()), 'Engine': config.get_engine_ini_path(self.path_entry.get()) }
        success, msg = logic.load_profile(name, files)
        if success:
            self.conf_parser = config.get_manager_config()
            self.load_manager_config()
            self.load_game_ini_settings()
            messagebox.showinfo("Success", msg)
            if self.server_pid is None and messagebox.askyesno("Loaded", "Start Server now?"):
                self.start_server("PROFILE_LOAD")
        else: messagebox.showerror("Error", msg)

    def delete_profile(self):
        name = self.profile_var.get()
        if not name: return
        if messagebox.askyesno("Delete", f"Delete profile '{name}'?"):
            try:
                import shutil
                shutil.rmtree(os.path.join(constants.PROFILES_DIR, name))
                self.refresh_profile_list()
                self.profile_var.set('')
            except: pass

    def run_doctor(self):
        self.diag_status_label.config(text="Running...", fg="blue"); self.root.update()
        pub_ip = logic.get_public_ip()
        p_game = self.port_entry.get(); p_query = self.query_port_entry.get()
        g_status = logic.check_port_open(p_game); q_status = logic.check_port_open(p_query)
        port_msg = ""
        if self.server_pid:
            if g_status and q_status: port_msg = "Ports Bound (OK)"
            else: port_msg = "Ports NOT Bound (Error!)"
        else:
            if not g_status and not q_status: port_msg = "Ports Free (OK)"
            else: port_msg = "Ports in use by another app!"
        fw = logic.check_firewall_rule()
        fw_msg = "Rule Found" if fw else "No Rule Found (Check Firewall)"
        self.diag_status_label.config(text="Done", fg="green")
        messagebox.showinfo("Health Check", f"Public IP: {pub_ip}\nStatus: {port_msg}\nFirewall: {fw_msg}")

    # --- IO HANDLERS ---
    def save_all_settings(self, silent=False):
        c = self.conf_parser
        c['Manager']['ServerPath'] = self.path_entry.get()
        c['Manager']['SteamCMDPath'] = self.steamcmd_path_entry.get()
        c['Manager']['KeepAlive'] = str(self.keep_alive_var.get())
        c['Manager']['Theme'] = self.theme_var.get()
        c['Manager']['ActiveProfile'] = self.profile_var.get()
        if 'Backups' not in c: c['Backups'] = {}
        c['Backups']['Reactive'] = str(self.reactive_backup_enabled.get())
        c['Backups']['OnStop'] = str(self.backup_on_stop.get())
        if 'Scheduler' not in c: c['Scheduler'] = {}
        c['Scheduler']['DailyEnabled'] = str(self.sched_daily_enabled.get())
        c['Scheduler']['IntervalEnabled'] = str(self.sched_interval_enabled.get())
        c['Scheduler']['Interval'] = self.sched_interval_entry.get()
        c['Scheduler']['Times'] = self.sched_time_entry.get()
        c['Scheduler']['Days'] = ",".join(["1" if v.get() else "0" for v in self.sched_days_vars])
        if 'Startup' not in c: c['Startup'] = {}
        c['Startup']['Map'] = self.map_combobox.get()
        c['Startup']['SessionName'] = self.session_name_entry.get()
        c['Startup']['Port'] = self.port_entry.get()
        c['Startup']['QueryPort'] = self.query_port_entry.get()
        c['Startup']['MaxPlayers'] = self.players_entry.get()
        c['Startup']['EnableHTTPAPI'] = str(self.http_api_enabled_var.get())
        c['Startup']['SuperAdminSteamIDs'] = self.admin_ids_var.get()
        if 'RCON' not in c: c['RCON'] = {}
        c['RCON']['Enabled'] = str(self.rcon_enabled_var.get())
        c['RCON']['Port'] = self.rcon_port_entry.get()
        c['RCON']['Password'] = self.rcon_password_entry.get()
        if 'Discord' not in c: c['Discord'] = {}
        c['Discord']['Enabled'] = str(self.discord_enabled.get())
        c['Discord']['WebhookURL'] = self.discord_webhook_url.get()
        c['Discord']['CommunityURL'] = self.community_url.get()
        if 'AutoUpdater' not in c: c['AutoUpdater'] = {}
        c['AutoUpdater']['Enabled'] = str(self.auto_update_enabled.get())
        c['AutoUpdater']['PassiveMode'] = str(self.auto_update_passive.get())
        c['AutoUpdater']['SteamBranch'] = self.steam_branch_var.get()
        config.save_manager_config(c)
        g_ini = config.load_game_ini(self.path_entry.get())
        gs = config.get_existing_section_name(g_ini, '/Script/Vein.VeinGameSession')
        ss = config.get_existing_section_name(g_ini, '/Script/Vein.ServerSettings')
        eng = config.get_existing_section_name(g_ini, '/Script/Engine.GameSession')
        if not g_ini.has_section(gs): g_ini.add_section(gs)
        if not g_ini.has_section(ss): g_ini.add_section(ss)
        if not g_ini.has_section(eng): g_ini.add_section(eng)
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
                elif data['type'] == 'bool': val = '1' if val else '0'
                engine_updates[key] = str(val)
        if self.players_entry.get(): engine_updates['vein.Characters.Max'] = self.players_entry.get()
        config.update_engine_ini_cvar(self.path_entry.get(), engine_updates)
        self.update_header_title()
        if not silent: messagebox.showinfo("Success", "Settings Saved")

    def load_manager_config(self):
        c = self.conf_parser
        self.path_entry.delete(0, tk.END); self.path_entry.insert(0, c.get('Manager', 'ServerPath', fallback=''))
        self.steamcmd_path_entry.delete(0, tk.END); self.steamcmd_path_entry.insert(0, c.get('Manager', 'SteamCMDPath', fallback=''))
        self.keep_alive_var.set(c.getboolean('Manager', 'KeepAlive', fallback=False))
        self.theme_var.set(c.get('Manager', 'Theme', fallback='Standard (Blue)'))
        self.profile_var.set(c.get('Manager', 'ActiveProfile', fallback=''))
        bak_fmt = c.get('Manager', 'BackupFormat', fallback="Server_Backup_%Y-%m-%d_%H-%M-%S")
        self.backup_format_entry.delete(0, tk.END); self.backup_format_entry.insert(0, bak_fmt)
        bak_ret = c.get('Manager', 'BackupRetention', fallback="20")
        try: 
            self.backup_retention_spinbox.delete(0, tk.END)
            self.backup_retention_spinbox.insert(0, bak_ret)
        except: pass
        if c.has_section('Backups'):
            self.reactive_backup_enabled.set(c.getboolean('Backups', 'Reactive', fallback=True))
            self.backup_on_stop.set(c.getboolean('Backups', 'OnStop', fallback=False))
        sch_times = c.get('Scheduler', 'Times', fallback="00:00, 04:00, 08:00, 12:00, 16:00, 20:00")
        self.sched_time_entry.delete(0, tk.END); self.sched_time_entry.insert(0, sch_times)
        if c.has_section('Scheduler'):
            self.sched_daily_enabled.set(c.getboolean('Scheduler', 'DailyEnabled', fallback=False))
            self.sched_interval_enabled.set(c.getboolean('Scheduler', 'IntervalEnabled', fallback=False))
            self.sched_interval_entry.delete(0, tk.END); self.sched_interval_entry.insert(0, c.get('Scheduler', 'Interval', fallback=''))
            days_str = c.get('Scheduler', 'Days', fallback="1,1,1,1,1,1,1")
            try:
                parts = days_str.split(',')
                for i in range(len(self.sched_days_vars)):
                    if i < len(parts): self.sched_days_vars[i].set(parts[i] == "1")
            except: pass
        self.map_combobox.set(c.get('Startup', 'Map', fallback='/Game/Vein/Maps/ChamplainValley?listen'))
        self.session_name_entry.delete(0, tk.END); self.session_name_entry.insert(0, c.get('Startup', 'SessionName', fallback='Server'))
        self.port_entry.delete(0, tk.END); self.port_entry.insert(0, c.get('Startup', 'Port', fallback='7779'))
        self.query_port_entry.delete(0, tk.END); self.query_port_entry.insert(0, c.get('Startup', 'QueryPort', fallback='27015'))
        self.players_entry.delete(0, tk.END); self.players_entry.insert(0, c.get('Startup', 'MaxPlayers', fallback='16'))
        self.http_api_enabled_var.set(c.getboolean('Startup', 'EnableHTTPAPI', fallback=False))
        if c.has_section('RCON'):
            self.rcon_enabled_var.set(c.getboolean('RCON', 'Enabled', fallback=False))
            self.rcon_port_entry.delete(0, tk.END); self.rcon_port_entry.insert(0, c.get('RCON', 'Port', fallback='27020'))
            self.rcon_password_entry.delete(0, tk.END); self.rcon_password_entry.insert(0, c.get('RCON', 'Password', fallback=''))
        if c.has_section('Discord'):
            self.discord_enabled.set(c.getboolean('Discord', 'Enabled', fallback=False))
            self.discord_webhook_url.set(c.get('Discord', 'WebhookURL', fallback=''))
            self.community_url.set(c.get('Discord', 'CommunityURL', fallback=constants.LINK_DISCORD_MAIN))
        if c.has_section('AutoUpdater'):
            self.auto_update_enabled.set(c.getboolean('AutoUpdater', 'Enabled', fallback=False))
            self.auto_update_passive.set(c.getboolean('AutoUpdater', 'PassiveMode', fallback=True))
            self.steam_branch_var.set(c.get('AutoUpdater', 'SteamBranch', fallback='public'))
        self.admin_ids_var.set(c.get('Startup', 'SuperAdminSteamIDs', fallback=''))

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
        eng_path = config.get_engine_ini_path(self.path_entry.get())
        cvar_data = config.load_engine_ini_raw(eng_path, list(self.gameplay_vars.keys()))
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
        is_running = state in ["ONLINE", "STARTING", "UPDATING"]
        s = "disabled" if is_running else "normal"
        self.start_button.config(state=s)
        self.save_button.config(state=s)
        
        # FIX: Ensure button text is reset
        self.stop_button.config(state="normal" if state == "ONLINE" else "disabled", text="Stop")
        self.restart_button.config(state="normal" if state == "ONLINE" else "disabled")
        
        widgets_to_lock = [self.path_entry, self.map_combobox, self.port_entry, self.players_entry, self.session_name_entry, self.server_name_entry, self.server_desc_entry, self.server_password_entry, self.query_port_entry, self.rcon_port_entry, self.rcon_password_entry, self.http_api_port_entry, self.admin_id_entry]
        for w in widgets_to_lock:
            try: w.config(state=s)
            except: pass
        for data in self.gameplay_vars.values():
             try: data['widget'].config(state=s if data['type'] != 'combo_scarcity' else ('readonly' if not is_running else 'disabled'))
             except: pass

    def append_to_log_viewer(self, text):
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, text + "\n") # Force newline for cleanliness
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')

    def open_logs_folder(self):
        if os.path.exists(constants.LOGS_ROOT_DIR): os.startfile(constants.LOGS_ROOT_DIR)

    def open_backup_folder(self):
        p = os.path.join(self.path_entry.get(), 'Backups')
        if os.path.exists(p): os.startfile(p)

    def refresh_backup_list(self):
        self.backup_list.delete(0, tk.END)
        path = os.path.join(self.path_entry.get(), 'Backups')
        if not os.path.exists(path): return
        files = glob.glob(os.path.join(path, "*.zip"))
        files.sort(key=os.path.getmtime, reverse=True)
        for f in files:
            name = os.path.basename(f)
            size_mb = os.path.getsize(f) / (1024*1024)
            self.backup_list.insert(tk.END, f"{name}  ({size_mb:.2f} MB)")

    def purge_manager_logs(self):
        if messagebox.askyesno("Confirm", "Clear logs?"):
            open(constants.EVENTS_LOG_FILE, 'w').close()

    def reset_crash_counter(self):
        self.crash_count = 0
        self.crash_label.config(text="Crashes: 0", fg="#555")

    def ban_selected_player(self):
        sel = self.players_listbox.curselection()
        if not sel: return
        text = self.players_listbox.get(sel[0])
        if "|" in text:
            parts = text.split("|")
            steamid = parts[1].strip()
            name = parts[0].strip()
            if messagebox.askyesno("BAN PLAYER", f"Ban {name} ({steamid})?"):
                if logic.ban_player_steamid(self.path_entry.get(), steamid):
                    messagebox.showinfo("Banned", "Player added to Ban List.")
                    self.refresh_ban_list()
                else: messagebox.showerror("Error", "Failed to write Game.ini")

    def unban_selected_input(self): pass 

    def refresh_ban_list(self):
        self.banned_list_text.delete('1.0', tk.END)
        bans = logic.get_banned_players(self.path_entry.get())
        for b in bans:
            self.banned_list_text.insert(tk.END, b + "\n")

    def load_player_history(self):
        if os.path.exists(constants.HISTORY_FILE):
            try: 
                with open(constants.HISTORY_FILE, 'r') as f: 
                    return json.load(f)
            except: 
                return {}
        return {}

    def save_player_history(self):
        try:
            with open(constants.HISTORY_FILE, 'w') as f:
                json.dump(self.player_history, f, indent=4)
        except: 
            pass

    def refresh_player_list_ui(self, current_online_names=None):
        mode = self.player_filter_var.get()
        self.players_listbox.delete(0, tk.END)
        if mode == "Online Now" and current_online_names:
            for n in current_online_names: self.players_listbox.insert(tk.END, f"• {n}")
        elif mode == "History (All Time)":
            for sid, data in self.player_history.items():
                name = data.get('name', 'Unknown')
                last = data.get('last_seen', '?')
                self.players_listbox.insert(tk.END, f"{name} | {sid} | {last}")

    def loop_log_reader(self):
        self.log_reader_active = True
        log_path = os.path.join(self.path_entry.get(), 'Vein', 'Saved', 'Logs', 'Vein.log')
        retries = 0
        while not os.path.exists(log_path) and retries < 10:
            time.sleep(1)
            retries += 1
        if not os.path.exists(log_path): 
            self.log_reader_active = False
            return
        try:
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                f.seek(0, 2) # Start at end
                while self.server_pid or self.server_was_running:
                    line = f.readline()
                    if line:
                        self.root.after(0, lambda l=line.strip(): self.append_to_log_viewer(l))
                        
                        # --- SENTINEL LOGIC ---
                        if constants.REGEX_SAVE_START in line:
                            self.is_save_active = True
                            self.root.after(0, lambda: self.append_to_log_viewer("🔒 SENTINEL: Auto-Save Started. Shutdown Locked."))
                        if constants.REGEX_SAVE_FINISH_A in line or constants.REGEX_SAVE_FINISH_B in line:
                            self.is_save_active = False
                            self.root.after(0, lambda: self.append_to_log_viewer("🔓 SENTINEL: Save Complete. Lock Released."))

                        data = logic.parse_log_line_for_analytics(line)
                        if data and 'steamid' in data:
                            sid = data['steamid']
                            name = data.get('name', 'Unknown')
                            if sid not in self.player_history:
                                self.player_history[sid] = {'name': name, 'first_seen': str(datetime.now())}
                            self.player_history[sid]['last_seen'] = str(datetime.now())
                            self.player_history[sid]['name'] = name 
                            self.save_player_history()
                    else: time.sleep(0.5)
        except: pass
        self.log_reader_active = False

    def loop_status(self):
        while True:
            time.sleep(5)
            if self.server_pid:
                if logic.is_process_running(self.server_pid):
                    self.root.after(0, lambda: self.update_gui_for_state("ONLINE"))
                    self.root.after(0, lambda: self.pid_label.config(text=f"PID: {self.server_pid}"))
                    self.server_was_running = True
                    if not self.log_reader_active:
                         logger.start_safe_thread(self.loop_log_reader, "LogReader")
                else:
                    self.server_pid = None
                    self.is_save_active = False # Reset on crash
                    self.root.after(0, lambda: self.update_gui_for_state("OFFLINE"))
                    
                    # --- CRASH HANDLER WITH MANUAL STOP CHECK ---
                    if self.server_was_running and not self.manual_shutdown_requested and not self.restart_requested:
                        self.crash_count += 1
                        logger.event("WATCHDOG", "Crash Detected.")
                        logic.send_discord_webhook(self.discord_webhook_url.get(), "CRASH", "Crash Detected.", self.env_type=="TEST")
                        if self.keep_alive_var.get():
                            self.root.after(0, lambda: self.start_server("WATCHDOG"))
                    
                    self.server_was_running = False
                    self.manual_shutdown_requested = False
                    self.restart_requested = False
            
            # --- ZOMBIE CHECK (Was running, now None, but KeepAlive wants it back) ---
            elif self.keep_alive_var.get() and self.server_was_running:
                 if not self.manual_shutdown_requested: # <--- FIX: Respect the Stop button
                     self.root.after(0, lambda: self.start_server("WATCHDOG"))

    def loop_scheduler(self):
        while True:
            time.sleep(10)
            if not self.sched_daily_enabled.get() or not self.server_pid: continue
            raw_times = self.sched_time_entry.get().split(',')
            target_times = []
            now = datetime.now()
            for t_str in raw_times:
                try:
                    parts = t_str.strip().split(':')
                    t = now.replace(hour=int(parts[0]), minute=int(parts[1]), second=0, microsecond=0)
                    if t < now: t += timedelta(days=1)
                    target_times.append(t)
                except: pass
            if not target_times: continue
            next_restart = min(target_times)
            diff = (next_restart - now).total_seconds()
            self.root.after(0, lambda d=diff: self.sched_status_label.config(text=f"Next Restart: {int(d//60)}m {int(d%60)}s"))
            
            # --- WARNINGS ---
            if diff <= 600 and diff > 300: 
                if self.scheduler_warning_level < 1:
                    logic.send_discord_webhook(self.discord_webhook_url.get(), "WARN", "Server restarting in 10 Minutes.", self.env_type=="TEST")
                    self.scheduler_warning_level = 1
            elif diff <= 300 and diff > 30: 
                if self.scheduler_warning_level < 2:
                    logic.send_discord_webhook(self.discord_webhook_url.get(), "WARN", "Server restarting in 5 Minutes. SAVE YOUR GAME!", self.env_type=="TEST")
                    self.scheduler_warning_level = 2
            
            # --- RESTART TRIGGER ---
            elif diff <= 30: 
                logger.event("SCHEDULER", "Restart Triggered.")
                self.scheduler_warning_level = 0
                self.root.after(0, self.restart_server)
                time.sleep(60) 
            
            # --- INTELLIGENT RESTART (PHASE 1) ---
            elif diff <= 1800 and diff > 300: # Between 30m and 5m remaining
                 pass 

    def loop_updater(self):
        try:
            req = urllib.request.Request(constants.GITHUB_API_URL, headers={'User-Agent': 'VeinManager'})
            with urllib.request.urlopen(req) as r:
                data = json.loads(r.read().decode())
                tag = data.get('tag_name') 
                if tag:
                    remote_ver = [int(x) for x in tag.replace('v','').split('.')]
                    local_str = constants.MANAGER_VERSION.split('(')[0].strip().replace('v','')
                    local_ver = [int(x) for x in local_str.split('.')]
                    
                    if remote_ver > local_ver:
                        self.root.after(0, lambda: self.update_notify_btn.config(text=f"⬇ Update Available! ({tag})", bg="orange"))
                    elif remote_ver < local_ver:
                         self.root.after(0, lambda: self.update_notify_btn.config(text=f"⚡ Dev Build ({tag})", bg="#3498db"))
                    else:
                        self.root.after(0, lambda: self.update_notify_btn.config(text="✔ Up to Date", bg="green"))
        except: 
            pass # Keep default text if offline
        time.sleep(3600) 

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
            self.root.after(0, self.refresh_backup_list) 
            if not silent: messagebox.showinfo("Backup", "Complete")
        logger.start_safe_thread(_bak, "ManualBackup")

    def start_steamcmd_update(self):
        self.notebook.select(5)
        self.steamcmd_console_output.config(state='normal')
        self.steamcmd_console_output.insert(tk.END, "Starting Update...\n")
        def _upd():
            logic.run_steamcmd(self.steamcmd_path_entry.get(), self.path_entry.get(), self.steam_branch_var.get(), 
                               lambda t: self.root.after(0, self.update_console, t), validate_files=False)
            self.root.after(0, lambda: messagebox.showinfo("SteamCMD", "Finished."))
        logger.start_safe_thread(_upd, "SteamCMDUpdate")
    
    def start_steamcmd_validate(self):
        self.notebook.select(5)
        self.steamcmd_console_output.config(state='normal')
        self.steamcmd_console_output.insert(tk.END, "Starting VALIDATE (This will take time)...\n")
        def _upd():
            logic.run_steamcmd(self.steamcmd_path_entry.get(), self.path_entry.get(), self.steam_branch_var.get(), 
                               lambda t: self.root.after(0, self.update_console, t), validate_files=True)
            self.root.after(0, lambda: messagebox.showinfo("SteamCMD", "Finished."))
        logger.start_safe_thread(_upd, "SteamCMDValidate")

    def update_console(self, text):
        self.steamcmd_console_output.insert(tk.END, text)
        self.steamcmd_console_output.see(tk.END)

    def on_closing(self):
        self.save_window_geometry()
        config.save_manager_config(self.conf_parser)
        self.root.destroy()
        sys.exit(0)

if __name__ == "__main__":
    logger.setup() # <--- HOOKS CRASH HANDLER
    # Removed global try/except block to allow hooks to work
    root = tk.Tk()
    app = ServerManager(root)
    root.mainloop()