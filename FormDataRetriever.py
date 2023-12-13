from httplib2 import Http
from googleapiclient.errors import HttpError
from loguru import logger
from constants import *

class FormDataRetriever:

    def __init__(self, driveAPIService, formAPIService):
        self.drive_service = driveAPIService
        self.form_service = formAPIService

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
                    elif click.confirm("Procesar este archivo?", default=True):
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
        churchNames = []
        if self.forms:
            logger.info("")
            logger.info("Obteniendo nombres de congregaciones...")
            logger.info("")
            form = self.forms[0]
            for item in form.get("items"):
                if CHURCH_QUESTION_ID in item.get("title"):
                    for option in item.get("questionItem").get("question").get("choiceQuestion").get("options"):
                        churchNames.append(option.get("value"))
        return churchNames
