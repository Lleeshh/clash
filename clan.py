from typing import List


class WarLog:
    def __init__(self, warDate, cardsEarned, battlesPlayed, wins, collectionDayBattlesPlayed):
        self.warDate = warDate
        self.cardsEarned = cardsEarned
        self.battlesPlayed = battlesPlayed
        self.wins = wins
        self.collectionDayBattlesPlayed = collectionDayBattlesPlayed


class Player:
    def __init__(self, name, tag, donations, donationsReceived, donationsPercent, warLogs=None):
        self.name = name
        self.tag = tag
        self.donations = donations
        self.donationsReceived = donationsReceived
        self.donationsPercent = donationsPercent
        self.lastPlayedTime = 0
        self.daysSinceLastPlayed = 0
        self.battles = 0
        self.warLogs: List[WarLog] = warLogs

    def getAsList(self):
        return {self.name,
                self.tag,
                self.lastPlayedTime,
                self.daysSinceLastPlayed,
                self.donations,
                self.donationsReceived,
                self.donationsPercent}


class Clan:
    def __init__(self, name, tag):
        self.name = name
        self.tag = tag
        self.players: List[Player] = []

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

