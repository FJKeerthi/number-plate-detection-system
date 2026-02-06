"""
License Plate Recognition - Raspberry Pi Optimized Version
Optimized for Raspberry Pi with ESP32-CAM
"""

import torch
import easyocr
import numpy as np
import cv2
import warnings
import os
import platform

# Suppress warnings
warnings.filterwarnings('ignore', category=FutureWarning)

# Suppress Qt warnings but allow display to work
os.environ['QT_LOGGING_RULES'] = '*.debug=false;qt.qpa.*=false'
os.environ['OPENCV_VIDEOIO_DEBUG'] = '0'

# ============================================================
# RASPBERRY PI CONFIGURATION
# ============================================================

IS_RASPBERRY_PI = platform.machine().startswith('aarch64') or platform.machine().startswith('armv')

print("="*60)
print("RASPBERRY PI OPTIMIZED LICENSE PLATE RECOGNITION")
print("="*60)
print(f"Platform: {platform.machine()}")
print(f"Running on Raspberry Pi: {IS_RASPBERRY_PI}")

if IS_RASPBERRY_PI:
    os.environ['OPENCV_VIDEOIO_PRIORITY_V4L2'] = '1'
    print("OpenCV V4L2 backend enabled")

# ESP32-CAM Configuration
ESP32_CAM_URL = "http://192.168.8.104:81/stream"
USE_ESP32_CAM = True

# Processing Configuration
PROCESS_EVERY_N_FRAMES = 2  # Process more frequently for immediate detection
YOLO_INPUT_SIZE = 416  # Reduced from 640 for faster inference (30-40% speedup)
OCR_ENABLED = True
SAVE_OUTPUT = False
DISPLAY_EVERY_N_FRAMES = 1  # Update display every frame for immediate feedback

# ============================================================
# MODEL LOADING
# ============================================================

print("\nLoading custom trained YOLOv5 model...")
model = torch.hub.load('ultralytics/yolov5', 'custom', path='best.pt', force_reload=True)
model.conf = 0.35
model.iou = 0.45
model.max_det = 3
model.eval()

if IS_RASPBERRY_PI:
    try:
        model.half()
        print("Model converted to FP16 (half precision)")
    except:
        print("FP16 not available, using FP32")

print("Custom YOLOv5 model loaded successfully!")

# Initialize EasyOCR
if OCR_ENABLED:
    print("Initializing EasyOCR (CPU mode for Raspberry Pi)...")
    reader = easyocr.Reader(['en'], gpu=False, model_storage_directory='./easyocr_models')
    print("EasyOCR initialized!")
else:
    print("OCR disabled for performance testing")
    reader = None

# ============================================================
# VIDEO SOURCE SETUP
# ============================================================

print("\n" + "="*60)
if USE_ESP32_CAM:
    print(f"Connecting to ESP32-CAM at: {ESP32_CAM_URL}")
    video_source = ESP32_CAM_URL
else:
    print("Using USB camera (device 0)")
    video_source = 0

# Open video stream with optimized settings for ESP32-CAM
print("Attempting to connect (this may take a few seconds)...")

if USE_ESP32_CAM:
    # Try simple connection first (works best with ESP32-CAM MJPEG streams)
    cap = cv2.VideoCapture(ESP32_CAM_URL)
    
    # Give it time to connect
    import time
    time.sleep(2)
    
    # Set minimal buffer to reduce lag
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
else:
    cap = cv2.VideoCapture(video_source)

if not cap.isOpened():
    print("\nERROR: Could not open video source")
    print("\nTroubleshooting steps:")
    print("1. Check if ESP32-CAM is powered on")
    print("2. Verify the IP address is correct (current: 192.168.8.104)")
    print("3. Test the stream in a browser: http://192.168.8.104:81/stream")
    print("4. Make sure you're on the same network as the ESP32-CAM")
    print("5. Try restarting the ESP32-CAM")
    exit()

print("Connected successfully!")

fps = int(cap.get(cv2.CAP_PROP_FPS)) or 15
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
print(f"Video: {frame_width}x{frame_height} @ {fps} FPS")
print(f"Using native ESP32-CAM resolution (no resizing)")
print(f"Processing every {PROCESS_EVERY_N_FRAMES} frames")
print("="*60 + "\n")

if SAVE_OUTPUT:
    output_video_path = "output_raspi.avi"
    fourcc = cv2.VideoWriter_fourcc(*'MJPG')
    out = cv2.VideoWriter(output_video_path, fourcc, fps // PROCESS_EVERY_N_FRAMES, 
                         (frame_width, frame_height))
    print(f"Saving output to: {output_video_path}")

# Performance tracking
frame_count = 0
detection_count = 0
last_detected_plate = ""
last_detection_time = 0
min_detection_interval = 0.5  # Minimum 0.5 seconds between duplicate outputs

print("Press Ctrl+C to quit")
print("Starting processing...\n")

# ============================================================
# MAIN PROCESSING LOOP
# ============================================================

try:
    consecutive_failures = 0
    max_failures_before_reconnect = 10
    last_status_time = 0
    
    while True:
        # Read frame directly (removed double grab for performance)
        ret, frame = cap.read()
        
        if not ret:
            consecutive_failures += 1
            
            # Print status every second during failures
            import time
            current_time = time.time()
            if current_time - last_status_time > 1.0:
                print(f"Failed to read frame (attempt {consecutive_failures}/{max_failures_before_reconnect})")
                last_status_time = current_time
            
            if consecutive_failures >= max_failures_before_reconnect:
                print("\nStream connection lost. Attempting to reconnect...")
                
                # Release old connection
                cap.release()
                
                # Wait before reconnecting
                print("Waiting 3 seconds before reconnection...")
                time.sleep(3)
                
                # Attempt reconnection
                print(f"Reconnecting to {ESP32_CAM_URL}...")
                cap = cv2.VideoCapture(ESP32_CAM_URL)
                time.sleep(2)
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                
                if cap.isOpened():
                    print("✓ Reconnected successfully! Resuming processing...\n")
                    consecutive_failures = 0
                else:
                    print("✗ Reconnection failed. Retrying...\n")
                    consecutive_failures = 0  # Reset to keep trying
                
                continue
            
            # Wait a bit before retrying
            time.sleep(0.05)
            continue
        
        # Reset failure counter on successful read
        consecutive_failures = 0
        frame_count += 1
        
        # Print progress every 100 frames
        if frame_count % 100 == 0:
            print(f"Stream active: {frame_count} frames captured")
        
        # Skip frames for speed
        if frame_count % PROCESS_EVERY_N_FRAMES != 0:
            if SAVE_OUTPUT:
                out.write(frame)
            # Update display every frame for immediate feedback
            cv2.imshow('Plate Detection - Raspberry Pi', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            continue
        
        # Convert to RGB for YOLOv5
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Run YOLOv5 detection
        with torch.no_grad():
            results = model(frame_rgb, size=YOLO_INPUT_SIZE)
        
        # Get detection results
        detections = results.xyxyn[0]
        height, width = frame.shape[:2]
        
        # Process detections
        for det in detections:
            confidence = det[4].item()
            
            if confidence >= 0.35:
                detection_count += 1
                
                # Get bounding box
                x1 = int(det[0].item() * width)
                y1 = int(det[1].item() * height)
                x2 = int(det[2].item() * width)
                y2 = int(det[3].item() * height)
                
                # Minimal padding
                pad = 2
                x1 = max(0, x1 - pad)
                y1 = max(0, y1 - pad)
                x2 = min(width, x2 + pad)
                y2 = min(height, y2 + pad)
                
                # Crop plate region
                plate_crop = frame[y1:y2, x1:x2]
                
                if plate_crop.size > 0:
                    # Draw bounding box
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    
                    # OCR processing (optimized)
                    if OCR_ENABLED and reader is not None:
                        h, w = plate_crop.shape[:2]
                        # Reduced upscaling from 3x to 2x for speed
                        plate_resized = cv2.resize(plate_crop, (w * 2, h * 2), 
                                                   interpolation=cv2.INTER_LINEAR)  # INTER_LINEAR faster than CUBIC
                        
                        # Simplified preprocessing
                        plate_resized = cv2.cvtColor(plate_resized, cv2.COLOR_BGR2GRAY)
                        
                        try:
                            ocr_result = reader.readtext(
                                plate_resized,
                                allowlist='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ-',
                                paragraph=False,
                                batch_size=1,
                                min_size=10,  # Skip very small detections for speed
                                text_threshold=0.6  # Higher threshold for faster processing
                            )
                            
                            if ocr_result:
                                # Sort by x position
                                ocr_sorted = sorted(ocr_result, key=lambda x: x[0][0][0])
                                
                                # Separate into small letters, large letters, and numbers
                                small_letters = []
                                large_letters = []
                                numbers = []
                                
                                # Calculate average height for letter detections only
                                letter_heights = []
                                for detection in ocr_sorted:
                                    bbox, text, conf = detection
                                    text = text.strip().upper()
                                    if text.isalpha() and conf >= 0.5:
                                        bbox_height = abs(bbox[2][1] - bbox[0][1])
                                        letter_heights.append(bbox_height)
                                
                                if letter_heights:
                                    avg_letter_height = sum(letter_heights) / len(letter_heights)
                                    
                                    # Categorize each text piece
                                    for detection in ocr_sorted:
                                        bbox, text, conf = detection
                                        text = text.strip().upper()
                                        bbox_height = abs(bbox[2][1] - bbox[0][1])
                                        
                                        if conf >= 0.5:
                                            # Separate based on content type
                                            if text.isalpha():
                                                if bbox_height < avg_letter_height * 0.95:
                                                    small_letters.append(text)
                                                else:
                                                    large_letters.append(text)
                                            elif text.isdigit():
                                                numbers.append(text)
                                            else:
                                                # Mixed - separate letters and numbers
                                                for c in text:
                                                    if c.isalpha():
                                                        large_letters.append(c)
                                                    elif c.isdigit():
                                                        numbers.append(c)
                                else:
                                    # No letters detected, just get numbers
                                    for detection in ocr_sorted:
                                        bbox, text, conf = detection
                                        text = text.strip().upper()
                                        if conf >= 0.5:
                                            for c in text:
                                                if c.isdigit():
                                                    numbers.append(c)
                                
                                # Format: SMALL_LETTERS + LARGE_LETTERS + NUMBERS
                                small_text = ''.join(small_letters)
                                large_text = ''.join(large_letters)
                                number_text = ''.join(numbers)
                                plate_text = small_text + large_text + number_text
                                
                                # Check if has both letters AND numbers
                                has_letters = bool(small_text or large_text)
                                has_numbers = bool(number_text)
                                
                                if has_letters and has_numbers and len(plate_text) >= 4:
                                    # Get average confidence
                                    ocr_conf = sum(x[2] for x in ocr_result) / len(ocr_result)
                                    
                                    # Output immediately if different from last detection or enough time has passed
                                    import time
                                    current_time = time.time()
                                    time_since_last = current_time - last_detection_time
                                    
                                    if plate_text != last_detected_plate or time_since_last >= min_detection_interval:
                                        last_detected_plate = plate_text
                                        last_detection_time = current_time
                                        
                                        # Print to console immediately
                                        print(f"\n{'='*60}")
                                        print(f"PLATE DETECTED: {plate_text}")
                                        print(f"Confidence: {ocr_conf:.2f} | Detection Confidence: {confidence:.2f}")
                                        print(f"Frame: {frame_count}")
                                        print(f"{'='*60}\n")
                                        
                                        # Display on frame
                                        cv2.putText(frame, f"DETECTED: {plate_text}", (10, 50), 
                                                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 3)
                                        cv2.putText(frame, f"Conf: {ocr_conf:.2f}", (10, 90), 
                                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
                        except Exception as e:
                            print(f"OCR Error: {e}")
                            cv2.putText(frame, "OCR ERR", (x1, y1-5), 
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 0, 255), 1)
                    else:
                        # Just show detection without OCR
                        cv2.putText(frame, f"PLATE {confidence:.2f}", (x1, y1-5), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 255, 0), 1)
        
        # Show last result if available
        if last_detected_plate:
            cv2.putText(frame, f"Last: {last_detected_plate}", 
                       (int(width) - 350, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        # Display frame count and status
        cv2.putText(frame, f"Frame: {frame_count} | Detections: {detection_count}", 
                   (10, int(height) - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        cv2.putText(frame, f"Processing every {PROCESS_EVERY_N_FRAMES} frames", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Save frame if enabled
        if SAVE_OUTPUT:
            out.write(frame)
        
        # Display frame (optimized timing)
        cv2.imshow('Plate Detection - Raspberry Pi', frame)
        
        # Minimal delay for responsiveness (1ms instead of 30ms)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            print("\nQuitting...")
            break

except KeyboardInterrupt:
    print("\nInterrupted by user")

finally:
    # Cleanup
    cap.release()
    if SAVE_OUTPUT:
        out.release()
    cv2.destroyAllWindows()
    
    print("\n" + "="*60)
    print(f"Total frames: {frame_count}")
    print(f"Frames processed: {frame_count // PROCESS_EVERY_N_FRAMES}")
    print(f"Plates detected: {detection_count}")
    print("Processing complete!")
    print("="*60)
