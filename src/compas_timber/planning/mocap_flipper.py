""" run pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib """

import os.path
from compas.data import json_load, json_dump
from compas.geometry import Vector
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

# The ID and range of a sample spreadsheet.
SAMPLE_SPREADSHEET_ID = "13c2DEVT9_uQ5VSQ_Dwb6qJXlzbRwSSO6T1FpB0bKZEM"
SAMPLE_RANGE_NAME = "FABRICATION!B3:P"


def main():
  """Shows basic usage of the Sheets API.
  Prints values from a sample spreadsheet.
  """
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          ".secrets/credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())

  try:


    service = build("sheets", "v4", credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()
    result = (
        sheet.values()
        .get(spreadsheetId=SAMPLE_SPREADSHEET_ID, range=SAMPLE_RANGE_NAME)
        .execute()
    )
    values = result.get("values", [])

    if not values:
      print("No data found.")
      return
    string = r"C:\Users\obucklin\repos\mas-t2-2324\production\fabrication\Module_42\btlx\Module_42_MoCap.json"
    string_out = string[:-5] + "_flipped.json"

    module = json_load(string).copy()
    module_id = list(module.keys())[0].split("_")[0]
    start, end = get_module_range(values, module_id)

    print(start, end)
    for row in values[start:end]:
        beam_id = module_id + "_" + row[1]
        print("Beam ID: ", beam_id)
        if row[13] == 'TRUE':
            print("flipping beam")
            beam = module.get(beam_id, None)
            if beam:
                frame = module[beam_id].get('beam_frame_relative_to_MoCap_Frame', None)
                # print("frame before", frame)
                if frame:
                    frame_after = frame.copy()
                    frame_after.yaxis = frame.yaxis * -1

                    module[beam_id]['beam_frame_relative_to_MoCap_Frame'] = frame_after
                    # print("frame after", module[beam_id].get('beam_frame_relative_to_MoCap_Frame', None))
    json_dump(module, string_out)




  except HttpError as err:
    print(err)

def get_module_range(data, module_id):
    start, end = None, None
    for i, row in enumerate(data):
        if start is not None and row[0] != "" and row[0][0] == "M":
            end = i
            break
        if row[0][0:3]  == module_id:
            start = i

    return start, end


if __name__ == "__main__":
  main()
