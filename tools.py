#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import sys
import requests
from collections import OrderedDict
from pathlib import Path

class IO_Tools:
    """ Provides tools for data input/output operations:
        1. Read a table from a csv file
        2. Read a table from Google Sheets. """
    def __init__(self):
        pass

    # CONVENIENCE METHODS
    def replacement_table_from_google(self, url):
        lines = self.load_google_sheet(url)
        return self.csv_to_dict(lines)

    def replacement_table_from_file(self, filename, delimiter="\t"):
        lines = self.load_file(filename)
        return self.csv_to_dict(lines, delimiter)

    # CORE METHODS
    @staticmethod
    def csv_to_dict(csv_lines, delimiter=","):
        """ Reads the lines of a csv file and transforms it to an OrderedDict:
            csv_lines: A list of strings.
            delimiter: A character used to separate the columns of the csv file,
                       e.g. ";", "," or "\t" (a tabulator)
            How it works:
            - the rows of the first column become the keys of the first level
            - the fieldnames in the first row become keys of the second level
            - lines that are empty or start with "#" are skipped. 
            That means…:
                a1, b1, c1
                # This is a comment
                a3, b3, c3
            …is transformed to:
                {'a3': {'b1': 'b3', 'c1': 'c3'},
                 'a4': {'b1': 'b4', 'c1': 'c4'}} """

        csv_reader = csv.reader(csv_lines, delimiter=delimiter)
        output = OrderedDict()

        for idx, row in enumerate(csv_reader):
            if idx == 0:
                fieldnames = row # The first row contains the fieldnames.
            else:
                if not row[0].startswith("#") and (row[0].strip() != ""):   # Skips comments and empty lines.
                    output[row[0]] = {}
                    for idx, element in enumerate(row[1:], 1): # starting with the second element
                        try:
                            output[row[0]][fieldnames[idx]] = element
                        except:
                            sys.exit("IO_Tools: ERROR processing contents of a csv file.")

        print("IO_Tools: Successfully loaded csv file.")
        return output

    @staticmethod
    def load_file(file):
        """ Opens a text file and returns a list of lines. 
            file: a string representing a path to the file. """

        try:
            with open(Path(file), "r", encoding="utf-8", newline="") as f:
                txt_file = f.read()
        except:
            sys.exit("IO_Tools: ERROR: "+str(file)+" not found!")
        
        lines = txt_file.split("\n")

        return lines

    @staticmethod
    def load_google_sheet(url):
        """ Loads a spreadsheet from Google Docs and returns it as an OrderedDict. 
            (The spreadsheet must be accessible as csv for 'anyone with the link'!)
            
            url:      a URL which returns the spreadsheet in csv format as in the second
                      example shown below. This URL contains two IDs to identify the sheet 
                      and the tab within the sheet: sheet_id and gid.
            sheet_id: a unique ID to identify the sheet as part of the URL: …/d/XXXXXX…/.
            gid:      identifies a tab within the sheet. The gid of the first tab 
                      always is 0, the others have unique IDs. The gid is the last query
                      parameter in the URL. 

            To get the sheet_id and gid, open the spreadsheet in your browser and look
            at the URL in the browser window:
                                                     sheet_id            gid
                                                         ↓                ↓
            https://docs.google.com/spreadsheets/d/XXXXXXXXXXXXX/edit#gid=0
            
            Extract both IDs and paste them into the following pattern: 
                                                     sheet_id           gid
                                                         ↓               ↓
            https://docs.google.com/spreadsheets/d/XXXXXXXXXXXXX/pub?gid=0&single=true&output=csv

            This is the URL needed by this function.
            
            """
        try:
            r = requests.get(url)
        except:
            sys.exit(f"IO_Tools: ERROR: Google Sheet not found!")
        
        lines = r.content.decode().splitlines()

        return lines

def main():
    url = "https://docs.google.com/spreadsheets/d/1BALDiEL3h71xUgQuXx9aChAhI_KbFX3un1Q_4Onob28/pub?gid=0&single=true&output=csv"
    filename = "replacement_table.tsv"
    tools = IO_Tools()
    print(tools.replacement_table_from_file(filename))
    #print(tools.replacement_table_from_google(url))

    pass

if __name__ == "__main__":
    main()
