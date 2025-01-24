ADDITIONAL_INFO = {
    "intro": """
The Affordable Modular IoT Gateway is a flexible solution designed to enable seamless communication between diverse IoT sensors and cloud platforms. Its modular architecture consists of:

- **Module A (Slave):** Interfaces with sensors, collects data, and prepares it for transmission using technologies such as Bluetooth, Wi-Fi, and others.
- **Module B (Master):** Processes and forwards data to cloud platforms or endpoints using LoRaWAN, Wi-Fi, or other communication technologies.

Inter-module communication is facilitated via an **I2C bus** using **JSON** as the standard data format. A **ring buffer** in Module B ensures reliable data handling during periods of delayed transmission, making the system adaptable for a wide range of IoT scenarios.
    """,
    "module_a": """
Module A (Slave) is responsible for data acquisition and preparation. Its core functionalities include:

1. **Sensor Integration:** Supports various sensors via Bluetooth, Wi-Fi, or other technologies.
2. **Data Formatting:** Converts sensor data into a standardized JSON format for compatibility with Module B.
3. **I2C Communication:** Sends the formatted data to Module B over the I2C bus.

To customize Module A, focus on the `createJsonData()` function, which handles JSON formatting for specific sensors. This function can be tailored to support diverse sensor types and data structures.

**Note:** If any sensor readings are unavailable, Module A should not send incomplete or nonexistent values via the I2C bus to Module B.
    """,
    "module_b": """
Module B (Master) manages data reception, processing, and transmission. Its primary responsibilities are:

1. **Data Reception:** Receives JSON data from Module A over the I2C bus.
2. **Data Validation and Storage:** Validates incoming data and stores it in a ring buffer to ensure reliability during delayed transmissions.
3. **Data Forwarding:** Sends data to cloud platforms or endpoints using technologies such as LoRaWAN, Wi-Fi, or Bluetooth.

To adapt Module B, modify the `forwardData()` function to implement specific transmission protocols or endpoint requirements.

**Note:** Module B should avoid transmitting incomplete or nonexistent values to a database or endpoint if certain sensor readings are unavailable in the incoming data from Module A.
    """,
    "both_modules": """
The Affordable Modular IoT Gateway leverages a modular architecture for seamless collaboration between its two core modules:

- **Module A (Slave):** Interfaces with sensors, collects data, and transmits it as a JSON structure to Module B.
- **Module B (Master):** Receives, processes, and transmits the data to designated endpoints using the selected communication technology.

This modular design supports scalability and flexibility, enabling the system to handle diverse IoT applications. JSON ensures compatibility, while the I2C bus facilitates efficient inter-module communication.

**Note:** Both modules should implement mechanisms to exclude incomplete or unavailable sensor readings to ensure data integrity and prevent invalid transmissions.
    """,
    "data_format": """
A well-defined data format is critical for effective communication between Module A and Module B. JSON is used as the standard format, offering readability, scalability, and support for hierarchical data structures.

### Example JSON Format:
{{ "sensor_id": "string", "timestamp": "ISO-8601", "temperature": "float" }}

- `sensor_id`: Unique identifier for the sensor.
- `timestamp`: Time the data was collected, in ISO-8601 format.
- `temperature`: Sensor reading (e.g., temperature value).

When defining a data format, ensure it meets the requirements of both the sensor and the endpoint. A well-structured format enhances system reliability and simplifies integration with IoT platforms.

**Note:** The data format should account for missing values by omitting unavailable fields, ensuring that only valid data is transmitted and stored.
    """
}


ADDITIONAL_INFO_CODE_MODULE_A = {
    "description": """
Module A is responsible for interfacing with sensors, collecting data, and transmitting it to Module B using JSON over the I2C bus. Below is an example implementation of Module A in Arduino, which includes sensor integration, data formatting, and I2C communication.
""",
    "example": """
```cpp
// Module A - Slave: Responsible for collecting data from different sensors or sources. It can interface with technologies like Bluetooth, Wi-Fi, and others.

/*
In Slave the I2C requests are handled as callbacks (interrupts)

*/

#include "AnttiGateway.h"
#include <ArduinoJson.h>

const uint8_t SLAVE_ADDRESS = 0x07;
AnttiGateway i2cSlave(SLAVE_ADDRESS);


void setup() {
    Serial.begin(115200);
    i2cSlave.initSlave();
    Serial.println("Affordable Modular IoT Gateway for IoT-Sensor Data Collection (AnttiGateway)");
    Serial.println("Slave - 22.4.2024");
    Serial.println("I2C Slave Initialized");
    Serial.println("--------------------------------------------------------------------\n");

    delay(2000); // time for master to find the I2C device before Bluetooth interrupts fille the operation
}

int loopcounter = -1;
int LastTimeSinceDataReceivedcounter = -1;  // counter is reseted under addToRingBufferInPieces


void loop() {
    loopcounter++;

    String sensorData = "{temp:" +String(loopcounter)+  "}"; // Data must be in JSON format!
    i2cSlave.addToRingBuffer(sensorData);  // save data to ring buffer

    delay(5000); // Delay for 10 seconds
}

"""
}

ADDITIONAL_INFO_CODE_MODULE_B = {
    "description": """
Module B handles receiving data from Module A, processing it, and forwarding it to cloud platforms or other endpoints using wireless technologies. Below is an example implementation for Module B in Arduino, which includes data reception, processing, and transmission.
""",
    "example": """
```cpp
// Module B – Master: Handles the forwarding of data to various endpoints like cloud databases (Google Firebase, Losant IoT, etc.), using technologies like LoRaWAN, Wi-Fi, and more.
// use Wireless Stick Lite / Wireless Shell


#include "AnttiGateway.h"
#include <ArduinoJson.h>
AnttiGateway i2cMaster; // Create an instance of the AnttiGateway class

int transmitFrequency = 2000;  // 


void setup() {
    Serial.begin(115200); // Start serial communication
    i2cMaster.initMaster(); // Initialize the master module

    Serial.println("Affordable Modular IoT Gateway for IoT-Sensor Data Collection (AnttiGateway)");
    Serial.println("Master - 22.4.2024");
    Serial.println("transmitFrequency: "+ String(transmitFrequency/1000)+" seconds");
    Serial.println(" ------------------------------------------------------------------\n");

    // check if specific number of slaves is found.. if not. reboot 
    uint8_t foundSlaves  = i2cMaster.slaveAddresses.size();
    if (foundSlaves < 1) {  
      Serial.println("Expected number of slaves not found. Rebooting...");
      delay(2000);
      ESP.restart();
    }

    // do not remove any code above this. add required for setup code after this
    delay(500); 
 
    Serial.println(" ------------------------------------------------------------------\n");
    delay(500); 

}

// Usually no need to make changes to loop function
void loop() {
    delay(transmitFrequency); // Main Loop Delay (how often requests data from slave) <===================================================================      

    // Randomize the order of slave addresses
    uint8_t addr = i2cMaster.slaveAddresses[random(0, i2cMaster.slaveAddresses.size())]; // Get a random address from the list
    Serial.println("addr: 0x"+String(addr, HEX));
    i2cMaster.setDeviceAddress(addr); // Set the slave device address

    // requests several rounds to make sure that it receives consequtive chunks   
    while (!i2cMaster.isDataSetComplete()) {
      Serial.println("      ============ > request chunks: ");
      int timer = millis();
      String receivedChunk = i2cMaster.receiveData(); // This is the main function that calls the library and Request data from slave via I2C
      if (timer > 2*60*1000) {
        Serial.println("I2C device does not respond! restarting");
        ESP.restart();
      }

      if (!AnttiGateway::ringBuffer.isEmpty()) {
        Serial.println("Data found in ring buffer!");
        break; // if data in buffer exist => exit for loop (the i2cMaster.receiveData() saves only complete json to buffer )
      }
      delay(1000); // Delay 
    }
    
    Serial.println("============= START Routing data ============="); 
    delay(5000); // Main Loop Delay (how often requests data from slave)
    forwardData(); //<------------------------------------------ data processed on loop
}

// This function can be modified for various tasks for example forwarding the data to a database via LoRaWAN, Wi-Fi or some other technology
void forwardData() {
    Serial.println("---------Processing data start: "+ String("xx"));
    
    String dataFromBuffer = i2cMaster.getFromRingBuffer(); // Check and process complete data sets from the ring buffer. Do not modify this
    if (!dataFromBuffer.isEmpty()) {
        Serial.println("---------Data from Buffer: " + dataFromBuffer); // 

        // Parse the JSON data
        StaticJsonDocument<5256> docG;
        deserializeJson(docG, dataFromBuffer);

    }
    
    delay(5000);
    Serial.println("---------Processing data done: "+ String("xx"));
}
"""
}


