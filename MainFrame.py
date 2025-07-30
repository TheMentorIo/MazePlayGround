"""
Main Frame for the Maze Playground Application.
Provides the main menu interface with navigation buttons.
"""

import tkinter as tk
from tkinter import ttk
import logging
from typing import Dict, Callable


class MainFrame(ttk.Frame):
    """
    Main menu frame for the Maze Playground application.
    
    This frame serves as the central hub providing navigation to all
    major features of the application including maze generation,
    viewing saved mazes, and playing maze games.
    """
    
    def __init__(self, parent: tk.Widget, controller):
        """
        Initialize the main frame.
        
        Args:
            parent: Parent widget
            controller: Main application controller
        """
        super().__init__(parent)
        self.controller = controller
        
        # Configure frame styling
        self.configure(padding="20")
        
        # Initialize UI components
        self.create_title()
        self.create_navigation_buttons()
        self.create_info_section()

        logging.debug("MainFrame initialized successfully")

    def create_title(self) -> None:
        """Create the main title section."""
        title_frame = ttk.Frame(self)
        title_frame.pack(fill=tk.X, pady=(0, 30))
        
        # Main title
        title_label = ttk.Label(
            title_frame,
            text="🏰 Maze Playground",
            font=("Arial", 24, "bold"),
            anchor="center"
        )
        title_label.pack()
        
        # Subtitle
        subtitle_label = ttk.Label(
            title_frame,
            text="Generate, Play, and Explore Amazing Mazes",
            font=("Arial", 12),
            anchor="center"
        )
        subtitle_label.pack(pady=(5, 0))

    def create_navigation_buttons(self) -> None:
        """Create the main navigation buttons."""
        nav_frame = ttk.Frame(self)
        nav_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Configure grid weights for responsive layout
        nav_frame.columnconfigure(0, weight=1)
        nav_frame.columnconfigure(1, weight=1)
        
        # Button configurations
        button_configs = [
            {
                "text": "🎲 Generate Maze",
                "description": "Create new mazes with custom settings",
                "command": lambda: self._navigate_to("MazeGenerator"),
                "style": "Primary.TButton",
                "row": 0,
                "column": 0
            },
            {
                "text": "🎮 Play Maze Game",
                "description": "Challenge yourself with maze games",
                "command": lambda: self._navigate_to("MazeGamePage"),
                "style": "Success.TButton",
                "row": 0,
                "column": 1
            },
            {
                "text": "📁 View Saved Mazes",
                "description": "Browse and manage your maze collection",
                "command": lambda: self._navigate_to("ViewMazesPage"),
                "style": "Info.TButton",
                "row": 1,
                "column": 0,
                "columnspan": 2
            }
        ]
        
        self._create_buttons(nav_frame, button_configs)

    def _create_buttons(self, parent: tk.Widget, configs: list) -> None:
        """
        Create buttons based on configuration.
        
        Args:
            parent: Parent widget for buttons
            configs: List of button configurations
        """
        for config in configs:
            button_frame = ttk.Frame(parent)
            button_frame.grid(
                row=config["row"],
                column=config["column"],
                columnspan=config.get("columnspan", 1),
                sticky="ew",
                padx=10,
                pady=10
            )
            
            # Main button
            button = ttk.Button(
                button_frame,
                text=config["text"],
                command=config["command"]
            )
            button.pack(fill=tk.X, ipady=15)
            
            # Description label
            desc_label = ttk.Label(
                button_frame,
                text=config["description"],
                font=("Arial", 9),
                foreground="gray"
            )
            desc_label.pack(pady=(5, 0))

    def create_info_section(self) -> None:
        """Create the information section at the bottom."""
        info_frame = ttk.Frame(self)
        info_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        # Separator
        ttk.Separator(info_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(10, 10))
        
        # Info grid
        info_grid = ttk.Frame(info_frame)
        info_grid.pack()
        
        # Statistics or quick info
        stats = [
            ("🎯", "Features", "Generate • Play • Explore"),
            ("⚡", "Performance", "Fast & Responsive"),
            ("🔧", "Customizable", "Multiple Algorithms")
        ]
        
        for i, (icon, title, desc) in enumerate(stats):
            stat_frame = ttk.Frame(info_grid)
            stat_frame.grid(row=0, column=i, padx=20, pady=10)
            
            ttk.Label(stat_frame, text=icon, font=("Arial", 16)).pack()
            ttk.Label(stat_frame, text=title, font=("Arial", 10, "bold")).pack()
            ttk.Label(stat_frame, text=desc, font=("Arial", 8), foreground="gray").pack()

    def _navigate_to(self, frame_name: str) -> None:
        """
        Navigate to a specific frame.
        
        Args:
            frame_name: Name of the frame to navigate to
        """
        try:
            self.controller.show_frame(frame_name)
            logging.info(f"Navigated to {frame_name}")
        except Exception as e:
            logging.error(f"Failed to navigate to {frame_name}: {e}")

    def refresh(self) -> None:
        """
        Refresh the frame content.
        Called when the frame is shown.
        """
        logging.debug("MainFrame refreshed")
        # Add any refresh logic here if needed

    def on_show(self, **kwargs) -> None:
        """
        Called when the frame is shown.
        
        Args:
            **kwargs: Additional arguments passed during frame transition
        """
        self.refresh()
        logging.debug("MainFrame shown")
