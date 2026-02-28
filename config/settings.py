# =============================================================================
# SETTINGS.PY - GLOBAL GAME CONSTANTS
# =============================================================================
#
# This file centralizes all game constants.
# Every module imports settings.py to access these values.

# =============================================================================
# DISPLAY SETTINGS
# =============================================================================
#
# Window size: 1024x768 (4:3 ratio like GBA)
# - 1024/32 = 32 tiles width
# - 768/32 = 24 tiles height
# Tile size: 32x32 pixels (standard for pixel art RPGs)

SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
TILE_SIZE = 32
FPS = 60
WINDOW_TITLE = "Pokémon La Plateforme"

# Calculated grid dimensions (useful for camera and rendering)
TILES_PER_ROW = SCREEN_WIDTH // TILE_SIZE      # = 32
TILES_PER_COL = SCREEN_HEIGHT // TILE_SIZE     # = 24

# =============================================================================
# CHARACTER DIMENSIONS
# =============================================================================
#
# Player/NPC size: 24x48 pixels
# - Width 24: centered on tile (4px margin on each side)
# - Height 48: 32px (ground) + 16px (head) for elongated look

CHAR_WIDTH = 24
CHAR_HEIGHT = 48

# =============================================================================
# POKÉMON & TEAM
# =============================================================================

MAX_TEAM_SIZE = 6
TOTAL_POKEMON = 54
TOTAL_TYPES = 18
EVOLUTION_STAGES = 3

# Number of attacks per evolution stage
ATTACKS_PER_STAGE = {
    1: 2,   # Stage 1: 2 attacks
    2: 3,   # Stage 2: 3 attacks
    3: 4    # Stage 3: 4 attacks
}

# =============================================================================
# COMBAT SYSTEM
# =============================================================================

MISS_CHANCE = 0.05                    # 5% chance to miss an attack
MIN_DAMAGE = 1                         # Minimum damage per hit
STAB_BONUS = 1.5                        # Same Type Attack Bonus
COMBAT_ORDER = "random"                  # Random turn order (no speed stat)

# =============================================================================
# CAPTURE SYSTEM
# =============================================================================

CAPTURE_RATES = {
    "pokeball": 0.30,
    "super_ball": 0.60,
    "hyper_ball": 0.80,
    "master_ball": 1.00
}

# =============================================================================
# DAY/NIGHT CYCLE
# =============================================================================
#
# 24 in-game hours = 1 real hour
# Time stored in minutes (0 to 1439)

DAY_START = 360                          # 6:00 AM (6*60)
NIGHT_START = 1200                        # 8:00 PM (20*60)
CYCLE_GAME_DURATION = 1440                 # 24h in minutes
CYCLE_REAL_DURATION = 3600                  # 1h in seconds
TIME_RATIO = CYCLE_GAME_DURATION / CYCLE_REAL_DURATION   # 0.4 min/sec
NIGHT_PENALTY = 0.20                        # -20% stats at night

# =============================================================================
# ECONOMY
# =============================================================================

TRAINER_REWARDS = {
    "B1": 20,
    "B2": 30,
    "B3": 50
}

TOURNAMENT_ENTRY_FEE = 150

# =============================================================================
# TOURNAMENT
# =============================================================================
#
# Tournament bracket: Quarter-finals, Semi-finals, Final → 3 rounds

BRACKET_SIZE = 3                          # Number of tournament rounds

# =============================================================================
# SAVE SYSTEM
# =============================================================================

SAVE_SLOTS = 3

# =============================================================================
# WILD ENCOUNTERS
# =============================================================================

ENCOUNTER_RATE = 0.15                      # 15% chance per step in grass

WILD_POKEMON_LEVELS = {
    "campus":    (3, 10),    # (min, max)
    "outside":   (8, 20),
    "arena":     (18, 25)
}

# =============================================================================
# FILE PATHS
# =============================================================================
#
# All paths are built from project root using pathlib
# This ensures compatibility across Windows, Mac and Linux

import os
from pathlib import Path

# Project root (settings.py is in config/, so go up two levels)
PROJECT_ROOT = Path(__file__).parent.parent

# Main directories
DATA_DIR = PROJECT_ROOT / "data"
SAVES_DIR = PROJECT_ROOT / "saves"
ASSETS_DIR = PROJECT_ROOT / "assets"

# Assets subdirectories
SPRITES_DIR = ASSETS_DIR / "sprites"
PLAYER_SPRITES_DIR = SPRITES_DIR / "player"
POKEMON_SPRITES_DIR = SPRITES_DIR / "pokemon"
NPC_SPRITES_DIR = SPRITES_DIR / "npcs"
ITEMS_SPRITES_DIR = SPRITES_DIR / "items"
UI_SPRITES_DIR = SPRITES_DIR / "ui"

MAPS_DIR = ASSETS_DIR / "maps"
TILESETS_DIR = MAPS_DIR / "tilesets"
MUSIC_DIR = ASSETS_DIR / "music"
SFX_DIR = ASSETS_DIR / "sfx"

# Data files
POKEMON_DATA_FILE = DATA_DIR / "pokemon.json"
TRAINERS_DATA_FILE = DATA_DIR / "trainers.json"
NPCS_DATA_FILE = DATA_DIR / "npcs.json"
QUESTS_DATA_FILE = DATA_DIR / "quests.json"
ITEMS_DATA_FILE = DATA_DIR / "items.json"
SHOP_CATALOG_FILE = DATA_DIR / "shop_catalog.json"

# =============================================================================
# UI COLORS (RGB tuples)
# =============================================================================

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)

# HP bars - color changes based on remaining HP
HP_GREEN = (0, 200, 0)          # > 50% HP
HP_YELLOW = (255, 200, 0)       # 20% - 50% HP
HP_RED = (200, 0, 0)            # < 20% HP
HP_BAR_BG = (40, 40, 40)         # Bar background

# XP bar
XP_BLUE = (0, 100, 255)

# Dialogue box
DIALOG_BG = (0, 0, 0)
DIALOG_BORDER = (255, 255, 255)
DIALOG_TEXT = (255, 255, 255)

# Night filter
NIGHT_FILTER_COLOR = (0, 0, 30)          # Dark blue
NIGHT_FILTER_ALPHA = 120                  # Opacity

# Menus
SELECTION_COLOR = (255, 215, 0)           # Gold
MENU_BG_COLOR = (20, 20, 40)               # Dark blue-gray