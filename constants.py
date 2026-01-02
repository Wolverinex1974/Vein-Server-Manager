# --- VERSION & IDENTITY ---
MANAGER_VERSION = "v5.1.4 (Integrity & Polish)"
AUTHOR_NAME = "Wolverinex77"

# constants.py
import os
import sys
from datetime import datetime

APP_TITLE = f"Vein Manager {MANAGER_VERSION}"
DEBUG_MODE = True

# --- FILE PATHS ---
if getattr(sys, 'frozen', False):
    APPLICATION_PATH = os.path.dirname(sys.executable)
else:
    APPLICATION_PATH = os.path.dirname(os.path.abspath(__file__))

EXECUTABLE_NAME = os.path.basename(sys.executable) if getattr(sys, 'frozen', False) else "main.py"
SERVER_EXECUTABLE = 'VeinServer-Win64-Test.exe'
MANAGER_CONFIG_FILE = os.path.join(APPLICATION_PATH, 'manager_config.ini')
HISTORY_FILE = os.path.join(APPLICATION_PATH, 'player_history.json')

# Log Organization
LOGS_ROOT_DIR = os.path.join(APPLICATION_PATH, 'Manager_Logs')
CRASH_LOGS_DIR = os.path.join(LOGS_ROOT_DIR, 'Crashes')
HISTORY_LOGS_DIR = os.path.join(LOGS_ROOT_DIR, 'History')
DAILY_LOG_FILE = os.path.join(HISTORY_LOGS_DIR, f"Events_{datetime.now().strftime('%Y-%m-%d')}.log")
DEBUG_LOG_FILE = os.path.join(APPLICATION_PATH, "debug_crash.log")

# Profiles
PROFILES_DIR = os.path.join(APPLICATION_PATH, 'User_Profiles')

ICON_FILE = os.path.join(APPLICATION_PATH, 'favicon.ico')

# --- MODDING SUITE ---
MODS_RELATIVE_PATH = os.path.join('Vein', 'Content', 'Paks', '~mods')

PROTECTED_SECTIONS = [
    '/script/vein.veingamesession',
    '/script/vein.serversettings',
    '/script/engine.gamesession',
    '/script/engine.gamenetworkmanager',
    'core.system',
    'url'
]

# --- EXTERNAL ---
VEIN_APP_ID = '2131400'
STEAMCMD_URL = "https://steamcdn-a.akamaihd.net/client/installer/steamcmd.zip"
GITHUB_API_URL = "https://api.github.com/repos/Wolverinex1974/Vein-Server-Manager/releases/latest"

# --- LINKS ---
LINK_DISCORD_MAIN = "https://discord.gg/qPhWD6AxhV"
LINK_DISCORD_MODS = "https://discord.gg/5McDc8javs"
LINK_NEXUS_MODS = "https://www.nexusmods.com/vein/mods/101"
LINK_GITHUB = "https://github.com/Wolverinex1974/Vein-Server-Manager"
LINK_GITHUB_RELEASES = "https://github.com/Wolverinex1974/Vein-Server-Manager/releases"
LINK_KOFI = "https://ko-fi.com/wolverine74"

# --- LOGGING & CONNECTIVITY (v5.1.0) ---
REGEX_SAVE_START = "LogVeinSaveGame: Saving all objects"
REGEX_SAVE_FINISH_A = "LogVeinSaveGame: Saved to slot Server"
REGEX_SAVE_FINISH_B = "LogVeinSaveGame: Saved autosave game to disk"

# Chat & Kill (Stateless)
REGEX_LOG_CHAT = r"LogVeinChat: \[.*?\] (.*?): (.*)" 
REGEX_LOG_KILL = r"LogVein: Display: (.*?) killed (.*?)" 

# Session Tracking (Stateful)
# Matches: Name=Wolverine??ID=7656...
REGEX_PLAYER_JOIN = r"Name=(.*?)\?.*ID=(\d+)"
# Matches: Ended auth session for ID 7656...
REGEX_PLAYER_LEAVE = r"Ended auth session for ID (\d+)"

# Smart Log Highlighting
LOG_HIGHLIGHTS = {
    "Error": "#FF4444",        # Soft Red
    "Fatal": "#FF0000",        # Bright Red
    "Warning": "#FFD700",      # Gold
    "LogVeinChat": "#00FFFF",  # Cyan
    "Join": "#00FF00",         # Green
    "Left": "#FFA07A",         # Light Salmon
    "Saved": "#ADFF2F",        # GreenYellow
    "Steam": "#1E90FF",        # DodgerBlue
    "Auth": "#1E90FF"
}

# --- FAQ CONTENT ---
FAQ_TEXT = {
    "Discord Setup Guide": (
        "STEP 1: CREATE BOT\n"
        "1. Go to discord.com/developers/applications\n"
        "2. Click 'New Application' -> Name it -> Create.\n"
        "3. Go to 'Bot' tab -> Enable 'MESSAGE CONTENT INTENT'.\n"
        "4. Click 'Reset Token', copy it, paste into Manager.\n\n"
        "STEP 2: INVITE BOT\n"
        "1. Go to 'OAuth2' -> 'URL Generator'.\n"
        "2. Select Scope: 'bot'.\n"
        "3. Scroll down to BOT PERMISSIONS -> Check 'Administrator'.\n"
        "4. Copy URL, open in browser, invite to server.\n\n"
        "STEP 3: CHANNEL ID\n"
        "1. Discord Settings -> Advanced -> Developer Mode ON.\n"
        "2. Right-click your desired channel -> Copy Channel ID.\n"
        "3. Paste into Manager -> Click SAVE.\n"
        "4. Test with !status"
    ),
    "Installation": "1. Go to 'Server Management'.\n2. Click 'Manual Update'.\n3. Wait for Success.",
    "Mods": "1. Go to 'Mods' tab.\n2. Drag & Drop .pak files or click Install.\n3. Use 'Safe Editor' to change settings without breaking the server.",
    "Update Hangs": "If the server stays offline during a restart, SteamCMD might be stuck. The Manager now auto-kills stuck updates after 5 minutes.",
    "Bot Commands": "!status, !start, !stop, !restart, !backup, !ip"
}

# --- GAMEPLAY DEFS ---
GAMEPLAY_DEFINITIONS = {
    "General & Loot": [
        ("Loot Scarcity", "vein.Scarcity.Difficulty", "Loot Rarity. (Default: Standard=2.0)", "combo_scarcity", "Engine", "ConsoleVariables", "2.0"),
        ("Max Characters", "vein.Characters.Max", "Chars per SteamID. (Default: 1)", "str", "Engine", "ConsoleVariables", "1"),
        ("Containers Respawn", "vein.ContainersRespawn.Enabled", "Chests refill over time? (Default: True)", "bool", "Engine", "ConsoleVariables", True),
        ("World Items Respawn", "vein.ItemActorSpawner.Respawns", "Items on shelves respawn? (Default: True)", "bool", "Engine", "ConsoleVariables", True),
        ("Furniture Respawns", "vein.Furniture.Respawns", "Destroyed doors/tables return? (Default: False)", "bool", "Engine", "ConsoleVariables", False),
        ("Furn. Respawn Rate", "vein.Furniture.RespawnRate", "Cooldown Seconds (Higher=Slower). (Default: 900.0)", "str", "Engine", "ConsoleVariables", "900.0"),
        ("Max Utility Cabinets", "vein.Placement.MaxUtilityCabinets", "Limit per area. 0=Unlimited. (Default: 0)", "str", "Engine", "ConsoleVariables", "0"),
        ("Wire Max Radius", "vein.Wire.MaxRadius", "Electrical wire range. (Default: 1500)", "str", "Engine", "ConsoleVariables", "1500"),
        ("TV Max Radius", "vein.Wire.TVMaxRadius", "Electrical range for TVs. (Default: 1500)", "str", "Engine", "ConsoleVariables", "1500"),
        ("Hideable Clothes", "vein.ClothingHideable", "Can armor be hidden? (Default: False)", "bool", "Engine", "ConsoleVariables", False),
    ],
    "Survival & Time": [
        ("Time Multiplier", "vein.Time.TimeMultiplier", "Day Speed (Higher=Faster Days). (Default: 15.1)", "str", "Engine", "ConsoleVariables", "15.1"),
        ("Night Multiplier", "vein.Time.NightTimeMultiplier", "Night Speed (Higher=Faster Night). (Default: 3.2)", "str", "Engine", "ConsoleVariables", "3.2"),
        ("Night Start Hour", "vein.Time.NightTimeMultiplierStart", "Hour night begins (24h). (Default: 20.0)", "str", "Engine", "ConsoleVariables", "20.0"),
        ("Night End Hour", "vein.Time.NightTimeMultiplierEnd", "Hour night ends (24h). (Default: 6.0)", "str", "Engine", "ConsoleVariables", "6.0"),
        ("Time Passes Empty", "vein.Time.ContinueWithNoPlayers", "Time runs when empty? (Default: False)", "bool", "Engine", "ConsoleVariables", False),
        ("Hunger Multiplier", "GS_HungerMultiplier", "Drain Speed (Higher=Starve Faster). (Default: 1.0)", "str", "Game", "/Script/Vein.ServerSettings", "1.0"),
        ("Thirst Multiplier", "GS_ThirstMultiplier", "Drain Speed (Higher=Thirst Faster). (Default: 1.0)", "str", "Game", "/Script/Vein.ServerSettings", "1.0"),
        ("Global XP Mult", "vein.Stats.XPMultiplier", "XP Gain (2.0 = Double XP). (Default: 1.0)", "str", "Engine", "ConsoleVariables", "1.0"),
        ("Start Offset Days", "vein.Time.StartOffsetDays", "Days passed at start. (Default: 0)", "str", "Engine", "ConsoleVariables", "0"),
        ("Elec Shutoff Day", "vein.Calendar.ElectricalShutoffTimeDays", "Day grid fails. (Default: 46)", "str", "Engine", "ConsoleVariables", "46"),
        ("Water Shutoff Day", "vein.Calendar.WaterShutoffTimeDays", "Day water fails. (Default: 30)", "str", "Engine", "ConsoleVariables", "30"),
    ],
    "Zombies (The Horde)": [
        ("Zombie Health", "vein.Zombies.Health", "Base HP (Default: 40).", "str", "Engine", "ConsoleVariables", "40"),
        ("Headshots Only", "vein.Zombies.HeadshotOnly", "Only headshots kill. (Default: False)", "bool", "Engine", "ConsoleVariables", False),
        ("Spawn Density", "vein.AISpawner.SpawnCapMultiplierZombie", "Higher = More Zombies. (Default: 1.0)", "str", "Engine", "ConsoleVariables", "1.0"),
        ("Run Speed Mult", "vein.Zombies.RunSpeedMultiplier", "Sprinters Speed (Higher=Faster). (Default: 1.0)", "str", "Engine", "ConsoleVariables", "1.0"),
        ("Walk Speed Mult", "vein.Zombies.WalkSpeedMultiplier", "Walkers Speed (Higher=Faster). (Default: 1.0)", "str", "Engine", "ConsoleVariables", "1.0"),
        ("Crawl Speed Mult", "vein.Zombies.CrawlSpeedMultiplier", "Crawlers Speed (Higher=Faster). (Default: 1.0)", "str", "Engine", "ConsoleVariables", "1.0"),
        ("Global Speed Mult", "vein.Zombies.SpeedMultiplier", "All Zombies Speed. (Default: 1.0)", "str", "Engine", "ConsoleVariables", "1.0"),
        ("Horde Mode", "vein.AISpawner.Hordes.Enabled", "Roaming hordes? (Default: True)", "bool", "Engine", "ConsoleVariables", True),
        ("Always Turn", "vein.AlwaysBecomeZombie", "Players turn on death. (Default: True)", "bool", "Engine", "ConsoleVariables", True),
        ("Can Climb", "vein.Zombies.CanClimb", "Zombies climb walls. (Default: True)", "bool", "Engine", "ConsoleVariables", True),
        ("Infection Chance", "vein.ZombieInfectionChance", "Prob on Hit (0.01 = 1%). (Default: 0.01)", "str", "Engine", "ConsoleVariables", "0.01"),
        ("Damage Mult", "vein.Zombies.DamageMultiplier", "Zombie Dmg Output. (Default: 1.0)", "str", "Engine", "ConsoleVariables", "1.0"),
        ("Hearing Mult", "vein.Zombies.HearingMultiplier", "Detection Range. (Default: 1.0)", "str", "Engine", "ConsoleVariables", "1.0"),
        ("Sight Mult", "vein.Zombies.SightMultiplier", "Vision Range. (Default: 1.0)", "str", "Engine", "ConsoleVariables", "1.0"),
        ("Stagger Chance", "vein.StaggerChance", "Chance on hit (0.1 = 10%). (Default: 0.1)", "str", "Engine", "ConsoleVariables", "0.1"),
        ("Stun Chance", "vein.StunLockChance", "Chance on hit (0.6 = 60%). (Default: 0.6)", "str", "Engine", "ConsoleVariables", "0.6"),
        ("Walker %", "vein.AISpawner.ZombieWalkerPercentage", "0.8 = 80% Walkers. (Default: 0.8)", "str", "Engine", "ConsoleVariables", "0.8"),
    ],
    "PVP & Vehicles": [
        ("Enable PvP", "vein.PvP", "Player vs Player combat. (Default: True)", "bool", "Engine", "ConsoleVariables", True),
        ("Vehicle Player Dmg", "vein.Vehicles.Damage.OutgoingPlayerDamage", "Collision damage (Higher=More). (Default: 1.0)", "str", "Engine", "ConsoleVariables", "1.0"),
        ("Permadeath", "vein.Permadeath", "Character deleted on death. (Default: False)", "bool", "Engine", "ConsoleVariables", False),
        ("Iron Man Mode", "vein.NoSaves", "No manual saves allowed. (Default: False)", "bool", "Engine", "ConsoleVariables", False),
        ("Base Damage", "vein.BaseDamage", "Can bases be damaged? (Default: True)", "bool", "Engine", "ConsoleVariables", True),
        ("Player Raid Base", "vein.BuildObjectPvP", "Can players damage bases? (Default: True)", "bool", "Engine", "ConsoleVariables", True),
        ("Structure Decay", "vein.BuildObjectDecay", "Abandoned structures decay? (Default: True)", "bool", "Engine", "ConsoleVariables", True),
        ("Decay Interval", "vein.UtilityCabinet.Interval", "Hours between decay ticks. (Default: 4.0)", "str", "Engine", "ConsoleVariables", "4.0"),
        ("Offline Protection", "vein.OfflineRaidProtection", "Prevent offline dmg. (Default: False)", "bool", "Engine", "ConsoleVariables", False),
        ("Pickpocketing", "vein.AllowPickpocketing", "Steal inventory? (Default: True)", "bool", "Engine", "ConsoleVariables", True),
        ("Headshot Mult", "vein.HeadshotDamageMultiplier", "PVP Dmg Multiplier. (Default: 1.9)", "str", "Engine", "ConsoleVariables", "1.9"),
    ]
}