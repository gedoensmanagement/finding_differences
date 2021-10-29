#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from cli import Transkribus_CLI
from cts import Cts

def main():
    cli = Transkribus_CLI()
    cli.login()

    # Choose operating mode according to the user's input:
    def choose_mode():
        mode = input("Would you like to\n  1 - select and print a page or\n  2 - compare pages to find censorship?\n  > ")
        if mode == "1":   # select and print a page
            print("Please, select the collection, the document and the page you want to print:")
            cts = cli.select_page_pipeline()
            cli.print_page_from_cts(cts)
        elif mode == "2": # compare two pages to find censorship
            print("\nPlease, select two page ranges to be compared.")
            print("Define the first page range (collection, document, first page, last page):")
            page_range_original = cli.select_range_pipeline()
            print("Define the second page range (collection, document, first page, last page):")
            page_range_censored = cli.select_range_pipeline()

            print(f"Differences found between\n{page_range_original['start'].to_string()}–{page_range_original['end'].pageNr} and\n{page_range_censored['start'].to_string()}–{page_range_censored['end'].pageNr}:\n")

            cli.compare_pipeline(page_range_original, page_range_censored)
        else:
            choose_mode()
    
    choose_mode()

    cli.logout()

if __name__ == "__main__":
    main()
