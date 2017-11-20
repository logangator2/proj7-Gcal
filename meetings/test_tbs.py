import nose
from free import freemaker
import timeblock

busy_list = [{ 'Summary': '322 Lab', 'Start Time': '2017-11-21T14:00:00-08:00', 'End Time': '2017-11-21T15:00:00-08:00'}, 
{'Summary': 'Thing to do every three days', 'Start Time': '2017-11-22T12:00:00-08:00', 'End Time': '2017-11-22T13:00:00-08:00'}, 
{'Summary': 'Thing to do every four days', 'Start Time': '2017-11-22T12:30:00-08:00', 'End Time': '2017-11-22T13:30:00-08:00'}, 
{'Summary': '322 Lab', 'Start Time': '2017-11-23T14:00:00-08:00', 'End Time': '2017-11-23T15:00:00-08:00'}, 
{'Summary': 'I SHOULD BE HERE', 'Start Time': '2017-11-24T14:30:00-08:00', 'End Time': '2017-11-25T19:00:00-08:00'}, 
{'Summary': 'Thing to do every three days', 'Start Time': '2017-11-25T12:00:00-08:00', 'End Time': '2017-11-25T13:00:00-08:00'}, 
{'Summary': 'Thing to do every four days', 'Start Time': '2017-11-26T12:30:00-08:00', 'End Time': '2017-11-26T13:30:00-08:00'}]

free_list = [timeblock.Timeblock("Test 1", , ), 
timeblock.Timeblock("Test 2", , )
timeblock.Timeblock("Test 3", , )
timeblock.Timeblock("Test 4", , )
timeblock.Timeblock("Test 5", , )]

def test_available_tbs():
  """
  Corresponding Tests:
  1. Check that a busy event outside the date range does not split up an available timeblock
  2. Check that a busy event inside the date range does not split up an available timeblock
  if it is outside the time range
  3. Check that a busy event inside the date and time ranges splits up an available timeblock correctly
  4. Check that an event that completely envelops an available timeblock removes the timeblock from the free_list
  5. Check that if a busy event partially covers an available timeblock that it removes the appropriate chunk
  of time
  # FIXME: There's probably a better way to test this.
  """
  assert freemaker(busy_list, , ) == free_list