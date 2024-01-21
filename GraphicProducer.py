import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from loguru import logger

class GraphicProducer:
      
    def generateLinearPlot(self, dataPoints, outputFile="linear_plot.png"):
            exchangeRate = 520

            moneyVariables = ["totalOfferingsColones", 
                        "totalOfferingsDollars"]
            moneyVariablesLabels = ["Total Ofrendas Colones", f"Total Ofrendas Dólares (conv. a colones) a {exchangeRate}"]

            dateVariable = "reportDate"
            dates = []

            for point in dataPoints:
                 dates.append(point[dateVariable])
            
            peopleVariables = ["assistants", "commulgants", "totalAdditions", "totalLosses"]
            peopleVariablesLabels = ["Asistentes", "Comulgantes", "Adiciones", "Pérdidas"]

            fig, ax = plt.subplots(figsize=(10, 6))
            logger.trace(f"Producing plot with data points:{dataPoints}")
            ax.ticklabel_format(style="plain")
            for i, variable in enumerate(moneyVariables):
                y_values = []
                for point in dataPoints:
                    if "Dollars" in variable:
                        y_values.append(point[variable] * exchangeRate)
                    else:
                        y_values.append(point[variable])                
                ax.plot(dates, y_values, marker='o', linestyle='-', label=moneyVariablesLabels[i])

            # Add labels and legend
            ax.set_title("Histórico hasta el corte")
            ax.set_ylabel("Ofrendas")
            ax.set_xlabel("Semana")
            ax.grid()


            ax2 = ax.twinx()
            for i, variable in enumerate(peopleVariables):
                y_values = [point[variable] for point in dataPoints]
                ax2.plot(dates, y_values, marker='*', linestyle="dotted", label=peopleVariablesLabels[i])

            ax2.set_ylabel("Personas")

            ax.legend(loc='upper left')
            ax2.legend(loc='upper right')
            plt.savefig(outputFile, transparent=True)
            return outputFile