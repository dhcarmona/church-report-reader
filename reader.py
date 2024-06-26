from __future__ import print_function
from urllib import response

from constants import *
import google.auth
import click
import json
import csv
import os
from apiclient import discovery
from httplib2 import Http
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from church import ChurchResponse, CummulativeDataRow, IndividualDataRow, IndividualFormRow
from EmailSender import EmailSender
from datetime import date

from os import path

formIds = []
forms = []
churchNames = []
config = None
emailPerChurch = {}
globalFileName = path.relpath('reporte_total.csv')
globalFileName = globalFileName.replace("(", "")
globalFileName = globalFileName.replace(")", "")

globalEmailData = {}
globalEmailData["attachments"] = []

fecha = date.today().strftime('%d-%m-%Y')


print("Limpiando archivos viejos...")
churchFileDirectory = "reportesPorIglesia"
formFileDirectory = "reportesPorFormulario"
filesInChurchDirectory = os.listdir(churchFileDirectory)
filesInFormDirectory = os.listdir(formFileDirectory)
for file in filesInChurchDirectory:
    path_to_file = os.path.join(churchFileDirectory, file)
    print("Borrando archivo " + path_to_file)
    os.remove(path_to_file)

for file in filesInFormDirectory:
    path_to_file = os.path.join(formFileDirectory, file)
    print("Borrando archivo " + path_to_file)
    os.remove(path_to_file)

path_to_global_file = os.path.join("", globalFileName)
print("Borrando archivo " + path_to_global_file)
os.remove(path_to_global_file)


print("")
print("Leyendo configuracion...")
print("")
configFile = open('/Users/dhcarmona/config-prueba.json')
configData = json.load(configFile)
print("Leida configuracion:")
print(configData)


creds = None
if path.exists('token.json'):
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open('token.json', 'w') as token:
        token.write(creds.to_json())

form_service = discovery.build('forms', 'v1', credentials=creds)
drive_service = discovery.build('drive', 'v3', credentials=creds)
gmail_service = discovery.build("gmail", "v1", credentials=creds)


print(" ---- Lector de Formularios: Iglesia Episcopal Costarricense ----")
print(" ")
print(" ")

def getBooleanConfig(key, question):
    setting = False
    try:
        setting = configData.get(key) == "true"
    except:
        setting = click.confirm(question, default=True)
    return setting

processAllFiles = getBooleanConfig("processAllFilesInFolder","Procesar TODOS los archivos de cada folder? Si escoge No, se preguntara por cada archivo individualmente")

try:
    files = []
    folders = []
    page_token = None
    while True:
        foldersResponse = drive_service.files().list(q="'"+ configData["formFolderId"] +"' in parents and mimeType = 'application/vnd.google-apps.folder'",
                                        spaces='drive',
                                        fields='nextPageToken, '
                                                'files(id, name)',
                                        pageToken=page_token).execute()
        folders.extend(foldersResponse.get('files', []))
        page_token = foldersResponse.get('nextPageToken', None)
        if page_token is None:
            break

    for folder in folders:
        print("Procesando folder "+ folder.get("name"))
        if not click.confirm("Procesar archivos del folder "+ folder.get("name") +"?"):
            continue
        while True:
            filesResponse = drive_service.files().list(q="'"+ folder.get("id")+"' in parents AND mimeType='application/vnd.google-apps.form'",
                                                    spaces='drive',
                                                    fields='nextPageToken, '
                                                            'files(id, name)',
                                                    pageToken=page_token).execute()
            for file in filesResponse.get('files', []):
                print(F'Encontrado archivo: {file.get("name")}, {file.get("id")}')
                files.extend(filesResponse.get('files', []))
                if processAllFiles:
                    formIds.append(file.get("id"))
                elif click.confirm("Procesar este archivo?", default=True):
                    formIds.append(file.get("id"))
            page_token = filesResponse.get('nextPageToken', None)
            if page_token is None:
                break

except HttpError as error:
    print(F'Error: {error}')

print(" ")
print(" ")

for formId in formIds:
    form = form_service.forms().get(formId=formId).execute()
    formName = form['info']['documentTitle']
    print("Leido formulario con nombre: " + formName)
    forms.append(form)

print("")
print("Procesando Formularios...")
print("")

churchNamesSet = False

if forms and not churchNamesSet:
    print("")
    print("Obteniendo nombres de congregaciones...")
    print("")
    form = forms[0]
    for item in form.get("items"):
        if CHURCH_QUESTION_ID in item.get("title"):
            for option in item.get("questionItem").get("question").get("choiceQuestion").get("options"):
                churchNames.append(option.get("value"))
            churchNamesSet = True

for name in churchNames:
    print(name)
    emailPerChurch[name] = {}

def getQuestionIds(form):
    questionIds = {}
    celebrantIndex = 0
    assistantIndex = 0
    commulgantIndex = 0
    for item in form.get("items"):
        #print(" DEBUG Processing Item ")
        #print(json.dumps(item, indent=4))
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

writeFilePerForm = getBooleanConfig("writeFilePerForm", "Escribir archivo por formulario?")

for form in forms:
    print(" ")
    formName = form['info']['documentTitle']
    formName.replace("//", "-")
    formName.replace("\/", "-")
    fileName = path.relpath('reportesPorFormulario/reporte_'+formName+'.csv')
    fileName = fileName.replace("(", "")
    fileName = fileName.replace(")", "")
    print(" ------- FORMULARIO: " + formName)
    churchQuestionId = ""
    questionIds = getQuestionIds(form)
    churchQuestionId = questionIds[CHURCH_QUESTION_TITLE]
    print("")
    # print("ID for church question: "+ churchQuestionId)
    print("Procesando respuestas...")
    responseResponse = form_service.forms().responses().list(formId=form.get("formId")).execute()
    responseList = responseResponse.get("responses")
    #print(json.dumps(responseList, indent=4))
    if not responseList:
        print(" --- ERROR: No hay respuestas para este formulario. ---")
        continue
    print("Encontradas "+ str(len(responseList)) +" respuestas para este formulario.")
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
                print("Encontrada respuesta para esta iglesia: " + churchAnswer)
                if churchAnswer in churchesWhoAnsweredThisForm:
                    print("Ya existe una respuesta de esta iglesia para este formulario.")
                    print("Ignorando esta respuesta.")
                    continue
                if writeFilePerForm:
                    writer.writerow(churchResponse.individualFormRow.getDataList())
                churchesWhoAnsweredThisForm.append(churchAnswer)
                if not churchAnswer in responsesPerChurch:
                    responsesPerChurch[churchAnswer] = []
                responsesPerChurch[churchAnswer].append(churchResponse)

            except Exception as e:
                print("ERROR GRAVE: No se pudo obtener los datos de esta respuesta.")
                print(e)
        for church in churchNames:
            if not church in churchesWhoAnsweredThisForm:
                print ("--- IGLESIA " + church + " NO RESPONDIO ESTE FORMULARIO -- ")
                if not church in formsMissingPerChurch:
                    formsMissingPerChurch[church] = []
                formsMissingPerChurch[church].append(form)
        globalEmailData["attachments"].append(fileName)

writeFilloutReport = getBooleanConfig("writeFilloutReport", "Imprimir reporte de llenado por iglesia?")

if writeFilloutReport:
    print("")
    print(" -- REPORTE DE LLENADO POR IGLESIA - FORMULARIOS FALTANTES ")
    print("------")

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
        print(report)
        emailPerChurch[church]["fillOutReport"] = report

writeCummulativeReportPerChurch = getBooleanConfig("writeCummulativeReportPerChurch", "Imprimir y escribir acumulados por iglesia?")

if writeCummulativeReportPerChurch:
    print("")
    print(" -- REPORTE DE ACUMULADOS POR IGLESIA")
    print("------")
    globalFileName = path.relpath('reporte_total.csv')
    globalFileName = globalFileName.replace("(", "")
    globalFileName = globalFileName.replace(")", "")
    print(" - Escribiendo a archivo: " + globalFileName)
    with open(globalFileName, 'w', encoding='UTF8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(CummulativeDataRow.getHeaderList())
        for church in responsesPerChurch.keys():
            print("------")
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

writeIndividualChurchForm = getBooleanConfig("writeIndividualChurchForm", "Escribir reporte por formulario, por iglesia?")

def sendIndividualChurchEmail(email, churchName, emailData):
    emailSender = EmailSender(gmail_service)
    emailSender.sendIndividualChurchEmail(email, churchName, emailData, fecha)

def sendGlobalEmail(email, emailData):
    emailSender = EmailSender(gmail_service)
    emailSender.sendGlobalReportEmail(email, emailData, fecha)


if writeIndividualChurchForm:
    print("")
    print(" -- REPORTE INDIVIDUAL POR IGLESIA")
    print("------")
    for church in responsesPerChurch.keys():
        fileName = path.relpath('reportesPorIglesia/reporte_formularios_'+church+'.csv')
        print(" - Escribiendo a archivo: " + fileName)
        with open(fileName, 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(IndividualDataRow.getHeaderList())
            for response in responsesPerChurch[church]:
                writer.writerow(response.individualDataRow.getDataList())
        #Add file to send as attachment
        emailPerChurch[church]["attachments"] = []
        emailPerChurch[church]["attachments"].append(fileName)      
        globalEmailData["attachments"].append(fileName)

    print("")
    print(" -- Enviando correos a iglesias")
    print("------")
    emails = configData["churchEmails"]
    for church in churchNames:
        try:
            churchEmail = emails[church]
            if churchEmail:
                print("Correo para iglesia: " + church + " es " + churchEmail)
                sendIndividualChurchEmail(churchEmail, church, emailPerChurch[church])
        except Exception as e:
            print("Error enviando correo")
            print(e)

    print("")
    print(" -- Enviando correo a oficina")
    print("------")
    email = configData.get("globalReportEmail")

    globalEmailData["attachments"].append(globalFileName)
    sendGlobalEmail(email, globalEmailData)