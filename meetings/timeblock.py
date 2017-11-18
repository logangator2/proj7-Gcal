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
    
  def x(self):
    return