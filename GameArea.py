import tkinter as tk
import numpy as np
import matplotlib.cm as cm
import matplotlib.colors as mcolors
from MazeConfig import CellType


class GameArea(tk.Canvas):
    """
    Enhanced maze display canvas with DP visualization support.
    Handles maze rendering, value function visualization, and policy display.
    """
        
    # Display configuration constants
    CELL_SIZE = 40
    COLORS = {
        "wall": "#2c3e50",
        "room": "#ecf0f1", 
        "player": "#3498db",
        "exit": "#e74c3c",
        "visited": "#bdc3c7",
        "background": "#34495e",
        "policy_arrow": "#e74c3c"
    }

    def __init__(self, parent, **kwargs):
        """Initialize the maze display canvas."""
        # Initialize canvas with display settings
        canvas_config = {
            'bg': self.COLORS["background"],
            'highlightthickness': 2,
            'highlightbackground': "#7f8c8d",
            'relief': 'sunken',
            'bd': 2,
            **kwargs
        }
        super().__init__(parent, **canvas_config)
        
        # Maze data
        self.maze = None
        
        # DP visualization data
        self.value_function = None
        self.policy = None
        self.show_values = False
        self.show_policy = False
        
        # Visualization settings
        self.value_colormap = 'viridis'
        self.arrow_size = 0.3
        
        # Element tracking for overlays
        self.value_elements = []
        self.policy_elements = []
        
        # Show empty state initially
        self.show_empty_state()
    
    def show_empty_state(self) -> None:
        """Show empty state when no maze is loaded."""
        self.delete("all")
        
        # Get canvas dimensions
        self.update_idletasks()
        canvas_width = self.winfo_width() or 400
        canvas_height = self.winfo_height() or 300
        
        # Center coordinates
        text_x = canvas_width // 2
        text_y = canvas_height // 2
        
        # Create centered empty state display
        self.create_text(
            text_x, text_y - 20,
            text="🎮",
            font=("Arial", 48),
            fill="#95a5a6",
            tags="empty_state"
        )
        
        self.create_text(
            text_x, text_y + 20,
            text="No maze loaded",
            font=("Arial", 16, "bold"),
            fill="#ecf0f1",
            tags="empty_state"
        )
    
    def load_maze(self, maze_data: np.ndarray) -> None:
        """
        Load and display a maze.
        
        Args:
            maze_data: 2D numpy array representing the maze
        """
        self.maze = maze_data.copy()
        self._draw_maze()
    
    def load_value_function(self, values: np.ndarray) -> None:
        """
        Load value function for visualization.
        
        Args:
            values: 2D numpy array of state values
        """
        self.value_function = values.copy()
        print(self.value_function)
    
    def load_policy(self, policy: np.ndarray) -> None:
        """
        Load policy for visualization.
        
        Args:
            policy: 2D numpy array of actions (0=up, 1=right, 2=down, 3=left)
        """
        self.policy = policy.copy()
    
    def set_show_values(self, show: bool) -> None:
        """Toggle value function display."""
        self.show_values = show
        if self.maze is not None:
            self._draw_maze()
    
    def set_show_policy(self, show: bool) -> None:
        """Toggle policy display."""
        self.show_policy = show
        if self.maze is not None:
            self._draw_maze()
    
    def _draw_maze(self) -> None:
        """Draw the maze on the canvas."""
        self.delete("all")
        self._clear_overlays()
        
        if self.maze is None:
            self.show_empty_state()
            return
        
        rows, cols = self.maze.shape
        canvas_width = cols * self.CELL_SIZE
        canvas_height = rows * self.CELL_SIZE
        
        # Configure canvas size and scroll region
        self.configure(scrollregion=(0, 0, canvas_width, canvas_height))
        
        # Draw maze cells
        for row in range(rows):
            for col in range(cols):
                self._draw_cell(row, col)
        
        # Draw overlays if enabled
        if self.show_values and self.value_function is not None:
            self._draw_values()
        
        if self.show_policy and self.policy is not None:
            self._draw_policy()
    
    def _clear_overlays(self) -> None:
        """Clear value and policy overlays."""
        for element in self.value_elements:
            self.delete(element)
        for element in self.policy_elements:
            self.delete(element)
        self.value_elements.clear()
        self.policy_elements.clear()
    
    def _draw_cell(self, row: int, col: int) -> None:
        """Draw a single maze cell."""
        x1 = col * self.CELL_SIZE
        y1 = row * self.CELL_SIZE
        x2 = x1 + self.CELL_SIZE
        y2 = y1 + self.CELL_SIZE
        
        cell_value = self.maze[row, col]
        
        # Determine cell color based on type
        if cell_value == CellType.WALL.value:
            color = self.COLORS["wall"]
        elif cell_value == CellType.EXIT.value:
            color = self.COLORS["exit"]
        elif cell_value == CellType.PLAYER.value:
            color = self.COLORS["player"]
        elif cell_value == CellType.VISITED.value:
            color = self.COLORS["visited"]
        else:  # Room, unvisited, or other walkable cells
            # Use value-based coloring if values are shown
            if self.show_values and self.value_function is not None and cell_value != CellType.WALL.value:
                color = self._get_value_color(row, col)
            else:
                color = self.COLORS["room"]
        
        # Create cell rectangle
        self.create_rectangle(
            x1, y1, x2, y2,
            fill=color,
            outline="#7f8c8d",
            width=1,
            tags=f"cell_{row}_{col}"
        )
        
        # Add special symbols for exit
        if cell_value == CellType.EXIT.value:
            self.create_text(
                x1 + self.CELL_SIZE // 2,
                y1 + self.CELL_SIZE // 2,
                text="🚪",
                font=("Arial", int(self.CELL_SIZE * 0.6)),
                tags=f"exit_symbol_{row}_{col}"
            )
        # Add symbol for player
        elif cell_value == CellType.PLAYER.value:
            self.create_oval(
                x1 + 5, y1 + 5, x2 - 5, y2 - 5,
                fill=self.COLORS["player"],
                outline="#2980b9",
                width=2,
                tags=f"player_symbol_{row}_{col}"
            )
    
    def _get_value_color(self, row: int, col: int) -> str:
        """Get color for cell based on its value."""
        if self.value_function is None:
            return self.COLORS["room"]
        
        value = self.value_function[row, col]
        
        # Normalize value to 0-1 range
        min_val = np.min(self.value_function)
        max_val = np.max(self.value_function)
        
        if max_val == min_val:
            normalized = 0.5
        else:
            normalized = (value - min_val) / (max_val - min_val)
        
        # Get color from colormap
        colormap = cm.get_cmap(self.value_colormap)
        rgba = colormap(normalized)
        
        # Convert to hex
        hex_color = mcolors.rgb2hex(rgba[:3])
        return hex_color
    
    def _draw_values(self) -> None:
        """Draw value function overlay."""
        if self.value_function is None or self.maze is None:
            return
        
        rows, cols = self.maze.shape
        
        for row in range(rows):
            for col in range(cols):
                if self.maze[row, col] != CellType.WALL.value:  # Not a wall
                    value = self.value_function[row, col]
                    
                    x = col * self.CELL_SIZE + self.CELL_SIZE // 2
                    y = row * self.CELL_SIZE + self.CELL_SIZE // 2
                    
                    # Create value text
                    text_id = self.create_text(
                        x, y,
                        text=f"{value:.2f}",
                        font=("Arial", 8, "bold"),
                        fill="black",
                        tags=f"value_{row}_{col}"
                    )
                    
                    self.value_elements.append(text_id)
    
    def _draw_policy(self) -> None:
        """Draw policy arrows overlay."""
        if self.policy is None or self.maze is None:
            return
        
        rows, cols = self.maze.shape
        arrow_size = int(self.CELL_SIZE * self.arrow_size)
        
        # Action to direction mapping
        action_directions = {
            0: (0, -1),    # UP
            1: (1, 0),     # RIGHT
            2: (0, 1),     # DOWN
            3: (-1, 0),    # LEFT
        }
        
        for row in range(rows):
            for col in range(cols):
                if self.maze[row, col] != CellType.WALL.value:  # Not a wall
                    action = self.policy[row, col]
                    
                    if action in action_directions:
                        dx, dy = action_directions[action]
                        
                        x = col * self.CELL_SIZE + self.CELL_SIZE // 2
                        y = row * self.CELL_SIZE + self.CELL_SIZE // 2
                        
                        # Create arrow
                        arrow_id = self.create_line(
                            x, y,
                            x + dx * arrow_size, y + dy * arrow_size,
                            fill=self.COLORS["policy_arrow"],
                            width=3,
                            arrow=tk.LAST,
                            arrowshape=(8, 10, 3),
                            tags=f"policy_{row}_{col}"
                        )
                        
                        self.policy_elements.append(arrow_id)



        