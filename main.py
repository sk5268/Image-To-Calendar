from __future__ import print_function
import os.path
import requests
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Define the Google Calendar API scope
SCOPES = ['https://www.googleapis.com/auth/calendar']
cid = 'your_calendar_id_here'  # Replace with your actual calendar ID

# Function to perform OCR on the provided image file
def ocr_space_file(filename):
    payload = {'isOverlayRequired': 'True',
               'apikey': 'your_ocr_api_key_here',  # Replace with your actual OCR API key
               'language': 'eng',
               }
    with open(filename, 'rb') as f:
        r = requests.post('https://api.ocr.space/parse/image',
                          files={filename: f},
                          data=payload,
                          )
    return r.content.decode()

# Perform OCR on the specified image file
response = ocr_space_file(filename='test.jpg')

# Save the OCR result to a JSON file
with open('result.json', 'w') as f:
    json.dump(json.loads(response), f)

# Load the JSON data from the file
with open('result.json', 'r') as f:
    data = json.load(f)

# Parse the OCR data to create a timetable matrix
ttmat = []
eve = data['ParsedResults'][0]['ParsedText'].split()
print(eve)
x = 0

for i in range(5):
    a = []
    for j in range(7):  
        a.append(eve[x])
        x += 7
        x %= 41
    ttmat.append(a)

# Function to create an event for Google Calendar
def eventmanager(i, j, k, t):
    if ((j+9) >= 13):
        j += 1
    if ((k+10) >= 13):
        k += 1

    sdt = '2023-08-' + '%02d' % (i+21) + 'T' + '%02d' % (j+9) + ':00:00+05:30'
    edt = '2023-08-' + '%02d' % (i+21) + 'T' + '%02d' % (j+k+10) + ':00:00+05:30'

    event = {
        'summary': t,
        'start': {
            'dateTime': sdt,
            'timeZone': 'Asia/Kolkata',
        },
        'end': {
            'dateTime': edt,
            'timeZone': 'Asia/Kolkata',
        },
        'recurrence': [
            'RRULE:FREQ=WEEKLY;COUNT=19'
        ],
        'reminders': {
            'useDefault': True,
        },
    }
    
    return event

# Main function to authenticate and create calendar events
def main():
    creds = None
    
    # Load credentials from the token file if it exists
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If there are no valid credentials, prompt the user to log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for future use
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        # Build the Google Calendar service
        service = build('calendar', 'v3', credentials=creds)

        # Iterate through the timetable matrix and create events
        for i in range(5):
            for j in range(7):
                k = 0
                if ttmat[i][j] == 'z':
                    pass
                else:
                    if j <= 5 and ttmat[i][j] == ttmat[i][j+1]:
                        k = 1
                    if j >= 1 and ttmat[i][j] == ttmat[i][j-1]:
                        pass
                    else:
                        event = service.events().insert(calendarId=cid, body=eventmanager(i, j, k, ttmat[i][j])).execute()
    except HttpError as error:
        print('An error occurred: %s' % error)

# Uncomment the following line to run the main function
# main()
