#!/usr/bin/env python
# -*- encoding: UTF-8 -*-

"""
pdf-factory
~~~~~~~~~~~

Parse a JSON to generate several PDFs then merge them in a single file.
"""

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

log = logging.getLogger(__name__)


####
# Module configuration
# Full path to WKHTMLTOPDF binary
WKHTMLTOPDF = 'wkhtmltopdf-i386'
# Full path to PDFTK binary
# pypdftk.PDFTK_PATH = '/usr/bin/pdftk'
# Path where the final PDF files are stored
BASE_OUTPUT_DIR = "./outputs/"
# WKHTMLTOPDF conversion timeout
TIMEOUT = 2400
# Should we stop process if error occurs ?
ABORT_ON_FAILURE = True
###


def usage():
    ''' print CLI usage '''
    print "usage:\t", sys.argv[0], "foo.json"
    print "\t", sys.argv[0], "http://www.foo.bar/document.json"


def set_pdftk_path(path):
    ''' Setter for pdftk path (usefull when pdfFactory is used as module) '''
    pypdftk.PDFTK_PATH = path


def clean_failure(tmp_dir, callback_url=None):
    ''' clean tmp folder and call callback '''
    if callback_url:
        success_callback(False, callback_url)
    clean_tmp(tmp_dir)
    sys.exit()


def clean_tmp(folder):
    ''' clean the temp directory '''
    log.info("Deleting temporary folder: '%s'...", folder)
    shutil.rmtree(folder)


def check_output_folder(root, path, create_folder=False):
    ''' raise exception if path is not inside root '''
    if not os.path.abspath(path).startswith(os.path.abspath(root)):
        raise Exception('incorrect path:%s', path)
    if create_folder:
        outdir = os.path.dirname(path)
        if not os.path.lexists(outdir):
            os.makedirs(outdir)


def make_tmp_file(tmp_dir, suffix='.pdf'):
    ''' shortcut to create a new PDF file '''
    handle, filename = tempfile.mkstemp(dir=tmp_dir, suffix=suffix)
    os.close(handle)
    return filename


def success_callback(success, callback_url):
    ''' emit a POST request to the callback_url with the generation result '''
    if callback_url is not None:
        payload = '{"success":%s}' % str(success).lower()
        try:
            log.info("Informing callback")
            requests.post(callback_url, data=payload, timeout=5)
        except:
            log.error("Can't post to callback !\n%s", traceback.format_exc())


def call_wkhtmltopdf(uri, tmp_dir, options=[]):
    ''' call WKHTMLTOPDF binary with a timeout and return generated file path '''

    pdf_filename = make_tmp_file(tmp_dir)

    log.info("Calling WKHTMLTOPDF on '%s'", uri)

    wk_options = [
        WKHTMLTOPDF
    ]
    if options:
        wk_options += options

    wk_options.append(uri)
    wk_options.append(pdf_filename)

    p = subprocess.Popen(wk_options)
    timeout = TIMEOUT
    while p.poll() is None:
        if timeout == 0:
            p.terminate()
            log.error('Wkhtmltopdf took too much time processing "%s". Aborting.', uri)
            raise Exception('WKHTMLTOPDF_TIMEOUT', uri)
        timeout -= 1
        sleep(0.05)
    if p.returncode != 0 and ABORT_ON_FAILURE:
        log.error('Wkhtmltopdf return code is not zero. Aborting. (URI: "%s")', uri)
        raise Exception('WKHTMLTOPDF_ERROR', uri)
    log.info("WKHTMLTOPDF ended successfully.")
    return pdf_filename


def process_item(item, tmp_dir):
    '''Process a single item from the JSON config
          - download remote resources
          - convert HTML to PDF
          - copy local resources
          - use supplied data to fill the PDF form fields
    '''
    log.debug("Processing item: '%s'", item)

    uri = item['uri']
    fill_forms = True
    process_file = True
    if 'output' in item and os.path.lexists(item['output']):
        # if the file has already been generated
        if item.get('overwrite', True):
            os.remove(item['output'])
        else:
            # we reuse the existing file
            pdf_filename = make_tmp_file(tmp_dir)
            log.info("Copying existing file '%s' to temporary '%s'...", item['output'], pdf_filename)
            shutil.copy2(item['output'], pdf_filename)
            process_file = False
    if process_file:
        if uri.startswith(('http://', 'https://')):
            f = requests.head(uri)
            f.raise_for_status()
            ftype = f.headers['content-type']
            if ftype.startswith('application/json'):
                # Start script recursively (ToDo)
                print "JSON !"
            elif ftype.startswith('application/pdf'):
                # download the PDF
                download = requests.get(uri)
                download.raise_for_status()
                pdf_filename = make_tmp_file(tmp_dir)
                log.info("Saving pdf from network to local '%s'", pdf_filename)
                # Write PDF
                with open(pdf_filename, 'wb') as f:
                    f.write(download.content)
            elif ftype.startswith('text/html'):
                # Make PDF from URL
                fill_forms = False
                pdf_filename = call_wkhtmltopdf(item['uri'], tmp_dir, item.get('options'))
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
                pdf_filename = make_tmp_file(tmp_dir)
                log.info("Copying '%s' to '%s'...", uri, pdf_filename)
                shutil.copy2(uri, pdf_filename)
            else:
                raise Exception('Unsupported file type', ftype)

        if 'output' in item:
            output = os.path.join(BASE_OUTPUT_DIR, item['output'])
            check_output_folder(BASE_OUTPUT_DIR, output, create_folder=True)
            shutil.copy2(pdf_filename, output)

    # Use data (item specific as well as global) to fill the PDF forms
    if fill_forms and item.get('data'):
        log.info("Filling '%s' with data...", pdf_filename)
        filled_filename = make_tmp_file(tmp_dir)
        try:
            pypdftk.fill_form(pdf_filename, item['data'], filled_filename)
        except:
            if os.path.lexists(filled_filename):
                os.remove(filled_filename)
            # raise
            log.error("Got an exception when filling PDF '%s'. Using empty one instead.", pdf_filename)
            filled_filename = pdf_filename
        pdf_filename = filled_filename

    return pdf_filename


def process(config):
    ''' parse the JSON configuration then process each item independently '''
    tmp_dir = tempfile.mkdtemp(prefix="pdfFactory-")
    callback_url = config.get('callback', None)

    if not os.path.lexists(config['output']) or config.get('overwrite', True):
        try:
            merge_list = []
            for item in config['items']:
                item_data = {}
                if 'data' in config:
                    item_data.update(config['data'])
                if 'data' in item:
                    item_data.update(item['data'])
                item['data'] = item_data
                merge_list.append(process_item(item, tmp_dir))
        except KeyError as e:
            log.error("Error when parsing JSON file, some important values are missing !")
            log.error("Missing value: %s", e)
            clean_failure(tmp_dir, callback_url)
        except:
            log.error("Cannot proceed, got an unknown error:\n %s\n", traceback.format_exc())
            clean_failure(tmp_dir, callback_url)

        # Merge resulting PDF
        log.debug("Merging pdf: %s...", str(merge_list))

        # So A/foo/../B don't become A/
        output = os.path.join(BASE_OUTPUT_DIR, config['output'])
        check_output_folder(BASE_OUTPUT_DIR, output, create_folder=True)
        pypdftk.concat(merge_list, output)
    else:
        log.info("Document '%s' already exists and do not need re-generation.", config['output'])

    success_callback(True, callback_url)
    clean_tmp(tmp_dir)


####
# Entry point
###
if __name__ == '__main__':
    log.addHandler(logging.StreamHandler())
    if ("--help" in sys.argv) or ("-h" in sys.argv) or (len(sys.argv) != 2):
        log.debug('Started with no arg or help')
        usage()
    else:
        log.info('Started with args %s', sys.argv)
        # PARSE ARGUMENTS AND FETCH JSON
        # ftp, ssh etc ?
        if sys.argv[1].startswith(('http://', 'https://')):
            try:
                r = requests.get(sys.argv[1])
                r.raise_for_status()
                config = r.json()
            except:
                log.error("Cannot load json from '%s'.", sys.argv[1])
                sys.exit()
        else:
            try:
                json_file = open(sys.argv[1], 'r')
                config = json.load(json_file)
                json_file.close()
            except:
                log.error("Cannot read json file '%s'.", sys.argv[1])
                sys.exit()
        # Start processing json
        process(config)
    log.info('Ended successfully')
