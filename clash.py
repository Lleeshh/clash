import argparse
import datetime
import time

import clashroyale

from clan import Clan
from clan import WarLog
from pickler import saveAsPickled, loadPickled
# File to store your royal api dev key or any other you may need
from sheets import writeGoogleSheets
from tokens import Tokens
from utils import str2bool, addSubDirsToPath, getDaysFromNow, openBrowserTab

tokensJsonFileName = 'tokens.json'
pickledFilename = 'output/pickled-clan.bin'

# Mostly for debugging.  If >Clan size, then all players are obtained.
# For example, 
# setting to 2 then only 2 players are retrieved, inspect the data, etc
# for faster debugging
PLAYER_FETCH_COUNT = 50

# output column names for the basic clan info
clanInfoColumnNames = ['Player Name', 'Player Tag', 'Last Played', 'Days Since Last Played',
                       'Donations', 'Donations Received', 'Donations Percent', 'War Battles Missed %']
clanWarInfoColumnNames = ['Player Name', 'War Date', 'War Final Battles Missed',
                          'War Final Battles Played', 'War Final Battle Wins', 'War Collection Day Battles Missed',
                          'War Collection Day Battles Played', 'War Cards Earned']


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
                                       player.percentWarBattlesMissed
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
            createdDate = datetime.datetime.fromtimestamp(createdDate).__str__()

            if clanWarLog['participants'] is not None:
                for participant in clanWarLog['participants']:
                    name = participant['name']
                    if name == playerName:
                        cardsEarned = participant['cardsEarned']
                        finalDayBattlesPlayed = participant['battlesPlayed']
                        wins = participant['wins']
                        collectionDayBattlesPlayed = participant['collectionDayBattlesPlayed']
                        warLog = WarLog(createdDate, cardsEarned, finalDayBattlesPlayed, wins,
                                        collectionDayBattlesPlayed)
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
            if player.daysSinceLastPlayed is None:
                player.daysSinceLastPlayed = 99999

        print("{}:{}".format(player.name, player.daysSinceLastPlayed))

        playerWarLogs = getPlayerWarInfo(clanWarLogs, player.name)
        if playerWarLogs is None:
            print("\tWar:{}".format("Not Participating"))
            continue

        player.warLogs = playerWarLogs
        player.sortByWarsMissed()
        player.updatePercentWarBattlesMissed()

        for warLog in player.warLogs:
            print(
                "\tWar:earned:{}, played:{}, finalDayWins:{}, collected:{}, collectDayMissed:{}, finalDayBattlesMissed:{}"
                    .format(warLog.cardsEarned, warLog.finalDayBattlesPlayed, warLog.finalDayWins,
                            warLog.collectionDayBattlesPlayed, warLog.numCollectDayBattlesMissed,
                            warLog.numFinalDayBattlesMissed))

        numPlayersToGet = numPlayersToGet - 1
        if numPlayersToGet == 0:
            break

    theClan.sortPlayersByLastPlayed()


def main(clanTag, useTestData, browse):
    print("------------------------------------------------------------------------")
    print("CLASH Running...")
    print()

    clan = None
    tokens = Tokens(tokensJsonFileName)

    # if we have saved test data, use it
    if useTestData is True:
        clan = loadPickled(pickledFilename)

    if clan is not None:
        writeOutputCsv(clan)
        writeGoogleSheets(tokens, clan, clanInfoColumnNames, clanWarInfoColumnNames)
        exit(0)

    # at this point, we need gather all the data from the servers
    royalDevKey = tokens.getRoyalDevKey()
    if royalDevKey is None:
        exit(1)

    clanTagToken = tokens.getClanTag();
    if clanTag is None and clanTagToken is None:
        exit(2)
    elif clanTagToken is not None:
        clanTag = clanTagToken

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
    writeGoogleSheets(tokens, clan, clanInfoColumnNames, clanWarInfoColumnNames)

    print()
    print("------------------------------------------------------------------------")
    print("CLASH Finished...")

    if browse:
        openBrowserTab("https://docs.google.com/spreadsheets/d/{}".format(tokens.getGoogleSheetId()))

    exit(0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--clantag",
                        dest="clantag",
                        required=False,
                        help="Clan Tag Value")
    parser.add_argument("-b", "--browse",
                        dest="browse",
                        required=False,
                        default=True,
                        help="Open browser tab with resulting spreadsheet")
    parser.add_argument("-td", "--testdata",
                        type=str2bool,
                        nargs='?',
                        dest="useTestData",
                        required=False,
                        default=False,
                        help="Use pickled test data if available")
    args = parser.parse_args()

    main(args.clantag, args.useTestData, args.browse)
