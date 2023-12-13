from __future__ import print_function
from urllib import response
from loguru import logger
import argparse
from constants import *
import csv
import os
from church import ChurchResponse, CummulativeDataRow, IndividualDataRow, IndividualFormRow
from EmailSender import EmailSender
from GoogleAPIService import GoogleAPIService
from FormDataRetriever import FormDataRetriever
from SettingsRetriever import SettingsRetriever
from datetime import date
from os import path

# Globals. TODO: refactor most of these

config = None
emailPerChurch = {}
globalFileName = path.relpath('reporte_total.csv')
globalFileName = globalFileName.replace("(", "")
globalFileName = globalFileName.replace(")", "")
globalEmailData = {}
globalEmailData["attachments"] = []
fecha = date.today().strftime('%d-%m-%Y')

parser = argparse.ArgumentParser()
parser.add_argument('--configFile', type=str, required=True)
args = parser.parse_args()

logger.info("Limpiando archivos viejos...")
churchFileDirectory = "reportesPorIglesia"
formFileDirectory = "reportesPorFormulario"
filesInChurchDirectory = os.listdir(churchFileDirectory)
filesInFormDirectory = os.listdir(formFileDirectory)
for file in filesInChurchDirectory:
    path_to_file = os.path.join(churchFileDirectory, file)
    logger.debug("Borrando archivo " + path_to_file)
    os.remove(path_to_file)

for file in filesInFormDirectory:
    path_to_file = os.path.join(formFileDirectory, file)
    logger.debug("Borrando archivo " + path_to_file)
    os.remove(path_to_file)

path_to_global_file = os.path.join("", globalFileName)
logger.info("Borrando archivo " + path_to_global_file)
try:
    os.remove(path_to_global_file)
except FileNotFoundError as fnfe:
    logger.info("Archivo de reporte global no existe.")

logger.info("")
logger.info("Leyendo configuracion...")
settings = SettingsRetriever(args.configFile)
logger.info("Leida configuracion.")
logger.info(" ")
logger.info(" ")
logger.info(" ---- Lector de Formularios: Iglesia Episcopal Costarricense ----")
logger.info(" ")
logger.info(" ")

googleApiService = GoogleAPIService()

logger.info(" ")
logger.info("Accediendo a cuenta de Google... ")
logger.info(" ")

googleApiService.login("credentials.json","token.json", SCOPES)

logger.info(" ")
logger.info("Obteniendo formularios")
logger.info(" ")

formDataRetriever = FormDataRetriever(googleApiService.getDriveService(), googleApiService.getFormService())
forms = formDataRetriever.retrieveForms(settings.getProperty("formFolderId"), True)

logger.info("")
logger.info("Procesando Formularios...")
logger.info("")

churchNames = formDataRetriever.retrieveChurchNames()

for name in churchNames:
    emailPerChurch[name] = {}

def getQuestionIds(form):
    questionIds = {}
    celebrantIndex = 0
    assistantIndex = 0
    commulgantIndex = 0
    for item in form.get("items"):
        #logger.info(" DEBUG Processing Item ")
        #logger.info(json.dumps(item, indent=4))
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

formsMissingPerChurch = {}
formsFilledPerChurch = {}
responsesPerChurch = {}

writeFilePerForm = settings.getProperty("writeFilePerForm")

for form in forms:
    logger.info(" ")
    formName = form['info']['documentTitle']
    formName.replace("//", "-")
    formName.replace("\/", "-")
    fileName = path.relpath('reportesPorFormulario/reporte_'+formName+'.csv')
    fileName = fileName.replace("(", "")
    fileName = fileName.replace(")", "")
    logger.info(" ------- FORMULARIO: " + formName)
    churchQuestionId = ""
    questionIds = getQuestionIds(form)
    churchQuestionId = questionIds[CHURCH_QUESTION_TITLE]
    logger.info("")
    # logger.info("ID for church question: "+ churchQuestionId)
    logger.info("Procesando respuestas...")
    responseList = formDataRetriever.retrieveFormResponses(form.get("formId"))
    #logger.info(json.dumps(responseList, indent=4))
    if not responseList:
        logger.info(" --- ERROR: No hay respuestas para este formulario. ---")
        continue
    logger.info("Encontradas "+ str(len(responseList)) +" respuestas para este formulario.")
    churchesWhoAnsweredThisForm = []
    with open(fileName, 'w', encoding='UTF8', newline='') as f:
        writer = csv.writer(f)
        if writeFilePerForm:
            writer.writerow(IndividualFormRow.getHeaderList())
        for response in responseList:
            churchResponse = ChurchResponse(response, questionIds, formName)
            try:
                responseAnswers = response.get("answers")
                churchQuestionAnswer = responseAnswers.get(churchQuestionId)
                churchQuestionTextAnswers = churchQuestionAnswer.get("textAnswers")
                churchAnswer = churchQuestionTextAnswers.get("answers")[0].get("value")
                logger.info("Encontrada respuesta para esta iglesia: " + churchAnswer)
                if churchAnswer in churchesWhoAnsweredThisForm:
                    logger.info("Ya existe una respuesta de esta iglesia para este formulario.")
                    logger.info("Ignorando esta respuesta.")
                    continue
                if writeFilePerForm:
                    writer.writerow(churchResponse.individualFormRow.getDataList())
                churchesWhoAnsweredThisForm.append(churchAnswer)
                if not churchAnswer in responsesPerChurch:
                    responsesPerChurch[churchAnswer] = []
                responsesPerChurch[churchAnswer].append(churchResponse)

            except Exception as e:
                logger.info("ERROR GRAVE: No se pudo obtener los datos de esta respuesta.")
                logger.info(e)
        for church in churchNames:
            if not church in churchesWhoAnsweredThisForm:
                print ("--- IGLESIA " + church + " NO RESPONDIO ESTE FORMULARIO -- ")
                if not church in formsMissingPerChurch:
                    formsMissingPerChurch[church] = []
                formsMissingPerChurch[church].append(form)
        globalEmailData["attachments"].append(fileName)

writeFilloutReport = settings.getProperty("writeFilloutReport")

if writeFilloutReport:
    logger.info("")
    logger.info(" -- REPORTE DE LLENADO POR IGLESIA - FORMULARIOS FALTANTES ")
    logger.info("------")

    for church in churchNames:
        report = ""
        report = report + "------\n"
        report = report + " Formularios Faltantes para Congregación: " + church + "\n"
        try:
            for missingForm in formsMissingPerChurch[church]:
                report = report + " -- " + missingForm['info']['documentTitle'] + "\n"
                report = report + " -- Enlace para llenarlo: " + missingForm.get("responderUri") + "\n"
        except KeyError:
            report = report + "Esta congregación no tiene ningun formulario faltante.\n"
        logger.info(report)
        emailPerChurch[church]["fillOutReport"] = report

writeCummulativeReportPerChurch = settings.getProperty("writeCummulativeReportPerChurch")

if writeCummulativeReportPerChurch:
    logger.info("")
    logger.info(" -- REPORTE DE ACUMULADOS POR IGLESIA")
    logger.info("------")
    globalFileName = path.relpath('reporte_total.csv')
    globalFileName = globalFileName.replace("(", "")
    globalFileName = globalFileName.replace(")", "")
    logger.info(" - Escribiendo a archivo: " + globalFileName)
    with open(globalFileName, 'w', encoding='UTF8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(CummulativeDataRow.getHeaderList())
        for church in responsesPerChurch.keys():
            logger.info("------")
            totalReports = 0
            totalAssistance = 0
            totalCommulgants = 0
            totalSimpleColones = 0
            totalSimpleDollars = 0
            totalDesignatedColones = 0
            totalDesignatedDollars = 0
            totalPromiseColones = 0
            totalPromiseDollars = 0
            totalBaptisms = 0
            totalConfirmations = 0
            totalReceptions = 0
            totalTransfers = 0
            totalRestores = 0
            totalDeaths = 0
            totalMoves = 0
            totalOtherLosses = 0
            totalWeekdayServices = 0
            totalWeekendServices = 0

            for response in responsesPerChurch[church]:
                totalReports = totalReports + 1
                totalAssistance = totalAssistance + response.totalAssistants
                totalCommulgants = totalCommulgants + response.totalCommulgants
                totalSimpleColones = totalSimpleColones + response.simpleColones
                totalSimpleDollars = totalSimpleDollars + response.simpleDollars
                totalDesignatedColones = totalDesignatedColones + response.designatedColones
                totalDesignatedDollars = totalDesignatedDollars + response.designatedDollars
                totalPromiseColones = totalPromiseColones + response.promiseColones
                totalPromiseDollars = totalPromiseDollars + response.promiseDollars
                totalBaptisms = totalBaptisms + response.baptisms
                totalConfirmations = totalConfirmations + response.confirmations
                totalReceptions = totalReceptions + response.receptions
                totalTransfers = totalTransfers + response.transfers
                totalRestores = totalRestores + response.restores
                totalDeaths = totalDeaths + response.deaths
                totalMoves = totalMoves + response.moves
                totalOtherLosses = totalOtherLosses + response.otherLosses
                totalWeekdayServices = totalWeekdayServices + response.amountOfWeekdayServices
                totalWeekendServices = totalWeekendServices + response.amountOfWeekendServices

            cummulativeDataRow = CummulativeDataRow(church, totalReports, totalAssistance, totalCommulgants, totalSimpleColones,            totalSimpleDollars,
                                                    totalDesignatedColones, totalDesignatedDollars, totalPromiseColones, totalPromiseDollars,
                                                    totalBaptisms, totalConfirmations, totalReceptions, totalTransfers, totalRestores,
                                                    totalDeaths, totalMoves, totalOtherLosses, totalWeekdayServices, totalWeekendServices)

            report = ""
            report = report + "---- \nAcumulados para Iglesia: " + church + " con corte al " + fecha + "\n"
            report = report + " - Total de formularios procesados para esta congregacion: " + str(len(responsesPerChurch[church]))  + "\n"
            report = report + " - Total asistentes en todo el periodo: " + str(totalAssistance)  + "\n"
            report = report + " - Total comulgantes en todo el periodo: " + str(totalCommulgants)  + "\n"
            report = report + " - Total ofrenda simple colones en todo el periodo: ₡ " + str(totalSimpleColones)  + "\n"
            report = report + " - Total ofrenda simple dolares en todo el periodo: $ " + str(totalSimpleDollars)  + "\n"
            report = report + " - Total ofrenda designada colones en todo el periodo: ₡ " + str(totalDesignatedColones)  + "\n"
            report = report + " - Total ofrenda designada dolares en todo el periodo: $ " + str(totalDesignatedDollars)  + "\n"
            report = report + " - Total promesa colones en todo el periodo: ₡ " + str(totalPromiseColones)  + "\n"
            report = report + " - Total promesa dolares en todo el periodo: $ " + str(totalPromiseDollars)  + "\n"
            report = report + " - Total celebraciones entre semana en todo el periodo: " + str(totalWeekdayServices)  + "\n"
            report = report + " - Total celebraciones fin de semana en todo el periodo: " + str(totalWeekendServices)  + "\n"
            emailPerChurch[church]["cummulativeReport"] = report
            writer.writerow(cummulativeDataRow.getDataList())

writeIndividualChurchForm = settings.getProperty("writeIndividualChurchForm")

def sendIndividualChurchEmail(email, churchName, emailData):
    emailSender = EmailSender(googleApiService.getGmailService())
    emailSender.sendIndividualChurchEmail(email, churchName, emailData, fecha)

def sendGlobalEmail(email, emailData):
    emailSender = EmailSender(googleApiService.getGmailService())
    emailSender.sendGlobalReportEmail(email, emailData, fecha)


if writeIndividualChurchForm:
    logger.info("")
    logger.info(" -- REPORTE INDIVIDUAL POR IGLESIA")
    logger.info("------")
    for church in responsesPerChurch.keys():
        fileName = path.relpath('reportesPorIglesia/reporte_formularios_'+church+'.csv')
        logger.info(" - Escribiendo a archivo: " + fileName)
        with open(fileName, 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(IndividualDataRow.getHeaderList())
            for response in responsesPerChurch[church]:
                writer.writerow(response.individualDataRow.getDataList())
        #Add file to send as attachment
        emailPerChurch[church]["attachments"] = []
        emailPerChurch[church]["attachments"].append(fileName)      
        globalEmailData["attachments"].append(fileName)

    logger.info("")
    logger.info(" -- Enviando correos a iglesias")
    logger.info("------")
    emails = settings.getProperty("churchEmails")
    for church in churchNames:
        try:
            churchEmail = emails[church]
            if churchEmail:
                logger.info("Correo para iglesia: " + church + " es " + churchEmail)
                sendIndividualChurchEmail(churchEmail, church, emailPerChurch[church])
        except Exception as e:
            logger.info("Error enviando correo")
            logger.info(e)

    logger.info("")
    logger.info(" -- Enviando correo a oficina")
    logger.info("------")
    email = settings.getProperty("globalReportEmail")

    globalEmailData["attachments"].append(globalFileName)
    sendGlobalEmail(email, globalEmailData)