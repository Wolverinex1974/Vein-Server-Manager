# --- VERSION & IDENTITY ---
# MANAGER_VERSION = "v4.4.5 (Stable Release)"

# config.py
import configparser
import os
import constants

def get_manager_config():
    """Reads manager_config.ini and returns the parser object."""
    config = configparser.ConfigParser(interpolation=None)
    if os.path.exists(constants.MANAGER_CONFIG_FILE):
        config.read(constants.MANAGER_CONFIG_FILE)
    return config

def save_manager_config(config_obj):
    """Writes the parser object to disk."""
    try:
        with open(constants.MANAGER_CONFIG_FILE, 'w') as f:
            config_obj.write(f)
    except Exception as e:
        print(f"Error saving config: {e}")

def get_game_ini_path(server_path):
    if not server_path: return None
    return os.path.join(server_path, 'Vein', 'Saved', 'Config', 'WindowsServer', 'Game.ini')

def get_engine_ini_path(server_path):
    if not server_path: return None
    return os.path.join(server_path, 'Vein', 'Saved', 'Config', 'WindowsServer', 'Engine.ini')

def get_existing_section_name(config_obj, target_section):
    """Finds a section case-insensitively."""
    for section in config_obj.sections():
        if section.lower() == target_section.lower():
            return section
    return target_section

def load_game_ini(server_path):
    """Safely loads Game.ini considering Case Sensitivity."""
    path = get_game_ini_path(server_path)
    config = configparser.ConfigParser(strict=False)
    config.optionxform = str # Preserve Case
    if path and os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                config.read_file(f)
        except:
            config.read(path)
    return config

def save_game_ini(server_path, config_obj):
    """Writes Game.ini."""
    path = get_game_ini_path(server_path)
    if not path: return
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            config_obj.write(f, space_around_delimiters=False)
    except Exception as e:
        print(f"Failed to write Game.ini: {e}")

def update_engine_ini_cvar(server_path, updates_dict):
    """Parses Engine.ini specifically for [ConsoleVariables] and updates keys."""
    path = get_engine_ini_path(server_path)
    if not path: return

    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    lines = []
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

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
                    for k, v in updates_dict.items():
                        if k not in keys_written:
                            new_lines.append(f"{k}={v}\n")
                            keys_written.add(k)
                in_cvar_section = False
                new_lines.append(line)
                continue

        if in_cvar_section:
            matched_key = None
            for k in updates_dict:
                if stripped.lower().startswith(k.lower() + "="):
                    matched_key = k
                    break
            
            if matched_key:
                new_lines.append(f"{matched_key}={updates_dict[matched_key]}\n")
                keys_written.add(matched_key)
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    if not section_found:
        new_lines.append("\n[ConsoleVariables]\n")
        in_cvar_section = True

    if in_cvar_section:
        for k, v in updates_dict.items():
            if k not in keys_written:
                new_lines.append(f"{k}={v}\n")

    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
    except Exception as e:
        print(f"Failed to write Engine.ini: {e}")

def load_engine_ini_raw(filepath, keys_to_find):
    """Reads Engine.ini and returns a dictionary of found values."""
    if not filepath or not os.path.exists(filepath): return {}
    
    found_values = {}
    in_cvar = False
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                s = line.strip()
                if s.lower() == '[consolevariables]': 
                    in_cvar = True
                    continue
                if s.startswith('[') and s.lower() != '[consolevariables]': 
                    in_cvar = False
                    continue
                
                if in_cvar and '=' in s:
                    parts = s.split('=', 1)
                    key = parts[0].strip()
                    val = parts[1].strip()
                    
                    for target in keys_to_find:
                        if key.lower() == target.lower():
                            found_values[target] = val
    except: pass
    return found_values