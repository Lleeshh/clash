import datetime

from gspread import WorksheetNotFound
from oauth2client.service_account import ServiceAccountCredentials
import gspread
from tokens import Tokens


# -----------------------------------------------------------------------------
def getGoogleClient():
    GOOGLE_API_SCOPE = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name('creds.json', GOOGLE_API_SCOPE)
    gc = gspread.authorize(credentials)
    return gc


# -----------------------------------------------------------------------------
def writeGoogleSheets(tokens: Tokens, clanData, clanInfoColumnNames, clanWarInfoColumnNames):
    if tokens is None:
        raise Exception("Tokens list not provided")

    spreadSheetId = tokens.getGoogleSheetId()
    spreadsheet = getGoogleClient().open_by_key(spreadSheetId)

    writeGoogleSheetMemberStats(spreadsheet, clanData, clanInfoColumnNames)
    writeGoogleSheetMemberWarStats(spreadsheet, clanData, clanWarInfoColumnNames)


# -----------------------------------------------------------------------------
def writeGoogleSheetMemberStats(spreadsheet, theClan, clanInfoColumnNames):
    worksheetName = "memberstats-" + datetime.date.today().__str__()
    try:
        worksheet = spreadsheet.worksheet(worksheetName)
    except WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=worksheetName, rows="100", cols="20")

    numColumns = clanInfoColumnNames.__len__()
    rangeMax = numColumns + 1;
    for colIndex in range(1, rangeMax):
        worksheet.update_cell(1, colIndex, clanInfoColumnNames[colIndex-1])

    cellList = worksheet.range(2, 1, 50+10, numColumns)
    index = 0
    for player in theClan.players:
        cellList[index].value = player.name
        cellList[index+1].value = player.tag
        cellList[index+2].value = player.lastPlayedTime
        cellList[index+3].value = player.daysSinceLastPlayed
        cellList[index+4].value = player.donations
        cellList[index+5].value = player.donationsReceived
        cellList[index+6].value = player.donationsPercent
        cellList[index+7].value = player.percentWarBattlesMissed
        index = index + numColumns

    worksheet.update_cells(cellList)


# -----------------------------------------------------------------------------
def writeGoogleSheetMemberWarStats(spreadsheet, theClan, clanWarInfoColumnNames):
    worksheetName = "warstats"
    try:
        worksheet = spreadsheet.worksheet(worksheetName)
    except WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=worksheetName, rows="100", cols="20")

    numColumns = clanWarInfoColumnNames.__len__()
    rangeMax = numColumns + 1;
    for colIndex in range(1, rangeMax):
        worksheet.update_cell(1, colIndex, clanWarInfoColumnNames[colIndex-1])

    cellList = worksheet.range(2, 1, 60*10, numColumns)
    index = 0
    for player in theClan.players:
        for warLog in player.warLogs:
            cellList[index].value = player.name
            cellList[index+1].value = warLog.warDate
            cellList[index+2].value = warLog.numFinalDayBattlesMissed
            cellList[index+3].value = warLog.finalDayBattlesPlayed
            cellList[index+4].value = warLog.finalDayWins
            cellList[index+5].value = warLog.numCollectDayBattlesMissed
            cellList[index+6].value = warLog.collectionDayBattlesPlayed
            cellList[index+7].value = warLog.cardsEarned
            index = index + numColumns

    worksheet.update_cells(cellList)

