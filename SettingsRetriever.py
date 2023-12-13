import json


class SettingsRetriever:

    def __init__(self, configFile):
        configFile = open(configFile)
        self.configData = json.load(configFile)
        

    def getBoolean(self, key, default = True):
        setting = default
        try:
            setting = self.configData.get(key) == "true"
        except:
            return setting
        
    def getProperty(self, key):
        return self.configData.get(key)
    
    def getEmailForChurch(self, churchName):
        return self.configData.get("churchEmails").get(churchName)