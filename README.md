About
=====

This is a Python implementation of an extremely expensive physical sun
clock I saw at Brookstone or something. In addition to showing the
lighted areas of the world with visually distinct sunset, civil,
nautical, and astronomical twilight terminators, it also shows the
current surface location of the sun, the moon, and all the planets,
and the lunar terminator. A strip at the bottom shows the current mean
time for every longitude, with lines drawn from cities to their
respective civil time, making the difference clear.

I originally wrote this back in 2006. I polished it up and did the
minimum work necessary to port it to Python 3 (and from Astrolabe to
Astronomia) in 2013, adding the lunar terminator and making some other
minor tweaks at the same time.


Requirements
============

* Python 3 (Probably 3.1 so you can use the below Pygame 2 builds)
* [Pygame 2.0](http://thorbrian.com/pygame/builds.php)
* [Astronomia](https://pypi.python.org/pypi/astronomia)
* [Pytz](https://pypi.python.org/pypi/pytz)


Usage
=====

Running
----------

Once all the dependencies are installed, you should just be able to
run moondial.py, possibly passing it as an argument to the Python
executable. You probably need to be in the same directory as the
"cities" and "continent.json" files for things to work right. This is
a bug I'll eventually get around to fixing. It's not that it's hard to
fix; I'm just practing ESR's "release early, release often"
mantra. Well, at least the "release early" part.


Adding cities
-------------

Edit the "cities" file. The format is whitespace separated with
coordinates given in decimal degrees. Latitude is first with positive
numbers being north, then the longitude with positive values being
east, then the city name in quotes, then "timezone=" followed by the
timezone in
[Olson format](http://www.ibm.com/developerworks/aix/library/au-aix-posix/)
(POSIX will probably work too). I don't recall exactly where this
somewhat silly file format comes from; it was probably xplanet. I'll
probably switch to YAML in the future.
