#!/usr/bin/env python3
#vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
'''

 Description:

    Module to simplify interaction with Jira

 Requirements:
   Python 3.8+

 Author: Chris Marrison

 Date Last Updated: 20240520

 Todo:

 Copyright (c) 2024 Chris Marrison / Infoblox

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
__version__ = '0.1.2'
__author__ = 'Chris Marrison'
__author_email__ = 'chris@infoblox.com'


import logging
import os
import sys
import datetime
import time
import argparse
import configparser
import jira
import jira.exceptions
from rich import print


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


class ISSUES():

    def __init__(self, 
                 inifile:str = 'jira.ini',
                 server:str = '',
                 user:str = '',
                 api_key:str = '',
                 field:str = ''):
        '''
        '''
        self.server:str = server
        self.user:str = user
        self.api_key:str = api_key
        self.resolution_field:str = field
        self.issue:object = None
        self.fields:list = []
        self.field_map:dict = {}

        if inifile:
            self.cfg:dict = self.read_ini(inifile)
            if not self.server:
                self.server = self.cfg.get('server')
            if not self.user:
                self.user = self.cfg.get('user')
            if not self.api_key:
                self.api_key = self.cfg.get('api_key')
            if not self.resolution_field:
                self.resolution_field = self.cfg.get('resolution_field')
        
        try:
            # Set up jira session
            self.jira_session = jira.JIRA(basic_auth=(self.user,self.api_key), 
                                          server=self.server)
            # Get fields and mappings
            self.get_fields()
            self.create_field_map()

        except:
            raise

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
        ini_keys = ['server', 'user', 'api_key', 'resolution_field']
    
        # Check for inifile and raise exception if not found
        if os.path.isfile(filename):
            # Attempt to read api_key from ini file
            try:
                cfg.read(filename)
            except configparser.Error as err:
                logging.error(err)

            # Look for BloxOne section
            if 'JIRA' in cfg:
                for key in ini_keys:
                    # Check for key in BloxOne section
                    if key in cfg['JIRA']:
                        config[key] = cfg['JIRA'][key].strip("'\"")
                        logging.debug(f'Key {key} found in {filename}: {config[key]}')
                    else:
                        logging.error(f'Key {key} not found in BloxOne section.')
                        raise IniFileKeyError(f'Key "{key}" not found within' +
                                f'[JIRA] section of ini file {filename}')
                        
            else:
                logging.error(f'No BloxOne Section in config file: {filename}')
                raise IniFileSectionError(f'No [BloxOne] section found in ini file {filename}')
            
        else:
            raise FileNotFoundError('ini file "{filename}" not found.')

        return config


    def get_issue(self, issue:str, expand:str = None) -> bool:
        '''
        '''
        status:bool = False
        try:
            self.issue = self.jira_session.issue(issue, expand=expand)
            status = True
        except:
            logging.error(f'Failed to retrieve issue: {issue}')
            status = False
        return status


    def get_transitions(self) -> bool:
        '''
        '''
        status:bool = False
        try:
            self.transitions = self.jira_session.transitions(self.issue.id)
        except:
            logging.error(f'Failed to retrieve transitions for: {self.issue}')
            status = False
        return status
    
    
    def get_resolution_key(self) -> bool:
        '''
        '''
        status:bool = False
        try:
            self.resolution_key = self.get_field_id(self.resolution_field)
            status = True
        except:
            logging.error(f'Failed to retrieve resolution field for: {self.issue}')
            status = False
        return status


    def get_field_id(self, fieldname) -> str:
        '''
        '''
        id:str = ''
        field_list:list

        field_list = self.jira_session.fields()
        for f in field_list:
            if f.get('name') == fieldname:
                id = f.get('id')
                break
        
        return id


    def status(self) -> str:
        '''
        '''
        return self.issue.fields.status.name


    def status_id(self) -> str:
        '''
        '''
        return self.issue.fields.status.id


    def transition_id(self, transition:str) -> str:
        '''
        '''
        id:str = ''
        for t in self.transitions:
            if t.get('name') == transition:
                id = t.get('id')
                break
        
        if not id:
            logging.info(f'Cannot {transition} {self.issue.key} transition not available')
        
        return id


    def resolution_id(self, transition, resolution) -> str:
        '''
        '''
        id:str = ''
        trns = self.jira_session.transitions(self.issue.key, expand='transitions.fields')
        
        # Check for resolution and get allowed values
        for r in trns:
            if r.get('name') == transition:
                av = r['fields'][self.resolution_key]['allowedValues']
                logging.debug(f'Found {transition} for issue')
                # Find the id of the allowed resolution
                # Don't know why these are different to the ids 
                # provided by JIRA.resolutions()
                for v in av:
                    if v.get('value') == resolution:
                        id = v.get('id')
                        logging.debug(f'Found {resolution} for transition')
                        break
                break

        if not id:
            logging.warning(f'Cannot find {resolution} id for {self.issue.key}')
        
        return id


    def transition_issue(self, t_id:str, r_id:str = '', comment:str = '') -> bool:
        '''
        '''
        status:bool = False
        # Confirm transition possible
        try:
            if r_id:
                self.jira_session.transition_issue(self.issue.key,
                                            transition=t_id, 
                                            fields={self.resolution_key: { 'id': r_id}},
                                            comment=comment)
            else:
                self.jira_session.transition_issue(self.issue.key,
                                            transition=t_id, 
                                            comment=comment)
            status = True
        except jira.exceptions.JIRAError as err:
            logging.error(err)
            status = False

        return status


    def get_fields(self,field:str = '') -> list:
        '''
        '''
        fields:list = []

        if not self.fields:
            # Get fields from Jira
            try:
                self.fields = self.jira_session.fields()
            except:
                raise

        if field and self.fields:
            for f in self.fields:
                if f.get('id') == field:
                    fields = [ f ]
                    break
                elif f.get('name') == field:
                    fields = [ f ]
                    break
        else:
            fields = self.fields

        return fields
    

    def create_field_map(self) -> dict:
        '''
        '''
        status:bool = False
        fields:list = []
        fmap:dict = {}

        try:
            fields = self.get_fields()
        except:
            logging.error('Failed to retrieve field mappings')
            status = False

        if fields:
            status = True
            for f in fields:
                fmap.update( { f.get('id'): f.get('name'),
                               f.get('name'): f.get('id')} )
        else:
            logging.error('Field mapping empty')
            status = False

        self.field_map = fmap

        return status


    def get_issue_type(self, name:str = 'New Feature') -> dict:
        '''
        Get the Issue Type using the name

        Parameters:
            name (str): Name of issue type defaults to 'New Feature'
        
        Returns:
            Jira issue_type object
        '''
        return self.jira_session.issue_type_by_name(name)


    def get_schema(self, project='IFR', issuetype='New Feature') -> dict:
        '''
        '''
        schema:list = []
        
        if not self.field_map:
            self.create_field_map()

        meta = self.jira_session.createmeta(projectKeys=project, 
                                            issuetypeNames=issuetype, 
                                            expand='projects.issuetypes.fields')
        schema = meta['projects'][0]['issuetypes'][0]['fields']

        return schema


    def get_required_fields(self, project='IFR', issuetype='New Feature') -> list:
        '''
        '''
        if not self.field_map:
            self.create_field_map()

        required_fields:list = []
        
        schema = self.get_schema(project=project, issuetype=issuetype)

        for field, field_value in schema.items():
            if field_value.get('required'):
                if 'customfield' in field:
                    field = self.field_map.get(field)
                required_fields.append({field: field_value})
        
        return required_fields


    def output_issue(self):
        '''
        '''
        project:str = ''
        issuetype:str = ''

        if self.issue:
            project = self.issue.fields.project.key
            issuetype = self.issue.fields.issuetype.name
            schema = self.get_schema(project=project, issuetype=issuetype)
            for k in schema.keys():
                if k in self.issue.fields.__dict__.keys():
                    print(f'{self.field_map[k]}: {getattr(self.issue.fields, k)}')
        
        else:
            print('No issue selected, use get_issue()')
        
        return


    def get_comments(self):
        '''
        '''
        return self.issue.fields.comment.comments


def MIGRATE_ISSUE():
    '''
    '''
    def __init__(self, 
                 source:str, 
                 destination:str = '', 
                 inifile:str = 'jira.ini',
                 server:str = 'https://infoblox.atlassian.net'):
        '''
        '''
        self.src = ISSUES(inifile=inifile, server=server)
        if not self.src.get_issue(source):
            assert self.src.issue
        self.dst = ISSUES(inifile=inifile, server=server)
        # self.dst.get_issue(source)

        return
        

    def migrate_issue(self, include_comments:bool = True):
        '''
        Migrate source Issue to destination Issue
        '''

        return


    def copy_comments(self):
        '''
        Copy comments from source to destination
        '''
        if self.src.issue and self.dst.issue:
            comments = self.get_comments()
            # Add comments to the target issue
            for comment in comments:
                author = comment.author.displayName
                created = datetime.strptime(comment.created, 
                                            '%Y-%m-%dT%H:%M:%S.%f%z')
                body = ( f"Comment by {author} on "
                         f"{created.strftime('%Y-%m-%d %H:%M:%S')}:\n\n{comment.body}" )
                jira.add_comment(self.dst.issue.key, body)

        else:
            if not self.src.issue:
                logging.error(f'Cannot find source Jira issue: {}')
        return

# --- Functions

def process_issue(config:str, 
                issue:str, 
                transition:str, 
                resolution:str,
                comment:str) -> bool:
    '''
    '''
    status:bool = False
    transition_id = None
    resolution_id = None


    try:
        r = ISSUES(issue=issue, inifile=config)
    
        current_status = r.status()
        current_status_id = r.status_id()
        transition_id = r.transition_id(transition)
        if transition_id:
            if transition == 'Close':
                resolution_id = r.resolution_id(transition, resolution)

            # Attempt transition
            if resolution_id:
                status = r.transition_issue(t_id=transition_id,
                                        r_id=resolution_id,
                                        comment=comment)
            else:
                status = r.transition_issue(t_id=transition_id,
                                        comment=comment)
        else:
            # Transition not possible
            status = False
        if status:
            logging.info(f'{issue} moved from {current_status} to {transition} successfully')
        else:
            logging.error(f'{issue} failed to transition from {current_status} to {transition}')


        # Debug
        logging.debug(f'{r.resolution_field}: {r.resolution_key}')
        logging.debug(f'Issue: {issue}, {current_status}: {current_status_id}, ' +
                    f'{transition}: {transition_id},' +
                    f'{resolution}: {resolution_id}' )

    except jira.exceptions.JIRAError as err:
        logging.error(err)
        status = False

    return status
    
    # Check current transi


def process_file(in_file:str, 
                 config:str,
                 transition:str,
                 resolution:str = '',
                 comment:str =''):
    '''
    '''
    count:int = 0
    success_count:int = 0
    try:
        f = open(in_file)
        for issue in f:
            issue = issue.rstrip()
            count += 1
            if process_issue(config=config, 
                        issue=issue,
                        transition=transition,
                        resolution=resolution,
                        comment=comment):
                
                success_count += 1
            else:
                logging.error(f'Failed to process Issue: {issue}')
        logging.info(f'{success_count} of {count} Issues processed successfully')
    
    except:
        raise

    return


def status_check(issue:str, config:str):
    '''
    '''
    status = False
    try:
        r = ISSUES(issue=issue, inifile=config)
        current_status = r.status()
        logging.info(f'{issue} status: {current_status}')
        status = True
    except:
        logging.error(f'{issue}: Failed to get current status')

    return status


def bulk_status_check(in_file:str, 
                 config:str):
    '''
    '''
    count:int = 0
    success_count:int = 0
    try:
        f = open(in_file)
        for issue in f:
            issue = issue.rstrip()
            count += 1
            if status_check(issue, config):
                success_count += 1
        logging.info(f'{success_count} of {count} Jira Issues processed successfully')
    
    except:
        raise

    return

def parseargs():
    '''
    Parse Arguments Using argparse

    Parameters:
        None

    Returns:
        Returns parsed arguments
    '''
    parse = argparse.ArgumentParser(description='Collected_data Excel Parser')
    parse.add_argument('-c', '--config', type=str, default='jira.ini',
                        help="Input file")
    parse.add_argument('-f', '--file', type=str, 
                        help="Input file")
    parse.add_argument('-i', '--issue', type=str, 
                        help='Jira issues to process')
    parse.add_argument('-l', '--logfile', type=str, 
                        help='Name of logfile')
    parse.add_argument('-t', '--transition', type=str, default='Close',
                        help='Transition (case-sensitive) default="Close"')
    parse.add_argument('-r', '--resolution', type=str, default="Field Cleanup 2024 May",
                        help='Transition resolution code, default="Field Cleanup May 2024"')
    parse.add_argument('-C', '--comment', type=str, default="Issue status modified via JiraAPI",
                        help='Transition comment')
    parse.add_argument('-s', '--silent', action='store_true', 
                        help='Silent mode')
    parse.add_argument('-d', '--debug', action='store_true', 
                        help="Enable debug messages")

    return parse.parse_args()


def main():
    '''
    '''
    args = parseargs()
    
    # Set up logging & reporting
    # log events to the log file and to stdout
    dateTime = time.strftime('%Y%m%d-%H%M%S')
    # Set up logging
    logfile = f'{dateTime}.log'
    file_handler = logging.FileHandler(filename=logfile)
    stdout_handler = logging.StreamHandler(sys.stdout)
    # Output to CLI and config
    handlers = [file_handler, stdout_handler]
    # Output to config only
    if args.debug:
        loglevel = logging.DEBUG
    else:
        loglevel = logging.INFO
    # Check for silent mode
    if args.silent:
        logging.basicConfig(
            level=loglevel,
            format='%(message)s',
            handlers=file_handler
            )
    else:
        logging.basicConfig(
            level=loglevel,
            format='%(message)s',
            handlers=handlers
            )

    if args.issue:
        if args.transition == 'status_check':
            status_check(issue=args.file,
                         config=args.config)
        else:
            process_issue(config=args.config, 
                        issue=args.issue, 
                        transition=args.transition,
                        resolution=args.resolution,
                        comment=args.comment)
    elif args.file:
        if args.transition == 'status_check':
            bulk_status_check(in_file=args.file,
                              config=args.config)
        
        else:
            process_file(in_file=args.file, 
                        config=args.config,
                        transition=args.transition,
                        resolution=args.resolution,
                        comment=args.comment)

    return


### Main ###
if __name__ == '__main__':
    exitcode = main()
    exit(exitcode)
## End Main ###