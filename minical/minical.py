#!/usr/bin/env python3
import sys
import os
import sqlite3
import datetime
import time
import readchar
import calendar
from collections import deque
from configparser import ConfigParser


RED_COLOR = u"\u001b[31m"
RESET_COLOR = u"\u001b[0m"
BLUE_COLOR = u"\u001b[34m"
MAGENTA_COLOR = u"\u001b[35m"
GREEN_COLOR = u"\u001b[32m"
BOLD = u"\u001b[1m"
UNDERLINE = u"\u001b[4m"
CLEARSCR = u"\u001b[2J"
COLORS = deque([BLUE_COLOR, GREEN_COLOR, MAGENTA_COLOR, RED_COLOR])
AGENDACOLORS = {}

FROMMILLI = 1000 * 1000

class Event:
    def __init__(self, calid, title, start, end):
        self.calid = calid
        self.title = title
        self.start = start
        self.end = end
        self.color = ""

    def __contains__(self, timestamp):
        if timestamp <= self.end and timestamp >= self.start:
            return True
        daystamp = datetime.datetime.fromtimestamp(timestamp)
        daystart = datetime.datetime.fromtimestamp(self.start)
        if daystamp.month == daystart.month and daystamp.year == daystart.year and daystamp.day == daystart.day:
            return True
        return False

    def is_multiday(self):
        return self.end - self.start >= 24 * 3600

    def __str__(self):
        if self.is_multiday():
            start = datetime.datetime.fromtimestamp(self.start)
            end = datetime.datetime.fromtimestamp(self.end)
            return "{}{}: {} -> {}{}".format(self.color, self.title, start.day, end.day, RESET_COLOR)
        else:
            start = datetime.datetime.fromtimestamp(self.start)
            end = datetime.datetime.fromtimestamp(self.end)
            return "{}{}: {} {}:{:02d} -> {}:{:02d}{}".format(self.color, self.title, start.day, start.hour, start.minute, end.hour, end.minute, RESET_COLOR)


def has_event(events, date):
    dayevents = []
    for event in events:
        if time.mktime(date.timetuple()) in event:
            dayevents.append(event)
    return dayevents

class Calendar:
    def __init__(self, options, **kwargs):
        if options.sunday:
            calendar.setfirstweekday(calendar.SUNDAY)
        elif options.monday:
            calendar.setfirstweekday(calendar.MONDAY)
        self.options = options
        self.db = self.get_db()
        month = datetime.datetime.now().replace(day=1)
        self.month = Month(month.month, month.year, self.db)

    def get_db(self):
        config = os.path.expanduser("~/.thunderbird/profiles.ini")
        if os.path.exists(config):
            cfg = ConfigParser()
            cfg.read(config)
            for section in cfg.sections():
                path = cfg.get(section, 'Path', fallback=None)
                if path is None:
                    continue
                config = os.path.expanduser("~/.thunderbird/{}/calendar-data/cache.sqlite".format(path))
                if os.path.exists(config):
                    return sqlite3.connect(config)


    def print_month(self):
        lines = str(self.month).splitlines()
        print(self.month.header())
        for idx, line in enumerate(lines):
            print("{:<23}".format(line), end="")
            if idx < len(self.month.events):
                print(self.month.events[idx])
            else:
                print("")
        for event in self.month.events[idx:]:
            print("                       {}".format(str(event)))

    def print_three(self):
        prev = self.month.previous()
        next = self.month.next()
        headers = [prev.header(), self.month.header(), next.header()]
        print(" ".join(headers))
        for parts in zip(str(prev).splitlines(), str(self.month).splitlines(), str(next).splitlines()):
            print(" ".join(parts))
        print("")
        for event in self.month.events:
            print(str(event))

    def print(self):
        if self.options.three:
            self.print_three()
        else:
            self.print_month()

    def run(self):
        self.print()
        while True:
            char = readchar.readkey()
            if char == "\x1b[C":
                self.month = self.month.next()
            elif char == "\x1b[D":
                self.month = self.month.previous()
            elif char == "q":
                sys.exit(0)
            print(CLEARSCR)
            self.print()

        

class Month:
    def __init__(self, month, year, db):
        self.db = db
        self.first = datetime.datetime(month=month, year=year, day=1)
        self.last = (self.first + datetime.timedelta(days=32)).replace(day=1) - datetime.timedelta(seconds=1)
        self.events = []
        if self.db:
            cursor = self.db.execute("select cal_id, id, title, event_start, event_end from cal_events where event_start > {} and event_start < {} order by event_start".format(self.first.timestamp() * FROMMILLI, self.last.timestamp() * FROMMILLI))
            ids = set()
            for event in cursor.fetchall():
                if event[1] in ids:
                    continue
                ids.add(event[1])
                self.events.append(Event(event[0], event[2], event[3] / FROMMILLI, event[4]/ FROMMILLI))

    def next(self):
        next = self.last + datetime.timedelta(seconds=1)
        return Month(next.month, next.year, self.db)

    def previous(self):
        next = (self.first - datetime.timedelta(seconds=1)).replace(day=1)
        return Month(next.month, next.year, self.db)

    def header(self):
        return "{:23s}".format(self.first.strftime("   %B / %Y"))

    def __str__(self):
        lines = []
        today = datetime.date.today()
        lines.append("{:23s}".format(calendar.weekheader(2)))
        for event in self.events:
            if event.calid in AGENDACOLORS:
                event.color = AGENDACOLORS[event.calid]
            else:
                event.color = COLORS[0]
                COLORS.rotate(-1)
                AGENDACOLORS[event.calid] = event.color

        for week in calendar.monthcalendar(self.first.year, self.first.month):
            days = []
            for day in week:
                start = ""
                end = RESET_COLOR
                dayevents = []
                if day == 0:
                    days.append("  ")
                    continue
                date = datetime.date(self.first.year, self.first.month, day)
                dayevents = has_event(self.events, date)
                if dayevents:
                    for event in dayevents:
                        if not event.is_multiday():
                            start = event.color
                            break
                    else:
                        start = self.events[0].color
                if date == today.month:
                    start += UNDERLINE
            
                days.append("{}{:2}{}".format(start, day, end))
            days.append("  ")
            lines.append(" ".join(days))

        lines.append("")
        return "\n".join(lines)

