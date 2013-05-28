#!/usr/bin/env python
# -*- encoding: UTF-8 -*-
"""Parse a JSON to generate several PDF then merge them."""

import sys
import os
import traceback
import shutil
from time import sleep
import json
import logging
import subprocess
import tempfile

import requests
import pypdftk

__author__ = "LaurentMox"
__copyright__ = "Copyright 2013, Revolunet"
__credits__ = ["Revolunet"]
__license__ = "MIT"
__version__ = "0.1.0"
__maintainer__ = "LaurentMox"
__email__ = "laurent@revolunet.com"
__status__ = "Development"

log = logging.getLogger()

####
# Module configuration
WKHTMLTOPDF = 'wkhtmltopdf-i386'
BASE_OUTPUT_DIR = "./outputs/"
TIMEOUT = 2400
###


def usage():
    """usage de la ligne de commande"""
    print "usage:\t", sys.argv[0], "foo.json"
    print "\t", sys.argv[0], "http://www.foo.bar/document.json"


def clean_failure(tmp_dir, callback=None):
    successCallback(False, callback)
    clean_tmp(tmp_dir)
    sys.exit()


def clean_tmp(folder):
    """supprime les fichiers et dossiers temporaires"""
    log.info("Deleting temporary folder: \033[34m'%s'\033[m...", folder)
    shutil.rmtree(folder)


def successCallback(success, callback):
    if callback is not None:
        if success:
            payload = '{"success":true}'
        else:
            payload = '{"success":false}'
        try:
            log.info("\033[33mInforming callback\033[m")
            requests.post(callback, data=payload, timeout=2)
        except:
            log.error("\033[33mCan't post to callback !\033[m\n%s", traceback.format_exc())


def call_wkhtmltopdf(item, tmp_dir):
    uri = item['uri']
    pdf_file, pdf_filename = tempfile.mkstemp(dir=tmp_dir, suffix=".pdf")

    print "pdf_file: %s" % pdf_filename
    log.info("\033[33mCalling WKHTMLTOPDF on '%s'\033[m", uri)

    wk_options = [
        WKHTMLTOPDF,
        # '--debug-javascript',
        '--disable-smart-shrinking',
        '--print-media-type',
        '--use-xserver',
    ]
    if "options" in item:
        for option in item["options"]:
            wk_options.append(option)
    wk_options.append(uri)
    wk_options.append(pdf_filename)
    print "options: %s" % wk_options
    p = subprocess.Popen(wk_options)
    timeout = TIMEOUT
    while p.poll() is None:
        if timeout == 0:
            p.terminate()
            log.error('033[31mWkhtmltopdf process took too much time. Aborting.033[m')
            raise Exception('WKHTMLTOPDF_TIMEOUT')
        timeout -= 1
        sleep(0.05)
    log.info("\033[33mWKHTMLTOPDF ended.\033[m")
    return pdf_filename


def processItem(item, tmp_dir):
    log.debug("Processing item: \033[34m%s\033[m", item)

    uri = item['uri']
    fill_forms = True
    doFile = True
    if os.path.lexists(item.get('output', '')):
        if not item.get('overwrite', True):
            pdf_file, pdf_filename = tempfile.mkstemp(dir=tmp_dir, suffix=".pdf")
            os.close(pdf_file)
            log.info("Copying existing file \033[33m'%s'\033[m to temporary \033[33m'%s'\033[m...", item['output'], pdf_filename)
            shutil.copy2(item['output'], pdf_filename)
            doFile = False
        else:
            os.remove(item['output'])
    if doFile:
        if uri.startswith(('http://', 'https://')):
            f = requests.head(uri)
            ftype = f.headers['content-type']
            f.raise_for_status()
            if ftype.startswith('application/json'):
                # Start script recursively (ToDo)
                print "JSON !"
            elif ftype.startswith('application/pdf'):
                f = requests.get(uri)
                pdf_file, pdf_filename = tempfile.mkstemp(dir=tmp_dir, suffix=".pdf")
                log.info("\033[33mSaving pdf from network to local '%s'\033[m", pdf_filename)
                # Write PDF
                os.write(pdf_file, f.content)
                os.close(pdf_file)
            elif ftype.startswith('text/html'):
                # Make PDF form URL
                fill_forms = False
                pdf_filename = call_wkhtmltopdf(item, tmp_dir)
        else:
            # Use the 'mimetype' system command to determine filetype
            # -b is for brief response, -M is for Magic Only.
            if not os.path.isfile(uri):
                raise Exception('File do not exist', uri)
            ftype = subprocess.check_output(['mimetype', '-b', '-M', uri]).strip()
            if ftype == 'application/json':
                # Start script recursively (ToDo)
                print "JSON !"
            elif ftype == 'application/pdf':
                pdf_file, pdf_filename = tempfile.mkstemp(dir=tmp_dir, suffix=".pdf")
                os.close(pdf_file)
                log.info("Copying \033[33m'%s'\033[m to \033[33m'%s'\033[m...", uri, pdf_filename)
                shutil.copy2(uri, pdf_filename)
            else:
                raise Exception('Unsupported file type', ftype)

        if 'output' in item:
            output = os.path.abspath(os.path.join(BASE_OUTPUT_DIR, os.path.normpath(item['output']).replace("..", "")))
            outdir = os.path.dirname(output)
            if not os.path.lexists(outdir):
                os.makedirs(outdir)
            shutil.copy2(pdf_filename, output)

    # Use data (item specific as well as global) to fill PDF
    if fill_forms and item.get('data'):
        log.info("Filling \033[33m'%s'\033[m with data...", pdf_filename)
        filled_file, filled_filename = tempfile.mkstemp(dir=tmp_dir, suffix=".pdf")
        os.close(filled_file)
        try:
            pypdftk.fill_form(pdf_filename, item['data'], filled_filename)
        except:
            os.remove(filled_filename)
            raise
        pdf_filename = filled_filename

    return pdf_filename


def process(config):
    tmp_dir = tempfile.mkdtemp(prefix="pdfFactory-")
    callback = config.get('callback', None)

    if not os.path.lexists(config['output']) or config.get('overwrite', True):
        try:
            merge_list = []
            for item in config['items']:
                if 'data' in config:
                    item_data = config['data'].copy()
                else:
                    item_data = []
                if 'data' in item:
                    item_data.update(item['data'])
                item['data'] = item_data
                merge_list.append(processItem(item, tmp_dir))
        except KeyError as e:
            log.error("\033[31mError when parsing JSON file, some important values are missing !\033[m")
            log.error("Missing: \033[33m%s\033[m value.", e)
            clean_failure(tmp_dir, callback)
        except:
            log.error("\033[31mCannot proceed, got an unknown error:\033[m\n %s\n", traceback.format_exc())
            clean_failure(tmp_dir, callback)

        # Merge PDF
        log.debug("Merging pdf: \033[32m%s\033[m...", str(merge_list))
        # So A/foo/../B don't become A/
        output = os.path.abspath(os.path.join(BASE_OUTPUT_DIR, os.path.normpath(config['output']).replace("..", "")))
        outdir = os.path.dirname(output)
        if not os.path.lexists(outdir):
            os.makedirs(outdir)
        pypdftk.concat(merge_list, output)
    else:
        log.info("Document \033[33m'%s'\033[m already exists and do not need re-generation.", config['output'])

    successCallback(True, callback)
    clean_tmp(tmp_dir)


####
# Entry point
###
if __name__ == '__main__':
    # Logging configuration
    #file handler
    # logging.basicConfig(
    #     filename='pdfFactory.log',
    #     level=logging.DEBUG,
    #     format='%(asctime)s %(levelname)s - %(message)s',
    #     datefmt='%d/%m/%Y %H:%M:%S',
    # )
    log.addHandler(logging.StreamHandler())
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
                sys.exit()
        else:
            try:
                json_file = open(sys.argv[1], 'r')
                config = json.load(json_file)
                json_file.close()
            except:
                log.error("\033[31mCannot read json file '%s'.\033[m", sys.argv[1])
                sys.exit()
        # Start processing json
        process(config)
    log.info('\033[33mEnded successfully\033[m')
