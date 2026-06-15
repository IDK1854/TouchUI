# TouchUI: Secondary Display System Dashboard & Controller

TouchUI is a custom system dashboard and control deck designed specifically for secondary displays, such as a 7-inch 1024x600 monitor mounted inside or alongside a PC case. It integrates low-level Windows APIs with a responsive web interface to provide real-time system monitoring, application launch control, a per-application volume mixer, and global system media integration.

---

## Features

* **System Resource Monitoring**: Real-time tracking of CPU and RAM utilization.
* **Quick Launch and Window Fitting**: Launch applications like Discord, TradingView, Spotify, or YouTube (via Microsoft Edge in App mode) with a single tap. TouchUI automatically detects the newly created window, strips its borders (removes `WS_THICKFRAME`), and positions it to fill the secondary display.
* **Application-Specific Volume Mixer**: Fine-grained volume control panel to adjust the master system volume and individual active audio sessions independently (e.g., lowering game volume while maintaining communication volume) powered by Windows WASAPI.
* **System Media Controller**: Real-time media playback status display (track title, artist, playback state) and control (play/pause, skip, previous) using the Windows Runtime (WinRT) API. Includes a source switcher to cycle focus between different active media applications.
* **Home Button Overlay**: An always-on-top, borderless Tkinter-based overlay widget positioned at the bottom-right corner of the secondary screen. Activating it minimizes any open windows on that screen and returns focus back to the TouchUI web dashboard.

---

## Tech Stack

### Backend (/backend)
* **Python & FastAPI**: Lightweight web server hosting the control API.
* **Windows Win32 APIs (via ctypes)**: Handles window positioning, border stripping, foreground management, and cursor state restoration.
* **PyCaw (Python Common Audio Windows)**: Communicates with Windows WASAPI to adjust master volume and individual active application audio levels.
* **WinRT (Windows Runtime API)**: Queries the `GlobalSystemMediaTransportControlsSessionManager` to read metadata and direct playback controls for system media players.
* **Tkinter**: Powers the lightweight, borderless desktop overlay widget that acts as the always-on-top Home button.

### Frontend (/frontend)
* **React 19 & TypeScript**: Component-based application framework.
* **Vite**: Build tool and development server.
* **Vanilla CSS**: Custom styling optimized for 1024x600 aspect ratios.

---

## Repository Structure

```
TouchUI/
├── backend/
│   ├── main.py            # FastAPI backend & Windows controller API
│   ├── overlay.py         # Tkinter Home overlay button
│   └── get_monitors.py    # Monitor detection utility
├── frontend/
│   ├── src/
│   │   ├── App.tsx        # Dashboard component logic
│   │   ├── App.css        # Dashboard custom styling
│   │   └── icons.tsx      # SVG icons for the dashboard
│   ├── index.html
│   └── package.json
├── requirements.txt       # Python backend dependencies
└── README.md              # Project documentation
```

---

## Setup and Installation

### 1. Identify Your Secondary Display Coordinates
TouchUI requires the precise coordinates of your secondary screen on your Windows desktop grid.
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Run the monitor detection script:
   ```bash
   python get_monitors.py
   ```
3. Record the **X Offset (Left)**, **Y Offset (Top)**, and **Resolution** of your secondary display.

### 2. Configure Coordinates and Launch Paths
Open `backend/main.py` and update the target screen parameters:
```python
TARGET_X = 3840  # Replace with your secondary monitor's X Offset
TARGET_Y = 0     # Replace with your secondary monitor's Y Offset
TARGET_W = 1024  # Replace with your secondary monitor's Width
TARGET_H = 600   # Replace with your secondary monitor's Height
```
You can also adjust the application executable paths in the `apps` dictionary in `backend/main.py` to match your local installation paths.

### 3. Install Python Backend Dependencies
We recommend setting up a virtual environment:
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Install Frontend Dependencies
```bash
cd frontend
npm install
```

---

## Running the Application

For a fully integrated experience, run the backend, the overlay button, and the web application:

1. **Start the Backend Server**:
   ```bash
   cd backend
   python main.py
   ```
   The backend will run a FastAPI server at `http://127.0.0.1:8000`.

2. **Start the Tkinter Home Overlay**:
   ```bash
   cd backend
   python overlay.py
   ```
   This initializes the translucent home icon in the bottom right corner of your secondary display.

3. **Start the Frontend Dashboard**:
   ```bash
   cd frontend
   npm run dev
   ```
   Open your browser (e.g., Microsoft Edge in App mode) on your secondary screen to view the dashboard:
   ```bash
   msedge.exe --app=http://localhost:5173
   ```

---

## Customization

### Adding New Quick Launch Apps
1. **Backend**: Add your application entry to the `apps` dictionary in `backend/main.py`, specifying the launch command and how the window should be located (`find_by: "process" | "title"`).
2. **Frontend**: Add a button corresponding to the backend launch ID inside `App.tsx` and render the appropriate icon.
