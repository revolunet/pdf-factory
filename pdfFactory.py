#!/usr/bin/env python
# -*- encoding: UTF-8 -*-
"""Parse a JSON to generate several PDF then merge them."""

import sys
import os
import traceback
import shutil
import json
import logging
import requests
import pypdftk
import subprocess
import tempfile

__author__ = "LaurentMox"
__copyright__ = "Copyright 2013, Revolunet"
__credits__ = ["Revolunet"]
__license__ = "MIT"
__version__ = "0.9.0"
__maintainer__ = "LaurentMox"
__email__ = "laurent@revolunet.com"
__status__ = "Development"

# Logging configuration
logging.basicConfig(
    filename='pdfFactory.log',
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s - %(message)s',
    datefmt='%d/%m/%Y %H:%M:%S',
)
log = logging.getLogger()
log.addHandler(logging.StreamHandler())

# Base output directory
OUTPUT_DIR = "output"
DEFAULT_TMP_DIR = tempfile.mkdtemp(prefix="pdfFactory-")


def usage():
    """usage de la ligne de commande"""
    print "usage:\t", sys.argv[0], "foo.json"
    print "\t", sys.argv[0], "http://www.foo.bar/document.json"


def clean_failure(tmp_dir=DEFAULT_TMP_DIR):
    successCallback(False)
    # clean_tmp(tmp_dir)
    sys.exit()


def clean_tmp(folder=DEFAULT_TMP_DIR):
    """supprime les fichiers et dossiers temporaires"""
    log.info("Deleting temporary folder: \033[34m'%s'\033[m...", folder)
    shutil.rmtree(folder)


def successCallback(success):
    if success:
        payload = '{"success":true}'
    else:
        payload = '{"success":false}'
    try:
        requests.post(config['callback'], data=payload, timeout=2)
    #ToDo: What to do ?
    except:
        pass


def processItem(item, tmp_dir=DEFAULT_TMP_DIR):
    log.debug("Processing item: \033[34m%s\033[m", item)
    uri = item['uri']
    output = item.get('output')

    fill_forms = True

    if uri.startswith(('http://', 'https://')):
        f = requests.head(uri)
        ftype = f.headers['content-type']
        if ftype.startswith('application/json'):
            # Start script recursively
            print "JSON !!"
        elif ftype.startswith('application/pdf'):
            f = requests.get(uri)
            pdf_file, pdf_filename = tempfile.mkstemp(dir=tmp_dir, suffix=".pdf")
            log.info("\033[33mSaving pdf from network to local '%s'\033[m", pdf_filename)
            # Write PDF
            os.write(pdf_file, f.content)
            os.close(pdf_file)
        elif ftype.startswith('text/html'):
            # Make PDF form URL
            # ToDo: Options a definir
            fill_forms = False
            pdf_file, pdf_filename = tempfile.mkstemp(dir=tmp_dir, suffix=".pdf")
            print "pdf_file: %s" % pdf_filename
            log.info("\033[33mCalling WKHTMLTOPDF on '%s'\033[m", uri)
            subprocess.check_output([
                '/home/laurent/Téléchargements/Apps/wkhtmltopdf-i386',
                '--debug-javascript',
                '--window-status',
                'ready',
                '--disable-smart-shrinking',
                '--print-media-type',
                '--use-xserver',
                uri,
                pdf_filename])
            log.info("\033[33mWKHTMLTOPDF ended.\033[m")
    else:
        # Use the 'mimetype' system command to determine filetype
        # -b is for brief response, -M is for Magic Only.
        ftype = subprocess.check_output(['mimetype', '-b', '-M', uri]).strip()
        if ftype == 'application/json':
            print "JSON !!"
        elif ftype == 'application/pdf':
            pdf_file, pdf_filename = tempfile.mkstemp(dir=tmp_dir, suffix=".pdf")
            log.info("Copying \033[33m'%s'\033[m to \033[33m'%s'\033[m...", uri, pdf_filename)
            shutil.copy2(uri, pdf_filename)
        else:
            print "\033[33mWhat did you expect ?\033[m"

    # Use data (item specific as well as global) to fill PDF
    if fill_forms and item.get('data'):
        log.info("Filling \033[33m'%s'\033[m with data...", pdf_filename)
        filled_file, filled_filename = tempfile.mkstemp(dir=tmp_dir, suffix=".pdf")
        try:
            pypdftk.fill_form(pdf_filename, item['data'], filled_filename)
        except:
            os.remove(filled_filename)
            raise
        pdf_filename = filled_filename

    return pdf_filename


####
# Entry point
###
if __name__ == '__main__':

    if ("--help" in sys.argv) or ("-h" in sys.argv) or (len(sys.argv) != 2):
        log.debug('\033[33mStarted with no arg or help\033[m')
        usage()
    else:
        log.info('Started with args \033[33m%s\033[m', sys.argv)
        # PARSE ARGUMENTS AND FETCH JSON
        # ftp, ssh etc ?
        if sys.argv[1].startswith(('http://', 'https://')):
            try:
                r = requests.get(sys.argv[1])
                config = r.json()
            except:
                log.error("\033[31mCannot load json from '%s'.\033[m", sys.argv[1])
                successCallback(False)
                sys.exit()
        else:
            try:
                json_file = open(sys.argv[1], 'r')
                config = json.load(json_file)
                json_file.close()
            except:
                log.error("\033[31mCannot read json file '%s'.\033[m", sys.argv[1])
                successCallback(False)
                sys.exit()

        try:
            output = config['output']
            merge_list = []
            for item in config['items']:
                if 'data' in config:
                    item_data = config['data'].copy()
                else:
                    item_data = []
                if 'data' in item:
                    item_data.update(item['data'])
                item['data'] = item_data
                merge_list.append(processItem(item))
        except KeyError as e:
            log.error("\033[31mError when parsing JSON file, some important values are missing !\033[m")
            log.error("Missing: \033[33m%s\033[m value.", e)
            clean_failure()
        except:
            log.error("\033[31mCannot proceed, got an unknown error:\033[m\n %s\n", traceback.format_exc())
            clean_failure()

        # Merge PDF
        log.debug("Merging pdf: \033[32m%s\033[m...", str(merge_list))
        # ToDo: Check return value
        out_pdf = pypdftk.concat(merge_list, output)
        if 'callback' in config:
            try:
                successCallback(True)
            except:
                log.error("\033[31mCannot make request to callback !\033[m")
        clean_tmp()
    log.info('\033[33mEnded sucessfuly\033[m')
