import base64
from email.mime.text import MIMEText
from requests import HTTPError

class EmailSender:
        
    def __init__(self, gmailService):
        self.gmailService = gmailService

    def sendEmail(self, email, churchName, emailData, date):
        print("Enviando correo a iglesia " + churchName + " con datos:")
        print(emailData)
        filloutReport = emailData.get("fillOutReport")
        cummulativeReport = emailData.get("cummulativeReport")
        if (filloutReport and cummulativeReport):
            emailSubject = "[Iglesia Episcopal - "+ churchName +"] Reporte con corte al " + date
            emailIntro = "Bendiciones. \nA continuación se provee un reporte general de las estadísticas reportadas para la congregación " + churchName + " durante el periodo que comprende a la actual Convención Diocesana, con corte al " + date + "\n"
            emailOutro = "\n\n --------- \n Esta información es generada automáticamente, por favor no responder a este correo. En caso de dudas o aclaraciones, por favor escribir al hermano Diego Carmona al correo dhcarmona@gmail.com ."
            emailContents = emailIntro + filloutReport + "\n" + cummulativeReport + emailOutro
            message = MIMEText(emailContents)
            message['to'] = email
            message['subject'] = emailSubject
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


