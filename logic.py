# --- VERSION & IDENTITY ---
# MANAGER_VERSION = "v5.1.4 (Integrity & Polish)"

# logic.py
import os
import sys
import subprocess
import shutil
import tempfile
import json
import urllib.request
import threading
import glob
import psutil
import time
import zipfile
import re
import socket
import hashlib
import asyncio
from datetime import datetime
import constants
import config
import logger 
from steam.client import SteamClient

# --- DISCORD LIBRARY SAFE IMPORT ---
try:
    import discord
    from discord.ext import tasks
    DISCORD_LIB_AVAILABLE = True
except ImportError:
    DISCORD_LIB_AVAILABLE = False

# --- DISCORD BOT CLASS ---
if DISCORD_LIB_AVAILABLE:
    class VeinDiscordBot(discord.Client):
        def __init__(self, callbacks, channel_id, *args, **kwargs):
            intents = discord.Intents.default()
            intents.message_content = True
            super().__init__(intents=intents, *args, **kwargs)
            self.callbacks = callbacks
            self.target_channel_id = int(channel_id) if channel_id and channel_id.isdigit() else 0
            self.live_status_msg_id = None
            self.status_loop_active = False

        async def on_ready(self):
            logger.debug(f"Discord Bot Connected as {self.user}")
            # Try to load existing message ID from config
            conf = config.get_manager_config()
            saved_id = conf.get('Discord', 'LiveStatusMessageID', fallback=None)
            if saved_id and saved_id.isdigit():
                self.live_status_msg_id = int(saved_id)
            
            # Start the Live Status Loop
            if self.target_channel_id and not self.status_loop_active:
                self.bg_task = self.loop.create_task(self.live_status_loop())
                self.status_loop_active = True

        async def live_status_loop(self):
            await self.wait_until_ready()
            while not self.is_closed():
                try:
                    await self.update_status_board()
                except Exception as e:
                    logger.debug(f"Live Status Error: {e}")
                await asyncio.sleep(60) # Update every 60 seconds

        async def update_status_board(self):
            if not self.target_channel_id: return
            
            status_data = self.callbacks['get_status']()
            # Determine Color
            color = 0x00ff00 if status_data['online'] else 0xff0000
            
            embed = discord.Embed(title="Server Live Status", color=color)
            embed.add_field(name="Status", value="🟢 ONLINE" if status_data['online'] else "🔴 OFFLINE", inline=True)
            embed.add_field(name="IP Address", value=f"`{status_data['ip']}`", inline=True)
            embed.add_field(name="Uptime", value=status_data['uptime'], inline=True)
            embed.add_field(name="RAM Usage", value=status_data['ram'], inline=True)
            
            # PLAYER LIST FEATURE (v5.1.0)
            players = status_data.get('players', [])
            if players:
                p_list_str = "\n".join([f"• {p}" for p in players])
                # Truncate if too long for Embed
                if len(p_list_str) > 1000: p_list_str = p_list_str[:900] + "\n...and more"
                embed.add_field(name=f"Online Players ({len(players)})", value=p_list_str, inline=False)
            else:
                embed.add_field(name="Online Players", value="No players online.", inline=False)

            embed.set_footer(text=f"Last Updated: {datetime.now().strftime('%H:%M:%S')}")

            channel = self.get_channel(self.target_channel_id)
            if not channel: return

            # Edit Existing or Send New
            if self.live_status_msg_id:
                try:
                    msg = await channel.fetch_message(self.live_status_msg_id)
                    await msg.edit(embed=embed)
                    return
                except discord.NotFound:
                    self.live_status_msg_id = None # Message deleted manually, create new
            
            # Create New
            try:
                msg = await channel.send(embed=embed)
                await msg.pin() 
                self.live_status_msg_id = msg.id
                
                # Save ID to Config so it persists restart
                c = config.get_manager_config()
                if 'Discord' not in c: c['Discord'] = {}
                c['Discord']['LiveStatusMessageID'] = str(msg.id)
                config.save_manager_config(c)
            except Exception as e:
                logger.debug(f"Failed to post/pin status message: {e}")

        async def on_message(self, message):
            if message.author == self.user: return
            if self.target_channel_id and message.channel.id != self.target_channel_id: return
            msg = message.content.lower().strip()

            if msg == "!status":
                await self.update_status_board()
            elif msg == "!restart":
                await message.channel.send("🔄 **Restart Command Received.** Initializing graceful shutdown...")
                self.callbacks['restart']()
            elif msg == "!stop":
                await message.channel.send("🛑 **Stop Command Received.** Shutting down...")
                self.callbacks['stop']()
            elif msg == "!start":
                await message.channel.send("🚀 **Start Command Received.** Launching server...")
                self.callbacks['start']()
            elif msg == "!backup":
                await message.channel.send("💾 **Backup Triggered.**")
                self.callbacks['backup']()
            elif msg == "!ip":
                status = self.callbacks['get_status']()
                await message.channel.send(f"🌐 **Public IP:** `{status['ip']}`")

def start_discord_bot(token, channel_id, callbacks):
    if not DISCORD_LIB_AVAILABLE: return
    def run_loop():
        try:
            bot = VeinDiscordBot(callbacks, channel_id)
            bot.run(token)
        except Exception as e:
            logger.debug(f"Discord Bot Crashed: {e}")
    threading.Thread(target=run_loop, name="DiscordBotThread", daemon=True).start()

# --- MODDING LOGIC ---
def ensure_mod_directory(server_path):
    if not server_path: return None
    path = os.path.join(server_path, constants.MODS_RELATIVE_PATH)
    if not os.path.exists(path):
        try: os.makedirs(path, exist_ok=True)
        except: return None
    return path

def scan_installed_mods(server_path):
    mod_dir = ensure_mod_directory(server_path)
    if not mod_dir: return []
    mods = []
    for f in glob.glob(os.path.join(mod_dir, "*.pak")):
        name = os.path.basename(f)
        mods.append({'name': name, 'status': 'Active', 'file': name})
    for f in glob.glob(os.path.join(mod_dir, "*.pak.disabled")):
        name = os.path.basename(f)
        mods.append({'name': name, 'status': 'Disabled', 'file': name})
    return sorted(mods, key=lambda x: x['name'])

def toggle_mod_state(server_path, filename):
    mod_dir = ensure_mod_directory(server_path)
    if not mod_dir: return False
    src = os.path.join(mod_dir, filename)
    if not os.path.exists(src): return False
    try:
        if filename.endswith(".disabled"):
            new_name = filename.replace(".disabled", "")
            os.rename(src, os.path.join(mod_dir, new_name))
        else:
            new_name = filename + ".disabled"
            os.rename(src, os.path.join(mod_dir, new_name))
        return True
    except Exception as e:
        logger.debug(f"Mod Toggle Error: {e}")
        return False

def install_mod_file(server_path, source_path):
    mod_dir = ensure_mod_directory(server_path)
    if not mod_dir or not source_path: return False
    try:
        filename = os.path.basename(source_path)
        if not filename.lower().endswith(".pak"): return False
        dest = os.path.join(mod_dir, filename)
        shutil.copy2(source_path, dest)
        return True
    except Exception as e:
        logger.debug(f"Mod Install Error: {e}")
        return False

def delete_mod_file(server_path, filename):
    mod_dir = ensure_mod_directory(server_path)
    if not mod_dir: return False
    path = os.path.join(mod_dir, filename)
    try:
        if os.path.exists(path):
            os.remove(path)
            return True
    except: pass
    return False

# --- LOG INTELLIGENCE & WEBHOOKS (v5.0.0) ---
class LogParser:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url
        self.chat_regex = re.compile(constants.REGEX_LOG_CHAT)
        self.kill_regex = re.compile(constants.REGEX_LOG_KILL)

    def process_line(self, line):
        """Analyzes a log line and triggers webhooks if matches found."""
        if not self.webhook_url: return

        # Check Chat
        chat_match = self.chat_regex.search(line)
        if chat_match:
            # chat_match.group(1) is SteamID, group(2) is Name: Message
            # We want to clean it up.
            raw_msg = chat_match.group(2) # "Name: Message"
            if ": " in raw_msg:
                name, content = raw_msg.split(": ", 1)
                self.send_webhook(f"💬 **{name}**: {content}", 3447003) # Blue
            return

        # Check Kill
        kill_match = self.kill_regex.search(line)
        if kill_match:
            killer = kill_match.group(1)
            victim = kill_match.group(2)
            self.send_webhook(f"💀 **{victim}** was killed by **{killer}**", 15158332) # Red
            return

    def send_webhook(self, description, color):
        payload = {
            "embeds": [{
                "description": description,
                "color": color,
                "timestamp": datetime.utcnow().isoformat()
            }]
        }
        def _send():
            try:
                req = urllib.request.Request(self.webhook_url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json', 'User-Agent': 'VeinManager'})
                urllib.request.urlopen(req)
            except: pass
        threading.Thread(target=_send, daemon=True).start()
        
    def send_join_leave_webhook(self, player_name, action, current_count):
        """Called manually by main.py when it detects join/leave."""
        if not self.webhook_url: return
        
        if action == "JOIN":
            desc = f"🟢 **{player_name}** has joined the server. (Players: {current_count})"
            color = 3066993 # Green
        else:
            desc = f"🔴 **{player_name}** has disconnected. (Players: {current_count})"
            color = 15158332 # Red
            
        self.send_webhook(desc, color)

# --- PROFILES ---
def get_profile_list():
    if not os.path.exists(constants.PROFILES_DIR): 
        try: os.makedirs(constants.PROFILES_DIR)
        except: return []
    return [name for name in os.listdir(constants.PROFILES_DIR) 
            if os.path.isdir(os.path.join(constants.PROFILES_DIR, name))]

def save_profile(name, file_paths_dict):
    if not name: return (False, "No profile name provided.")
    target_dir = os.path.join(constants.PROFILES_DIR, name)
    try:
        os.makedirs(target_dir, exist_ok=True)
        files_copied = 0
        if 'Game' in file_paths_dict and os.path.exists(file_paths_dict['Game']):
            shutil.copy2(file_paths_dict['Game'], os.path.join(target_dir, 'Game.ini'))
            files_copied += 1
        if 'Engine' in file_paths_dict and os.path.exists(file_paths_dict['Engine']):
            shutil.copy2(file_paths_dict['Engine'], os.path.join(target_dir, 'Engine.ini'))
            files_copied += 1
        if os.path.exists(constants.MANAGER_CONFIG_FILE):
            shutil.copy2(constants.MANAGER_CONFIG_FILE, os.path.join(target_dir, 'manager_config.ini'))
            files_copied += 1
        return (True, f"Profile '{name}' saved successfully ({files_copied} files).")
    except Exception as e:
        return (False, f"Error saving profile: {str(e)}")

def load_profile(name, file_paths_dict):
    source_dir = os.path.join(constants.PROFILES_DIR, name)
    if not os.path.exists(source_dir): return (False, "Profile folder not found.")
    try:
        restored = 0
        src_game = os.path.join(source_dir, 'Game.ini')
        if os.path.exists(src_game):
            shutil.copy2(src_game, file_paths_dict['Game'])
            restored += 1
        src_engine = os.path.join(source_dir, 'Engine.ini')
        if os.path.exists(src_engine):
            shutil.copy2(src_engine, file_paths_dict['Engine'])
            restored += 1
        src_man = os.path.join(source_dir, 'manager_config.ini')
        if os.path.exists(src_man):
            shutil.copy2(src_man, constants.MANAGER_CONFIG_FILE)
            restored += 1
        return (True, f"Profile '{name}' loaded. ({restored} files restored).")
    except Exception as e:
        return (False, f"Error loading profile: {str(e)}")

# --- DIAGNOSTICS ---
def get_public_ip():
    try:
        with urllib.request.urlopen('https://api.ipify.org?format=json', timeout=3) as r:
            return json.loads(r.read().decode())['ip']
    except: return "Error fetching IP"

def check_port_listening(port):
    try:
        target = int(port)
        for conn in psutil.net_connections(kind='inet'):
            if conn.laddr.port == target:
                if conn.status == psutil.CONN_LISTEN or conn.status == psutil.CONN_NONE:
                    return True
        return False
    except: return False

def check_firewall_fuzzy():
    try:
        cmd = ["netsh", "advfirewall", "firewall", "show", "rule", "name=all"]
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, startupinfo=startupinfo, text=True)
        stdout, stderr = process.communicate()
        if "vein" in stdout.lower(): return True
        return False
    except: return False

def check_disk_activity(pid):
    try:
        if not psutil.pid_exists(pid): return False
        p = psutil.Process(pid)
        io = p.io_counters()
        initial = io.write_bytes
        time.sleep(0.1)
        final = p.io_counters().write_bytes
        return (final - initial) > 0
    except: return False

def get_process_memory_mb(pid):
    try:
        if not pid or not psutil.pid_exists(pid): return 0
        process = psutil.Process(pid)
        mem = process.memory_info().rss
        return mem / (1024 * 1024)
    except: return 0

# --- BACKUPS & STEAMCMD ---
def create_backup(server_path, format_str, retention_count):
    if not server_path: return False
    saved_dir = os.path.join(server_path, 'Vein', 'Saved')
    backup_dir = os.path.join(server_path, 'Backups')
    os.makedirs(backup_dir, exist_ok=True)
    try:
        if not format_str: format_str = "Server_Backup_%Y-%m-%d_%H-%M-%S"
        time_str = datetime.now().strftime(format_str)
        temp_dir = tempfile.mkdtemp()
        temp_save_path = os.path.join(temp_dir, 'Saved')
        cmd = ['robocopy', saved_dir, temp_save_path, '/E', '/ZB', '/COPY:DAT', '/R:1', '/W:1', '/XD', 'Logs', 'Crashes', 'Saved/Logs', '*.log']
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
        shutil.make_archive(os.path.join(backup_dir, time_str), 'zip', temp_save_path)
        shutil.rmtree(temp_dir)
        try:
            limit = int(retention_count)
            if limit > 0:
                backups = sorted(glob.glob(os.path.join(backup_dir, "*.zip")), key=os.path.getmtime)
                while len(backups) > limit: os.remove(backups.pop(0))
        except: pass
        logger.event("BACKUP", f"Created backup: {time_str}")
        return True
    except Exception as e: 
        logger.debug(f"Backup Failed: {e}")
        return False

def run_steamcmd(steam_exe, server_path, branch, output_callback=None, validate_files=False):
    if not steam_exe or not server_path: return False
    validate_cmd = ['validate'] if validate_files else []
    args = ['+login', 'anonymous', '+app_update', constants.VEIN_APP_ID, '-beta', branch] + validate_cmd + ['+quit']
    cmd = [steam_exe, '+force_install_dir', server_path] + args
    
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        
        def read_output(proc, callback):
            try:
                for line in iter(proc.stdout.readline, ''):
                    if callback: callback(line)
            except: pass

        t = threading.Thread(target=read_output, args=(process, output_callback))
        t.start()
        
        try:
            process.wait(timeout=300) 
            t.join(timeout=1)
            return process.returncode == 0
        except subprocess.TimeoutExpired:
            process.kill()
            if output_callback: output_callback("CRITICAL: SteamCMD Timed Out! Forcing execution to continue...")
            logger.debug("SteamCMD Timed Out (5m). Process killed to allow server boot.")
            return False 

    except Exception as e:
        if output_callback: output_callback(f"CRITICAL ERROR: {e}")
        return False

# --- PROCESS UTILS ---
def send_discord_webhook(url, msg_type, description, is_test_env=False):
    if not url: return
    if is_test_env: description = f"**[TEST ENV]** {description}"
    colors = {"START": 5763719, "STOP": 15548997, "CRASH": 15158332, "UPDATE": 3447003, "WARN": 16776960}
    iso_time = datetime.utcnow().isoformat()
    payload = {
        "embeds": [{
            "title": f"Vein Server - {msg_type}",
            "description": description,
            "color": colors.get(msg_type, 0),
            "footer": {"text": f"{constants.MANAGER_VERSION}"},
            "timestamp": iso_time
        }]
    }
    def _send():
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json', 'User-Agent': 'VeinManager'})
            urllib.request.urlopen(req)
        except Exception as e: logger.debug(f"Discord Webhook Failed: {e}")
    threading.Thread(target=_send, daemon=True).start()

def install_autostart_task():
    try:
        exe_path = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath("main.py")
        
        # Generate unique ID based on the folder path
        folder_hash = hashlib.md5(os.getcwd().encode()).hexdigest()[:8]
        task_name = f"VeinManager_{folder_hash}"
        
        cmd = f'schtasks /Create /SC ONLOGON /TN "{task_name}" /TR "\'{exe_path}\'" /RL HIGHEST /F'
        subprocess.run(cmd, shell=True, check=True)
        return True, f"Task '{task_name}' created successfully."
    except Exception as e: return False, str(e)

def remove_autostart_task():
    try:
        folder_hash = hashlib.md5(os.getcwd().encode()).hexdigest()[:8]
        task_name = f"VeinManager_{folder_hash}"
        
        # Try removing both old and new style tasks
        subprocess.run(f'schtasks /Delete /TN "{task_name}" /F', shell=True, check=False)
        subprocess.run('schtasks /Delete /TN "VeinServerManager" /F', shell=True, check=False)
        
        return True, "Tasks removed."
    except Exception as e: return False, str(e)

def parse_log_line_for_analytics(line):
    data = {}
    steam_match = re.search(r'(?:SteamID|steamid|ID)[:\s=]+(7656\d{13})', line, re.IGNORECASE)
    if steam_match: data['steamid'] = steam_match.group(1)
    name_match = re.search(r'AddClient:\s+([^\s]+)', line)
    if name_match: data['name'] = name_match.group(1)
    return data

def ban_player_steamid(server_path, steamid):
    if not server_path or not steamid: return False
    game_ini_path = os.path.join(server_path, 'Vein', 'Saved', 'Config', 'WindowsServer', 'Game.ini')
    section = '/Script/Vein.VeinGameStateBase'
    key = 'BannedPlayers'
    lines = []
    if os.path.exists(game_ini_path):
        with open(game_ini_path, 'r', encoding='utf-8') as f: lines = f.readlines()
    entry = f"{key}={steamid}\n"
    for line in lines:
        if line.strip() == entry.strip(): return True
    new_lines = []
    section_found = False
    inserted = False
    for line in lines:
        new_lines.append(line)
        if line.strip().lower() == section.lower() or (line.strip().startswith('[') and section.lower() in line.lower()):
            section_found = True
        elif section_found and line.strip().startswith('[') and not inserted:
            new_lines.insert(-1, entry)
            inserted = True
            section_found = False
    if not section_found:
        new_lines.append(f"\n[{section}]\n")
        new_lines.append(entry)
    elif section_found and not inserted:
        new_lines.append(entry)
    try:
        with open(game_ini_path, 'w', encoding='utf-8') as f: f.writelines(new_lines)
        return True
    except: return False

def get_banned_players(server_path):
    path = os.path.join(server_path, 'Vein', 'Saved', 'Config', 'WindowsServer', 'Game.ini')
    bans = []
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    if 'BannedPlayers=' in line: bans.append(line.split('=')[1].strip())
        except: pass
    return bans

def is_process_running(pid):
    if not pid: return False
    if psutil.pid_exists(pid):
        try:
            if psutil.Process(pid).status() != psutil.STATUS_ZOMBIE: return True
        except: pass
    return False

def find_server_pid(server_path):
    if not server_path: return None
    try:
        norm_path = os.path.normpath(server_path).lower()
        
        # --- FIX v5.1.4: Strict Directory Matching ---
        # Ensure path ends with separator to prevent "C:\Vein" matching "C:\Vein_Test"
        if not norm_path.endswith(os.sep): 
            norm_path += os.sep
            
        for proc in psutil.process_iter(['pid', 'name', 'exe']):
            try:
                if proc.info['name'] == constants.SERVER_EXECUTABLE:
                    proc_exe = proc.info['exe']
                    if proc_exe:
                        # Check if process executable is located INSIDE the server path
                        if os.path.normpath(proc_exe).lower().startswith(norm_path):
                            return proc.info['pid']
            except: pass
    except: pass
    return None

def kill_server_by_pid(pid):
    if not pid: return
    try:
        logger.debug(f"Surgical Kill Requested for PID {pid}")
        if psutil.pid_exists(pid):
            p = psutil.Process(pid)
            p.terminate()
            try: p.wait(timeout=10)
            except: p.kill()
    except: pass
    try:
        subprocess.run(['TASKKILL', '/F', '/PID', str(pid), '/T'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
    except: pass

def check_prerequisites(server_path, steamcmd_path, log_callback):
    if not server_path: return
    dll_dir = os.path.join(server_path, 'Vein', 'Binaries', 'Win64')
    dll_path = os.path.join(dll_dir, 'steamclient64.dll')
    if not os.path.exists(dll_path):
        if steamcmd_path and os.path.exists(steamcmd_path):
            src = os.path.join(os.path.dirname(steamcmd_path), 'steamclient64.dll')
            if os.path.exists(src):
                try:
                    os.makedirs(dll_dir, exist_ok=True)
                    shutil.copy(src, dll_path)
                    if log_callback: log_callback(">> System: Auto-Fixed steamclient64.dll")
                    logger.debug("System: Auto-Fixed steamclient64.dll")
                except: pass

# --- STEAM BETA BRANCH RETRIEVAL USING STEAMCLIENT ---
# --- REQUIRES 'steam' PYPI PACKAGE ---
def steam_get_beta_branches():
    # Initialize the client
    client = SteamClient()

    # Log in (you will be prompted for credentials/2FA if not cached)
    client.anonymous_login() 

    # Set APP ID to Vein
    appid = int(constants.VEIN_APP_ID)

    # Retrieve product info for the specific AppID
    product_info = client.get_product_info(apps=[appid])
    
    if not product_info or 'apps' not in product_info:
        return "Game not found or info unavailable."

    # Navigate the nested dictionary to find branches
    # Structure: product_info['apps'][appid]['depots']['branches']
    app_data = product_info['apps'].get(appid, {})
    branches = app_data.get('depots', {}).get('branches', {})
    
    if not branches:
        return "No beta branches found for this app."
    
    #for branch_name, details in branches.items():
    branches = list(branches.keys()) # or [name for name in branches]

    client.disconnect()
    
    return branches