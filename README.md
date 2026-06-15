# 🖥️ TouchUI — 7" Secondary Display System Dashboard & Controller

TouchUI is a modern, custom-built hardware control deck and sensor dashboard designed specifically for secondary displays (like a 7-inch 1024x600 monitor inside or next to a PC case). It integrates low-level Windows APIs with a responsive web dashboard to provide system monitoring, application launch control, a per-app volume mixer, and system media integration.

---

## ✨ Features

* **📈 Live System Stats**: Real-time monitoring of CPU and RAM utilization.
* **🚀 Quick Launch & Window Auto-Fitting**: Launch apps like Discord, TradingView, Spotify, or YouTube (as an Edge PWA app) with one tap. TouchUI automatically detects the window, strips its title borders (`WS_THICKFRAME`), and positions/resizes it to perfectly fit the secondary screen.
* **🎛️ Per-App Volume Mixer**: A complete control panel to adjust master volume and individual application audio sessions (e.g., lower game volume while keeping Discord loud) powered by Windows WASAPI.
* **🎵 System Media Deck**: Real-time media playback display (track title, artist, play status) and controls (Play/Pause, Skip, Previous) using Windows WinRT media integration. Includes a custom **source switcher** to toggle controls between active media sources (e.g., Spotify vs. Edge/Chrome).
* **🏠 Floating 'Home' Overlay**: An always-on-top, borderless Tkinter-based overlay widget positioned at the bottom-right corner of the secondary screen. A single tap minimizes other windows on the screen and restores focus back to the TouchUI dashboard.

---

## 🛠️ Tech Stack

### Backend (`/backend`)
* **Python & FastAPI**: Lightweight web server hosting the control API.
* **Windows Win32 APIs (via `ctypes`)**: Low-level window manipulation (positioning, border stripping, bringing windows to foreground, thread input attachment) and cursor state restoration.
* **PyCaw (Python Common Audio Windows)**: Controls system master volume and active Windows Audio Session API (WASAPI) application levels.
* **WinRT (Windows Runtime API)**: Taps into the `GlobalSystemMediaTransportControlsSessionManager` to read metadata and direct playback controls for system media players.
* **Tkinter**: Powers the lightweight, borderless desktop overlay widget that acts as an always-on-top Home button.

### Frontend (`/frontend`)
* **React 19 & TypeScript**: Component-based application framework.
* **Vite**: Ultra-fast build tool and development server.
* **Vanilla CSS**: Premium dark-mode dashboard styling custom-tailored for 1024x600 aspect ratios.

---

## 📁 Repository Structure

```
TouchUI/
├── backend/
│   ├── main.py            # FastAPI backend & Windows controller API
│   ├── overlay.py         # Tkinter Home overlay button
│   └── get_monitors.py    # Monitor detection utility
├── frontend/
│   ├── src/
│   │   ├── App.tsx        # Dashboard component logic
│   │   ├── App.css        # Premium custom styling
│   │   └── icons.tsx      # SVG icons for the dashboard
│   ├── index.html
│   └── package.json
├── requirements.txt       # Python backend dependencies
└── README.md              # Project documentation
```

---

## 🚀 Setup & Installation

### 1. Identify Your Secondary Display Coordinates
TouchUI needs to know the exact coordinates of your secondary screen on your Windows desktop grid.
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Run the monitor detection script:
   ```bash
   python get_monitors.py
   ```
3. Take note of the **X Offset (Left)**, **Y Offset (Top)**, and **Resolution** of your 7-inch display.

### 2. Configure Coordinates & Quick Launch Paths
Open [backend/main.py](file:///c:/Users/HrakosCZ/Downloads/TouchUI/backend/main.py) and update the target screen parameters:
```python
TARGET_X = 3840  # Replace with your secondary monitor's X Offset
TARGET_Y = 0     # Replace with your secondary monitor's Y Offset
TARGET_W = 1024  # Replace with your secondary monitor's Width
TARGET_H = 600   # Replace with your secondary monitor's Height
```
You can also adjust the application executable paths in the `apps` dictionary in [backend/main.py](file:///c:/Users/HrakosCZ/Downloads/TouchUI/backend/main.py#L179-L204) to match where your apps are installed.

### 3. Install Python Backend Dependencies
We recommend using a virtual environment:
```bash
# From the root directory
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

## 🏃 Running the Application

For a fully integrated experience, you will run the backend, the overlay button, and the web app:

1. **Start the Backend Server**:
   ```bash
   # In venv
   cd backend
   python main.py
   ```
   The backend will run a FastAPI server at `http://127.0.0.1:8000`.

2. **Start the Tkinter Home Overlay**:
   ```bash
   # In venv
   cd backend
   python overlay.py
   ```
   This will create a small, translucent house icon in the bottom right corner of your secondary display.

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

## 🎨 Customization

### Adding New Quick Launch Apps
1. **Backend**: Add your application entry to the `apps` dictionary in [backend/main.py](file:///c:/Users/HrakosCZ/Downloads/TouchUI/backend/main.py#L179-L204) specifying the launch command and how the window should be located (`find_by: "process" | "title"`).
2. **Frontend**: Add a button corresponding to the backend launch ID inside `App.tsx` and render the appropriate icon.
