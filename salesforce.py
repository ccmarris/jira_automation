#!/usr/bin/env python3
#vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
'''

 Description:

    Module to simplify interaction with Jira

 Requirements:
   Python 3.10+

 Author: Chris Marrison

 Date Last Updated: 20250207

 Todo:

 Copyright (c) 2025 Chris Marrison / Infoblox

 Redistribution and use in source and binary forms,
 with or without modification, are permitted provided
 that the following conditions are met:

 1. Redistributions of source code must retain the above copyright
 notice, this list of conditions and the following disclaimer.

 2. Redistributions in binary form must reproduce the above copyright
 notice, this list of conditions and the following disclaimer in the
 documentation and/or other materials provided with the distribution.

 THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
 FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
 COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
 INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
 BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
 LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
 CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
 LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
 ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 POSSIBILITY OF SUCH DAMAGE.

'''
__version__ = '0.0.1'
__author__ = 'Chris Marrison'
__author_email__ = 'chris@infoblox.com'


import logging
import os
import configparser
import requests

_logger = logging.getLogger(__name__)


# Custom Exceptions
class IniFileSectionError(Exception):
    '''
    Exception for missing section in ini file
    '''
    pass

class IniFileKeyError(Exception):
    '''
    Exception for missing key in ini file
    '''
    pass

class APIKeyFormatError(Exception):
    '''
    Exception for API key format mismatch
    '''
    pass


class SalesforceAPI:
    '''
    '''
    def __init__(self, inifile:str='salesforce.ini',
                 server:str = '',
                 api_key:str = '',
                 version:str = '') -> None:
        '''
        '''
        self.server = server
        self.api_key = api_key
        self.api_version = version
        
        if inifile:
            self.cfg:dict = self.read_ini(inifile)
            if not self.server:
                self.server = self.cfg.get('server')
            if not self.api_key:
                self.api_key = self.cfg.get('api_key')
            if not self.api_version:
                self.api_version = self.cfg.get('version')

        self.base_url = f'{self.server}/services/data/v{self.api_version}'
        self.query_url = f'{self.base_url}/query'

        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        return


    # ** Facilitate ini file for basic configuration including API Key

    def read_ini(self, filename:str) -> dict:
        '''
        Open and parse ini file

        Parameters:
            filename (str): name of inifile

        Returns:
            config (dict): Dictionary of BloxOne configuration elements

        Raises:
            IniFileSectionError
            IniFileKeyError
            APIKeyFormatError
            FileNotFoundError

        '''
        # Local Variables
        cfg = configparser.ConfigParser()
        config = {}
        ini_keys = [ 'server', 'api_key', 'version' ]
    
        # Check for inifile and raise exception if not found
        if os.path.isfile(filename):
            # Attempt to read api_key from ini file
            try:
                cfg.read(filename)
            except configparser.Error as err:
                _logger.error(err)

            # Look for Salesforce section
            if 'Salesforce' in cfg:
                for key in ini_keys:
                    # Check for key in BloxOne section
                    if key in cfg['Salesforce']:
                        config[key] = cfg['Salesforce'][key].strip("'\"")
                        _logger.debug(f'Key {key} found in {filename}: {config[key]}')
                    else:
                        _logger.error(f'Key {key} not found in Salesforce section.')
                        raise IniFileKeyError(f'Key "{key}" not found within' +
                                f'[Saleforce] section of ini file {filename}')
                        
            else:
                _logger.error(f'No Salesforce Section in config file: {filename}')
                raise IniFileSectionError(f'No [Salesforce] section found in ini file {filename}')
            
        else:
            raise FileNotFoundError('ini file "{filename}" not found.')

        return config


    def get(self, url:str, params:dict) -> requests.Response:
        '''
        '''
        if params:
            response = requests.get(url, headers=self.headers, params=params)
        else:
            response = requests.get(url, headers=self.headers)
        
        return response


    def query(self, query:str) -> requests.Response:
        '''
        '''
        params = {'q': query}
        response = self.get(url=self.query_url, params=params)
        
        return response


    def search_account(self, account_name):
        '''
        '''
        query = f"SELECT Name, Industry, Phone FROM Account WHERE Name LIKE '%{account_name}%'"

        response = self.query(query=query)
        
        return response


# Example usage
if __name__ == '__main__':
    access_token = 'YOUR_ACCESS_TOKEN'
    instance = 'yourInstance'
    api_version = 'vXX.X'

    salesforce_api = SalesforceAPI(access_token, instance, api_version)
    result = salesforce_api.search_account('Acme')
    print(result)
