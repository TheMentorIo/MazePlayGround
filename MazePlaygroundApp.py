import tkinter as tk
from tkinter import ttk, messagebox
import logging
import sys
import os
from typing import Dict, Optional, Any
from AppConfig import AppConfig
from FrameManager import FrameManager
from StyleManager import StyleManager
from MainFrame import MainFrame

class MazePlaygroundApp(tk.Tk):
    def __init__(self):
        """Initialize the main application."""
        super().__init__()
        
        # Initialize configuration
        self.config = AppConfig()
        self.frame_manager = FrameManager()
        self.style_manager = StyleManager(self)
        self.container = ttk.Frame(self)
        self.container.pack(fill=tk.BOTH, expand=True, padx=self.config.PADDING, pady=self.config.PADDING)
        self.setup_window()
        self.apply_theme()
        self.initialize_frames()
        self.create_navigation()
        self.show_initial_frame()
        
        logging.info("Maze Playground Application initialized successfully")

    def show_initial_frame(self) -> None:
        """Show the initial frame when application starts."""
        self.show_frame("MainFrame")

    def create_navigation(self) -> None:
        """Create the navigation bar."""
        nav_frame = ttk.Frame(self.container)
        nav_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Home button with better styling
        home_btn = ttk.Button(
            nav_frame,
            text="🏠 Home",
            command=lambda: self.show_frame("MainFrame")
        )
        home_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Add separator
        ttk.Separator(nav_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)

    def initialize_frames(self) -> None:
        """Initialize all application frames."""
        frame_classes = {
            "MainFrame": MainFrame,
            "MazeGenerator": GenerateMazeFrame,
            # "ViewMazesPage": ViewMazesPage,
            # "MazeGamePage": MazeGamePage
        }
        
        for frame_name, frame_class in frame_classes.items():
            try:
                frame = frame_class(self.container, self)
                self.frame_manager.register_frame(frame_name, frame)
                logging.debug(f"Successfully initialized {frame_name}")
            except Exception as e:
                logging.error(f"Failed to initialize {frame_name}: {e}")
                messagebox.showerror(
                    "Initialization Error",
                    f"Failed to initialize {frame_name}.\nError: {e}"
                )
    def apply_theme(self) -> None:
        """Apply the selected theme to the application."""
        self.style_manager.apply_theme(self.config.THEME)

    def setup_window(self):
        """Configure the main application window."""
        self.title(self.config.WINDOW_TITLE)
        self.geometry(self.config.WINDOW_GEOMETRY)
        self.minsize(*self.config.MIN_WINDOW_SIZE)
        
        # Configure window closing behavior
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self) -> None:
        """Handle application closing event."""
        if messagebox.askokcancel("Quit", "Do you want to quit the Maze Playground?"):
            logging.info("Application closing")
            self.destroy()
    
    def run(self) -> None:
        """Start the application main loop."""
        try:
            self.mainloop()
        except KeyboardInterrupt:
            logging.info("Application interrupted by user")
        except Exception as e:
            logging.error(f"Unexpected error in main loop: {e}")
            messagebox.showerror("Fatal Error", f"An unexpected error occurred: {e}")
        finally:
            logging.info("Application terminated")

    def show_frame(self, frame_name: str, maze: Optional[Any] = None) -> None:
        """
        Show a specific frame by name.
        
        Args:
            frame_name: Name of the frame to show
            maze: Optional maze data to pass to the frame
        """
        kwargs = {}
        if maze is not None:
            kwargs['maze'] = maze
            
        success = self.frame_manager.show_frame(frame_name, **kwargs)
        if success:
            logging.info(f"Successfully showed frame: {frame_name}")
        else:
            messagebox.showerror("Error", f"Failed to show {frame_name}")

def main() -> None:
    """Main entry point for the application."""
    try:
        app = MazePlaygroundApp()
        app.run()
    except Exception as e:
        logging.error(f"Failed to start application: {e}")
        messagebox.showerror("Startup Error", f"Failed to start application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()