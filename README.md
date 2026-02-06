# Number Plate Detection System

License Plate Recognition System using YOLOv5 and EasyOCR, optimized for Raspberry Pi with ESP32-CAM integration.

## Features

- Real-time license plate detection using custom YOLOv5 model
- OCR text recognition with EasyOCR
- ESP32-CAM wireless streaming support
- Raspberry Pi optimized performance (FP16, reduced input size, frame skipping)
- Automatic reconnection for stable streaming
- Multi-frame buffering for accurate plate reading

## Hardware Requirements

- Raspberry Pi (Pi 4 or Pi 5 recommended)
- ESP32-CAM module (optional, can use USB camera)
- Power supply for both devices

## Software Requirements

```bash
pip install -r requirements.txt
```

## Usage

### For Raspberry Pi (Optimized):
```bash
python video_plate_recognition_raspi.py
```

### For Desktop/Laptop:
```bash
python video_plate_recognition.py
```

## ESP32-CAM Setup

See [ESP32_CAM_SETUP.md](ESP32_CAM_SETUP.md) for detailed setup instructions.

## Configuration

Edit the configuration variables in the Python files:
- `ESP32_CAM_URL`: Your ESP32-CAM stream URL
- `PROCESS_EVERY_N_FRAMES`: Frame skipping for performance
- `YOLO_INPUT_SIZE`: Model input size (416 for Raspberry Pi, 640 for desktop)
- `OCR_ENABLED`: Enable/disable OCR processing

## Performance Optimizations

The Raspberry Pi version includes:
- Reduced YOLO input size (416 vs 640) - 30-40% speedup
- Frame skipping (processes every 4th frame)
- Optimized OCR preprocessing (2x upscaling vs 3x)
- FP16 model inference when available
- Reduced display update frequency

## License

This project uses:
- YOLOv5 by Ultralytics
- EasyOCR
- OpenCV

## Author

Keerthi FJ
