# --- VERSION & IDENTITY ---
# MANAGER_VERSION = "v5.1.4 (Integrity & Polish)"

# gui.py
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import constants
import webbrowser
import os
import glob
import logic 

def create_main_layout(app):
    top_bar = tk.Frame(app.root, padx=10, pady=5)
    top_bar.pack(fill="x", side="top")
    tk.Label(top_bar, text="Server Path:").pack(side="left")
    app.path_entry = tk.Entry(top_bar)
    app.path_entry.pack(side="left", fill="x", expand=True, padx=5)
    tk.Button(top_bar, text="Browse...", command=app.browse_path).pack(side="left")

    id_frame = tk.Frame(app.root, padx=15, pady=5)
    id_frame.pack(fill="x", side="top")
    app.status_canvas = tk.Canvas(id_frame, width=20, height=20, highlightthickness=0)
    app.status_dot = app.status_canvas.create_oval(2, 2, 18, 18, fill="red", outline="")
    app.status_canvas.pack(side="left", pady=5)
    app.header_title_label = tk.Label(id_frame, text="Vein Server", font=("Segoe UI", 16, "bold"), fg="#2c3e50")
    app.header_title_label.pack(side="left", padx=10)
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

    info_bar = tk.Frame(app.root, padx=10, pady=2, bg="#e0e0e0", relief="sunken", bd=1)
    info_bar.pack(fill="x", side="top")
    app.status_text_label = tk.Label(info_bar, text="Status: OFFLINE", bg="#e0e0e0", fg="red")
    app.status_text_label.pack(side="left", padx=10)
    app.pid_label = tk.Label(info_bar, text="PID: -", bg="#e0e0e0")
    app.pid_label.pack(side="left", padx=10)
    
    # --- NEW FEATURE (v5.1.4): Player Count Label ---
    app.player_count_label = tk.Label(info_bar, text="Players: 0/0", bg="#e0e0e0", fg="#0056b3")
    app.player_count_label.pack(side="left", padx=10)
    # ------------------------------------------------
    
    app.version_label = tk.Label(info_bar, text=f"Build: {app.current_build_id}", bg="#e0e0e0")
    app.version_label.pack(side="left", padx=10)
    app.crash_label = tk.Label(info_bar, text="Crashes: 0", bg="#e0e0e0")
    app.crash_label.pack(side="left", padx=10)
    tk.Button(info_bar, text="Reset", font=("Arial", 7), command=app.reset_crash_counter).pack(side="left")
    
    app.update_notify_btn = tk.Button(info_bar, text="Checking...", bg="gray", fg="black", font=("Segoe UI", 9, "bold"), command=lambda: webbrowser.open(constants.LINK_GITHUB_RELEASES))
    app.update_notify_btn.pack(side="left", padx=10)

    grip = ttk.Sizegrip(info_bar)
    grip.pack(side="right", anchor="se")
    app.author_label = tk.Label(info_bar, text=f"Dev: {constants.AUTHOR_NAME}", bg="#e0e0e0", fg="#0056b3", font=("Segoe UI", 8, "bold"), cursor="hand2")
    app.author_label.pack(side="right", padx=10)
    app.author_label.bind("<Button-1>", lambda e: webbrowser.open(constants.LINK_DISCORD_MAIN))
    tk.Button(info_bar, text="📂 Logs", font=("Arial", 8), command=app.open_logs_folder).pack(side="right", padx=5)
    app.accent_line = tk.Frame(app.root, height=3, bg="#3498db") 
    app.accent_line.pack(fill="x", side="top")

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
    build_tabs(app)

def build_tabs(app):
    app.notebook = ttk.Notebook(app.scrollable_frame)
    app.notebook.pack(fill="both", expand=True, padx=10, pady=5)
    app.notebook.add(ttk.Frame(app.notebook), text="Main Settings"); _build_main_tab(app, app.notebook.nametowidget(app.notebook.tabs()[0]))
    app.notebook.add(ttk.Frame(app.notebook), text="Gameplay"); _build_gameplay_tab(app, app.notebook.nametowidget(app.notebook.tabs()[1]))
    app.notebook.add(ttk.Frame(app.notebook), text="Mods"); _build_mods_tab(app, app.notebook.nametowidget(app.notebook.tabs()[2]))
    app.notebook.add(ttk.Frame(app.notebook), text="Online Players"); _build_players_tab(app, app.notebook.nametowidget(app.notebook.tabs()[3]))
    app.notebook.add(ttk.Frame(app.notebook), text="Restart Schedule"); _build_scheduler_tab(app, app.notebook.nametowidget(app.notebook.tabs()[4]))
    app.notebook.add(ttk.Frame(app.notebook), text="Live Log Viewer"); _build_logs_tab(app, app.notebook.nametowidget(app.notebook.tabs()[5]))
    app.notebook.add(ttk.Frame(app.notebook), text="Server Management"); _build_mgmt_tab(app, app.notebook.nametowidget(app.notebook.tabs()[6]))
    app.notebook.add(ttk.Frame(app.notebook), text="Integrations"); _build_integrations_tab(app, app.notebook.nametowidget(app.notebook.tabs()[7]))
    app.notebook.add(ttk.Frame(app.notebook), text="Backups"); _build_backup_tab(app, app.notebook.nametowidget(app.notebook.tabs()[8]))
    app.notebook.add(ttk.Frame(app.notebook), text="Help / FAQ"); _build_help_tab(app, app.notebook.nametowidget(app.notebook.tabs()[9]))
    app.notebook.add(ttk.Frame(app.notebook), text="About"); _build_about_tab(app, app.notebook.nametowidget(app.notebook.tabs()[10]))

def _build_main_tab(app, parent):
    prof_frame = tk.LabelFrame(parent, text="Configuration Profiles", padx=10, pady=5, fg="#8e44ad")
    prof_frame.grid(row=0, column=0, columnspan=4, sticky="ew", padx=10, pady=10)
    tk.Label(prof_frame, text="Active Profile:").pack(side='left')
    app.profile_combobox = ttk.Combobox(prof_frame, textvariable=app.profile_var, state="readonly")
    app.profile_combobox.pack(side='left', padx=5, fill='x', expand=True)
    app.btn_prof_load = tk.Button(prof_frame, text="Load", bg="#ddffdd", command=app.load_selected_profile)
    app.btn_prof_load.pack(side='left', padx=2)
    app.btn_prof_save = tk.Button(prof_frame, text="Save", bg="#ffffcc", command=app.update_active_profile)
    app.btn_prof_save.pack(side='left', padx=2)
    tk.Button(prof_frame, text="Save As...", bg="#e1f5fe", command=app.save_new_profile).pack(side='left', padx=2)
    app.btn_prof_del = tk.Button(prof_frame, text="Delete", bg="#ffdddd", command=app.delete_profile)
    app.btn_prof_del.pack(side='left', padx=2)

    tk.Label(parent, text="Map Selection:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
    app.map_combobox = ttk.Combobox(parent, width=57, values=["/Game/Vein/Maps/ChamplainValley?listen"])
    app.map_combobox.grid(row=1, column=1, columnspan=2, padx=5)
    app.auto_update_start_check = tk.Checkbutton(parent, text="Update Server on Start", variable=app.auto_update_on_start_var, fg="#0056b3")
    app.auto_update_start_check.grid(row=1, column=3, sticky="w", padx=5)
    
    fields = [("Server Name:", "server_name_entry", 50), ("Description:", "server_desc_entry", 50), ("Session:", "session_name_entry", 50), ("Password:", "server_password_entry", 30), ("Game Port:", "port_entry", 10), ("Query Port:", "query_port_entry", 10), ("Max Players:", "players_entry", 10)]
    for i, (l, a, w) in enumerate(fields, start=2):
        tk.Label(parent, text=l).grid(row=i, column=0, sticky="w", padx=10)
        e = tk.Entry(parent, width=w)
        if "Port" in l or "Players" in l: e.config(validate='key', validatecommand=app.vcmd)
        if "Password" in l: e.config(show="*")
        setattr(app, a, e)
        e.grid(row=i, column=1, columnspan=2, sticky="w", padx=5)

    r_row = 10
    ttk.Separator(parent).grid(row=r_row, columnspan=4, sticky='ew', pady=10)
    app.rcon_checkbox = tk.Checkbutton(parent, text="Enable RCON", variable=app.rcon_enabled_var)
    app.rcon_checkbox.grid(row=r_row+1, column=0, columnspan=2, sticky="w", padx=10)
    app.rcon_port_entry = tk.Entry(parent, width=10); app.rcon_port_entry.grid(row=r_row+2, column=1, sticky="w")
    app.rcon_password_entry = tk.Entry(parent, width=40, show="*"); app.rcon_password_entry.grid(row=r_row+3, column=1, columnspan=2, sticky="w")
    
    h_row = r_row + 4
    ttk.Separator(parent).grid(row=h_row, columnspan=4, sticky='ew', pady=10)
    app.http_api_checkbox = tk.Checkbutton(parent, text="Enable HTTP API", variable=app.http_api_enabled_var)
    app.http_api_checkbox.grid(row=h_row+1, column=0, columnspan=2, sticky="w", padx=10)
    app.http_api_port_entry = tk.Entry(parent, width=10); app.http_api_port_entry.grid(row=h_row+2, column=1, sticky="w")
    
    a_row = h_row + 3
    ttk.Separator(parent).grid(row=a_row, columnspan=4, sticky='ew', pady=10)
    tk.Label(parent, text="Super Admin SteamIDs (Separate with commas):").grid(row=a_row+1, column=0, sticky="w", padx=10)
    app.admin_id_entry = tk.Entry(parent, textvariable=app.admin_ids_var, width=50); app.admin_id_entry.grid(row=a_row+1, column=1, columnspan=2, sticky="w", padx=5)

def _build_gameplay_tab(app, parent):
    paned = tk.PanedWindow(parent, orient=tk.HORIZONTAL)
    paned.pack(fill="both", expand=True)
    menu_frame = tk.Frame(paned, width=160, bg="#f0f0f0", relief="sunken", bd=1); menu_frame.pack_propagate(False)
    content_frame = tk.Frame(paned, padx=10, pady=10)
    paned.add(menu_frame); paned.add(content_frame)
    def show_frame(cat_name):
        for name, btn in app.menu_buttons.items():
            btn.config(bg="white" if name == cat_name else "#f0f0f0", relief="sunken" if name == cat_name else "flat")
        for f in app.gameplay_frames.values(): f.pack_forget()
        if cat_name in app.gameplay_frames: app.gameplay_frames[cat_name].pack(fill="both", expand=True)
    first = None
    for category, settings_list in constants.GAMEPLAY_DEFINITIONS.items():
        if not first: first = category
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
                widget = tk.Checkbutton(row, variable=var); widget.pack(side="left")
            elif type_str == "combo_scarcity":
                var = tk.StringVar(value="Standard (2.0)")
                widget = ttk.Combobox(row, textvariable=var, width=18, state="readonly", values=["Infinite (0.0)", "More Loot (1.0)", "Standard (2.0)", "Less Loot (3.0)", "Impossible (4.0)"]); widget.pack(side="left")
            else:
                var = tk.StringVar(value=str(default_val))
                widget = tk.Entry(row, textvariable=var, width=18); widget.pack(side="left")
            tk.Label(row, text=tooltip, fg="grey", anchor="w", width=50).pack(side="left", padx=10)
            app.gameplay_vars[key] = {'var': var, 'type': type_str, 'file': file_type, 'section': section, 'widget': widget, 'default': default_val}
    tk.Button(menu_frame, text="↺ Reset to Vanilla", bg="#ffebee", fg="red", command=app.reset_gameplay_to_vanilla).pack(side="bottom", fill="x", padx=10, pady=20)
    if first: show_frame(first)

def _build_mods_tab(app, parent):
    paned = tk.PanedWindow(parent, orient=tk.HORIZONTAL)
    paned.pack(fill="both", expand=True, padx=5, pady=5)
    
    # LEFT: File Manager
    left_f = tk.LabelFrame(paned, text="Installed Mods (~mods)", padx=5, pady=5, width=300)
    paned.add(left_f)
    
    # 1. TOP: Install Button
    btn_box = tk.Frame(left_f)
    btn_box.pack(side='top', fill='x', pady=(0,5))
    app.btn_mod_install = tk.Button(btn_box, text="+ Install Mod (.pak)", bg="#ddffdd", command=app.install_mod_dialog)
    app.btn_mod_install.pack(fill='x')
    
    # 2. BOTTOM: Action Buttons (Toggle, Delete, Refresh)
    action_box = tk.Frame(left_f)
    action_box.pack(side='bottom', fill='x', pady=(5,0))
    sub_act = tk.Frame(action_box)
    sub_act.pack(fill='x')
    app.btn_mod_toggle = tk.Button(sub_act, text="Toggle (On/Off)", command=app.toggle_selected_mod, state="disabled")
    app.btn_mod_toggle.pack(side='left', fill='x', expand=True, padx=2)
    app.btn_mod_del = tk.Button(sub_act, text="Delete", fg="red", command=app.delete_selected_mod, state="disabled")
    app.btn_mod_del.pack(side='left', fill='x', expand=True, padx=2)
    tk.Button(action_box, text="Refresh List", command=app.refresh_mod_list).pack(fill='x', pady=(5,0))

    # 3. MIDDLE: Listbox (Takes remaining space)
    list_frame = tk.Frame(left_f)
    list_frame.pack(side='top', fill='both', expand=True)
    scrollbar = tk.Scrollbar(list_frame, orient="vertical")
    app.mod_listbox = tk.Listbox(list_frame, selectmode=tk.SINGLE, font=("Segoe UI", 9), yscrollcommand=scrollbar.set)
    scrollbar.config(command=app.mod_listbox.yview)
    scrollbar.pack(side="right", fill="y")
    app.mod_listbox.pack(side="left", fill="both", expand=True)
    app.mod_listbox.bind('<<ListboxSelect>>', lambda e: app.on_mod_selected())

    # RIGHT: Safe Config Editor
    right_f = tk.LabelFrame(paned, text="Safe Config Editor (Game.ini)", padx=5, pady=5)
    paned.add(right_f)
    top_c = tk.Frame(right_f); top_c.pack(fill='x', pady=5)
    tk.Label(top_c, text="Select Mod Section:").pack(side='left')
    app.mod_sec_var = tk.StringVar()
    app.mod_sec_combo = ttk.Combobox(top_c, textvariable=app.mod_sec_var, state="readonly", width=35)
    app.mod_sec_combo.pack(side='left', padx=5)
    app.mod_sec_combo.bind("<<ComboboxSelected>>", lambda e: app.load_mod_section_data())
    tk.Button(top_c, text="Save Config", bg="#ddffdd", command=app.save_mod_section_data).pack(side='right')

    app.mod_editor_frame = tk.Frame(right_f)
    app.mod_editor_frame.pack(fill='both', expand=True)
    app.mod_kv_entries = [] 
    app.mod_editor_canvas = tk.Canvas(app.mod_editor_frame)
    scroll = ttk.Scrollbar(app.mod_editor_frame, orient="vertical", command=app.mod_editor_canvas.yview)
    app.mod_editor_inner = tk.Frame(app.mod_editor_canvas)
    app.mod_editor_inner.bind("<Configure>", lambda e: app.mod_editor_canvas.configure(scrollregion=app.mod_editor_canvas.bbox("all")))
    app.mod_editor_canvas.create_window((0,0), window=app.mod_editor_inner, anchor="nw")
    app.mod_editor_canvas.configure(yscrollcommand=scroll.set)
    app.mod_editor_canvas.pack(side="left", fill="both", expand=True)
    scroll.pack(side="right", fill="y")
    tk.Label(app.mod_editor_inner, text="Select a section above to edit.", fg="grey").pack(pady=20)

def _build_players_tab(app, parent):
    f_frame = tk.Frame(parent, pady=5); f_frame.pack(fill='x', padx=10)
    tk.Label(f_frame, text="View Mode:").pack(side='left')
    app.player_filter_menu = ttk.Combobox(f_frame, textvariable=app.player_filter_var, values=["Online Now", "History (All Time)"], state="readonly")
    app.player_filter_menu.pack(side='left', padx=10)
    app.player_filter_menu.bind("<<ComboboxSelected>>", lambda e: app.refresh_player_list_ui())
    tk.Button(f_frame, text="🚫 Ban Selected SteamID", bg="#ffebee", fg="red", command=app.ban_selected_player).pack(side='right', padx=10)
    pl_cont = tk.LabelFrame(parent, text="Players (Name | SteamID | Last Seen)", padx=10, pady=10)
    pl_cont.pack(fill='both', expand=True, padx=10, pady=10)
    app.players_listbox = tk.Listbox(pl_cont, font=("Courier New", 10), height=15)
    app.players_listbox.pack(fill='both', expand=True, side='left')
    tk.Scrollbar(pl_cont, orient="vertical", command=app.players_listbox.yview).pack(side="right", fill="y")

def _build_scheduler_tab(app, parent):
    d_grp = tk.LabelFrame(parent, text="Fixed Time Schedule", padx=10, pady=10); d_grp.pack(fill='x', padx=10, pady=10)
    tk.Checkbutton(d_grp, text="Enable Time Schedule", variable=app.sched_daily_enabled).pack(anchor='w')
    d_f = tk.Frame(d_grp); d_f.pack(fill='x', pady=5)
    for i, n in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]): tk.Checkbutton(d_f, text=n, variable=app.sched_days_vars[i]).pack(side='left', padx=5)
    t_f = tk.Frame(d_grp); t_f.pack(fill='x', pady=5)
    tk.Label(t_f, text="Restart Times (HH:MM):").pack(side='left')
    app.sched_time_entry = tk.Entry(t_f, width=40); app.sched_time_entry.pack(side='left', padx=5)
    tk.Label(t_f, text="| Warnings (Min):").pack(side='left', padx=5)
    app.sched_warning_entry = tk.Entry(t_f, textvariable=app.sched_warning_var, width=15)
    app.sched_warning_entry.pack(side='left')

    i_grp = tk.LabelFrame(parent, text="Uptime Limit", padx=10, pady=10); i_grp.pack(fill='x', padx=10, pady=10)
    tk.Checkbutton(i_grp, text="Enable Uptime Limit", variable=app.sched_interval_enabled).pack(anchor='w')
    i_f = tk.Frame(i_grp); i_f.pack(fill='x', pady=5)
    tk.Label(i_f, text="Restart after").pack(side='left')
    app.sched_interval_entry = tk.Entry(i_f, width=5); app.sched_interval_entry.pack(side='left', padx=5)
    tk.Label(i_f, text="hours").pack(side='left')
    
    ram_grp = tk.LabelFrame(parent, text="Resource Protection (Memory Leak Watchdog)", padx=10, pady=10, fg="red")
    ram_grp.pack(fill='x', padx=10, pady=10)
    r_f = tk.Frame(ram_grp); r_f.pack(fill='x', pady=5)
    tk.Label(r_f, text="Force Restart if RAM usage exceeds:").pack(side='left')
    app.ram_limit_entry = tk.Entry(r_f, textvariable=app.ram_limit_var, width=5)
    app.ram_limit_entry.pack(side='left', padx=5)
    tk.Label(r_f, text="GB (0 = Disabled)").pack(side='left')
    app.sched_status_label = tk.Label(parent, text="Scheduler Status: Waiting...", font=("Courier New", 10))
    app.sched_status_label.pack(pady=10)

def _build_logs_tab(app, parent):
    # v5.0.0 Change: Manual Search Button & Key Binding
    l_bar = tk.Frame(parent); l_bar.pack(fill='x', padx=5, pady=2)
    tk.Label(l_bar, text="Filter:", font=("Segoe UI", 8)).pack(side='left')
    
    app.log_filter_var = tk.StringVar()
    app.log_filter_entry = tk.Entry(l_bar, textvariable=app.log_filter_var, width=20)
    app.log_filter_entry.pack(side='left', padx=5)
    
    # BIND ENTER KEY
    app.log_filter_entry.bind('<Return>', lambda e: app.apply_log_filter())
    
    # SEARCH BUTTON
    tk.Button(l_bar, text="Search", width=8, command=app.apply_log_filter).pack(side='left', padx=2)
    
    tk.Button(l_bar, text="Purge Logs", command=app.purge_manager_logs).pack(side='right')
    
    app.log_text = tk.Text(parent, state='disabled', wrap='word', bg='black', fg='#00ff00', font=("Courier New", 9), height=20)
    app.log_text.pack(fill="both", expand=True, padx=5, pady=5)
    
    # DEFINE COLOR TAGS (New v5.0.0)
    for tag, color in constants.LOG_HIGHLIGHTS.items():
        app.log_text.tag_config(tag, foreground=color)

def _build_mgmt_tab(app, parent):
    doc_frame = tk.LabelFrame(parent, text="The Doctor (Diagnostics)", padx=10, pady=5, fg="#27ae60")
    doc_frame.pack(fill='x', padx=10, pady=5)
    app.diag_btn = tk.Button(doc_frame, text="Run Health Check", bg="#ddffdd", command=app.run_doctor)
    app.diag_btn.pack(side='top', padx=10, pady=5, anchor="w")
    app.diag_port_label = tk.Label(doc_frame, text="Port Status: Unknown", fg="grey")
    app.diag_port_label.pack(side='top', padx=10, anchor="w")
    app.diag_fw_label = tk.Label(doc_frame, text="Firewall Rules: Unknown", fg="grey")
    app.diag_fw_label.pack(side='top', padx=10, anchor="w")

    as_frame = tk.LabelFrame(parent, text="Startup Behavior", padx=10, pady=5, fg="#d35400")
    as_frame.pack(fill='x', padx=10, pady=5)
    r1 = tk.Frame(as_frame); r1.pack(fill='x', pady=2)
    
    # --- FIXED BUTTON ACTIONS (v4.9.1 Hotfix included) ---
    def install_task_wrapper():
        success, msg = logic.install_autostart_task()
        if success: messagebox.showinfo("Auto-Start", msg)
        else: messagebox.showerror("Error", msg)
        
    def remove_task_wrapper():
        success, msg = logic.remove_autostart_task()
        if success: messagebox.showinfo("Auto-Start", msg)
        else: messagebox.showerror("Error", msg)

    tk.Button(r1, text="Install Windows Boot Task", command=install_task_wrapper).pack(side='left', padx=5)
    tk.Button(r1, text="Remove Task", command=remove_task_wrapper).pack(side='left', padx=5)
    # ----------------------------

    r2 = tk.Frame(as_frame); r2.pack(fill='x', pady=5)
    tk.Checkbutton(r2, text="Auto-Start Server when Manager Opens", variable=app.auto_start_server_var).pack(side='left')
    tk.Label(r2, text="(Delay Seconds):").pack(side='left', padx=5)
    tk.Entry(r2, textvariable=app.boot_delay_var, width=5).pack(side='left')

    vis_frame = tk.LabelFrame(parent, text="Visual Theme", padx=10, pady=5)
    vis_frame.pack(fill='x', padx=10, pady=5)
    tk.Label(vis_frame, text="Interface Accent Color:").pack(side='left')
    app.theme_combobox = ttk.Combobox(vis_frame, textvariable=app.theme_var, state="readonly", values=["Standard (Blue)", "PvP (Orange)", "Hardcore (Purple)", "Eco (Green)", "Test (Grey)"])
    app.theme_combobox.pack(side='left', padx=10)
    app.theme_combobox.bind("<<ComboboxSelected>>", app.apply_theme_selection)

    ban_frame = tk.LabelFrame(parent, text="Banned Players Management", padx=10, pady=5, fg="red")
    ban_frame.pack(fill='x', padx=10, pady=10)
    app.banned_list_text = tk.Text(ban_frame, height=4, width=60, font=("Courier New", 9))
    app.banned_list_text.pack(side='left', padx=5)
    tk.Button(ban_frame, text="Refresh List", command=app.refresh_ban_list).pack(side='left', padx=5, anchor='n')
    
    sc_frame = tk.LabelFrame(parent, text="SteamCMD Path", padx=10, pady=5)
    sc_frame.pack(fill='x', padx=10, pady=10)
    tk.Label(sc_frame, text="⚠️ First Time Setup: Click 'Manual Update' below to download/install the server files.", fg="blue").pack(anchor="w", padx=5)
    app.steamcmd_path_entry = tk.Entry(sc_frame)
    app.steamcmd_path_entry.pack(side='left', fill='x', expand=True, padx=5)
    tk.Button(sc_frame, text="Browse...", command=app.browse_steamcmd).pack(side='left', padx=5)

    up_frame = tk.LabelFrame(parent, text="Smart Auto-Updater", padx=10, pady=5, fg="#0056b3"); up_frame.pack(fill='x', padx=10, pady=5)
    r1 = tk.Frame(up_frame); r1.pack(fill='x', pady=2)
    tk.Checkbutton(r1, text="Enable Auto-Updater", variable=app.auto_update_enabled).pack(side='left')
    tk.Checkbutton(r1, text="Passive Mode", variable=app.auto_update_passive).pack(side='left', padx=10)
    r2 = tk.Frame(up_frame); r2.pack(fill='x', pady=2)
    tk.Label(r2, text="Steam Branch:").pack(side='left')
    app.steambranch_combobox = ttk.Combobox(r2, width=57, values=logic.steam_get_beta_branches())
    app.steambranch_combobox.pack(side='left', padx=5)
    app.updater_status_label = tk.Label(r2, text="Status: Idle", fg="grey"); app.updater_status_label.pack(side='right', padx=10)
    
    bf = tk.Frame(parent); bf.pack(fill='x', padx=10, pady=5)
    app.btn_steam_upd = tk.Button(bf, text="Manual Update", command=app.start_steamcmd_update); app.btn_steam_upd.pack(side='left', padx=5)
    app.btn_steam_val = tk.Button(bf, text="Manual Validate (Slow)", command=app.start_steamcmd_validate); app.btn_steam_val.pack(side='left', padx=5)

    app.steamcmd_console_output = scrolledtext.ScrolledText(parent, state='disabled', wrap='word', bg='black', fg='#00ff00', font=("Courier New", 9), height=15)
    app.steamcmd_console_output.pack(fill='both', expand=True, padx=10)

def _build_integrations_tab(app, parent):
    df = tk.LabelFrame(parent, text="Discord Webhooks (One-Way)", padx=10, pady=5, fg="#7289da")
    df.pack(fill='x', padx=10, pady=10)
    tk.Checkbutton(df, text="Enable Discord Webhooks", variable=app.discord_enabled).pack(anchor='w')
    dr = tk.Frame(df); dr.pack(fill='x', pady=2)
    tk.Label(dr, text="Webhook URL:").pack(side='left')
    tk.Entry(dr, textvariable=app.discord_webhook_url).pack(side='left', fill='x', expand=True, padx=5)
    dr2 = tk.Frame(df); dr2.pack(fill='x', pady=2)
    tk.Label(dr2, text="Community URL:").pack(side='left')
    tk.Entry(dr2, textvariable=app.community_url).pack(side='left', fill='x', expand=True, padx=5)
    
    bf = tk.LabelFrame(parent, text="Discord Bot 2.0 (Two-Way)", padx=10, pady=5, fg="#9b59b6")
    bf.pack(fill='x', padx=10, pady=10)
    tk.Label(bf, text="Allows !restart, !status, !start, !stop, !backup, !ip", fg="grey").pack(anchor="w")
    br1 = tk.Frame(bf); br1.pack(fill='x', pady=2)
    tk.Label(br1, text="Bot Token:").pack(side='left')
    tk.Entry(br1, textvariable=app.discord_bot_token, show="*").pack(side='left', fill='x', expand=True, padx=5)
    br2 = tk.Frame(bf); br2.pack(fill='x', pady=2)
    tk.Label(br2, text="Channel ID:").pack(side='left')
    tk.Entry(br2, textvariable=app.discord_channel_id).pack(side='left', fill='x', expand=True, padx=5)

def _build_backup_tab(app, parent):
    bs = tk.LabelFrame(parent, text="Backup Settings", padx=10, pady=5); bs.pack(fill='x', padx=10, pady=5)
    tk.Label(bs, text="Format:").pack(side='left'); app.backup_format_entry = tk.Entry(bs, width=30); app.backup_format_entry.pack(side='left', padx=5)
    tk.Label(bs, text="| Keep:").pack(side='left'); app.backup_retention_spinbox = tk.Spinbox(bs, from_=1, to=100, width=3); app.backup_retention_spinbox.pack(side='left')
    ba = tk.LabelFrame(parent, text="Automated", padx=10, pady=5); ba.pack(fill='x', padx=10, pady=5)
    tk.Checkbutton(ba, text="Enable Reactive Backups", variable=app.reactive_backup_enabled).pack(side='left')
    tk.Checkbutton(ba, text="Backup on Stop", variable=app.backup_on_stop).pack(side='left', padx=10)
    blf = tk.Frame(parent); blf.pack(fill='both', expand=True, padx=10, pady=5)
    app.backup_list = tk.Listbox(blf, bg='#f0f0f0', font=("Courier New", 10), height=10); app.backup_list.pack(side='left', fill='both', expand=True)
    tk.Scrollbar(blf, orient="vertical", command=app.backup_list.yview).pack(side='right', fill='y')
    bac = tk.Frame(parent); bac.pack(fill='x', padx=10)
    app.create_backup_button = tk.Button(bac, text="Create Backup", command=app.start_manual_backup)
    app.create_backup_button.pack(side='left', pady=5, padx=5)
    tk.Button(bac, text="Open Folder", command=app.open_backup_folder).pack(side='left', pady=5, padx=5)

def _build_help_tab(app, parent):
    paned = ttk.PanedWindow(parent, orient=tk.HORIZONTAL)
    paned.pack(fill='both', expand=True, padx=5, pady=5)
    frame_list = ttk.Frame(paned, width=150)
    paned.add(frame_list, weight=1)
    lbl_topics = ttk.Label(frame_list, text="Topics", font=("Segoe UI", 10, "bold"))
    lbl_topics.pack(anchor='w', pady=(0,5))
    app.help_topic_list = tk.Listbox(frame_list, height=20, font=("Segoe UI", 9))
    app.help_topic_list.pack(fill='both', expand=True)
    frame_content = ttk.Frame(paned)
    paned.add(frame_content, weight=4)
    lbl_details = ttk.Label(frame_content, text="Details", font=("Segoe UI", 10, "bold"))
    lbl_details.pack(anchor='w', pady=(0,5))
    app.help_text_area = scrolledtext.ScrolledText(frame_content, wrap=tk.WORD, font=("Segoe UI", 10), state='disabled')
    app.help_text_area.pack(fill='both', expand=True)
    for topic in constants.FAQ_TEXT.keys():
        app.help_topic_list.insert(tk.END, topic)
    def display_faq(event):
        selection = app.help_topic_list.curselection()
        if selection:
            topic = app.help_topic_list.get(selection[0])
            content = constants.FAQ_TEXT.get(topic, "No details found.")
            app.help_text_area.configure(state='normal')
            app.help_text_area.delete(1.0, tk.END)
            app.help_text_area.insert(tk.END, f"--- {topic} ---\n\n{content}")
            app.help_text_area.configure(state='disabled')
    app.help_topic_list.bind('<<ListboxSelect>>', display_faq)
    app.help_text_area.configure(state='normal')
    app.help_text_area.insert(tk.END, "Select a topic on the left to view help documentation.")
    app.help_text_area.configure(state='disabled')

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