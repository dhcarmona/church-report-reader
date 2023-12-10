import base64
from email.mime.text import MIMEText
from email.message import EmailMessage
from requests import HTTPError

class EmailSender:
        
    def __init__(self, gmailService):
        self.gmailService = gmailService

    def sendEmail(self, email, churchName, emailData, date):
        print("Enviando correo a iglesia " + churchName + " con datos:")
        filloutReport = emailData.get("fillOutReport")
        cummulativeReport = emailData.get("cummulativeReport")
        if (filloutReport and cummulativeReport):
            emailSubject = "[Iglesia Episcopal - "+ churchName +"] Reporte con corte al " + date
            emailIntro = "Bendiciones. \n\nA continuación se provee un reporte general de las estadísticas reportadas para la congregación " + churchName + " durante el periodo que comprende a la actual Convención Diocesana, con corte al " + date + ".\n"
            emailIntro = emailIntro + "Se adjunta un archivo que puede ser usado en Microsoft Excel con la mayoría de la información reportada.\n\n\n"
            emailOutro = "\n\n --------- \n Esta información es generada automáticamente, por favor responder a este correo, o escribir al hermano Diego Carmona al correo dhcarmona@gmail.com "
            emailContents = emailIntro + filloutReport + "\n\n" + cummulativeReport + emailOutro
            message = EmailMessage()
            message.set_content(emailContents)
            message['to'] = email
            message['subject'] = emailSubject
            attachments = emailData.get("attachments")
            print(attachments)
            if attachments:
                for attachment in attachments:
                    print("Agregando adjunto: " + attachment)
                    with open(attachment, 'rb') as content_file:
                        print("Abriendo adjunto: " + attachment)
                        content = content_file.read()
                        print("Contenido adjunto: " + content.decode("utf-8"))
                        message.add_attachment(content, maintype='application', subtype= (attachment.split('.')[1]), filename=attachment)
            create_message = {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}
            try:
                message = (self.gmailService.users().messages().send(userId="me", body=create_message).execute())
            except HTTPError as error:
                print("An error occurred: " + error)
                message = None
        else:
            print("Error: no se encontraron datos necesarios para correo.")
            print("filloutreport:" + filloutReport)
            print("cummulativereport:" + cummulativeReport)


