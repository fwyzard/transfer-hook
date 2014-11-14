# -*- coding: utf-8 -*-
'''
Provides classes that facilitate parsing of CMS DAQ2 meta-file filenames and
contents. For example,
    
    >>> myjson = Filename('/store/lustre/mergeMacro/run229878/run229878_ls0021_streamA_StorageManager.jsn')
    >>> myjson.run 
    229878
    >>> myjson.ls
    21
    >>> myjson.stream 
    'A'
    >>> myjson.type == Type.MacroMerger
    True
    
The examples of supported JSON file types include:

    * run229878_ls0021_streamA_StorageManager.jsn
    * run229878_ls0019_streamL1Rates_mrg-c2f13-35-01.jsn
    * run229878_ls0000_MiniEoR_bu-c2e18-09-01.jsn
        
USAGE:
    python metafile.py ## run unit tests
    python metafile.py -v ## run unit tests with verbose output
'''

__author__     = 'Jan Veverka'
__copyright__  = 'Unknown'
__credits__    = []
__licence__    = 'Unknown'
__version__    = '0.1.1'
__maintainer__ = 'Jan Veverka'
__email__      = 'veverka@mit.edu'
__status__     = 'Development'


import os
import enum

## Enumerates different types of JSON meta files.
Type = enum.enum('MacroMerger', 'MiniEoR', 'Unknown')

#_______________________________________________________________________________
class Filename(object):
    '''
    Takes a filename of a meta-data file, parses it and stores the results in
    its attributes.
    
    The given path is required to be of the form run<N>_ls<M>_*_*.jsn
    with <N> and <M> denoting integers, eventually padded with zeroes:
        
        >>> Filename('foo')
        Traceback (most recent call last):
            ...
        ValueError: Bad filename `foo', expect `.jsn' extension!

        >>> Filename('foo.jsn')
        Traceback (most recent call last):
            ...
        ValueError: Bad filename `foo.jsn', expect `*_*_*_*.jsn' form!
        
        >>> Filename('f_o_o_bar.jsn')
        Traceback (most recent call last):
            ...
        ValueError: Bad filename `f_o_o_bar.jsn', expect `run<N>_*_*_*.jsn' form!
        
    '''
    def __init__(self, path):
        self.path      = path
        self.dirname   = os.path.dirname(path)
        self.basename  = os.path.basename(path)
        self._parse_basename()

    def _parse_basename(self):
        root, ext = os.path.splitext(self.basename)
        if not ext == '.jsn':
            self._raise_bad_filename("expect `.jsn' extension")
        tokens = root.split('_')
        if not len(tokens) == 4:
            self._raise_bad_filename("expect `*_*_*_*.jsn' form")
        runtoken, lumitoken = tokens[:2]
        self._parse_runnumber(runtoken)
        self._parse_lumi(lumitoken)
        self._parse_file_type(tokens[2])

    def _raise_bad_filename(self, msg=''):
        if msg:
            msg = ', ' + msg
        raise ValueError, "Bad filename `%s'%s!" % (self.basename, msg)

    def _parse_runnumber(self, token):
        try:
            if 'run' not in token:
                raise ValueError
            self.run = int(token.replace('run', ''))
        except ValueError:
            self._raise_bad_filename("expect `run<N>_*_*_*.jsn' form")

    def _parse_lumi(self, token):
        try:
            if 'ls' not in token:
                raise ValueError
            self.ls = int(token.replace('ls', ''))
        except ValueError:
            self._raise_bad_filename("expect `*_ls<M>_*_*.jsn' form")
            
    def _parse_file_type(self, token):
        if 'stream' in token:
            self.type = Type.MacroMerger
            self._parse_stream(token)
        elif 'MiniEoR' in token:
            self.type = Type.MiniEoR
        else:
            self.type = Type.Unknown
            
    def _parse_stream(self, token):
        self.stream = token.replace('stream', '')
## Filename


#_______________________________________________________________________________
class File(Filename):
    def __init__(self, path):
        Filename.__init__(self, path)
        pass
## File


#_______________________________________________________________________________
if __name__ == '__main__':
    import doctest
    doctest.testmod()
