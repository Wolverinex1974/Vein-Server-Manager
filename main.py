# --- VERSION & IDENTITY ---
# MANAGER_VERSION = "v5.1.4 (Integrity & Polish)"

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
import queue
import psutil 
import re
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
        self.manual_shutdown_requested = False
        self.restart_requested = False
        self.server_was_running = False
        self.is_backing_up = False
        self.is_save_active = False 
        self.crash_count = 0
        self.current_build_id = "Unknown"
        self.manager_update_available = False
        self.log_reader_active = False
        self.scheduler_last_warning_min = -1
        self.player_history = {}
        self.cached_public_ip = None
        self.online_sessions = {}
        
        self.vcmd = (self.root.register(self.validate_number_input), '%P')
        self.command_queue = queue.Queue()

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
        
        self.auto_start_server_var = tk.BooleanVar(value=False)
        self.boot_delay_var = tk.StringVar(value="30")
        self.discord_bot_token = tk.StringVar()
        self.discord_channel_id = tk.StringVar()
        self.ram_limit_var = tk.StringVar(value="0")
        self.auto_update_on_start_var = tk.BooleanVar(value=False)
        self.sched_warning_var = tk.StringVar(value="30, 10, 5, 1")

        self.gameplay_vars = {} 
        self.menu_buttons = {}
        self.gameplay_frames = {}
        self.selected_mod_filename = None

        self.check_environment()
        
        # BOOT
        logger.debug("Loading Player History...")
        self.player_history = self.load_player_history()
        self.conf_parser = config.get_manager_config()
        geo = self.conf_parser.get('Manager', 'WindowGeometry', fallback='')
        if geo:
            try: self.root.geometry(geo)
            except: self.root.geometry("1100x750")
        else:
            self.root.geometry("1100x750")

        server_path = self.conf_parser.get('Manager', 'ServerPath', fallback='')
        if not server_path or not os.path.exists(server_path):
            self.launch_dashboard()
        else:
            self.launch_dashboard()

    def check_environment(self):
        self.env_type = "LIVE" 
        if "TEST" in os.path.basename(constants.APPLICATION_PATH).upper():
            self.env_type = "TEST"
        logger.debug(f"Environment Detected: {self.env_type}")

    def validate_number_input(self, P):
        return P == "" or P.isdigit()

    # --- DASHBOARD ---
    def launch_dashboard(self):
        gui.create_main_layout(self)
        self.load_manager_config()
        self.apply_theme_selection(None)
        self.load_game_ini_settings()
        self.refresh_backup_list()
        self.refresh_profile_list()
        
        logic.ensure_mod_directory(self.path_entry.get())
        self.refresh_mod_list()
        self.refresh_mod_sections()

        found_pid = logic.find_server_pid(self.path_entry.get())
        if found_pid:
            self.server_pid = found_pid
            self.append_to_log_viewer(f">> System: Attached to running server (PID: {found_pid})")
            self.update_gui_for_state("ONLINE")
            if not self.log_reader_active:
                logger.start_safe_thread(self.loop_log_reader, "LogReader")
        else:
            if self.auto_start_server_var.get():
                logger.debug("Auto-Start Enabled. Triggering Boot Sequence.")
                threading.Thread(target=self.auto_boot_sequence, daemon=True).start()
        
        logger.start_safe_thread(self.loop_status, "StatusLoop")
        logger.start_safe_thread(self.loop_scheduler, "SchedulerLoop")
        logger.start_safe_thread(self.loop_updater, "UpdaterLoop")
        
        self.root.after(100, self.process_command_queue)
        logic.check_prerequisites(self.path_entry.get(), self.steamcmd_path_entry.get(), self.append_to_log_viewer)
        
        if self.discord_bot_token.get():
            self.init_discord_bot()

    def process_command_queue(self):
        try:
            while True:
                cmd = self.command_queue.get_nowait()
                
                # Determine Trigger Source
                trigger = "USER"
                if isinstance(cmd, str) and cmd == "START": 
                     # Only "START" is ambiguous (Watchdog vs Discord vs AutoStart)
                     # For now, default to DISCORD if it comes via queue without context
                     trigger = "DISCORD" 
                
                if cmd == "START": self.start_server("DISCORD")
                elif cmd == "STOP": self.stop_server()
                elif cmd == "RESTART": self.restart_server()
                elif cmd == "BACKUP": self.start_manual_backup()
        except queue.Empty:
            pass
        finally:
            self.root.after(200, self.process_command_queue)

    def init_discord_bot(self):
        callbacks = {
            'get_status': self.get_status_info, 
            'restart': lambda: self.command_queue.put("RESTART"),
            'start': lambda: self.command_queue.put("START"),
            'stop': lambda: self.command_queue.put("STOP"),
            'backup': lambda: self.command_queue.put("BACKUP")
        }
        logic.start_discord_bot(self.discord_bot_token.get(), self.discord_channel_id.get(), callbacks)

    def get_status_info(self):
        mem_usage = "0 MB"
        uptime = "N/A"
        if self.cached_public_ip is None: self.cached_public_ip = logic.get_public_ip()
            
        if self.server_pid:
            try:
                p = psutil.Process(self.server_pid)
                mem = p.memory_info().rss / (1024 * 1024)
                mem_usage = f"{mem:.1f} MB"
                create_time = datetime.fromtimestamp(p.create_time())
                uptime = str(datetime.now() - create_time).split('.')[0]
            except: pass
        
        return {
            'online': self.server_pid is not None, 
            'pid': self.server_pid or "None", 
            'ram': mem_usage, 
            'uptime': uptime, 
            'ip': self.cached_public_ip,
            'players': list(self.online_sessions.values())
        }

    def auto_boot_sequence(self):
        try: delay = int(self.boot_delay_var.get())
        except: delay = 30
        self.append_to_log_viewer(f">> System: Auto-Booting Server in {delay} seconds...")
        time.sleep(delay)
        if not self.server_pid: self.command_queue.put("START")

    def start_server(self, trigger="USER"):
        logger.event(trigger, "Start Requested.")
        server_path = self.path_entry.get()
        existing_pid = logic.find_server_pid(server_path)
        
        if existing_pid:
            self.server_pid = existing_pid
            self.update_gui_for_state("ONLINE")
            
            # --- CRITICAL FIX: NON-BLOCKING CHECK ---
            if trigger == "USER":
                messagebox.showinfo("Info", f"Server is already running (PID: {existing_pid}). Attached to it.")
            else:
                logger.debug(f"Start Request Ignored ({trigger}): Server is already running.")
            return

        exe = os.path.join(server_path, 'Vein', 'Binaries', 'Win64', constants.SERVER_EXECUTABLE)
        if not os.path.exists(exe):
            # Only show popup for manual clicks
            if trigger == "USER":
                if messagebox.askyesno("Server Missing", "Executable not found.\nGo to Management tab?"):
                    self.notebook.select(6)
            else:
                logger.debug(f"Start Failed ({trigger}): Executable not found.")
            return
            
        self.save_all_settings(silent=True)
        if self.auto_update_on_start_var.get() and trigger != "WATCHDOG":
            self.append_to_log_viewer(">> Update on Start Active: Checking for updates...")
            threading.Thread(target=self._update_then_launch, args=(trigger,), daemon=True).start()
            return
        self._spawn_server_process()

    def _update_then_launch(self, trigger):
        self.root.after(0, lambda: self.update_gui_for_state("UPDATING"))
        def update_cb(text): pass
        success = logic.run_steamcmd(self.steamcmd_path_entry.get(), self.path_entry.get(), self.steam_branch_var.get(), update_cb, validate_files=False)
        if success:
            self.root.after(0, lambda: self.append_to_log_viewer(">> Update Complete. Launching..."))
            self.root.after(1000, self._spawn_server_process)
        else:
            self.root.after(0, lambda: self.append_to_log_viewer(">> Update Failed (or Timed Out)! Launching anyway..."))
            self.root.after(1000, self._spawn_server_process)

    def _spawn_server_process(self):
        server_path = self.path_entry.get()
        exe = os.path.join(server_path, 'Vein', 'Binaries', 'Win64', constants.SERVER_EXECUTABLE)
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
            self.server_was_running = True 
            self.update_gui_for_state("STARTING")
            logic.send_discord_webhook(self.discord_webhook_url.get(), "START", "Server Starting...", self.env_type=="TEST")
            if not self.log_reader_active:
                logger.start_safe_thread(self.loop_log_reader, "LogReader")
        except Exception as e: messagebox.showerror("Error", str(e))

    def stop_server(self):
        self.disable_controls()
        self.manual_shutdown_requested = True
        logger.event("USER", "Stop Requested.")
        if self.backup_on_stop.get():
            self.stop_button.config(text="Backing up...")
            logger.start_safe_thread(self.shutdown_with_backup_sequence, "ShutdownBackup")
        else:
            self.update_gui_for_state("SHUTTING DOWN...")
            logger.start_safe_thread(self.shutdown_sequence, "Shutdown")

    def restart_server(self):
        self.disable_controls()
        self.restart_requested = True
        logger.event("USER", "Restart Requested.")
        self.stop_server() 

    def disable_controls(self):
        """Fix for AttributeError: Locks UI during state transitions."""
        self.start_button.config(state="disabled")
        self.stop_button.config(state="disabled")
        self.restart_button.config(state="disabled")
        try: self.btn_steam_upd.config(state="disabled")
        except: pass
        try: self.btn_steam_val.config(state="disabled")
        except: pass

    def shutdown_with_backup_sequence(self):
        fmt = self.backup_format_entry.get()
        ret = self.backup_retention_spinbox.get()
        logic.create_backup(self.path_entry.get(), fmt, ret)
        self.root.after(0, self.refresh_backup_list)
        self.shutdown_sequence()

    def shutdown_sequence(self):
        timeout = 0
        max_timeout = 60
        while timeout < max_timeout:
            is_saving_log = self.is_save_active
            is_disk_busy = False
            if self.server_pid:
                is_disk_busy = logic.check_disk_activity(self.server_pid)
            if not is_saving_log and not is_disk_busy:
                break 
            msg = f"⏳ SENTINEL: Waiting for Save... (Log: {is_saving_log} | Disk: {is_disk_busy}) - {timeout}s"
            self.root.after(0, lambda m=msg: self.append_to_log_viewer(m))
            time.sleep(1)
            timeout += 1

        if timeout >= max_timeout:
             self.root.after(0, lambda: self.append_to_log_viewer("⚠️ SENTINEL: Timeout reached. Forcing Shutdown."))
             logger.event("SENTINEL", "Force Shutdown due to Timeout.")

        if self.server_pid: logic.kill_server_by_pid(self.server_pid)

        self.server_pid = None
        self.server_was_running = False 
        self.is_save_active = False 
        self.online_sessions.clear() 
        self.root.after(0, self.refresh_player_list_ui)
        
        # --- VISUAL POLISH (v5.1.4): Show Orange RESTARTING status ---
        if self.restart_requested:
             self.root.after(0, lambda: self.update_gui_for_state("RESTARTING"))
        else:
             self.root.after(0, lambda: self.update_gui_for_state("OFFLINE"))
             
        self.root.after(0, lambda: self.pid_label.config(text="PID: -")) 
        logic.send_discord_webhook(self.discord_webhook_url.get(), "STOP", "Server Stopped.", self.env_type=="TEST")
        
        if self.restart_requested:
            self.root.after(0, lambda: self.append_to_log_viewer("⏳ Restart: Waiting 10s for clean shutdown..."))
            self.root.after(10000, lambda: self.start_server("RESTART"))
            self.restart_requested = False
        else:
            self.manual_shutdown_requested = False

    def loop_log_reader(self):
        self.log_reader_active = True
        log_path = os.path.join(self.path_entry.get(), 'Vein', 'Saved', 'Logs', 'Vein.log')
        log_parser = None
        if self.discord_enabled.get():
            log_parser = logic.LogParser(self.discord_webhook_url.get())

        while self.server_pid or self.server_was_running:
            if not os.path.exists(log_path):
                time.sleep(3)
                continue 
            try:
                with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
                    f.seek(0, 0)
                    while self.server_pid or self.server_was_running:
                        line = f.readline()
                        if line:
                            clean_line = line.strip()
                            
                            current_filter = self.log_filter_var.get().lower()
                            if not current_filter or current_filter in clean_line.lower():
                                self.root.after(0, lambda l=clean_line: self.append_to_log_viewer(l))
                            
                            if log_parser: log_parser.process_line(clean_line)

                            if constants.REGEX_SAVE_START in line:
                                self.is_save_active = True
                                self.root.after(0, lambda: self.append_to_log_viewer("🔒 SENTINEL: Auto-Save Started."))
                            if constants.REGEX_SAVE_FINISH_A in line or constants.REGEX_SAVE_FINISH_B in line:
                                self.is_save_active = False
                                self.root.after(0, lambda: self.append_to_log_viewer("🔓 SENTINEL: Save Complete."))
                            
                            # --- PLAYER TRACKING ---
                            join_match = re.search(constants.REGEX_PLAYER_JOIN, line)
                            if join_match:
                                p_name = join_match.group(1)
                                p_id = join_match.group(2)
                                if p_id not in self.online_sessions:
                                    self.online_sessions[p_id] = p_name
                                    self.root.after(0, self.refresh_player_list_ui)
                                    # Update History
                                    if p_id not in self.player_history:
                                        self.player_history[p_id] = {'name': p_name, 'first_seen': str(datetime.now())}
                                    self.player_history[p_id]['last_seen'] = str(datetime.now())
                                    self.player_history[p_id]['name'] = p_name
                                    self.save_player_history()
                                    
                                    if log_parser:
                                        log_parser.send_join_leave_webhook(p_name, "JOIN", len(self.online_sessions))

                            leave_match = re.search(constants.REGEX_PLAYER_LEAVE, line)
                            if leave_match:
                                p_id = leave_match.group(1)
                                if p_id in self.online_sessions:
                                    p_name = self.online_sessions[p_id]
                                    del self.online_sessions[p_id]
                                    self.root.after(0, self.refresh_player_list_ui)
                                    if log_parser:
                                        log_parser.send_join_leave_webhook(p_name, "LEAVE", len(self.online_sessions))
                        else: 
                            time.sleep(0.5)
                            if not os.path.exists(log_path): break
            except Exception as e:
                time.sleep(1)
        self.log_reader_active = False

    def append_to_log_viewer(self, text):
        try:
            filter_txt = self.log_filter_var.get().lower()
            if filter_txt and filter_txt not in text.lower(): return
            self.log_text.config(state='normal')
            matched_tag = None
            for key in constants.LOG_HIGHLIGHTS.keys():
                if key in text:
                    matched_tag = key
                    break
            if matched_tag:
                self.log_text.insert(tk.END, text + "\n", matched_tag)
            else:
                self.log_text.insert(tk.END, text + "\n")
            self.log_text.see(tk.END)
            self.log_text.config(state='disabled')
        except: pass

    def apply_log_filter(self):
        filter_txt = self.log_filter_var.get().lower().strip()
        log_path = os.path.join(self.path_entry.get(), 'Vein', 'Saved', 'Logs', 'Vein.log')
        if not os.path.exists(log_path): return
        self.log_text.config(state='normal')
        self.log_text.delete('1.0', tk.END)
        try:
            with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
                for line in f:
                    clean = line.strip()
                    if not filter_txt or filter_txt in clean.lower():
                        matched_tag = None
                        for key in constants.LOG_HIGHLIGHTS.keys():
                            if key in clean:
                                matched_tag = key
                                break
                        if matched_tag:
                            self.log_text.insert(tk.END, clean + "\n", matched_tag)
                        else:
                            self.log_text.insert(tk.END, clean + "\n")
        except:
            self.log_text.insert(tk.END, "Error reading log file.\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')

    def refresh_mod_list(self):
        try:
            self.mod_listbox.delete(0, tk.END)
            mods = logic.scan_installed_mods(self.path_entry.get())
            for m in mods:
                color = "#006400" if m['status'] == 'Active' else "#808080"
                self.mod_listbox.insert(tk.END, m['name'])
                self.mod_listbox.itemconfig(tk.END, {'fg': color})
            self.selected_mod_filename = None
            self.btn_mod_toggle.config(state="disabled")
            self.btn_mod_del.config(state="disabled")
        except: pass

    def on_mod_selected(self):
        sel = self.mod_listbox.curselection()
        if not sel: return
        name = self.mod_listbox.get(sel[0])
        mods = logic.scan_installed_mods(self.path_entry.get())
        for m in mods:
            if m['name'] == name:
                self.selected_mod_filename = m['file']
                self.btn_mod_toggle.config(state="normal")
                self.btn_mod_del.config(state="normal")
                break

    def install_mod_dialog(self):
        files = filedialog.askopenfilenames(filetypes=[("Unreal Pak", "*.pak")])
        if files:
            count = 0
            for f in files:
                if logic.install_mod_file(self.path_entry.get(), f): count += 1
            self.refresh_mod_list()
            messagebox.showinfo("Install", f"Installed {count} mods.")

    def toggle_selected_mod(self):
        if self.selected_mod_filename:
            logic.toggle_mod_state(self.path_entry.get(), self.selected_mod_filename)
            self.refresh_mod_list()

    def delete_selected_mod(self):
        if self.selected_mod_filename:
            if messagebox.askyesno("Delete", f"Delete {self.selected_mod_filename}?"):
                logic.delete_mod_file(self.path_entry.get(), self.selected_mod_filename)
                self.refresh_mod_list()

    def refresh_mod_sections(self):
        secs = config.get_modifiable_sections(self.path_entry.get())
        self.mod_sec_combo['values'] = secs
        if secs: self.mod_sec_combo.current(0)

    def load_mod_section_data(self):
        section = self.mod_sec_var.get()
        if not section: return
        for w in self.mod_editor_inner.winfo_children(): w.destroy()
        self.mod_kv_entries = []
        data = config.read_mod_config_section(self.path_entry.get(), section)
        row = 0
        for key, val in data:
            self._add_kv_row(row, key, val)
            row += 1
        self._add_kv_row(row, "", "")

    def _add_kv_row(self, row, k_val, v_val):
        f = tk.Frame(self.mod_editor_inner)
        f.pack(fill='x', pady=2)
        k_entry = tk.Entry(f, width=25)
        k_entry.insert(0, k_val)
        k_entry.pack(side='left')
        tk.Label(f, text="=").pack(side='left')
        v_entry = tk.Entry(f, width=25)
        v_entry.insert(0, v_val)
        v_entry.pack(side='left', fill='x', expand=True)
        self.mod_kv_entries.append((k_entry, v_entry))

    def save_mod_section_data(self):
        section = self.mod_sec_var.get()
        if not section: return
        data_to_write = []
        for k_ent, v_ent in self.mod_kv_entries:
            k = k_ent.get().strip()
            v = v_ent.get().strip()
            if k: data_to_write.append((k, v))
        if config.write_mod_config_section(self.path_entry.get(), section, data_to_write):
            messagebox.showinfo("Success", f"Updated section [{section}]")
        else: messagebox.showerror("Error", "Failed to write config.")

    # --- UI HELPERS ---
    def browse_path(self):
        d = filedialog.askdirectory()
        if d: 
            self.path_entry.delete(0, tk.END); self.path_entry.insert(0, d)
            logic.check_prerequisites(d, self.steamcmd_path_entry.get(), self.append_to_log_viewer)
            logic.ensure_mod_directory(d)
            self.refresh_mod_list()
            self.refresh_mod_sections()
            self.load_game_ini_settings()

    def browse_steamcmd(self):
        f = filedialog.askopenfilename(filetypes=[("Executable", "*.exe")])
        if f: self.steamcmd_path_entry.delete(0, tk.END); self.steamcmd_path_entry.insert(0, f)

    def update_header_title(self):
        self.header_title_label.config(text=self.server_name_entry.get() or "Vein Server")

    def update_gui_for_state(self, state):
        self.status_text_label.config(text=f"Status: {state}", fg="green" if state == "ONLINE" else ("#FFA500" if state == "RESTARTING" else "red"))
        try: 
            if state == "RESTARTING":
                self.status_canvas.itemconfig(self.status_dot, fill="#FFA500") # Orange
            else:
                self.status_canvas.itemconfig(self.status_dot, fill="green" if state == "ONLINE" else "red")
        except: pass
        is_running = state in ["ONLINE", "STARTING", "UPDATING"]
        s = "disabled" if is_running else "normal"
        self.start_button.config(state=s)
        self.save_button.config(state=s)
        self.stop_button.config(state="normal" if state == "ONLINE" else "disabled", text="Stop")
        self.restart_button.config(state="normal" if state == "ONLINE" else "disabled")
        
        self.btn_mod_install.config(state=s)
        if is_running:
            self.btn_mod_toggle.config(state="disabled")
            self.btn_mod_del.config(state="disabled")
        else:
            if self.selected_mod_filename:
                self.btn_mod_toggle.config(state="normal")
                self.btn_mod_del.config(state="normal")

        widgets_to_lock = [self.path_entry, self.map_combobox, self.port_entry, self.players_entry, self.session_name_entry, self.server_name_entry, self.server_desc_entry, self.server_password_entry, self.query_port_entry, self.rcon_port_entry, self.rcon_password_entry, self.http_api_port_entry, self.admin_id_entry]
        for w in widgets_to_lock:
            try: w.config(state=s)
            except: pass
        for data in self.gameplay_vars.values():
             try: data['widget'].config(state=s if data['type'] != 'combo_scarcity' else ('readonly' if not is_running else 'disabled'))
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

    def apply_theme_selection(self, event):
        selection = self.theme_var.get()
        color = self.theme_codes.get(selection, "#3498db")
        try: self.accent_line.config(bg=color)
        except: pass

    def refresh_profile_list(self):
        profs = logic.get_profile_list()
        self.profile_combobox['values'] = profs
        self.profile_combobox.update_idletasks()
        if profs and not self.profile_combobox.get():
            self.profile_combobox.current(0)
    
    def update_active_profile(self):
        name = self.profile_var.get()
        if not name:
            messagebox.showwarning("Warning", "No active profile selected.")
            return
        if not messagebox.askyesno("Confirm Overwrite", f"Overwrite profile '{name}'?"): return
        self.save_all_settings(silent=True) 
        files = { 'Game': config.get_game_ini_path(self.path_entry.get()), 'Engine': config.get_engine_ini_path(self.path_entry.get()) }
        success, msg = logic.save_profile(name, files)
        if success: messagebox.showinfo("Success", f"Profile '{name}' updated.")
        else: messagebox.showerror("Error", msg)

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
        self.diag_btn.config(text="Running...", state="disabled")
        self.root.update()
        def _diag_thread():
            pub_ip = logic.get_public_ip()
            p_game = self.port_entry.get()
            is_listening = logic.check_port_listening(p_game)
            is_fw_ok = logic.check_firewall_fuzzy()
            self.root.after(0, lambda: self._update_doctor_ui(pub_ip, is_listening, is_fw_ok))
        logger.start_safe_thread(_diag_thread, "Diagnostics")

    def _update_doctor_ui(self, pub_ip, is_listening, is_fw_ok):
        self.diag_btn.config(text="Run Health Check", state="normal")
        if is_listening: self.diag_port_label.config(text=f"Game Port: ACTIVE (Server is Online)", fg="green")
        else:
             if self.server_pid: self.diag_port_label.config(text=f"Game Port: BLOCKED/SILENT (Server Running but not listening?)", fg="red")
             else: self.diag_port_label.config(text=f"Game Port: AVAILABLE (Ready to start)", fg="blue")
        if is_fw_ok: self.diag_fw_label.config(text=f"Firewall: 'Vein' Rule Found (OK)", fg="green")
        else: self.diag_fw_label.config(text=f"Firewall: No 'Vein' Rule Found! (Players may not connect)", fg="red")
        messagebox.showinfo("Health Check", f"Public IP: {pub_ip}\n\nCheck the Diagnostics panel for details.")

    # --- IO HANDLERS ---
    def save_all_settings(self, silent=False):
        c = self.conf_parser
        if 'AutoStart' not in c: c['AutoStart'] = {}       
        c['Manager']['ServerPath'] = self.path_entry.get()
        c['Manager']['SteamCMDPath'] = self.steamcmd_path_entry.get()
        c['Manager']['KeepAlive'] = str(self.keep_alive_var.get())
        c['Manager']['Theme'] = self.theme_var.get()
        c['Manager']['ActiveProfile'] = self.profile_var.get()
        
        if 'AutoStart' not in c: c['AutoStart'] = {}
        c['AutoStart']['Enabled'] = str(self.auto_start_server_var.get())
        c['AutoStart']['Delay'] = self.boot_delay_var.get()
        
        if 'Backups' not in c: c['Backups'] = {}
        c['Backups']['Reactive'] = str(self.reactive_backup_enabled.get())
        c['Backups']['OnStop'] = str(self.backup_on_stop.get())
        
        if 'Scheduler' not in c: c['Scheduler'] = {}
        c['Scheduler']['DailyEnabled'] = str(self.sched_daily_enabled.get())
        c['Scheduler']['IntervalEnabled'] = str(self.sched_interval_enabled.get())
        c['Scheduler']['Interval'] = self.sched_interval_entry.get()
        c['Scheduler']['Times'] = self.sched_time_entry.get()
        c['Scheduler']['Days'] = ",".join(["1" if v.get() else "0" for v in self.sched_days_vars])
        c['Scheduler']['RamLimit'] = self.ram_limit_var.get() 
        c['Scheduler']['Warnings'] = self.sched_warning_var.get()

        if 'Startup' not in c: c['Startup'] = {}
        c['Startup']['Map'] = self.map_combobox.get()
        c['Startup']['SessionName'] = self.session_name_entry.get()
        c['Startup']['Port'] = self.port_entry.get()
        c['Startup']['QueryPort'] = self.query_port_entry.get()
        c['Startup']['MaxPlayers'] = self.players_entry.get()
        c['Startup']['EnableHTTPAPI'] = str(self.http_api_enabled_var.get())
        
        if 'RCON' not in c: c['RCON'] = {}
        c['RCON']['Enabled'] = str(self.rcon_enabled_var.get())
        c['RCON']['Port'] = self.rcon_port_entry.get()
        c['RCON']['Password'] = self.rcon_password_entry.get()
        if 'Discord' not in c: c['Discord'] = {}
        c['Discord']['Enabled'] = str(self.discord_enabled.get())
        c['Discord']['WebhookURL'] = self.discord_webhook_url.get()
        c['Discord']['CommunityURL'] = self.community_url.get()
        c['Discord']['BotToken'] = self.discord_bot_token.get()
        c['Discord']['ChannelID'] = self.discord_channel_id.get()
        
        if 'AutoUpdater' not in c: c['AutoUpdater'] = {}
        c['AutoUpdater']['Enabled'] = str(self.auto_update_enabled.get())
        c['AutoUpdater']['PassiveMode'] = str(self.auto_update_passive.get())
        c['AutoUpdater']['SteamBranch'] = self.steam_branch_var.get()
        c['AutoUpdater']['UpdateOnStart'] = str(self.auto_update_on_start_var.get())

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
        
        if self.http_api_enabled_var.get(): g_ini.set(gs, 'HTTPPort', self.http_api_port_entry.get())
        for key, data in self.gameplay_vars.items():
            if data['file'] == 'Game':
                sec = config.get_existing_section_name(g_ini, data['section'])
                if not g_ini.has_section(sec): g_ini.add_section(sec)
                val = data['var'].get()
                if data['type'] == 'bool': val = "True" if val else "False"
                g_ini.set(sec, key, str(val))
        config.save_game_ini(self.path_entry.get(), g_ini)
        
        raw_admins = self.admin_ids_var.get()
        if raw_admins:
            admin_list = [x.strip() for x in raw_admins.split(',') if x.strip()]
            config.save_game_ini_array(self.path_entry.get(), gs, 'SuperAdminSteamIDs', admin_list)

        engine_updates = {}
        for key, data in self.gameplay_vars.items():
            if data['file'] == 'Engine':
                val = data['var'].get()
                if data['type'] == 'combo_scarcity':
                    raw = data['widget'].get()
                    if "(" in raw: val = raw.split("(")[1].replace(")", "")
                elif data['type'] == 'bool': val = '1' if val else '0'
                engine_updates[key] = str(val)
        
        # --- FIXED "DrkShrk" BUG (v5.1.4): Removed the line that overwrites MaxCharacters with MaxPlayers ---
        
        config.update_engine_ini_cvar(self.path_entry.get(), engine_updates)
        self.update_header_title()
        self.refresh_mod_sections() # Updates dropdown if user manually edited files
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
        
        if c.has_section('AutoStart'):
            self.auto_start_server_var.set(c.getboolean('AutoStart', 'Enabled', fallback=False))
            self.boot_delay_var.set(c.get('AutoStart', 'Delay', fallback='30'))

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
            self.ram_limit_var.set(c.get('Scheduler', 'RamLimit', fallback='0'))
            self.sched_warning_var.set(c.get('Scheduler', 'Warnings', fallback='30, 10, 5, 1'))

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
            self.discord_bot_token.set(c.get('Discord', 'BotToken', fallback=''))
            self.discord_channel_id.set(c.get('Discord', 'ChannelID', fallback=''))

        if c.has_section('AutoUpdater'):
            self.auto_update_enabled.set(c.getboolean('AutoUpdater', 'Enabled', fallback=False))
            self.auto_update_passive.set(c.getboolean('AutoUpdater', 'PassiveMode', fallback=True))
            self.steam_branch_var.set(c.get('AutoUpdater', 'SteamBranch', fallback='public'))
            self.auto_update_on_start_var.set(c.getboolean('AutoUpdater', 'UpdateOnStart', fallback=False))
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

    def refresh_ban_list(self):
        self.banned_list_text.delete('1.0', tk.END)
        bans = logic.get_banned_players(self.path_entry.get())
        for b in bans:
            self.banned_list_text.insert(tk.END, b + "\n")

    def load_player_history(self):
        if os.path.exists(constants.HISTORY_FILE):
            try: 
                with open(constants.HISTORY_FILE, 'r') as f: return json.load(f)
            except: return {}
        return {}

    def save_player_history(self):
        try:
            with open(constants.HISTORY_FILE, 'w') as f: json.dump(self.player_history, f, indent=4)
        except: pass

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
    def start_steamcmd_update(self):
        self.notebook.select(6)
        self.steamcmd_console_output.config(state='normal')
        self.steamcmd_console_output.insert(tk.END, "Starting Update...\n")
        def _upd():
            logic.run_steamcmd(self.steamcmd_path_entry.get(), self.path_entry.get(), self.steam_branch_var.get(), 
                               lambda t: self.root.after(0, self.update_console, t), validate_files=False)
            self.root.after(0, lambda: messagebox.showinfo("SteamCMD", "Finished."))
        logger.start_safe_thread(_upd, "SteamCMDUpdate")
    
    def start_steamcmd_validate(self):
        self.notebook.select(6)
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
   # --- LOOPS & IO (CONT) ---
    def loop_status(self):
        while True:
            time.sleep(5)
            if self.server_pid:
                if logic.is_process_running(self.server_pid):
                    self.root.after(0, lambda: self.update_gui_for_state("ONLINE"))
                    self.root.after(0, lambda: self.pid_label.config(text=f"PID: {self.server_pid}"))
                    
                    # --- UI UPDATE: PLAYER COUNT (v5.1.4) ---
                    try:
                        count = len(self.online_sessions)
                        max_p = self.players_entry.get() or "?"
                        self.player_count_label.config(text=f"Players: {count}/{max_p}")
                    except: pass
                    
                    try:
                        mem_limit_str = self.ram_limit_var.get()
                        if mem_limit_str and mem_limit_str.isdigit():
                            limit_gb = int(mem_limit_str)
                            if limit_gb > 0:
                                mem_mb = logic.get_process_memory_mb(self.server_pid)
                                limit_mb = limit_gb * 1024
                                if mem_mb > limit_mb:
                                    logger.event("RESOURCE", f"Memory Limit Exceeded: {int(mem_mb)}MB")
                                    logic.send_discord_webhook(self.discord_webhook_url.get(), "WARN", f"⚠️ High RAM. Restarting...", self.env_type=="TEST")
                                    self.command_queue.put("RESTART")
                                    time.sleep(10)
                    except: pass
                    
                    self.server_was_running = True
                    if not self.log_reader_active:
                         logger.start_safe_thread(self.loop_log_reader, "LogReader")
                else:
                    self.server_pid = None
                    self.is_save_active = False 
                    self.root.after(0, lambda: self.update_gui_for_state("OFFLINE"))
                    self.root.after(0, lambda: self.pid_label.config(text="PID: -")) 
                    
                    if self.server_was_running and not self.manual_shutdown_requested and not self.restart_requested:
                        self.crash_count += 1
                        logger.event("WATCHDOG", "Crash Detected.")
                        logic.send_discord_webhook(self.discord_webhook_url.get(), "CRASH", "Crash Detected.", self.env_type=="TEST")
                        if self.keep_alive_var.get():
                            self.command_queue.put("START")
                    
                    self.server_was_running = False
            
            elif self.keep_alive_var.get() and self.server_was_running:
                 if not self.manual_shutdown_requested: 
                     self.command_queue.put("START")

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
            diff_seconds = (next_restart - now).total_seconds()
            diff_min = int(diff_seconds / 60)
            self.root.after(0, lambda d=diff_seconds: self.sched_status_label.config(text=f"Next Restart: {int(d//60)}m {int(d%60)}s"))
            try:
                warn_str = self.sched_warning_var.get()
                warnings = [int(x.strip()) for x in warn_str.split(',') if x.strip().isdigit()]
            except: warnings = [30, 10, 5, 1]
            if diff_min in warnings and diff_min != self.scheduler_last_warning_min:
                logic.send_discord_webhook(self.discord_webhook_url.get(), "WARN", f"Server restarting in {diff_min} Minutes.", self.env_type=="TEST")
                self.scheduler_last_warning_min = diff_min
            elif diff_seconds <= 30: 
                logger.event("SCHEDULER", "Restart Triggered.")
                self.scheduler_last_warning_min = -1
                self.command_queue.put("RESTART")
                time.sleep(60) 
            elif diff_min > max(warnings):
                self.scheduler_last_warning_min = -1

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
        except: pass 
        time.sleep(3600) 

    def on_closing(self):
        config.save_manager_config(self.conf_parser)
        self.root.destroy()
        sys.exit(0)

if __name__ == "__main__":
    logger.setup() 
    root = tk.Tk()
    app = ServerManager(root)
    root.mainloop()