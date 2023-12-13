import csv
from loguru import logger

class CSVWriter:
    def __init__(self, file_name, header):
        self.file_name = file_name
        self.header = header
        self.header_length = len(header)
        self.file = open(file_name, mode='w', newline='')
        self.writer = csv.writer(self.file)
        self.writer.writerow(header)

    def writeRow(self, row):
        if len(row) != self.header_length:
            print(f"Error: Number of elements in the row ({len(row)}) does not match the header length ({self.header_length}).")
        else:
            self.writer.writerow(row)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.file.close()
