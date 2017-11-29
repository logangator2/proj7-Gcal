import arrow

class Timeblock:
  """
  A class that defines a block of time in arrow objects
  """
  def __init__(self, name, start, end):
    """
    Values:
      name: str, the summary of an event, used for identification
      begin: start datetime
      end: end datetime
    """
    self.name = name
    self.start = arrow.get(start)
    self.end = arrow.get(end)
    self.start_time = self.start.time()
    self.end_time = self.end.time()
    self.start_date = self.start.date()
    self.end_date = self.end.date()
    
  def __str__(self):
    # String representation
    return "{}: Start Time: {}, End Time: {}, Start Date: {}, End Date: {}".format(self.name, 
      self.start_time, self.end_time, self.start_date, self.end_date)

  def split(self, tb):
    """
    Splits a timeblock in two based off of another timeblock's start and end time.
    Args:
      tb: another timeblock on the same day as self, and with a smaller time range
    Returns:
      Two timeblocks, one up to the start time of tb, and one that starts at the end time of tb
    """
    tb1 = Timeblock(self.name + ".1", self.start, tb.start)
    tb2 = Timeblock(self.name + ".2", tb.end, self.end)
    return tb1, tb2

  def x(self):
    return