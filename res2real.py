#!/usr/bin/env python

# Filter common research paper terms to 'real' meanings. Takes a pdf and outputs an rtf.
# A Glossary for Research Reports
# Allegedly, this was originally published in 'A Random Walk in Science'.
# Keelan Chu For
# 2014-07-20

import re, sys, getopt, os, urllib


if sys.version_info.major == 3:
    print('the pdfminer module used in this script does not support Python 3')
    sys.exit()
try:
    from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
except ImportError, e:
    print('cannot find pdfminer module')
    val = raw_input('Would you download it to the current directory? y/n: ')
    if val == 'y':
        raw_input('\nOnce downloaded, unpack the file and run setup.py. Then, re-run this script.\n' +
                  'Press Enter to continue.. ')
        download_progress = 0
        def report(block_no, block_size, file_size):
            global download_progress
            download_progress += block_size
            sys.stdout.write("\rDownloaded block %i, %i/%i bytes recieved."
                  % (block_no, download_progress, file_size))
            sys.stdout.flush()
        filename, headers = urllib.urlretrieve('https://pypi.python.org/packages/source/p/pdfminer/pdfminer-20140328.tar.gz#md5=dfe3eb1b7b7017ab514aad6751a7c2ea','pdfminer-20140328.tar.gz', reporthook=report)
        print('\nFile downloaded.')
        sys.exit()
    
    elif val == 'n':
        sys.exit()
    else:
        print('Incorrect input')
        sys.exit()

from pdfminer.pdfpage import PDFPage
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.image import ImageWriter


def MultilineKeys(key):
    """for creating a new dictionary with multiline-proof keys, which will be used as a pattern to search for"""
    #    formatted_key = re.sub('\s',r'(\n*| *|\r*)',key)
    formatted_key = re.sub('\s',r'\s*\n*\r*',key)
    return formatted_key


def FixKeys(key):
    """[almost] the reverse of MultilineKeys"""
    formatted_key = re.sub('\n*\r*','',key)
    return formatted_key


def MakeRTFRed(value):
    """Add red font color rtf format to dictionary values"""
    formatted_val = '\cf2' + value + '\cf1 '
    return formatted_val


def MakeRTFStrike(str_val):
    """Add strikethrough rtf format to dictionary values"""
    formatted_val = '\strike\strikec0' + str_val + '\strike0\striked0 '
    return formatted_val


class CaseInsensitiveDict(dict):
    """for use with 'ref' dictionary
        http://stackoverflow.com/questions/2082152/case-insensitive-dictionary"""
    def __setitem__(self, key, value):
        super(CaseInsensitiveDict, self).__setitem__(key.lower(), value)
    
    def __getitem__(self, key):
        return MakeRTFRed(super(CaseInsensitiveDict, self).__getitem__(key.lower()))


class StrHolder(object):
    """object to hold the string generated from PDFMiner"""
    def __init__(self, name):
        self.name = name
        self.contents = ''
    
    def write(self, writeInput):
        #print(writeInput)
        self.contents = self.contents + writeInput


def truemeaning(pdf_str,outputfile):
    """takes a string, replaces certain terms, and creates an rtf"""
    my_file2 = open(outputfile,'w')

    definitions = {
        #        "\n\n":                                                 "\\line \n \\line \n",
        "it has long been known":                               "I didn't look up the original reference, ",
        "a definite trend is evident":                          "the data are practically meaningless",
        "of great theoretical and practical importance":        "tnteresting to me",
        "three of the samples were chosen for detailed study":  "the results of the others didn't make any sense",
        "typical results are shown":                            "this is the prettiest graph",
        "these results will be shown in a subsequent report":   "I might get around to this sometime, if I'm pushed / funded",
        "the most reliable results are those obtained by jones":"he was my graduate assistant",
        "after additional study by my colleages":               "they didn't understand it, either",
        "a highly significant area for exploratory study":      "a totally useless topic selected by my commitee",
        "it is believed that":                                  "I think",
        "it is generally believed that":                        "a couple of other people think so, too",
        "correct within an order of magnitude":                 "wrong",
        "in my experience":                                     "once",
        "in case after case":                                   "twice",
        "in a series of cases":                                 "thrice",
        "according to statistical analysis":                    "rumor has it",
        "a careful analysis of obtainable data": "three pages of notes were obliterated when I knocked over a glass of wine"
        #        "while it has not been possible to provide definite answers to these questions": "an unsuccessful experiment, but I still hope to get it published",
        #        "it is clear that much additional work will be required before a complete understanding of the phenomenon occurs": "I don't understand it",
        #        "a statistically oriented projection of the significance of these findings.": "a wild guess",
        #        "thanks are due to joe blotz for assistance with the experiment and to george frink for valuable discussions": "Blotz did the work and Frink explained to me what it meant",
        #        "it is hoped that this study will stimulate further investigation in this field": "I quit"
    }
    pdf_str = re.sub(r'\n\n', '\\line \n \\line \n', pdf_str)
    """http://stackoverflow.com/questions/6116978/python-replace-multiple-strings"""
    definitions = CaseInsensitiveDict((k, v) for k, v in definitions.iteritems())
    rep = CaseInsensitiveDict((MultilineKeys(k), v) for k, v in definitions.iteritems())
    #    print repr(rep.keys())
    #    print ''
    pattern = re.compile("|".join(rep.keys()), re.IGNORECASE)
    #    print repr(pdf_str)
    new_str = pattern.sub(lambda m: MakeRTFStrike(m.group(0))+ ' ' + definitions[FixKeys(m.group(0))], pdf_str)

    rtf_header = '{\\rtf1\\ansi{\\fonttbl\\f0\\fswiss Helvetica;}\\f0\pard\n'
    rtf_color_header = '{\colortbl;\\red0\green0\\blue0;\\red255\green0\\blue0;}\n'
    my_file2.write(rtf_header + rtf_color_header + new_str)
    my_file2.write('\n}')
    my_file2.close()


def my_pdf2txt(inputfile):
    """my trimmed version of the default pdf2txt script from PDFMiner"""
    output_str = StrHolder('output_str')
    outfp = output_str

    password = ''
    pagenos = set()
    maxpages = 0
    codec = 'utf-8'
    caching = True
    imagewriter = None
    rotation = 0
    laparams = LAParams()
    rsrcmgr = PDFResourceManager(caching=caching)

    device = TextConverter(rsrcmgr, outfp, codec=codec, laparams=laparams, imagewriter=imagewriter)

    fp = file(inputfile, 'rb')
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    for page in PDFPage.get_pages(fp, pagenos, maxpages=maxpages, password=password, caching=caching, check_extractable=True):
        page.rotate = (page.rotate+rotation) % 360
        interpreter.process_page(page)
    fp.close()
    device.close()

    return output_str.contents


def main(argv):
    def usage():
        print('usage: res2real.py [-o outputfile] inputfile')
        sys.exit(2)
    try:
        (opts, args) = getopt.getopt(argv, 'o:')
    except getopt.GetoptError: usage()
    if len(args) != 1: return usage()
    if not(args[0].endswith('.pdf')):
        print '<inputfile> must be a pdf'
        sys.exit()
    inputfile = args[0]
    outputfile = ''
    for (k, v) in opts:
        if k == '-o': outputfile = v
    if not len(outputfile):
        outputfile = os.path.splitext(inputfile)[0] + '_new.rtf'

    pdf_str = my_pdf2txt(inputfile)
#    print pdf_str

    truemeaning(pdf_str,outputfile)
    print('done!')
    print('Saved as %s\n' % outputfile)


if __name__ == "__main__":
    main(sys.argv[1:])


# Some other useful links:
# http://www.pindari.com/rtf1.html
# https://docs.python.org/2/library/re.html
# http://www.pythonforbeginners.com/regex/regular-expressions-in-python
# http://stackoverflow.com/questions/1769403/understanding-kwargs-in-python
