#include <WiFi.h>
#include <ArduinoJson.h>
#include "AnttiGateway.h"

AnttiGateway i2cMaster;

const char* ssid = "xxx";
const char* password = "xxx";
const char* endpoint = "xxx";

void setup() {
    Serial.begin(115200);
    i2cMaster.initMaster();

    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(1000);
        Serial.println("Connecting to WiFi...");
    }
    Serial.println("Connected to WiFi");
}

void loop() {
    delay(2000);

    uint8_t addr = i2cMaster.slaveAddresses[random(0, i2cMaster.slaveAddresses.size())];
    i2cMaster.setDeviceAddress(addr);

    while (!i2cMaster.isDataSetComplete()) {
        String receivedChunk = i2cMaster.receiveData();
        if (!AnttiGateway::ringBuffer.isEmpty()) {
            break;
        }
        delay(1000);
    }

    forwardData();
}

void forwardData() {
    String dataFromBuffer = i2cMaster.getFromRingBuffer();
    if (!dataFromBuffer.isEmpty()) {
        StaticJsonDocument<256> doc;
        DeserializationError error = deserializeJson(doc, dataFromBuffer);

        if (!error) {
            String jsonString;
            serializeJson(doc, jsonString);
            sendDataToEndpoint(jsonString);
            Serial.println("Data forwarded successfully.");
        } else {
            Serial.println("JSON deserialization failed.");
        }
    }
}

void sendDataToEndpoint(String jsonData) {
    if (WiFi.status() == WL_CONNECTED) {
        WiFiClient client;
        if (client.connect("moi.rd.tuni.fi", 1880)) {
            client.println("POST /xxx HTTP/1.1");
            client.println("Host: xxx");
            client.println("Content-Type: application/json");
            client.println("Connection: close");
            client.print("Content-Length: ");
            client.println(jsonData.length());
            client.println();
            client.println(jsonData);
            client.stop();
        } else {
            Serial.println("Connection to endpoint failed.");
        }
    } else {
        Serial.println("WiFi not connected.");
    }
}