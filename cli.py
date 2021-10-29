#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from os import EX_DATAERR
from transkribus_web import Transkribus_Web
from cleaner import Cleaner
from cts import Cts
import re
import sys
from pprint import pprint

class Transkribus_CLI:
    """ A very simple command line interface (CLI) to operate the Transkribus_Web client 
        and a pipeline which normalizes a diplomatic transcription of Latin text. 
        Caveats: No handling of erroneus user input and no possibility to go one step back. """
    def __init__(self):
        # Initialize the Transkribus_Web object:
        self.client = Transkribus_Web()
        self.cleaner = Cleaner(replacement_table_path = "replacement_table.tsv")
            
    def login(self):
        YOUR_USER_NAME = input("Transkribus user name: ")
        YOUR_PASSWORD = input("Password: ")
        success = self.client.login(YOUR_USER_NAME, YOUR_PASSWORD)
        if success == False:
            print("Wrong username or password. Try again!")
            self.login()

    def choose_collection(self):
        """ Get a list of the user's collections on the Transkribus server
            and let the user choose a collection. """
        my_collections = self.client.get_collections()

        if my_collections:
            for idx, col in enumerate(my_collections):
                print(f"{idx+1} - {col['colName']} ({col['colId']}): {col['nrOfDocuments']} documents")

            this_collection = int(input(f"Choose a collection (1-{len(my_collections)+1}): "))
            colId = my_collections[this_collection - 1]['colId']
            print(f"Opening {colId}...\n")
            return colId
        else:
            sys.exit("No collections found.")    

    def choose_document(self, colId):
        """ Get a list of documents in a collections on the Transkribus server
            and let the user choose a document. """
        my_documents = self.client.get_documents_in_collection(colId)

        if my_documents:
            for idx, doc in enumerate(my_documents):
                print(f"{idx+1} - {doc['title']} ({doc['docId']}): {doc['nrOfPages']} pages")

            this_document = int(input(f"Choose a document (1-{len(my_documents)+1}): "))
            docId = my_documents[this_document - 1]['docId']
            print(f"Opening {colId}/{docId}...\n")
            return docId
        else:
            sys.exit("No documents found.")            

    def choose_page(self, colId, docId):
        """ Get a list of pages in a document on the Transkribus server
            and let the user choose a page. Note that only pages with
            status FINAL or GT (Ground Truth) are listed (FINAL in 
            parenthesis). """
        my_pages = self.client.get_pages_in_document(colId, docId)

        if my_pages:
            page_list = []
            for page in my_pages:
                # Select only those pages with status FINAL or GT (Ground Truth):
                status = page['tsList']['transcripts'][0]['status']
                if status == "FINAL":
                    page_list.append(f"({page['pageNr']})")
                elif status == "GT":
                    page_list.append(f"{page['pageNr']}")

            print()
            print(" ".join(page_list)) # Print the list of pages in this document.
            print("(Status of page numbers in parenthesis is FINAL, otherwise it's GROUND TRUTH.)")
            pageNr = input(f"Choose a page from the list above: ")
            print(f"Opening {colId}/{docId}/{pageNr}...\n")
            return pageNr
        else:
            sys.exit("No pages with status FINAL or GT found.")

    def select_page_pipeline(self):
        """ Convenience function that glues the "choose" functions together
            to provide a workflow for selecting a page via the cli. 
            Returns a Cts object."""
        colId = self.choose_collection()
        docId = self.choose_document(colId)
        pageNr = self.choose_page(colId, docId)
        return Cts().from_string(f"tr:{colId}.{docId}:{pageNr}")

    def select_range_pipeline(self):
        """ Convenience function that glues the "choose" functions together
            to provide a workflow for selecting a page rage via the cli. 
            Returns a dict with two Cts objects (start, end)."""
        colId = self.choose_collection()
        docId = self.choose_document(colId)

        def select_range(colId, docId):
            print("\nDefine the START of the page range:")
            pageNr_start = self.choose_page(colId, docId)
            print("Define the END of the page range:")
            print("(Make sure that selected sequence has no gaps in it. There is no handling of input errors!)")
            pageNr_end = self.choose_page(colId, docId)
            if pageNr_end < pageNr_start:
                print("The end must be greater than the start!")
                select_range(colId, docId)
            
            return pageNr_start, pageNr_end
        
        pageNr_start, pageNr_end = select_range(colId, docId)

        return {"start": Cts().from_string(f"tr:{colId}.{docId}:{pageNr_start}"),
                "end": Cts().from_string(f"tr:{colId}.{docId}:{pageNr_end}")}

    def check_for_errors(self, page_xml):
        """ Helper function. Make sure that the page_xml contains
            – TextRegions
            – Baselines
            – TextEquiv, i.e. actual text in the lines. 
            This is useful for further processing of the data to prevent crashes.
            
            page_xml -- a lxml.objectify object of a page in Transkribus 
            
            Returns False if everything is OK, otherwise an error message. """
            
        ns = "{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}"
        
        if page_xml.find(f".//{ns}TextRegion") is None:
            return "PAGE-XML: ERROR: No TextRegions found."
        if page_xml.find(f".//{ns}Baseline") is None:
            return "PAGE-XML: ERROR: No BaseLines found."
        if page_xml.find(f".//{ns}TextEquiv") is None:
            return "PAGE-XML: ERROR: Lines contain no text."

        return False

    def get_custom_attributes(self, string):
        """ Helper function. Returns the custom attributes of a TextRegion as a dict. """
        custom_attributes = re.compile(r'\{(\w*?):(\w*?);\}')
        return dict(custom_attributes.findall(string))

    def get_page(self, colId, docId, pageNr):
        """ Download the page_xml data from Transkribus and process
            the text of a page. Returns an error if the page 
            does not contain TextRegions, BaseLines or actual text in 
            the lines. Otherwise, it returns a page object (i.e. a dict). """
        # Store the namespace string used by the Transkribus page_xml format:
        ns = "{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}"
        
        my_page = self.client.get_page_xml(colId, docId, pageNr)
        
        check_for_errors = self.check_for_errors(my_page)
        if check_for_errors:
            self.logout()
            sys.exit(f"ERROR processing {colId}/{docId}, page {pageNr}: {check_for_errors}")
        else:
            # Extract the lines of my_page and build a page object:
            page = {"lines": []}
            for line in my_page.Page.iter(f"{ns}TextLine"): # Cf. the section "tree iteration" in https://lxml.de/tutorial.html
                # Get the attributes of the TextRegion:
                custom_attributes_region = self.get_custom_attributes(line.getparent().attrib['custom'])
                regionNr = custom_attributes_region['index']
                # In the following line you could filter TextRegions tagged with a specific tag (like "paragraph"):
                if custom_attributes_region.get("type") == "paragraph": # Filter all TextRegions tagged as "paragraph".
                    lineNr = self.get_custom_attributes(line.attrib['custom'])['index']
                    # Build a line object
                    raw_data = line.TextEquiv.Unicode
                    cleaned = self.cleaner.replace_abbreviations(raw_data)
                    words = self.cleaner.tokenize(cleaned)
                    words = self.cleaner.resolve_macrons(words)
                    new_line = {'identifier': f"r{regionNr}l{lineNr}",
                                'raw_data': raw_data,
                                'cleaned_data': cleaned,
                                'words': words}
                    page["lines"].append(new_line)

            # Resolve linebreaks on this page:
            page = self.cleaner.resolve_linebreaks(page)

            return page

    def get_pages(self, page_range):
        """ Download the page_xml data for a sequence of pages
            from Transkribus and process the text of a pages. 
            Returns a list of page objects (i.e. dicts). """

        pages = []
        range_length = int(page_range['end'].pageNr) - int(page_range['start'].pageNr) + 1
        for this_page in range(range_length):
            pageNr = str(int(page_range['start'].pageNr) + this_page)
            page = self.get_page(colId = page_range['start'].colId, 
                                 docId = page_range['start'].docId, 
                                 pageNr = pageNr)
            cts = page_range['start']
            cts.pageNr = pageNr
            cts.passage = pageNr
            page['cts'] = cts
            pages.append(page)

        return pages

    def print_page(self, page, raw_text=False):
        """ Prints a page object to the command line. """

        for line in page['lines']:
            print(f"{line['identifier'].rjust(8)} {self.cleaner.auto_spacer(line)}")
            
            if raw_text:
                print(f"{''.rjust(8)} {line['raw_data']}")

    def print_page_from_cts(self, cts):
        """ Convenience function: Eats a Cts object, fetches the corresponding 
            page from Transkribus and prints it to the screen. """
        page = self.get_page(cts.colId, cts.docId, cts.pageNr)
        self.print_page(page, raw_text=False)      

    def extract_words_from_pages(self, pages, breaks=False):
        word_list = []
        for page in pages:
            if breaks:
                word_list.append(f"$${page['cts'].to_string()}")  # Add a page break
            for line in page['lines']:
                if breaks:
                    word_list.append(f"$${line['identifier']}")   # Add a line break
                for word in line['words']:
                    if word['data_type'] != "punctuation":
                        word_list.append(word['data'])
        return word_list

    def compare_word_lists(self, list_1, list_2):
        import difflib

        d = difflib.Differ()
        delta = d.compare(list_1, list_2)  # returns a generator
        delta = [*delta]  # converts the generator into a list

        # Functions providing markup with combining unicode characters
        def strikethrough(text):
            return ''.join([u'\u0336{}'.format(c) for c in text])

        def underline(text):
            return ''.join([u'\u0332{}'.format(c) for c in text])

        # Process the differences found with difflib:
        output = []
        for line in delta:
            # Extract the code and the data from each line:
            code = line[:1]
            data = line[2:]

            # Add markup:
            if data.startswith("$$"):
                output.append(f"\n{data[2:]}")
            else:
                if code == " ":
                    output.append(data)
                elif code == "-":
                    output.append(strikethrough(data))
                elif code == "+":
                    output.append(underline(data))

        print(" ".join(output))

    def compare_pipeline(self, page_range_original, page_range_censored):
        """ Eats a two page range dicts containing two Cts objects (start, end) produced
            by the select_range_pipeline() function. """
        original_pages = self.get_pages(page_range_original)
        censored_pages = self.get_pages(page_range_censored)
        
        original_words = self.extract_words_from_pages(original_pages, breaks=True)
        censored_words = self.extract_words_from_pages(censored_pages)

        self.compare_word_lists(original_words, censored_words)

    def logout(self):
        self.client.logout()
