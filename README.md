# proj7-Gcal
Snarf appointment data from a selection of a user's Google calendars 

# Contact Information:
- Name: Maxwell Logan
- Email: mlogan@uoregon.edu

## Program Description

Provided code for the authorization (oauth2) protocol for Google
calendars. There is also a picker for a date range. 
The program allows the user to choose calendars (a single
user may have several Google calendars, one of which is the 'primary'
calendar) and list 'blocking'  (non-transparent)
appointments between a start date and an end date
for some subset of them. Displays busy times and free times within
the designated date and time ranges. Allows the user to set up a 
meeting and generates urls for invitees. Invitees are redirected to 
a modified version of the starting page, which allows them to compare 
their calendar to the selected meeting times.

## Credits

- Google API documentation and examples
- Former project code