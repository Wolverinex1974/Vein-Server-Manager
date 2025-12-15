# gui.py
import tkinter as tk
from tkinter import ttk
import constants
import webbrowser

def setup_styles():
    # Placeholder if we want custom styles later
    pass

def create_main_layout(app):
    """Builds the top bar, dashboard, and tabs container."""
    
    # 1. Top Bar (Path)
    top_bar = tk.Frame(app.root, padx=10, pady=5)
    top_bar.pack(fill="x", side="top")
    tk.Label(top_bar, text="Server Path:").pack(side="left")
    app.path_entry = tk.Entry(top_bar)
    app.path_entry.pack(side="left", fill="x", expand=True, padx=5)
    tk.Button(top_bar, text="Browse...", command=app.browse_path).pack(side="left")

    # 2. Dashboard (Control Panel)
    id_frame = tk.Frame(app.root, padx=15, pady=5)
    id_frame.pack(fill="x", side="top")
    
    app.status_canvas = tk.Canvas(id_frame, width=20, height=20, highlightthickness=0)
    app.status_dot = app.status_canvas.create_oval(2, 2, 18, 18, fill="red", outline="")
    app.status_canvas.pack(side="left", pady=5)
    
    # Large Header
    app.header_title_label = tk.Label(id_frame, text="Vein Server", font=("Segoe UI", 16, "bold"), fg=app.text_color)
    app.header_title_label.pack(side="left", padx=10)

    # Buttons
    app.start_button = tk.Button(id_frame, text="Start", width=10, bg="#ddffdd", command=lambda: app.start_server("USER"))
    app.start_button.pack(side="left", padx=5)
    
    app.stop_button = tk.Button(id_frame, text="Stop", width=10, bg="#ffdddd", command=app.stop_server, state="disabled")
    app.stop_button.pack(side="left", padx=5)
    
    app.restart_button = tk.Button(id_frame, text="Restart", width=10, command=app.restart_server, state="disabled")
    app.restart_button.pack(side="left", padx=5)
    
    app.keep_alive_checkbox = tk.Checkbutton(id_frame, text="Keep Alive", variable=app.keep_alive_var)
    app.keep_alive_checkbox.pack(side="left", padx=10)
    
    app.save_button = tk.Button(id_frame, text="💾 SAVE", bg="#e1f5fe", command=app.save_all_settings)
    app.save_button.pack(side="right", padx=5)

    # 3. Info Bar (Status Line)
    info_bar = tk.Frame(app.root, padx=10, pady=2, bg="#e0e0e0", relief="sunken", bd=1)
    info_bar.pack(fill="x", side="top")
    
    app.status_text_label = tk.Label(info_bar, text="Status: OFFLINE", bg="#e0e0e0", fg="red")
    app.status_text_label.pack(side="left", padx=10)
    
    app.pid_label = tk.Label(info_bar, text="PID: -", bg="#e0e0e0")
    app.pid_label.pack(side="left", padx=10)
    
    app.version_label = tk.Label(info_bar, text="Build: -", bg="#e0e0e0")
    app.version_label.pack(side="left", padx=10)
    
    app.player_count_label = tk.Label(info_bar, text="Players: - / -", bg="#e0e0e0")
    app.player_count_label.pack(side="left", padx=10)
    
    app.crash_label = tk.Label(info_bar, text="Crashes: 0", bg="#e0e0e0")
    app.crash_label.pack(side="left", padx=10)
    tk.Button(info_bar, text="Reset", font=("Arial", 7), command=app.reset_crash_counter).pack(side="left")

    # Update Button (Hidden by default)
    app.update_notify_btn = tk.Button(info_bar, text="⬇ Update Available!", bg="orange", fg="black", font=("Segoe UI", 9, "bold"), command=lambda: webbrowser.open(constants.LINK_GITHUB_RELEASES))
    
    # Author
    app.author_label = tk.Label(info_bar, text=f"Dev: {constants.AUTHOR_NAME}", bg="#e0e0e0", fg="#0056b3", font=("Segoe UI", 8, "bold"), cursor="hand2")
    app.author_label.pack(side="right", padx=10)
    app.author_label.bind("<Button-1>", lambda e: webbrowser.open(constants.LINK_DISCORD_MAIN))
    
    tk.Button(info_bar, text="📂 Logs", font=("Arial", 8), command=app.open_logs_folder).pack(side="right", padx=5)

    # 4. Scrollable Container
    container = tk.Frame(app.root)
    container.pack(fill="both", expand=True)
    app.canvas = tk.Canvas(container)
    scrollbar = ttk.Scrollbar(container, orient="vertical", command=app.canvas.yview)
    app.scrollable_frame = ttk.Frame(app.canvas)
    
    app.scrollable_frame.bind("<Configure>", lambda e: app.canvas.configure(scrollregion=app.canvas.bbox("all")))
    app.canvas.create_window((0, 0), window=app.scrollable_frame, anchor="nw")
    app.canvas.configure(yscrollcommand=scrollbar.set)
    
    app.canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    app.canvas.bind_all("<MouseWheel>", lambda e: app.canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
    
    # 5. Build Tabs
    build_tabs(app)

def build_tabs(app):
    app.notebook = ttk.Notebook(app.scrollable_frame)
    app.notebook.pack(fill="both", expand=True, padx=10, pady=5)
    
    # Tab 1: Main
    t_main = ttk.Frame(app.notebook)
    app.notebook.add(t_main, text="Main Server Settings")
    _build_main_tab(app, t_main)
    
    # Tab 2: Gameplay (Vertical)
    t_game = ttk.Frame(app.notebook)
    app.notebook.add(t_game, text="Gameplay")
    _build_gameplay_tab(app, t_game)
    
    # Tab 3: Players
    t_play = ttk.Frame(app.notebook)
    app.notebook.add(t_play, text="Online Players")
    _build_players_tab(app, t_play)
    
    # Tab 4: Scheduler
    t_sched = ttk.Frame(app.notebook)
    app.notebook.add(t_sched, text="Restart Schedule")
    _build_scheduler_tab(app, t_sched)
    
    # Tab 5: Logs
    t_logs = ttk.Frame(app.notebook)
    app.notebook.add(t_logs, text="Live Log Viewer")
    _build_logs_tab(app, t_logs)
    
    # Tab 6: Management
    t_mgmt = ttk.Frame(app.notebook)
    app.notebook.add(t_mgmt, text="Server Management")
    _build_mgmt_tab(app, t_mgmt)
    
    # Tab 7: Backups
    t_back = ttk.Frame(app.notebook)
    app.notebook.add(t_back, text="Backups")
    _build_backup_tab(app, t_back)
    
    # Tab 8: About
    t_about = ttk.Frame(app.notebook)
    app.notebook.add(t_about, text="About & Community")
    _build_about_tab(app, t_about)

def _build_main_tab(app, parent):
    tk.Label(parent, text="Map Selection:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
    app.map_combobox = ttk.Combobox(parent, width=57, values=["/Game/Vein/Maps/ChamplainValley?listen"])
    app.map_combobox.grid(row=0, column=1, columnspan=2, padx=5)
    
    fields = [
        ("Server Name (Display):", "server_name_entry", 50),
        ("Server Description:", "server_desc_entry", 50),
        ("Session Name (Save File):", "session_name_entry", 50),
        ("Server Password:", "server_password_entry", 30),
        ("Game Port (UDP):", "port_entry", 10),
        ("Query Port (UDP):", "query_port_entry", 10),
        ("Max Players:", "players_entry", 10),
    ]
    
    for i, (label, attr, width) in enumerate(fields, start=1):
        tk.Label(parent, text=label).grid(row=i, column=0, sticky="w", padx=10)
        entry = tk.Entry(parent, width=width)
        if "Port" in label or "Players" in label:
            entry.config(validate='key', validatecommand=app.vcmd)
        if "Password" in label:
            entry.config(show="*")
        setattr(app, attr, entry)
        entry.grid(row=i, column=1, columnspan=2, sticky="w", padx=5)

    ttk.Separator(parent, orient='horizontal').grid(row=9, columnspan=4, sticky='ew', pady=10)
    
    app.rcon_checkbox = tk.Checkbutton(parent, text="Enable RCON (WIP)", variable=app.rcon_enabled_var, fg="grey")
    app.rcon_checkbox.grid(row=10, column=0, columnspan=2, sticky="w", padx=10)
    
    tk.Label(parent, text="RCON Port:", fg="grey").grid(row=11, column=0, sticky="w", padx=10)
    app.rcon_port_entry = tk.Entry(parent, width=10, validate='key', validatecommand=app.vcmd)
    app.rcon_port_entry.grid(row=11, column=1, sticky="w", padx=5)
    
    tk.Label(parent, text="RCON Password:", fg="grey").grid(row=12, column=0, sticky="w", padx=10)
    app.rcon_password_entry = tk.Entry(parent, width=40, show="*")
    app.rcon_password_entry.grid(row=12, column=1, columnspan=2, sticky="w", padx=5)
    
    ttk.Separator(parent, orient='horizontal').grid(row=13, columnspan=4, sticky='ew', pady=10)
    
    app.http_api_checkbox = tk.Checkbutton(parent, text="Enable HTTP API", variable=app.http_api_enabled_var)
    app.http_api_checkbox.grid(row=14, column=0, columnspan=2, sticky="w", padx=10)
    
    tk.Label(parent, text="HTTP Port:").grid(row=15, column=0, sticky="w", padx=10)
    app.http_api_port_entry = tk.Entry(parent, width=10, validate='key', validatecommand=app.vcmd)
    app.http_api_port_entry.grid(row=15, column=1, sticky="w", padx=5)
    
    ttk.Separator(parent, orient='horizontal').grid(row=16, columnspan=4, sticky='ew', pady=15)
    
    tk.Label(parent, text="Super Admin SteamIDs:").grid(row=17, column=0, sticky="w", padx=10)
    app.admin_ids_var = tk.StringVar()
    app.admin_id_entry = tk.Entry(parent, textvariable=app.admin_ids_var, width=50)
    app.admin_id_entry.grid(row=17, column=1, columnspan=2, sticky="w", padx=5)

def _build_gameplay_tab(app, parent):
    paned = tk.PanedWindow(parent, orient=tk.HORIZONTAL)
    paned.pack(fill="both", expand=True)
    menu_frame = tk.Frame(paned, width=160, bg="#f0f0f0", relief="sunken", bd=1)
    menu_frame.pack_propagate(False)
    content_frame = tk.Frame(paned, padx=10, pady=10)
    paned.add(menu_frame)
    paned.add(content_frame)

    first_category = None
    def show_frame(cat_name):
        for name, btn in app.menu_buttons.items():
            btn.config(bg="white" if name == cat_name else "#f0f0f0", relief="sunken" if name == cat_name else "flat")
        for f in app.gameplay_frames.values(): f.pack_forget()
        if cat_name in app.gameplay_frames: app.gameplay_frames[cat_name].pack(fill="both", expand=True)

    for category, settings_list in constants.GAMEPLAY_DEFINITIONS.items():
        if not first_category: first_category = category
        btn = tk.Button(menu_frame, text=category, anchor="w", padx=10, pady=8, font=("Segoe UI", 9), command=lambda c=category: show_frame(c))
        btn.pack(fill="x")
        app.menu_buttons[category] = btn
        
        cat_frame = tk.Frame(content_frame)
        app.gameplay_frames[category] = cat_frame
        tk.Label(cat_frame, text=category, font=("Segoe UI", 12, "bold", "underline")).pack(anchor="w", pady=(0, 15))
        
        for (label_text, key, tooltip, type_str, file_type, section, default_val) in settings_list:
            row = tk.Frame(cat_frame); row.pack(fill="x", pady=2)
            tk.Label(row, text=label_text, width=25, anchor="w").pack(side="left")
            widget = None
            if type_str == "bool":
                var = tk.BooleanVar(value=default_val)
                widget = tk.Checkbutton(row, variable=var)
                widget.pack(side="left")
            elif type_str == "combo_scarcity":
                var = tk.StringVar(value="Standard (2.0)")
                widget = ttk.Combobox(row, textvariable=var, width=18, state="readonly", 
                                      values=["Infinite (0.0)", "More Loot (1.0)", "Standard (2.0)", "Less Loot (3.0)", "Impossible (4.0)"])
                widget.pack(side="left")
            else:
                var = tk.StringVar(value=str(default_val))
                widget = tk.Entry(row, textvariable=var, width=18)
                widget.pack(side="left")
            tk.Label(row, text=tooltip, fg="grey", anchor="w", width=50).pack(side="left", padx=10)
            app.gameplay_vars[key] = {'var': var, 'type': type_str, 'file': file_type, 'section': section, 'widget': widget, 'default': default_val}
            
    if first_category: show_frame(first_category)

def _build_players_tab(app, parent):
    f_frame = tk.Frame(parent, pady=5); f_frame.pack(fill='x', padx=10)
    tk.Label(f_frame, text="View Mode:").pack(side='left')
    app.player_filter_menu = ttk.Combobox(f_frame, textvariable=app.player_filter_var, values=["Online Now", "History (All Time)"], state="readonly")
    app.player_filter_menu.pack(side='left', padx=10)
    app.player_filter_menu.bind("<<ComboboxSelected>>", lambda e: app.refresh_player_list_ui())
    pl_cont = tk.LabelFrame(parent, text="Players", padx=10, pady=10); pl_cont.pack(fill='both', expand=True, padx=10, pady=10)
    app.players_listbox = tk.Listbox(pl_cont, font=("Helvetica", 10), height=15); app.players_listbox.pack(fill='both', expand=True, side='left')
    pl_scroll = tk.Scrollbar(pl_cont, orient="vertical", command=app.players_listbox.yview); pl_scroll.pack(side="right", fill="y")
    app.players_listbox.config(yscrollcommand=pl_scroll.set)

def _build_scheduler_tab(app, parent):
    d_grp = tk.LabelFrame(parent, text="Fixed Time Schedule", padx=10, pady=10); d_grp.pack(fill='x', padx=10, pady=10)
    tk.Checkbutton(d_grp, text="Enable Time Schedule", variable=app.sched_daily_enabled, font=("Helvetica", 9, "bold")).pack(anchor='w')
    d_f = tk.Frame(d_grp); d_f.pack(fill='x', pady=5)
    for i, n in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]): 
        tk.Checkbutton(d_f, text=n, variable=app.sched_days_vars[i]).pack(side='left', padx=5)
    t_f = tk.Frame(d_grp); t_f.pack(fill='x', pady=5)
    tk.Label(t_f, text="Restart Times (HH:MM):").pack(side='left')
    app.sched_time_entry = tk.Entry(t_f, width=40); app.sched_time_entry.pack(side='left', padx=5)
    
    i_grp = tk.LabelFrame(parent, text="Uptime Limit", padx=10, pady=10); i_grp.pack(fill='x', padx=10, pady=10)
    tk.Checkbutton(i_grp, text="Enable Uptime Limit", variable=app.sched_interval_enabled, font=("Helvetica", 9, "bold")).pack(anchor='w')
    i_f = tk.Frame(i_grp); i_f.pack(fill='x', pady=5)
    tk.Label(i_f, text="Restart after").pack(side='left')
    app.sched_interval_entry = tk.Entry(i_f, width=5); app.sched_interval_entry.pack(side='left', padx=5)
    tk.Label(i_f, text="hours").pack(side='left')
    
    app.sched_status_label = tk.Label(parent, text="Scheduler Status: Waiting...", font=("Courier New", 10))
    app.sched_status_label.pack(pady=10)

def _build_logs_tab(app, parent):
    l_bar = tk.Frame(parent); l_bar.pack(fill='x', padx=5, pady=2)
    tk.Label(l_bar, text="Manager Events Log", font=("Segoe UI", 8, "bold"), fg="grey").pack(side='left')
    tk.Button(l_bar, text="Purge Logs", font=("Segoe UI", 8), bg="#ffebee", command=app.purge_manager_logs).pack(side='right')
    app.log_text = tk.Text(parent, state='disabled', wrap='word', bg='black', fg='#00ff00', font=("Courier New", 9), height=20)
    app.log_text.pack(fill="both", expand=True, padx=5, pady=5)

def _build_mgmt_tab(app, parent):
    sc_frame = tk.LabelFrame(parent, text="SteamCMD Path", padx=10, pady=5); sc_frame.pack(fill='x', padx=10, pady=10)
    app.steamcmd_path_entry = tk.Entry(sc_frame); app.steamcmd_path_entry.pack(side='left', fill='x', expand=True, padx=5)
    tk.Button(sc_frame, text="Browse...", command=app.browse_steamcmd).pack(side='left', padx=5)
    
    up_frame = tk.LabelFrame(parent, text="Smart Auto-Updater", padx=10, pady=5, fg="#0056b3"); up_frame.pack(fill='x', padx=10, pady=5)
    r1 = tk.Frame(up_frame); r1.pack(fill='x', pady=2)
    tk.Checkbutton(r1, text="Enable Auto-Updater", variable=app.auto_update_enabled).pack(side='left')
    tk.Checkbutton(r1, text="Passive Mode (Wait for 0 Players)", variable=app.auto_update_passive).pack(side='left', padx=10)
    r2 = tk.Frame(up_frame); r2.pack(fill='x', pady=2)
    tk.Label(r2, text="Steam Branch:").pack(side='left')
    tk.Entry(r2, textvariable=app.steam_branch_var, width=15).pack(side='left', padx=5)
    app.updater_status_label = tk.Label(r2, text="Status: Idle", fg="grey"); app.updater_status_label.pack(side='right', padx=10)
    
    bf = tk.Frame(parent); bf.pack(fill='x', padx=10, pady=5)
    app.update_button = tk.Button(bf, text="Manual Update", command=app.start_steamcmd_update); app.update_button.pack(side='left', padx=5)
    app.validate_button = tk.Button(bf, text="Manual Validate", command=app.start_steamcmd_validate); app.validate_button.pack(side='left', padx=5)

    df = tk.LabelFrame(parent, text="Notifications (Discord)", padx=10, pady=5, fg="#7289da"); df.pack(fill='x', padx=10, pady=5)
    tk.Checkbutton(df, text="Enable Discord Webhooks", variable=app.discord_enabled).pack(anchor='w')
    dr = tk.Frame(df); dr.pack(fill='x', pady=2)
    tk.Label(dr, text="Webhook URL:").pack(side='left')
    tk.Entry(dr, textvariable=app.discord_webhook_url).pack(side='left', fill='x', expand=True, padx=5)
    dr2 = tk.Frame(df); dr2.pack(fill='x', pady=2)
    tk.Label(dr2, text="Community URL:").pack(side='left')
    tk.Entry(dr2, textvariable=app.community_url).pack(side='left', fill='x', expand=True, padx=5)

    cf = tk.LabelFrame(parent, text="SteamCMD Output", padx=5, pady=5); cf.pack(fill='both', expand=True, padx=10, pady=10)
    app.steamcmd_console_output = tk.Text(cf, state='disabled', wrap='word', bg='black', fg='#00ff00', font=("Courier New", 9), height=10); app.steamcmd_console_output.pack(fill='both', expand=True)

def _build_backup_tab(app, parent):
    bs = tk.LabelFrame(parent, text="Backup Settings", padx=10, pady=5); bs.pack(fill='x', padx=10, pady=5)
    tk.Label(bs, text="Format:").pack(side='left')
    app.backup_format_entry = tk.Entry(bs, width=30); app.backup_format_entry.pack(side='left', padx=5)
    tk.Label(bs, text="| Keep:").pack(side='left')
    app.backup_retention_spinbox = tk.Spinbox(bs, from_=1, to=100, width=3); app.backup_retention_spinbox.pack(side='left')
    
    ba = tk.LabelFrame(parent, text="Automated", padx=10, pady=5); ba.pack(fill='x', padx=10, pady=5)
    tk.Checkbutton(ba, text="Enable Reactive Backups", variable=app.reactive_backup_enabled).pack(side='left')
    tk.Checkbutton(ba, text="Backup on Stop", variable=app.backup_on_stop).pack(side='left', padx=10)
    
    blf = tk.Frame(parent); blf.pack(fill='both', expand=True, padx=10, pady=5)
    app.backup_list = tk.Listbox(blf, bg='#f0f0f0', font=("Courier New", 10), height=10); app.backup_list.pack(side='left', fill='both', expand=True)
    bac = tk.Frame(blf); bac.pack(side='left', fill='y', padx=10)
    app.create_backup_button = tk.Button(bac, text="Create Backup", command=app.start_manual_backup); app.create_backup_button.pack(pady=5, fill='x')
    app.open_backup_folder_button = tk.Button(bac, text="Open Folder", command=app.open_backup_folder); app.open_backup_folder_button.pack(pady=5, fill='x')

def _build_about_tab(app, parent):
    c = tk.Frame(parent, padx=20, pady=20); c.pack(fill='both', expand=True)
    tk.Label(c, text="Vein Server Manager", font=("Segoe UI", 20, "bold")).pack(pady=5)
    tk.Label(c, text=f"{constants.MANAGER_VERSION}", fg="grey").pack()
    tk.Label(c, text=f"Created by {constants.AUTHOR_NAME}", font=("Segoe UI", 12)).pack(pady=(0, 20))
    bf = tk.Frame(c); bf.pack(pady=10)
    def link(u): webbrowser.open(u)
    tk.Button(bf, text="Join Paradoxal Discord", bg="#7289da", fg="white", font=("bold"), width=35, command=lambda: link(constants.LINK_DISCORD_MAIN)).pack(pady=5)
    tk.Button(bf, text="Vein Modding Community", bg="#2c2f33", fg="white", width=35, command=lambda: link(constants.LINK_DISCORD_MODS)).pack(pady=5)
    tk.Button(bf, text="View on Nexus Mods", bg="#e67e22", fg="white", font=("bold"), width=35, command=lambda: link(constants.LINK_NEXUS_MODS)).pack(pady=5)
    tk.Button(bf, text="Source Code (GitHub)", bg="black", fg="white", width=35, command=lambda: link(constants.LINK_GITHUB)).pack(pady=5)
    tk.Button(bf, text="❤ Support Development (Ko-fi)", bg="#FFD700", fg="black", font=("bold"), width=35, command=lambda: link(constants.LINK_KOFI)).pack(pady=(15, 5))