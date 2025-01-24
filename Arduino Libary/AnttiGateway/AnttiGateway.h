//#ifndef I2CCOMMUNICATION_HntSize ntSize 
//#define I2CCOMMUNICATION_H

#ifndef ANTTIGATEWAY_HntSize ntSize 
#define ANTTIGATEWAY_H

#include <Arduino.h>
#include <Wire.h>
#include <vector>
#include "RingBuffer.h" // Include the RingBuffer class
#include "SimpleQueue.h" // Include the SimpleQueue class
#pragma once

// Configuration values, they are compile-time constants.
//constexpr size_t I2CRequestBufferSize = 128; // I2C request buffer size
constexpr size_t RingBufferSize = 10; // Ring buffer size (was 500 and worked ok)
constexpr size_t SimpleQueueSize = 500; // oli: Queue size --------------------------------------------------
constexpr size_t JsonDocumentSize = 1500; // JSON document size (max? )
//constexpr size_t MaxChunks = 100; // Assuming a maximum of 100 chunks
constexpr size_t MaxChunkSizeSlave = 64; // Maximum size of each chunk to send (Slave) 
constexpr size_t MaxChunkSize = 128; // Maximum size of each chunk to request (Master) needs to be bigger than the above
static constexpr int MaxDataSize = 5000; // Adjust as needed (completeData)

class AnttiGateway {
public:

    std::vector<uint8_t> slaveAddresses; // List of slave device addresses

    static void universalReset(); // for slave when Master requests data

    uint8_t _laskuri = 0;

    static bool statusOfI2CResponse();
    void disableI2CResponse();
    void enableI2CResponse();
    static bool _i2cResponseEnabled;
    
    

    AnttiGateway(); // Default constructor for master mode
    explicit AnttiGateway(uint8_t deviceAddress); // Constructor for slave mode

    
    void setDeviceAddress(uint8_t deviceAddress);
    void initMaster(uint32_t clockFrequency = 100000); // Default I2C clock is 100 kHz
    void initSlave();
    static void requestEvent(); // for slave when Master requests data
    static void receiveEvent(int len); // for slave when Master sends data
    //static void scanI2CBus(std::vector<uint8_t>& deviceAddresses);
    static uint8_t scanI2CBus(std::vector<uint8_t>& deviceAddresses); // Method to scan the I2C bus
    String receiveData(); // Function to receive data
    static bool isDataSetComplete();
    static void resetDataSetComplete();
    static String getCompleteDataSet();
    static bool _isDataSetComplete;
 
    // Ring buffer related methods
    void addToRingBuffer(const String& data);
    String getFromRingBuffer(); // 
    void addCompleteDataToRingBuffer(); 
    // Ring buffer instance
    static RingBuffer<String, RingBufferSize> ringBuffer; // Example size, adjust as needed

    // Simple queue related methods
    void prepareData(const String& jsonData); // Prepare complete data for transmission
    String getNextChunk(); // Get the next chunk to send
    bool hasMoreChunks(); // Check if there are more chunks to send
    //static SimpleQueue chunkQueue; // Queue to store data chunks
    static void breakDataIntoChunks(const String& data); // Break data into smaller chunks
    static SimpleQueue<String, SimpleQueueSize> simpleQueue; // Example size, adjust as needed
    



private:
    uint8_t _deviceAddress = 0;

    static char completeData[MaxDataSize]; // Array to store complete data

    void processReceivedChunk(const String& chunk);  // not static anymore
    static int getChunkNumber(const String& chunk);
    static int getTotalChunks(const String& chunk);
    static String getChunkData(const String& chunk);





};

#endif // ANTTIGATEWAY_H
