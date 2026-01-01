import os
import time
import logging
from actions import NotepadBot
from utils import fetch_posts, ensure_directory

# Configuration
DESKTOP_PATH = os.path.join(os.path.expanduser("~"), "Desktop")
OUTPUT_DIR = os.path.join(DESKTOP_PATH, "tjm-project")
NOTEPAD_ICON_LABEL = "Notepad" 

def main():
    logging.info("Starting Vision-Based Desktop Automation...")
    
    # 1. Setup Data & Directory
    posts = fetch_posts(limit=10)
    if not posts:
        logging.error("No posts fetched. Exiting.")
        return

    ensure_directory(OUTPUT_DIR)
    
    # 2. Initialize Bot
    bot = NotepadBot()
    
    # 3. Main Loop
    for post in posts:
        post_id = post['id']
        title = post['title']
        body = post['body']
        
        logging.info(f"Processing Post {post_id}...")
        
        max_retries = 3
        launched = False
        for attempt in range(max_retries):
            
            if bot.launch_app_via_icon(NOTEPAD_ICON_LABEL):
                launched = True
                break
            logging.warning(f"Launch attempt {attempt+1} failed. Retrying...")
            time.sleep(1.0)
            
        if not launched:
            logging.error(f"Failed to launch Notepad for post {post_id}. Skipping.")
            continue
            
        # B. Write Content
        bot.write_post(title, body)
        
        # C. Save
        filename = f"post_{post_id}.txt"
        full_path = os.path.join(OUTPUT_DIR, filename)
        bot.save_file(full_path)
        logging.info(f"Saved to {full_path}")
        bot.close_app()
        
        time.sleep(1.5)

    logging.info("Automation run complete. All files are minimized.")
    

if __name__ == "__main__":
    main()
