"""
Application configuration settings.
"""

import os
from typing import Dict, Tuple


class AppConfig:
    """Configuration class for the Maze Playground application."""
    
    # Window settings
    WINDOW_TITLE = "Maze Playground"
    WINDOW_GEOMETRY = "800x500"
    MIN_WINDOW_SIZE = (600, 400)
    
    # UI settings
    PADDING = 5
    BUTTON_PADDING = (5, 2)
    
    # Logging settings
    LOG_LEVEL = "INFO"
    LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
    LOG_TO_FILE = False
    LOG_FILENAME = "maze_app.log"
    
    # Theme settings
    THEME = "default"  # Can be "default", "dark", "light"
    
    # File paths
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    MAZES_DIR = os.path.join(BASE_DIR, "mazes")
    ASSETS_DIR = os.path.join(BASE_DIR, "assets")
    
    # Frame configuration
    FRAME_CLASSES = {
        "MainFrame": "MainFrame",
        "MazeGenerator": "GenerateMazeFrame", 
        "ViewMazesPage": "ViewMazesPage",
        "MazeGamePage": "MazeGamePage"
    }
    
    # Navigation configuration
    NAV_BUTTONS = [
        {"text": "🏠 Home", "frame": "MainFrame", "tooltip": "Go to main menu"},
        {"text": "⚙️ Settings", "frame": None, "tooltip": "Application settings"},
    ]
    
    @classmethod
    def get_frame_class_name(cls, frame_key: str) -> str:
        """Get the class name for a frame key."""
        return cls.FRAME_CLASSES.get(frame_key, frame_key)


# Theme configurations
THEMES = {
    "default": {
        "bg": "#f0f0f0",
        "fg": "#000000",
        "select_bg": "#0078d4",
        "select_fg": "#ffffff"
    },
    "dark": {
        "bg": "#2d2d2d", 
        "fg": "#ffffff",
        "select_bg": "#404040",
        "select_fg": "#ffffff"
    },
    "light": {
        "bg": "#ffffff",
        "fg": "#000000", 
        "select_bg": "#e1e1e1",
        "select_fg": "#000000"
    }
}
