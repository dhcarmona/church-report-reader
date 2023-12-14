import json
from httplib2 import Http
from googleapiclient.errors import HttpError
from loguru import logger
from constants import *
from church import ChurchResponse, CummulativeDataRow, IndividualDataRow, IndividualFormRow
from CSVWriter import CSVWriter
from os import path

class FormDataRetriever:

    def __init__(self, driveAPIService, formAPIService):
        self.drive_service = driveAPIService
        self.form_service = formAPIService
        self.forms = []
        self.responsesPerChurch = {}
        self.formsMissingPerChurch = {}
        self.reportFiles = []
        self.churchNames = []

    def retrieveForms(self, formFolderId, processAllFiles):
        self.forms = []
        try:
            files = []
            formIds = []
            page_token = None
            logger.info("Procesando folder "+ formFolderId)
            while True:
                filesResponse = self.drive_service.files().list(q="'"+ formFolderId + "' in parents AND mimeType='application/vnd.google-apps.form'",
                                                        spaces='drive',
                                                        fields='nextPageToken, '
                                                                'files(id, name)',
                                                        pageToken=page_token).execute()
                for file in filesResponse.get('files', []):
                    logger.info(F'Encontrado archivo: {file.get("name")}, {file.get("id")}')
                    files.extend(filesResponse.get('files', []))
                    if processAllFiles:
                        formIds.append(file.get("id"))
                page_token = filesResponse.get('nextPageToken', None)
                if page_token is None:
                    break
            for formId in formIds:
                form = self.form_service.forms().get(formId=formId).execute()
                formName = form['info']['documentTitle']
                logger.info("Leido formulario con nombre: " + formName)
                self.forms.append(form)
        except HttpError as error:
            logger.info(F'Error: {error}')
        return self.forms
    
    def retrieveFormResponses(self, formId):
       responseResponse = self.form_service.forms().responses().list(formId=formId).execute()
       return responseResponse.get("responses")
    
    def retrieveChurchNames(self):
        if self.forms and not self.churchNames:
            logger.debug("")
            logger.debug("Obteniendo nombres de congregaciones...")
            logger.debug("")
            form = self.forms[0]
            for item in form.get("items"):
                if CHURCH_QUESTION_ID in item.get("title"):
                    for option in item.get("questionItem").get("question").get("choiceQuestion").get("options"):
                        name = option.get("value")
                        logger.debug(name)
                        self.churchNames.append(name)
        return self.churchNames

    def getQuestionIds(self, form):
        questionIds = {}
        celebrantIndex = 0
        assistantIndex = 0
        commulgantIndex = 0
        for item in form.get("items"):
            #logger.trace(json.dumps(item, indent=4))
            questionTitle = item.get("title") 
            if (CHURCH_QUESTION_ID) in questionTitle:
                questionIds[CHURCH_QUESTION_TITLE] = item.get("questionItem").get("question").get("questionId")
            elif ("que llena este") in questionTitle:
                questionIds[REPORT_FILLER] = item.get("questionItem").get("question").get("questionId")
            elif ("a Cargo") in questionTitle:
                questionIds[PERSON_IN_CHARGE] = item.get("questionItem").get("question").get("questionId")
            elif ("celebrante") in questionTitle:
                questionIds[CELEBRANT_PREFIX+str(celebrantIndex)] = item.get("questionItem").get("question").get("questionId")
                celebrantIndex = celebrantIndex + 1
            elif ("asistieron") in questionTitle:
                questionIds[ASSISTANTS_PREFIX+str(assistantIndex)] = item.get("questionItem").get("question").get("questionId")
                assistantIndex = assistantIndex + 1
            elif ("comulgaron") in questionTitle:
                questionIds[COMMULGANTS_PREFIX+str(commulgantIndex)] = item.get("questionItem").get("question").get("questionId")
                commulgantIndex = commulgantIndex + 1
            elif ("realizaron entre semana") in questionTitle:
                questionIds[WEEKDAY_SERVICES] = item.get("questionItem").get("question").get("questionId")
            elif ("realizaron el fin de semana") in questionTitle:
                questionIds[WEEKEND_SERVICES] = item.get("questionItem").get("question").get("questionId")
            elif ("Ofrenda Simple - Colones") in questionTitle:
                questionIds[SIMPLE_COLONES] = item.get("questionItem").get("question").get("questionId")
            elif ("Ofrenda Simple - Dólares") in questionTitle:
                questionIds[SIMPLE_DOLLARS] = item.get("questionItem").get("question").get("questionId")
            elif ("Ofrenda Designada - Colones") in questionTitle:
                questionIds[DESIGNATED_OFFERING_COLONES] = item.get("questionItem").get("question").get("questionId")
            elif ("Ofrenda Designada - Dólares") in questionTitle:
                questionIds[DESIGNATED_OFFERING_DOLLARS] = item.get("questionItem").get("question").get("questionId")
            elif ("Promesas - Colones") in questionTitle:
                questionIds[PROMISES_COLONES] = item.get("questionItem").get("question").get("questionId")
            elif ("Promesas - Dólares") in questionTitle:
                questionIds[PROMISES_DOLLARS] = item.get("questionItem").get("question").get("questionId")
            elif ("Bautismos") in questionTitle:
                questionIds[BAPTISMS] = item.get("questionItem").get("question").get("questionId")
            elif ("Confirmaciones") in questionTitle:
                questionIds[CONFIRMATIONS] = item.get("questionItem").get("question").get("questionId")
            elif ("Recepciones") in questionTitle:
                questionIds[RECEPTIONS] = item.get("questionItem").get("question").get("questionId")
            elif ("Transferencias") in questionTitle:
                questionIds[TRANSFERS] = item.get("questionItem").get("question").get("questionId")
            elif ("Restauraciones") in questionTitle:
                questionIds[RESTORES] = item.get("questionItem").get("question").get("questionId")
            elif ("Muertes") in questionTitle:
                questionIds[DEATHS] = item.get("questionItem").get("question").get("questionId")
            elif ("Traslados") in questionTitle:
                questionIds[MOVES] = item.get("questionItem").get("question").get("questionId")
            elif ("Otras causas") in questionTitle:
                questionIds[OTHER_LOSSES] = item.get("questionItem").get("question").get("questionId")
        return questionIds
    
    def parseAllResponsesAndWriteCSVFiles(self):
        for form in self.forms:
            logger.info(" ")
            formName = form['info']['documentTitle']
            formName.replace("//", "-")
            formName.replace("\/", "-")
            fileName = path.relpath('reportesPorFormulario/reporte_'+formName+'.csv')
            fileName = fileName.replace("(", "")
            fileName = fileName.replace(")", "")
            logger.info(" ------- FORMULARIO: " + formName)
            churchQuestionId = ""
            questionIds = self.getQuestionIds(form)
            churchQuestionId = questionIds[CHURCH_QUESTION_TITLE]
            logger.info("")
            logger.debug("ID for church question: "+ churchQuestionId)
            logger.info("Procesando respuestas...")
            responseList = self.retrieveFormResponses(form.get("formId"))
            logger.trace(json.dumps(responseList, indent=4))
            if not responseList:
                logger.info(" --- ERROR: No hay respuestas para el formulario. "+ formName +" ---")
                continue
            logger.debug("Encontradas "+ str(len(responseList)) +" respuestas para este formulario.")
            churchesWhoAnsweredThisForm = []
            with CSVWriter(fileName, IndividualFormRow.getHeaderList()) as csvWriter:
                for response in responseList:
                    churchResponse = ChurchResponse(response, questionIds, formName)
                    try:
                        responseAnswers = response.get("answers")
                        churchQuestionAnswer = responseAnswers.get(churchQuestionId)
                        churchQuestionTextAnswers = churchQuestionAnswer.get("textAnswers")
                        churchAnswer = churchQuestionTextAnswers.get("answers")[0].get("value")
                        logger.debug("Encontrada respuesta para esta iglesia: " + churchAnswer)
                        if churchAnswer in churchesWhoAnsweredThisForm:
                            logger.debug("Ya existe una respuesta de esta iglesia para este formulario.")
                            logger.debug("Ignorando esta respuesta.")
                            continue
                        csvWriter.writeRow(churchResponse.individualFormRow.getDataList())
                        churchesWhoAnsweredThisForm.append(churchAnswer)
                        if not churchAnswer in self.responsesPerChurch:
                            self.responsesPerChurch[churchAnswer] = []
                        self.responsesPerChurch[churchAnswer].append(churchResponse)

                    except Exception as e:
                        logger.debug("ERROR GRAVE: No se pudo obtener los datos de esta respuesta.")
                        logger.debug(e)
                for church in self.retrieveChurchNames():
                    if not church in churchesWhoAnsweredThisForm:
                        logger.debug("--- IGLESIA " + church + " NO RESPONDIO ESTE FORMULARIO -- ")
                        if not church in self.formsMissingPerChurch:
                            self.formsMissingPerChurch[church] = []
                        self.formsMissingPerChurch[church].append(form)
                self.reportFiles.append(fileName)

    def getAllResponsesPerChurch(self):
        return self.responsesPerChurch
    
    def getFormsMissingPerChurch(self):
        return self.formsMissingPerChurch
    
    def getReportFiles(self):
        return self.reportFiles