# --- URLs ---
SECTOR_MAP_URL = "https://www.stargate-game.cz/mapa.php?page=0&id_sektor=47"
GAME_HOST = "stargate-game.cz"

# --- Browser attach (CDP) ---
# Start Chrome with: chrome.exe --remote-debugging-port=9222
# Then log into the game manually, then run the bot.
CDP_URL = "http://127.0.0.1:9222"  # explicit IPv4 — localhost resolves to ::1 on Win11

# --- Detection ---
DOT_MIN_RADIUS = 8
DOT_MAX_RADIUS = 25
DOT_COLOR_SATURATION_MIN = 80
POSITION_MATCH_TOLERANCE = 0.15
POLL_INTERVAL_BASE = 1           # seconds between sector map scans — dots disappear in 5-10s!

# --- Human behavior profiles ---
# Switch between "cautious", "normal", "aggressive"
BEHAVIOR_PROFILE = "normal"

BEHAVIOR_PROFILES = {
    "cautious": {
        "reaction_delay": (4.0, 9.0),       # seconds after dot detected
        "click_jitter_px": 6,               # pixel randomness on clicks
        "mouse_speed": (0.6, 1.4),          # seconds to move mouse
        "poll_jitter": (0.8, 1.4),          # multiplier on POLL_INTERVAL_BASE
        "between_actions": (1.5, 4.0),      # delay between sequential actions
        "occasional_pause_chance": 0.15,    # 15% chance of a random pause
        "occasional_pause_duration": (3.0, 12.0),
    },
    "normal": {
        "reaction_delay": (3.0, 4.5),       # 3-4s human reaction before acting on a dot
        "click_jitter_px": 4,
        "mouse_speed": (0.3, 0.9),
        "poll_jitter": (0.8, 1.2),          # tight jitter — keep close to 1s base
        "between_actions": (0.8, 2.0),
        "occasional_pause_chance": 0.08,
        "occasional_pause_duration": (2.0, 7.0),
    },
    "aggressive": {
        "reaction_delay": (0.8, 2.5),
        "click_jitter_px": 2,
        "mouse_speed": (0.2, 0.5),
        "poll_jitter": (0.6, 1.0),
        "between_actions": (0.4, 1.2),
        "occasional_pause_chance": 0.03,
        "occasional_pause_duration": (1.0, 3.0),
    },
}

# --- Robustness ---
MAX_RETRIES = 3
ACTION_TIMEOUT = 120
CONSECUTIVE_ERROR_LIMIT = 5
LONG_SLEEP_AFTER_ERRORS = 600   # 10 minutes

# --- Paths ---
SCREENSHOT_DIR = "screenshots"
LOG_DIR = "logs"
DEBUG_MODE = True
