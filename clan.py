from typing import List


class WarLog:
    def __init__(self, warDate, cardsEarned, finalDayBattlesPlayed, finalDayWins, collectionDayBattlesPlayed):
        MAX_NUM_FINAL_WAR_BATTLES = 1
        MAX_NUM_COLLECTION_DAY_BATTLES = 3

        self.warDate = warDate
        self.cardsEarned = cardsEarned
        self.finalDayBattlesPlayed = finalDayBattlesPlayed
        self.finalDayWins = finalDayWins
        self.collectionDayBattlesPlayed = collectionDayBattlesPlayed

        self.numCollectDayBattlesMissed = MAX_NUM_COLLECTION_DAY_BATTLES - collectionDayBattlesPlayed
        self.numFinalDayBattlesMissed = MAX_NUM_FINAL_WAR_BATTLES - finalDayBattlesPlayed

    def __getstate__(self):
        return self

    def __setstate__(self, d):
        return

    def __getattr__(self, attr):
        print(attr.upper())
        return attr.upper()


class Player:
    def __init__(self, name, tag, donations, donationsReceived, donationsPercent,
                 lastPlayedTime=0, daysSinceLastPlayed=0, battles=[], warLogs=None):
        self.name = name
        self.tag = tag
        self.donations = donations
        self.donationsReceived = donationsReceived
        self.donationsPercent = donationsPercent
        self.lastPlayedTime = lastPlayedTime
        self.daysSinceLastPlayed = daysSinceLastPlayed
        self.battles = battles
        self.warLogs: List[WarLog] = warLogs
        self.percentWarBattlesMissed = 0

        self.updatePercentWarBattlesMissed()

    def __getstate__(self):
        return self

    def __setstate__(self, d):
        return

    def __getattr__(self, attr):
        print(attr.upper())
        return attr.upper()

    def getAsList(self):
        return {self.name,
                self.tag,
                self.lastPlayedTime,
                self.daysSinceLastPlayed,
                self.donations,
                self.donationsReceived,
                self.donationsPercent}

    def sortByWarsMissed(self):
        self.warLogs.sort(key=self.sortingKeyWarsMissed, reverse=False)

    @staticmethod
    def sortingKeyWarsMissed(warLog: WarLog):
        return warLog.numFinalDayBattlesMissed

    def updatePercentWarBattlesMissed(self):
        if self.warLogs is None:
            return

        missedCount = 0
        totalWars = 0
        for warLog in self.warLogs:
            missedCount = missedCount + warLog.numFinalDayBattlesMissed
            totalWars = totalWars + 1

        if missedCount > 0:
            self.percentWarBattlesMissed = missedCount / totalWars

        return self.percentWarBattlesMissed * 100


class Clan:
    def __init__(self, name, tag):
        self.name = name
        self.tag = tag
        self.players: List[Player] = []

    def __getstate__(self):
        return self

    def __setstate__(self, d):
        return

    def __getattr__(self, attr):
        print(attr.upper())
        return attr.upper()

    def sortPlayersByLastPlayed(self):
        self.players.sort(key=self.sortingKeyLastPlayed)

    @staticmethod
    def sortingKeyLastPlayed(player: Player):
        return player.daysSinceLastPlayed

    @staticmethod
    def clanFromClanJson(clanInfoJson):
        theClan = Clan(clanInfoJson.raw_data['name'], clanInfoJson.raw_data['tag'])

        theClan.players = []
        if 'members' in clanInfoJson.raw_data:
            for member in clanInfoJson.raw_data['members']:
                if 'name' in member:
                    player = Player(member['name'],
                                    member['tag'],
                                    member['donations'],
                                    member['donationsReceived'],
                                    member['donationsPercent'])
                    theClan.players.append(player)

        return theClan

