"""
License Plate Recognition - Video Processing
This script detects and reads license plates from video files or webcam streams using YOLOv5 and EasyOCR.
"""

import torch
import easyocr
import pathlib
import numpy as np
import cv2
import warnings
import time
import base64
import requests
from collections import Counter

# Suppress FutureWarning messages from PyTorch
warnings.filterwarnings('ignore', category=FutureWarning)

# On Windows, unpickling objects that include pathlib.PosixPath (saved on POSIX systems)
# raises: NotImplementedError: cannot instantiate 'PosixPath' on your system.
# Map PosixPath to WindowsPath so torch.load (pickle) can instantiate paths correctly.
pathlib.PosixPath = pathlib.WindowsPath

# Windows path to your custom YOLOv5 weights
weights_path = r"best.pt"

# Check GPU availability
device = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f"Using device: {device}")
if device == 'cuda':
    print(f"GPU: {torch.cuda.get_device_name(0)}")

# Load custom YOLOv5 model 
print("Loading YOLOv5 model...")
model = torch.hub.load('ultralytics/yolov5', 'custom', path='best.pt', force_reload=False)
model.to(device)  # Move model to GPU
model.conf = 0.35  # Lower for better detection (was 0.5)
model.iou = 0.45  # IOU threshold for NMS
model.max_det = 5  # Increased for multiple plates
print("Model loaded successfully!")
# Using best.pt (your trained model) for better accuracy

# Initialize EasyOCR reader with CPU (more stable, avoids CUDA errors)
print("Initializing EasyOCR reader...")
reader = easyocr.Reader(['en'], gpu=False)  # Use CPU to avoid CUDA compatibility issues
print("EasyOCR reader initialized (CPU mode)!")

# Web server configuration
SERVER_URL = "http://localhost:5000/api/detect"  # Change if server is on different host
SEND_TO_SERVER = True  # Set to False to disable sending to server

# Process video stream (webcam or video file)

# OPTION 1: Use video file
video_source = "http://192.168.8.104:81/stream"
#"http://192.168.8.104:81/stream"

# OPTION 2: Use webcam (uncomment the line below and comment the line above)
# video_source = 0  # 0 = default webcam, 1 = external webcam

# Open video stream
print(f"\nOpening video source: {video_source}")
cap = cv2.VideoCapture(video_source)

# Check if video opened successfully
if not cap.isOpened():
    print("Error: Could not open video stream")
    exit()

print("Video stream opened successfully")
print("Press 'q' to quit")

# Get video properties
fps = int(cap.get(cv2.CAP_PROP_FPS))
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
print(f"Video: {frame_width}x{frame_height} @ {fps} FPS")

# Optional: Save output video
save_output = True  # Set to False if you don't want to save
if save_output:
    output_video_path = r"output_video.avi"
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (frame_width, frame_height))
    print(f"Saving output to: {output_video_path}")

frame_count = 0
process_every_n_frames = 1  # Process every frame for faster real-time detection
last_detected_plate = ""  # Cache last detected plate

# Time-based detection (simpler approach)
detection_buffer = []  # Store all detected plates
time_limit = 5.0  # 5 seconds to collect predictions
start_time = time.time()  # Start timer

print("\n" + "="*60)
print("Starting video processing...")
print(f"Detection mode: 5 second time window")
print(f"Processing every {process_every_n_frames} frames for speed")
print("="*60 + "\n")

# Process video frame by frame
while True:
    # Read frame
    ret, frame = cap.read()
    
    # Break if no frame is captured (end of video)
    if not ret:
        print("End of video stream or failed to capture frame")
        break
    
    # Flip frame horizontally (ESP32-CAM gives mirrored image)
    frame = cv2.flip(frame, 1)  # 1 = horizontal flip
    
    frame_count += 1
    
    # Skip frames for faster processing
    if frame_count % process_every_n_frames != 0:
        # Display frame count on skipped frames
        cv2.putText(frame, f"Frame: {frame_count} (SKIPPED)", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        if save_output:
            out.write(frame)
        cv2.imshow('License Plate Detection - Video Stream', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("Quitting...")
            break
        continue
    
    # Resize frame for faster inference (640x480 is already good, but can go smaller)
    # frame_resized = cv2.resize(frame, (320, 240))  # Uncomment for even faster processing
    
    # Convert BGR to RGB for YOLOv5
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # Run YOLOv5 detection with smaller size for faster processing
    results = model(frame_rgb, size=416)  # 416 for faster inference
    
    # Get detection results
    labels, coordinates = results.xyxyn[0][:, -1], results.xyxyn[0][:, :-1]
    height, width = frame.shape[:2]
    
    # Collect all OCR results from this frame to combine them
    frame_ocr_texts = []
    
    # Process each detected plate
    for i, row in enumerate(coordinates):
        confidence = row[4]
        
        if confidence >= 0.35:  # Lower threshold for better detection
            # Get bounding box coordinates
            x1, y1, x2, y2 = int(row[0]*width), int(row[1]*height), int(row[2]*width), int(row[3]*height)
            
            # Add padding
            padding_x = int((x2 - x1) * 0.05)
            padding_y = int((y2 - y1) * 0.05)
            x1 = max(0, x1 - padding_x)
            y1 = max(0, y1 - padding_y)
            x2 = min(width, x2 + padding_x)
            y2 = min(height, y2 + padding_y)
            
            # Crop and resize plate
            plate_crop = frame[y1:y2, x1:x2]
            
            if plate_crop.size > 0:  # Check if crop is valid
                # Resize to 2x for faster OCR
                h, w = plate_crop.shape[:2]
                plate_resized = cv2.resize(plate_crop, (w * 2, h * 2), 
                                           interpolation=cv2.INTER_LINEAR)  # LINEAR for speed
                
                # Enhance image for better OCR
                plate_resized = cv2.cvtColor(plate_resized, cv2.COLOR_BGR2GRAY)
                plate_resized = cv2.equalizeHist(plate_resized)  # Improve contrast
                
                # Run OCR with optimizations
                ocr_result = reader.readtext(plate_resized, 
                                            allowlist='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ-',
                                            paragraph=False,
                                            batch_size=1)  # Lower batch for less memory
                
                # Draw bounding box
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                
                # Collect all OCR text from this detection
                if ocr_result:
                    for detection in ocr_result:
                        bbox = detection[0]  # Bounding box coordinates
                        text = detection[1].strip()
                        conf = detection[2]
                        
                        if conf >= 0.5 and len(text) >= 1:
                            # Calculate text height from bounding box
                            text_height = abs(bbox[2][1] - bbox[0][1])  # Height of text
                            # Store: (text, confidence, x1, y1, x2, y2, height)
                            frame_ocr_texts.append((text, conf, x1 + bbox[0][0], y1, x2, y2, text_height))
    
    # Combine all detected texts into one plate number
    if frame_ocr_texts:
        # Sort by x-coordinate (left to right)
        frame_ocr_texts.sort(key=lambda x: x[2])
        
        # Separate letters by size and numbers
        small_letters = []  # Province code (smaller)
        large_letters = []  # Vehicle code (larger)
        numbers = []
        
        # Calculate average height for letter detections only
        letter_heights = [(t[0], t[6]) for t in frame_ocr_texts if t[0].isalpha()]
        
        if letter_heights:
            avg_letter_height = sum([h[1] for h in letter_heights]) / len(letter_heights)
            
            # Categorize each text piece
            for text_data in frame_ocr_texts:
                text = text_data[0]
                height = text_data[6]
                
                # Separate based on content type
                if text.isalpha():
                    # If height is below average, it's small (province)
                    # If height is above average, it's large (vehicle code)
                    if height < avg_letter_height * 0.95:  # 5% tolerance
                        small_letters.append(text)
                    else:
                        large_letters.append(text)
                elif text.isdigit():
                    numbers.append(text)
                else:
                    # Mixed - separate letters and numbers
                    for c in text:
                        if c.isalpha():
                            large_letters.append(c)  # Default to large if mixed
                        elif c.isdigit():
                            numbers.append(c)
        else:
            # No letters detected, just get numbers
            for text_data in frame_ocr_texts:
                text = text_data[0]
                for c in text:
                    if c.isdigit():
                        numbers.append(c)
        
        # Format: SMALL_LETTERS + LARGE_LETTERS + NUMBERS
        small_text = ''.join(small_letters).upper()
        large_text = ''.join(large_letters).upper()
        number_text = ''.join(numbers)
        formatted_plate = small_text + large_text + number_text
        
        # Only proceed if we have BOTH letters AND numbers
        has_letters = bool(small_text or large_text)
        has_numbers = bool(number_text)
        
        if not (has_letters and has_numbers):
            # Skip this detection - incomplete plate (only letters or only numbers)
            pass
        else:
            avg_confidence = sum([t[1] for t in frame_ocr_texts]) / len(frame_ocr_texts)
            
            # Add to detection buffer
            if len(formatted_plate) >= 4:
                detection_buffer.append(formatted_plate)
    
    # Check if 5 seconds have passed
    elapsed_time = time.time() - start_time
    
    if elapsed_time >= time_limit and detection_buffer:
        # Find the most common plate
        plate_counts = Counter(detection_buffer)
        most_common = plate_counts.most_common(1)[0]  # (plate, count)
        detected_plate = most_common[0]
        count = most_common[1]
        
        # Only show if different from last output
        if detected_plate != last_detected_plate:
            last_detected_plate = detected_plate
            
            # Print to console
            print(f"\n{'='*60}")
            print(f"PLATE DETECTED: {detected_plate}")
            print(f"Detections: {count}/{len(detection_buffer)} over {elapsed_time:.1f} seconds")
            print(f"{'='*60}\n")
            
            # Send to web server
            if SEND_TO_SERVER:
                try:
                    # Encode frame as JPEG
                    _, buffer = cv2.imencode('.jpg', frame)
                    image_base64 = base64.b64encode(buffer).decode('utf-8')
                    
                    # Prepare data
                    data = {
                        'plate_number': detected_plate,
                        'detection_count': count,
                        'total_detections': len(detection_buffer),
                        'image': image_base64
                    }
                    
                    # Send POST request
                    response = requests.post(SERVER_URL, json=data, timeout=2)
                    
                    if response.status_code == 200:
                        print(f"✅ Sent to server successfully!")
                    else:
                        print(f"⚠️ Server returned status {response.status_code}")
                        
                except requests.exceptions.ConnectionError:
                    print(f"❌ Could not connect to server at {SERVER_URL}")
                except Exception as e:
                    print(f"❌ Error sending to server: {e}")
            
            # Display on frame
            cv2.putText(frame, f"RESULT: {detected_plate}", (10, 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
            cv2.putText(frame, f"{count}/{len(detection_buffer)} detections", (10, 90), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        
        # Reset buffer and timer
        detection_buffer = []
        start_time = time.time()
    
    # Show analysis status on frame
    progress = (elapsed_time / time_limit) * 100
    cv2.putText(frame, f"Analyzing: {progress:.0f}% ({elapsed_time:.1f}s / {time_limit:.0f}s)", 
               (10, int(height) - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    # Show current detections in buffer
    if detection_buffer:
        cv2.putText(frame, f"Buffered: {len(detection_buffer)} detections", 
                   (10, int(height) - 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)
    
    # Show last result if available
    if last_detected_plate:
        cv2.putText(frame, f"Last: {last_detected_plate}", 
                   (int(width) - 300, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
    
    # Display frame count and FPS
    cv2.putText(frame, f"Frame: {frame_count} (Processing every {process_every_n_frames})", (10, 30), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    # Save frame to output video
    if save_output:
        out.write(frame)
    
    # Display the frame
    cv2.imshow('License Plate Detection - Video Stream', frame)
    
    # Press 'q' to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        print("Quitting...")
        break

# Release resources
cap.release()
if save_output:
    out.release()
cv2.destroyAllWindows()

print("\n" + "="*60)
print(f"Processed {frame_count} frames")
print("Video processing complete!")
print("="*60)
