"""
Simple ESP32-CAM Stream Test
Tests if ESP32-CAM stream is accessible
"""

import cv2
import sys

# Change this to your ESP32-CAM IP address
ESP32_CAM_IP = "192.168.8.104"  # Your ESP32-CAM IP
ESP32_CAM_URL = f"http://{ESP32_CAM_IP}:81/stream"

print("=" * 60)
print("ESP32-CAM Stream Test")
print("=" * 60)
print(f"Attempting to connect to: {ESP32_CAM_URL}")
print("Make sure your ESP32-CAM is:")
print("  1. Powered on")
print("  2. Connected to WiFi")
print("  3. IP address is correct")
print("=" * 60)

# Try to open stream
cap = cv2.VideoCapture(ESP32_CAM_URL)

if not cap.isOpened():
    print("\n❌ ERROR: Could not connect to ESP32-CAM stream")
    print("\nTroubleshooting:")
    print(f"  1. Check if ESP32-CAM is accessible: Open browser to http://{ESP32_CAM_IP}")
    print(f"  2. Verify stream URL works in browser: {ESP32_CAM_URL}")
    print("  3. Make sure you're on the same network")
    print("  4. Check ESP32-CAM Serial Monitor for actual IP address")
    sys.exit(1)

print("✅ Connected successfully!")
print("\nReading stream...")

frame_count = 0
try:
    while True:
        ret, frame = cap.read()
        
        if not ret:
            print("\n⚠️ Failed to read frame")
            break
        
        frame_count += 1
        
        # Get frame info
        height, width = frame.shape[:2]
        
        # Display info on frame
        cv2.putText(frame, f"ESP32-CAM Stream - Frame: {frame_count}", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f"Resolution: {width}x{height}", 
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, "Press 'q' to quit", 
                   (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        # Show frame
        cv2.imshow('ESP32-CAM Stream Test', frame)
        
        # Print status every 30 frames
        if frame_count % 30 == 0:
            print(f"Frames received: {frame_count} | Resolution: {width}x{height}")
        
        # Press 'q' to quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("\nQuitting...")
            break

except KeyboardInterrupt:
    print("\n\nInterrupted by user")

finally:
    cap.release()
    cv2.destroyAllWindows()
    print(f"\nTotal frames received: {frame_count}")
    print("Stream test complete!")
    print("=" * 60)
