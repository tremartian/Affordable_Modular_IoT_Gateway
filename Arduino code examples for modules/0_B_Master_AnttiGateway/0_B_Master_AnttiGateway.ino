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
        Serial.println("---------Data from Buffer: " + dataFromBuffer); 

        // Parse the JSON data
        StaticJsonDocument<5256> docG;
        deserializeJson(docG, dataFromBuffer);

    }
    
    delay(5000);
    Serial.println("---------Processing data done: "+ String("xx"));
}

















