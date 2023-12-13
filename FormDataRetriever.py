from httplib2 import Http
from googleapiclient.errors import HttpError

class FormDataRetriever:

    def __init__(self, driveAPIService, formAPIService):
        self.drive_service = driveAPIService
        self.form_service = formAPIService

    def retrieveForms(self, formFolderId, processAllFiles):
        forms = []
        try:
            files = []
            formIds = []
            page_token = None
            print("Procesando folder "+ formFolderId)
            while True:
                filesResponse = self.drive_service.files().list(q="'"+ formFolderId + "' in parents AND mimeType='application/vnd.google-apps.form'",
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
            for formId in formIds:
                form = self.form_service.forms().get(formId=formId).execute()
                formName = form['info']['documentTitle']
                print("Leido formulario con nombre: " + formName)
                forms.append(form)
        except HttpError as error:
            print(F'Error: {error}')
        return forms
    
    def retrieveFormResponses(self, formId):
       responseResponse = self.form_service.forms().responses().list(formId=formId).execute()
       return responseResponse.get("responses")
