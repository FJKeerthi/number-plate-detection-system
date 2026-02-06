/*
 * ESP32-CAM Video Stream Server for Raspberry Pi License Plate Recognition
 * Based on Official Arduino ESP32-CAM Example
 * 
 * This sketch turns your ESP32-CAM into a streaming server that can be accessed
 * by the Raspberry Pi license plate recognition system.
 * 
 * Features:
 * - MJPEG video stream using official ESP32-CAM server
 * - Configurable resolution and quality with PSRAM support
 * - Web interface for camera settings
 * - Low latency streaming optimized for license plate detection
 * 
 * Hardware: ESP32-CAM (AI-Thinker or similar with PSRAM)
 * 
 * Upload Instructions:
 * 1. Install ESP32 board support in Arduino IDE (version 2.0.0 or higher)
 * 2. Select "AI Thinker ESP32-CAM" board
 * 3. Tools > Partition Scheme: "Huge APP (3MB No OTA/1MB SPIFFS)"
 * 4. Connect ESP32-CAM using USB-to-TTL adapter (GPIO0 to GND for programming)
 * 5. Update WiFi credentials below
 * 6. Upload sketch
 * 7. Remove GPIO0-GND connection and reset
 * 8. Open Serial Monitor at 115200 baud to get IP address
 * 
 * IMPORTANT: PSRAM IC required for UXGA resolution and high JPEG quality
 */

#include "esp_camera.h"
#include <WiFi.h>

// ===================
// Select camera model
// ===================
#define CAMERA_MODEL_AI_THINKER // Has PSRAM

// Pin definitions for AI-Thinker ESP32-CAM
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27

#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

#define LED_GPIO_NUM       4

// ===========================
// WiFi credentials - UPDATE THESE!
// ===========================
const char *ssid = "Potato";
const char *password = "G5YNAMR4GL3";

void startCameraServer();
void setupLedFlash();

void setup() {
  Serial.begin(115200);
  Serial.setDebugOutput(true);
  Serial.println();
  Serial.println("===========================================");
  Serial.println("ESP32-CAM for Raspberry Pi License Plate Recognition");
  Serial.println("Based on Official Arduino ESP32-CAM Example");
  Serial.println("===========================================");

  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.frame_size = FRAMESIZE_VGA;  // Start with VGA for license plates
  config.pixel_format = PIXFORMAT_JPEG;  // for streaming
  //config.pixel_format = PIXFORMAT_RGB565; // for face detection/recognition
  config.grab_mode = CAMERA_GRAB_WHEN_EMPTY;
  config.fb_location = CAMERA_FB_IN_PSRAM;
  config.jpeg_quality = 10;  // Lower number = better quality (0-63)
  config.fb_count = 1;

  // if PSRAM IC present, init with UXGA resolution and higher JPEG quality
  //                      for larger pre-allocated frame buffer.
  if (config.pixel_format == PIXFORMAT_JPEG) {
    if (psramFound()) {
      config.jpeg_quality = 10;  // Better quality for license plates
      config.fb_count = 2;
      config.grab_mode = CAMERA_GRAB_LATEST;
    } else {
      // Limit the frame size when PSRAM is not available
      config.frame_size = FRAMESIZE_VGA;  // Use VGA even without PSRAM
      config.fb_location = CAMERA_FB_IN_DRAM;
    }
  } else {
    // Best option for face detection/recognition
    config.frame_size = FRAMESIZE_240X240;
#if CONFIG_IDF_TARGET_ESP32S3
    config.fb_count = 2;
#endif
  }

#if defined(CAMERA_MODEL_ESP_EYE)
  pinMode(13, INPUT_PULLUP);
  pinMode(14, INPUT_PULLUP);
#endif

  // camera init
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x", err);
    return;
  }

  sensor_t *s = esp_camera_sensor_get();
  // initial sensors are flipped vertically and colors are a bit saturated
  if (s->id.PID == OV3660_PID) {
    s->set_vflip(s, 1);        // flip it back
    s->set_brightness(s, 1);   // up the brightness just a bit
    s->set_saturation(s, -2);  // lower the saturation
  }
  
  // drop down frame size for higher initial frame rate
  // Optimized for license plate recognition - VGA is ideal
  if (config.pixel_format == PIXFORMAT_JPEG) {
    s->set_framesize(s, FRAMESIZE_VGA);  // 640x480 - good for license plates
    s->set_hmirror(s, 1);                // Enable horizontal mirror
    s->set_quality(s, 10);               // JPEG quality (0-63, lower = better)
  }

#if defined(CAMERA_MODEL_M5STACK_WIDE) || defined(CAMERA_MODEL_M5STACK_ESP32CAM)
  s->set_vflip(s, 1);
  s->set_hmirror(s, 1);
#endif

#if defined(CAMERA_MODEL_ESP32S3_EYE)
  s->set_vflip(s, 1);
#endif

  // Setup LED Flash if LED pin is defined in camera_pins.h
#if defined(LED_GPIO_NUM)
  setupLedFlash();
#endif

  WiFi.begin(ssid, password);
  WiFi.setSleep(false);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.println("WiFi connected");

  startCameraServer();

  Serial.println("===========================================");
  Serial.print("Camera Ready! Use 'http://");
  Serial.print(WiFi.localIP());
  Serial.println("' to connect");
  Serial.println("");
  Serial.println("For Raspberry Pi, use this stream URL:");
  Serial.print("http://");
  Serial.print(WiFi.localIP());
  Serial.println(":81/stream");
  Serial.println("===========================================");
}

void loop() {
  // Do nothing. Everything is done in another task by the web server
  delay(10000);
}
