import argparse
import json

import clashroyale
import datetime
import time

import sys
import os
import gspread
from gspread import WorksheetNotFound

from oauth2client.service_account import ServiceAccountCredentials
from clan import Clan
from clan import WarLog
from pickler import saveAsPickled, loadPickled


# File to store your royal api dev key or any other you may need
tokensJsonFileName = 'tokens.json'

# Mostly for debugging.  If >Clan size, then all players are obtained.
# For example, setting to 2 then only 2 players are retrieved, inspect the data, etc
# for faster debugging
PLAYER_FETCH_COUNT = 50

# output column names for the basic clan info
clanInfoColumnNames = ['Player Name', 'Player Tag', 'Last Played', 'Days Since Last Played',
                       'Donations', 'Donations Received', 'Donations Percent']
clanWarInfoColumnNames = ['Player Name', 'War Date', 'War Final Battles Missed',
                          'War Final Battles Played', 'War Final Battle Wins', 'War Collection Day Battles Missed',
                          'War Collection Day Battles Played', 'War Cards Earned']

# -----------------------------------------------------------------------------
def getGoogleClient():
    GOOGLE_API_SCOPE = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name('creds.json', GOOGLE_API_SCOPE)
    gc = gspread.authorize(credentials)
    return gc


# -----------------------------------------------------------------------------
def writeToSheet(tokens, theClan):
    spreadSheetId = getGoogleSheetId(tokens)
    spreadsheet = getGoogleClient().open_by_key(spreadSheetId)

    worksheetName = datetime.date.today().__str__()
    try:
        worksheet = spreadsheet.worksheet(worksheetName)
    except WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=worksheetName, rows="100", cols="20")

    # write header
    rangeMax = clanInfoColumnNames.__len__() + 1;
    for colIndex in range(1, rangeMax):
        worksheet.update_cell(1, colIndex, clanInfoColumnNames[colIndex-1])

    cellList = worksheet.range(2, 1, PLAYER_FETCH_COUNT+10, clanInfoColumnNames.__len__())
    index = 0
    for player in theClan.players:
        cellList[index].value = player.name
        cellList[index+1].value = player.tag
        cellList[index+2].value = player.lastPlayedTime
        cellList[index+3].value = player.daysSinceLastPlayed
        cellList[index+4].value = player.donations
        cellList[index+5].value = player.donationsReceived
        cellList[index+6].value = player.donationsPercent
        index = index + clanInfoColumnNames.__len__()

    worksheet.update_cells(cellList)

# -----------------------------------------------------------------------------
# Hack to get the paths to work on windows to find any input or output files
def addSubDirsToPath():
    excludeList = ['.git', '.idea', 'venv', '__pycache__', 'output']
    a_dir = os.path.dirname(sys.modules['__main__'].__file__)
    for name in os.listdir(a_dir):
        if os.path.isdir(name):
            pathToAdd = a_dir + "\\" + name
            if name not in excludeList:
                sys.path.append(pathToAdd)


# -----------------------------------------------------------------------------
def getTokens():
    try:
        with open(tokensJsonFileName) as f:
            data = json.load(f)
    except:
        print("Failure:{} must exist and must contain json with key={}:<royal dev key>".format(tokensJsonFileName, "royale-dev-key"))
        return None

    return data


# -----------------------------------------------------------------------------
def getRoyalDevKey(tokensJson):
    if tokensJson is not None and tokensJson['royale-dev-key'] is not None:
        return tokensJson['royale-dev-key']


# -----------------------------------------------------------------------------
def getGoogleSheetId(tokensJson):
    if tokensJson is not None and tokensJson['google-sheet-id'] is not None:
        return tokensJson['google-sheet-id']


# -----------------------------------------------------------------------------
def writeOutputCsv(theClan):
    rowFormat = "{},{},{},{},{},{},{}\n"
    headerRow = ','.join(clanInfoColumnNames)
    with open('output/clanplayerinfo.csv', 'w', encoding='UTF-8', newline='') as out:
        out.write(headerRow)
        for player in theClan.players:
            out.write(rowFormat.format(player.name,
                                       player.tag,
                                       player.lastPlayedTime,
                                       player.daysSinceLastPlayed,
                                       player.donations,
                                       player.donationsReceived,
                                       player.donationsPercent,
                                       ))

    headerRow = ','.join(clanWarInfoColumnNames)
    with open('output/clanwarinfo.csv', 'w', encoding='UTF-8', newline='') as out:
        out.write(headerRow)
        for player in theClan.players:
            for warLog in player.warLogs:
                out.write(rowFormat.format(player.name,
                                           warLog.warDate,
                                           warLog.numFinalDayBattlesMissed,
                                           warLog.finalDayBattlesPlayed,
                                           warLog.finalDayWins,
                                           warLog.numCollectDayBattlesMissed,
                                           warLog.collectionDayBattlesPlayed,
                                           warLog.cardsEarned
                                           ))


# -----------------------------------------------------------------------------
def getDaysFromNow(timeStamp):
    if timeStamp > 0:
        lastPlayedDateTime = datetime.datetime.fromtimestamp(timeStamp)
        todayDateTime = datetime.datetime.fromtimestamp(time.time())
        diff = todayDateTime - lastPlayedDateTime
        daysSincePlayed = diff.days
    else:
        daysSincePlayed = "99999"

    return daysSincePlayed


# -----------------------------------------------------------------------------
def fetchPlayerBattlesWithRetries(client, playerTag, retries=10, sleepInSec=2):
    for count in range(retries):
        try:
            battles = client.get_player_battles(playerTag)
            return battles
        except:
            print("\tRetrying on {} count={}".format("get_player_battles", count))
            time.sleep(sleepInSec)
            continue

    raise clashroyale.NotResponding()


# -----------------------------------------------------------------------------
def getPlayerWarInfo(clanWarLogs, playerName):
    if clanWarLogs.__len__() == 0:
        return

    warLogList = []
    for clanWarLog in clanWarLogs:
        if clanWarLog['createdDate'] is not None:
            createdDate = clanWarLog['createdDate']

            if clanWarLog['participants'] is not None:
                for participant in clanWarLog['participants']:
                    name = participant['name']
                    if name == playerName:
                        cardsEarned = participant['cardsEarned']
                        finalDayBattlesPlayed = participant['battlesPlayed']
                        wins = participant['wins']
                        collectionDayBattlesPlayed = participant['collectionDayBattlesPlayed']
                        warLog = WarLog(datetime.datetime.fromtimestamp(createdDate),
                                        cardsEarned, finalDayBattlesPlayed, wins, collectionDayBattlesPlayed)
                        warLogList.append(warLog)

    return warLogList


# -----------------------------------------------------------------------------
def updateClanPlayersData(client, theClan, clanWarLogs):
    # for each player, get there battles which contains the game time
    # using the newest game time as the "last played" time
    numPlayersToGet = PLAYER_FETCH_COUNT
    for player in theClan.players:
        try:
            player.battles = fetchPlayerBattlesWithRetries(client, player.tag)
        except:
            print("\tFailed to get player battles")
            continue

        if player.battles.__len__() == 0:
            player.daysSinceLastPlayed = 99999
        else:
            for battle in player.battles:
                lastPlayedPosixTime = battle['utcTime']
                if lastPlayedPosixTime > player.lastPlayedTime:
                    player.lastPlayedTime = lastPlayedPosixTime  # update the players last played time

            player.daysSinceLastPlayed = getDaysFromNow(player.lastPlayedTime)

        print("{}:{}".format(player.name, player.daysSinceLastPlayed))

        playerWarLogs = getPlayerWarInfo(clanWarLogs, player.name)
        if playerWarLogs is None:
            print("\tWar:{}".format("Not Participating"))
            continue

        player.warLogs = playerWarLogs
        for warLog in player.warLogs:
            print("\tWar:earned:{}, played:{}, finalDayWins:{}, collected:{}, collectDayMissed:{}, finalDayBattlesMissed:{}"
                  .format(warLog.cardsEarned, warLog.finalDayBattlesPlayed, warLog.finalDayWins,
                          warLog.collectionDayBattlesPlayed, warLog.numCollectDayBattlesMissed,
                          warLog.numFinalDayBattlesMissed))

        numPlayersToGet = numPlayersToGet - 1
        if numPlayersToGet == 0:
            break


# -----------------------------------------------------------------------------
def main(clanTag, useTestData):
    print("------------------------------------------------------------------------")
    print("CLASH Running...")
    print()

    clan = None
    tokens = getTokens()
    if tokens is None:
        exit(1)

    pickledFilename = 'output/pickled-clan.bin'

    # if we have saved test data, use it
    if useTestData is True:
        clan = loadPickled(pickledFilename)

    if clan is not None:
        writeOutputCsv(clan)
        writeToSheet(tokens, clan)
        exit(0)

    # at this point, we need gather all the data from the servers
    royalDevKey = getRoyalDevKey(tokens)
    if royalDevKey is None:
        exit(1)

    try:
        client = clashroyale.RoyaleAPI(royalDevKey)
    except:
        print("\tFailure: Unable to get the royal client")
        exit(2)

    # Get the clans war info
    try:
        clanWarLogs = client.get_clan_war_log(clanTag)
    except:
        print("\tRetrying on {}".format("get_clan_war_log"))
        clanWarLogs = client.get_clan_war_log(clanTag)

    # Get the clan info
    try:
        clanInfoJson = client.get_clan(clanTag)
    except:
        print("\tRetrying on {}".format("get_clan"))
        clanInfoJson = client.get_clan(clanTag)

    # theClan = Clan(clanInfoJson.raw_data['name'], clanInfoJson.raw_data['tag'])
    clan = Clan.clanFromClanJson(clanInfoJson)

    # Get the members of the clan and their info
    updateClanPlayersData(client, clan, clanWarLogs)

    # save test data for faster testing
    saveAsPickled(pickledFilename, clan)

    # write the output to a csv
    writeOutputCsv(clan)

    # put the data in our google sheet
    writeToSheet(tokens, clan)

    print()
    print("------------------------------------------------------------------------")
    print("CLASH Ending...")

    exit(0)


# -----------------------------------------------------------------------------
def str2bool(v):
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


if __name__ == '__main__':
    addSubDirsToPath()

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--clantag",
                        dest="clantag",
                        required=True,
                        help="Clan Tag Value")
    parser.add_argument("-td", "--testdata",
                        type=str2bool,
                        nargs='?',
                        dest="useTestData",
                        required=False,
                        default=False,
                        help="Use pickled test data if available")
    args = parser.parse_args()

    main(args.clantag, args.useTestData)
