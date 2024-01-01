import base64
import json
from email.mime.text import MIMEText
from email.message import EmailMessage
from requests import HTTPError
from loguru import logger
from jinja2 import Template
from HtmlPDFConverter import *


class EmailSender:
        
    def __init__(self, gmailService):
        self.gmailService = gmailService

    def attachFileToMessage(self, message, filePath):
        logger.debug("Attaching file: " + filePath)
        with open(filePath, 'rb') as content_file:
            content = content_file.read()
            message.add_attachment(content, maintype='application', subtype= (filePath.split('.')[1]), filename=filePath)

    def sendGlobalReportEmail(self, email, emailData, date):
        logger.info("Enviando correo global a oficinas al correo " + email)
        emailSubject = "[Iglesia Episcopal] Estadísticas congregacionales con corte al " + date
        emailIntro = "Bendiciones. <br>A continuación se provee un reporte general de las estadísticas reportadas para todas las congregaciones durante el periodo que comprende a la actual Convención Diocesana, con corte al " + date + ".<br>"
        emailIntro = emailIntro + "Un reporte general acumulado se puede encontrar en el archivo adjunto con nombre 'reporte_total.csv'.<br><br>"
        emailIntro = emailIntro + "Se adjuntan también archivos que pueden ser usados en Microsoft Excel con la mayoría de la información reportada, por cada semana, y por cada iglesia.<br><br><br>"
        emailOutro = "<br><br> --------- <br> Esta información es generada automáticamente, si tiene dudas o necesita aclaraciones, por favor responder a este correo, o escribir al hermano Diego Carmona al correo dhcarmona@gmail.com "
        emailContents = emailIntro + "<br><br>" + emailOutro
        logger.trace(emailContents)
        attachments = emailData.get("attachments")
        message = EmailMessage()
        message.add_header('Content-Type','text/html')
        message.add_alternative(
                emailContents,
                subtype="html",
            )
        message['to'] = email
        message['subject'] = emailSubject
        if attachments:
            for attachment in attachments:
                self.attachFileToMessage(message, attachment)
        create_message = {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")}
        try:
            message = (self.gmailService.users().messages().send(userId="me", body=create_message).execute())
        except HTTPError as error:
            logger.info("An error occurred: " + error)
            message = None

    def parseJinjaTemplate(self, title, churchName, cutoffDate, cummulativeData, fillOutData):
        logger.info("Parsing Jinja template")
        data = []
        dataNames = []

        if cummulativeData:
            for item in cummulativeData:
                value = cummulativeData.get(item)
                data.append(value)
                dataNames.append(item)

        templateData = {
            'email_title': title,
            'church_name': churchName,
            'cutoff_date': cutoffDate,
            'base64_logo': 'YourBase64EncodedLogo',
            'base64_image': 'YourBase64EncodedImage',
            'data': data,
            'dataNames': dataNames,
            'fillOutData' : fillOutData
        }

        logger.trace("Data for Jinja template:")
        logger.trace(json.dumps(templateData))

        # Read the HTML template from a file or provide it as a string
        with open('email_templates/church_template.html', 'r') as file:
            templateFileContents = file.read()

        # Create a Jinja2 template
        template = Template(templateFileContents)

        # Render the template with dynamic data
        renderedTemplate = template.render(templateData)

        return renderedTemplate

    def sendIndividualChurchEmail(self, churchName, email, emailData, date):
        logger.info("Enviando correo a iglesia " + churchName)
        fillOutReport = emailData.get("fillOutReport")
        cummulativeData = emailData.get("cummulativeData")
        fillOutData = emailData.get("fillOutData")
        if (not cummulativeData):
            cummulativeReport = "Esta iglesia no ha llenado ningún formulario, por lo que no tiene reporte acumulado.\n\n"
        emailSubject = "[Iglesia Episcopal - "+ churchName +"] Reporte con corte al " + date
        htmlContents = self.parseJinjaTemplate(emailSubject, churchName, date, cummulativeData, fillOutData)
        emailContents = f"""Bendiciones. <br>
        Adjunto a este correo encontrará un archivo PDF con la información estadística correspondiente al corte actual. <br> 
        Adicionamente, encontrará un archivo CSV que puede ser usado en Excel, y contiene la mayoría de la información proporcionada <br><br> 
        --------- <br> <br>
        {fillOutReport}
        --------- <br> 
        Esta información es generada automáticamente, si tiene dudas o necesita aclaraciones, por favor responder a este correo, o escribir al hermano Diego Carmona al correo dhcarmona@gmail.com "
        """
        churchPdfFileName = "pdf"+churchName+date+".pdf"

        message = EmailMessage()
        message.add_header('Content-Type','text/html')
        message.add_alternative(
                emailContents,
                subtype="html",
            )
        message['to'] = email
        message['subject'] = emailSubject
        HtmlPDFConverter.convertHtmlToPDF(htmlContents, churchPdfFileName)
        self.attachFileToMessage(message, churchPdfFileName)
        attachments = emailData.get("attachments")
        if attachments:
            for attachment in attachments:
                self.attachFileToMessage(message, attachment)
        create_message = {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}
        try:
            message = (self.gmailService.users().messages().send(userId="me", body=create_message).execute())
        except HTTPError as error:
            logger.info("An error occurred: " + error)
            message = None


