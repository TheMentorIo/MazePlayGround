"""
Maze Game Page for the Maze Playground Application.
Interactive maze game with player movement, scoring, and game state management.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import copy
import logging
import time
import numpy as np
from typing import Optional, Tuple
from enum import Enum
from MazeConfig import CellType,Direction
from MazeGame import MazeGame
from AppConfig import AppConfig
from GameArea import GameArea
 

class GameState(Enum):
    """Enumeration for game states."""
    IDLE = "idle"
    PLAYING = "playing"
    PAUSED = "paused"
    WON = "won"
    LOST = "lost"


class MazeGamePage(ttk.Frame):
    """
    Interactive maze game page optimized for GameArea integration.
    
    Features:
    - Player movement with keyboard controls via GameArea
    - Game state management
    - Score tracking and timer
    - GameArea integration for all visual aspects
    - Clean separation of concerns
    """
    
    # Button text constants
    PLAY_TEXT = "▶️ Play"
    RESUME_TEXT = "▶️ Resume"
    PAUSE_TEXT = "⏸️ Pause"
    RESTART_TEXT = "🔄 Restart"
    
    def __init__(self, parent: tk.Widget, controller):
        """
        Initialize the maze game page.
        
        Args:
            parent: Parent widget
            controller: Main application controller
        """
        super().__init__(parent)
        self.controller = controller
        self.config = AppConfig()
        
        # Game state variables
        self.game_state = GameState.IDLE
        self.maze: Optional[list] = None
        self.original_maze: Optional[list] = None
        self.maze_engine: Optional[MazeGame] = None
        
        # Game statistics
        self.start_time: Optional[float] = None
        self.moves_count = 0
        self.score = 0
        self.best_time = float('inf')
        
        # UI components
        self.game_area: Optional[GameArea] = None
        self.status_vars = {}
        
        # Initialize UI
        self._create_header()
        self._create_game_controls()
        self._create_game_area()
        self._create_status_bar()
        self._setup_callbacks()
        
        logging.debug("MazeGamePage initialized successfully")

    def _create_header(self) -> None:
        """Create the game header with title and info."""
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Title
        title_label = ttk.Label(
            header_frame,
            text="🎮 Maze Game",
            font=("Arial", 16, "bold")
        )
        title_label.pack(side=tk.LEFT)
        
        # Game info
        info_frame = ttk.Frame(header_frame)
        info_frame.pack(side=tk.RIGHT)
        
        self.control_info = ttk.Label(
            info_frame, 
            text="Use arrow keys or WASD to move", 
            font=("Arial", 9), 
            foreground="gray"
        )
        self.control_info.pack()
        
        # Status indicator
        self.focus_indicator = ttk.Label(
            info_frame,
            text="Click game area to enable controls",
            font=("Arial", 8),
            foreground="orange"
        )
        self.focus_indicator.pack()

    def _create_game_controls(self) -> None:
        """Create game control buttons."""
        controls_frame = ttk.LabelFrame(self, text="Game Controls", padding=10)
        controls_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Primary controls
        primary_frame = ttk.Frame(controls_frame)
        primary_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.play_btn = ttk.Button(
            primary_frame,
            text=self.PLAY_TEXT,
            command=self._play_game,
            state="disabled"
        )
        self.play_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.pause_btn = ttk.Button(
            primary_frame,
            text=self.PAUSE_TEXT,
            command=self._pause_game,
            state="disabled"
        )
        self.pause_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.restart_btn = ttk.Button(
            primary_frame,
            text=self.RESTART_TEXT,
            command=self._restart_game,
            state="disabled"
        )
        self.restart_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Secondary controls
        secondary_frame = ttk.Frame(controls_frame)
        secondary_frame.pack(fill=tk.X)
        
        # Game management buttons
        game_mgmt_buttons = [
            ("💾 Save Game", self._save_game),
            ("📁 Load Game", self._load_game),
            ("⚙️ Settings", self._show_settings)
        ]
        
        for text, command in game_mgmt_buttons:
            ttk.Button(
                secondary_frame,
                text=text,
                command=command
            ).pack(side=tk.LEFT, padx=(0, 5))
        
        # Debug button for testing
        ttk.Button(
            secondary_frame,
            text="🔧 Test Move",
            command=self._test_move
        ).pack(side=tk.LEFT, padx=(0, 5))

    def _create_game_area(self) -> None:
        """Create the game area with GameArea canvas."""
        game_frame = ttk.LabelFrame(self, text="Game Area", padding=5)
        game_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Create simplified GameArea
        self.game_area = GameArea(
            game_frame, 
            width=800,
            height=600
        )
        
        # Create scrollbars
        v_scrollbar = ttk.Scrollbar(game_frame, orient=tk.VERTICAL, command=self.game_area.yview)
        h_scrollbar = ttk.Scrollbar(game_frame, orient=tk.HORIZONTAL, command=self.game_area.xview)
        
        self.game_area.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack scrollbars and canvas
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.game_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _setup_callbacks(self) -> None:
        """Setup callbacks for GameArea events."""
        # Note: Simplified GameArea doesn't have callbacks
        # Game logic will be handled directly in MazeGamePage
        
        # Setup keyboard bindings for player movement
        self.bind("<Key>", self._on_key_press)
        self.focus_set()

    def _create_status_bar(self) -> None:
        """Create status bar with game information."""
        status_frame = ttk.Frame(self)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        # Separator
        ttk.Separator(status_frame, orient=tk.HORIZONTAL).pack(fill=tk.X)
        
        # Status content
        status_content = ttk.Frame(status_frame)
        status_content.pack(fill=tk.X, padx=5, pady=2)
        
        # Game statistics
        stats_frame = ttk.Frame(status_content)
        stats_frame.pack(side=tk.LEFT)
        
        # Initialize status variables
        status_items = [
            ("state", "No maze loaded"),
            ("time", "Time: 00:00"),
            ("moves", "Moves: 0"),
            ("score", "Score: 0")
        ]
        
        self.status_vars = {key: tk.StringVar(value=value) for key, value in status_items}
        
        # Create status labels
        for i, (key, _) in enumerate(status_items):
            label = ttk.Label(stats_frame, textvariable=self.status_vars[key], font=("Arial", 9))
            label.grid(row=0, column=i, padx=(0, 15), sticky="w")
        
        # Timer update
        self._update_timer()

    def _on_player_move(self, position: Tuple[int, int], direction: str) -> None:
        """Handle player movement event from GameArea."""
        if self.game_state == GameState.PLAYING:
            self.moves_count += 1
            self.score = max(0, self.score - 1)  # Decrease score with each move
            
            # Check if player reached exit
            if self.maze_engine and self.maze_engine.game_over:
                self._handle_game_won()
    
    def _on_key_press(self, event) -> None:
        """Handle keyboard events for player movement."""
        if self.game_state != GameState.PLAYING or not self.maze_engine:
            return
        
        # Map keys to directions
        key_direction_map = {
            'Up': Direction.UP, 'Down': Direction.DOWN, 'Left': Direction.LEFT, 'Right': Direction.RIGHT,
            'w': Direction.UP, 's': Direction.DOWN, 'a': Direction.LEFT, 'd': Direction.RIGHT
        }
        
        direction = key_direction_map.get(event.keysym)
        if direction:
            # Try to move player using maze engine
            if self.maze_engine.move_player(direction):
                # Update moves and score
                self.moves_count += 1
                self.score = max(0, self.score - 1)
                
                # Update the display
                self.maze = self.maze_engine.maze
                self._load_maze_to_game_area()
                
                # Check win condition
                if self.maze_engine.game_over:
                    self._handle_game_won()
    
    def _on_game_completed(self) -> None:
        """Handle game completion event from GameArea."""
        self._handle_game_won()
    
    def _on_cell_click(self, row: int, col: int) -> None:
        """Handle cell click event from GameArea."""
        print(f"Cell clicked: ({row}, {col})")
        # Can add special click interactions here if needed

    def _play_game(self) -> None:
        """Start or resume the game."""
        try:
            if self.maze is None:
                messagebox.showwarning("Warning", "No maze loaded. Please load a maze first.")
                return
            
            if self.game_state == GameState.IDLE:
                self._start_new_game()
            elif self.game_state == GameState.PAUSED:
                self._resume_game()
            
            self._update_ui_state()
            self._ensure_focus()
            
            print(f"Game started. State: {self.game_state}")
            
        except Exception as e:
            logging.error(f"Error starting game: {e}")
            messagebox.showerror("Error", f"Failed to start game: {e}")
            print(f"Error starting game: {e}")
    
    def _start_new_game(self) -> None:
        """Start a new game session."""
        # Backup original maze
        self.original_maze = copy.deepcopy(self.maze)
        
        # Initialize maze engine and generate positions
        self._initialize_maze_engine()
        
        # Convert and load maze into GameArea
        self._load_maze_to_game_area(include_entities=True)
        
        # Reset game statistics
        self._reset_game_statistics()
        
        self.game_state = GameState.PLAYING
    
    def _load_maze_to_game_area(self, include_entities: bool = False) -> bool:
        """
        Consolidated method to load maze into GameArea.
        
        Args:
            include_entities: Whether to include player and exit positions (not used in simplified GameArea)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.maze:
            return False
            
        try:
            maze_array = np.array(self.maze, dtype=int)
            
            # Simplified GameArea only needs the maze data
            self.game_area.load_maze(maze_array)
            
            return True
        except Exception as e:
            logging.error(f"Error loading maze into GameArea: {e}")
            return False

    def _initialize_maze_engine(self) -> None:
        """Initialize the maze engine and generate player/exit."""
        self.maze_engine = MazeGame(self.maze)
        self.maze_engine.generate_player()
        self.maze_engine.generate_exit()
        self.maze = self.maze_engine.maze

    def _find_game_positions(self) -> Tuple[Optional[Tuple[int, int]], Optional[Tuple[int, int]]]:
        """Find player and exit positions in the maze."""
        player_pos = None
        exit_pos = None
        
        for i in range(len(self.maze)):
            for j in range(len(self.maze[i])):
                if self.maze[i][j] == CellType.PLAYER.value:
                    player_pos = (i, j)
                elif self.maze[i][j] == CellType.EXIT.value:
                    exit_pos = (i, j)
        
        return player_pos, exit_pos
    
    def _reset_game_statistics(self) -> None:
        """Reset game statistics for new game."""
        self.start_time = time.time()
        self.moves_count = 0
        self.score = 1000  # Starting score
    
    def _resume_game(self) -> None:
        """Resume a paused game."""
        self.game_state = GameState.PLAYING
    
    def _ensure_focus(self) -> None:
        """Ensure proper focus for keyboard input."""
        self.focus_set()
        # Make sure this frame can receive keyboard events
        self.configure(takefocus=True)

    def _pause_game(self) -> None:
        """Pause the current game."""
        if self.game_state == GameState.PLAYING:
            self.game_state = GameState.PAUSED
            self._update_ui_state()

    def _restart_game(self) -> None:
        """Restart the current game."""
        try:
            if self.original_maze is not None:
                self.maze = copy.deepcopy(self.original_maze)
                self.game_state = GameState.IDLE
                self._reset_statistics()
                self._update_ui_state()
                
                # Reset GameArea to empty state
                self.set_maze(self.maze)
                self._load_maze_to_game_area()
            
        except Exception as e:
            logging.error(f"Error restarting game: {e}")
            messagebox.showerror("Error", f"Failed to restart game: {e}")

    def _reset_statistics(self) -> None:
        """Reset game statistics."""
        self.start_time = None
        self.moves_count = 0
        self.score = 0

    def _update_ui_state(self) -> None:
        """Update UI elements based on current game state."""
        # Define state configurations
        state_configs = {
            GameState.IDLE: {
                "play_btn": ("normal" if self.maze else "disabled", self.PLAY_TEXT),
                "pause_btn": "disabled",
                "restart_btn": "disabled",
                "status": "Ready to play"
            },
            GameState.PLAYING: {
                "play_btn": ("disabled", self.PLAY_TEXT),
                "pause_btn": "normal",
                "restart_btn": "normal",
                "status": "Playing..."
            },
            GameState.PAUSED: {
                "play_btn": ("normal", self.RESUME_TEXT),
                "pause_btn": "disabled",
                "restart_btn": "normal",
                "status": "Paused"
            },
            GameState.WON: {
                "play_btn": ("disabled", self.PLAY_TEXT),
                "pause_btn": "disabled",
                "restart_btn": "normal",
                "status": "Congratulations! You won!"
            }
        }
        
        config = state_configs.get(self.game_state)
        if config:
            # Update buttons
            play_state, play_text = config["play_btn"]
            self.play_btn.configure(state=play_state, text=play_text)
            self.pause_btn.configure(state=config["pause_btn"])
            self.restart_btn.configure(state=config["restart_btn"])
            
            # Update status
            self.status_vars["state"].set(config["status"])

    def _handle_game_won(self) -> None:
        """Handle game completion."""
        self.game_state = GameState.WON
        
        # Calculate time bonus
        time_taken = 0
        if self.start_time:
            time_taken = time.time() - self.start_time
            time_bonus = max(0, 500 - int(time_taken))
            self.score += time_bonus
            
            # Update best time
            if time_taken < self.best_time:
                self.best_time = time_taken
        
        self._update_ui_state()
        
        # Show congratulations
        messagebox.showinfo(
            "Congratulations!",
            f"You completed the maze!\n\n"
            f"Moves: {self.moves_count}\n"
            f"Time: {self._format_time(time_taken)}\n"
            f"Score: {self.score}"
        )

    def _update_timer(self) -> None:
        """Update the timer display."""
        if self.game_state == GameState.PLAYING and self.start_time:
            elapsed = time.time() - self.start_time
            self.status_vars["time"].set(f"Time: {self._format_time(elapsed)}")
        
        # Update other status variables
        self.status_vars["moves"].set(f"Moves: {self.moves_count}")
        self.status_vars["score"].set(f"Score: {self.score}")
        
        # Schedule next update
        self.after(1000, self._update_timer)

    def _format_time(self, seconds: float) -> str:
        """
        Format time in seconds to MM:SS format.
        
        Args:
            seconds: Time in seconds
            
        Returns:
            Formatted time string
        """
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"

    def _save_game(self) -> None:
        """Save current game state."""
        messagebox.showinfo("Save Game", "Save game functionality coming soon!")

    def _load_game(self) -> None:
        """Load saved game state."""
        messagebox.showinfo("Load Game", "Load game functionality coming soon!")

    def _show_settings(self) -> None:
        """Show game settings dialog."""
        messagebox.showinfo("Settings", "Game settings coming soon!")

    def _test_move(self) -> None:
        """Test move functionality for debugging."""
        if self.game_state == GameState.PLAYING and self.maze_engine:
            try:
                # Try moving down using maze engine
                success = self.maze_engine.move_player('down')
                if success:
                    # Update display
                    self.maze = self.maze_engine.maze
                    self._load_maze_to_game_area()
                    messagebox.showinfo("Test", "Moved player down successfully!")
                else:
                    messagebox.showinfo("Test", "Could not move player down (blocked)")
            except Exception as e:
                messagebox.showerror("Test Error", f"Error during test move: {e}")
        else:
            messagebox.showwarning("Test", "Game not running or engine not available")

    def set_maze(self, maze: list) -> None:
        """
        Set the maze for the game.
        
        Args:
            maze: 2D list representing the maze
        """
        try:
            self.maze = copy.deepcopy(maze) if maze else None
            self.original_maze = copy.deepcopy(maze) if maze else None
            self.game_state = GameState.IDLE
            self._reset_statistics()
            self._update_ui_state()
            
            # Show empty state in GameArea if no maze
            if not self.maze:
                self.game_area.show_empty_state()
            
            logging.info("Maze set successfully")
        except Exception as e:
            logging.error(f"Error setting maze: {e}")
            messagebox.showerror("Error", f"Failed to load maze: {e}")

    def refresh(self) -> None:
        """Refresh the game page."""
        # GameArea handles its own refresh, just ensure UI state is correct
        self._update_ui_state()

    def on_show(self, **kwargs) -> None:
        """
        Called when the frame is shown.
        
        Args:
            **kwargs: Additional arguments, may contain 'maze'
        """
        if 'maze' in kwargs:
            self.set_maze(kwargs['maze'])
        
        # Load maze into game_area for rendering if maze exists
        if self.maze is not None:
            self._load_maze_to_game_area(include_entities=False)
        
        # Ensure focus for key events
        self.after(100, self._set_focus)
        
        logging.debug("MazeGamePage shown")

    def _set_focus(self) -> None:
        """Set focus to enable keyboard input."""
        self.focus_set()
        # Make sure this frame can receive keyboard events
        self.configure(takefocus=True)
        
        # Update focus indicator
        if hasattr(self, 'focus_indicator'):
            self.focus_indicator.config(text="Controls active", foreground="green")
            
        print("Focus set for MazeGamePage")

    def on_maze_completed(self) -> None:
        """Called by GameArea when maze is completed."""
        self._handle_game_won()

