#!/usr/bin/env python3

"""
Title: Mux Weather
Author: Lem Canady (Death@CrescentMoonMux)

https://github.com/lcanady/CrescentMoonMux/

Description:  This script processes weather information from Yahoo Weather,
and strological information from the USNO to compile a text file to be used
in a TinyMux chat server to power an in-game weather system.

Usage:
    ./weather.py --help
    ./weather.py "location (Alexandria, VA)" -p path/to/game/text/folder

Returns: weather.txt

"""

import re
import requests
import datetime
import time
import sys
import os
import argparse


class Struct(object):
    """For structuring json queries into objects"""

    def __init__(self, data):
        for name, value in data.items():
            setattr(self, name, self._wrap(value))

    def _wrap(self, value):
        if isinstance(value, (tuple, list, set, frozenset)):
            return type(value)([self._wrap(v) for v in value])
        else:
            return Struct(value) if isinstance(value, dict) else value

    def __repr__(self):
        return '{%s}' % str(', '.join("'%s': %s" % (k, repr(v))
                                      for (k, v) in self.__dict__.items()))


class Conditions(object):
    """ Framework for the the weather condition entries """

    def __init__(self):
        """ Inititate all required attributes to empty strings """
        self.conditions = ""
        self.temperature = ""
        self.wind = ""
        self.pressure = ""
        self.visibility = ""
        self.humidity = ""
        self.sunrise = ""
        self.sunset = ""
        self.moonrise = ""
        self.moonset = ""
        self.moon_phase = ""


class ColorDatabase(object):
    """ Small color database """

    def __init__(self):
        """ Build a dictionary of color escape codes that can be
        called on by name """
        self.color = {"black": "\u001b[30m",
                      "red": "\u001b[31m",
                      "green": "\u001b[32m",
                      "yellow": "\u001b[33m",
                      "blue": "\u001b[34m",
                      "magenta": "\u001b[35m",
                      "cycan": "\u001b[36m",
                      "white": "\u001b[37m",
                      "normal": "\u001b[0m",
                      "bold": "\u001b[1m",
                      "underline": "\u001b[4m",
                      "reversed": "\u001b[7m"}


def cels(temp):
    """ convert F to C """

    Celsius = 0
    Celsius = (temp - 32) * 5.0 / 9.0

    return round(Celsius, 2)


def degToCompass(num):
    """ Turn degress into a compass direction """

    val = int((num / 22.5) + .5)

    arr = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S",
           "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]

    return arr[(val % 16)]


def connect(url, name):
    """ Connect to API Sources """

    if args.verbose:
        msg("Attempting connection to host: " + color(name, "bold"))

    # Try to connect.  Exit with code 1 if can't.
    try:
        res = requests.get(url)
    except requests.exceptions.RequestException as e:
        msg(e, error=True)

    if args.verbose:
        msg("Connected to API: " + color(name, "bold"))

    return res.json()


def supports_color():
    """
    Returns True if the running system's terminal supports color, and False
    otherwise.
    """
    plat = sys.platform
    supported_platform = plat != 'Pocket PC' and (plat != 'win32' or
                                                  'ANSICON' in os.environ)
    # isatty is not always implemented, #6223.
    is_a_tty = hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()
    if not supported_platform or not is_a_tty:
        return False
    return True


def color(message, color):
    library = ColorDatabase()

    # Does the terminal allow for ansi color codes?
    if supports_color():

        # Is the color defined?
        if color in library.color:
            return library.color[color] + message + library.color['normal']
        else:
            # No color found
            return message

    # color not supported
    else:
        return message


def msg(message, error=None):
    """ Print an message """

    output = ""

    # Put together the output message
    if not error:
        output = color("Mux Weather: ", "yellow") + message
        print(output)

    # If it's an error message, print to stderr and exit with code 1.
    else:
        output = color("Mux Weather: ", "red") + str(message)
        sys.stderr.write(output)
        sys.exit(1)


def populate_report(yahoo, moon, tz):
    """ Prep the weather object to be writen to weather.txt """

    weather = Conditions()

    weather.conditions = yahoo.query.results.channel.item.condition.text
    weather.temperature = "{} F ({} C)".format(
        yahoo.query.results.channel.item.condition.temp,
        cels(int(yahoo.query.results.channel.item.condition.temp)))
    weather.wind = "{} MPH {} ({} KPH)".format(
        yahoo.query.results.channel.wind.speed,
        degToCompass(int(yahoo.query.results.channel.wind.direction)),
        round(int(yahoo.query.results.channel.wind.speed) * 1.60934, 2))
    weather.pressure = "{} mb ({} inHg)".format(
        yahoo.query.results.channel.atmosphere.pressure,
        round(float(yahoo.query.results.channel.atmosphere.pressure) * 0.02953, 2))
    weather.humidity = "{}%%".format(yahoo.query.results.channel.atmosphere.humidity)
    weather.visibility = "{} miles ({} km)".format(
        yahoo.query.results.channel.atmosphere.visibility,
        round(float(yahoo.query.results.channel.atmosphere.visibility) * 1.60934, 2))
    weather.sunrise = moon.sundata[1].time
    weather.sunset = moon.sundata[3].time

    if hasattr('moon', 'curphase'):
        weather.moonrise = moon.moondata[2].time + '|' + str(int(tz))
        weather.moonset = moon.moondata[1].time + '|' + str(int(tz))
    else:
        weather.moonrise = moon.moondata[2].time + '|' + str(int(tz))
        weather.moonset = moon.moondata[1].time + '|' + str(int(tz))

    if hasattr('moon', 'curphase'):
        weather.moon_phase = "{} ({}%)".format(moon.curphase, moon.fracillum)
    else:
        weather.moon_phase = "Unavailable"
    return weather


def generate_report(weather):

    file_index = "& help\n"
    file_index += "This is the weather system raw data file.\n\n"
    file_index += "conditions: Weather conditions\n"
    file_index += "Credits: Thanks and credits\n"
    file_index += "Last run: {}\n\n".format(
        datetime.datetime.today().strftime('%m.%d.%Y %H:%M:%S'))

    file_conditions = "& conditions\n"

    for key, value in weather.__dict__.items():
        file_conditions += "{}: {}\n".format(key, value)

    file_credits = "\n& credits\n"
    file_credits += """PHP and TinyMUX code originally by Brus using the Yahoo Weather API.

Rewritten by Thenomain using the Weather Underground API.

Re-rewritten by Death@CrescentMoonMux https://github.com/lcanady to
use Python and the Yahoo Weather API (again!) https://www.yahoo.com/?ilc=401,
and the USNO Atrological API http://aa.usno.navy.mil/data/docs/api.php, with
a little Google Timezones API to help bridge the two:
https://developers.google.com/maps/documentation/timezone/start
Weather Underground was great but it's no longer free use for developers! Boo!
"""

    if args.path:

        # Is path a directory?
        if os.path.isdir(args.path[0]):
            path = args.path[0]

        else:
            msg("Error: Path not found: " + color(args.path[0], "yellow"), error=True)

    # No path provided.  Print in current working directory.
    else:
        path = os.getcwd() + '/'

    fullpath = os.path.abspath(path + 'weather.txt')

    msg("Generating File: " + color(fullpath, "bold"))
    try:
        with open(fullpath, 'w') as file:

            file.write(file_index)
            file.write(file_conditions)
            file.write(file_credits)

    except Exception as e:
        msg(e, error=True)
    else:
        msg("Update Complete: " + color(
            datetime.datetime.today().strftime('%m.%d.%Y %H:%M:%S'), "bold"))
        sys.exit(0)


def main():
    """ main entry point of the script. """

    msg("Script Activated.")

    msg("Start time: " +
        color(datetime.datetime.today().strftime('%m.%d.%Y %H:%M:%S'), "bold"))

    if args.verbose:
        msg("Attempting connections:")
        print("-------------------------------------------------")

    yahoo_url = 'https://query.yahooapis.com/v1/public/yql?q=select * from\
    weather.forecast where woeid in (select woeid from geo.places(1) \
    where text="{}")&format=json'.format(args.location)

    # get today's date
    today = datetime.datetime.today().strftime('%m/%d/%Y')

    yahoo = Struct(connect(url=yahoo_url,
                           name="Yahoo Weather"))

    try:

        # If Yahoo found a location
        if yahoo.query.count:

            city = yahoo.query.results.channel.location.city
            region = yahoo.query.results.channel.location.region
            lat = yahoo.query.results.channel.item.lat
            lon = yahoo.query.results.channel.item.long

            # If verbose show information about location.
            if args.verbose:
                msg("Location found: " + color(city + "," + region, "bold"))

            # Google Timezone API
            ts = datetime.datetime.now().timestamp()
            google_url = 'https://maps.googleapis.com/maps/api/timezone/json?location={},{}&timestamp={}'.format(lat, lon, ts)

            google = Struct(connect(url=google_url,
                                    name="Google Timezones API"))

            # calculate UTC Timezone
            tz = round((google.rawOffset + google.dstOffset) / 3600, 0)

            # USNO (Sun moon Database) URL strung.
            usno_url = 'http://api.usno.navy.mil/rstt/oneday?date=\
            {}&coords={},{}&tz={}'.format(today, lat, lon, int(tz))

            # Connect to the USNO database
            moon = Struct(connect(url=usno_url,
                                  name="USNO Database"))

            if args.verbose:
                print("-------------------------------------------------")

            # Generate reports
            report = populate_report(yahoo, moon, tz)
            generate_report(report)

        # Else error and exit.
        else:
            msg("Error: Couldn't find a matching location.", error=True)

    except Exception as e:
        msg("Error: " + str(e), error=True)


if __name__ == '__main__':

    # Setup argparse
    parser = argparse.ArgumentParser(description="Generate a weather report.",
                                     prog="weather.py")
    parser.add_argument('-p',
                        '--path',
                        nargs=1,
                        metavar="PATH",
                        help="Path to store weather.txt")
    parser.add_argument('location',
                        type=str,
                        help="The report location (City, state, Zip, etc).")
    parser.add_argument('-v',
                        '--verbose',
                        action="store_true",
                        help="Turn on extra output.")
    args = parser.parse_args()

    # Run the script
    main()
