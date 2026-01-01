from botcity.core import DesktopBot
import time
import logging
import subprocess
from grounding import GroundingEngine
import pyperclip

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
        time.sleep(1.0) 
        
        # Grounding
        coords = self.grounding.ground_icon(label=app_name, template_path=template_path)
        
        if not coords:
            logging.error(f"Could not find {app_name} icon.")
            return False
            
        if not coords:
            logging.error(f"Could not find {app_name} icon.")
            return False
            
        x, y = coords
        logging.info(f"Found icon at Logical Coordinates: ({x}, {y})")
        
        # --- ROBUST INTERACTION BLOCK ---
        # 1. Move using pynput (Direct Hardware Input)
        from pynput.mouse import Button, Controller
        mouse = Controller()
        mouse.position = (x, y)
        time.sleep(0.5)
        
        # 2. Hybrid Clicking Strategy
        # Click 1: Select
        mouse.press(Button.left)
        mouse.release(Button.left)
        time.sleep(0.2)
        
        # Click 2: Double Click
        mouse.press(Button.left)
        mouse.release(Button.left)
        time.sleep(0.1)
        mouse.press(Button.left)
        mouse.release(Button.left)
        time.sleep(0.5)
        
        # Click 3: Enter Key Failsafe
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
        start = time.time()
        while (time.time() - start) * 1000 < timeout:
            cmd = "Get-Process | Where-Object {$_.MainWindowTitle -match 'Notepad'} | Select-Object -ExpandProperty Id"
            result = subprocess.run(["powershell", "-command", cmd], capture_output=True, text=True, shell=True)
            if result.stdout.strip():
                time.sleep(0.5)
                return True
            time.sleep(1.0)
        return False

    def write_post(self, title, body):
        """
        Types the content into Notepad.
        """
        # Ensure window is focused
        time.sleep(1.0)
        
        content = f"Title: {title}\n\n{body}"
        
        # Use Clipboard Paste (Fast + Safe)
        pyperclip.copy(content)
        time.sleep(0.5) # Wait for clipboard
        self.control_v()
        time.sleep(1.0)

    def save_file(self, full_path):
        """
        Saves the file to the specific path.
        """
        self.control_s() 
        time.sleep(1.0)
        
        # Set clipboard path first
        pyperclip.copy(full_path)
        time.sleep(0.5)
        self.control_v()
        
        time.sleep(0.5)
        self.enter()
        
        # Wait for overwrite popup just in case (blind enter)
        time.sleep(1.0)
        self.enter() 
        
        time.sleep(1.0)

    def close_app(self):
        self.alt_f4()
        time.sleep(1.0)
        
        # Handle "Do you want to save changes?" popup
        # If we already saved, this might appear if we typed something after save or timing.
        # The default button is usually "Save". 
        # Since we want to just close, and we (theoretically) saved, we can just press Enter to "Save again" 
        # OR press Tab -> Enter to "Don't Save".
        # Let's be safe: If this popup appears, it means there are unsaved changes (or the app "thinks" so).
        # We'll just press Enter to confirm "Save" (if focused) to be safe, or just close.
        
        # ACTUALLY: The image shows "Save" button is focused by default (Blue outline).
        # So hitting Enter will just save it and close. This is harmless.
        # But if it's "Save As", it might get stuck.
        
        # Quick check: Press Enter.
        from pynput.keyboard import Key, Controller as KeyboardController
        keyboard = KeyboardController()
        
        # We blind press Enter just in case the dialog is there.
        # If dialog is NOT there, Enter usually does nothing on desktop.
        time.sleep(0.5)
        keyboard.press(Key.enter)
        keyboard.release(Key.enter)
        time.sleep(1.0)
