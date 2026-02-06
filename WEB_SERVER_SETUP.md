# Web Server for License Plate Detection

## Overview
This setup includes a Flask web server that receives license plate detections from the video recognition script and stores them in a SQLite database with images.

## Architecture
```
┌─────────────────────────────┐
│  video_plate_recognition.py │
│  (ESP32-CAM Stream)         │
│  - Detects plates           │
│  - Captures images          │
└──────────────┬──────────────┘
               │ HTTP POST
               │ (plate + image)
               ▼
┌─────────────────────────────┐
│        server.py            │
│   (Flask Web Server)        │
│  - Receives detections      │
│  - Stores in SQLite DB      │
│  - Web interface            │
└─────────────────────────────┘
               │
               ▼
┌─────────────────────────────┐
│        plates.db            │
│      (SQLite Database)      │
│  - plate_number             │
│  - detection_count          │
│  - image_data (base64)      │
│  - timestamp                │
└─────────────────────────────┘
```

## Setup Instructions

### 1. Install Required Packages
```bash
pip install Flask requests
```
Or install from requirements.txt:
```bash
pip install -r requirements.txt
```

### 2. Start the Web Server
Open a **new terminal** and run:
```bash
python server.py
```

You should see:
```
🚀 Starting License Plate Detection Server
📊 Database: D:\akka project\slnumplate\plates.db
🌐 Web Interface: http://localhost:5000
📡 API Endpoint: http://localhost:5000/api/detect
```

### 3. Run the Detection Script
In **another terminal**, run:
```bash
python video_plate_recognition.py
```

## Usage

### Web Interface
Open your browser and go to:
- **http://localhost:5000** - View all detections

Features:
- ✅ View all detected plates
- ✅ See detection statistics (count, timestamp)
- ✅ Click "View Image" to see the captured image
- ✅ Automatic refresh when new detections arrive

### API Endpoints

#### POST /api/detect
Send a new detection to the server.

**Request Body:**
```json
{
  "plate_number": "TN01AB1234",
  "detection_count": 15,
  "total_detections": 20,
  "image": "base64_encoded_image_data"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Detection stored successfully",
  "id": 123
}
```

#### GET /api/detections
Get all detections (without images).

**Response:**
```json
[
  {
    "id": 1,
    "plate_number": "TN01AB1234",
    "detection_count": 15,
    "total_detections": 20,
    "timestamp": "2026-02-06 10:30:45"
  }
]
```

## Configuration

### video_plate_recognition.py
Edit these settings at the top of the file:
```python
SERVER_URL = "http://localhost:5000/api/detect"  # Change if server is on different host
SEND_TO_SERVER = True  # Set to False to disable sending to server
```

### Server Port
To change the server port, edit `server.py`:
```python
app.run(host='0.0.0.0', port=5000, debug=True)  # Change port here
```

## Database Schema

**Table: detections**
| Column            | Type     | Description                      |
|-------------------|----------|----------------------------------|
| id                | INTEGER  | Primary key (auto-increment)     |
| plate_number      | TEXT     | Detected plate number            |
| detection_count   | INTEGER  | How many times detected          |
| total_detections  | INTEGER  | Total detections in time window  |
| confidence        | REAL     | Average confidence (future use)  |
| image_data        | TEXT     | Base64 encoded JPEG image        |
| timestamp         | DATETIME | When detection was recorded      |

## Troubleshooting

### Port Already in Use
If you see "Address already in use":
1. Kill the existing process on port 5000
2. Or change the port in `server.py`

### Connection Refused
Make sure:
1. Server is running (`python server.py`)
2. Server URL in `video_plate_recognition.py` matches
3. No firewall blocking port 5000

### Database Locked
If you see "database is locked":
1. Close any DB browser tools
2. Restart the server

## Advanced Usage

### Remote Server
To access from other devices:
1. Run server with `host='0.0.0.0'` (already set)
2. Find your IP: `ipconfig` (Windows) or `ifconfig` (Linux)
3. Update `SERVER_URL` in detection script: `http://YOUR_IP:5000/api/detect`
4. Access web interface: `http://YOUR_IP:5000`

### Custom Database Location
Change `DB_PATH` in `server.py`:
```python
DB_PATH = 'path/to/your/database.db'
```

## Files Created

- **server.py** - Flask web server
- **plates.db** - SQLite database (created automatically)
- **WEB_SERVER_SETUP.md** - This file

## Testing

Test the server without running detection:
```bash
curl -X POST http://localhost:5000/api/detect \
  -H "Content-Type: application/json" \
  -d '{"plate_number":"TEST1234","detection_count":5,"total_detections":10,"image":""}'
```

## Features

✅ Real-time detection storage  
✅ Image capture with each detection  
✅ Web-based viewing interface  
✅ SQLite database (no setup required)  
✅ RESTful API  
✅ Timestamp tracking  
✅ Detection statistics  

## Next Steps

Possible enhancements:
- Add authentication
- Export to CSV/Excel
- Search functionality
- Detection analytics/charts
- Email/SMS alerts for specific plates
- Integration with parking systems
