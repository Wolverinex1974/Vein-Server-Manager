# constants.py
import os
import sys

# --- VERSION & IDENTITY ---
MANAGER_VERSION = "v3.9.0 (Modular Refactor)"
AUTHOR_NAME = "Wolverinex77"
APP_TITLE = f"Vein Manager {MANAGER_VERSION}"

# --- FILE PATHS ---
if getattr(sys, 'frozen', False):
    APPLICATION_PATH = os.path.dirname(sys.executable)
else:
    APPLICATION_PATH = os.path.dirname(os.path.abspath(__file__))

SERVER_EXECUTABLE = 'VeinServer-Win64-Test.exe'
MANAGER_CONFIG_FILE = os.path.join(APPLICATION_PATH, 'manager_config.ini')
HISTORY_FILE = os.path.join(APPLICATION_PATH, 'player_history.json')
LOGS_DIR = os.path.join(APPLICATION_PATH, 'Manager_Logs')
EVENTS_LOG_FILE = os.path.join(LOGS_DIR, 'Manager_Events.log')
ICON_FILE = os.path.join(APPLICATION_PATH, 'favicon.ico')

# --- EXTERNAL ---
VEIN_APP_ID = '2131400'
STEAMCMD_URL = "https://steamcdn-a.akamaihd.net/client/installer/steamcmd.zip"
GITHUB_API_URL = "https://api.github.com/repos/Wolverinex1974/Vein-Server-Manager/releases/latest"

# --- LINKS ---
LINK_DISCORD_MAIN = "https://discord.gg/qPhWD6AxhV"
LINK_DISCORD_MODS = "https://discord.gg/5McDc8javs"
LINK_NEXUS_MODS = "https://www.nexusmods.com/vein/mods/101"
LINK_GITHUB = "https://github.com/Wolverinex1974/Vein-Server-Manager"
LINK_KOFI = "https://ko-fi.com/wolverine74"

# --- THE TRUTH TABLE (Gameplay Defaults) ---
# Format: (Label, Key, Tooltip, Type, IniFile, Section, DefaultValue)
GAMEPLAY_DEFINITIONS = {
    "General & Loot": [
        ("Loot Scarcity", "vein.Scarcity.Difficulty", "Loot Rarity. Standard=2.0. (Default: 2.0)", "combo_scarcity", "Engine", "ConsoleVariables", "2.0"),
        ("Containers Respawn", "vein.ContainersRespawn.Enabled", "Do chests/cabinets refill over time? (Default: True)", "bool", "Engine", "ConsoleVariables", True),
        ("World Items Respawn", "vein.ItemActorSpawner.Respawns", "Do items on shelves/tables respawn? (Default: True)", "bool", "Engine", "ConsoleVariables", True),
        ("Furniture Respawns", "vein.Furniture.Respawns", "Do destroyed doors/tables come back? (Default: False)", "bool", "Engine", "ConsoleVariables", False),
        ("Furn. Respawn Rate", "vein.Furniture.RespawnRate", "Cooldown in Seconds (900s = 15m). (Default: 900.0)", "str", "Engine", "ConsoleVariables", "900.0"),
        ("Max Utility Cabinets", "vein.Placement.MaxUtilityCabinets", "Limit per area. 0=Unlimited. (Default: 0)", "str", "Engine", "ConsoleVariables", "0"),
        ("Wire Max Radius", "vein.Wire.MaxRadius", "Electrical wire range. (Default: 1500)", "str", "Engine", "ConsoleVariables", "1500"),
        ("Hideable Clothes", "vein.ClothingHideable", "Can armor be hidden for Roleplay? (Default: False)", "bool", "Engine", "ConsoleVariables", False),
    ],
    "Survival & Time": [
        ("Time Multiplier", "vein.Time.TimeMultiplier", "Day Speed. Higher = Faster. (Default: 15.1 ~ 90mins)", "str", "Engine", "ConsoleVariables", "15.1"),
        ("Night Multiplier", "vein.Time.NightTimeMultiplier", "Night Speed. Higher = Faster. (Default: 3.2)", "str", "Engine", "ConsoleVariables", "3.2"),
        ("Night Start Hour", "vein.Time.NightTimeMultiplierStart", "Hour night begins (24h). (Default: 20.0 = 8PM)", "str", "Engine", "ConsoleVariables", "20.0"),
        ("Night End Hour", "vein.Time.NightTimeMultiplierEnd", "Hour night ends (24h). (Default: 6.0 = 6AM)", "str", "Engine", "ConsoleVariables", "6.0"),
        ("Time Passes Empty", "vein.Time.ContinueWithNoPlayers", "Does time run when no one is online? (Default: False)", "bool", "Engine", "ConsoleVariables", False),
        ("Hunger Multiplier", "GS_HungerMultiplier", "Drain Rate. Higher = Starve Faster. (Default: 1.0)", "str", "Game", "/Script/Vein.ServerSettings", "1.0"),
        ("Thirst Multiplier", "GS_ThirstMultiplier", "Drain Rate. Higher = Dehydrate Faster. (Default: 1.0)", "str", "Game", "/Script/Vein.ServerSettings", "1.0"),
        ("Start Offset Days", "vein.Time.StartOffsetDays", "Days passed at start. (Default: 0)", "str", "Engine", "ConsoleVariables", "0"),
        ("Elec Shutoff Day", "vein.Calendar.ElectricalShutoffTimeDays", "Day grid fails. (Default: 46 = 1.5 Months)", "str", "Engine", "ConsoleVariables", "46"),
        ("Water Shutoff Day", "vein.Calendar.WaterShutoffTimeDays", "Day water fails. (Default: 30 = 1 Month)", "str", "Engine", "ConsoleVariables", "30"),
    ],
    "Hardcore & PVP": [
        ("Enable PvP", "vein.PvP", "Player vs Player combat. (Default: True)", "bool", "Engine", "ConsoleVariables", True),
        ("Permadeath", "vein.Permadeath", "Character deleted on death. (Default: False)", "bool", "Engine", "ConsoleVariables", False),
        ("Iron Man Mode", "vein.NoSaves", "No manual saves allowed. (Default: False)", "bool", "Engine", "ConsoleVariables", False),
        ("Base Damage", "vein.BaseDamage", "Can bases be damaged by anything? (Default: True)", "bool", "Engine", "ConsoleVariables", True),
        ("Player Raid Base", "vein.BuildObjectPvP", "Can players damage bases? (Default: True)", "bool", "Engine", "ConsoleVariables", True),
        ("Structure Decay", "vein.BuildObjectDecay", "Abandoned structures decay? (Default: True)", "bool", "Engine", "ConsoleVariables", True),
        ("Decay Interval", "vein.UtilityCabinet.Interval", "Decay tick in hours. (Default: 4.0)", "str", "Engine", "ConsoleVariables", "4.0"),
        ("Offline Protection", "vein.OfflineRaidProtection", "Reduce offline dmg. (Default: False)", "bool", "Engine", "ConsoleVariables", False),
        ("Pickpocketing", "vein.AllowPickpocketing", "Steal inventory? (Default: True)", "bool", "Engine", "ConsoleVariables", True),
        ("Headshot Mult", "vein.HeadshotDamageMultiplier", "Dmg Multiplier. (Default: 1.9)", "str", "Engine", "ConsoleVariables", "1.9"),
    ],
    "Zombies (The Horde)": [
        ("Zombie Health", "vein.Zombies.Health", "Base HP. Higher = Tankier. (Default: 40)", "str", "Engine", "ConsoleVariables", "40"),
        ("Headshots Only", "vein.Zombies.HeadshotOnly", "Zombies only die from headshots. (Default: False)", "bool", "Engine", "ConsoleVariables", False),
        ("Spawn Density", "vein.AISpawner.SpawnCapMultiplierZombie", "Higher = More Zombies. (Default: 1.0)", "str", "Engine", "ConsoleVariables", "1.0"),
        ("Horde Mode", "vein.AISpawner.Hordes.Enabled", "Enable random roaming hordes? (Default: True)", "bool", "Engine", "ConsoleVariables", True),
        ("Always Turn", "vein.AlwaysBecomeZombie", "Players turn on death. (Default: True)", "bool", "Engine", "ConsoleVariables", True),
        ("Can Climb", "vein.Zombies.CanClimb", "Zombies climb walls. (Default: True)", "bool", "Engine", "ConsoleVariables", True),
        ("Infection Chance", "vein.ZombieInfectionChance", "Prob on Hit (0.01 = 1%). (Default: 0.01)", "str", "Engine", "ConsoleVariables", "0.01"),
        ("Damage Mult", "vein.Zombies.DamageMultiplier", "Damage Output. (Default: 1.0)", "str", "Engine", "ConsoleVariables", "1.0"),
        ("Hearing Mult", "vein.Zombies.HearingMultiplier", "Detection Range. (Default: 1.0)", "str", "Engine", "ConsoleVariables", "1.0"),
        ("Sight Mult", "vein.Zombies.SightMultiplier", "Vision Range. (Default: 1.0)", "str", "Engine", "ConsoleVariables", "1.0"),
        ("Speed Mult", "vein.Zombies.SpeedMultiplier", "Global Speed. (Default: 1.0)", "str", "Engine", "ConsoleVariables", "1.0"),
        ("Stagger Chance", "vein.StaggerChance", "Chance on hit (0.1 = 10%). (Default: 0.1)", "str", "Engine", "ConsoleVariables", "0.1"),
        ("Stun Chance", "vein.StunLockChance", "Chance on hit (0.6 = 60%). (Default: 0.6)", "str", "Engine", "ConsoleVariables", "0.6"),
        ("Walker %", "vein.AISpawner.ZombieWalkerPercentage", "0.8 = 80% Walkers. (Default: 0.8)", "str", "Engine", "ConsoleVariables", "0.8"),
    ]
}