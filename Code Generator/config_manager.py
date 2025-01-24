import json
import os

CONFIG_FILE = "config.json"

def load_config():
    """Load the configuration file."""
    if not os.path.exists(CONFIG_FILE):
        return {
            "boards": ["ESP32 Firebeetle", "Heltec LoRa", "Arduino Uno"],
            "technologies": {
                "Bluetooth": "Provide BLE Device MAC address and supported services.",
                "LoRaWAN": "Include frequency band and credentials for the gateway.",
                "Wi-Fi": "Provide SSID, password, and endpoint URL."
            },
            "models": {
                "gpt-3.5-turbo": {
                    "key": "your_api_key_for_gpt_3.5_turbo",
                    "description": "General-purpose ChatGPT model."
                },
                "gpt-4": {
                    "key": "your_api_key_for_gpt_4",
                    "description": "Advanced ChatGPT model with better reasoning capabilities."
                }
            }
        }
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_config(config):
    """Save the configuration file."""
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)
