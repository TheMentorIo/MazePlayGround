import tkinter as tk
from tkinter import messagebox
import logging
import functools
from typing import Callable, Any, Optional


def safe_execute(func: Callable, *args, **kwargs) -> Optional[Any]:
    """
    Safely execute a function with error handling.
    
    Args:
        func: Function to execute
        *args: Arguments to pass to function
        **kwargs: Keyword arguments to pass to function
        
    Returns:
        Function result or None if error occurred
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logging.error(f"Error executing {func.__name__}: {e}")
        return None


def handle_errors(show_dialog: bool = True):
    """
    Decorator to handle errors in GUI methods.
    
    Args:
        show_dialog: Whether to show error dialog to user
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logging.error(f"Error in {func.__name__}: {e}")
                if show_dialog:
                    messagebox.showerror("Error", f"An error occurred: {e}")
                return None
        return wrapper
    return decorator


def validate_input(value: str, input_type: type, min_val: Optional[float] = None, 
                  max_val: Optional[float] = None) -> bool:
    """
    Validate user input.
    
    Args:
        value: String value to validate
        input_type: Expected type (int, float, str)
        min_val: Minimum value (for numeric types)
        max_val: Maximum value (for numeric types)
        
    Returns:
        True if valid, False otherwise
    """
    try:
        if input_type in (int, float):
            num_val = input_type(value)
            if min_val is not None and num_val < min_val:
                return False
            if max_val is not None and num_val > max_val:
                return False
        elif input_type == str:
            if not value.strip():
                return False
        return True
    except (ValueError, TypeError):
        return False


def center_window(window: tk.Tk, width: int = None, height: int = None) -> None:
    """
    Center a window on the screen.
    
    Args:
        window: Tkinter window to center
        width: Optional width override
        height: Optional height override
    """
    window.update_idletasks()
    
    if width is None:
        width = window.winfo_width()
    if height is None:
        height = window.winfo_height()
    
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    
    window.geometry(f"{width}x{height}+{x}+{y}")


def create_tooltip(widget: tk.Widget, text: str) -> None:
    """
    Create a tooltip for a widget.
    
    Args:
        widget: Widget to add tooltip to
        text: Tooltip text
    """
    def on_enter(event):
        tooltip = tk.Toplevel()
        tooltip.wm_overrideredirect(True)
        tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
        
        label = tk.Label(tooltip, text=text, background="yellow", 
                        relief="solid", borderwidth=1, font=("Arial", 8))
        label.pack()
        
        widget.tooltip = tooltip
    
    def on_leave(event):
        if hasattr(widget, 'tooltip'):
            widget.tooltip.destroy()
            del widget.tooltip
    
    widget.bind("<Enter>", on_enter)
    widget.bind("<Leave>", on_leave)

