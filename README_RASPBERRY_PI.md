# License Plate Recognition on Raspberry Pi 5

## Optimizations for Raspberry Pi 5

This optimized version runs efficiently on Raspberry Pi 5 with the following improvements:

### Performance Optimizations:
1. **YOLOv5n (Nano)** - Smallest model (1.9MB vs 14MB for YOLOv5s)
2. **Lower Resolution** - 320x240 input instead of 640x480 (4x fewer pixels)
3. **Frame Skipping** - Processes every 5th frame
4. **FP16 Inference** - Half precision for 2x speed boost
5. **Hardware Acceleration** - OpenCV V4L2 backend
6. **Minimal OCR** - Single worker, smaller resize

### Expected Performance:
- **Processing Speed**: 2-5 FPS (on processed frames)
- **Detection Latency**: ~500-1500ms per detection
- **Memory Usage**: ~500-800MB RAM

## Setup Instructions

### 1. Install Dependencies on Raspberry Pi 5

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python dependencies
sudo apt install python3-pip python3-opencv python3-numpy -y

# Install PyTorch (ARM64 version)
pip3 install torch torchvision torchaudio

# Install other requirements
pip3 install ultralytics easyocr opencv-python-headless

# For better performance, install optimized numpy
pip3 install numpy --upgrade
```

### 2. ESP32-CAM Setup (Optional)

If using ESP32-CAM, flash it with the Camera Web Server example:
1. Open Arduino IDE
2. Install ESP32 board support
3. Load: File → Examples → ESP32 → Camera → CameraWebServer
4. Select your camera model (e.g., AI_THINKER)
5. Upload and note the IP address from Serial Monitor
6. Update `ESP32_CAM_URL` in the script

### 3. Configuration

Edit `video_plate_recognition_raspi.py`:

```python
# For ESP32-CAM
USE_ESP32_CAM = True
ESP32_CAM_URL = "http://192.168.1.100:81/stream"  # Your ESP32 IP

# For USB camera
USE_ESP32_CAM = False  # Uses /dev/video0

# Performance tuning
PROCESS_EVERY_N_FRAMES = 5  # Lower = more accurate, Higher = faster
INPUT_WIDTH = 320  # Lower = faster, Higher = better quality
OCR_ENABLED = True  # Set False to test detection only
```

### 4. Running the Script

```bash
# On Raspberry Pi
python3 video_plate_recognition_raspi.py

# Press 'q' to quit
```

## Performance Tuning

### For Faster Processing (lower accuracy):
```python
PROCESS_EVERY_N_FRAMES = 10  # Process every 10th frame
INPUT_WIDTH = 256
INPUT_HEIGHT = 192
YOLO_INPUT_SIZE = 256
OCR_ENABLED = False  # Disable OCR for testing
```

### For Better Accuracy (slower):
```python
PROCESS_EVERY_N_FRAMES = 3
INPUT_WIDTH = 416
INPUT_HEIGHT = 312
YOLO_INPUT_SIZE = 416
model.conf = 0.5  # Lower confidence threshold
```

## Raspberry Pi GPU Acceleration

Raspberry Pi 5 has VideoCore VII GPU, but PyTorch doesn't support it directly. However:

### Using ONNX Runtime for GPU (Advanced):

```bash
# Install ONNX runtime with OpenGL support
pip3 install onnxruntime

# Export YOLOv5 to ONNX format
python3 -c "
import torch
model = torch.hub.load('ultralytics/yolov5', 'yolov5n')
torch.onnx.export(model, torch.randn(1,3,320,320), 'yolov5n.onnx')
"
```

### Hardware Video Decoding:

Raspberry Pi 5 supports hardware H.264 decoding:
```bash
# For video files, use hardware decoding
ffmpeg -hwaccel h264_v4l2m2m -i input.mp4 -f rawvideo - | python3 script.py
```

## Troubleshooting

### Camera Not Detected:
```bash
# Check USB cameras
ls /dev/video*

# Test camera
raspistill -o test.jpg  # For Raspberry Pi camera
ffmpeg -f v4l2 -i /dev/video0 -frames 1 test.jpg  # For USB camera
```

### Memory Issues:
```bash
# Increase swap space
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# Set CONF_SWAPSIZE=2048
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

### Slow Performance:
1. Disable OCR: `OCR_ENABLED = False`
2. Increase frame skip: `PROCESS_EVERY_N_FRAMES = 10`
3. Lower resolution: `INPUT_WIDTH = 256`
4. Use headless OpenCV: `pip install opencv-python-headless`

## Comparison: Desktop vs Raspberry Pi 5

| Feature | Desktop (Windows) | Raspberry Pi 5 |
|---------|------------------|----------------|
| Model | YOLOv5s (14MB) | YOLOv5n (1.9MB) |
| Resolution | 640x480 | 320x240 |
| Frame Skip | Every 3rd | Every 5th |
| FPS | 5-10 FPS | 2-5 FPS |
| Memory | 1-2GB | 500-800MB |

## ESP32-CAM Stream Format

ESP32-CAM typically provides:
- Resolution: 640x480 (VGA) or 1600x1200 (UXGA)
- Format: MJPEG stream
- Framerate: 10-15 FPS
- URL: `http://<IP>:81/stream`

Recommended settings:
- Resolution: VGA (640x480)
- Quality: 10-12
- Brightness: 0
- Contrast: 0
