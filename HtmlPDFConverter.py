import os
from pyhtml2pdf import converter
from loguru import logger

class HtmlPDFConverter:

    def convertHtmlToPDF(htmlString, pdfPath):
        options = {
            'scale': 0.5,
            'landscape' : True,
            'format': 'Letter',
            'margin': {
                'top': '0.75in',
                'right': '0.75in',
                'bottom': '0.75in',
                'left': '0.75in',
            }
        }
        logger.trace("HTML to convert:")
        logger.trace(htmlString)

        tempHtmlFilePath = pdfPath + ".html"
        with open(tempHtmlFilePath, 'w') as tempHtmlFile:
            tempHtmlFile.write(htmlString)
        try:
            absolutePath = os.path.abspath(tempHtmlFilePath)
            tempHtmlFilePathWithProtocol = f"file:///{absolutePath}"
            logger.debug(f"Converting HTML file: {tempHtmlFilePathWithProtocol}")
            return converter.convert(tempHtmlFilePathWithProtocol, pdfPath, print_options=options)
        except Exception as err:
            logger.error(err)
