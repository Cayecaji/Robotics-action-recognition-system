# Robotics Action Recognition System 🤖

> ROS2-based action recognition system for robotic perception and human-robot interaction.

## Overview

Robotics Action Recognition System is a computer vision and robotics project focused on recognizing and classifying human actions in real time using ROS2.

The system aims to provide robots with the ability to understand human behavior through visual perception pipelines, enabling safer and more intelligent human-robot interaction scenarios.

This repository is currently under active development.

## Features

* ROS2-native architecture.
* Modular and scalable design.
* Real-time action recognition pipeline.
* Integration with robotic perception systems.
* Easy deployment on Linux-based robotic platforms.
* Designed for future integration with machine learning and deep learning models.

## Project Structure

```text
robotics-action-recognition-system/
│
├── src/                # Source code
├── build/              # ROS2 build artifacts
├── install/            # Installation artifacts
├── log/                # Execution logs 
└── ...
---------------------------------------------------
robotics-action-recognition-system/src
│
├── action_recognition/  # Nodes and requirements
├── arc_params.yaml      # HAR config. file
├── tracking_params.yaml # Tracking config. file
├── prompts/             # Prompts used for system
├── yolov8s.pt           # Selected YOLO model
└── ...
```

## Requirements

### Software

* Ubuntu 22.04 LTS (recommended)
* ROS2 Humble Hawksbill
* Python 3.10+
* OpenCV
* NumPy

### Hardware

The system is designed to run on standard Linux workstations and robotic computing platforms.

Recommended:

* Multi-core CPU
* Dedicated GPU for deep learning inference
* RGB camera or RGB-D sensor

## Installation

### Clone the repository

```bash
git clone https://github.com/Cayecaji/robotics-action-recognition-system.git
cd robotics-action-recognition-system
```

### Build the workspace

```bash
colcon build
```

### Source the workspace

```bash
source install/setup.bash
```

## Usage

Launch the action recognition pipeline:

```bash
ros2 launch action_recognition action_launch.launch.py
```

Or execute the corresponding nodes:

```bash
ros2 run action_recognition action_recognition_core.py
ros2 run action_recognition tracking_node.py
ros2 run usb_cam usb_cam_node_exe
```

## Architecture

The system follows a typical ROS2 perception pipeline:

```text
Camera Input
      │
      ▼
Frame Acquisition
      │
      ▼
Human filtering model (YOLO + ByteTrack)
      │
      ▼
Action Recognition Model
      │
      ▼
Behaviour Tree based Interaction
      │
      ▼
Robot Decision Making
```

## Future Work

* Deep learning-based action classification.
* Real-time optimization for embedded devices.
* Harder benchmarking and evaluation framework.
* Reduce latency to chase realtime interaction.

## Contributing

Contributions are welcome.

1. Fork the repository.
2. Create a feature branch.

```bash
git checkout -b feature/my-feature
```

3. Commit your changes.

```bash
git commit -m "Add new feature"
```

4. Push to your branch.

```bash
git push origin feature/my-feature
```

5. Open a Pull Request.

## License

This project is distributed under the MIT License unless stated otherwise.

## Author

**Cayecaji**

GitHub: https://github.com/Cayecaji

---

⚠️ This project is currently under active development. Features, APIs, and repository structure may change as the system evolves.
