# Medical Camera User Manual (V2.0)

## 1. Software Overview
This software is designed for medical endoscopy imaging systems, supporting Hikvision industrial cameras (GigE/USB3.0) and standard UVC protocol cameras. It provides real-time image acquisition, image parameter control, precision geometric recognition, and result analysis.

## 2. Device Connection and Management
### 2.1 Camera Type Selection
In the "Device List" on the left panel, you can choose:
- **Hikvision Industrial Camera**: Connect via Hikvision MVS driver, supports high-precision exposure and gain adjustment.
- **USB Camera**: Supports standard driver-free UVC modules, suitable for most endoscopic modules.

### 2.2 Enumeration and Opening
- Click the "Refresh" icon to enumerate the hardware currently connected to the system.
- Select the target device and click "Open Camera" to enter the real-time preview.
- If connection fails, check if the device is occupied by other software or if the driver is installed.

## 3. Image Parameter Adjustment
### 3.1 Exposure and Gain
- **Hikvision Camera**: Supports fine numerical stepping, supports manual/auto exposure switching.
- **USB Camera**: Provides standard UVC adjustment items, including brightness, contrast, etc.

### 3.2 White Balance
- Supports real-time RGB three-channel gain adjustment.
- Recommended to perform "Auto White Balance" calibration under standard color temperature light sources.

## 4. Recognition Control Functions
The core function of this system is the automatic detection of specific geometric features in the image.

### 4.1 Recognition Area (Scope)
- **Full Image Mode**: Performs full analysis on the entire frame.
- **ROI Selection**: Generate a blue region of interest by dragging the mouse in the preview area, performing recognition only in this region to greatly improve the frame rate.
- **Three-Point Circle**: For circular endoscopic fields of view, users click three edge points, and the system automatically fits the perfect circular boundary (Circumcircle).

### 4.2 Field of View Type and Threshold
- Supports "Circular FOV" and "Rectangular FOV" detection.
- **FOV Boundary Threshold**: Adjust the binarization threshold to adapt to different background light intensities.
- **Circle Extraction Threshold**: Adjust the sensitivity of circularity fitting.

## 5. Overlay Display and Assistance
Assistant lines can be enabled via the "Display Overlay" panel:
- **FOV Boundary**: Highlights the detected FOV edges.
- **Inner Shapes**: Displays detected geometric features (e.g., 5-point calibration blocks).
- **n% FOV Ring**: Custom proportional reference circle for distortion testing.
- **Crosshair/Starhair**: Assists in composition and center alignment.

## 6. Recognition Result Analysis
Recognition results are displayed in real-time in the bottom-right table:
- **Orientation**: Coordinates of feature points relative to the center.
- **Major/Minor Axis**: Dimensions of the detected geometry.

## 7. Configuration Management
- **Save Config**: Saves all current camera parameters, recognition algorithm settings, and ROI coordinates locally to `config_auto.json`.
- **Load Config**: Restore a previously saved complex test environment with one click.
- **Restore Defaults**: Reset all parameters to factory settings.

## 8. Troubleshooting
- **Black Screen**: Check if the camera is open or if the resolution exceeds hardware bandwidth.
- **Inaccurate Recognition**: Ensure uniform lighting and properly adjust the "FOV Boundary Threshold".
- **Software Lag**: It is recommended to enable "ROI Selection" mode to reduce the image processing burden.
