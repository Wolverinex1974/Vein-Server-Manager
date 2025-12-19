# --- VERSION & IDENTITY ---
# MANAGER_VERSION = "v4.4.5 (Stable Release)"

# logger.py
import os
import sys
import traceback
import threading
import ctypes
from datetime import datetime
import constants

# --- INITIALIZATION ---
def setup():
    """Hooks into the system to catch all errors."""
    try:
        # 1. Create Directories
        os.makedirs(constants.LOGS_ROOT_DIR, exist_ok=True)
        os.makedirs(constants.CRASH_LOGS_DIR, exist_ok=True)
        os.makedirs(constants.HISTORY_LOGS_DIR, exist_ok=True)

        # 2. Reset Debug Log (Ephemeral)
        if constants.DEBUG_MODE:
            with open(constants.DEBUG_LOG_FILE, 'w', encoding='utf-8') as f:
                f.write(f"--- DEBUG SESSION START: {datetime.now()} ---\n")
            
            # 3. Redirect Standard Error to Debug Log
            sys.stderr = open(constants.DEBUG_LOG_FILE, 'a', buffering=1)

        # 4. Attach Crash Handlers
        sys.excepthook = handle_uncaught_exception
        if sys.version_info >= (3, 8):
            threading.excepthook = handle_thread_exception
        
        debug("Logger System Initialized.")
    except Exception as e:
        print(f"LOGGER INIT FAILED: {e}")

# --- HANDLERS ---
def handle_uncaught_exception(exc_type, exc_value, exc_traceback):
    """Catches Main Thread Crashes."""
    err_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    log_crash(err_msg, "MAIN_CRASH")
    debug(f"CRITICAL MAIN ERROR: {err_msg}")
    
    # Attempt visual alert
    try: ctypes.windll.user32.MessageBoxW(0, f"Critical Error:\n{exc_value}", "Vein Manager Crashed", 0x10)
    except: pass
    sys.exit(1)

def handle_thread_exception(args):
    """Catches Background Thread Crashes."""
    # NOISE FILTER: Ignore errors caused by the app closing
    if args.exc_type == RuntimeError and "main thread is not in main loop" in str(args.exc_value):
        debug(f"Thread '{args.thread.name}' stopped during shutdown (Ignored).")
        return

    err_msg = "".join(traceback.format_exception(args.exc_type, args.exc_value, args.exc_traceback))
    log_crash(err_msg, f"THREAD_{args.thread.name}")
    debug(f"CRITICAL THREAD ERROR ({args.thread.name}): {err_msg}")

# --- LOGGING FUNCTIONS ---
def debug(msg):
    """Tier 3: The Brain Scan (Developer Info)."""
    if constants.DEBUG_MODE:
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] [DEBUG] {msg}"
        print(formatted) # Keep console output
        try:
            with open(constants.DEBUG_LOG_FILE, "a", encoding='utf-8') as f:
                f.write(formatted + "\n")
        except: pass

def event(category, msg):
    """Tier 2: The Audit Trail (User History)."""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted = f"[{timestamp}] [{category}] {msg}\n"
        with open(constants.DAILY_LOG_FILE, "a", encoding='utf-8') as f:
            f.write(formatted)
        debug(f"EVENT: {category} - {msg}")
    except: pass

def log_crash(trace, tag="UNKNOWN"):
    """Tier 1: The Black Box (Crash Dump)."""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"Crash_{timestamp}_{tag}.txt"
        filepath = os.path.join(constants.CRASH_LOGS_DIR, filename)
        with open(filepath, "w", encoding='utf-8') as f:
            f.write(f"--- VEIN MANAGER CRASH REPORT ---\n")
            f.write(f"Version: {constants.MANAGER_VERSION}\n")
            f.write(f"Time: {datetime.now()}\n")
            f.write(f"Tag: {tag}\n")
            f.write("-" * 30 + "\n")
            f.write(trace + "\n")
    except Exception as e:
        print(f"CRITICAL: Failed to write crash log: {e}")

# --- THREAD WRAPPERS ---
def start_safe_thread(target, name="UnknownThread", args=(), daemon=True):
    """Starts a thread that is monitored by the logger."""
    def _wrapper(*args):
        try:
            target(*args)
        except Exception:
            # Manually trigger handler if hook fails
            exc_type, exc_value, exc_traceback = sys.exc_info()
            
            # NOISE FILTER for manual wrapper
            if exc_type == RuntimeError and "main thread is not in main loop" in str(exc_value):
                debug(f"Thread '{name}' stopped during shutdown (Ignored).")
                return

            err_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
            log_crash(err_msg, f"THREAD_{name}")
            debug(f"Thread '{name}' DIED: {exc_value}")
    
    t = threading.Thread(target=_wrapper, name=name, args=args, daemon=daemon)
    t.start()
    debug(f"Thread Started: {name}")