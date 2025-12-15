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
from datetime import datetime
import constants
import config

# --- DISCORD ---
def send_discord_webhook(url, msg_type, description, is_test_env=False):
    if not url: return
    
    if is_test_env:
        description = f"**[TEST ENV]** {description}"

    colors = {
        "START": 5763719,  # Green
        "STOP": 15548997,  # Red
        "CRASH": 15158332, # Orange/Red
        "UPDATE": 3447003, # Blue
        "WARN": 16776960   # Yellow
    }
    
    payload = {
        "embeds": [{
            "title": f"Vein Server - {msg_type}",
            "description": description,
            "color": colors.get(msg_type, 0),
            "footer": {"text": f"{constants.MANAGER_VERSION}"},
            "timestamp": datetime.now().isoformat()
        }]
    }
    
    # Add tip footer on crash
    if msg_type == "CRASH":
        payload["embeds"][0]["footer"]["text"] += " | Server Watchdog Active"

    def _send():
        try:
            req = urllib.request.Request(
                url, 
                data=json.dumps(payload).encode('utf-8'), 
                headers={'Content-Type': 'application/json', 'User-Agent': 'VeinManager'}
            )
            urllib.request.urlopen(req)
        except Exception as e:
            print(f"Discord Error: {e}")

    threading.Thread(target=_send, daemon=True).start()

# --- BACKUPS ---
def create_backup(server_path, format_str, retention_count):
    if not server_path: return False
    
    saved_dir = os.path.join(server_path, 'Vein', 'Saved')
    backup_dir = os.path.join(server_path, 'Backups')
    os.makedirs(backup_dir, exist_ok=True)
    
    try:
        # 1. Zip
        if not format_str: format_str = "Server_Backup_%Y-%m-%d_%H-%M-%S"
        time_str = datetime.now().strftime(format_str)
        
        # Create temp copy to avoid file locks
        temp_dir = tempfile.mkdtemp()
        temp_save_path = os.path.join(temp_dir, 'Saved')
        
        # Robocopy is safer for live files than shutil
        cmd = ['robocopy', saved_dir, temp_save_path, '/E', '/ZB', '/COPY:DAT', '/R:1', '/W:1', '/XD', 'Logs', 'Crashes', 'Saved/Logs', '*.log']
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
        
        shutil.make_archive(os.path.join(backup_dir, time_str), 'zip', temp_save_path)
        shutil.rmtree(temp_dir)
        
        # 2. Retention (Cleanup)
        try:
            limit = int(retention_count)
            if limit > 0:
                backups = sorted(glob.glob(os.path.join(backup_dir, "*.zip")), key=os.path.getmtime)
                if len(backups) > limit:
                    for f in backups[:-limit]:
                        os.remove(f)
        except: pass
        
        return True
    except Exception as e:
        print(f"Backup Error: {e}")
        return False

# --- STEAMCMD ---
def run_steamcmd(steam_exe, server_path, branch, output_callback=None):
    if not steam_exe or not server_path: return False
    
    args = ['+login', 'anonymous', '+app_update', constants.VEIN_APP_ID, '-beta', branch, '+quit']
    cmd = [steam_exe, '+force_install_dir', server_path] + args
    
    try:
        # No window creation flag
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, 
            text=True, 
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        for line in iter(process.stdout.readline, ''):
            if output_callback:
                output_callback(line)
        
        process.wait()
        return process.returncode == 0
    except Exception as e:
        if output_callback: output_callback(f"CRITICAL ERROR: {e}")
        return False

# --- SYSTEM UTILS ---
def is_process_running(pid):
    if not pid: return False
    if psutil.pid_exists(pid):
        try:
            if psutil.Process(pid).status() != psutil.STATUS_ZOMBIE:
                return True
        except: pass
    return False

def find_server_pid(server_path):
    if not server_path: return None
    expected_exe = os.path.join(server_path, 'Vein', 'Binaries', 'Win64', constants.SERVER_EXECUTABLE)
    
    for proc in psutil.process_iter(['pid', 'name', 'exe']):
        try:
            if proc.info['name'] == constants.SERVER_EXECUTABLE:
                if proc.info['exe'] and os.path.normpath(proc.info['exe']) == os.path.normpath(expected_exe):
                    return proc.info['pid']
        except: pass
    return None

def check_prerequisites(server_path, steamcmd_path, log_callback):
    """Auto-fixes the missing steamclient64.dll issue"""
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
                    if log_callback: log_callback(">> System: Auto-Fixed steamclient64.dll\n")
                except: pass

def get_build_id(server_path, is_local=True, steamcmd_path=None, branch="public"):
    """Gets either local or remote Build ID"""
    if is_local:
        if not server_path: return None
        paths = [
            os.path.join(server_path, 'steamapps', f'appmanifest_{constants.VEIN_APP_ID}.acf'),
            os.path.join(server_path, 'Vein', 'steamapps', f'appmanifest_{constants.VEIN_APP_ID}.acf'),
            os.path.join(server_path, f'appmanifest_{constants.VEIN_APP_ID}.acf')
        ]
        for p in paths:
            if os.path.exists(p):
                try:
                    with open(p, 'r', encoding='utf-8', errors='ignore') as f:
                        match = re.search(r'"buildid"\s+"(\d+)"', f.read())
                        if match: return match.group(1)
                except: pass
        return None
    else:
        # Remote Check via SteamCMD
        if not steamcmd_path or not os.path.exists(steamcmd_path): return None
        args = [steamcmd_path, '+login', 'anonymous', '+app_info_update', '1', '+app_info_print', constants.VEIN_APP_ID, '+quit']
        try:
            p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=subprocess.CREATE_NO_WINDOW, errors='ignore', cwd=os.path.dirname(steamcmd_path))
            out, _ = p.communicate()
            
            lines = out.splitlines()
            in_branches = False
            in_target = False
            for line in lines:
                clean = line.strip().replace('"', '')
                if "branches" in clean: in_branches = True
                if in_branches:
                    if clean.startswith(branch): in_target = True
                    if in_target:
                        if "buildid" in clean: return clean.split()[1]
                        if "}" in clean and "buildid" not in clean: in_target = False
        except: pass
        return None