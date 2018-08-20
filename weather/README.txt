I haven't done many README files yet, so please let me know if there's any
confusion.  You can probably just send me an issue request and I'll clarify

This system is re-written, inspired by Brus and Thenomian.  Originally the
code used Yahoo, then was moved over to Weather Underground when Yahoo
switched.  Now Weather Underground has stopped giving out keys to
developers, so I took it back to Yahoo APIs, the USNO and good old Google
geocoding. You aren't going to need an API Key to use this code.  You are
however going to need potential access to sudo, and will definitely need
access to crontab, your mux config files, and access to a wizard bit
on your game server.

*** STEP 1: Make sure Python is Installed ************************************

You need to make sure that you have AT LEAST Python 3 installed on your
server. More than likely if you're on a Debain based Linux system (Read Ubuntu)
Python 3 is already installed. Type 'python3 --version' to check! If you have
it, great! If not, no problem! Type 'sudo apt-get install python3.7'.

You're also going to need to have PIP Python's package installer installed.
To check and see if PIP3 is installed, type 'command -v pip3'  If pip isn't on
your system, this a great guide to getting setup:

https://pip.pypa.io/en/latest/installing/ It's pretty short.

Python developers like to use what are called virtual enviornments to keep
their development enviornments clean and seperated.  Here's a great guide
on getting setup:

https://docs.python-guide.org/dev/virtualenvs/#virtualenvironments-ref

Once all that's done! You need to install one package
'python pip install requests'

*** STEP 2: Running The Code ************************************************

Before we can run weather.py we need to make it executable, this is done with
'chmod +x weather.py'.  To access the help screen for the script, type
'./weather.py --help'.  We need to feed some basic information to get the
script to generate our first report:

./weather.py "location" -p full/path/to/your/game/text/directory

A great way to start working out your location is to go here:
https://developer.yahoo.com/weather/ and start location hunting. You can
manipulate the query language in green near the top.  At the very end of the
string is whre you'll find the spot to enter your location.

*** STEP 3: Setting up Crontab ***********************************************

Type 'Crontab -e' to edit your cron jobs.  At the bottom, add:

@hourly CD path/to/script; ./weather.py 'location' -p path/to/game/text/dir

Save, and exit!

*** STEP 4: Introducing weather.txt to your game *****************************

Find your game's config file. It's probably '<gamename>.conf'. Add this line:

helpfile meteo text/weather

Notice no .txt at the end!

*** STEP 5: Check The Game and Load the Softcode *****************************

As a wizard, type @restart, then @readcache.  Once that's done type 'meteo',
the weather file should pull up! 'meteo conditions'. It should list the
weather data. Once that's good, install the softcode in weather.min.mux and
test it out by typing 'weather'.

*** STEP 6: Start Mushcron ***************************************************

The game needs to run "@readcache" once an hour. In your Myrddin's mushcron
system, add the following lines:

&CRON_TIME_WEATHER mushcron=||||01 02|
&CRON_JOB_WEATHER mushcron=@readcache

You can find Mushcron here:

http://www.mushcode.com/File/Myrddins-MushCron-1-0-0

*** STEP 7: Done! ************************************************************

Check back in two minutes after the hour and see if your report is updated!
You can either use the weather command, or type 'meteo' and check the
timestamp on the file.
