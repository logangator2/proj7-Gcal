import timeblock
import logging
import arrow

def freemaker(busy_list, begin, end):
  """
  Takes a list of busy times and checks to see if they are within the proper time range
  Args:
    busy_list: a list of busy events within a datetime range (with overlapping in/out of dates)
    begin: start datetime of daterange
    end: end datetime of daterange
  Returns:
    free_list: list that has free blocks in datetime range
  """
  free_list = []
  busy_tb_list = []
  for event in busy_list:
  	event_tb = timeblock.Timeblock(event["Summary"], event["Start Time"], event["End Time"])
  	busy_tb_list.append(event_tb)

  # List of available timeblocks
  availability = convert_datetime(begin, end)

  return free_list

def convert_datetime(begin, end):
  """
  Converts start and end datetimes of the datetime range into a
  list of available timeblocks for every day included in the range.
  Args:
    begin: see freemaker
    end: see freemaker
  Returns:
    avail_list: a list of available timeblocks
  """
  avail_list = []
  day_list = []
  counter = 0

  # Convert to arrow objects
  begin = arrow.get(begin)
  end = arrow.get(end)
  # Convert to strings for subsequent conversion
  begin_time = str(begin.time())
  end_time = str(end.time())
  # Logic from arrowizer in flask_main
  begin_hour = int(begin_time[:2])
  end_hour = int(end_time[:2])
  begin_minute = int(begin_time[3:5])
  end_minute = int(end_time[3:5])

  # Find how many days there are between begin and end
  for day in arrow.Arrow.span_range('day', begin, end):
    day_list.append(day)
  for day in day_list:
    counter += 1
    # Access first of every arrow tuple, make it at begin time
    start = day[0].replace(hour=begin_hour, minute=begin_minute)
    # Access second of every arrow tuple, make it at end time
    end = day[1].replace(hour=end_hour, minute=end_minute)
    # Create a new timeblock with properties begin arrow, end arrow
    avail_tb = timeblock.Timeblock("Available Block {}".format(counter), start, end)
    # Add Timeblock to avail_list as an available time
    avail_list.append(avail_tb)
    """
    Example:
    Name: Available Block 1, Start: 2017-11-19T09:00:00-08:00, End: 2017-11-19T20:00:59.999999-08:00
    Name: Available Block 2, Start: 2017-11-20T09:00:00-08:00, End: 2017-11-20T20:00:59.999999-08:00
    """
  return avail_list
