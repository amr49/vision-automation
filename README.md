Vision-Based Desktop Automation with Dynamic Icon Grounding
This project automates fetching blog posts and saving them to text files using Notepad. It features a robust Computer Vision system (powered by BotCity) to dynamically "Ground" (locate) the Notepad icon on the desktop regardless of its position or resolution.

Key Features
Dynamic Grounding: Uses Multi-Scale Template Matching to find the icon anywhere on the screen.

BotCity Framework: Leverages BotCity's enterprise-grade CV engine for stable detection.

Visual Debugging: Generates annotated screenshots (with bounding boxes) using OpenCV to prove detection.

Robust Workflow: Follows a strict "Close -> Ground -> Launch" loop to demonstrate detection reliability.

Prerequisites
Python 3.10+

Notepad Shortcut:

Create a shortcut named "Notepad" on your desktop.

Resources Setup (Crucial):

This project uses Image Matching. You must provide reference images for your specific screen resolution.

Go to the resources/ folder.

Take a screenshot of the Notepad icon on your desktop.

Save it as notepad.png (overwrite the existing one if needed).

Installation
Install dependencies using uv or pip:

PowerShell

uv pip install -r requirements.txt
# OR
pip install -r requirements.txt
Usage
Minimize all windows (the bot will also attempt to minimize).

Run the automation:

PowerShell

python main.py
How It Works
Grounding: The bot captures the screen and uses BotCity to scan for the notepad.png template (supporting multiple sizes).

Annotation: Once found, OpenCV calculates the coordinates and draws a red bounding box around the icon, saving the image as proof.

Interaction: The bot performs a double-click on the detected coordinates to launch the app.

Automation Loop: It fetches data from the API, types it, saves the file, and closes the app to force a fresh detection for the next item.

Troubleshooting
Icon not found?

The most common cause is screen resolution/scaling differences.

Fix: Take a fresh screenshot of your Notepad icon, crop it tightly, and save it as resources/notepad.png.

Bot doesn't click?

Ensure no other windows are covering the icon (the bot attempts to minimize, but manual cleanup helps).