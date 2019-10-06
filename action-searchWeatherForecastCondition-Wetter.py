#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import configparser
from hermes_python.hermes import Hermes
#from hermes_python.ontology import *
import io
import random  # for random answer forms
from weather import Weather

CONFIGURATION_ENCODING_FORMAT = "utf-8"
CONFIG_INI = "config.ini"


class SnipsConfigParser(configparser.ConfigParser):
    def to_dict(self):
        return {section: {option_name: option for option_name, option in self.items(section)} for section in self.sections()}


def read_configuration_file(configuration_file):
    try:
        with io.open(configuration_file, encoding=CONFIGURATION_ENCODING_FORMAT) as f:
            conf_parser = SnipsConfigParser()
            conf_parser.read_file(f)
            return conf_parser.to_dict()
    except (IOError, configparser.Error) as e:
        return dict()


def subscribe_intent_callback(hermes, intentMessage):
    conf = read_configuration_file(CONFIG_INI)
    hermes.publish_end_session(
        intentMessage.session_id, weather.forecast_condition(intentMessage))


if __name__ == "__main__":
    conf = read_configuration_file(CONFIG_INI)
    weather = Weather(conf)
    with Hermes("localhost:1883") as h:
        h.subscribe_intent(
            "choudini:searchWeatherForecastCondition", subscribe_intent_callback).start()
