
#include "AnttiGateway.h"
#include <ArduinoJson.h>



// Static member initialization
char AnttiGateway::completeData[MaxDataSize];
bool AnttiGateway::_isDataSetComplete = false;
RingBuffer<String, RingBufferSize> AnttiGateway::ringBuffer; // Define the static member variable
SimpleQueue<String, SimpleQueueSize> AnttiGateway::simpleQueue; // Define the static member variable

AnttiGateway instance;  // Create an instance of the class

// Define the static queue with a size of your choice
//SimpleQueue AnttiGateway::chunkQueue(QueueSize); // Adjust the size as needed

bool AnttiGateway::_i2cResponseEnabled = true;

AnttiGateway::AnttiGateway() {}

AnttiGateway::AnttiGateway(uint8_t deviceAddress) {
    _deviceAddress = deviceAddress;
}

void AnttiGateway::setDeviceAddress(uint8_t deviceAddress) {
    _deviceAddress = deviceAddress;
}

void AnttiGateway::initMaster(uint32_t clockFrequency) {
    delay(100); 
    Wire.begin(); // Start I2C as master
    Wire.setClock(clockFrequency);
    Serial.println("\n ------------------------------------------------------------------");
    Serial.println("Master device initialized");
    // added more to init
    scanI2CBus(slaveAddresses); // Populate the slaveAddresses vector by scanning the I2C bus
    Serial.println("Detected I2C Devices:");
    for (uint8_t addr : slaveAddresses) {
        Serial.print("0x");
        Serial.println(addr, HEX);
    }
    delay(100); 


}

// Initialize as I2C slave
void AnttiGateway::initSlave() {
    Serial.println("\n ------------------------------------------------------------------");
    Wire.begin(_deviceAddress);
    Serial.println("I2C Slave Initialized 1");
    delay(1000);
    Wire.onReceive(receiveEvent);  // when Master sends data
    Serial.println("I2C Slave Initialized 2");
    Wire.onRequest(requestEvent);  // when Master requests data
    Serial.println("I2C Slave Initialized 3");
}





// Modify scanI2CBus to return the number of detected devices
uint8_t AnttiGateway::scanI2CBus(std::vector<uint8_t>& deviceAddresses) {
    deviceAddresses.clear();
    uint8_t count = 0; // Count of detected devices
    for (uint8_t address = 1; address < 127; address++) {
        Wire.beginTransmission(address);
        if (Wire.endTransmission() == 0) {
            deviceAddresses.push_back(address);
            count++;
        }
    }
    return count;
}

// function that is called from loop
String AnttiGateway::receiveData() {
    String receivedData = "";
    Wire.requestFrom(static_cast<int>(_deviceAddress), MaxChunkSize); // request longer chunks 
    while (Wire.available()) {
        char c = Wire.read();
        if (c == '\n') {
            processReceivedChunk(receivedData);  // calls the most important function
            //Serial.println("receivedData:"+ receivedData);
            receivedData = "";
        } else {
            receivedData += c;
        }
    }
    return receivedData;
}

//----------------- CHUNK Master----------------

void AnttiGateway::processReceivedChunk(const String& chunk) {
    static int lastChunkNumber = -1; // Tracks the last received chunk number

    int chunkNumber = getChunkNumber(chunk);
    int currentTotalChunks = getTotalChunks(chunk);
    String data = getChunkData(chunk);

    Serial.println("cn:" + String(chunkNumber) + " tc:" + String(currentTotalChunks) + " data:" + data);

    // Check for consecutive order
    if (chunkNumber != lastChunkNumber + 1) {
        Serial.println("\n                   Error: Non-consecutive chunk received \n");
        delay(10000);
        // Handle error
    }

    lastChunkNumber = chunkNumber;

    // Append directly to completeData if within bounds
    if ((strlen(completeData) + data.length()) < sizeof(completeData)) {
        strncat(completeData, data.c_str(), sizeof(completeData) - strlen(completeData) - 1);
    } else {
        Serial.println("\n                   Error: completeData buffer overflow \n");
        delay(10000);
        // Handle buffer overflow
    }

    // Check if dataset is complete
    if (chunkNumber == currentTotalChunks) {
        _isDataSetComplete = true;
        Serial.println("Complete Data Set Received:");
        Serial.println(completeData);
        addCompleteDataToRingBuffer();  // Add data to the ring buffer
        memset(completeData, 0, sizeof(completeData)); // Clear the completeData array
        lastChunkNumber = -1; // Resets the last received chunk number
    }
}


// returns the status of _isDataSetComplete
bool AnttiGateway::isDataSetComplete() {
    return _isDataSetComplete;
}

// resets the status of _isDataSetComplete
void AnttiGateway::resetDataSetComplete() {
    _isDataSetComplete = false;
}

// possibly useless function
String AnttiGateway::getCompleteDataSet() {
    return String(completeData);
}

// Functions to read cn, tc and data from received json chunks

int AnttiGateway::getChunkNumber(const String& chunk) {
    StaticJsonDocument<JsonDocumentSize> doc;
    if (deserializeJson(doc, chunk.c_str()) == DeserializationError::Ok) {
        return doc["cn"];
    }
    return -1;
}

int AnttiGateway::getTotalChunks(const String& chunk) {
    StaticJsonDocument<JsonDocumentSize> doc;
    if (deserializeJson(doc, chunk) == DeserializationError::Ok) {
        return doc["tc"];
    }
    return -1;
}

String AnttiGateway::getChunkData(const String& chunk) {
    StaticJsonDocument<JsonDocumentSize> doc;
    if (deserializeJson(doc, chunk) == DeserializationError::Ok) {
        return doc["data"].as<String>();
    }
    return "";
}

// ------------------------------------------- RING BUFFER ------------------

/*
The function first checks if the complete dataset is ready and the ring buffer is not currently being written to.
It then validates if the completeData is in JSON format using the ArduinoJson library. If it's not valid JSON, the function prints an error message and exits without adding the data to the buffer.
If the ring buffer is full, the oldest data is removed before adding new data. This ensures that the buffer never overflows and always has space for new data.
Finally, the validated and processed data is added to the ring buffer, and the _isDataSetComplete flag is reset.
This approach ensures that only valid JSON data is added to the buffer and manages the buffer capacity effectively.
*/
// this function is used by MASTER
void AnttiGateway::addCompleteDataToRingBuffer() {
    // Check if there is complete data and the buffer is not in a write operation
    if (_isDataSetComplete && !AnttiGateway::ringBuffer.isWritingToBuffer()) {
        // Validate JSON format before adding to the buffer
        size_t dataSize = strlen(completeData);
        //Serial.println("dataSize: "+String(dataSize));
        Serial.println("addCompleteDataToRingBuffer(): "+String(completeData));
              
        // check if valid json
        if (completeData[0] == '{' && completeData[dataSize - 1] == '}') {
            // JSON is valid
        } else {
            Serial.println("\nError: Invalid JSON format. Data not added to buffer.\n");
            _isDataSetComplete = false; // Reset the flag after tried adding to the buffer ------------------------------------------------- 15.1 added
            return; // exit the addCompleteDataToRingBuffer() function adding data to buffer
        }

        // Check if buffer is full, and manage it accordingly
        if (AnttiGateway::ringBuffer.isFull()) {
            // Optionally, handle full buffer scenario (e.g., log the event, notify, etc.)
            Serial.println("\n                   Notice: Ring buffer is full. Overwriting oldest data.\n");
            AnttiGateway::ringBuffer.pop(); // Remove the oldest data
        }

        // Add data to the buffer
        //Serial.println("addCompleteDataToRingBuffer() function called: "+ String(completeData));
        AnttiGateway::ringBuffer.push(String(completeData)); // Convert char array to String and push to buffer
        _isDataSetComplete = false; // Reset the flag after adding to the buffer ------------------------------------------------- 15.1 uncommented
    }
}



// this function is used by SLAVE 
void AnttiGateway::addToRingBuffer(const String& data) {

    if (data != "") {  // check if there is data add
      // Add slave address to json before it is stored to buffer
      StaticJsonDocument<JsonDocumentSize+100> docA;
      deserializeJson(docA, data); // Parse the JSON data
      docA["SlaveID"] = _deviceAddress; // Add the _deviceAddress to the JSON object
      String modifiedData;
      serializeJson(docA, modifiedData);
      Serial.println("AnttiGateway::addToRingBuffer -> data: "+ String(modifiedData));

      if (!AnttiGateway::ringBuffer.isFull()) {
        AnttiGateway::ringBuffer.push(modifiedData);
      } else {
        // Handle buffer full scenario, e.g., overwrite oldest data
        Serial.println("\n                   Notice: Ring buffer is full. Overwriting oldest data.\n");
        AnttiGateway::ringBuffer.pop(); // Remove the oldest data
        AnttiGateway::ringBuffer.push(modifiedData); // Add new data
      }
    }



}

String AnttiGateway::getFromRingBuffer() {
      if (!AnttiGateway::ringBuffer.isEmpty()) {
          return AnttiGateway::ringBuffer.pop();
      }
      return ""; // Return empty string if buffer is empty
}



// --------- Chunks slave---------------

void AnttiGateway::receiveEvent(int len){
  Serial.println("receiveEvent");
  /*Serial.printf("onReceive[%d]: ", len);
  while(Wire.available()){
    Serial.write(Wire.read());
  }
  Serial.println();
  */
}

// returns the status of _i2cResponseEnabled
bool AnttiGateway::statusOfI2CResponse() {
    return _i2cResponseEnabled;
}

void AnttiGateway::disableI2CResponse() {
    _i2cResponseEnabled = false;
}

void AnttiGateway::enableI2CResponse() {
    _i2cResponseEnabled = true;
}

// When Masters requests data
void AnttiGateway::requestEvent() {
    Serial.print("."); // For testing, print the JSON data
    instance._laskuri ++;
    Serial.print("_laskuri: " + String( instance._laskuri ));
    if (!_i2cResponseEnabled) { // if false
        Serial.println("       Do not respond to I2C requests if disabled");
        return;  // Do not respond to I2C requests if disabled
    }
    _i2cResponseEnabled = false;
    
    // Get the current size of the SimpleQueue
    unsigned int simpleQueueSize = simpleQueue.getSize();
    Serial.println(" currentSize: " + String(simpleQueueSize) ); 
    Serial.println(" RingBufferSize: " + String(ringBuffer.getSize()) ); 
    

    /*
    for (int i = 0; i <= 20; i++) {
        String chunkki = instance.getNextChunk();
        Serial.println(" chunkki: " + String(chunkki) ); 
        delay(10);
        }
    */
        
    // if chunkqueue empty => fill the queue => data is taken from the buffer
    if (simpleQueueSize == 0) {
      Serial.println("no chunks -> add more chunks to simpleQueue");

      // test to fill the dataFromBuffer with some data -> should be replaced with real data from buffer
      StaticJsonDocument<256> docR;
      docR["SlaveHello"] = "requestEvent()"; // Add the receivedDataID to the JSON object
      String dataFromBuffer1 = ""; // empty the string before JSON is added
      serializeJson(docR, dataFromBuffer1); // Serialize the JSON object back to string
      // test to fill the dataFromBuffer with some data -> should be replaced with real data from buffer
   
      String dataFromBuffer = AnttiGateway::ringBuffer.pop();
      //Serial.println("\n          ===========================requestEvent()==== dataFromBuffer: " + String(dataFromBuffer) +"\n" );
      //Serial.println("dataFromBuffer.length(): " + String( dataFromBuffer.length() ) );

      breakDataIntoChunks(dataFromBuffer); // divides data into chunk and pushes chunks to chunkQueue
    }

    Serial.println(" simpleQueueSize2: " + String(simpleQueue.getSize()) ); 


    if (simpleQueueSize > 0) {
        String chunk = instance.getNextChunk();  // gets next chunk from chunkQueue
        Serial.println("\n I2C call from Master -> Write chunk to I2C bus -> chunk:"+chunk); // For testing, print the JSON data
        Wire.write((const uint8_t*)chunk.c_str(), chunk.length());
    }
    _i2cResponseEnabled = true;
}



void AnttiGateway::breakDataIntoChunks(const String& data) {
    Serial.println("breakDataIntoChunks function called");
    size_t start = 0;
    size_t chunkNumber = 0;
    size_t totalChunks = (data.length() / MaxChunkSizeSlave);

    while (start < data.length()) {
        Serial.print(chunkNumber);
        size_t chunkSize = std::min(MaxChunkSizeSlave, data.length() - start);
        String chunk = data.substring(start, start + chunkSize);
        Serial.println(" chunk:" + String(chunk) );
        
        StaticJsonDocument<JsonDocumentSize> chunkDoc;
        chunkDoc["cn"] = chunkNumber; // Shortened key for chunk number
        chunkDoc["tc"] = totalChunks; // Shortened key for total chunks
        chunkDoc["data"] = chunk;

        String chunkJson;
        serializeJson(chunkDoc, chunkJson);
        
        chunkJson += "\n";  // add sign to show that this is where chunks ends

        simpleQueue.push(chunkJson); // Chunks are added to simpleQueue

        start += chunkSize;
        chunkNumber++;
    }
 }

String AnttiGateway::getNextChunk() {
    String chunk;
        if (simpleQueue.pop(chunk)) { // Use the custom queue to pop chunks
            return chunk;
        }
        return "";
    }

bool AnttiGateway::hasMoreChunks() {
    return !simpleQueue.empty();
}
