import base64
from email.mime.text import MIMEText
from email.message import EmailMessage
from requests import HTTPError
from loguru import logger

class EmailSender:
        
    def __init__(self, gmailService):
        self.gmailService = gmailService

    def sendGlobalReportEmail(self, email, emailData, date):
        logger.info("Enviando correo global a oficinas al correo " + email)
        emailSubject = "[Iglesia Episcopal] Estadísticas congregacionales con corte al " + date
        emailIntro = "Bendiciones. \n\nA continuación se provee un reporte general de las estadísticas reportadas para todas las congregaciones durante el periodo que comprende a la actual Convención Diocesana, con corte al " + date + ".\n"
        emailIntro = emailIntro + "Un reporte general acumulado se puede encontrar en el archivo adjunto con nombre 'reporte_total.csv'.\n\n"
        emailIntro = emailIntro + "Se adjuntan también archivos que pueden ser usados en Microsoft Excel con la mayoría de la información reportada, por cada semana, y por cada iglesia.\n\n\n"
        emailOutro = "\n\n --------- \n Esta información es generada automáticamente, si tiene dudas o necesita aclaraciones, por favor responder a este correo, o escribir al hermano Diego Carmona al correo dhcarmona@gmail.com "
        emailContents = emailIntro + "\n\n" + emailOutro
        attachments = emailData.get("attachments")
        message = EmailMessage()
        message.set_content(emailContents)
        message['to'] = email
        message['subject'] = emailSubject
        if attachments:
            for attachment in attachments:
                with open(attachment, 'rb') as content_file:
                    content = content_file.read()
                    message.add_attachment(content, maintype='application', subtype= (attachment.split('.')[1]), filename=attachment)
        create_message = {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}
        try:
            message = (self.gmailService.users().messages().send(userId="me", body=create_message).execute())
        except HTTPError as error:
            logger.info("An error occurred: " + error)
            message = None

    def sendIndividualChurchEmail(self, email, churchName, emailData, date):
        logger.info("Enviando correo a iglesia " + churchName)
        filloutReport = emailData.get("fillOutReport")
        cummulativeReport = emailData.get("cummulativeReport")
        if (filloutReport and cummulativeReport):
            emailSubject = "[Iglesia Episcopal - "+ churchName +"] Reporte con corte al " + date
            emailIntro = "Bendiciones. \n\nA continuación se provee un reporte general de las estadísticas reportadas para la congregación " + churchName + " durante el periodo que comprende a la actual Convención Diocesana, con corte al " + date + ".\n"
            emailIntro = emailIntro + "Se adjunta un archivo que puede ser usado en Microsoft Excel con la mayoría de la información reportada.\n\n\n"
            emailOutro = "\n\n --------- \n Esta información es generada automáticamente, si tiene dudas o necesita aclaraciones, por favor responder a este correo, o escribir al hermano Diego Carmona al correo dhcarmona@gmail.com "
            emailContents = emailIntro + filloutReport + "\n\n" + cummulativeReport + emailOutro
            message = EmailMessage()
            message.set_content(emailContents)
            message['to'] = email
            message['subject'] = emailSubject
            attachments = emailData.get("attachments")
            if attachments:
                for attachment in attachments:
                    with open(attachment, 'rb') as content_file:
                        content = content_file.read()
                        message.add_attachment(content, maintype='application', subtype= (attachment.split('.')[1]), filename=attachment)
            create_message = {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}
            try:
                message = (self.gmailService.users().messages().send(userId="me", body=create_message).execute())
            except HTTPError as error:
                logger.info("An error occurred: " + error)
                message = None
        else:
            logger.info("Error: no se encontraron datos necesarios para correo.")
            logger.info("filloutreport:" + filloutReport)
            logger.info("cummulativereport:" + cummulativeReport)


