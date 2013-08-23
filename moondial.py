#!/usr/bin/env python
import json, re, sys
from datetime import datetime
from math import *

import pytz

import pygame, pygame.font
from pygame.locals import *

from astronomia.coordinates import ecl_to_equ
from astronomia.constants import sun_rst_altitude, standard_rst_altitude

#import pyproj

import planets

_CLOCK_HEIGHT = 20
UTC = pytz.timezone('UTC')

planet_font = "QRSTUVWXYZ"
zodiac_font = "ABCDEFGHIJKL"
red = (255, 0, 0)
green = (0, 255, 0)
blue = (0, 0, 255)
yellow = (255, 255, 0)
white = (255, 255, 255)
planet_color = (yellow, white, green, green, red, red, yellow, green, blue, blue)
zodiac_color = (red, yellow, green, blue, red, yellow, green, blue, red, \
                yellow, green, blue)


#_proj = pyproj.Proj('+proj=laea +lat_0=90 +lon_0=0 +x_0=0 +y_0=0 +ellps=WGS84 '
#                    '+datum=WGS84 +units=m +no_defs')

def lonlat2xy(lonlat, wh):
    lon, lat = lonlat
    w, h = wh
    return int(round((lon+180.0)*w/360.0)), int(round((90.0-lat)*h/180.0))


class City(object):
    line_re = re.compile('(-?[\d\.]+)\s+(-?[\d\.]+)\s+("[^"]+")\s+(?:timezone=(\S+))?$')
    def __init__(self, name, lat, lon, tz=None):
        self.name = name
        self.lat = lat
        self.lon = lon
        self.tz = tz

    @classmethod
    def read(cls, fp):
        cities = []
        for line in fp:
            line = line.strip()
            if not line or line[0] == '#':
                continue
            m = cls.line_re.match(line)
            if m is None:
                raise ValueError('Unmatched line: %r' % line)
            lat = float(m.group(1))
            lon = float(m.group(2))
            name = m.group(3)
            tz = m.group(4)
            if tz is not None:
                tz = pytz.timezone(tz)
            cities.append(City(name, lat, lon, tz))
        return cities

    def utcoffset(self, dt):
        return self.tz.fromutc(dt).replace(tzinfo=None) - dt

    def draw(self, surface):
        w, h = surface.get_size()
        x, y = lonlat2xy((self.lon, self.lat), (w, h))
        #pygame.draw.circle(surface, (0, 0, 0), (x, y), 2, 1)
        surface.set_at((x-1, y), (0, 0, 0))
        surface.set_at((x+1, y), (0, 0, 0))
        surface.set_at((x, y-1), (0, 0, 0))
        surface.set_at((x, y+1), (0, 0, 0))
        tz = self.tz
        if tz is not None:
            offset = self.utcoffset(datetime.utcnow())
            seconds = offset.days * 86400 + offset.seconds
            tzx = int(round(w/2.0 + seconds * w / 86400.0))
            pygame.draw.line(surface, (0, 0, 0), (x, y+2), (x, h-10))
            pygame.draw.line(surface, (0, 0, 0), (x, h-10), (tzx, h-5))
            pygame.draw.line(surface, (0, 0, 0), (tzx, h-5), (tzx, h))


def split_blit(dst, src, xy):
    x, y = xy
    w, h = src.get_size()
    dst.blit(src, (0, y), (w-x, 0, x, h))
    dst.blit(src, (x, y))
    return [Rect((0, y, w, h))]


class MoonDial(object):
    def __init__(self):
        self.world = json.load(open('continent.json'))
        fp = open('cities')
        self.cities = City.read(fp)
        fp.close()
        self.planet_rects = []
        self.resize((0, 0))

    def make_planets(self):
        font = pygame.font.Font('ASTRO.TTF', 16)
        planets = []
        for char, color in zip(planet_font, planet_color):
            planet_surface = font.render(char, True, color)
            planet_shadow = font.render(char, True, (0, 0, 0, 96))
            surface = pygame.Surface(
                (planet_surface.get_width() + 1,
                 planet_surface.get_height() + 1)).convert_alpha()
            surface.fill((0, 0, 0, 0))
            surface.blit(planet_shadow, (1, 1))
            surface.blit(planet_surface, (0, 0))
            planets.append(surface)
        self.planets = planets

    def erase_planets(self):
        rects = self.planet_rects
        for rect in rects:
            self.blit_map(rect)
            self.blit_nightmap(rect)
        self.planet_rects = []
        return rects

    def update_planets(self):
        self.planet_pos = planets.get_planets()

    def draw_planets(self):
        size = self.surface.get_size()
        rects = []
        for surf, (lat, lon) in zip(self.planets, self.planet_pos):
            x, y = lonlat2xy((lon, lat), size)
            x -= surf.get_width() / 2
            y -= surf.get_height() / 2
            rects.append(self.surface.blit(surf, (x, y)))

        self.planet_rects = rects
        return rects

    def make_nightmap(self):
        lat = self.planet_pos[0][0]
        w, h = self.map.get_size()
        surface = pygame.Surface((w, h)).convert_alpha()
        surface.fill((0, 0, 0, 0))
        # sunset
        points = planets.get_terminator(lat, sun_rst_altitude, (w, h))
        pygame.draw.polygon(surface, (0, 0, 0, 64), points)
        # civil twilight
        points = planets.get_terminator(lat, -6.0/180.0*pi, (w, h))
        pygame.draw.polygon(surface, (0, 0, 0, 96), points)
        # nautical twilight
        points = planets.get_terminator(lat, -12.0/180.0*pi, (w, h))
        pygame.draw.polygon(surface, (0, 0, 0, 128), points)
        # astronomical twilight
        points = planets.get_terminator(lat, -18.0/180.0*pi, (w, h))
        pygame.draw.polygon(surface, (0, 0, 0, 160), points)
        self.nightmap = surface

    def make_moonmap(self):
        lat = self.planet_pos[0][0]
        size = self.map.get_size()
        surface = pygame.Surface(size).convert_alpha()
        surface.fill((0, 0, 0, 0))

        # moon visibility
        pointss = planets.get_terminator(lat, standard_rst_altitude, size,
                                         False)
        for points in pointss:
            pygame.draw.lines(surface, (255, 255, 255, 160), False, points)
        self.moonmap = surface

    def make_map(self):
        w, h = self.surface.get_size()
        h -= _CLOCK_HEIGHT
        surface = pygame.Surface((w, h))
        world = self.world
        surface.fill((0, 0, 192))
        size = (w, h)
        for feature in world['features']:
            if feature['properties']['CONTINENT'] == 'Antarctica':
                color = (255, 255, 255)
            else:
                color = (0, 192, 0)

            geometry = feature['geometry']
            t = geometry['type']
            coordinates = feature['geometry']['coordinates']
            if t == 'Polygon':
                coordinates = [coordinates]

            for coords in coordinates:
                points = [lonlat2xy(point, size) for point in coords[0][:-1]]
                pygame.draw.polygon(surface, color, points)

        self.map = surface
        self.draw_cities()

    def lon_to_x(self, lon):
        w = self.map.get_width()
        return int(round((lon / 360.0 + 0.25) * w)) % w

    def blit_map(self):
        return self.surface.blit(self.map, (0, 0))

    def blit_nightmap(self):
        x = self.lon_to_x(self.planet_pos[0][1])
        return split_blit(self.surface, self.nightmap, (x, 0))

    def blit_moonmap(self):
        x = self.lon_to_x(self.planet_pos[1][1])
        return split_blit(self.surface, self.moonmap, (x, 0))

    def draw_cities(self):
        surface = self.map
        for city in self.cities:
            city.draw(surface)

    def make_clock(self):
        w, h = self.surface.get_width(), _CLOCK_HEIGHT
        font = pygame.font.SysFont('arialblack', 16)
        fh = font.size('0123456789')[1]
        surface = pygame.Surface((w, h))
        surface.fill((0, 128, 255))
        for hour in range(24):
            x = int(round(hour * w / 24.0))
            x1 = int(round((hour+0.5) * w / 24.0))
            pygame.draw.line(surface, (255, 255, 255), (x, 0), (x, h))
            pygame.draw.line(surface, (255, 255, 255), (x1, 0), (x1, h-fh))
            text = font.render(str(hour), True, (255, 255, 255))
            surface.blit(text, (x1-int(round(text.get_width()/2.0)), h-fh))

        self.clock = surface

    def blit_clock(self):
        surface = self.surface
        clock = self.clock
        now = datetime.utcnow()
        frac = now.hour/24.0  + now.minute/1440.0 + now.second/86400.0
        w, h = surface.get_size()
        x = int(round((w/2.0 - w*frac) % w))
        ch = clock.get_height()
        return split_blit(surface, clock, (x, h-ch))

    def resize(self, size):
        self.surface = pygame.display.set_mode(size, RESIZABLE)
        self.make_planets()
        self.draw()

    def draw(self):
        self.make_map()
        self.blit_map()
        self.update_planets()
        self.make_nightmap()
        self.blit_nightmap()
        self.make_moonmap()
        self.blit_moonmap()
        self.draw_planets()
        self.make_clock()
        self.blit_clock()
        pygame.display.flip()

    def update(self):
        self.blit_map()
        self.update_planets()
        self.blit_nightmap()
        self.blit_moonmap()
        self.blit_clock()
        self.draw_planets()
        pygame.display.flip()

DRAWCLOCK = USEREVENT

def main():
    pygame.init()
    window = MoonDial()
    pygame.time.set_timer(DRAWCLOCK, 10000)

    while True:
        event = pygame.event.wait()
        if event.type == QUIT:
            return
        elif event.type == VIDEORESIZE:
            if pygame.event.peek([VIDEORESIZE]):
                continue
            window.resize(event.size)
        elif event.type == DRAWCLOCK:
            window.update()


if __name__ == '__main__':
    main()
