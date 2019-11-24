#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import configparser
import paho.mqtt.client as mqtt
import json
import io
import random  # for random answer forms
from weather import Weather

CONFIGURATION_ENCODING_FORMAT = "utf-8"
CONFIG_INI = "config.ini"

# define HOST and PORT
HOST = 'localhost'
PORT = 1883


class SnipsConfigParser(configparser.ConfigParser):
    def to_dict(self):
        return {section: {option_name: option for option_name, option in self.items(section)} for section in self.sections()}


def read_configuration_file(configuration_file):
    try:
        with io.open(configuration_file, encoding=CONFIGURATION_ENCODING_FORMAT) as f:
            conf_parser = SnipsConfigParser()
            conf_parser.read_file(f)
            return conf_parser.to_dict()
    except (IOError, configparser.Error):
        return dict()


# The callback for when the client receives a CONNECT response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))

    # Subscribe to hotword topic
    client.subscribe("hermes/hotword/default/detected")
    # Subscribe to intent topic
    client.subscribe("hermes/intent/#")


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload.decode()))
    payload = json.loads(msg.payload.decode())
    if msg.topic == 'hermes/hotword/default/detected':
        print("Wakeword detected!")
    else:
        try:
            intent = msg.topic[(
                (len(msg.topic) - msg.topic.index(":")) - 1) * -1:]
            print("Intent "+intent+" found.")
            if intent in actions:
                print("Running intent...")
                response = {"sessionId": str(payload["sessionId"]),
                            "text": str(actions[intent](msg.payload))}
                client.publish(
                    "hermes/dialogueManager/endSession", json.dumps(response))
        except:
            e = sys.exc_info()[0]
            print("Error while trying to invoke intent from topic '"+msg.topic+"': "+e)


def on_publish(client, userdata, result):  # create function for callback
    print("data published \n")
    pass


if __name__ == "__main__":
    conf = read_configuration_file(CONFIG_INI)
    weather = Weather(conf)
    actions = {"searchWeatherForecast":  weather.forecast}

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_publish = on_publish

    client.connect(HOST, PORT, 60)

    client.loop_forever()
