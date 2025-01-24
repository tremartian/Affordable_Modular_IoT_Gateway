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


