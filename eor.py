#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Detects the macromerger end-of-run and reacts to it by closing the given run.

Jan Veverka, 13 November 2014, veverka@mit.edu

USAGE:
    ./eor.py eor.cfg

TODO:
    * Add protection against missing MiniEoR files; options include:
        * Add the total sum over all BUs of the processed number of events 
          from upstream in the MiniEoR file
        * Obtain the list of BUs from somewhere and make sure we have
          all the MiniEoR files.
    * Factor out the Run class into a separate file
'''

__author__     = 'Jan Veverka'
__copyright__  = 'Unknown'
__credits__    = []
__licence__    = 'Unknonw'
__version__    = '0.1.1'
__maintainer__ = 'Jan Veverka'
__email__      = 'veverka@mit.edu'
__status__     = 'Development'

import ConfigParser
import glob
import json
import logging
import os
import sys

import bookkeeper
import metafile

from merger.cmsDataFlowCleanUp import isCompleteRun

logger = logging.getLogger(__name__)

#_______________________________________________________________________________
def main():
    '''
    Main entry point of execution.
    '''
    cfg = get_config()
    setup(cfg)
    logger.info('Start processing ...')
    process(cfg)
    logger.info('Exiting with great success!')
## main


#_______________________________________________________________________________
class Config(object):
    '''
    Extracts configuration from the config file and holds its data
    in memory during run time.
    '''
    def __init__(self, filename=None):
        self.filename = filename
        self.general_dryrun = True
        self.input_path = '/store/lustre/transfer'
        ## Set to None for logging to STDOUT
        self.logging_filename = 'eor.log'
        self.logging_level = logging.INFO
        self.logging_format = (r'%(asctime)s %(name)s %(levelname)s: '
                               r'%(message)s')
        self.runs_first = 230195
        self.runs_last  = 230201
        if filename:
            self._parse_config_file()
    ## __init__

    def _parse_config_file(self):
        parser = ConfigParser.ConfigParser()
        parser.read(self.filename)
        self.input_path = parser.get('Input', 'path')
        self.logging_filename = parser.get('Logging', 'filename')
        self.logging_level = getattr(logging, parser.get('Logging', 'level'))
        self.logging_format = parser.get('Logging', 'format', True)
    ## _parse_config_file
## Config


#_______________________________________________________________________________
def get_config():
    if len(sys.argv) == 1:
        return Config()
    elif len(sys.argv) == 2:
        return Config(sys.argv[1])
    else:
        logger.critical("Invalid args: %s" % str(sys.argv))
        print_usage()
        sys.exit(1)
## get_config


#_______________________________________________________________________________
def setup(cfg):
    '''
    Sets up the logging configuration.  Plan to apply configuration.
    '''
    ## Hack to undo logging config from the merger
    logger.root.handlers = []
    logger.disabled = 0
    ## Now reconfigure the logging
    logging.basicConfig(filename = cfg.logging_filename,
                        level    = cfg.logging_level,
                        format   = cfg.logging_format)
    bookkeeper._dry_run = cfg.general_dryrun
## setup


#_______________________________________________________________________________
def process(cfg):
    logger.info('Processing path %s ...' % cfg.input_path)
    for run in get_runs(cfg):
        if run.is_complete2():
            logger.info('Closing run %d ...' % run.number)
            bookkeeper._run_number = run.number
            bookkeeper.main()
            run.close()
        else:
            logger.warning('Run %d is incomplete!' % run.number)
    logger.info('Finished processing path %s.' % cfg.input_path)
## process


#_______________________________________________________________________________
def get_runs(cfg):
    runs = []
    dirnames = glob.glob(os.path.join(cfg.input_path, 'run*'))
    dirnames.sort()
    for dirname in dirnames:
        logger.debug("Inspecting `%s' ..." % dirname)
        try:
            run = Run(dirname)
            if cfg.runs_first and run.number < cfg.runs_first:
                logger.debug('Skipping run %d < %d because it is outside '
                              'of the range.' % (run.number, cfg.runs_first))
                continue
            if cfg.runs_last and run.number > cfg.runs_last:
                logger.debug('Skipping run %d > %d because it is outside '
                              'of the range.' % (run.number, cfg.runs_first))
                continue
            if run.is_closed():
                logger.debug('Skipping run %d because it is already closed.' %
                              run.number)
                continue
            logger.debug('Adding run %d to the processing.' % run.number)
            runs.append(run)
        except ValueError:
            logger.debug("Skipping `%s'." % dirname)
    return runs
# get_runs


#_______________________________________________________________________________
class Run(object):
    def __init__(self, path, suffix='hook'):
        self.path = path
        self.suffix = suffix
        self.name = os.path.basename(self.path)
        self.number = int(self.name.replace('run', ''))
        eorname = '_'.join([self.name, 'ls0000', 'TransferEoR', suffix])
        self.eorpath = os.path.join(self.path, eorname + '.jsn')
    def is_complete(self, bu_count=15):
        eorfiles = self._get_minieor_files()
        if len(eorfiles) != bu_count:
            return False
        for eorfile in eorfiles:
            if not eorfile.is_run_complete():
                return False
        return True
    def is_complete2(self, debug=10, threshold=1.0):
        isCompleteRun(debug = debug,
                      theInputDataFolder = self.path,
                      completeMergingThreshold = threshold,
                      outputEndName = self.suffix)
        name = '_'.join([self.name, 'ls0000', 'MacroEoR', self.suffix])
        with open(os.path.join(self.path, name + '.jsn')) as source:
            data = json.load(source)
        return data['isComplete']
    def _get_minieor_files(self):
        mask = os.path.join(self.path, '*MiniEoR*.jsn')
        return [metafile.MiniEoRFile(f) for f in glob.glob(mask)]
    def is_open(self):
        '''
        A run is open when it is not closed.
        '''
        return not is_closed(self)
    def is_closed(self):
        '''
        A run is closed if the TransferEoR JSON exists.
        '''
        return os.path.exists(self.eorpath)
    def close(self):
        '''
        Creates the TransferEoR file
        '''
        logger.info("Creating `%s' ..." % self.eorpath)
        with file(self.eorpath, 'a') as destination:
            pass
## Run


#_______________________________________________________________________________
def print_usage():
    print 'USAGE: ./eor.py [config]'
## print_usage


#_______________________________________________________________________________
if __name__ == '__main__':
    import user
    main()
# End of the module eor.py
