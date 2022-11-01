import json
from pickle import TRUE
from urllib import response

from constants import ASSISTANTS_PREFIX, CELEBRANT_PREFIX, CHURCH_QUESTION_TITLE, COMMULGANTS_PREFIX, DESIGNATED_OFFERING_COLONES, DESIGNATED_OFFERING_DOLLARS, PROMISES_COLONES, PROMISES_DOLLARS, REPORT_FILLER, SIMPLE_COLONES, SIMPLE_DOLLARS

class WeekData:

    def __init__(self, questionTitle = "", celebrantName = "", assistants = 0, commulgants = 0):
        self.questionTitle = questionTitle
        self.celebrantName = celebrantName
        self.assistants = assistants
        self.comulgants = commulgants

class ChurchResponse: 
    weekDatum = []

    def getAnswerValue(self, responseAnswer):
        return responseAnswer.get("textAnswers").get("answers")[0].get("value")

    def sanitizeMonetaryInput(self, input):
        sanitizedInput = 0
        try:
            sanitizedInput = int(input.replace(".", ""))
        except ValueError as ve:
            print(" ==== ERROR: No se pudo convertir a un numero: ")
            print(ve)
        return sanitizedInput

    def __init__(self, formResponse, questionIds):
        #print(json.dumps(formResponse, indent=4))

        # Get general form data
        answers = formResponse.get("answers")
        self.churchName = self.getAnswerValue(answers[questionIds[CHURCH_QUESTION_TITLE]])
        self.reportFiller = self.getAnswerValue(answers[questionIds[REPORT_FILLER]])
        
        self.simpleColones = 0
        self.simpleDollars = 0
        self.designatedColones = 0
        self.designatedDollars = 0
        self.promiseColones = 0
        self.promiseDollars = 0

        # Get financial form data
        #print(json.dumps(questionIds, indent = 4))
        if questionIds[SIMPLE_COLONES] in answers:
            self.simpleColones = self.sanitizeMonetaryInput(self.getAnswerValue(answers[questionIds[SIMPLE_COLONES]]))
        if questionIds[SIMPLE_DOLLARS] in answers:
            self.simpleDollars = self.sanitizeMonetaryInput(self.getAnswerValue(answers[questionIds[SIMPLE_DOLLARS]]))
        if questionIds[DESIGNATED_OFFERING_COLONES] in answers:
            self.designatedColones = self.sanitizeMonetaryInput(self.getAnswerValue(answers[questionIds[DESIGNATED_OFFERING_COLONES]]))
        if questionIds[DESIGNATED_OFFERING_DOLLARS] in answers:
            self.designatedDollars = self.sanitizeMonetaryInput(self.getAnswerValue(answers[questionIds[DESIGNATED_OFFERING_DOLLARS]]))
        if questionIds[PROMISES_COLONES] in answers:
            self.promiseColones = self.sanitizeMonetaryInput(self.getAnswerValue(answers[questionIds[PROMISES_COLONES]]))
        if questionIds[PROMISES_DOLLARS] in answers:
            self.promiseDollars = self.sanitizeMonetaryInput(self.getAnswerValue(answers[questionIds[PROMISES_DOLLARS]]))

        self.simpleColones = int(self.simpleColones)
        self.simpleDollars = int(self.simpleDollars)
        self.designatedColones = int(self.designatedColones)
        self.designatedDollars = int(self.designatedDollars)
        self.promiseColones = int(self.promiseColones)
        self.promiseDollars = int(self.promiseDollars)

        # Get data per week
        
        index = 0
        self.totalAssistants = 0
        self.totalCommulgants = 0
        while(True):
            if CELEBRANT_PREFIX+str(index) in questionIds:
                if index >=1:
                    self.isCummulative = True
                # There's a week with this index
                assistantsAnswer = answers[questionIds[ASSISTANTS_PREFIX+str(index)]]
                assistantsAnswerValue = self.getAnswerValue(assistantsAnswer)
                print("-- Asistentes a la semana "+ str(index) +": " + assistantsAnswerValue)
                try:
                    self.totalAssistants = self.totalAssistants + int(assistantsAnswerValue)
                except ValueError:
                    print("Error converting value to int.")

                commulgantsAnswer = answers[questionIds[COMMULGANTS_PREFIX+str(index)]]
                commulgantsAnswerValue = self.getAnswerValue(commulgantsAnswer)
                print("-- Comulgantes para la semana: " + assistantsAnswerValue)
                try:
                    self.totalCommulgants = self.totalCommulgants + int(assistantsAnswerValue)
                except ValueError:
                    print("Error converting value to int.")

                index = index + 1
            else:
                break
                
        print(json.dumps(self.__dict__, indent = 4))


    def addWeekData(self, weekData):
        self.weekDatum.append(weekData)