# barcelona-events
Python script to find events in Barcelona in a certain date and [Bicing](https://www.bicing.barcelona/es)'s bike stations near them.
Uses requests to extract the necessary data. Shows the result to the user in the terminal. Some endpoints may be outdated.

## Prerequisites
You only need Python3 installed in your machine.

## Usage
```
python3 cerca.py --key CONCERT --date 20/07/2023 --distance 500
```

## Arguments
The arguments supported in the script are:
- **Help**: Shows the description of the arguments.
- **Key**: Selects all the activities that have this keyword as the name of the event, place or district.
- **Date**: Selects the events that have this date included between the start and the end.
- **Distance**: Indicates the maximum distance in meters that Bicing stations are showed.
