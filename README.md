# Cinematic Drone AI: Hardware-In-The-Loop Mock Streaming

A professional ROS 2 Jazzy and PX4 SITL simulation architecture. This package demonstrates a deterministic "mock streaming" AI pipeline for drones, leveraging YOLOv8 for real-time human detection with cinematic video feed switching gated by live flight telemetry.
##Watch the DEMO Video here ---------> https://lnkd.in/p/guNxqQuw

## 🏗️ Architecture Overview

To ensure zero hardware failure during live demonstrations, this project utilizes a **Hardware/Software-In-The-Loop Mock Streaming** approach. The physical camera sensor is replaced with a deterministic video playback engine that dynamically interacts with real flight logic.

* **The Flight Gate:** The AI node drops all video frames to save bandwidth while the drone is grounded. It listens to the PX4 Micro-XRCE DDS agent (`/fmu/out/vehicle_status_v4`), unlocking the video stream the exact millisecond the drone enters `Takeoff` mode.
* **Dual-Feed Switching:** The system maintains two live video states:
  * **Search Mode (Empty Feed):** When no targets are present, YOLOv8 detects zero humans and outputs a cinematic `TRACKING...` HUD.
  * **Action Mode (People Feed):** Upon receiving a ROS 2 topic trigger, the system swaps to a populated feed. YOLOv8 instantly plots bounding boxes, and the system alerts the terminal.

## ⚙️ Tech Stack
* **OS:** Ubuntu 24.04 (Noble Numbat)
* **Middleware:** ROS 2 Jazzy Jalisco
* **Simulation:** PX4 Autopilot SITL + Gazebo Harmonic
* **AI/CV:** Ultralytics YOLOv8 Nano + OpenCV (`cv_bridge`)
* **Telemetry & Visualization:** MicroXRCEAgent + Foxglove Studio

## 🚀 Installation & Setup

1. **Clone the Repository:**
   ```bash
   cd ~/ros2_ws/src
   git clone <YOUR_GITHUB_REPO_URL>
