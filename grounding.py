import cv2
import pytesseract
from PIL import ImageGrab
import numpy as np
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class GroundingEngine:
    def __init__(self, tesseract_cmd=None):
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        else:
            # Attempt to find tesseract in common Windows locations if not in PATH
            common_paths = [
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
                os.path.expanduser(r"~\AppData\Local\Tesseract-OCR\tesseract.exe")
            ]
            for path in common_paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    logging.info(f"Found Tesseract at: {path}")
                    break
        
    def capture_screen(self):
        """Captures the full screen and returns it as a numpy array (BGR)."""
        screen = ImageGrab.grab()
        return cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2BGR)

    def find_icon_by_text(self, label="Notepad", confidence_threshold=40):
        """
        Locates the icon by finding the text label below it using OCR.
        Tries multiple preprocessing techniques to maximize detection rate.
        """
        logging.info(f"Attempting to find icon with label '{label}' via OCR...")
        original_img = self.capture_screen()
        
        # Define preprocessing pipeline
        # Optimized for speed and stability:
        # 1. Grayscale (No upscale, just high contrast config)
        pipeline = [
            ("Standard Gray", lambda img: cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)),
            ("Thresholding", lambda img: cv2.threshold(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1])
        ]
        
        # Use simpler config initially to avoid hang
        custom_config = r'--oem 3 --psm 3' # Default page segmentation (might work better for full desktop)
        # OR stick to 11 but with smaller image
        
        # NOTE: 2x Upscaling a 1080p Screenshot makes it 4K (huge for Tesseract on CPU), causing the freeze/timeout.
        # We will remove upscaling or limit it.
        
        custom_config = r'--oem 3 --psm 11' # Sparse text search
        
        for name, process_func in pipeline:
            logging.info(f"Trying OCR Strategy: {name}")
            try:
                processed = process_func(original_img)
                # Ensure we don't pass a massive image if user has high DPI
                h, w = processed.shape[:2]
                if w > 2500: # If > 2K width, resize DOWN or keep original
                    scale = 0.8
                    processed = cv2.resize(processed, None, fx=scale, fy=scale)
                else:
                    scale = 1.0

                data = pytesseract.image_to_data(processed, config=custom_config, output_type=pytesseract.Output.DICT)
            except Exception as e:
                logging.warning(f"Strategy {name} failed: {e}")
                continue

            n_boxes = len(data['text'])
            candidates = []
            
            for i in range(n_boxes):
                text = data['text'][i].strip()
                if not text:
                    continue
                
                conf = int(data['conf'][i])
                
                # Extremely loose matching
                text_lower = text.lower().strip()
                label_lower = label.lower().strip()
                
                # Check 1: Exact substring match
                match = label_lower in text_lower
                
                # Check 2: Fuzzy match for common OCR errors (e.g. "Notepqd", "Notepad.")
                # Simple heuristic: if 4+ characters match sequentially
                if not match and len(label_lower) > 3:
                    if label_lower[:4] in text_lower: # "Note"
                        match = True
                
                if match:
                    # Ignore confidence if the text is clearly there
                    effective_conf = conf if conf > -1 else 0
                    
                    logging.info(f"Potential match: '{text}' (conf: {conf})")
                    
                    (x, y, w, h) = (data['left'][i], data['top'][i], data['width'][i], data['height'][i])
                    
                    # Scale back coordinates
                    x, y, w, h = int(x / scale), int(y / scale), int(w / scale), int(h / scale)
                    
                    text_center_x = x + w // 2
                    text_center_y = y + h // 2
                    
                    # Heuristic: Icon center is ~40-50px above text center (Physical Pixels)
                    icon_center_x_physical = text_center_x
                    icon_center_y_physical = text_center_y - 50
                    
                    # DPI SCALING CORRECTION
                    # Detect screen scaling to convert Physical Pixels (Image) -> Logical Pixels (Mouse)
                    try:
                        from ctypes import windll
                        user32 = windll.user32
                        user32.SetProcessDPIAware()
                        w_physical = user32.GetSystemMetrics(0)
                        
                        # Logical width (BotCity/Mouse default context)
                        # We can get this by standard tkinter or verifying ratio
                        # Simple hack: Image width (Physical) / Screen Width (Logical?)
                        # Actually ImageGrab returns physical.
                        # Pynput moves in logical.
                        
                        # Let's get logical width via a non-DPI aware method implied by standard frameworks?
                        # Or just calculate directly if we know image width.
                        
                        img_width = original_img.shape[1] # Physical
                        
                        # To clean this up:
                        # We just apply a divisor if we suspect scaling.
                        # But simpler: Let's assume the ratio matches image_width / system_metrics_width
                        pass
                    except:
                        pass
                        
                    # Simplified Correction:
                    # If users have 125% scaling, we need to divide by 1.25
                    # We can infer this often by checking standard bounds.
                    # But without complex logic, let's look at the failure description.
                    # "Standing in an empty place" usually means overshoot.
                    
                    # Let's assume 125% scaling (1.25) which is very common on laptops.
                    # better approach: Check the image resolution vs standard 1920x1080.
                    # The user said target is 1920x1080 resolution.
                    # If image is 1920x1080, and user has 100%, match is 1:1.
                    # If image is 1920x1080, and user has 125%, Logical is 1536x864.
                    
                    # We will implement dynamic scaling based on ctypes (reliable).
                    
                    import ctypes
                    user32 = ctypes.windll.user32
                    # Get Physical
                    user32.SetProcessDPIAware()
                    phys_w = user32.GetSystemMetrics(0)
                    phys_h = user32.GetSystemMetrics(1)
                    
                    # Get Logical (by temporarily resetting or using alternative API? No, easier way:)
                    # Using a non-DPI aware call or standard lib which is usually unaware
                    # Actually, we can compare `phys_w` to `original_img.shape[1]` (which is captured physically).
                    # Wait, ImageGrab is physical.
                    
                    # We need the LOGICAL width Pynput uses.
                    # Simply:
                    # scale_factor = phys_w / logical_w
                    # x_logical = x_physical / scale_factor
                    
                    # Get logical metrics
                    # Creating a separate non-aware context is hard in one script.
                    # Let's just hardcode a common fix or try to read it.
                    
                    # Heuristic: If we are clicking "empty space", we are likely overshooting.
                    # Let's try to normalize by 1.25 blindly? No, risky.
                    
                    # Alternate: Use `pyautogui.size()` which returns logical size.
                    try:
                       import pyautogui
                       log_w, log_h = pyautogui.size()
                       scale_x = original_img.shape[1] / log_w
                       scale_y = original_img.shape[0] / log_h
                    except ImportError:
                       scale_x = 1.0
                       scale_y = 1.0
                       
                    icon_center_x = int(icon_center_x_physical / scale_x)
                    icon_center_y = int(icon_center_y_physical / scale_y)
                    
                    candidates.append((icon_center_x, icon_center_y, conf))
                    
                    # If we find "Notepad" exactly, stop searching strategies as we found it.
                    if text_lower == "notepad":
                         candidates.sort(key=lambda x: x[2], reverse=True)
                         return (candidates[0][0], candidates[0][1])

            if candidates:
                # specific match with highest confidence
                candidates.sort(key=lambda x: x[2], reverse=True)
                return (candidates[0][0], candidates[0][1])
        
        # If we failed all strategies
        logging.warning(f"Label '{label}' not found after trying all OCR strategies.")
        
        # Save debug image of the last attempt (Thresholding usually shows structure best)
        debug_path = "debug_ocr_view.png"
        cv2.imwrite(debug_path, pipeline[1][1](original_img))
        logging.info(f"Saved debug view to {debug_path}")
        
        return None

    def find_icon_by_image(self, template_path, threshold=0.8):
        """
        Locates the icon using template matching.
        """
        if not os.path.exists(template_path):
            logging.warning(f"Template file not found: {template_path}")
            return None
            
        logging.info(f"Attempting to find icon via Template Matching using {template_path}...")
        img_rgb = self.capture_screen()
        img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)
        template = cv2.imread(template_path, 0)
        w, h = template.shape[::-1]

        res = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

        if max_val >= threshold:
            center_x = max_loc[0] + w // 2
            center_y = max_loc[1] + h // 2
            logging.info(f"Found template match with confidence {max_val:.2f} at ({center_x}, {center_y})")
            return (center_x, center_y)
        
        logging.warning(f"Template not found. Max confidence: {max_val:.2f}")
        return None

    def ground_icon(self, label="Notepad", template_path=None):
        """
        Wrapper to try multiple strategies.
        """
        # Strategy 1: OCR (Dynamic)
        coords = self.find_icon_by_text(label)
        if coords:
            return coords
            
        # Strategy 2: Template (Visual Fallback)
        if template_path:
            coords = self.find_icon_by_image(template_path)
            if coords:
                return coords
                
        return None
