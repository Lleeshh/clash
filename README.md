# Clash Royal Clan Info
Script to fetch Clash Royal (TM) info via the RoyalApi (TM).

## Setup
1. Python 3.x and greater
1. Get a RoyalApi Dev key (see the RoyalApi.com site https://docs.royaleapi.com/#/authentication)
1. Get your clan tag (visit royalapi.com)
1. Get setup with google api (http://gspread.readthedocs.org/en/latest/oauth2.html)
1. Google credentials into creds.json placed in the root of the project
1. Create a tokens.json (see example below)
1. pip install clashroyale
1. pip install gspread (wrapper/helper for google sheets api)

## Run
1. Add a command line parmaeter such as -c <clan tag> when running you
1. Run as ```python clash.py -c 1234abcd```
1. From IDE, runs the clash.py

## Example: tokens.json
```javascript
{
  "royale-dev-key": "my key from royalapi.com",
  "google-sheet-id": "my sheet id from the sheet url"
}
```
