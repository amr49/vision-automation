import cv2
import time
import logging
import os
from grounding import GroundingEngine

def verify():
    print("Beginning Grounding Verification in 5 seconds...")
    print("Please ensure 'Notepad' icon is visible on desktop.")
    time.sleep(5)
    
    engine = GroundingEngine()
    
    # Capture and Detect
    img = engine.capture_screen()
    coords = engine.find_icon_by_text("Notepad")
    
    if coords:
        x, y = coords
        print(f"SUCCESS: Found Notepad at ({x}, {y})")
        
        # Draw marker
        # Draw a red circle
        cv2.circle(img, (x, y), 20, (0, 0, 255), 2)
        # Draw crosshair
        cv2.line(img, (x-10, y), (x+10, y), (0, 0, 255), 2)
        cv2.line(img, (x, y-10), (x, y+10), (0, 0, 255), 2)
        
        output_file = "grounding_debug.png"
        cv2.imwrite(output_file, img)
        print(f"Saved annotated screenshot to {os.path.abspath(output_file)}")
    else:
        print("FAILURE: Could not find 'Notepad' text via OCR.")
        # Save raw screenshot for debugging
        cv2.imwrite("grounding_failed.png", img)
        print("Saved raw screenshot to grounding_failed.png")

if __name__ == "__main__":
    verify()
