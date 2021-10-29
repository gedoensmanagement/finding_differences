# -*- coding: utf-8 -*-
"""
Created on Thu Sep 17 16:38:05 2020

@author: muellerM@ieg-mainz.de
"""

import re

class Cts:
    """ The Cts object represents a "Canonical Text Service" address. 
        See http://cts.informatik.uni-leipzig.de to learn more on the Canonical 
        Text Service protocol. Depending on the namspace, you can implement your
        own parsers. """
    def __init__(self, 
                 namespace="", 
                 work="",
                 passage="",
                 subreference=""):
        self.namespace = namespace
        self.work = work
        self.passage = passage
        self.subreference = subreference
        self.m = None # used by from_string() to store a re match object temporarily
    
    def __repr__(self):
        return f"""<cts object>
    cts         : {self.to_string()}
    namespace   : {self.namespace}
    work        : {self.work}
    passage     : {self.passage}
    subreference: {self.subreference}"""
    
    def to_string(self, with_urn = False):
        """ Returns a cts address as cts string, e.g. "zt:wild1550b:fol.10r"
            If with_urn = True the address is prefixed with "urn:cts:" """

        return f"{'urn:cts:' if with_urn else ''}{self.namespace}:{self.work}{':'+self.passage if self.passage != '' else ''}{'@'+self.subreference if self.subreference != '' else ''}"

    def from_string(self, cts_string):
        """ Builds a cts object from a string containing a valid cts address.
        Make sure the string is valid cts since there is no validation yet! """

        PATTERN = r'([a-z]{2})\:([a-zA-Z0-9]*)\.?([a-zA-Z0-9]*)\:([a-z]*)([0-9]*)[\.|\:]?([0-9a-z]*)@?([0-9a-z]*)'
        p = re.compile(PATTERN)
        m = p.match(cts_string)
        self.m = m
        self.namespace = m.group(1)
        self.work = f"{m.group(2)}{'.'+m.group(3) if m.group(3) != '' else ''}"
        self.passage = f"{m.group(4)}{m.group(5)}{'.'+m.group(6) if m.group(6) != '' else ''}"
        self.subreference = m.group(7)
        
        self.explode()
        
        return self

    def explode(self):
        """ Tries to extract additional data fields from the work and passage fields
            depending on the namespace. The functions in the cts_parser can do that for us. """
        self.parse_cts(self)
        delattr(self, "m") # after parsing we can throw away the match object!
                           # (By doing so, the Cts object becomes JSON serializable!)

    def parse_cts(self, cts_object):
        """ This function defines the namespaces recognized by the Cts object
            and links them to corresponding parser functions which add further 
            properties to the object. """
        namespaces = {'zt': self.zotero_parser,
                      'tr': self.transkribus_parser,
                      'zs': self.censorship_parser}
        
        namespaces[cts_object.namespace](cts_object)    
    
    def zotero_parser(self, zt):
        """ Treats the Cts object as a Zotero cts object. """
        #print("zotero_parser")
        #print(zt)
        if zt.m.group(4) != '':
            zt.mode = zt.m.group(4)
            zt.number = zt.m.group(6)
        #print(f"Zotero extras: mode = {zt.mode}, number = {zt.number}")
        
        return zt
        
    def transkribus_parser(self, tr):
        """ Treats the Cts object as a Transkribus cts object. """
        #print("transkribus_parser")
        #print(tr)
        tr.colId = tr.m.group(2)
        tr.docId = tr.m.group(3)
        tr.pageNr = tr.m.group(5)
        #print(f"Transkribus extras:\ncol = {tr.colId}\ndoc = {tr.docId}\npage = {tr.pageNr}")
        if tr.m.group(6) != '':
            p = re.compile(r'r(\d{1,})l?(\d{1,})')
            m = p.match(tr.m.group(6))
            if m.group(1):
                tr.region = m.group(1)
                #print(f"region = {tr.region}")
            if m.group(2):
                tr.line = m.group(2)
                #print(f"line = {tr.line}")
            tr.rl = f"{'r'+tr.region if m.group(1) else ''}" + f"{'l'+tr.line if m.group(2) else ''}"
        if tr.subreference != '':
            tr.word = tr.subreference
            #print(f"word = {tr.word}")
        
        return tr
        
    def censorship_parser(self, zs):
        """ Treats the Cts object as a censorship cts. """
        #print("censorship_parser: yet to be implemented... ")
    
def main():
    test = Cts().from_string("tr:1234.5678:10.r2l11@2")
    print(test)
    print(test.__dict__)

if __name__ == "__main__":
    main()