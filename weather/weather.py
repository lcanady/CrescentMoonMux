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


class ColorDatabase(object):
    """ Small color database """

    def __init__(self):
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


def connect(location, url, name):
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

    if args.path:

        # Is path a directory?
        if os.path.isdir(args.path[0]):
            path = args.path[0]

        else:
            msg("Error: Path not found: " + color(args.path[0], "yellow"), error=True)

    # No path provided.  Print in current working directory.
    else:
        path = os.getcwd() + '\\'

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
        msg("Starting connections:")
        print("-------------------------------------------------")

    yahoo_url = 'https://query.yahooapis.com/v1/public/yql?q=select * from\
    weather.forecast where woeid in (select woeid from geo.places(1) \
    where text="{}")&format=json'.format(args.location)

    # get today's date
    today = datetime.datetime.today().strftime('%m/%d/%Y')

    # USNO (Sun moon Database) URL strung.
    usno_url = 'http://api.usno.navy.mil/rstt/oneday?date={}&loc={}'.format(today, args.location)

    yahoo = Struct(connect(url=yahoo_url,
                           name="Yahoo Weather",
                           location=args.location))

    try:

        # If Yahoo found a location
        if yahoo.query.count:
            city = yahoo.query.results.channel.location.city
            region = yahoo.query.results.channel.location.region

            # If verbose show information about location.
            if args.verbose:
                msg("Location found: " + color(city + "," + region, "bold"))

            location = city + "," + region

            # Connect to the USNO database
            moon = Struct(connect(url=usno_url,
                                  name="USNO Database",
                                  location=location))

            # Generate reports
            report = populate_report(yahoo, moon)
            generate_report(report)

        # Else error and exit.
        else:
            msg("Error: Couldn't find a matching location.", error=True)

    except AttributeError:
        msg("Error: Couldn't resolve " + color("Yahoo API.", "bold"), error=True)


if __name__ == '__main__':

    # Setup argparse
    parser = argparse.ArgumentParser(description="Generate a weather report.",
                                     prog="weather.py")
    parser.add_argument('-p',
                        '--path',
                        nargs=1,
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
