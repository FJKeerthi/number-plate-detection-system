# ESP32-CAM Setup - Updated with Official Arduino Example

## Changes Made

Your `esp32_cam_stream.ino` file has been updated to use the official Arduino ESP32-CAM example structure. This provides better compatibility and reliability.

### Key Updates:

1. **Official Camera Initialization**: Uses the standard ESP32-CAM configuration from Arduino examples
2. **PSRAM Support**: Properly detects and utilizes PSRAM for higher quality streams
3. **Built-in Camera Server**: Uses `startCameraServer()` function from ESP32 camera library
4. **Better Pin Management**: Includes `camera_pins.h` for proper pin definitions
5. **Optimized for License Plates**: Set to VGA resolution (640x480) which is ideal for plate recognition
6. **WiFi Credentials**: Pre-configured with your WiFi (SSID: "Potato")

## How to Upload to ESP32-CAM

### Hardware Setup:
1. Connect ESP32-CAM to USB-to-TTL adapter:
   - **5V** → VCC (ESP32-CAM)
   - **GND** → GND
   - **TX** → U0R (RX on ESP32)
   - **RX** → U0T (TX on ESP32)
   - **GPIO0** → GND (for programming mode)

2. Connect USB-to-TTL to your computer

### Arduino IDE Configuration:
1. Install ESP32 board support (if not already):
   - File → Preferences
   - Add to "Additional Board Manager URLs": 
     ```
     https://espressif.github.io/arduino-esp32/package_esp32_index.json
     ```
   - Tools → Board → Boards Manager → Search "ESP32" → Install

2. Select Board:
   - Tools → Board → ESP32 Arduino → **AI Thinker ESP32-CAM**

3. Configure Settings:
   - **CPU Frequency**: 240MHz
   - **Flash Frequency**: 80MHz
   - **Flash Mode**: QIO
   - **Partition Scheme**: **Huge APP (3MB No OTA/1MB SPIFFS)**
   - **Upload Speed**: 115200

4. Select Port:
   - Tools → Port → (Select your USB-to-TTL COM port)

### Upload Process:
1. Make sure GPIO0 is connected to GND
2. Press the Reset button on ESP32-CAM
3. Click **Upload** in Arduino IDE
4. Wait for "Connecting...." message
5. Once uploaded successfully:
   - Disconnect GPIO0 from GND
   - Press Reset button
   - Open Serial Monitor (115200 baud)
   - You should see the IP address

## Using with Raspberry Pi

Once the ESP32-CAM is running:

1. **Get the IP Address**: Check Serial Monitor (115200 baud)
   - You'll see something like: `Camera Ready! Use 'http://192.168.1.100' to connect`
   - Stream URL will be: `http://192.168.1.100:81/stream`

2. **Update Raspberry Pi Script**: In `video_plate_recognition_raspi.py`, set:
   ```python
   USE_ESP32_CAM = True
   ESP32_CAM_URL = "http://192.168.1.100:81/stream"  # Use your actual IP
   ```

3. **Test the Stream**: Open a web browser and go to:
   - Main interface: `http://192.168.1.100`
   - Direct stream: `http://192.168.1.100:81/stream`

## Troubleshooting

### "Camera init failed"
- Check if you selected the correct board (AI Thinker ESP32-CAM)
- Verify PSRAM is available
- Try different partition scheme

### "WiFi not connecting"
- Double-check WiFi credentials in the code
- Make sure you're using 2.4GHz WiFi (ESP32 doesn't support 5GHz)
- Check if WiFi is in range

### "Upload failed"
- Ensure GPIO0 is connected to GND during upload
- Press Reset button before uploading
- Try lower upload speed (115200)
- Check USB-to-TTL connections

### "Brownout detector triggered"
- Use external 5V power supply (not USB)
- Ensure power supply can deliver at least 500mA

## Stream Details

- **Resolution**: 640x480 (VGA) - Optimal for license plate recognition
- **Format**: MJPEG stream
- **Port 80**: Web interface with live preview
- **Port 81**: Direct stream endpoint for Raspberry Pi
- **JPEG Quality**: 10 (high quality when PSRAM available)
- **Frame Buffer**: 2 buffers for smooth streaming

## Next Steps

1. Upload the code to your ESP32-CAM
2. Note the IP address from Serial Monitor
3. Test the stream in a web browser
4. Update your Raspberry Pi script with the stream URL
5. Run the license plate recognition on Raspberry Pi

The ESP32-CAM will now work as a video source for your Raspberry Pi license plate recognition system!
