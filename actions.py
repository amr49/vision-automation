from botcity.core import DesktopBot
import time
import logging
import subprocess
import pyperclip

class NotepadBot(DesktopBot):
    def __init__(self):
        super().__init__()
        # Register the image resources
        self.image_paths = {
            "notepad": r"resources\notepad.png",
            "notepad_small": r"resources\notepad_small_size.png",
            "notepad_big": r"resources\notepad_big_size.png"
        }
        for label, path in self.image_paths.items():
            self.add_image(label, path)
        
    def launch_app_via_icon(self, app_name="Notepad", template_path=None):
        """
        Finds the desktop icon and launches it using BotCity image matching with retry logic.
        Tries multiple size variations.
        """
        logging.info(f"Looking for {app_name} on desktop using BotCity...")
        
        # Minimize all windows to see desktop
        subprocess.run(["powershell", "-command", "(New-Object -ComObject Shell.Application).MinimizeAll()"], shell=True)
        time.sleep(1.0) 
        
        # BotCity Check with Retry Logic (3 attempts, 1s delay)
        icon_found = False
        found_label = None
        
        # List of labels to try
        labels_to_try = ["notepad", "notepad_small", "notepad_big"]
        
        for attempt in range(3):
            for label in labels_to_try:
                if self.find(label, matching=0.9, waiting_time=500): # Short wait per icon
                    icon_found = True
                    found_label = label
                    logging.info(f"Found icon matching label: {label}")
                    break
            
            if icon_found:
                break
                
            logging.warning(f"Attempt {attempt+1}: Icon not found. Retrying...")
            time.sleep(1.0)
            
        if not icon_found:
             logging.error(f"Could not find {app_name} icon via image matching after 3 attempts.")
             return False
        
        logging.info(f"Found {app_name} icon.")
        
        # --- DELIVERABLE REQUIREMENT: Annotated Screenshot ---
        try:
            # Since self.find() moves the mouse to the center of the found image, 
            # we can get the location from the mouse position.
            # We can get the size from the image file itself.
            import pyautogui
            import cv2
            import numpy as np
            from PIL import ImageGrab
            import os
            
            # Get current mouse position (Center of icon)
            mx, my = pyautogui.position()
            
            # Get Image Dimensions using the matched label
            image_path = self.image_paths.get(found_label, r"resources\notepad.png")
            
            if os.path.exists(image_path):
                template = cv2.imread(image_path)
                h, w = template.shape[:2]
                
                # Calculate Top-Left
                x = mx - w // 2
                y = my - h // 2
                
                # Capture full screen
                screen = ImageGrab.grab()
                img = cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2BGR)
                
                # Draw Rectangle (Red)
                cv2.rectangle(img, (int(x), int(y)), (int(x+w), int(y+h)), (0, 0, 255), 2)
                
                # Draw Text
                cv2.putText(img, f"Detected: {app_name} ({found_label})", (int(x), int(y)-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                
                # Save
                filename = f"detected_icon_{int(time.time())}.png"
                cv2.imwrite(filename, img)
                logging.info(f"Saved annotated screenshot: {filename}")
        except Exception as e:
            logging.warning(f"Failed to save annotated screenshot: {e}")
        
        # Simplify Launch Strategy
        # Click the CENTER of the detected element (Mouse is already there)
        self.click() # Click current position
        time.sleep(0.2)
        
        # Double Click to launch
        self.double_click()
        time.sleep(1.0)
        
        # Wait for window to ensure it opened
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
        # Ensure focus by waiting
        time.sleep(2.0)
        
        content = f"Title: {title}\n\n{body}"
        
        # Use Clipboard
        pyperclip.copy(content)
        time.sleep(1.0)
        self.control_v()
        time.sleep(1.0)

    def save_file(self, full_path):
        """
        Saves the file to the specific path and overwrites if exists.
        """
        self.control_s()
        time.sleep(1.5) # Wait for dialog

        # Paste full path
        pyperclip.copy(full_path)
        time.sleep(1.0)
        self.control_v()

        time.sleep(1.0)
        self.enter()  # Save

        # --- HANDLE OVERWRITE POPUP ---
        time.sleep(1.0)

        # Use BotCity built-in methods instead of pynput
        # Press 'y' to confirm overwrite
        self.type_keys('y')
        time.sleep(0.3)
        self.enter()
        
        time.sleep(1.0)

    def close_app(self):
        """
        Closes Notepad safely using taskkill to avoid accidental interactions with other windows (like Desktop Shutdown).
        """
        logging.info("Closing Notepad...")
        try:
            subprocess.run(["taskkill", "/IM", "notepad.exe", "/F"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(1.0)
        except Exception as e:
            logging.error(f"Error closing Notepad: {e}")

    
    