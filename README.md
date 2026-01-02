# Vision-Based Desktop Automation with Dynamic Icon Grounding

This project demonstrates a robust desktop automation pipeline that fetches blog posts from an API and saves them to local text files using Notepad.

Unlike standard coordinate-based automation, this solution features a **Computer Vision system (powered by BotCity)** to dynamically "Ground" (locate) the Notepad icon on the desktop, regardless of its position or screen resolution.

## 🚀 Key Features

* **Dynamic Grounding:** Utilizes **Multi-Scale Template Matching** to locate the application icon anywhere on the screen.
* **BotCity Framework:** Leverages BotCity's enterprise-grade CV engine for high-reliability detection.
* **Visual Debugging:** Automatically generates annotated screenshots (with bounding boxes) using **OpenCV** to provide visual proof of detection logic.
* **Robust Workflow:** Follows a strict `Close -> Ground -> Launch` loop to demonstrate reliability across multiple iterations.

## 🛠 Prerequisites

* **Python 3.10+**
* **Notepad Shortcut:** Please create a shortcut named `Notepad` on your desktop for the bot to interact with.

## ⚙️ Setup & Installation

1.  **Install dependencies:**
    You can use `uv` or standard `pip`:

    ```powershell
    # Using uv (Recommended)
    uv pip install -r requirements.txt
    
    # OR using standard pip
    pip install -r requirements.txt
    ```

2.  **Resource Configuration (CRUCIAL):**
    Since this project relies on **Computer Vision (Image Matching)**, it requires a reference image that matches your specific screen resolution and scaling.
    
    * Navigate to the `resources/` folder.
    * Take a screenshot of the **Notepad icon** on your own desktop.
    * Crop it tightly and save it as `notepad.png` (overwrite the existing file if necessary).

##  ▶️ Usage

1.  **Minimize all windows** (The bot is designed to attempt this, but starting clean is recommended).
2.  **Run the automation:**

    ```powershell
    uv run main.py
    ```

## How It Works

1.  **Grounding:** The bot captures the screen and utilizes BotCity to scan for the `notepad.png` template (supporting multiple scales for better accuracy).
2.  **Annotation:** Once identified, OpenCV calculates the coordinates, draws a **red bounding box** around the icon, and saves the image as proof of detection.
3.  **Interaction:** The bot performs a double-click on the dynamic coordinates to launch the application.
4.  **Automation Loop:** It fetches data from the API, simulates keystrokes to type the content, saves the file, and terminates the app to force a fresh detection cycle for the next item.

## ❓ Troubleshooting

**Icon not found?**
* The most common cause is **Screen Resolution/Scaling** differences between machines.
* **Fix:** Take a fresh screenshot of your Notepad icon, crop it tightly, and save it as `resources/notepad.png`.

**Bot doesn't click?**
* Ensure no other windows are covering the icon (the bot attempts to minimize windows, but manual cleanup ensures the best results).

