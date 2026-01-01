from botcity.core import DesktopBot
import time
import logging
import os
from grounding import GroundingEngine

import subprocess

class NotepadBot(DesktopBot):
    def __init__(self):
        super().__init__()
        self.grounding = GroundingEngine()
        
    def launch_app_via_icon(self, app_name="Notepad", template_path=None):
        """
        Finds the desktop icon and launches it.
        """
        logging.info(f"Looking for {app_name} on desktop...")
        
        # Minimize all windows to see desktop
        subprocess.run(["powershell", "-command", "(New-Object -ComObject Shell.Application).MinimizeAll()"], shell=True)
        time.sleep(1.0) # Wait for animation
        
        # Click on desktop to clear unwanted selection (e.g. gray/blue highlight on icon)
        from pynput.mouse import Button, Controller
        mouse = Controller()
        try:
             # Move to a neutral spot (top left) and click
             mouse.position = (10, 100)
             time.sleep(0.1)
             mouse.click(Button.left)
             time.sleep(0.5)
        except Exception as e:
             logging.warning(f"Could not click to clear selection: {e}")
        
        # Grounding
        coords = self.grounding.ground_icon(label=app_name, template_path=template_path)
        
        if not coords:
            logging.error(f"Could not find {app_name} icon.")
            return False
            
        x, y = coords
        
        # Use pynput for direct input to bypass BotCity's element state checks
        from pynput.mouse import Button, Controller
        mouse = Controller()
        
        # Move and Click explicitly at coordinates
        self.mouse_move(x, y)
        time.sleep(0.5)
        
        # Direct left click (Select)
        mouse.press(Button.left)
        mouse.release(Button.left)
        
        time.sleep(0.5)
        
        # Launch using ENTER key only (Prevents double opening)
        from pynput.keyboard import Key, Controller as KeyboardController
        keyboard = KeyboardController()
        keyboard.press(Key.enter)
        keyboard.release(Key.enter)
        
        # Wait for window
        if self.wait_for_window(title_re=".*Notepad.*", timeout=10000):
            logging.info("Notepad launched successfully.")
            return True
        else:
            logging.error("Notepad did not appear.")
            return False

    def wait_for_window(self, title_re, timeout=10000):
        """
        Waits for the Notepad process to be active.
        """
        start = time.time()
        while (time.time() - start) * 1000 < timeout:
            # Check if notepad process exists via PowerShell
            # We filter by MainWindowTitle to ensure it's actually open
            cmd = "Get-Process | Where-Object {$_.MainWindowTitle -match 'Notepad'} | Select-Object -ExpandProperty Id"
            result = subprocess.run(["powershell", "-command", cmd], capture_output=True, text=True, shell=True)
            
            if result.stdout.strip():
                time.sleep(0.5) # Give it a moment to render
                return True
            
            time.sleep(1.0)
            
        return False

    def write_post(self, title, body):
        """
        Types the content into Notepad.
        """
        # Ensure window is focused and ready
        time.sleep(1.0)
        
        content = f"Title: {title}\n\n{body}"
        # Use pyperclip to manually set clipboard first to ensure "vsv" doesn't happen
        # BotCity's paste method sometimes relies on internal buffers.
        import pyperclip
        pyperclip.copy(content)
        time.sleep(0.5) # Wait for clipboard to take
        
        self.control_v() # Explicit Paste shortcut
        time.sleep(1.0)

    def save_file(self, full_path):
        """
        Saves the file to the specific path.
        """
        self.control_s() # Ctrl+S
        time.sleep(1.0)
        
        # Wait for Save As dialog?
        # We assume it pops up.
        
        # Type full path
        self.paste(full_path)
        time.sleep(0.5)
        self.enter()
        
        # Handle "Confirm Save As" if it exists (overwrite)
        # Maybe wait a sec and see if a popup for "Do you want to replace it?" appears.
        time.sleep(1.0)
        # Primitive "Yes" handling: If we are still in dialog? Hard to know without finding "Yes" button image.
        # We will assume unique filenames (post_id) avoid this usually.
        # If we need to overwrite, usually pressing 'y' works in some dialogs or Alt+Y.
        
        # Wait for save to finish
        time.sleep(1.0)

    def close_app(self):
        self.alt_f4()
        time.sleep(1.0)
