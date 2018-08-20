#!/usr/bin/env python3
#
# Weather.py
#
# USAGE:
#   ./weather.py --help
#   ./weather.py "Location (Alexandria, VA)" -p /path/to/game/text/folder
#
# Before you can run the script you're going to have have to set it
# executable:  chmod weather.py +x
#
#############################################################################

import re
import requests
import datetime
import time
import sys
import argparse


class Struct(object):
    """object for structuring json queries into objects"""

    def __init__(self, data):
        for name, value in data.items():
            setattr(self, name, self._wrap(value))

    def _wrap(self, value):
        if isinstance(value, (tuple, list, set, frozenset)):
            return type(value)([self._wrap(v) for v in value])
        else:
            return Struct(value) if isinstance(value, dict) else value

    def __repr__(self):
        return '{%s}' % str(', '.join("'%s': %s" % (k, repr(v)) for (k, v) in self.__dict__.items()))


class Conditions(object):
    """ Framework for the the weather condition entries """

    def __init__(self):
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


def epoch(string, timezone):
    """ Convert a time string into epoch seconds for MUX consumption """

    # Get current date
    date = datetime.datetime.today().strftime('%m.%d.%Y')

    # Use regular expressions to break the time string apart.
    regex = re.match("^(\d:\d{2})\s(\w\.\w\.)", string)

    if regex.group(2) == "a.m.":
        ampm = "AM"
    else:
        ampm = "PM"

    # Build UTC Offset string.  This is kind of hacky and I'm pretty
    # sure it won't work for all cases.  I'll have to come back through
    # and fix this logic later!
    x = str(timezone)
    tz = x[0] + '0' + x[1:2] + '00'

    # Format date_time string
    date_time = "{} {} {} {}".format(date, regex.group(1), ampm, tz)
    pattern = "%m.%d.%Y %I:%M %p %z"
    epoch = int(time.mktime(time.strptime(date_time, pattern)))

    return epoch


def yahoo_connect(location):
    """ Get Current Weather information from Yahoo Weather """

    # Yahoo weather URL string.
    url = 'https://query.yahooapis.com/v1/public/yql?q=select * from\
    weather.forecast where woeid in (select woeid from geo.places(1) \
    where text="{}")&format=json'.format(location)

    # Try to connect to yahoo.  Exit code 1 if connection can't be made.
    try:
        res = requests.get(url)
    except requests.exceptions.RequestException as e:
        print(e)
        sys.exit(1)

    if args.verbose:
        print("Mux Weather: Connected to Yahoo Weather")

    return res.json()


def google_geocode(location):
    """ Get geocode information for the given location to make sure
    it's an actual location."""

    # Yahoo weather URL string.
    url = 'https://maps.googleapis.com/maps/api/geocode/json?address={}'.format(location)

    # Try to connect to google.  Exit code 1 if connection can't be made.
    try:
        res = requests.get(url)
    except requests.exceptions.RequestException as e:
        print(e)
        sys.exit(1)

    if args.verbose:
        print("Mux Weather: Connected to Google Geoencoding")

    return res.json()


def usno_connect(location):
    """ Get sun and moon data from the USNO database """

    # get today's date
    today = datetime.datetime.today().strftime('%m/%d/%Y')

    # USNO (Sun moon Database) URL strung.
    url = 'http://api.usno.navy.mil/rstt/oneday?date={}&loc={}'.format(today, location)

    # Try to connect.  Exit with code 1 if can't.
    try:
        res = requests.get(url)
    except requests.exceptions.RequestException as e:
        print(e)
        sys.exit(1)

    if args.verbose:
        print("Mux Weather: Connected to USNO database")

    return res.json()


def populate_report(yahoo, moon):
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
    weather.sunrise = str(epoch(moon.sundata[1].time, moon.tz))
    weather.sunset = str(epoch(moon.sundata[3].time, moon.tz))
    weather.moonrise = str(epoch(moon.moondata[1].time, moon.tz))
    weather.moonset = str(epoch(moon.moondata[0].time, moon.tz))
    weather.moon_phase = "{} ({}%)".format(moon.curphase, moon.fracillum)

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
and the USNO Atrological API http://aa.usno.navy.mil/data/docs/api.php.
Weather Underground was great but it's no longer free use for developers! Boo!
"""

    print("Mux Weather: Generating weather.txt")

    if args.path:
        path = args.path
    else:
        path = ""

    fullpath = path + 'weather.txt'
    if args.verbose:
        if args.path:
            print("Mux Weather: File path: {}".format(args.path))

    try:
        with open(fullpath, 'w') as file:

            file.write(file_index)
            file.write(file_conditions)
            file.write(file_credits)

    except Exception as e:
        print(e)
        sys.stderr.write('{}: error: could not open weather.txt.\n'.format(sys.argv[0]))
        sys.exit(1)
    else:
        if args.verbose:
            print("Mux Weather: {} generated.".format(fullpath))
        print("Mux Weather: Update Complete: {}".format(
            datetime.datetime.today().strftime('%m.%d.%Y %H:%M:%S')))
        sys.exit(0)


def main():
    """ main entry point of the script. """

    print("Welcome to Mux Weather")
    print("Mux Weather: Start time: {}".format(
        datetime.datetime.today().strftime('%m.%d.%Y %H:%M:%S')))

    if args.verbose:
        print("Mux Weather: Connecting to API:")
        print("-----------------------------------------------")

    yahoo = Struct(yahoo_connect(args.location))
    moon = Struct(usno_connect(args.location))
    geocode = Struct(google_geocode(args.location))

    # if google didn't return with a location throw an error and exit,
    # else generate the report. Also error if the connection times out
    # and locality doesn't populate.

    try:

        if not geocode.results[0].address_components[0].types[0] == "locality":
            sys.stderr.write('{}: error: location not found.\n'.format(sys.argv[0]))
            sys.exit(1)
        else:
            report = populate_report(yahoo, moon)
            generate_report(report)

    except IndexError:
        sys.stderr.write('{}: error: geolocation error.\n'.format(sys.argv[0]))
        sys.exit(1)


if __name__ == '__main__':

    # Setup argparse
    parser = argparse.ArgumentParser("Generate a weather report.")
    parser.add_argument('-p',
                        '--path',
                        metavar="",
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
