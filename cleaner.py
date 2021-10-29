#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
from pathlib import Path
from tools import IO_Tools
from dictionary import Dictionary
from itertools import product

class Cleaner:

    def __init__(self, replacement_table_path):
        self.replacement_table_path = Path(replacement_table_path)
        self.dictionary = Dictionary()

        # Load the replacement table (you can load the replacement table from a csv/tsv file
        # or remotely from a Google sheet. Take a look at tools.py to understand the details!):
        tools = IO_Tools()
        self.replacement_table = tools.replacement_table_from_file(self.replacement_table_path)

    def replace_abbreviations(self, text):
        """ Normalizes Latin spelling (u/v, i/j).
            Eliminates unnecessary diacritics (à, certè etc.).
            Resolves all abbreviations in a Latin text except the n/m-macrons.
            Uses the replacement table (self.replacement_table) to search and
            replace abbreviations.
            Returns the cleaned text. """  

        for pattern, replacement in self.replacement_table.items():
            repl = replacement['replacement']

            pattern = r"{}".format(pattern) # convert the pattern to a raw string
                                            # (otherwise "\b" does not work!!)

            # Helper function to preserve the case of the original text:
            def func(match):
                g = match.group()
                if g.islower(): return repl.lower()
                if g.istitle(): return repl.title()
                if g.isupper(): return repl.upper()
                return repl

            text = re.sub(pattern, func, str(text), flags=re.IGNORECASE)

        return text

    def tokenize(self, text):
        """ Eats a string containing the normalized text.
            Tokenizes the string separating letters and punctuation.
            Returns a list of word objects, i.e. dictionaries.
            To distinguish correctly between words and punctuation, 
            the abbreviations in the text have to be resolved 
            /before/ the tokenization. """

        words = []
        for input_word in re.split("([\s.,;:?\-=()\]])", text):
            # This pattern generates some empty elements that have
            # to be filtered out. 
            if input_word != " " and input_word != '': 
                if input_word in ".,;:?-=()]":
                    data_type = "punctuation"
                elif "#" in input_word:  
                    # TODO könnte man verbessern: wenn das Wort außer
                    # "#" noch lesbare Buchstaben enthält, ist es nicht
                    # gänzlich "unreadable".
                    data_type = "unreadable"
                else:
                    data_type = "word"

                if data_type != "word":
                    words.append({'data_type': data_type,
                                  'data': input_word})
                else:
                    words.append({'data_type': data_type,
                                  'data': input_word})

        return words

    def resolve_macrons(self, words):
        """ Resolve the macrons for a list of words (which are dicts), 
            except the first and last word. Those will be 
            checked later while resolving the line breaks. """
            
        # Search for the last word in the line (avoiding punctuation, unreadable, etc.)
        if words[-1]['data_type'] == "word":
            offset = -1
        elif len(words) > 1:
            if words[-1]['data_type'] != "word" and words[-2]['data_type'] != "word":
                offset = -3
            elif words[-1]['data_type'] != "word":
                offset = -2            
        else:
            return words

        # Resolve the macrons now:
        for word in words[1:offset]:
            if word['data_type'] == "word":
                word['data'] = self.replace_macrons(word['data'])
        return words

    def replace_macrons(self, unresolved):
        """ Eats the string of a word and replaces macrons with 'n' or 'm' 
            after checking self.dictionary for the correct replacement. 
            It returns the resolved word. If there are no macrons in the word 
            it returns the input. If no solution was found it resolves the 
            macron as '●' so that you can resolve it manually. """
        
        thisword = unresolved.lower()
        replacements = {'ā': 'a',
                        'ē': 'e',
                        'ō': 'o',
                        'ū': 'u',
                        'ī': 'i'}
        mns = ['m', 'n']
        candidates = []
        # Get a list of all vocals with macrons in this word:
        macrons = re.findall(r'[āēīōū]', thisword)
        if len(macrons) != 0:
            # Generate lists with all possible replacement comibinations:
            # (https://www.geeksforgeeks.org/python-extract-combination-mapping-in-two-lists/)
            combinations = list(list(zip(macrons, e)) for e in product(mns, repeat=len(macrons)))
            # For every combination, ask the dictionary if the word exists:
            for c in combinations:
                new_word = thisword
                # perform all the replacements suggested in this combination:
                for pair in c:
                    new_word = re.sub(pair[0], replacements[pair[0]]+pair[1], new_word, count=1)
                # if the new word exists, add it to the list of candidates:
                exists = self.dictionary.check_word(new_word)
                if exists: 
                    candidates.append(new_word)
            if len(candidates) != 0:
                # if there are candidates: return the first candidate:
                return candidates[0]
            else:
                # if there are no candidates: replace the macron with "●":
                for k,v in replacements.items():
                    unresolvable = re.sub(k, v+'●', unresolved)
                return unresolvable
        else:
            return unresolved

    def resolve_linebreaks(self, page):
        """ Eats a page. Inspects the first and the last word of every
            line on the page and decides whether the last word of a line 
            and the first word of the following line belong together. If 
            so, the parts are joined and the remaining empty position is
            deleted or (if the whole line would become empty) marked as 
            "empty". 
            
            NB: The first and the last word on the page are NOT
            processed by this function! You have to treat them separately 
            when you join pages. """
        nextLine = None
        for lineId, line in enumerate(page['lines']):
            
            # ====================================
            # Check if this line is not empty or already done
            if len(line['words']) == 1 and line['words'][0]['data_type'] == "empty":
                continue # This line is empty!
            
            # ====================================
            # Check if there is a next line
            try:
                nextLine = page['lines'][lineId+1]
            except:
                continue # This line is the last line on the page.

            # ====================================
            # Now that we are sure that there is a nextLine,
            # check if the nextLine is not empty and get the 
            # first word of the nextLine:
            if len(nextLine['words']) == 0:
                continue # nextLine is empty
            elif nextLine['words'][0]['data_type'] == "empty":
                continue # first word of nextLine is empty
            else:
                nextWord = nextLine['words'][0]

            # ====================================
            # Now that we are sure that there is a nextword
            # inspect the last word of this line:

            thisWord = line['words'][-1]

            # -----------------------------------
            # Last word is PUNCTUATION:
            if thisWord['data_type'] == "punctuation":
                # take the penultimate word
                # If it's a hyphenated word: join it with the next word!
                if line['words'][-1]['data'] == "-" or line['words'][-1]['data'] == "=":
                    # cut off the "-" or "=", i.e. the last word of this line
                    line['words'].pop()
                    # join the two words
                    line = self.join_words(True, 
                                            line, -1,
                                            nextLine,
                                            "hyphenated")
                    continue
                # If it's a punctuation but not "-/=" --> ends of a part of speech
                else: 
                    # do NOT join the two words
                    line = self.join_words(False,
                                            line, -2,
                                            nextLine,
                                            "ends a part of speech")
                    continue
            # -----------------------------------
            # Last word is a NORMAL WORD!
            elif thisWord['data_type'] == "word":
                # If the first letter of the nextword is uppercase:
                if nextWord['data'][0].isupper(): # nextword is a proper name
                    line = self.join_words(False,
                                            line, -1,
                                            nextLine,
                                            "capitalized")
                    continue
                else:
                    line = self.join_words(True,
                                            line, -1,
                                            nextLine,
                                            "try joining")

            else: # It's something else, e.g. "unreadable".
                print(f"CLEANER: INFO: Leaving outLeaving out {line['identifier']}: unknown data_type = {thisWord['data_type']}.")
                continue   

        return page

    def clean_word(self, text):
        """ Helper function that replaces abbreviations and
            macrons in a word (i.e. a string). Words that are joined during 
            the resolution of line breaks still need this treatment. """
        cleaned = self.replace_abbreviations(text)
        cleaned = self.replace_macrons(cleaned)
        return cleaned

    def join_words(self, yes_no, thisLine, thisWordIndex, nextLine, message):
        """ The function a) cleans the words, b) tries to join them (if 
            yes_no is True), and c) takes care of the nextLine if it is
            empty after having moved words during resolving linebreaks.
            
            yes_no        -- a boolean whether the words should be joined or not
            thisLine      -- line object (i.e. a dict) 
            thisWordIndex -- the index of the last word (-1 or -2)
            nextLine      -- line object
            message       -- a message (string) for logging. """

        if yes_no == False: # do NOT join
            # Clean the words
            thisLine['words'][thisWordIndex]['data'] = self.clean_word(thisLine['words'][thisWordIndex]['data'])
            nextLine['words'][0]['data'] = self.clean_word(nextLine['words'][0]['data'])
            return thisLine
        else:               # DO join
            clean_up = True
            if message == "hyphenated": # if hyphenated, JOIN them in any case
                combi = self.clean_word(thisLine['words'][thisWordIndex]['data'] + nextLine['words'][0]['data'])
                thisLine['words'][thisWordIndex]['data'] = combi
                del nextLine['words'][0]
            else: # ask the dictionary if thisWord and nextWord fit together:
                first = self.clean_word(thisLine['words'][thisWordIndex]['data'])
                second = self.clean_word(nextLine['words'][0]['data'])
                combination = self.clean_word(thisLine['words'][thisWordIndex]['data'] + nextLine['words'][0]['data'])
                combination = self.dictionary.check_word(combination)
                
                if combination: # The combination is in the dictionary: join the words!
                    thisLine['words'][thisWordIndex]['data'] = combination
                    del nextLine['words'][0]
                else: # The combination does not exist: do not join!
                    thisLine['words'][thisWordIndex]['data'] = first
                    nextLine['words'][0]['data'] = second
                    clean_up = False
                
            if clean_up:
                # Clean up the nextLine.
                # If nextLine looses all its words due to the joining
                # process, it cannot remain completely empty because
                # this would break the rest of the code as well as the 
                # correct order of the line_numbers! Therefore, we
                # insert one empty word as a dummy:
                if len(nextLine['words']) == 0:
                    print("CLEANER: !! Line", nextLine['identifier'], "is EMPTY after resolving hyphenation.")
                    nextLine['words'].insert(0, {'data_type': 'empty',
                                                 'data': ''})                
                # If the new composite word was followed by a punctuation:
                # move the punctuation to the end of thisLine.
                if nextLine['words'][0]['data_type'] == "punctuation":
                    thisLine['words'].append(nextLine['words'][0])
                    del nextLine['words'][0]
                # And again: make sure the next line has at least one "empty" word.
                if len(nextLine['words']) == 0:
                    print("CLEANER: !! Line", nextLine['identifier'], "is EMPTY after resolving hyphenation.")
                    nextLine['words'].insert(0, {'data_type': 'empty',
                                                 'data': ''})

        return thisLine
           
    def auto_spacer(self, line):
        """ Reads a Line object and joins all its words to a string
            while putting spaces at the correct places (e.g. no space
            before punctuation, special treatment for parenthesis etc.). 
            Returns the line as a string. """
        newline = ""
        no_leading_space = True
        for word in line['words']:
            if word['data_type'] == "word":
                if no_leading_space == True:
                    newline += word['data']
                    no_leading_space = False
                else:
                    newline += " " + word['data']
            else:
                if word['data'] == "(":
                    newline += " " + word['data']
                    no_leading_space = True
                else:
                    newline += word['data']
        
        return newline

def main():
    cleaner = Cleaner("replacement_table.tsv")
    print(cleaner.replacement_table)

    
if __name__ == "__main__":
    main()
