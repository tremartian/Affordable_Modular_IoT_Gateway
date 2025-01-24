#ifndef RINGBUFFER_H
#define RINGBUFFER_H

/*
data can be retrieved from the ring buffer while new data is being written, 
as long as the data being read is not the same as the data being written. 
The ring buffer is designed to handle such concurrent operations, 
making it suitable for applications where data needs to be read and written simultaneously,
like in this case with I2C communication.
*/

// RingBuffer class definition
template <typename T, size_t bufferSize>
class RingBuffer {
public:
    void push(const T& item) {
        if (isFull()) {
            // Handle buffer overflow here, e.g., overwrite old data or simply return.
            // For this example, let's just return.
            return;
        }
        buffer[tail] = item;
        tail = (tail + 1) % bufferSize;
    }

    T pop() {
        if (isEmpty()) {
            // Handle buffer underflow here, e.g., return a default value.
            return T(); // Return default-constructed object.
        }
        T item = buffer[head];
        head = (head + 1) % bufferSize;
        return item; // returns the oldest data from the buffer
    }

    bool isEmpty() const {
        return head == tail;
    }

    bool isFull() const {
        return (tail + 1) % bufferSize == head;
    }

    void startWrite() {
        isWriting = true;
    }

    void endWrite() {
        isWriting = false;
    }

    bool isWritingToBuffer() const {
        return isWriting;
    }

    size_t getSize() const {
        if (tail >= head) {
            return tail - head;
        } else {
            return bufferSize - (head - tail);
        }
    }

private:
    T buffer[bufferSize];
    size_t head = 0;
    size_t tail = 0;
    volatile bool isWriting = false; // Flag to indicate buffer is being written to
};


#endif // RINGBUFFER_H