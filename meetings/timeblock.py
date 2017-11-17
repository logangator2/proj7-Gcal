import arrow

class Timeblock:
  """
  A class that defines a block of time in arrow objects
  """
  def __init__(self, name, begin, end):
    """
    Args:
      name: str, the summary of an event
      begin: an ISO datetime string
      end: an ISO datetime string
    """
    self.name = name
    self.begin = begin
    self.end = end

  def arrowize(datetime):
    """
    Turns datetime strings into date arrow objects and time arrow objects
    Args:
      datetime: a datetime string, likely to be begin or end
    Returns:

    """
    date = arrow.get(datetime)
    time = arrow.get(datetime)
    return