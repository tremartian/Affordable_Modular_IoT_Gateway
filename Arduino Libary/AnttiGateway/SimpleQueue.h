// SimpleQueue.h - Custom queue implementation
#ifndef SIMPLEQUEUE_H
#define SIMPLEQUEUE_H

#include <Arduino.h>

template <typename T, unsigned int Capacity>
class SimpleQueue {
public:
    SimpleQueue() : front_(0), rear_(0), size_(0) {}

    bool empty() const {
        return size_ == 0;
    }

    bool full() const {
        return size_ == Capacity;
    }

    bool push(const T &value) {
        if (!full()) {
            data_[rear_] = value;
            rear_ = (rear_ + 1) % Capacity;
            size_++;
            return true;
        }
        return false; // Queue is full
    }

    bool pop(T &value) {
        if (!empty()) {
            value = data_[front_];
            front_ = (front_ + 1) % Capacity;
            size_--;
            return true;
        }
        return false; // Queue is empty
    }

    unsigned int getSize() const {
        return size_;
    }



    

private:
    T data_[Capacity];
    unsigned int front_;
    unsigned int rear_;
    unsigned int size_;
};

#endif // SIMPLEQUEUE_H
