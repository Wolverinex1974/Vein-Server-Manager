# --- VERSION & IDENTITY ---
# MANAGER_VERSION = "v4.4.5 (Stable Release)"

# logic.py
import os
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
from datetime import datetime
import constants
import config
import logger 

# --- PROFILES ---
def get_profile_list():
    if not os.path.exists(constants.PROFILES_DIR): 
        try: os.makedirs(constants.PROFILES_DIR)
        except: return []
    return [name for name in os.listdir(constants.PROFILES_DIR) 
            if os.path.isdir(os.path.join(constants.PROFILES_DIR, name))]

def save_profile(name, file_paths_dict):
    """Saves critical INI files. Returns (Success_Bool, Message_String)."""
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
        if files_copied == 0:
            return (True, f"Profile '{name}' created, but NO config files were found to copy.\nCheck your Server Path.")
        return (True, f"Profile '{name}' saved successfully ({files_copied} files).")
    except Exception as e:
        return (False, f"Error saving profile: {str(e)}")

def load_profile(name, file_paths_dict):
    """Restores INI files. Returns (Success_Bool, Message_String)."""
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

def check_port_open(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.bind(('0.0.0.0', int(port)))
        result = False 
    except: result = True 
    finally: sock.close()
    return result

def check_firewall_rule():
    try:
        output = subprocess.check_output('netsh advfirewall firewall show rule name="VeinServer"', shell=True, stderr=subprocess.STDOUT)
        if b"No rules match" in output: return False
        return True
    except: return False

def check_disk_activity(pid):
    """Returns True if the process is writing to disk."""
    try:
        if not psutil.pid_exists(pid): return False
        p = psutil.Process(pid)
        io = p.io_counters()
        initial = io.write_bytes
        time.sleep(0.1)
        final = p.io_counters().write_bytes
        return (final - initial) > 0
    except:
        return False

# --- DISCORD ---
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
    if msg_type == "CRASH": payload["embeds"][0]["footer"]["text"] += " | Server Watchdog Active"
    def _send():
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json', 'User-Agent': 'VeinManager'})
            urllib.request.urlopen(req)
        except Exception as e: logger.debug(f"Discord Webhook Failed: {e}")
    threading.Thread(target=_send, daemon=True).start()

# --- BACKUPS ---
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
        for line in iter(process.stdout.readline, ''):
            if output_callback: output_callback(line)
        process.wait()
        return process.returncode == 0
    except Exception as e:
        if output_callback: output_callback(f"CRITICAL ERROR: {e}")
        return False

# --- ANALYTICS & PROCESS MANAGEMENT ---
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
    """
    Finds a running VeinServer.exe process that specifically belongs to the given folder path.
    Prevents cross-talk between Live and Test servers.
    """
    if not server_path: return None
    try:
        # Normalize slashes for comparison
        norm_path = os.path.normpath(server_path).lower()
        
        for proc in psutil.process_iter(['pid', 'name', 'exe']):
            try:
                # Check Name
                if proc.info['name'] == constants.SERVER_EXECUTABLE:
                    # Check Executable Path
                    proc_exe = proc.info['exe']
                    if proc_exe:
                        # proc_exe is usually .../Binaries/Win64/VeinServer.exe
                        # We want to know if it lives inside our 'server_path'
                        if norm_path in os.path.normpath(proc_exe).lower():
                            return proc.info['pid']
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
    except:
        pass
    return None

def kill_server_by_pid(pid):
    """Surgically kills only the specified PID."""
    if not pid: return
    try:
        logger.debug(f"Surgical Kill Requested for PID {pid}")
        # Python Kill
        if psutil.pid_exists(pid):
            p = psutil.Process(pid)
            p.terminate()
            try: p.wait(timeout=5)
            except: p.kill()
    except: pass
    
    # Windows Taskkill Force (Safety Net) - PID ONLY
    try:
        subprocess.run(['TASKKILL', '/F', '/PID', str(pid), '/T'], 
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, 
                       creationflags=subprocess.CREATE_NO_WINDOW)
    except: pass

def check_prerequisites(server_path, steamcmd_path, log_callback):
    """Checks for required DLLs and copies them if missing."""
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