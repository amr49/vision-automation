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
         # ImageGrab returns RGB, we convert to BGR for OpenCV
        return cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2BGR)

    def find_icon_by_text(self, label="Notepad", confidence_threshold=40):
        """
        Locates the icon by finding the text label below it using OCR.
        """
        logging.info(f"Attempting to find icon with label '{label}' via OCR...")
        original_img = self.capture_screen()
        
        # Define preprocessing pipeline
        # Optimized for speed and stability (Standard 1080p-4k range)
        pipeline = [
            ("Standard Gray", lambda img: cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)),
            ("Thresholding", lambda img: cv2.threshold(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1])
        ]
        
        # Config: Sparse text search, reliable for desktop labels
        custom_config = r'--oem 3 --psm 11'
        
        for name, process_func in pipeline:
            logging.info(f"Trying OCR Strategy: {name}")
            try:
                processed = process_func(original_img)
                # Cap max width to prevent Tesseract freeze on huge screenshots
                h, w = processed.shape[:2]
                if w > 3000: 
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
                
                # Fuzzy Matching Logic
                text_lower = text.lower().strip()
                label_lower = label.lower().strip()
                
                match = label_lower in text_lower
                # Heuristic: "Notepa" or similar
                if not match and len(label_lower) > 3:
                     if label_lower[:4] in text_lower:
                        match = True

                if match:
                    logging.info(f"Potential match: '{text}' (conf: {conf})")
                    
                    (x, y, w, h) = (data['left'][i], data['top'][i], data['width'][i], data['height'][i])
                    
                    # Scale back coordinates if we resized image
                    x, y, w, h = int(x / scale), int(y / scale), int(w / scale), int(h / scale)
                    
                    text_center_x = x + w // 2
                    text_center_y = y + h // 2
                    
                    # --- CRITICAL COORDINATE LOGIC (GOLDEN VERIFIED) ---
                    # 1. Base Heuristic: Icon body is above the text.
                    # Physical pixels (from Screenshot)
                    icon_center_x_physical = text_center_x
                    icon_center_y_physical = text_center_y - 45 
                    
                    # 2. DPI Scaling Correction
                    # Compares Physical resolution (Image) vs Logical resolution (Mouse)
                    try:
                       import pyautogui
                       log_w, log_h = pyautogui.size()
                       scale_x = original_img.shape[1] / log_w
                       scale_y = original_img.shape[0] / log_h
                    except Exception:
                       scale_x = 1.0
                       scale_y = 1.0
                       
                    icon_center_x = int(icon_center_x_physical / scale_x)
                    icon_center_y = int(icon_center_y_physical / scale_y)
                    
                    candidates.append((icon_center_x, icon_center_y, conf))

                    # Exact match priority
                    if text_lower == "notepad":
                         return (icon_center_x, icon_center_y)

            if candidates:
                candidates.sort(key=lambda x: x[2], reverse=True)
                return (candidates[0][0], candidates[0][1])
        
        # Debug output if failed
        logging.warning(f"Label '{label}' not found.")
        debug_path = "debug_ocr_view.png"
        cv2.imwrite(debug_path, pipeline[1][1](original_img))
        logging.info(f"Saved debug view to {debug_path}")
        return None

    def find_icon_by_image(self, template_path, threshold=0.8):
        """Locates the icon using template matching."""
        if not os.path.exists(template_path):
            return None
        logging.info(f"Template matching: {template_path}")
        img_rgb = self.capture_screen()
        img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)
        template = cv2.imread(template_path, 0)
        w, h = template.shape[::-1]
        res = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        if max_val >= threshold:
            center_x = max_loc[0] + w // 2
            center_y = max_loc[1] + h // 2
            # Apply same DPI scaling if needed (usually template match is 1:1 with screen, but coordinates need scaling)
            try:
               import pyautogui
               log_w, log_h = pyautogui.size()
               scale_x = img_rgb.shape[1] / log_w
               scale_y = img_rgb.shape[0] / log_h
               center_x = int(center_x / scale_x)
               center_y = int(center_y / scale_y)
            except:
               pass
            return (center_x, center_y)
        return None

    def ground_icon(self, label="Notepad", template_path=None):
        coords = self.find_icon_by_text(label)
        if coords: return coords
        if template_path: return self.find_icon_by_image(template_path)
        return None
