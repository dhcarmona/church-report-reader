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

    def getAnswerIfExists(self, questionId, questionIds, answers):
        if questionId in questionIds:
            if questionIds[questionId] in answers:
                return self.sanitizeMonetaryInput(self.getAnswerValue(answers[questionIds[questionId]]))
        return 0

    def __init__(self, formResponse, questionIds, formName):

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

        self.amountOfWeekdayServices = 0
        self.amountOfWeekendServices = 0

        # Get financial form data
        self.simpleColones = self.getAnswerIfExists(SIMPLE_COLONES, questionIds, answers)        
        self.simpleDollars = self.getAnswerIfExists(SIMPLE_DOLLARS, questionIds, answers)        
        self.designatedColones = self.getAnswerIfExists(DESIGNATED_OFFERING_COLONES, questionIds, answers)
        self.designatedDollars = self.getAnswerIfExists(DESIGNATED_OFFERING_DOLLARS, questionIds, answers)
        self.promiseColones = self.getAnswerIfExists(PROMISES_COLONES, questionIds, answers)
        self.promiseDollars = self.getAnswerIfExists(PROMISES_DOLLARS, questionIds, answers)
        self.baptisms = self.getAnswerIfExists(BAPTISMS, questionIds, answers)

        self.amountOfWeekdayServices = self.getAnswerIfExists(WEEKDAY_SERVICES, questionIds, answers);
        self.amountOfWeekendServices = self.getAnswerIfExists(WEEKEND_SERVICES, questionIds, answers);


        self.confirmations = self.getAnswerIfExists(CONFIRMATIONS, questionIds, answers)
        self.receptions = self.getAnswerIfExists(RECEPTIONS, questionIds, answers)
        self.transfers = self.getAnswerIfExists(TRANSFERS, questionIds, answers)
        self.restores = self.getAnswerIfExists(RESTORES, questionIds, answers)
        self.deaths = self.getAnswerIfExists(DEATHS, questionIds, answers)
        self.moves = self.getAnswerIfExists(MOVES, questionIds, answers)
        self.otherLosses = self.getAnswerIfExists(OTHER_LOSSES, questionIds, answers)

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
                try:
                    self.totalAssistants = self.totalAssistants + int(assistantsAnswerValue)
                except ValueError:
                    print("Error converting value to int.")

                commulgantsAnswer = answers[questionIds[COMMULGANTS_PREFIX+str(index)]]
                commulgantsAnswerValue = self.getAnswerValue(commulgantsAnswer)
                try:
                    self.totalCommulgants = self.totalCommulgants + int(commulgantsAnswerValue)
                except ValueError:
                    print("Error converting value to int.")

                index = index + 1
            else:
                break
                
        self.individualDataRow = IndividualDataRow(self.formName, self.totalAssistants, self.totalCommulgants, self.simpleColones,
                                self.simpleDollars, self.designatedColones, self.designatedDollars, self.promiseColones,
                                self.promiseDollars, self.baptisms, self.confirmations, self.receptions, self.transfers,
                                self.restores, self.deaths, self.moves, self.otherLosses, self.amountOfWeekdayServices, self.amountOfWeekendServices)
        
        self.individualFormRow = IndividualFormRow(self.churchName, self.reportFiller, self.totalAssistants, self.totalCommulgants,
                                                    self.simpleColones, self.simpleDollars, self.designatedColones, self.designatedDollars,
                                                    self.promiseColones, self.promiseDollars, self.baptisms, self.confirmations, self.receptions,
                                                    self.transfers, self.restores, self.deaths, self.moves, self.otherLosses)


    def addWeekData(self, weekData):
        self.weekDatum.append(weekData)

class CummulativeDataRow:
    def __init__(self, churchName, totalReports, totalAssistants, totalCommulgants, totalSimpleColones, totalSimpleDollars, totalDesignatedColones,
                totalDesignatedDollars, totalPromiseColones, totalPromiseDollars, totalBaptisms, totalConfirmations, totalReceptions, totalTransfers,
                totalRestores, totalDeaths, totalMoves, totalOtherLosses, totalWeekdayServices, totalWeekendServices):
        self.totalReports = totalReports
        self.churchName = churchName
        self.totalAssistants = totalAssistants
        self.totalCommulgants = totalCommulgants
        self.totalSimpleColones = totalSimpleColones
        self.totalSimpleDollars = totalSimpleDollars
        self.totalDesignatedColones = totalDesignatedColones
        self.totalDesignatedDollars = totalDesignatedDollars
        self.totalPromiseColones = totalPromiseColones
        self.totalPromiseDollars = totalPromiseDollars
        self.totalBaptisms = totalBaptisms
        self.totalConfirmations = totalConfirmations
        self.totalReceptions = totalReceptions
        self.totalTransfers = totalTransfers
        self.totalRestores = totalRestores
        self.totalDeaths = totalDeaths
        self.totalMoves = totalMoves
        self.totalOtherLosses = totalOtherLosses
        self.totalWeekdayServices = totalWeekdayServices
        self.totalWeekendServices = totalWeekendServices

    @staticmethod
    def getHeaderList():
        return ["Nombre Iglesia", "Formularios Llenos", "Asistentes en el Periodo", "Comulgantes en el Periodo", "Total Ofrenda Simple Colones",
                "Total Ofrenda Simple Dolares", "Total Ofrenda Designada Colones", "Total Ofrenda Designada Dolares", "Total Promesas Colones",
                "Total Promesas Dolares", "Bautismos", "Confirmaciones", "Recepciones", "Transferencias", "Restauraciones", "Muertes", "Traslados",
                "Otras Causas (Perdidas)", "Celebraciones Entre Semana", "Celebraciones Fin de Semana"]

    def getDataList(self):
        return [str(self.churchName), str(self.totalReports), str(self.totalAssistants), str(self.totalCommulgants), str(self.totalSimpleColones),
                str(self.totalSimpleDollars), str(self.totalDesignatedColones), str(self.totalDesignatedDollars), str(self.totalPromiseColones),
                str(self.totalPromiseDollars), str(self.totalBaptisms), str(self.totalConfirmations), str(self.totalReceptions), str(self.totalTransfers),
                str(self.totalRestores), str(self.totalDeaths), str(self.totalTransfers), str(self.totalOtherLosses), str(self.totalWeekdayServices),
                str(self.totalWeekendServices)]

class IndividualDataRow:

    def __init__(self, formName, assistants, comulgants, simpleColones, 
                simpleDollars, designatedColones, designatedDollars, promiseColones, promiseDollars,
                baptisms, confirmations, receptions, transfers, restorations, deaths, moves, otherLosses, amountOfWeekdayServices, amountOfWeekendServices):
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
                self.amountofWeekdayServices = amountOfWeekdayServices
                self.amountofWeekendServices = amountOfWeekendServices


    @staticmethod
    def getHeaderList():
        return ["Nombre Formulario", "Asistentes", "Comulgantes", "Ofrenda Simple Colones",
                "Ofrenda Simple Dolares", "Ofrenda Designada Colones", "Ofrenda Designada Dolares",
                "Promesas Colones", "Promesas Dolares", "Bautismos", "Confirmaciones", "Recepciones",
                "Transferencias", "Restauraciones", "Muertes", "Traslados", "Otras Causas (Perdidas)", "Celebraciones Entre Semana", "Celebraciones Fin de Semana"]

    def getDataList(self):
        return [str(self.formName), str(self.assistants), str(self.comulgants), str(self.simpleColones),
                str(self.simpleDollars), str(self.designatedColones), str(self.designatedDollars),
                str(self.promiseColones), str(self.promiseDollars), str(self.baptisms), str(self.confirmations), str(self.receptions),
                str(self.transfers), str(self.restorations), str(self.deaths), str(self.moves), str(self.otherLosses), 
                str(self.amountofWeekdayServices), str(self.amountofWeekendServices)]

class IndividualFormRow:
        def __init__(self, churchName, personWhoFills, assistants, comulgants, simpleColones, 
                simpleDollars, designatedColones, designatedDollars, promiseColones, promiseDollars,
                baptisms, confirmations, receptions, transfers, restorations, deaths, moves, otherLosses):
                self.personWhoFills = personWhoFills
                self.churchName = churchName
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

        @staticmethod
        def getHeaderList():
            return ["Nombre Iglesia", "Persona Que Llena Formulario", "Asistentes", "Comulgantes", "Ofrenda Simple Colones",
                    "Ofrenda Simple Dolares", "Ofrenda Designada Colones", "Ofrenda Designada Dolares",
                    "Promesas Colones", "Promesas Dolares", "Bautismos", "Confirmaciones", "Recepciones",
                    "Transferencias", "Restauraciones", "Muertes", "Traslados", "Otras Causas (Perdidas)"]

        def getDataList(self):
            return [str(self.churchName), str(self.personWhoFills), str(self.assistants), str(self.comulgants), str(self.simpleColones),
                    str(self.simpleDollars), str(self.designatedColones), str(self.designatedDollars),
                    str(self.promiseColones), str(self.promiseDollars), str(self.baptisms), str(self.confirmations), str(self.receptions),
                    str(self.transfers), str(self.restorations), str(self.deaths), str(self.moves), str(self.otherLosses)]