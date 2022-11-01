import json
from pickle import TRUE
from urllib import response

from constants import *

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

    def __init__(self, formResponse, questionIds, formName):
        #print(json.dumps(formResponse, indent=4))

        # Get general form data
        answers = formResponse.get("answers")
        self.churchName = self.getAnswerValue(answers[questionIds[CHURCH_QUESTION_TITLE]])
        self.reportFiller = self.getAnswerValue(answers[questionIds[REPORT_FILLER]])
        self.formName = formName
        
        self.simpleColones = 0
        self.simpleDollars = 0
        self.designatedColones = 0
        self.designatedDollars = 0
        self.promiseColones = 0
        self.promiseDollars = 0
        self.baptisms = 0
        self.confirmations = 0
        self.receptions = 0
        self.transfers = 0
        self.restores = 0
        self.deaths = 0
        self.moves = 0
        self.otherLosses = 0

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
        if questionIds[BAPTISMS] in answers:
            self.baptisms = self.sanitizeMonetaryInput(self.getAnswerValue(answers[questionIds[BAPTISMS]]))
        if questionIds[CONFIRMATIONS] in answers:
            self.confirmations = self.sanitizeMonetaryInput(self.getAnswerValue(answers[questionIds[CONFIRMATIONS]]))
        if questionIds[RECEPTIONS] in answers:
            self.receptions = self.sanitizeMonetaryInput(self.getAnswerValue(answers[questionIds[RECEPTIONS]]))
        if questionIds[TRANSFERS] in answers:
            self.transfers = self.sanitizeMonetaryInput(self.getAnswerValue(answers[questionIds[TRANSFERS]]))
        if questionIds[RESTORES] in answers:
            self.restores = self.sanitizeMonetaryInput(self.getAnswerValue(answers[questionIds[RESTORES]]))
        if questionIds[DEATHS] in answers:
            self.deaths = self.sanitizeMonetaryInput(self.getAnswerValue(answers[questionIds[DEATHS]]))
        if questionIds[MOVES] in answers:
            self.moves = self.sanitizeMonetaryInput(self.getAnswerValue(answers[questionIds[MOVES]]))
        if questionIds[OTHER_LOSSES] in answers:
            self.otherLosses = self.sanitizeMonetaryInput(self.getAnswerValue(answers[questionIds[OTHER_LOSSES]]))

        self.simpleColones = int(self.simpleColones)
        self.simpleDollars = int(self.simpleDollars)
        self.designatedColones = int(self.designatedColones)
        self.designatedDollars = int(self.designatedDollars)
        self.promiseColones = int(self.promiseColones)
        self.promiseDollars = int(self.promiseDollars)

        if "Marcos" in self.churchName:
            print(" -- PROMESA SAN MARCOS: " + str(self.promiseColones))

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
                
        #print(json.dumps(self.__dict__, indent = 4))
        self.individualDataRow = IndividualDataRow(self.formName, self.totalAssistants, self.totalCommulgants, self.simpleColones,
                                self.simpleDollars, self.designatedColones, self.designatedDollars, self.promiseColones,
                                self.promiseDollars, self.baptisms, self.confirmations, self.receptions, self.transfers,
                                self.restores, self.deaths, self.moves, self.otherLosses)


    def addWeekData(self, weekData):
        self.weekDatum.append(weekData)

class IndividualDataRow:

    def __init__(self, formName, assistants, comulgants, simpleColones, 
                simpleDollars, designatedColones, designatedDollars, promiseColones, promiseDollars,
                baptisms, confirmations, receptions, transfers, restorations, deaths, moves, otherLosses):
                self.formName = formName
                self.assistants = assistants
                self.comulgants = comulgants
                self.simpleColones = simpleColones
                self.simpleDollars = simpleDollars
                self.designatedColones = designatedColones
                self.designatedDollars = designatedDollars
                self.promiseColones = promiseColones
                self.promiseDollars = promiseDollars
                self.baptisms = baptisms
                self.confirmations = confirmations
                self.receptions = receptions
                self.transfers = transfers
                self.restorations = restorations
                self.deaths = deaths
                self.moves = moves
                self.otherLosses = otherLosses

    def getHeaderList(self):
        return ["Nombre Formulario", "Asistentes", "Comulgantes", "Ofrenda Simple Colones",
                "Ofrenda Simple Dolares", "Ofrenda Designada Colones", "Ofrenda Designada Dolares",
                "Promesas Colones", "Promesas Dolares", "Bautismos", "Confirmaciones", "Recepciones",
                "Transferencias", "Restauraciones", "Muertes", "Traslados", "Otras Causas (Perdidas)"]

    def getDataList(self):
        return [str(self.formName), str(self.assistants), str(self.comulgants), str(self.simpleColones),
                str(self.simpleDollars), str(self.designatedColones), str(self.designatedColones), str(self.designatedDollars),
                str(self.promiseColones), str(self.promiseDollars), str(self.baptisms), str(self.confirmations), str(self.receptions),
                str(self.transfers), str(self.restorations), str(self.deaths), str(self.moves), str(self.otherLosses)]