# -*- encoding: utf-8 -*-
import requests
import datetime
import random
from darksky import forecast as ds_forecast
from geopy.geocoders import Nominatim


class Weather:
    def __init__(self, config):
        self.fromtimestamp = datetime.datetime.fromtimestamp
        # self.weather_api_base_url = "https://api.darksky.net/forecast/"
        self.geolocator = Nominatim(user_agent="darksky")
        try:
            self.weather_api_key = config['secret']['darksky_api_key']
        except KeyError:
            self.weather_api_key = "XXXXXXXXXXXXXXXXXXXXX"
        try:
            self.default_city_name = config['secret']['default_city'].encode('utf8')
        except KeyError:
            self.default_city_name = "Berlin"
        try:
            self.units = config['global']['units']
        except KeyError:
            self.units = "si"

    def parse_dark_sky_forecast_response(self, response, location):
        # Parse the output of Dark Sky's forecast endpoint
        try:
            today = self.fromtimestamp(response["list"][0]["dt"]).day
            today_forecasts = list(
                filter(lambda forecast: self.fromtimestamp(forecast["dt"]).day == today, response["list"]))

            all_min = [x["main"]["temp_min"] for x in today_forecasts]
            all_max = [x["main"]["temp_max"] for x in today_forecasts]
            all_conditions = [x["weather"][0]["description"].encode('utf8') for x in today_forecasts]
            rain = list(filter(lambda forecast: forecast["weather"][0]["main"] == "Rain", today_forecasts))
            snow = list(filter(lambda forecast: forecast["weather"][0]["main"] == "Snow", today_forecasts))

            return {
                "rc": 0,
                "location": location,
                "inLocation": " in {0}".format(location) if location else "",
                "temperature": int(today_forecasts[0]["main"]["temp"]),
                "temperatureMin": int(min(all_min)),
                "temperatureMax": int(max(all_max)),
                "rain": len(rain) > 0,
                "snow": len(snow) > 0,
                "mainCondition": max(set(all_conditions), key=all_conditions.count).lower()
            }
        except KeyError:  # error 404 (locality not found or api key is wrong)
            return {'rc': 2}
    
    def error_response(self, data):
        error_num = data.rc
        if error_num == 1:
            response = random.choice(["Es ist leider kein Internet verfügbar.",
                                      "Ich bin nicht mit dem Internet verbunden.",
                                      "Es ist kein Internet vorhanden."])
            # if 'location' in data.keys() and data['location'] == self.default_city_name:
            #     response = "Schau doch aus dem Fenster. " + response
        elif error_num == 2:
            response = random.choice(["Wetter konnte nicht abgerufen werden. Entweder gibt es den Ort nicht, oder der "
                                      "API-Schlüssel ist ungültig.",
                                      "Fehler beim Abrufen. Entweder gibt es den Ort nicht, oder der API-Schlüssel "
                                      "ist ungültig."])
        else:
            response = random.choice(["Es ist ein Fehler aufgetreten.", "Hier ist ein Fehler aufgetreten."])
        return response

    def get_weather_forecast(self, intentMessage):
        # Parse the query slots, and fetch the weather forecast from Dark Sky's API
        locations = []
        for (slot_value, slot) in intentMessage.slots.items():
            if slot_value not in ['forecast_condition_name', 'forecast_start_date_time',
                                  'forecast_item', 'forecast_temperature_name']:
                locations.append(slot[0].slot_value.value)
        location_objects = [loc_obj for loc_obj in locations if loc_obj is not None]
        if location_objects:
            location = location_objects[0].value.encode('utf8')
        else:
            location = self.default_city_name
        # get longitude and latitude from geopy
        geolocation = self.geolocator.geocode(location)
        location = geolocation.address.split(',')[0]

        # forecast_url = "{0}/{1}/{2}".format(
        #     self.weather_api_base_url, self.weather_api_key, location)
        try:
            r_forecast = ds_forecast(self.weather_api_key, geolocation.latitude, geolocation.longitude, units='si')
            r_forecast.location = location
            r_forecast.inLocation = " in {0}".format(location) if location else "",
            r_forecast.rc = 0
            return r_forecast
            # return self.parse_dark_sky_forecast_response(r_forecast.json(), location)
        except (requests.exceptions.ConnectionError, ValueError):
            return {'rc': 1}  # Error: No internet connection

    @staticmethod
    def add_warning_if_needed(response, weather_forecast):
        weather_today = weather_forecast.daily[0]
        if weather_today.precipProbability > 0.1 and weather_today.precipType = "rain" \ 
                and "rain" not in weather_today.summary:
            response += ' Es könnte regnen.'
        if weather_today.precipProbability > 0.1 and weather_today.precipType = "snow" \ 
                and "snow" not in weather_today.summary:
            response += ' Es könnte schneien.'
        return response

    def forecast(self, intentMessage):
        """
                Complete answer:
                    - condition
                    - current temperature
                    - max and min temperature
                    - warning about rain or snow if needed
        """
        weather_forecast = self.get_weather_forecast(intentMessage)
        if weather_forecast.rc != 0:
            response = self.error_response(weather_forecast)
        else:
            weather_today = weather_forecast.daily[0]
            response = ("Wetter heute{1}: {0}. "
                        "Aktuelle Temperatur ist {2} Grad. "
                        "Höchsttemperatur: {3} Grad. "
                        "Tiefsttemperatur: {4} Grad.").format(
                weather_today.summary,
                weather_forecast.inLocation,
                weather_forecast.currently.temperature,
                weather_today.temperatureMax,
                weather_today.temperatureMin
            )
            response = self.add_warning_if_needed(response, weather_today)
        response = response.decode('utf8')
        return response

    def forecast_condition(self, intentMessage):
        """
        Condition-focused answer:
            - condition
            - warning about rain or snow if needed
        """
        weather_forecast = self.get_weather_forecast(intentMessage)
        if weather_forecast['rc'] != 0:
            response = self.error_response(weather_forecast)
        else:
            weather_today = weather_forecast.daily[0]
            response = "Wetter heute{1}: {0}.".format(
                weather_today.summary,
                weather_forecast.inLocation
            )
            response = self.add_warning_if_needed(response, weather_forecast)
        response = response.decode('utf8')
        return response

    def forecast_temperature(self, intentMessage):
        """
        Temperature-focused answer:
            - current temperature
            - max and min temperature
        """
        weather_forecast = self.get_weather_forecast(intentMessage)
        if weather_forecast['rc'] != 0:
            response = self.error_response(weather_forecast)
        else:
            weather_today = weather_forecast.daily[0]
            response = ("{0} hat es aktuell {1} Grad. "
                        "Heute wird die Höchsttemperatur {2} Grad sein "
                        "und die Tiefsttemperatur {3} Grad.").format(
                weather_forecast.inLocation,
                weather_forecast.currently.temperature,
                weather_today.temperatureMax,
                weather_today.temperatureMin)
        response = response.decode('utf8')
        return response
