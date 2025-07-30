"""
Lightweight Maze Block Widget for displaying individual maze thumbnails.
Optimized for performance with many maze items.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Callable

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logging.warning("PIL not available, using basic image handling")


class MazeBlockWidget:
    """
    Lightweight widget for displaying maze thumbnails.
    
    Uses composition instead of inheritance for better performance.
    Only creates GUI elements when needed (lazy loading).
    """
    
    THUMBNAIL_SIZE = (120, 120)  # Smaller for better performance
    
    def __init__(self, parent: tk.Widget, controller, image_path: str):
        """
        Initialize maze block widget.
        
        Args:
            parent: Parent widget (for compatibility, not used in lightweight version)
            controller: Main application controller
            image_path: Path to the maze image file
        """
        self.controller = controller
        self.image_path = Path(image_path)
        self.on_select = None  # Can be set later if needed
        self.maze_data: Optional[Dict[str, Any]] = None
        self._widget_created = False
        self._thumbnail_loaded = False
        self.container = None
        self.photo = None
        
        # Cached metadata
        self._metadata_cache = None
        
    def create_widget(self, parent: tk.Widget) -> tk.Widget:
        """
        Create the actual GUI widget (lazy creation).
        
        Args:
            parent: Parent widget
            
        Returns:
            Created widget container
        """
        if self._widget_created:
            return self.container
            
        try:
            # Create lightweight container
            self.container = tk.Frame(parent, relief="flat", bd=1, bg="#f0f0f0")
            self._create_content()
            self._widget_created = True
            
        except Exception as e:
            logging.error(f"Error creating maze widget for {self.image_path}: {e}")
            self.container = self._create_error_widget(parent, str(e))
            
        return self.container

    def _create_content(self) -> None:
        """Create lightweight content."""
        # Create compact layout
        self._create_thumbnail_compact()
        self._create_info_compact()
        self._create_actions_compact()
        
    def _create_thumbnail_compact(self) -> None:
        """Create compact thumbnail display."""
        try:
            # Lazy load thumbnail
            if not self._thumbnail_loaded:
                self._load_thumbnail()
                
            if self.photo:
                # Create simple thumbnail label
                thumbnail_label = tk.Label(
                    self.container, 
                    image=self.photo, 
                    bg="#f0f0f0",
                    cursor="hand2"
                )
                thumbnail_label.pack(pady=2)
                thumbnail_label.bind("<Button-1>", self._on_thumbnail_click)
                thumbnail_label.bind("<Double-Button-1>", self._play_maze)
            else:
                # Fallback text
                tk.Label(
                    self.container, 
                    text="🖼️", 
                    font=("Arial", 20),
                    bg="#f0f0f0"
                ).pack(pady=5)
                
        except Exception as e:
            logging.error(f"Error creating thumbnail: {e}")
            
    def _load_thumbnail(self) -> None:
        """Load thumbnail image efficiently."""
        try:
            if PIL_AVAILABLE:
                # Use PIL for better quality and smaller memory footprint
                with Image.open(self.image_path) as img:
                    # More aggressive resizing for performance
                    img.thumbnail(self.THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
                    self.photo = ImageTk.PhotoImage(img)
            else:
                # Basic tkinter fallback
                self.photo = tk.PhotoImage(file=str(self.image_path))
                # Simple subsample for basic resizing
                factor = max(
                    self.photo.width() // self.THUMBNAIL_SIZE[0],
                    self.photo.height() // self.THUMBNAIL_SIZE[1]
                )
                if factor > 1:
                    self.photo = self.photo.subsample(factor, factor)
                    
            self._thumbnail_loaded = True
            
        except Exception as e:
            logging.error(f"Error loading thumbnail: {e}")
            self.photo = None

    def _create_info_compact(self) -> None:
        """Create compact info display."""
        metadata = self._get_metadata()
        
        # Single line info display
        info_text = f"{metadata.get('size', '?')} • {metadata.get('date', '?')}"
        
        info_label = tk.Label(
            self.container,
            text=info_text,
            font=("Arial", 8),
            bg="#f0f0f0",
            fg="#666666"
        )
        info_label.pack(pady=1)
        
    def _create_actions_compact(self) -> None:
        """Create compact action buttons."""
        # Single button frame
        btn_frame = tk.Frame(self.container, bg="#f0f0f0")
        btn_frame.pack(fill=tk.X, pady=2)
        
        # Play button (primary action)
        play_btn = tk.Button(
            btn_frame,
            text="▶",
            font=("Arial", 10),
            width=3,
            command=self._play_maze,
            bg="#4CAF50",
            fg="white",
            relief="flat",
            cursor="hand2"
        )
        play_btn.pack(side=tk.LEFT, padx=(0, 2))
        
        # View button
        view_btn = tk.Button(
            btn_frame,
            text="👁",
            font=("Arial", 8),
            width=3,
            command=self._view_details,
            bg="#2196F3",
            fg="white",
            relief="flat",
            cursor="hand2"
        )
        view_btn.pack(side=tk.LEFT, padx=1)
        
        # Delete button
        delete_btn = tk.Button(
            btn_frame,
            text="🗑",
            font=("Arial", 8),
            width=3,
            command=self._delete_maze,
            bg="#f44336",
            fg="white",
            relief="flat",
            cursor="hand2"
        )
        delete_btn.pack(side=tk.RIGHT)

    def _create_error_widget(self, parent: tk.Widget, error_msg: str) -> tk.Widget:
        """Create error display widget."""
        error_frame = tk.Frame(parent, bg="#ffebee", relief="solid", bd=1)
        
        tk.Label(
            error_frame, 
            text="⚠️", 
            font=("Arial", 16),
            bg="#ffebee"
        ).pack(pady=5)
        
        tk.Label(
            error_frame, 
            text="Error", 
            font=("Arial", 9, "bold"),
            bg="#ffebee",
            fg="#c62828"
        ).pack()
        
        return error_frame

    def _get_metadata(self) -> Dict[str, str]:
        """Get cached metadata efficiently."""
        if self._metadata_cache is None:
            self._metadata_cache = self._parse_filename()
        return self._metadata_cache
        
    def _load_maze_data_lazy(self) -> Optional[Dict[str, Any]]:
        """Load maze data only when needed."""
        if self.maze_data is None:
            try:
                filename_stem = self.image_path.stem
                json_path = self.image_path.parent.parent / "json" / f"{filename_stem}.json"
                
                if json_path.exists():
                    with open(json_path, 'r') as file:
                        self.maze_data = json.load(file)
                        
            except Exception as e:
                logging.error(f"Error loading maze data: {e}")
                
        return self.maze_data

    def destroy(self) -> None:
        """Clean up resources."""
        if self.container:
            self.container.destroy()
        self.photo = None
        self.maze_data = None
        self._metadata_cache = None

    def _parse_filename(self) -> Dict[str, str]:
        """
        Parse metadata from filename.
        
        Returns:
            Dictionary with parsed metadata
        """
        try:
            filename_stem = self.image_path.stem
            parts = filename_stem.split("_")
            
            if len(parts) >= 4:
                return {
                    "size": parts[1],
                    "date": self._format_date(parts[2]),
                    "time": self._format_time(parts[3])
                }
            else:
                return {
                    "size": "Unknown",
                    "date": "Unknown", 
                    "time": "Unknown"
                }
        except Exception as e:
            logging.error(f"Error parsing filename: {e}")
            return {"size": "Unknown", "date": "Unknown", "time": "Unknown"}

    def _format_date(self, date_str: str) -> str:
        """
        Format date string for display.
        
        Args:
            date_str: Date string from filename
            
        Returns:
            Formatted date string
        """
        try:
            if len(date_str) == 8:  # YYYYMMDD format
                year = date_str[:4]
                month = date_str[4:6]
                day = date_str[6:8]
                return f"{day}/{month}/{year}"
            return date_str
        except Exception:
            return date_str

    def _format_time(self, time_str: str) -> str:
        """
        Format time string for display.
        
        Args:
            time_str: Time string from filename
            
        Returns:
            Formatted time string
        """
        try:
            if len(time_str) == 6:  # HHMMSS format
                hour = time_str[:2]
                minute = time_str[2:4]
                second = time_str[4:6]
                return f"{hour}:{minute}:{second}"
            return time_str
        except Exception:
            return time_str

    def _play_maze(self, event=None) -> None:
        """Play the maze game."""
        try:
            maze_data = self._load_maze_data_lazy()
            if maze_data:
                maze = maze_data.get("maze")
                self.controller.show_frame("MazeGamePage", maze)
            else:
                messagebox.showwarning("Warning", "Maze data not available")
        except Exception as e:
            logging.error(f"Error playing maze: {e}")
            messagebox.showerror("Error", f"Failed to play maze: {e}")

    def _view_details(self) -> None:
        """View detailed information about the maze."""
        try:
            details = f"""Maze Details:
File: {self.image_path.name}
Size: {self._get_file_size()}

{self._get_maze_details()}"""
            messagebox.showinfo("Maze Details", details)
        except Exception as e:
            logging.error(f"Error viewing details: {e}")

    def _delete_maze(self) -> None:
        """Delete the maze files."""
        try:
            result = messagebox.askyesno(
                "Confirm Delete",
                f"Delete this maze?\n\n{self.image_path.name}"
            )
            
            if result:
                # Delete files
                self.image_path.unlink(missing_ok=True)
                
                json_path = self.image_path.parent.parent / "json" / f"{self.image_path.stem}.json"
                json_path.unlink(missing_ok=True)
                
                # Cleanup and notify
                self.destroy()
                
                # Refresh parent view if possible
                try:
                    self.controller.frame_manager.frames["ViewMazesPage"].refresh()
                except Exception:
                    pass
                    
                messagebox.showinfo("Success", "Maze deleted successfully")
                
        except Exception as e:
            logging.error(f"Error deleting maze: {e}")
            messagebox.showerror("Error", f"Failed to delete maze: {e}")

    def _on_thumbnail_click(self, event) -> None:
        """Handle thumbnail click."""
        if self.on_select:
            self.on_select(self)
        else:
            self._view_details()

    def _get_file_size(self) -> str:
        """Get formatted file size."""
        try:
            size_bytes = self.image_path.stat().st_size
            if size_bytes < 1024:
                return f"{size_bytes} B"
            elif size_bytes < 1024*1024:
                return f"{size_bytes/1024:.1f} KB"
            else:
                return f"{size_bytes/(1024*1024):.1f} MB"
        except Exception:
            return "Unknown"

    def _get_maze_details(self) -> str:
        """Get detailed maze information."""
        maze_data = self._load_maze_data_lazy()
        if not maze_data:
            return "Maze data not available"
        
        try:
            maze = maze_data.get("maze", [])
            if not maze:
                return "No maze data found"
            
            height = len(maze)
            width = len(maze[0]) if maze else 0
            total_cells = height * width
            room_cells = sum(row.count(1) for row in maze)
            wall_cells = total_cells - room_cells
            
            return f"""Dimensions: {width} x {height}
Total Cells: {total_cells}
Room Cells: {room_cells}
Wall Cells: {wall_cells}
Room Coverage: {(room_cells/total_cells*100):.1f}%"""
        except Exception as e:
            return f"Error reading maze data: {e}"


# Backward compatibility alias
MazeBlockFrame = MazeBlockWidget
