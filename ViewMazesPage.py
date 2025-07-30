"""
View Mazes Page for the Maze Playground Application.
Displays a grid of saved mazes with search and filter capabilities.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
import logging
from typing import List, Optional, Tuple
import threading
from pathlib import Path

try:
    from MazeBlockFrame import MazeBlockFrame
    from AppConfig import AppConfig
except ImportError as e:
    logging.error(f"Failed to import required modules: {e}")


class ViewMazesPage(ttk.Frame):
    """
    Page for viewing and managing saved mazes.
    
    Features:
    - Grid layout of maze thumbnails
    - Search functionality
    - Sorting options
    - Refresh capability
    - Error handling
    """
    
    # Configuration constants
    GRID_COLUMNS = 3
    VALID_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.gif', '.bmp')
    THUMBNAIL_SIZE = (150, 150)
    
    def __init__(self, parent: tk.Widget, controller):
        """
        Initialize the View Mazes page.
        
        Args:
            parent: Parent widget
            controller: Main application controller
        """
        super().__init__(parent)
        self.controller = controller
        self.config = AppConfig()
        
        # State variables
        self.maze_files: List[str] = []
        self.filtered_files: List[str] = []
        self.current_search_term = ""
        self.current_sort_option = "name"
        self.is_loading = False
        
        # Initialize UI
        self._create_header()
        self._create_search_filter_section()
        self._create_scrollable_area()
        self._create_status_bar()
        
        # Load mazes on initialization
        self.refresh()
        
        logging.debug("ViewMazesPage initialized successfully")

    def _create_header(self) -> None:
        """Create the page header with title and controls."""
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Title
        title_label = ttk.Label(
            header_frame,
            text="📁 Saved Mazes",
            font=("Arial", 16, "bold")
        )
        title_label.pack(side=tk.LEFT)
        
        # Controls frame
        controls_frame = ttk.Frame(header_frame)
        controls_frame.pack(side=tk.RIGHT)
        
        # Refresh button
        refresh_btn = ttk.Button(
            controls_frame,
            text="🔄 Refresh",
            command=self._refresh_async
        )
        refresh_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Settings button
        settings_btn = ttk.Button(
            controls_frame,
            text="⚙️ Settings",
            command=self._show_settings
        )
        settings_btn.pack(side=tk.RIGHT, padx=(5, 0))

    def _create_search_filter_section(self) -> None:
        """Create search and filter controls."""
        filter_frame = ttk.LabelFrame(self, text="Search & Filter", padding=10)
        filter_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Search section
        search_frame = ttk.Frame(filter_frame)
        search_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._on_search_changed)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=(5, 10), fill=tk.X, expand=True)
        
        # Clear search button
        clear_btn = ttk.Button(
            search_frame,
            text="✕",
            width=3,
            command=self._clear_search
        )
        clear_btn.pack(side=tk.RIGHT)
        
        # Sort section
        sort_frame = ttk.Frame(filter_frame)
        sort_frame.pack(fill=tk.X)
        
        ttk.Label(sort_frame, text="Sort by:").pack(side=tk.LEFT)
        
        self.sort_var = tk.StringVar(value="name")
        sort_combo = ttk.Combobox(
            sort_frame,
            textvariable=self.sort_var,
            values=["name", "date", "size"],
            state="readonly",
            width=15
        )
        sort_combo.pack(side=tk.LEFT, padx=(5, 0))
        sort_combo.bind("<<ComboboxSelected>>", self._on_sort_changed)

    def _create_scrollable_area(self) -> None:
        """Create the scrollable area for maze thumbnails."""
        # Main container
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True)
        
        # Canvas and scrollbar
        self.canvas = tk.Canvas(container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack scrollbar and canvas
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollable frame
        self.scrollable_frame = ttk.Frame(self.canvas)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        # Create window in canvas
        self.canvas_window = self.canvas.create_window(
            (0, 0), 
            window=self.scrollable_frame, 
            anchor="nw"
        )
        
        # Bind canvas resize to update scrollable frame width
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        
        # Bind mousewheel to canvas
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)

    def _create_status_bar(self) -> None:
        """Create status bar at the bottom."""
        self.status_frame = ttk.Frame(self)
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        ttk.Separator(self.status_frame, orient=tk.HORIZONTAL).pack(fill=tk.X)
        
        status_content = ttk.Frame(self.status_frame)
        status_content.pack(fill=tk.X, padx=5, pady=2)
        
        self.status_label = ttk.Label(status_content, text="Ready")
        self.status_label.pack(side=tk.LEFT)
        
        self.progress_bar = ttk.Progressbar(
            status_content,
            mode='indeterminate',
            length=100
        )
        # Don't pack initially - only show when loading

    def _get_mazes_directory(self) -> Path:
        """Get the mazes directory path."""
        mazes_dir = Path(self.config.MAZES_DIR) / "imgs"
        return mazes_dir

    def _load_maze_files(self) -> List[str]:
        """
        Load list of maze image files.
        
        Returns:
            List of image file paths
        """
        try:
            img_dir = self._get_mazes_directory()
            
            if not img_dir.exists():
                logging.warning(f"Mazes directory not found: {img_dir}")
                return []
            
            # Get all valid image files
            image_files = [
                str(f) for f in img_dir.iterdir()
                if f.is_file() and f.suffix.lower() in self.VALID_EXTENSIONS
            ]
            
            logging.info(f"Found {len(image_files)} maze files")
            return image_files
            
        except Exception as e:
            logging.error(f"Error loading maze files: {e}")
            return []

    def _filter_and_sort_files(self, files: List[str]) -> List[str]:
        """
        Filter and sort files based on current criteria.
        
        Args:
            files: List of file paths
            
        Returns:
            Filtered and sorted list of files
        """
        # Filter by search term
        if self.current_search_term:
            files = [
                f for f in files 
                if self.current_search_term.lower() in Path(f).stem.lower()
            ]
        
        # Sort files
        if self.current_sort_option == "name":
            files.sort(key=lambda f: Path(f).stem.lower())
        elif self.current_sort_option == "date":
            files.sort(key=lambda f: Path(f).stat().st_mtime, reverse=True)
        elif self.current_sort_option == "size":
            files.sort(key=lambda f: Path(f).stat().st_size, reverse=True)
        
        return files

    def _display_mazes(self, files: List[str]) -> None:
        """
        Display maze thumbnails in grid layout.
        
        Args:
            files: List of image file paths to display
        """
        try:
            # Clear existing widgets
            for widget in self.scrollable_frame.winfo_children():
                widget.destroy()
            
            if not files:
                self._show_empty_state()
                return
            
            # Create maze blocks in grid
            for i, filepath in enumerate(files):
                try:
                    row = i // self.GRID_COLUMNS
                    col = i % self.GRID_COLUMNS
                    
                    # Create maze block widget and get its container
                    block_widget = MazeBlockFrame(self.scrollable_frame, self.controller, filepath)
                    block_container = block_widget.create_widget(self.scrollable_frame)
                    block_container.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
                    
                except Exception as e:
                    logging.error(f"Error creating maze block for {filepath}: {e}")
                    continue
            
            # Configure grid weights for responsive layout
            for col in range(self.GRID_COLUMNS):
                self.scrollable_frame.columnconfigure(col, weight=1)
                
            self._update_status(f"Displaying {len(files)} mazes")
            
        except Exception as e:
            logging.error(f"Error displaying mazes: {e}")
            self._show_error_state(str(e))

    def _show_empty_state(self) -> None:
        """Show message when no mazes are found."""
        empty_frame = ttk.Frame(self.scrollable_frame)
        empty_frame.pack(expand=True, fill=tk.BOTH, pady=50)
        
        ttk.Label(
            empty_frame,
            text="📂",
            font=("Arial", 48),
            anchor="center"
        ).pack()
        
        ttk.Label(
            empty_frame,
            text="No mazes found",
            font=("Arial", 14, "bold"),
            anchor="center"
        ).pack(pady=(10, 5))
        
        ttk.Label(
            empty_frame,
            text="Generate some mazes to see them here!",
            font=("Arial", 10),
            foreground="gray",
            anchor="center"
        ).pack()

    def _show_error_state(self, error_message: str) -> None:
        """
        Show error message.
        
        Args:
            error_message: Error message to display
        """
        error_frame = ttk.Frame(self.scrollable_frame)
        error_frame.pack(expand=True, fill=tk.BOTH, pady=50)
        
        ttk.Label(
            error_frame,
            text="⚠️",
            font=("Arial", 48),
            anchor="center"
        ).pack()
        
        ttk.Label(
            error_frame,
            text="Error loading mazes",
            font=("Arial", 14, "bold"),
            anchor="center"
        ).pack(pady=(10, 5))
        
        ttk.Label(
            error_frame,
            text=error_message,
            font=("Arial", 10),
            foreground="red",
            anchor="center",
            wraplength=400
        ).pack()

    def _update_status(self, message: str) -> None:
        """
        Update status bar message.
        
        Args:
            message: Status message
        """
        self.status_label.config(text=message)

    def _start_loading(self) -> None:
        """Start loading animation."""
        self.is_loading = True
        self.progress_bar.pack(side=tk.RIGHT, padx=(5, 0))
        self.progress_bar.start(10)
        self._update_status("Loading mazes...")

    def _stop_loading(self) -> None:
        """Stop loading animation."""
        self.is_loading = False
        self.progress_bar.stop()
        self.progress_bar.pack_forget()

    def _refresh_async(self) -> None:
        """Refresh mazes asynchronously to prevent UI blocking."""
        if self.is_loading:
            return
        
        def load_in_background():
            try:
                self._start_loading()
                
                # Load files
                self.maze_files = self._load_maze_files()
                
                # Filter and sort
                self.filtered_files = self._filter_and_sort_files(self.maze_files)
                
                # Schedule UI update on main thread
                self.after(0, lambda: self._display_mazes(self.filtered_files))
                
            except Exception as e:
                logging.error(f"Error in background refresh: {e}")
                self.after(0, lambda: self._show_error_state(str(e)))
            finally:
                self.after(0, self._stop_loading)
        
        thread = threading.Thread(target=load_in_background, daemon=True)
        thread.start()

    def refresh(self) -> None:
        """
        Refresh the maze list.
        Public method called by the application.
        """
        self._refresh_async()

    def _on_search_changed(self, *args) -> None:
        """Handle search term changes."""
        self.current_search_term = self.search_var.get().strip()
        self._apply_filters()

    def _on_sort_changed(self, event=None) -> None:
        """Handle sort option changes."""
        self.current_sort_option = self.sort_var.get()
        self._apply_filters()

    def _apply_filters(self) -> None:
        """Apply current search and sort filters."""
        if self.maze_files:
            self.filtered_files = self._filter_and_sort_files(self.maze_files)
            self._display_mazes(self.filtered_files)

    def _clear_search(self) -> None:
        """Clear the search field."""
        self.search_var.set("")

    def _on_canvas_configure(self, event) -> None:
        """Handle canvas resize to update scrollable frame width."""
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_window, width=canvas_width)

    def _on_mousewheel(self, event) -> None:
        """Handle mouse wheel scrolling."""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _show_settings(self) -> None:
        """Show settings dialog for the mazes view."""
        messagebox.showinfo("Settings", "Settings dialog coming soon!")

    def on_show(self, **kwargs) -> None:
        """
        Called when the frame is shown.
        
        Args:
            **kwargs: Additional arguments
        """
        # Refresh if we haven't loaded or if explicitly requested
        if not self.maze_files or kwargs.get('force_refresh', False):
            self.refresh()
        
        logging.debug("ViewMazesPage shown")
