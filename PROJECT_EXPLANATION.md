# License Plate Detection System - Project Documentation

## 📋 Project Overview

This is a **two-stage AI-powered license plate detection and recognition system** designed for real-time vehicle license plate reading. The system combines computer vision and optical character recognition (OCR) to detect and read license plates from images and video streams.

---

## 🎯 System Architecture

### **Stage 1: License Plate Detection (YOLOv5)**
- **Model**: Custom-trained YOLOv5s
- **Purpose**: Detect and localize license plate regions in images/video frames
- **Output**: Bounding box coordinates + confidence scores

### **Stage 2: Text Recognition (EasyOCR)**
- **Model**: Pre-trained EasyOCR (CRAFT + CRNN)
- **Purpose**: Read alphanumeric text from detected license plate regions
- **Output**: Recognized text + confidence scores

```
Input Image/Video → YOLOv5 Detection → Crop Plate Region → Resize 3x → EasyOCR → License Plate Text
```

---

## 🔧 Training Process

### **1. Dataset Preparation**

#### Input Data Format:
- **Images**: `.jpg` files containing vehicles with visible license plates
- **Annotations**: Pascal VOC XML format with bounding box coordinates
  - Format: `<xmin>`, `<ymin>`, `<xmax>`, `<ymax>`
  - Single class: `license`

#### Preprocessing Steps:
1. **XML Parsing**: Extract bounding boxes from annotation files
2. **Format Conversion**: Convert absolute coordinates to YOLO normalized format
   ```
   x_center = (xmin + xmax) / 2 / image_width
   y_center = (ymin + ymax) / 2 / image_height
   width = (xmax - xmin) / image_width
   height = (ymax - ymin) / image_height
   ```
3. **Data Organization**: Create pandas DataFrame for easy manipulation
4. **Label Generation**: Save as `.txt` files in YOLO format: `class_id x_center y_center width height`

### **2. Dataset Split**
- **Training**: 80%
- **Validation**: 20%
- **Tool**: `splitfolders` library
- **Random Seed**: 42 (for reproducibility)

### **3. Model Training Configuration**

```yaml
Architecture: YOLOv5s (small variant - faster inference)
Input Size: 800x800 pixels
Batch Size: 16
Epochs: 200
Workers: 2 (parallel data loading)
Device: GPU (CUDA device 0)
Cache: Enabled (faster training)
Base Weights: yolov5s.pt (pre-trained on COCO)
Classes: 1 (license plate only)
```

#### Transfer Learning Approach:
- Started with `yolov5s.pt` weights (trained on COCO dataset)
- Fine-tuned on custom license plate dataset
- Leverages pre-learned features for faster convergence

### **4. Training Output**
- **best.pt**: Best performing model weights (lowest validation loss)
- **last.pt**: Final epoch weights
- **Training metrics**: Precision, recall, mAP@0.5, loss curves

---

## 🚀 Inference Pipeline

### **Detection Parameters**
- **YOLOv5 Confidence Threshold**: 0.3 (30%)
- **IOU Threshold**: 0.45
- **Max Detections**: 3 plates per frame
- **Input Size**: 416x416 (Raspberry Pi) / 640x640 (Desktop)

### **OCR Enhancement Techniques**
1. **Padding**: Add 5% padding around detected plate (capture full context)
2. **Upscaling**: Resize plate region 3x using INTER_CUBIC interpolation
3. **Character Filtering**: Allowlist = `'0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ-'`
4. **Text Validation**: Ensure both letters AND numbers are present (min 4 chars)

### **Sri Lankan License Plate Format Detection**
The system intelligently handles Sri Lankan plate formats by:
- Separating small letters (province codes)
- Separating large letters (district/vehicle codes)
- Separating numbers
- Formatting: `SmallLetters + LargeLetters + Numbers`

Example: `ශ්‍රී + ABC + 1234` → `ABC1234`

---

## 📦 Model Components

### **Final Deployment Package**

#### 1. **Custom YOLOv5 Model** ⭐ (Your trained model)
- **File**: `best.pt` (~14MB)
- **Type**: Object detection
- **Framework**: PyTorch
- **Status**: Trained on your dataset

#### 2. **EasyOCR Models** (Pre-trained)
- **Files**: 
  - `craft_mlt_25k.pth` - Text detection model
  - `english_g2.pth` - Character recognition model
- **Location**: `./easyocr_models/`
- **Status**: Downloaded automatically on first run

#### 3. **Required Libraries**
```
torch
torchvision
opencv-python
easyocr
numpy
pandas
```

---

## 💻 Implementation Variants

### **1. Desktop Version** (`video_plate_recognition.py`)
- Full processing power
- Higher resolution (640x640)
- Real-time display with annotations
- Video recording capability

### **2. Raspberry Pi Version** (`video_plate_recognition_raspi.py`)
- Optimized for low-power devices
- Reduced input size (416x416)
- FP16 precision (if supported)
- Frame skipping for performance
- **Immediate detection mode**: No buffering, instant output

### **3. ESP32-CAM Integration**
- MJPEG stream support
- Network-based video capture
- Automatic reconnection on stream loss
- Low-latency buffer management

---

## 🔍 Key Features

### **Performance Optimizations**
- ✅ Frame skipping (process every N frames)
- ✅ Minimal buffering for reduced latency
- ✅ Half-precision inference (FP16 on Pi)
- ✅ Reduced input resolution for speed
- ✅ Efficient OCR with character allowlist

### **Detection Reliability**
- ✅ Confidence-based filtering
- ✅ Text validation (require letters AND numbers)
- ✅ Time-based duplicate suppression
- ✅ Smart character grouping (small/large letters, numbers)

### **Real-time Processing**
- ✅ Immediate output on detection
- ✅ Streaming reconnection logic
- ✅ Live visualization with bounding boxes
- ✅ Console logging with timestamps

---

## 📊 Preprocessing Summary

| **Stage** | **Technique** | **Purpose** |
|-----------|---------------|-------------|
| **Training Data** | XML → YOLO format | Convert annotations to model format |
| **Training Data** | Normalize coordinates | Scale-independent representation |
| **Training Data** | 80/20 split | Prevent overfitting |
| **Inference** | 3x upscaling | Improve OCR accuracy |
| **Inference** | 5% padding | Capture full plate context |
| **Inference** | Character filtering | Remove invalid detections |
| **Inference** | Text validation | Ensure realistic plate format |

### **No Traditional Image Preprocessing**
- ❌ No brightness/contrast adjustment during training
- ❌ No denoise filters
- ❌ No histogram equalization
- ❌ No augmentation (except YOLOv5 built-in)

**Why?** YOLOv5 handles variations internally through:
- Mosaic augmentation
- Random affine transforms
- HSV color space augmentation
- Random flip

---

## 🎓 Model Training Results

### **Training Environment**
- **Platform**: Google Colab (GPU)
- **Training Time**: Varies (200 epochs)
- **GPU**: CUDA-enabled device

### **Deliverables**
1. `best.pt` - Production-ready model
2. `last.pt` - Backup/comparison model
3. Training plots (precision, recall, loss)
4. Confusion matrix
5. Sample predictions

---

## 🚦 Usage Scenarios

### **Scenario 1: Single Image Testing**
- Load model
- Read image
- Detect plate region
- Enhance and read text
- Display result

### **Scenario 2: Video Processing**
- Open video stream (file/webcam)
- Process frame by frame
- Real-time detection and OCR
- Save annotated output

### **Scenario 3: ESP32-CAM Real-time**
- Connect to ESP32-CAM MJPEG stream
- Process frames on Raspberry Pi
- Immediate detection output
- Handle stream interruptions

---

## 🔮 Future Improvements

### **Potential Enhancements**
1. **Training**:
   - Data augmentation (rotation, blur, weather conditions)
   - More diverse dataset (different angles, lighting)
   - Multi-scale training

2. **Inference**:
   - GPU acceleration on desktop
   - TensorRT optimization
   - ONNX export for cross-platform

3. **OCR**:
   - Language-specific models (Sinhala/Tamil)
   - Custom OCR training for local fonts
   - Post-processing rules (plate format validation)

4. **System**:
   - Database integration (store detections)
   - Web API (REST/WebSocket)
   - Mobile app integration

---

## 📝 File Structure

```
slnumplate/
├── best.pt                              # Custom YOLOv5 weights ⭐
├── yolov5s.pt                          # Base YOLOv5 weights
├── yolov5n.pt                          # Nano variant
├── video_plate_recognition.py          # Desktop version
├── video_plate_recognition_raspi.py    # Raspberry Pi optimized
├── server.py                           # Web server (if applicable)
├── test_esp32_stream.py               # ESP32 testing
├── sl_number_plate.ipynb              # Training notebook
├── requirements.txt                    # Python dependencies
├── requirements_raspi.txt             # Raspberry Pi specific
├── easyocr_models/                    # OCR model weights
│   ├── craft_mlt_25k.pth
│   └── english_g2.pth
├── ESP32_CAM_SETUP.md                 # Hardware setup guide
└── README.md                           # Main documentation
```

---

## 🏆 Summary

This license plate detection system combines:
1. **Custom-trained YOLOv5** for accurate plate localization
2. **Pre-trained EasyOCR** for reliable text recognition
3. **Smart preprocessing** for OCR enhancement
4. **Optimized inference** for real-time performance
5. **Platform-specific variants** (Desktop/Raspberry Pi/ESP32-CAM)

The final model (`best.pt` + EasyOCR) works as a **coordinated pipeline** where YOLOv5 finds plates and EasyOCR reads them, achieving both speed and accuracy for practical license plate recognition applications.

---

**Created**: February 2026  
**Platform**: Windows/Linux/Raspberry Pi  
**Frameworks**: PyTorch, OpenCV, EasyOCR
