import json


class Tokens:
    def __init__(self, tokensJsonFileName):
        self.fileName = tokensJsonFileName
        self.tokensJson = self.loadTokens()

    def loadTokens(self):
        try:
            with open(self.fileName) as f:
                data = json.load(f)
        except:
            msg = "Failure:{} must exist and must contain json with key={}:<royal dev key>".format(self.fileName, "royale-dev-key")
            raise Exception(msg)

        return data

    def getRoyalDevKey(self):
        if self.tokensJson is None:
            return None

        if self.tokensJson['royale-dev-key'] is None:
            return None

        return self.tokensJson['royale-dev-key']

    def getGoogleSheetId(self):
        if self.tokensJson is None:
            return None

        if self.tokensJson['google-sheet-id'] is None:
            return None

        return self.tokensJson['google-sheet-id']

    def getClanTag(self):
        if self.tokensJson is None:
            return None

        if self.tokensJson['clantag'] is None:
            return None

        return self.tokensJson['clantag']
