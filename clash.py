import argparse
import json

import clashroyale
import datetime
import time
from clan import Clan
from clan import WarLog
import sys
import os

# File to store your royal api dev key or any other you may need
tokensJsonFileName = 'tokens.json'

# Mostly for debugging.  If >Clan size, then all players are obtained.
# For example, setting to 2 then only 2 players are retrieved, inspect the data, etc
# for faster debugging
PLAYER_FETCH_COUNT = 50


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
def writeOutputCsv(theClan):
    rowFormat = "{},{},{},{},{},{},{}\n"
    headerRow = rowFormat.format('Player Name',
                                 'Player Tag',
                                 'Last Played',
                                 'Days Since Last Played',
                                 'Donations',
                                 'Donations Received',
                                 'Donations Percent')
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

    headerRow = rowFormat.format('Player Name',
                                 'Player Tag',
                                 'War Date',
                                 'War Cards Earned',
                                 'War Final Battles Played',
                                 'War Final Battle Wins',
                                 'War Collection Day Battles Played')
    with open('output/clanwarinfo.csv', 'w', encoding='UTF-8', newline='') as out:
        out.write(headerRow)
        for player in theClan.players:
            for warLog in player.warLogs:
                out.write(rowFormat.format(player.name,
                                           player.tag,
                                           warLog.warDate,
                                           warLog.cardsEarned,
                                           warLog.battlesPlayed,
                                           warLog.wins,
                                           warLog.collectionDayBattlesPlayed
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
                        battlesPlayed = participant['battlesPlayed']
                        wins = participant['wins']
                        collectionDayBattlesPlayed = participant['collectionDayBattlesPlayed']
                        warLog = WarLog(datetime.datetime.fromtimestamp(createdDate),
                                        cardsEarned, battlesPlayed, wins, collectionDayBattlesPlayed)
                        warLogList.append(warLog)

    return warLogList


# -----------------------------------------------------------------------------
def updateClanPlayersData(client, theClan, clanWarLogs):
    # for each player, get there battles which contains the game time
    # using the newest game time as the "last played" time
    numPlayersToGet = PLAYER_FETCH_COUNT
    for player in theClan.players:
        try:
            battles = fetchPlayerBattlesWithRetries(client, player.tag)
        except:
            print("\tFailed to get player battles")
            continue

        player.battles = battles

        if battles.__len__() == 0:
            player.daysSinceLastPlayed = 99999
        else:
            for battle in battles:
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
            print("\tWar:earned:{}, played:{}, wins:{}, collected:{}"
                  .format(warLog.cardsEarned, warLog.battlesPlayed, warLog.wins,
                          warLog.collectionDayBattlesPlayed))

        numPlayersToGet = numPlayersToGet - 1
        if numPlayersToGet == 0:
            break


# -----------------------------------------------------------------------------
def main(clanTag):
    print("------------------------------------------------------------------------")
    print("CLASH Running...")
    print()

    tokens = getTokens()
    if tokens is None:
        exit(1)

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
    eleventyNine = Clan.clanFromClanJson(clanInfoJson)

    # Get the members of the clan and their info
    updateClanPlayersData(client, eleventyNine, clanWarLogs)

    # write the output to a csv
    writeOutputCsv(eleventyNine)

    print()
    print("------------------------------------------------------------------------")
    print("CLASH Ending...")


if __name__ == '__main__':
    addSubDirsToPath()

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--clantag",
                        dest="clantag",
                        required=True,
                        help="Clan Tag Value")
    args = parser.parse_args()

    main(args.clantag)