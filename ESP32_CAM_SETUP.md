# ESP32-CAM Setup Guide for Raspberry Pi License Plate Recognition

## ⚠️ IMPORTANT: Hardware Compatibility

**You MUST use ESP32-CAM** for camera streaming. Regular boards won't work:

❌ **NOT COMPATIBLE:**
- NodeMCU (ESP8266) - No camera interface, insufficient memory
- ESP8266 boards - Cannot handle video streaming
- Arduino Uno/Nano - No WiFi, no camera support
- Raspberry Pi Pico - No native camera support for streaming

✅ **COMPATIBLE:**
- ESP32-CAM (AI-Thinker) - **RECOMMENDED**
- ESP32-CAM (M5Stack)
- ESP32-CAM (WROVER)
- ESP-EYE

**If you have NodeMCU ESP8266**, you cannot use it for camera streaming. You need to purchase an ESP32-CAM module (~$8-15 USD).

## Hardware Requirements

- **ESP32-CAM module** (AI-Thinker or compatible) - **REQUIRED**
- USB to TTL Serial adapter (FTDI, CP2102, or CH340)
- Jumper wires
- 5V power supply (2A recommended)
- MicroUSB cable

## Wiring for Programming

### Method 1: Using NodeMCU ESP8266 as Programmer (Your Setup)

This is a clever way to use NodeMCU as a USB-to-Serial adapter for ESP32-CAM:

```
NodeMCU (ESP8266)    →    ESP32-CAM
-----------------          ---------
GND                  →    GND
3.3V (or 5V/VIN)    →    5V (use external 5V if current issues)
TX (GPIO1/TXD0)     →    U0R (RX)
RX (GPIO3/RXD0)     →    U0T (TX)

For Programming Mode:
GPIO0               →    GND (connect only during upload)
```

**Important Steps:**
1. **Remove ESP8266 chip** from NodeMCU (or hold RESET on NodeMCU during upload)
2. Connect wires as shown above
3. Connect GPIO0 on ESP32-CAM to GND
4. Plug NodeMCU into USB
5. Upload code to ESP32-CAM
6. **Disconnect GPIO0 from GND**
7. Press RESET on ESP32-CAM

⚠️ **Power Note**: ESP32-CAM needs 2A @ 5V. If NodeMCU 3.3V can't provide enough current:
- Use external 5V 2A power supply to ESP32-CAM 5V pin
- Keep GND connected between all devices

### Method 2: Using USB-to-TTL Adapter

```
USB-TTL     →   ESP32-CAM
-------         ---------
GND         →   GND
5V          →   5V
TX          →   U0R (RX)
RX          →   U0T (TX)

For Programming Mode:
GPIO0       →   GND (connect only during upload)
```

⚠️ **Important**: 
- Connect GPIO0 to GND ONLY when uploading code
- Remove GPIO0-GND connection after upload
- Press RESET button after upload

## Software Setup

### 1. Install Arduino IDE

Download from: https://www.arduino.cc/en/software

### 2. Add ESP32 Board Support

1. Open Arduino IDE
2. Go to **File → Preferences**
3. Add this URL to "Additional Board Manager URLs":
   ```
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
   ```
4. Go to **Tools → Board → Boards Manager**
5. Search for "esp32"
6. Install "esp32 by Espressif Systems"

### 3. Configure Board Settings

1. **Tools → Board** → Select **"AI Thinker ESP32-CAM"** (NOT NodeMCU!)
2. **Tools → Upload Speed** → 115200
3. **Tools → Flash Frequency** → 80MHz
4. **Tools → Flash Mode** → QIO
5. **Tools → Partition Scheme** → Huge APP (3MB No OTA)
6. **Tools → Core Debug Level** → None
7. **Tools → Port** → Select your COM port

⚠️ **If you only see "NodeMCU" options**, you installed ESP8266 boards instead of ESP32. Go back to step 2 and install "esp32 by Espressif Systems".

### 4. Upload the Code

1. Open `esp32_cam_stream.ino` in Arduino IDE
2. **Update WiFi credentials** in the code:
   ```cpp
   const char* ssid = "YOUR_WIFI_SSID";
   const char* password = "YOUR_WIFI_PASSWORD";
   ```
3. Connect GPIO0 to GND (programming mode)
4. Connect USB-to-TTL adapter
5. Press RESET button on ESP32-CAM
6. Click **Upload** in Arduino IDE
7. Wait for "Hard resetting via RTS pin..." message
8. **Disconnect GPIO0 from GND**
9. Press RESET button

### 5. Get IP Address

1. Open **Tools → Serial Monitor**
2. Set baud rate to **115200**
3. Press RESET on ESP32-CAM
4. Note the IP address shown:
   ```
   WiFi Connected!
   IP Address: 192.168.1.100
   Stream URL: http://192.168.1.100:81/stream
   ```

## Testing the Stream

### Test in Web Browser

Open your browser and go to:
```
http://192.168.1.100
```
(Replace with your ESP32-CAM IP)

You should see:
- Live camera preview
- Stream URL
- Configuration info

### Test Stream Directly

```
http://192.168.1.100:81/stream
```

### Test with Python (on Raspberry Pi)

```python
import cv2

stream_url = "http://192.168.1.100:81/stream"
cap = cv2.VideoCapture(stream_url)

while True:
    ret, frame = cap.read()
    if ret:
        cv2.imshow('ESP32-CAM', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
```

## Configure Raspberry Pi Script

Edit `video_plate_recognition_raspi.py`:

```python
# ESP32-CAM Configuration
USE_ESP32_CAM = True
ESP32_CAM_URL = "http://192.168.1.100:81/stream"  # Your ESP32 IP
```

Run the script:
```bash
python3 video_plate_recognition_raspi.py
```

## Camera Settings Optimization

In `esp32_cam_stream.ino`, you can adjust these settings for license plates:

```cpp
// Frame size options (from smallest to largest):
// FRAMESIZE_QQVGA  (160x120)
// FRAMESIZE_QVGA   (320x240)
// FRAMESIZE_VGA    (640x480)   ← Recommended for plates
// FRAMESIZE_SVGA   (800x600)
// FRAMESIZE_XGA    (1024x768)
// FRAMESIZE_SXGA   (1280x1024)
// FRAMESIZE_UXGA   (1600x1200)

config.frame_size = FRAMESIZE_VGA;  // 640x480

// JPEG quality (10-63, lower = better quality, higher = faster)
config.jpeg_quality = 12;  // Good balance for plates

// Brightness (-2 to 2)
s->set_brightness(s, 0);

// Contrast (-2 to 2)
s->set_contrast(s, 0);

// Exposure (0 to 1200)
s->set_aec_value(s, 300);  // Increase for bright conditions
```

## Troubleshooting

### "Camera init failed"
- Check wiring connections
- Ensure 5V power supply is adequate (2A minimum)
- Try pressing RESET button
- Check camera module is properly seated

### "Failed to connect to WiFi"
- Verify SSID and password are correct
- Check WiFi is 2.4GHz (ESP32 doesn't support 5GHz)
- Move ESP32-CAM closer to router
- Check Serial Monitor for error messages

### "Brownout detector was triggered"
- Use better 5V power supply (2A minimum)
- **If using NodeMCU as programmer**: NodeMCU's 3.3V regulator is too weak
  - Use external 5V 2A power supply connected to ESP32-CAM 5V pin
  - Keep GND connected between NodeMCU and ESP32-CAM
- Add 470µF capacitor between 5V and GND on ESP32-CAM
- Don't power from USB-to-TTL adapter during operation

### Poor image quality
- Adjust `jpeg_quality` (lower = better)
- Increase lighting
- Clean camera lens
- Adjust exposure settings

### Stream is slow/laggy
- Reduce frame size to FRAMESIZE_QVGA (320x240)
- Increase `jpeg_quality` value (lower quality, faster)
- Check WiFi signal strength
- Reduce distance to WiFi router

### Can't upload code
- **If using NodeMCU as programmer:**
  - Hold down RESET button on NodeMCU during upload (or remove ESP8266 chip)
  - Ensure TX/RX are correctly connected (TX→RX, RX→TX)
  - Try swapping TX/RX if not working
- Ensure GPIO0 is connected to GND on ESP32-CAM
- Press RESET button on ESP32-CAM before upload
- Check USB-to-TTL TX/RX are not swapped
- Try different USB port or cable
- Select correct COM port in Arduino IDE
- In Arduino IDE, select "AI Thinker ESP32-CAM" NOT "NodeMCU"

## Power Consumption

- ESP32-CAM idle: ~180mA
- ESP32-CAM streaming: ~300-400mA
- **Recommended**: 5V 2A power supply

## Camera Module Variations

If you have a different camera model, change this in the code:

```cpp
// For AI-Thinker (most common)
#define CAMERA_MODEL_AI_THINKER

// For M5Stack
// #define CAMERA_MODEL_M5STACK_PSRAM

// For WROVER KIT
// #define CAMERA_MODEL_WROVER_KIT
```

## Network Configuration

### Static IP (Optional)

To set a static IP, add before `WiFi.begin()`:

```cpp
IPAddress local_IP(192, 168, 1, 100);
IPAddress gateway(192, 168, 1, 1);
IPAddress subnet(255, 255, 255, 0);

WiFi.config(local_IP, gateway, subnet);
```

### Find ESP32-CAM on Network

If you lose the IP address:

**Windows:**
```cmd
arp -a
```

**Linux/Mac:**
```bash
arp -a
nmap -sn 192.168.1.0/24
```

**Router:**
Check DHCP client list in router admin panel

## Performance Tips

1. **Use 2.4GHz WiFi** - ESP32 doesn't support 5GHz
2. **Strong WiFi signal** - Keep ESP32-CAM close to router
3. **Adequate power** - Use 2A power supply
4. **Adjust quality** - Balance between speed and quality
5. **Frame size** - VGA (640x480) is best for license plates

## Security Note

This code uses unencrypted HTTP. For production:
- Add authentication
- Use HTTPS if possible
- Don't expose to internet directly
- Keep on local network only
