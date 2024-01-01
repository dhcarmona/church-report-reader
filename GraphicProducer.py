import matplotlib.pyplot as plt
from loguru import logger

class GraphicProducer:
      
    def generateLinearPlot(self, dataPoints, outputFile="linear_plot.png"):
            variables = ["assistants", "commulgants", "totalOfferingsColones", 
                        "totalOfferingsDollars", "totalAdditions", "totalLosses"]

            # Create a single plot
            fig, ax = plt.subplots(figsize=(10, 6))
            logger.trace(f"Producing plot with data points:{dataPoints} and variables: {variables}")

            # Loop through variables and plot each one with a different color
            for i, variable in enumerate(variables):
                y_values = [point[variable] for point in dataPoints]
                x_values = list(range(1, len(dataPoints) + 1))  # Use indices as y-values
                
                # Create a linear plot with a different color for each variable
                ax.plot(x_values, y_values, marker='o', linestyle='-', label=variable)

            # Add labels and legend
            ax.set_title("Linear Plot of Variables")
            ax.set_ylabel("Ofrendas en Dinero")
            ax.set_xlabel("Semana")
            ax.legend()

            # Save the plot as a PNG file
            plt.savefig(outputFile, transparent=True)
            return outputFile