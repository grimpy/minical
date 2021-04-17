#!/usr/bin/env python3
from .minical import Calendar


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-3", "--three", action="store_true", default=False)
    parser.add_argument("-s", "--sunday", action="store_true", default=False)
    parser.add_argument("-m", "--monday", action="store_true", default=False)
    parser.add_argument("-p", "--show-past", action="store_true", default=False)
    parser.add_argument("-e", "--max-events", type=int, default=5)
    options = parser.parse_args()
    cal = Calendar(options)
    cal.run()


if __name__ == "__main__":
    main()
