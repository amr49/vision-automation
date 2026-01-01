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
        # 1. Grayscale (Standard)
        # 2. Thresholding (High Contrast)
        # 3. Inverted (Dark text on light bg vs Light on Dark)
        # 4. Dilate (Beef up thin text)
        # 5. Raw Color (Let Tesseract decide)
        pipeline = [
            ("Standard Gray", lambda img: cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)),
            ("Thresholding", lambda img: cv2.threshold(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]),
            ("Inverted", lambda img: cv2.bitwise_not(cv2.threshold(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1])),
            ("Dilated", lambda img: cv2.dilate(cv2.threshold(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1], cv2.getStructuringElement(cv2.MORPH_RECT, (2,2)), iterations=1)),
            ("Raw Color", lambda img: img)
        ]
        
        # Use simpler config initially to avoid hang
        custom_config = r'--oem 3 --psm 3' # Default page segmentation (might work better for full desktop)
        # OR stick to 11 but with smaller image
        
        # NOTE: 2x Upscaling a 1080p Screenshot makes it 4K (huge for Tesseract on CPU), causing the freeze/timeout.
        # We will remove upscaling or limit it.
        
        # Tesseract Configurations to try
        # PSM 11: Sparse text (Best for icons scattered)
        # PSM 4: Single column (Good if icons are aligned)
        # PSM 3: Fully automatic (Fallback)
        configs = [
            r'--oem 3 --psm 11',
            r'--oem 3 --psm 4',
            r'--oem 3 --psm 3'
        ]
        
        for psm_config in configs:
            logging.info(f"Trying Tesseract Config: {psm_config}")
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

                    data = pytesseract.image_to_data(processed, config=psm_config, output_type=pytesseract.Output.DICT)
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
                    
                    # --- FILTER TRAPS ---
                    # Ignore the debug files themselves if they are visible on desktop
                    if "detected_icon" in text_lower or ".png" in text_lower:
                        continue
                    
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
                   
                            # Let's get logical width via a non-DPI aware method implied by standard frameworks?
                            # Or just calculate directly if we know image width.
                            
                            img_width = original_img.shape[1] # Physical
                            pass
                        except:
                            pass
                            
                        # Simplified Correction:
                        import ctypes
                        user32 = ctypes.windll.user32
                        # Get Physical
                        user32.SetProcessDPIAware()
                        phys_w = user32.GetSystemMetrics(0)
                        phys_h = user32.GetSystemMetrics(1)
                        
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
                             # Draw Debug & Save (For Deliverables)
                             try:
                                 debug_img = original_img.copy()
                                 # Draw Text Rect (Red)
                                 cv2.rectangle(debug_img, (x, y), (x+w, y+h), (0, 0, 255), 2)
                                 # Draw Click Point (Green Dot)
                                 cv2.circle(debug_img, (icon_center_x, icon_center_y), 5, (0, 255, 0), -1)
                                 cv2.putText(debug_img, f"Found: {text} ({conf}%)", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                                 
                                 filename = f"detected_icon_{text}_{conf}.png"
                                 cv2.imwrite(filename, debug_img)
                                 logging.info(f"Saved success screenshot: {filename}")
                             except Exception as e:
                                 logging.warning(f"Could not save debug image: {e}")

                             candidates.sort(key=lambda x: x[2], reverse=True)
                             return (candidates[0][0], candidates[0][1])

                if candidates:
                    # specific match with highest confidence
                    candidates.sort(key=lambda x: x[2], reverse=True)
                    
                    # Draw Debug for best candidate
                    try:
                         best = candidates[0]
                         cx, cy, c_conf = best
                         debug_img = original_img.copy()
                         cv2.circle(debug_img, (cx, cy), 10, (0, 255, 0), -1)
                         cv2.imwrite(f"detected_candidate_{c_conf}.png", debug_img)
                    except: pass
                    
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
