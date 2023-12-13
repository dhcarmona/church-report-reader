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

formDataRetriever.parseAllResponsesAndWriteCSVFiles()

formsMissingPerChurch = formDataRetriever.getFormsMissingPerChurch()
responsesPerChurch = formDataRetriever.getAllResponsesPerChurch()

writeFilePerForm = settings.getProperty("writeFilePerForm")

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


globalEmailData = {}
globalEmailData["attachments"] = []

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
    for church in churchNames:
        try:
            churchEmail = settings.getEmailForChurch(church)
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

    globalEmailData["attachments"].append(formDataRetriever.getReportFiles())
    sendGlobalEmail(email, globalEmailData)