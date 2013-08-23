from datetime import datetime
from itertools import groupby
from math import *

from astronomia.planets import geocentric_planet
from astronomia.lunar import Lunar
from astronomia import sun
from astronomia.calendar import cal_to_jd, cal_to_jde, lt_to_str, \
    sidereal_time_greenwich
from astronomia.dynamical import deltaT_seconds
from astronomia.nutation import obliquity
from astronomia.constants import seconds_per_day, days_per_second
from astronomia.calendar import hms_to_fday, fday_to_hms
from astronomia.util import r_to_d
from astronomia.coordinates import ecl_to_equ

elp2000 = Lunar()

def equ_to_geo(ra, dec, st):
    lon = r_to_d(ra - st)
    if lon > 180.0:
        lon -= 360.0
    return r_to_d(dec), lon


def get_planets():
    planet_names = ('Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus',
                    'Neptune')
    d = datetime.utcnow()
    jd = cal_to_jde(d.year, d.month, d.day, d.hour, d.minute, d.second)
    dt = jd + deltaT_seconds(jd) / seconds_per_day
    st = sidereal_time_greenwich(jd)
    deltaPsi = 0.0
    epsilon = obliquity(dt)
    delta = days_per_second
    planets = []

    # this is in ecliptic coordinates
    lon = sun.apparent_longitude_low(dt, sun.longitude_radius_low(dt)[0])
    ra, dec = ecl_to_equ(lon, 0.0, epsilon)
    planets.append(equ_to_geo(ra, dec, st))

    lon, lat = elp2000.dimension3(dt)[:2]
    ra, dec = ecl_to_equ(lon, lat, epsilon)
    planets.append(equ_to_geo(ra, dec, st))

    for planet in planet_names:
        ra, dec = geocentric_planet(dt, planet, deltaPsi, epsilon, days_per_second)
        planets.append(equ_to_geo(ra, dec, st))

    return planets


def get_terminator(lat, alt, wh, polygon=True):
    (w, h) = wh
    lat = lat / 180.0 * pi
    obl = lat - pi/2
    pointss = []
    points = []
    if lat < 0.0:
        prev_x = w
    else:
        prev_x = -1
    for deg in range(360):
        H = deg / 180.0 * pi
        alpha, delta = ecl_to_equ(H, alt, obl)
        x = int(round(alpha / (2*pi) * w))
        y = int(round((0.5 - delta / pi) * h))
        if lat < alt:
            if x > prev_x:
                if polygon:
                    points.extend([(0, 0), (w-1, 0)])
                else:
                    points.append(None)
        elif lat > -alt and x < prev_x:
            if polygon:
                points.extend([(w-1, h-1), (0, h-1)])
            else:
                points.append(None)
        points.append((x, y))
        prev_x = x

    if polygon:
        return points
    else:
        return [list(group) for k, group in groupby(points, bool) if k]


def main():
    print(get_planets())


if __name__ == '__main__':
    main()
