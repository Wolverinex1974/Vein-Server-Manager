# Vein Server Manager
Need help - [Join the Support Discord](https://pages.github.com/)  
Published / Distributed at [Nexus Mods](https://www.nexusmods.com/vein/mods/101?tab=description)
 
## 🚀 INTRODUCTION
Stop messing with batch files. Stop manually editing confusing INI text files.  The Vein Server Manager is a standalone tool designed to make hosting, configuring, and protecting your Vein server effortless. Whether you are a complete beginner or a veteran host, this tool handles the heavy lifting so you can focus on surviving.  


## 📥 INSTALLATION
1. Download VeinServerManager.exe from the "Files" tab.
2. Place it in a folder where you want your server to live (e.g., C:\VeinServer).
3. Important: Keep favicon.ico in the same folder as the .exe if included.
4. Run the Manager.
5. Follow the Wizard to install the server files.
6. (Optional) Go to the "Integrations" tab to set up your Discord Bot Token for the Live Status Board.


## 🤖 Discord Remote Control (New in v4.8)
- Manage your server without logging into the host PC!
1. Get a Bot Token from the Discord Developer Portal.
2. Get your Channel ID (Right-click a channel in Discord -> Copy ID).
3. Paste them into the Manager's "Integrations" tab.
### Discord Commands:
- `!status` : Check if server is Online/Offline + RAM usage.
- `!restart` : Graceful reboot (warns players -> saves -> restarts).
- `!backup` :Create a zip backup instantly.
- (Note: The bot runs inside the Manager app. The Manager must be open for commands to work.)


## ⚡ KEY FEATURES
- Auto-Install Wizard
- Detects if you are missing SteamCMD or the Game Files and automatically downloads/installs them for you. No command line needed.
- GUI Configuration (Visual Editor)
- Edit gameplay settings with simple text boxes, dropdowns, and checkboxes. Change Day/Night speed, Zombie Difficulty, Loot Scarcity, and Max Players without ever opening a text file.
- Now includes support for Zombie Speed Multipliers, XP Rates, and Vehicle Collision Damage.
- Safety & Recovery
- Includes a "Keep Alive" Watchdog. If your server crashes or freezes, the Manager detects it and automatically restarts the process. It now includes "Auto-Repair" logic to validate server files if an update fails.
- Reactive Backups
- Never lose progress. The system creates a zipped backup of your world every time the server stops or restarts.
- Multi-Instance Support
- Run a "Live" server and a "Test" server on the same machine? The Manager now intelligently handles startup tasks so multiple instances can auto-start simultaneously on Windows boot.
- Diagnostics 2.0
- Run a "Health Check" to verify your Ports (7777/27015) are actually listening and that Windows Firewall isn't blocking the connection.

### 🤖 Discord Live Status Board  
- Stop spamming chat commands. The Manager now maintains a Single, Self-Updating Pinned Message in your Discord channel.  
- Real-Time Dashboard: Updates every 60 seconds with Server Status, IP, Uptime, and RAM usage.  
- Live Player List: See exactly who is online directly from Discord.  
- Zero Spam: It edits one message instead of filling your chat history.  

### 📡 Real-Time Telemetry
- Chat Relay: In-game Global Chat is mirrored to your Discord via Webhooks. Monitor your community from your phone.
- Kill Feed: Death events are tracked and broadcasted to Discord automatically.

### 📦 The Modding Suite
- A dedicated interface for safely managing server-side mods (.pak files).
- Drag-and-Drop Installer: Install mods easily without navigating complex folder structures.
- Safe Toggle System: Enable or disable mods instantly without deleting the files.
- The "Safe Config" Editor: A specialized editor for Game.ini that creates a "Vanilla Shield." It hides critical server settings to prevent accidental corruption while allowing you to surgically edit Mod Config settings.

### 🧠 Log Intelligence
- Smart Highlighting: The log viewer is no longer a wall of text. Events are color-coded (Chat=Cyan, Errors=Red, Warnings=Gold, Joins=Green).
- Active Filtering: Instantly filter the log history with a search bar to find exactly what you need.


## 🗺️ THE ROADMAP (Road to v5.2.0)The next major update will focus on automation, integrity, and user experience.
1. SteamCMD Auto-Repair (The Watchdog 2.0)
    - If an update hangs or corrupts, the Manager will automatically kill the process and trigger a validation command to repair the server without human intervention.
2. Player Management Overhaul  
    - Unified Tab: Merging "Online Players" and "Banned Players" into a single, powerful interface.
    - Moderator Support: Adding a new "Regular Admin" list (distinct from Super Admins) to allow for game moderators who cannot change server settings.
    - Unban Button: Adding a GUI button to remove players from the ban list.
3. Quality of Life
    - System Tray: Options to "Minimize to Tray" and "Start Minimized" to keep your desktop clean.
    - Whitelist Support: Implementation of a soft-whitelist to restrict server access to specific SteamIDs.
4. Visual Analytics
    - Simple graphs to monitor CPU and RAM usage over time, helping admins detect memory leaks before they cause a crash.


## ⚠️ CURRENT LIMITATIONS
- NO RCON SUPPORT YET
- The game developers have not yet fully implemented the RCON protocol in the dedicated server executable. Remote administration (Kicking/Banning players via console) is currently disabled to prevent instability. Please use in-game admin tools.


## Useful Vein Links:  
> Official Documentation - 🗃️ https://ramjet.notion.site/dedicated-servers#17ef9ec29f17805b9942f9fd29d5187f  
> The Game - 🕹️ https://store.steampowered.com/app/1857950/VEIN/  
> Dedicated server info - 🖥️ https://steamdb.info/app/2131400  
> Linux Manager - https://github.com/warmbo/vein-server  


## DISCLAIMER:  
Vein Server Manager is an unofficial, open-source tool and is not affiliated with or endorsed by the developers of VEIN. This software is provided "as is" without warranty of any kind. Use at your own risk. The developer is not responsible for any data loss, server corruption, or configuration errors. Always maintain independent backups of your server files.
