from __future__ import print_function
from urllib import response

from constants import *
import google.auth
import click
import json
from apiclient import discovery
from httplib2 import Http
from oauth2client import client, file, tools
from googleapiclient.errors import HttpError
from church import ChurchResponse

formIds = []
forms = []
churchNames = []

store = file.Storage('token.json')
creds = None
if not creds or creds.invalid:
    flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
    creds = tools.run_flow(flow, store)

form_service = discovery.build('forms', 'v1', http=creds.authorize(
    Http()), discoveryServiceUrl=FORMS_DISCOVERY_DOC, static_discovery=False)

drive_service = discovery.build('drive', 'v3', http=creds.authorize(
    Http()), static_discovery=False)

print(" ---- Lector de Formularios: Iglesia Episcopal Costarricense ----")
print(" ")
print(" ")
print(" ")

processAllFiles = click.confirm("Procesar TODOS los archivos de cada folder? Si escoge No, se preguntara por cada archivo individualmente", default=True)

try:
    files = []
    folders = []
    page_token = None
    while True:
        foldersResponse = drive_service.files().list(q="'"+ FORM_FOLDER_ID +"' in parents",
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
                try: 
                    if processAllFiles:
                        formIds.append(file.get("id"))
                    elif click.confirm("Procesar este archivo?", default=True, abort=True):
                        formIds.append(file.get("id"))
                except:
                    break
            page_token = filesResponse.get('nextPageToken', None)
            if page_token is None:
                break

except HttpError as error:
    print(F'Error: {error}')

print(" ")
print(" ")

for formId in formIds:
    form = form_service.forms().get(formId=formId).execute()
    formName = form['info']['title']
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
        if item.get("title") == CHURCH_QUESTION_TITLE:
            for option in item.get("questionItem").get("question").get("choiceQuestion").get("options"):
                churchNames.append(option.get("value"))
            churchNamesSet = True
            

for name in churchNames:
    print(name)

def getQuestionIds(form):
    questionIds = {}
    celebrantIndex = 0
    assistantIndex = 0
    commulgantIndex = 0
    for item in form.get("items"):
        #print(" DEBUG Processing Item ")
        #print(json.dumps(item, indent=4))
        questionTitle = item.get("title") 
        if questionTitle == CHURCH_QUESTION_TITLE:
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
            questionIds[TRANSFERS] = item.get("questionItem").get("question").get("questionId")
        elif ("Otras causas") in questionTitle:
            questionIds[OTHER_LOSSES] = item.get("questionItem").get("question").get("questionId")
    # print(json.dumps(questionIds, indent=4))
    return questionIds

formsMissingPerChurch = {}
formsFilledPerChurch = {}
responsesPerChurch = {}

for form in forms:
    print(" ")
    #print(json.dumps(form, indent=4))
    formName = form['info']['title']
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
    for response in responseList:
        churchResponse = ChurchResponse(response, questionIds)
        #print(json.dumps(response, indent=4))
        try:
            responseAnswers = response.get("answers")
            churchQuestionAnswer = responseAnswers.get(churchQuestionId)
            churchQuestionTextAnswers = churchQuestionAnswer.get("textAnswers")
            churchAnswer = churchQuestionTextAnswers.get("answers")[0].get("value")
            # print("Encontrada iglesia para esta respuesta: " + churchAnswer)
            churchesWhoAnsweredThisForm.append(churchAnswer)
            if not churchAnswer in responsesPerChurch:
                responsesPerChurch[churchAnswer] = []
            responsesPerChurch[churchAnswer].append(churchResponse)

        except:
            print("ERROR GRAVE: No se pudo obtener los datos de esta respuesta.")
    for church in churchNames:
        if not church in churchesWhoAnsweredThisForm:
            # print ("--- IGLESIA " + church + " NO RESPONDIO ESTE FORMULARIO -- ")
            if not church in formsMissingPerChurch:
                formsMissingPerChurch[church] = []
            formsMissingPerChurch[church].append(form)


if click.confirm("Imprimir reporte de llenado por iglesia?", default=False):
    print("")
    print(" -- REPORTE DE LLENADO POR IGLESIA - FORMULARIOS FALTANTES ")
    print("------")

    for church in churchNames:
        print("")
        print("------")
        print(" Formularios Faltantes para Iglesia: " + church)
        try:
            for missingForm in formsMissingPerChurch[church]:
                print(" -- " + missingForm['info']['title'])
                print(" -- Enlace para llenarlo: " + missingForm.get("responderUri"))
        except KeyError:
            print("Esta iglesia no tiene ningun formulario faltante.")


if click.confirm("Imprimir acumulados por iglesia?", default=True):
    print("")
    print(" -- REPORTE DE ACUMULADOS POR IGLESIA")
    print("------")
    for church in responsesPerChurch.keys():
        print("------")
        totalAssistance = 0
        totalCommulgants = 0
        totalSimpleColones = 0
        totalSimpleDollars = 0
        totalDesignatedColones = 0
        totalDesignatedDollars = 0
        totalPromiseColones = 0
        totalPromiseDollars = 0
        for response in responsesPerChurch[church]:
            totalAssistance = totalAssistance + response.totalAssistants
            totalCommulgants = totalCommulgants + response.totalCommulgants
            totalSimpleColones = totalSimpleColones + response.simpleColones
            totalSimpleDollars = totalSimpleDollars + response.simpleDollars
            totalDesignatedColones = totalDesignatedColones + response.designatedColones
            totalDesignatedDollars = totalDesignatedDollars + response.designatedDollars
            totalPromiseColones = totalPromiseColones + response.promiseColones
            totalPromiseDollars = totalPromiseDollars + response.promiseDollars

        print("---- Acumulados para Iglesia: " + church)
        print(" - Total de formularios procesados para esta iglesia: " + str(len(responsesPerChurch[church])))
        print(" - Total asistentes en todo el periodo: " + str(totalAssistance))
        print(" - Total comulgantes en todo el periodo: " + str(totalCommulgants))
        print(" - Total ofrenda simple colones en todo el periodo: " + str(totalSimpleColones))
        print(" - Total ofrenda simple dolares en todo el periodo: $" + str(totalSimpleDollars))
        print(" - Total ofrenda designada colones en todo el periodo: " + str(totalDesignatedColones))
        print(" - Total ofrenda designada dolares en todo el periodo: $" + str(totalDesignatedDollars))
        print(" - Total promesa colones en todo el periodo: " + str(totalPromiseColones))
        print(" - Total promesa dolares en todo el periodo: $" + str(totalPromiseDollars))

        print(" -------- ")

