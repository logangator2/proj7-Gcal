import flask
from flask import render_template
from flask import request
from flask import url_for
import uuid

import json
import logging

# Date handling 
import arrow # Replacement for datetime, based on moment.js
# import datetime # But we still need time
from dateutil import tz  # For interpreting local times

# OAuth2  - Google library implementation for convenience
from oauth2client import client
import httplib2   # used in oauth2 flow

# Google API for services 
from apiclient import discovery

# Mongo database
import pymongo
from pymongo import MongoClient

# My modules
import timeblock
from free import freemaker

###
# Globals
###
import config
if __name__ == "__main__":
    CONFIG = config.configuration()
else:
    CONFIG = config.configuration(proxied=True)

app = flask.Flask(__name__)
app.debug=CONFIG.DEBUG
app.logger.setLevel(logging.DEBUG)
app.secret_key=CONFIG.SECRET_KEY

SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'
CLIENT_SECRET_FILE = CONFIG.GOOGLE_KEY_FILE  ## You'll need this
APPLICATION_NAME = 'MeetMe class project'

MONGO_CLIENT_URL = "mongodb://{}:{}@{}:{}/{}".format(
    CONFIG.DB_USER,
    CONFIG.DB_USER_PW,
    CONFIG.DB_HOST, 
    CONFIG.DB_PORT, 
    CONFIG.DB)

try: 
    dbclient = MongoClient(MONGO_CLIENT_URL)
    db = getattr(dbclient, CONFIG.DB)
    collection0 = db.hashcodes
    collection1 = db.startendtimes
    collection2 = db.timeblocks

except:
    print("Failure opening database.  Is Mongo running? Correct password?")
    sys.exit(1)

#############################
#
#  Pages (routed from URLs)
#
#############################

@app.route("/")
@app.route("/index")
def index():
  app.logger.debug("Entering index")
  init_session_values()
  return render_template('index.html')

@app.route("/choose")
def choose():
    ## We'll need authorization to list calendars 
    ## I wanted to put what follows into a function, but had
    ## to pull it back here because the redirect has to be a
    ## 'return' 
    app.logger.debug("Checking credentials for Google calendar access")
    credentials = valid_credentials()
    if not credentials:
      app.logger.debug("Redirecting to authorization")
      return flask.redirect(flask.url_for('oauth2callback'))

    gcal_service = get_gcal_service(credentials)
    app.logger.debug("Returned from get_gcal_service")
    flask.g.calendars = list_calendars(gcal_service)
    return render_template('index.html')

# Invitation page
@app.route("/invitation", methods=["POST"])
def invitation():

  # Hidden Forms
  flask.g.freeblocks = request.form.getlist("freeblocks")
  invitation = flask.request.form.get("invite")
  flask.g.invitation = invitation
  if request.form.get("invite_num") != None:
    flask.g.invite_num = int(request.form.get("invite_num"))

  flask.g.names = request.form.getlist("names")
  flask.g.urls = []
  for name in flask.g.names:
    flask.g.urls.append(url_for("invitation", _external=True) + "/" + name)

  # Accessing the database
  flask.g.memo1 = get_memos(0)
  flask.g.memo2 = get_memos(1)
  flask.g.memo3 = get_memos(2)

  return render_template(invitation)

# For invited users
@app.route("/invitation/<token>")
def invite(token):
  flask.g.token = token
  # This really needs to do most of what is in display

  # Google Auth
  app.logger.debug("Checking credentials for Google calendar access")
  credentials = valid_credentials()
  if not credentials:
    app.logger.debug("Redirecting to authorization")
    return flask.redirect(flask.url_for('oauth2callback'))

  gcal_service = get_gcal_service(credentials)
  app.logger.debug("Returned from get_gcal_service")
  flask.g.calendars = list_calendars(gcal_service)

  return render_template("invitee.html")

@app.route("/display", methods=['POST'])
def display():
  """
  Displays busy time events
  """
  # Accessing the database to hold data for invitations
  flask.g.memo1 = get_memos(0)
  flask.g.memo2 = get_memos(1)
  flask.g.memo3 = get_memos(2)
  #mcode = random.randint(1, 100000)

  # For comparison
  daterange = flask.session['daterange']
  timerange = flask.session['timerange']
  ar_dict = arrowizer(timerange, daterange)
  # Example: ar_dict = "begin_date": "2017-11-18T09:00:00-08:00", "end_date": "2017-11-24T17:00:00-08:00"

  #add_ranges(daterange, timerange, mcode)

  # Getting Google credentials and calendar
  credentials = valid_credentials()
  if not credentials:
    return flask.redirect(flask.url_for('oauth2callback'))
  gcal_service = get_gcal_service(credentials)
  flask.g.calendars = list_calendars(gcal_service)

  # Grabs events in selected calendars
  flask.g.checked = request.form.getlist("calendarcheck")

  # Algorithm for displaying results
  busy_list = []
  for calendar in flask.g.checked:
    for cal in flask.g.calendars:
      if calendar == cal['summary']:
        calendar = cal
    # Obtain calendar id for that calendar's events
    cal_id = calendar['id']

    # Obtain events for that calendar
    starter = ar_dict["begin_date"]
    ender = ar_dict["end_date"]
    eventsResult = gcal_service.events().list(
        calendarId=cal_id, timeMin=starter, timeMax=ender, maxResults=10, singleEvents=True,
        orderBy='startTime').execute()
    events = eventsResult.get('items', [])

    # Put each busy event into busy list
    for event in events:
      if event.get("transparency") == None:
        summary = event['summary']
        desc = event.get('description', "No description.")
        # Double checks for None values for times
        start = event.get('start')
        start = start.get('dateTime')
        end = event.get('end')
        end = end.get('dateTime')

        # Checks that the event is within the date/time constraints and is not None
        if start != None and end != None:
            busy_list.append(
                  { "Calendar": calendar['summary'],
                    'Summary': summary,
                    "Description": desc,
                    "Start Time": start,
                    "End Time": end
                    })
  busy_list = within_time(busy_list, ar_dict["begin_date"], ar_dict["end_date"])
  free_list = freemaker(busy_list, ar_dict["begin_date"], ar_dict["end_date"])
  tb_list = []
  for event in busy_list:
    tb = timeblock.Timeblock(event["Summary"], event["Start Time"], event["End Time"])
    tb_list.append(tb)
  busy_list = tb_list
  flask.g.events = busy_list # busy times within datetime range
  flask.g.free = free_list # free times within datetime range
  return render_template('index.html')

@app.errorhandler(404)
def error_404(e):
    app.logger.warning("++ 404 error: {}".format(e))
    return flask.render_template('404.html'), 404

####
#
#  Google calendar authorization:
#      Returns us to the main /choose screen after inserting
#      the calendar_service object in the session state.  May
#      redirect to OAuth server first, and may take multiple
#      trips through the oauth2 callback function.
#
#  Protocol for use ON EACH REQUEST: 
#     First, check for valid credentials
#     If we don't have valid credentials
#         Get credentials (jump to the oauth2 protocol)
#         (redirects back to /choose, this time with credentials)
#     If we do have valid credentials
#         Get the service object
#
#  The final result of successful authorization is a 'service'
#  object.  We use a 'service' object to actually retrieve data
#  from the Google services. Service objects are NOT serializable ---
#  we can't stash one in a cookie.  Instead, on each request we
#  get a fresh serivce object from our credentials, which are
#  serializable. 
#
#  Note that after authorization we always redirect to /choose;
#  If this is unsatisfactory, we'll need a session variable to use
#  as a 'continuation' or 'return address' to use instead. 
#
####

def valid_credentials():
    """
    Returns OAuth2 credentials if we have valid
    credentials in the session.  This is a 'truthy' value.
    Return None if we don't have credentials, or if they
    have expired or are otherwise invalid.  This is a 'falsy' value. 
    """
    if 'credentials' not in flask.session:
      return None

    credentials = client.OAuth2Credentials.from_json(
        flask.session['credentials'])

    if (credentials.invalid or
        credentials.access_token_expired):
      return None
    return credentials

def get_gcal_service(credentials):
  """
  We need a Google calendar 'service' object to obtain
  list of calendars, busy times, etc.  This requires
  authorization. If authorization is already in effect,
  we'll just return with the authorization. Otherwise,
  control flow will be interrupted by authorization, and we'll
  end up redirected back to /choose *without a service object*.
  Then the second call will succeed without additional authorization.
  """
  app.logger.debug("Entering get_gcal_service")
  http_auth = credentials.authorize(httplib2.Http())
  service = discovery.build('calendar', 'v3', http=http_auth)
  app.logger.debug("Returning service")
  return service

@app.route('/oauth2callback')
def oauth2callback():
  """
  The 'flow' has this one place to call back to.  We'll enter here
  more than once as steps in the flow are completed, and need to keep
  track of how far we've gotten. The first time we'll do the first
  step, the second time we'll skip the first step and do the second,
  and so on.
  """
  app.logger.debug("Entering oauth2callback")
  flow =  client.flow_from_clientsecrets(
      CLIENT_SECRET_FILE,
      scope= SCOPES,
      redirect_uri=flask.url_for('oauth2callback', _external=True))
  ## Note we are *not* redirecting above.  We are noting *where*
  ## we will redirect to, which is this function. 
  
  ## The *second* time we enter here, it's a callback 
  ## with 'code' set in the URL parameter.  If we don't
  ## see that, it must be the first time through, so we
  ## need to do step 1. 
  app.logger.debug("Got flow")
  if 'code' not in flask.request.args:
    app.logger.debug("Code not in flask.request.args")
    auth_uri = flow.step1_get_authorize_url()
    return flask.redirect(auth_uri)
    ## This will redirect back here, but the second time through
    ## we'll have the 'code' parameter set
  else:
    ## It's the second time through ... we can tell because
    ## we got the 'code' argument in the URL.
    app.logger.debug("Code was in flask.request.args")
    auth_code = flask.request.args.get('code')
    credentials = flow.step2_exchange(auth_code)
    flask.session['credentials'] = credentials.to_json()
    ## Now I can build the service and execute the query,
    ## but for the moment I'll just log it and go back to
    ## the main screen
    app.logger.debug("Got credentials")
    return flask.redirect(flask.url_for('choose'))

#####
#
#  Option setting:  Buttons or forms that add some
#     information into session state.  Don't do the
#     computation here; use of the information might
#     depend on what other information we have.
#   Setting an option sends us back to the main display
#      page, where we may put the new information to use. 
#
#####

@app.route('/setrange', methods=['POST'])
def setrange():
    """
    User chose a date range with the bootstrap daterange
    widget.
    """
    app.logger.debug("Entering setrange")  
    flask.flash("Set range: '{}'".format(
      request.form.get('daterange')))
    daterange = request.form.get('daterange')
    timerange = request.form.get('timerange')

    flask.session['daterange'] = daterange
    flask.session['timerange'] = timerange

    daterange_parts = daterange.split()
    flask.session['begin_date'] = interpret_date(daterange_parts[0])
    flask.session['end_date'] = interpret_date(daterange_parts[2])

    timerange_parts = timerange.split()
    flask.session['begin_time'] = interpret_time(timerange_parts[0])
    flask.session['end_time'] = interpret_time(timerange_parts[2])

    app.logger.debug("Setrange parsed {} - {}  dates as {} - {}".format(
      daterange_parts[0], daterange_parts[1], 
      flask.session['begin_date'], flask.session['end_date']))
    return flask.redirect(flask.url_for("choose"))

####
#
#   Initialize session variables 
#
####

def init_session_values():
    """
    Start with some reasonable defaults for date and time ranges.
    Note this must be run in app context ... can't call from main. 
    """
    # Default date span = tomorrow to 1 week from now
    now = arrow.now('local')     # We really should be using tz from browser
    tomorrow = now.replace(days=+1)
    nextweek = now.replace(days=+7)
    flask.session["begin_date"] = tomorrow.floor('day').isoformat()
    flask.session["end_date"] = nextweek.ceil('day').isoformat()
    flask.session["daterange"] = "{} - {}".format(
        tomorrow.format("MM/DD/YYYY"),
        nextweek.format("MM/DD/YYYY"))
    # Default time span each day, 8 to 5
    nine_am = now.replace(hour=9, minute=0)
    five_pm = now.replace(hour=17, minute=0)
    flask.session["begin_time"] = nine_am.isoformat()
    flask.session["end_time"] = five_pm.isoformat()
    flask.session["timerange"] = "{} - {}".format(
        nine_am.format("HH:mm"),
        five_pm.format("HH:mm"))
    return

def interpret_time( text ):
    """
    Read time in a human-compatible format and
    interpret as ISO format with local timezone.
    May throw exception if time can't be interpreted. In that
    case it will also flash a message explaining accepted formats.
    """
    app.logger.debug("Decoding time '{}'".format(text))
    time_formats = ["ha", "h:mma",  "h:mm a", "H:mm"]
    try: 
        as_arrow = arrow.get(text, time_formats).replace(tzinfo=tz.tzlocal())
        as_arrow = as_arrow.replace(year=2016) #HACK see below
        app.logger.debug("Succeeded interpreting time")
    except:
        app.logger.debug("Failed to interpret time")
        flask.flash("Time '{}' didn't match accepted formats 13:30 or 1:30pm"
              .format(text))
        raise
    return as_arrow.isoformat()
    #HACK #Workaround
    # isoformat() on raspberry Pi does not work for some dates
    # far from now.  It will fail with an overflow from time stamp out
    # of range while checking for daylight savings time.  Workaround is
    # to force the date-time combination into the year 2016, which seems to
    # get the timestamp into a reasonable range. This workaround should be
    # removed when Arrow or Dateutil.tz is fixed.
    # FIXME: Remove the workaround when arrow is fixed (but only after testing
    # on raspberry Pi --- failure is likely due to 32-bit integers on that platform)

def interpret_date( text ):
    """
    Convert text of date to ISO format used internally,
    with the local time zone.
    """
    try:
      as_arrow = arrow.get(text, "MM/DD/YYYY").replace(
          tzinfo=tz.tzlocal())
    except:
        flask.flash("Date '{}' didn't fit expected format 12/31/2001")
        raise
    return as_arrow.isoformat()

def next_day(isotext):
    """
    ISO date + 1 day (used in query to Google calendar)
    """
    as_arrow = arrow.get(isotext)
    return as_arrow.replace(days=+1).isoformat()

####
#
#  Functions (NOT pages) that return some information
#
####

def within_time(busy_list, begin, end):
  """
  Takes a list of busy times and checks to see if they are within the proper time range
  Args:
    busy_list: a list of busy events within a date range (with overlapping in/out of dates)
    begin: start datetime of daterange
    end: end datetime of daterange
  Returns:
    busy_list: updated list that has events that are only in datetime range
  """
  # start_time datetime object
  begin_time = begin.time()
  # end_time datetime object
  end_time = end.time()

  for event in busy_list:
    ending = arrow.get(event["End Time"])
    ending = ending.time()
    beginning = arrow.get(event["Start Time"])
    beginning = beginning.time()
    # Compare datetime for lack of overlap
    if ending < begin_time:
      busy_list.remove(event)
    if beginning > end_time:
      busy_list.remove(event)
    # else keep the event in the list
  return busy_list

def arrowizer(timerange, daterange):
  """
  Turns the timerange and daterange into arrow objects
  Args:
    timerange: range of times selected by the user
    daterange: range of dates selected by the user
  Returns:
    ar_dict: a dictionary of arrow objects consisting of start and end
    datetime
  """
  # Grab time values for date modification
  timerange_parts = timerange.split()
  begin_time = timerange_parts[0]
  end_time = timerange_parts[2]
  begin_hour = int(begin_time[:2])
  end_hour = int(end_time[:2])
  begin_minute = int(begin_time[3:])
  end_minute = int(end_time[3:])

  # Grab date values
  daterange_parts = daterange.split()
  begin_date = interpret_date(daterange_parts[0])
  end_date = interpret_date(daterange_parts[2])

  # Turn each string into an arrow object, then replace with 
  begin_date = arrow.get(begin_date)
  begin_date = begin_date.replace(hour=begin_hour, minute=begin_minute)
  end_date = arrow.get(end_date)
  end_date = end_date.replace(hour=end_hour, minute=end_minute)

  # Add each arrow object to the dictionary
  ar_dict = {
      "begin_date": begin_date,
      "end_date": end_date
    }
  return ar_dict
  
def list_calendars(service):
    """
    Given a google 'service' object, return a list of
    calendars.  Each calendar is represented by a dict.
    The returned list is sorted to have
    the primary calendar first, and selected (that is, displayed in
    Google Calendars web app) calendars before unselected calendars.
    """
    app.logger.debug("Entering list_calendars")  
    calendar_list = service.calendarList().list().execute()["items"]
    result = [ ]
    for cal in calendar_list:
        kind = cal["kind"]
        id = cal["id"]
        if "description" in cal: 
            desc = cal["description"]
        else:
            desc = "(no description)"
        summary = cal["summary"]
        # Optional binary attributes with False as default
        selected = ("selected" in cal) and cal["selected"]
        primary = ("primary" in cal) and cal["primary"]

        result.append(
          { "kind": kind,
            "id": id,
            "desc": desc,
            "summary": summary,
            "selected": selected,
            "primary": primary
            })
    return sorted(result, key=cal_sort_key)

def cal_sort_key( cal ):
    """
    Sort key for the list of calendars:  primary calendar first,
    then other selected calendars, then unselected calendars.
    (" " sorts before "X", and tuples are compared piecewise)
    """
    if cal["selected"]:
       selected_key = " "
    else:
       selected_key = "X"
    if cal["primary"]:
       primary_key = " "
    else:
       primary_key = "X"
    return (primary_key, selected_key, cal["summary"])

def get_memos(num):
    """
    Returns all memos in the database, in a form that
    can be inserted directly in the 'session' object.
    Args:
      num: 0-2 that designates which collection it goes to
    0 goes to hashcodes
    1 goes to startendtimes
    2+ or < 0 goes to timeblocks
    """
    records = [ ]
    if num == 0:
      for record in collection0.find( { "type": "dated_memo" } ):
        record['date'] = arrow.get(record['date']).isoformat()
        del record['_id']
        records.append(record)
    if num == 1:
      for record in collection1.find( { "type": "dated_memo" } ):
        record['date'] = arrow.get(record['date']).isoformat()
        del record['_id']
        records.append(record)
    else:
      for record in collection2.find( { "type": "dated_memo" } ):
        record['date'] = arrow.get(record['date']).isoformat()
        del record['_id']
        records.append(record)
    return records 

def add_ranges(daterange, timerange):
  """
  Adds daterange and timerange to the database for the meeting
  """
  record = { "daterange": daterange,
           "timerange": timerange
          }
  collection1.insert(record)
  return

def add_timeblocks(timeblock_list):
  """
  Adds daterange and timerange to the database for the meeting
  """
  for timeblock in timeblock_list:
    record = { "daterange": daterange,
             "timerange": timerange
            }
    collection2.insert(record)
  return

#################
#
# Functions used within the templates
#
#################

@app.template_filter( 'fmtdate' )
def format_arrow_date( date ):
    try: 
        normal = arrow.get( date )
        return normal.format("ddd MM/DD/YYYY")
    except:
        return "(bad date)"

@app.template_filter( 'fmttime' )
def format_arrow_time( time ):
    try:
        normal = arrow.get( time )
        return normal.format("HH:mm")
    except:
        return "(bad time)"
    
#############

if __name__ == "__main__":
  # App is created above so that it will
  # exist whether this is 'main' or not
  # (e.g., if we are running under green unicorn)
  app.run(port=CONFIG.PORT,host="0.0.0.0")