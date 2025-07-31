"""
Maze Game Page for the Maze Playground Application.
Interactive maze game with player movement, scoring, and game state management.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import copy
import logging
import time
from typing import Optional, Tuple, Dict, Any
from enum import Enum

try:
    from MazeConfig import MazeConfig,CellType
    from MazeGame import MazeGame
    from AppConfig import AppConfig
except ImportError as e:
    logging.error(f"Failed to import required modules: {e}")


class GameState(Enum):
    """Enumeration for game states."""
    IDLE = "idle"
    PLAYING = "playing"
    PAUSED = "paused"
    WON = "won"
    LOST = "lost"


class MazeGamePage(ttk.Frame):
    """
    Interactive maze game page.
    
    Features:
    - Player movement with keyboard controls
    - Game state management
    - Score tracking and timer
    - Multiple difficulty levels
    - Save/load game functionality
    - Visual feedback and animations
    """
    
    # Game configuration constants
    CELL_SIZE = 40
    COLORS = {
        "wall": "#2c3e50",
        "room": "#ecf0f1", 
        "player": "#3498db",
        "exit": "#e74c3c",
        "visited": "#bdc3c7",
        "path": "#f39c12"
    }
    
    # Game element values (should match mazeGame.py)
    
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
        self.canvas: Optional[tk.Canvas] = None
        self.status_vars = {}
        
        # Initialize UI
        self._create_header()
        self._create_game_controls()
        self._create_game_area()
        self._create_status_bar()
        self._setup_key_bindings()
        
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
            text="▶️ Play",
            command=self._play_game,
            state="disabled"
        )
        self.play_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.pause_btn = ttk.Button(
            primary_frame,
            text="⏸️ Pause",
            command=self._pause_game,
            state="disabled"
        )
        self.pause_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.restart_btn = ttk.Button(
            primary_frame,
            text="🔄 Restart",
            command=self._restart_game,
            state="disabled"
        )
        self.restart_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Secondary controls
        secondary_frame = ttk.Frame(controls_frame)
        secondary_frame.pack(fill=tk.X)
        
        ttk.Button(
            secondary_frame,
            text="💾 Save Game",
            command=self._save_game
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            secondary_frame,
            text="📁 Load Game",
            command=self._load_game
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            secondary_frame,
            text="⚙️ Settings",
            command=self._show_settings
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        # Debug button for testing
        ttk.Button(
            secondary_frame,
            text="🔧 Test Move",
            command=self._test_move
        ).pack(side=tk.LEFT, padx=(0, 5))

    def _create_game_area(self) -> None:
        """Create the main game canvas area."""
        game_frame = ttk.LabelFrame(self, text="Game Area")
        game_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Create canvas with scrollbars
        canvas_frame = ttk.Frame(game_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Canvas
        self.canvas = tk.Canvas(
            canvas_frame,
            bg=self.COLORS["room"],
            highlightthickness=1,
            highlightbackground="gray"
        )
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        h_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        
        self.canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack scrollbars and canvas
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Bind mouse events
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        
        # Initial empty state
        self._show_empty_game_state()

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
        self.status_vars = {
            "state": tk.StringVar(value="No maze loaded"),
            "time": tk.StringVar(value="Time: 00:00"),
            "moves": tk.StringVar(value="Moves: 0"),
            "score": tk.StringVar(value="Score: 0")
        }
        
        # Create status labels
        for i, (key, var) in enumerate(self.status_vars.items()):
            label = ttk.Label(stats_frame, textvariable=var, font=("Arial", 9))
            label.grid(row=0, column=i, padx=(0, 15), sticky="w")
        
        # Timer update
        self._update_timer()

    def _setup_key_bindings(self) -> None:
        """Setup keyboard bindings for player movement."""
        # Bind to the main frame
        self.bind_all("<Key>", self._on_key_press)
        
        # Also bind to canvas
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.bind("<FocusIn>", lambda e: None)  # Enable focus
        
        # Make canvas focusable
        self.canvas.configure(takefocus=True)
        
        # Bind specific keys
        movement_keys = ["<Up>", "<Down>", "<Left>", "<Right>", 
                        "<w>", "<s>", "<a>", "<d>",
                        "<W>", "<S>", "<A>", "<D>"]
        
        for key in movement_keys:
            self.bind_all(key, self._on_key_press)
            self.canvas.bind(key, self._on_key_press)

    def _show_empty_game_state(self) -> None:
        """Show empty state when no maze is loaded."""
        self.canvas.delete("all")
        
        # Center text
        text_x = 200
        text_y = 150
        
        self.canvas.create_text(
            text_x, text_y - 30,
            text="🎯",
            font=("Arial", 48),
            fill="gray"
        )
        
        self.canvas.create_text(
            text_x, text_y,
            text="No maze loaded",
            font=("Arial", 14, "bold"),
            fill="gray"
        )
        
        self.canvas.create_text(
            text_x, text_y + 25,
            text="Load a maze from the View Mazes page\nor generate a new one",
            font=("Arial", 10),
            fill="gray"
        )
        
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _play_game(self) -> None:
        """Start or resume the game."""
        try:
            if self.maze is None:
                messagebox.showwarning("Warning", "No maze loaded. Please load a maze first.")
                return
            
            if self.game_state == GameState.IDLE:
                # Start new game
                self.original_maze = copy.deepcopy(self.maze)
                self.maze_engine = MazeGame(self.maze)
                
                # Generate player and exit
                self.maze_engine.generate_player()
                self.maze_engine.generate_exit()
                
                # Update our maze reference
                self.maze = self.maze_engine.maze
                
                # Reset statistics
                self.start_time = time.time()
                self.moves_count = 0
                self.score = 1000  # Starting score
                
                self.game_state = GameState.PLAYING
                
            elif self.game_state == GameState.PAUSED:
                # Resume game
                self.game_state = GameState.PLAYING
            
            self._update_ui_state()
            self._draw_maze()
            
            # Ensure focus for key events
            self.focus_set()
            self.canvas.focus_set()
            
            print(f"Game started. State: {self.game_state}")
            
        except Exception as e:
            logging.error(f"Error starting game: {e}")
            messagebox.showerror("Error", f"Failed to start game: {e}")
            print(f"Error starting game: {e}")

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
                self._draw_maze()
            
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
        if self.game_state == GameState.IDLE:
            self.play_btn.configure(state="normal" if self.maze else "disabled")
            self.pause_btn.configure(state="disabled")
            self.restart_btn.configure(state="disabled")
            self.status_vars["state"].set("Ready to play")
            
        elif self.game_state == GameState.PLAYING:
            self.play_btn.configure(state="disabled")
            self.pause_btn.configure(state="normal")
            self.restart_btn.configure(state="normal")
            self.status_vars["state"].set("Playing...")
            
        elif self.game_state == GameState.PAUSED:
            self.play_btn.configure(state="normal", text="▶️ Resume")
            self.pause_btn.configure(state="disabled")
            self.restart_btn.configure(state="normal")
            self.status_vars["state"].set("Paused")
            
        elif self.game_state == GameState.WON:
            self.play_btn.configure(state="disabled")
            self.pause_btn.configure(state="disabled")
            self.restart_btn.configure(state="normal")
            self.status_vars["state"].set("Congratulations! You won!")
            
        # Reset play button text if not paused
        if self.game_state != GameState.PAUSED:
            self.play_btn.configure(text="▶️ Play")

    def _draw_maze(self) -> None:
        """Draw the maze on the canvas."""
        if not self.maze:
            self._show_empty_game_state()
            return
        
        try:
            self.canvas.delete("all")
            
            rows = len(self.maze)
            cols = len(self.maze[0]) if rows > 0 else 0
            
            for i in range(rows):
                for j in range(cols):
                    x1 = j * self.CELL_SIZE
                    y1 = i * self.CELL_SIZE
                    x2 = x1 + self.CELL_SIZE
                    y2 = y1 + self.CELL_SIZE
                    
                    # Determine cell color
                    cell_value = self.maze[i][j]
                    fill_color = self._get_cell_color(cell_value)
                    
                    # Draw cell
                    self.canvas.create_rectangle(
                        x1, y1, x2, y2,
                        fill=fill_color,
                        outline="gray",
                        width=1
                    )
                    
                    # Add special symbols for player and exit
                    if cell_value == CellType.PLAYER.value:
                        self._draw_player(x1, y1)
                    elif cell_value == CellType.EXIT.value:
                        self._draw_exit(x1, y1)
            
            # Update scroll region
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            
        except Exception as e:
            logging.error(f"Error drawing maze: {e}")

    def _get_cell_color(self, cell_value: int) -> str:
        """
        Get color for a cell based on its value.
        
        Args:
            cell_value: Cell value from maze
            
        Returns:
            Color string
        """
        color_map = {
            CellType.WALL.value: self.COLORS["wall"],
            CellType.ROOM.value: self.COLORS["room"],
            CellType.PLAYER.value: self.COLORS["player"],
            CellType.EXIT.value: self.COLORS["exit"],
            CellType.VISITED.value: self.COLORS["visited"],
        }
        return color_map.get(cell_value, self.COLORS["wall"])

    def _draw_player(self, x: int, y: int) -> None:
        """Draw player symbol."""
        center_x = x + self.CELL_SIZE // 2
        center_y = y + self.CELL_SIZE // 2
        radius = self.CELL_SIZE // 3
        
        self.canvas.create_oval(
            center_x - radius, center_y - radius,
            center_x + radius, center_y + radius,
            fill=self.COLORS["player"],
            outline="white",
            width=2
        )
        
        # Add player symbol
        self.canvas.create_text(
            center_x, center_y,
            text="😊",
            font=("Arial", 12)
        )

    def _draw_exit(self, x: int, y: int) -> None:
        """Draw exit symbol."""
        center_x = x + self.CELL_SIZE // 2
        center_y = y + self.CELL_SIZE // 2
        
        self.canvas.create_text(
            center_x, center_y,
            text="🏁",
            font=("Arial", 16)
        )

    def _on_key_press(self, event):
        """Handle key press events for player movement."""
        if self.game_state != GameState.PLAYING or not self.maze_engine:
            return
        
        # Map keys to movement characters expected by mazeGame
        key_to_move = {
            "Up": "w",
            "Down": "s", 
            "Left": "a",
            "Right": "d",
            "w": "w",
            "s": "s", 
            "a": "a",
            "d": "d",
            "W": "w",
            "S": "s",
            "A": "a", 
            "D": "d"
        }
        
        move_char = key_to_move.get(event.keysym)
        if move_char:
            try:
                # Print debug info
                print(f"Key pressed: {event.keysym}, mapped to: {move_char}")
                
                moved = self.maze_engine.move_player(move_char)
                print(f"Player moved: {moved}")
                
                if moved:
                    self.moves_count += 1
                    self.score = max(0, self.score - 1)  # Decrease score with each move
                    
                    # Update the maze with new positions
                    self.maze = self.maze_engine.maze
                    
                    # Check if player reached exit
                    if hasattr(self.maze_engine, 'game_won') and self.maze_engine.game_won:
                        self._handle_game_won()
                    else:
                        self._draw_maze()
                
            except Exception as e:
                logging.error(f"Error moving player: {e}")
                print(f"Error moving player: {e}")
            
            # Return "break" only for handled keys to prevent event propagation
            return "break"

    def _handle_game_won(self) -> None:
        """Handle game completion."""
        self.game_state = GameState.WON
        
        # Calculate time bonus
        if self.start_time:
            time_taken = time.time() - self.start_time
            time_bonus = max(0, 500 - int(time_taken))
            self.score += time_bonus
            
            # Update best time
            if time_taken < self.best_time:
                self.best_time = time_taken
        
        self._update_ui_state()
        self._draw_maze()
        
        # Show congratulations
        messagebox.showinfo(
            "Congratulations!",
            f"You completed the maze!\n\n"
            f"Moves: {self.moves_count}\n"
            f"Time: {self._format_time(time_taken)}\n"
            f"Score: {self.score}"
        )

    def _on_canvas_click(self, event) -> None:
        """Handle canvas click events."""
        # Set focus to enable keyboard input
        self.focus_set()
        self.canvas.focus_set()
        
        # Update focus indicator
        if hasattr(self, 'focus_indicator'):
            self.focus_indicator.config(text="Controls active", foreground="green")
            
        print("Canvas clicked, focus set for keyboard input")

    def _on_mousewheel(self, event) -> None:
        """Handle mouse wheel scrolling."""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

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
                # Try moving down
                moved = self.maze_engine.move_player("s")
                print(f"Test move result: {moved}")
                if moved:
                    self.moves_count += 1
                    self.maze = self.maze_engine.maze
                    self._draw_maze()
                    messagebox.showinfo("Test", "Move successful!")
                else:
                    messagebox.showinfo("Test", "Move blocked")
            except Exception as e:
                messagebox.showerror("Test Error", f"Error: {e}")
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
            self._draw_maze()
            
            logging.info("Maze set successfully")
            
        except Exception as e:
            logging.error(f"Error setting maze: {e}")
            messagebox.showerror("Error", f"Failed to load maze: {e}")

    def refresh(self) -> None:
        """Refresh the game page."""
        if self.maze:
            self._draw_maze()

    def on_show(self, **kwargs) -> None:
        """
        Called when the frame is shown.
        
        Args:
            **kwargs: Additional arguments, may contain 'maze'
        """
        if 'maze' in kwargs:
            self.set_maze(kwargs['maze'])
        
        # Ensure focus for key events
        self.after(100, self._set_focus)
        
        logging.debug("MazeGamePage shown")

    def _set_focus(self) -> None:
        """Set focus to enable keyboard input."""
        self.focus_set()
        self.canvas.focus_set()
        
        # Update focus indicator
        if hasattr(self, 'focus_indicator'):
            self.focus_indicator.config(text="Controls active", foreground="green")
            
        print("Focus set for MazeGamePage")

