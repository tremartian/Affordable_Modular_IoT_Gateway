#include <AnttiGateway.h>
#include <NimBLEDevice.h>
#include <ArduinoJson.h>

// Define the target MAC address and I2C slave address
const char* targetMAC = "d3:6a:36:7a:fb:6f";  // Use lowercase letters
const uint8_t SLAVE_ADDRESS = 0x07;

// Initialize the I2C slave
AnttiGateway i2cSlave(SLAVE_ADDRESS);

// Define a class to handle scan callbacks with rate limiting
class ScanCallbacks : public NimBLEScanCallbacks {
public:
    ScanCallbacks() : lastTransmissionTime(0), transmissionInterval(5000) {} // 5 seconds interval

    void onResult(const NimBLEAdvertisedDevice* advertisedDevice) override { // Corrected signature
        // Check if the advertised device matches the target MAC address
        if (advertisedDevice->getAddress().toString() == targetMAC) {
            unsigned long currentTime = millis();
            if (currentTime - lastTransmissionTime >= transmissionInterval) {
                Serial.printf("RuuviTag found: %s\n", advertisedDevice->getAddress().toString().c_str());

                // Extract manufacturer-specific data
                std::string data = advertisedDevice->getManufacturerData();
                Serial.printf("Manufacturer Data: ");
                for (size_t i = 0; i < data.length(); i++) {
                    Serial.printf("%02X ", (uint8_t)data[i]);
                }
                Serial.println();

                // Parse Ruuvi RAWv2 data
                if (data.length() >= 8) { // Ensure data is long enough
                    uint8_t* payload = (uint8_t*)data.data();
                    if (payload[0] == 0x99 && payload[1] == 0x04) { // Ruuvi Manufacturer ID and RAWv2 format
                        parseRuuviRawV2(payload, data.length());
                        lastTransmissionTime = currentTime;
                    } else {
                        Serial.println("Unknown or unsupported data format.");
                    }
                }
            }
        }
    }

private:
    unsigned long lastTransmissionTime;
    const unsigned long transmissionInterval; // Minimum interval between transmissions in milliseconds

    void parseRuuviRawV2(uint8_t* data, size_t length) {
        // Ensure it's the RAWv2 format
        if (length < 8) {
            Serial.println("Incomplete RAWv2 data.");
            return;
        }

        // Extract temperature, humidity, and pressure
        float temperature = ((int16_t)(data[3] << 8 | data[4])) * 0.005;
        float humidity = (data[5] * 0.5);
        float pressure = ((uint16_t)(data[6] << 8 | data[7])) + 50000;

        // Print the parsed data
        Serial.printf("Temperature: %.2f°C\n", temperature);
        Serial.printf("Humidity: %.2f%%\n", humidity);
        Serial.printf("Pressure: %.2f hPa\n", pressure / 100.0);

        // Create a JSON document to structure the data
        StaticJsonDocument<200> doc;
        doc["sensor_id"]     = targetMAC;
        doc["temperature"]   = temperature;
        doc["humidity"]      = humidity;
        doc["pressure"]      = pressure / 100.0; // Convert to hPa

        // Serialize JSON to a string
        String output;
        serializeJson(doc, output);

        // Send the data via I2C
        i2cSlave.addToRingBuffer(output);
        Serial.printf("Sent data via I2C: %s\n", output.c_str());
    }
} scanCallbacks;

void setup() {
    Serial.begin(115200);
    while (!Serial) {
        // Wait for Serial to be ready (necessary for some boards)
    }

    i2cSlave.initSlave();
    Serial.println("Affordable Modular IoT Gateway for IoT-Sensor Data Collection");
    Serial.println("I2C Slave Initialized");

    // Initialize NimBLE
    NimBLEDevice::init("RuuviTag-Scanner");

    // Create the BLE scan object
    NimBLEScan* pScan = NimBLEDevice::getScan();
    pScan->setScanCallbacks(&scanCallbacks, false);
    pScan->setInterval(100);  // Scan interval in milliseconds
    pScan->setWindow(100);    // Scan window in milliseconds
    pScan->setActiveScan(true); // Active scan to get more data
    pScan->start(0); // Start scanning indefinitely until manually stopped

    Serial.println("Scanning for RuuviTag...");
}

void loop() {
    // No need to handle scanning in loop since it's managed by NimBLE callbacks
    // Add a delay to prevent the loop from running too frequently
    delay(1000);
}
