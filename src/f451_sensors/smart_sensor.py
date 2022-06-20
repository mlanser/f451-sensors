"""
MQTT Smart temperature Sensor
"""

import time

import paho.mqtt.client as mqtt
from faker import Faker

MIN_DELAY: int = 1     # Min 1 sec delay
MAX_DELAY: int = 3600  # Max 1h delay

# let's connect to the MQTT broker
MQTT_BROKER_URL    = "mqtt.eclipseprojects.io"
MQTT_PUBLISH_TOPIC = "temperature"

mqttc = mqtt.Client()
mqttc.connect(MQTT_BROKER_URL)

# Init faker our fake data provider
fake = Faker()

# Infinite loop of fake data sent to the Broker
def run_smart_sensor(inDelay: int = 1, iterMax: int = 0) -> None:
    delay = max(min(inDelay, MAX_DELAY), MIN_DELAY)
    cntr = 0

    while cntr != iterMax:
        if iterMax:
            cntr += 1

        temperature = fake.random_int(min=0, max=30)
        mqttc.publish(MQTT_PUBLISH_TOPIC, temperature)
        print(f"Published new temperature measurement: {temperature}")
        time.sleep(delay)
