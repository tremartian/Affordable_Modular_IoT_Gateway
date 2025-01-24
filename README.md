# Affordable_Modular_IoT_Gateway
Affordable Modular IoT Gateway for IoT-Sensor Data Collection and a Large Language Model-powered programming tool 

This repository contains the source code and documentation for the Affordable Modular IoT Gateway, a flexible and modular gateway architecture that simplifies the development and prototyping of IoT systems. The gateway is designed to interface with various wireless technologies, sensors, and cloud platforms, enabling accelerated IoT implementations and promoting innovative research and development.

# Features
- Modular gateway architecture based on Arduino-compatible microcontroller development boards
- Can be configured to support various wireless technologies, such as Wi-Fi, Bluetooth, LoRa, ZigBee, and Z-wave
- Compatible with different cloud platforms, like Google Firebase and Losant IoT
- Implements a JSON-based communication structure between modules for efficient data handling
- Incorporates a ring buffer in Module B to enhance data transfer performance and prevent data loss or mixing

# Structure
The gateway comprises two types of microcontroller modules, referred to as Module A (Receiver) and Module B (Transmitter). Module A focuses on receiving data from various sensors, translating it into a standardized format, and sending it to Module B. Module B acts as a router towards the endpoint, transforming the received data for the endpoint, and establishing physical connectivity.

![image](https://user-images.githubusercontent.com/49767803/234206827-64d36386-4ec2-4de8-9a2c-b62162c70e27.png)

The I2C bus is used as the communication protocol between the modules, with Module B serving as the master and Module A as the slave. The ArduinoJson library is employed to work with JSON within the Arduino environment, which enables a clear structure for data transfers.

# Implementation
The Affordable Modular IoT Gateway has been tested using various wireless technologies, data sources, and endpoints, employing different development boards to support diverse wireless technologies. Example implementations for Module A and Module B showcase the versatility and adaptability of the proposed gateway architecture.

![image](https://user-images.githubusercontent.com/49767803/234206661-8629095c-5fdf-40fa-9fad-98732207f967.png)

# Getting Started
Please refer to the documentation provided in this repository for detailed information on the hardware and software requirements, setup instructions, and example implementations. The templates for Module A and Module B are a good strating point.

# License
This project is open-source and available under the MIT License.

# Contributing
We welcome contributions from the community. If you'd like to contribute to this project, please follow the standard GitHub workflow: fork the repository, make your changes, and submit a pull request. For major changes, please open an issue first to discuss your proposed changes.

# Support
If you encounter any issues or have questions regarding the implementation of the Affordable Modular IoT Gateway, feel free to open an issue on this repository.





