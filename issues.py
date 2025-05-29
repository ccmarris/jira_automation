#!/usr/bin/env python3
#vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
'''

 Description:

    Module to simplify interaction with Jira

 Requirements:
   Python 3.8+

 Author: Chris Marrison

 Date Last Updated: 20250528

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
__version__ = '0.3.7'
__author__ = 'Chris Marrison'
__author_email__ = 'chris@infoblox.com'


import logging
import os
import configparser
import jira
import jira.exceptions
from rich import print

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


class ISSUES():
    '''
    Wrapper Class to simplify handling of Jira issues
    using the jira module
    '''

    def __init__(self, 
                 inifile:str = 'jira.ini',
                 server:str = '',
                 user:str = '',
                 api_key:str = '',
                 res_field:str = ''):
        '''
        Initial Values

        Parameters:
            inifile:str = Inifile to read API Key and other parameters
            server:str = Jira server string (overides inifile value)
            user:str = Override inifile values
            api_key:str = Override inifile values
            res_field:str = Resolution field for transitions
        '''
        self.server:str = server
        self.user:str = user
        self.api_key:str = api_key
        self.resolution_field:str = res_field
        self.issue:object = None
        self.fields:list = []
        self.field_map:dict = {}
        self.summary_fields:list = [ 'Product',
                                     'Summary',
                                     'Reporter',
                                     'Priority',
                                     'Prospects/Customers',
                                     'RFE #' ]

        # self.required_fields:dict = {}

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
                _logger.error(err)

            # Look for BloxOne section
            if 'JIRA' in cfg:
                for key in ini_keys:
                    # Check for key in BloxOne section
                    if key in cfg['JIRA']:
                        config[key] = cfg['JIRA'][key].strip("'\"")
                        _logger.debug(f'Key {key} found in {filename}: {config[key]}')
                    else:
                        _logger.error(f'Key {key} not found in BloxOne section.')
                        raise IniFileKeyError(f'Key "{key}" not found within' +
                                f'[JIRA] section of ini file {filename}')
                        
            else:
                _logger.error(f'No BloxOne Section in config file: {filename}')
                raise IniFileSectionError(f'No [BloxOne] section found in ini file {filename}')
            
        else:
            raise FileNotFoundError('ini file "{filename}" not found.')

        return config


    def get_issue(self, issue:str, expand:str = None) -> bool:
        '''
        Get Jira issue and bind to self.issue

        Parameters:
            issue:str = issue key
            expand:str = value to pass to expand paramter
        
        Returns:
            bool based on successfully retrieving the jira issue
        '''
        status:bool = False
        try:
            self.issue = self.jira_session.issue(issue, expand=expand)
            status = True
            _logger.debug(f'Successfully retrieved {issue}')
        except:
            _logger.error(f'Failed to retrieve issue: {issue}')
            status = False
        return status


    def create_issue(self, issue_dict:dict) -> bool:
        '''
        '''
        status = False

        try:
            self.issue = self.jira_session.create_issue(fields=issue_dict)
            status = True
            _logger.debug(f'Successfully created {self.issue}')
        except jira.exceptions.JIRAError as Err:
            status = False
            _logger.error(Err)

        return status
        
    
    def create_issue_dict(self,
                          summary:str, 
                          description:str, 
                          issue_type:str = 'New Feature', 
                          custom_fields:dict = None, 
                          components:list = [],
                          project:str = 'IFR') -> dict:
        '''
        '''
        issue_dict:dict

        issue_dict = {
                      'project': { 'key': project},
                      'summary': summary,
                      'description': description,
                      'issuetype': { 'name': issue_type }
                     }
        
        if custom_fields:
            issue_dict.update(custom_fields)
        
        if components:
            issue_dict.update(components)

        _logger.debug(f'Created issue dictionary: {issue_dict}')

        return issue_dict


    def get_transitions(self) -> bool:
        '''
        Get transitions for and bind to self.transitions

        Returns:
            False on error
        '''
        status:bool = False
        try:
            self.transitions = self.jira_session.transitions(self.issue.id)
            _logger.debug(f'Successfully retrieved transitions for: {self.issue}')
            status = True
        except:
            _logger.error(f'Failed to retrieve transitions for: {self.issue}')
            status = False
        return status
    
    
    def get_resolution_key(self) -> bool:
        '''
        Get key for named resolution and bind to self.resolution_key

        Returns:
            status: bool
        '''
        status:bool = False
        try:
            self.resolution_key = self.get_field_id(self.resolution_field)
            status = True
            _logger.debug(f'Successfully retrieved resolution key: {self.resolution_key}')
        except:
            _logger.error(f'Failed to retrieve resolution field for: {self.issue}')
            status = False
        return status


    def get_field_id(self, fieldname) -> str:
        '''
        Get id of an issue field
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
        Returns current status as a str
        '''
        return self.issue.fields.status.name


    def status_id(self) -> str:
        '''
        Returns status id as str
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
            _logger.warning(f'Cannot {transition} {self.issue.key} transition not available')
        
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
                _logger.debug(f'Found {transition} for issue')
                # Find the id of the allowed resolution
                # Don't know why these are different to the ids 
                # provided by JIRA.resolutions()
                for v in av:
                    if v.get('value') == resolution:
                        id = v.get('id')
                        _logger.debug(f'Found {resolution} for transition')
                        break
                break

        if not id:
            _logger.warning(f'Cannot find {resolution} id for {self.issue.key}')
        
        return id


    def transition_issue(self, 
                         t_id:str, 
                         r_id:str = '', 
                         comment:str = '',
                         target:str = '') -> bool:
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
            elif target:
                fieldname = self.field_map.get('Target Release')
                self.jira_session.transition_issue(self.issue.key,
                                            transition=t_id, 
                                            fields={fieldname: [{'name': target }] },
                                            comment=comment)
            else:
                self.jira_session.transition_issue(self.issue.key,
                                            transition=t_id, 
                                            comment=comment)
            status = True
        except jira.exceptions.JIRAError as err:
            _logger.error(err)
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
            _logger.error('Failed to retrieve field mappings')
            status = False

        if fields:
            status = True
            for f in fields:
                fmap.update( { f.get('id'): f.get('name'),
                               f.get('name'): f.get('id')} )
        else:
            _logger.error('Field mapping empty')
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


    def get_schema(self, 
                   project:str = 'IFR',
                   issuetype:str='New Feature') -> dict:
        '''

        '''
        schema:list = []
        
        if not self.field_map:
            self.create_field_map()

        meta = self.jira_session.createmeta(projectKeys=project, 
                                            issuetypeNames=issuetype, 
                                            expand='projects.issuetypes.fields')
        if meta.get('projects'):
            if meta['projects'][0].get('issuetypes'):
                if meta['projects'][0]['issuetypes'][0].get('fields'):
                    # Get the fields for the first issue type
                    schema = meta['projects'][0]['issuetypes'][0]['fields']
                else:
                    _logger.error(f'No fields found for {project} {issuetype}')
            else:
                _logger.error(f'No issue types found for {project}')

        return schema


    def get_issue_fields(self, 
                            project:str='IFR', 
                            issuetype:str='New Feature',
                            required:bool = False) -> list:
        '''
        '''
        issue_fields:dict = {}

        if not self.field_map:
            self.create_field_map()

        if self.issue:
            project = self.issue.fields.project.name
        else:
            project = project

        
        schema = self.get_schema(project=project, issuetype=issuetype)

        for field, field_value in schema.items():
            if required:
                if field_value.get('required'):
                    if 'customfield' in field:
                        field = self.field_map.get(field)
                    issue_fields.update({field: field_value})
            else:
                if 'customfield' in field:
                    field = self.field_map.get(field)
                issue_fields.update({field: field_value})
        
        return issue_fields


    def output_issue(self,
                     translate:bool = True,
                     all_fields:bool = False):
        '''
        '''
        project:str = ''
        issuetype:str = ''
        output_fields:dict = {}

        if self.issue:
            project = self.issue.fields.project.key
            issuetype = self.issue.fields.issuetype.name
            if all_fields:
                for k in self.issue.fields.__dict__.keys():
                    if translate:
                        field = self.field_map.get(k)
                    else:
                        field = k
                    value = getattr(self.issue.fields, k)
                    if value:
                        print(f'{field}: {value}')
                        output_fields.update({field: value})
                    
            
            else:
                schema = self.get_schema(project=project, issuetype=issuetype)
                if isinstance(schema, dict):
                    for k in schema.keys():
                        if k in self.issue.fields.__dict__.keys():
                            if translate:
                                print(f'{self.field_map[k]}: {getattr(self.issue.fields, k)}')
                                output_fields.update({self.field_map[k]: getattr(self.issue.fields, k)})
                            else:
                                print(f'{k}: {getattr(self.issue.fields, k)}')
                                output_fields.update({k: getattr(self.issue.fields, k)})
                else:
                    _logger.warning(f'Failed to retrieve schema for {project} {issuetype}')
                    print(f'Failed to retrieve schema for {project} {issuetype}')
                    print('Attempting to output all fields:')
                    self.output_issue(translate=translate, all_fields=True)
        
        else:
            print('No issue selected, use get_issue()')
        
        return output_fields


    def summarise_issue(self, 
                        fields:list = []) -> list:
        '''
        '''
        summary:dict = {}

        if not fields:
            fields = self.summary_fields

        if self.issue:
            key = self.issue.key
            summary['key'] = key
            status = self.status()
            summary['status'] = status

            if fields:
                for k in fields:
                    fieldname = self.field_map.get(k)
                    if fieldname in self.issue.fields.__dict__.keys():
                        summary[k] = str(getattr(self.issue.fields, fieldname))
        else:
            summary = {}
        
        return summary


    def get_comments(self):
        '''
        '''
        return self.issue.fields.comment.comments
    

    def update_field(self, field:str, value:str) -> bool:
        '''
        '''
        status:bool = False

        if 'customfield_' in field:
            rfe_field = field
        else:
            rfe_field = self.field_map.get(field)
        
        try:
            self.issue.update(fields={rfe_field: value})
            _logger.debug(f'{rfe_field}: {value}')
            status = True
        except jira.JIRAError as err:
            _logger.debug({err})
            status = False
        
        return status


    def add_weblink(self, link:str, comment:str):
        '''
        '''
        status:bool = False

        web_link = {
                    "object": { 
                                "url": link,
                                "title": comment
                              }
                  }

        try:
            if self.jira_session.add_remote_link(self.issue.key, web_link):
                status = True
                _logger.info(f'Sucessfully add web link to {self.issue.key}')
            else:
                status = False
        except jira.exceptions.JIRAError as err:
            _logger.error(f'Failed add web link to {self.issue.key}')
            _logger.error(err)
            status = False
        
        return status


    def add_comment(self, comment) -> bool:
        '''
        Add a comment to the RFE
        '''
        status:bool = False

        try:
            self.jira_session.add_comment(self.issue.key, body=comment)
            status = True
            _logger.info(f'Added comment to {self.issue.key}')
            _logger.debug(f'Comment: {comment}')
        except jira.exceptions.JIRAError as err:
            _logger.error(f'Failed add comment to {self.issue.key}')
            _logger.debug(f'Comment: {comment}')
            _logger.error(err)
            status = False
        
        return status


    def query_field(self, 
                    project:str = 'IFR',
                    field:str = '',
                    value:str = '' ) -> list:
        '''
        '''
        issue_list:list = []

        jql_query = f'"{field}" = "{value}" AND project = "{project}"'

        try:
            issues = self.jira_session.search_issues(jql_query)

            if issues:
                for issue in issues:
                    _logger.debug(f'Matched issue: {issue}')
                    issue_list.append(issue.key)
            else:
                issue_list = []

        except jira.exceptions.JIRAError as Err:
            _logger.error(Err)
            issue_list = []
        
        return issue_list
    

    def jql_query(self, query:str = 'project = "IFR"') -> list:
        '''
        '''
        issue_list:list = []


        try:
            issues = self.jira_session.search_issues(query)

            if issues:
                for issue in issues:
                    _logger.debug(f'Matched issue: {issue}')
                    issue_list.append(issue.key)
            else:
                issue_list = []

        except jira.exceptions.JIRAError as Err:
            _logger.error(Err)
            issue_list = []
        
        return issue_list
    

    def get_reporter_id(self):
        '''
        '''
        accountId:str

        if self.issue:
            accountId = self.issue.fields.reporter.accountId
            _logger.info(f'Reporter: {accountId}')
        else:
            _logger.warning('Use get_issue() to retrieve an issue first')
            accountId = ''
        
        return accountId


    def update_reporter(self, email:str = '', accountId:str = '') -> bool:
        '''
        Update the reporter field with the account id supplied
        '''
        status: bool = False

        if accountId:
            reporter = { 'reporter': { 'accountId': accountId } }
            try:
                self.issue.update(fields=reporter)
                _logger.info(f'Issue reporter updated successfully')
                status = True
            except jira.exceptions.JIRAError as Err:
                _logger.debug(Err)
                status = False
        
        elif email:
            query = self.jira_session.search_users(query=email)
            if query:
                accountId = query[0].accountId
                status = self.update_reporter(accountId=accountId)
            else:
                _logger.warning(f'No user found with email: {email}')
                status = False
        
        else:
            _logger.warning('No accountId supplied')
            status = False
        
        return status
    

    def get_comment_author(self, index:int) -> str:
        '''
        Get the author of a comment by index

        Return acccountId or None
        '''
        accountId:str = None

        if self.issue:
            try:
                accountId = self.issue.fields.comment.comments[index].author.accountId
            except:
                _logger.error(f'Failed to retrieve author for comment {index}')
                accountId = None
        else:
            _logger.warning('Use get_issue() to retrieve an issue first')
            accountId = None

        return accountId

