#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hunspell import Hunspell

class Dictionary:
    """ Latin dictionary built with cyhunspell: https://pypi.org/project/cyhunspell/.
        Dictionary.check_word(word) checks a single word (string) and returns True or False.
        Needs the Latin Hunspell dictionary by Karl Zeiler and Jean-Pierre Sutto 
        from https://latin-dict.github.io/docs/hunspell-la.zip  ↓↓↓↓  """
    def __init__(self):
        self.hunspell = Hunspell('la_LA', hunspell_data_dir='hunspell-la')

    def check_word(self, word):
        """ Eats a word (string) and checks whether it is in the dictionary. 
            Returns True/False. """
        if self.hunspell.spell(word):
            return word
        else:
            return False


