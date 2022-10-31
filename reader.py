from __future__ import print_function
from urllib import response

import google.auth
import click
import json
from apiclient import discovery
from httplib2 import Http
from oauth2client import client, file, tools
from googleapiclient.errors import HttpError

SCOPES = "https://www.googleapis.com/auth/forms https://www.googleapis.com/auth/drive"
FORMS_DISCOVERY_DOC = "https://forms.googleapis.com/$discovery/rest?version=v1"
DRIVE_DISCOVERY_DOC = "https://drive.googleapis.com/$discovery/rest?version=v3"

# Question identifiers
CHURCH_QUESTION_TITLE = "Iglesia"


FORM_FOLDER_ID = '13GJ86ikI8fvpM975FIyDQUI3hlnlhrfu'

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

print("")
print(" --- REPORTE DE LLENADO ---")
print("")


formsMissingPerChurch = {}
formsFilledPerChurch = {}

for form in forms:
    print(" ")
    formName = form['info']['title']
    print(" ------- FORMULARIO: " + formName)
    churchQuestionId = ""
    for item in form.get("items"):
        if item.get("title") == CHURCH_QUESTION_TITLE:
            #print(json.dumps(item, indent=4))
            churchQuestionId = item.get("questionItem").get("question").get("questionId")
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
        #print(json.dumps(response, indent=4))
        try:
            responseAnswers = response.get("answers")
            churchQuestionAnswer = responseAnswers.get(churchQuestionId)
            churchQuestionTextAnswers = churchQuestionAnswer.get("textAnswers")
            churchAnswer = churchQuestionTextAnswers.get("answers")[0].get("value")
            # print("Encontrada iglesia para esta respuesta: " + churchAnswer)
            churchesWhoAnsweredThisForm.append(churchAnswer)
            if not church in formsFilledPerChurch:
                formsFilledPerChurch[church] = []
            formsFilledPerChurch[church].append(form)
        except:
            print("ERROR GRAVE: No se pudo obtener los datos de esta respuesta.")
    for church in churchNames:
        if not church in churchesWhoAnsweredThisForm:
            # print ("--- IGLESIA " + church + " NO RESPONDIO ESTE FORMULARIO -- ")
            if not church in formsMissingPerChurch:
                formsMissingPerChurch[church] = []
            formsMissingPerChurch[church].append(form)

print("")
print(" -- REPORTE DE LLENADO POR IGLESIA - FORMULARIOS FALTANTES ")
print("------")

if click.confirm("Imprimir reporte de llenado por iglesia?", default=False):
    for church in churchNames:
        print("")
        print("------")
        print(" Formularios Faltantes para Iglesia: " + church)
        for missingForm in formsMissingPerChurch[church]:
            print(" -- " + missingForm['info']['title'])
            print(" -- Enlace para llenarlo: " + missingForm.get("responderUri"))
