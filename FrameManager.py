import tkinter as tk
from tkinter import messagebox
import logging
import functools
from typing import Callable, Any, Optional

class FrameManager:
    """Manager for handling frame transitions and state."""
    
    def __init__(self):
        self.frames = {}
        self.current_frame = None
        self.frame_history = []
    
    def register_frame(self, name: str, frame: tk.Frame) -> None:
        """Register a frame with the manager."""
        self.frames[name] = frame
    
    def show_frame(self, name: str, **kwargs) -> bool:
        """Show a frame by name."""
        if name not in self.frames:
            logging.error(f"Frame '{name}' not found")
            return False
        
        try:
            # Hide current frame
            if self.current_frame:
                self.current_frame.pack_forget()
                self.frame_history.append(self.current_frame)
            
            # Show new frame
            frame = self.frames[name]
            self.current_frame = frame
            frame.pack(fill=tk.BOTH, expand=True)
            frame.tkraise()
            
            # Call frame methods if they exist
            if hasattr(frame, 'on_show'):
                frame.on_show(**kwargs)
            elif hasattr(frame, "refresh") and callable(getattr(frame, "refresh")):
                frame.refresh()
            
            if 'maze' in kwargs and hasattr(frame, "set_maze") and callable(getattr(frame, "set_maze")):
                frame.set_maze(kwargs['maze'])
            
            return True
        except Exception as e:
            logging.error(f"Error showing frame '{name}': {e}")
            return False
    
    def go_back(self) -> bool:
        """Go back to the previous frame."""
        if not self.frame_history:
            return False
        
        previous_frame = self.frame_history.pop()
        if self.current_frame:
            self.current_frame.pack_forget()
        
        self.current_frame = previous_frame
        previous_frame.pack(fill=tk.BOTH, expand=True)
        previous_frame.tkraise()
        
        return True


def confirm_action(title: str, message: str) -> bool:
    """
    Show a confirmation dialog.
    
    Args:
        title: Dialog title
        message: Dialog message
        
    Returns:
        True if user confirmed, False otherwise
    """
    return messagebox.askyesno(title, message)


def show_info(title: str, message: str) -> None:
    """Show an information dialog."""
    messagebox.showinfo(title, message)


def show_warning(title: str, message: str) -> None:
    """Show a warning dialog."""
    messagebox.showwarning(title, message)


def show_error(title: str, message: str) -> None:
    """Show an error dialog."""
    messagebox.showerror(title, message)
