# Vision-Based Desktop Automation

This project automates fetching blog posts and saving them to text files using Notepad, with a robust computer-vision-based "Grounding" system to find the Notepad icon on the desktop.

## Prerequisites

1.  **Python 3.10+** (Managed via `uv` preferably)
2.  **Tesseract-OCR**:
    *   Download and install from: https://github.com/UB-Mannheim/tesseract/wiki
    *   Ensure `tesseract.exe` is in your system PATH or at `C:\Program Files\Tesseract-OCR\tesseract.exe`.
3.  **Notepad Shortcut**:
    *   Create a shortcut named **"Notepad"** on your desktop.
    *   (Right-click Desktop > New > Shortcut > type `notepad` > Next > name it `Notepad`).

## Installation

1.  Initialize the project:
    ```powershell
    uv sync
    ```

## Usage

1.  Close any open Notepad windows.
2.  Run the automation:
    ```powershell
    uv run main.py
    ```

## How It Works

1.  **Grounding**: The script takes a screenshot and uses OCR (Tesseract) to find the text "Notepad" on the desktop.
2.  **Interaction**: It calculates the icon center (above the text) and uses BotCity to double-click.
3.  **Automation**: Fetches posts from an API, types them into Notepad, and saves them to `Desktop/tjm-project`.

## Troubleshooting

*   **Icon not found?** Ensure the shortcut is named exactly "Notepad". If using a different name, update `NOTEPAD_ICON_LABEL` in `main.py`.
*   **Tesseract error?** Install Tesseract and restart your terminal.
