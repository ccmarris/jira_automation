#!/usr/bin/env python3
#vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
'''

 Description:

    Module to simplify interaction with Jira

 Requirements:
   Python 3.8+

 Author: Chris Marrison

 Date Last Updated: 20241127

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
__version__ = '0.2.1'
__author__ = 'Chris Marrison'
__author_email__ = 'chris@infoblox.com'


import logging
import issues
import jira
import jira.exceptions

_logger = logging.getLogger(__name__)

class MIGRATE_ISSUE():
    '''
    Note this returns an assertion error if the source issue is not found

    '''
    def __init__(self, 
                 issue:str,
                 dst_project:str = 'IFR', 
                 inifile:str = 'jira.ini',
                 server:str = 'https://infoblox.atlassian.net'):
        '''
        Initialise class

        Parameters:
            issue: str = Source issue to migrate
            dst_project: str = Destination project
            inifile: str = Inifile containing jira api configuration
            server: str = URL of Jira cloud instance
        '''
        self.src = issues.ISSUES(inifile=inifile, server=server)
        if not self.src.get_issue(issue):
            assert self.src.issue
        self.dst = issues.ISSUES(inifile=inifile, server=server)
        self.dst_project = dst_project
        # self.required_fields = self.dst.get_required_fields(self.dst_project)
        self.issue_fields = self.dst.get_issue_fields()
        self.required_fields = self.dst.get_issue_fields(required=True)
        self.allowed_components = self.get_allowed_components()

        return
        

    def migrate_issue(self, 
                      include_comments:bool = True,
                      additional_fields:list = ['Support Cases',
                                                'Prospects/Customers' ]):
        '''
        Migrate source Issue to destination Issue

        Returns:
            Issue key or None
        '''
        status:str
        summary:str
        description:str
        project:str
        components:list
        custom_fields:dict

        migrated = self.migrated()

        if not migrated:
            summary = self.src.issue.fields.summary
            description = self.normalise_string(self.src.issue.fields.description)
            project = self.dst_project
            versions = self.get_versions()
            
            # Create components list
            components = self.build_components()

            # Build basic dictionary of minimum fields
            issue_dict = {
                            "issuetype": { "name": "New Feature" },
                            "summary": summary,
                            "description": description,
                            "project": { "key": project },
                            "versions": versions,
                            "components": components
                        }

            # Handle Custom Fields
            custom_fields = self.build_custom_fields()
            issue_dict.update(custom_fields)

            _logger.debug(f'Issue Dictionary: {issue_dict}')

            # Create Destination Issue
            if self.dst.create_issue(issue_dict=issue_dict):
                # status = self.dst.issue.key
                status = f'{self.src.issue.key} submitted as: {self.dst.issue.key}'
                # Add Origin Information as a comment
                if self.add_origin_data():
                    _logger.info('Origin data added')
                else:
                    _logger.error('Origin data not added')
                # Check whether we copy existing comments from source issue
                if include_comments:
                    self.copy_comments()
                if additional_fields:
                    if self.add_additional_fields(fieldlist=additional_fields):
                        _logger.info(f'Successfully added: {additional_fields}')
                    else:
                        _logger.error(f'Failed to add: {additional_fields}')
            else:
                status = f'Error creating IFR from {self.src.issue.key}'
        else:
            _logger.warning(f'Previously migrated')
            # status = f'Previously migrated as: {migrated}'
            status = f'{self.src.issue.key} previously migrated as: {migrated}'

        return status


    def migrated(self, project:str = 'IFR'):
        '''
        '''
        status:str = ''

        jql_query = f'"RFE #[Short text]" ~ "{self.src.issue.key}" AND project = "{project}"'

        try:
            issues = self.dst.jira_session.search_issues(jql_query)

            if issues:
                for issue in issues:
                    _logger.warning(f'{self.src.issue.key} already migrated as {issue.key}')
                    status = issue.key
                    break
            else:
                status = ''
        except jira.exceptions.JIRAError as Err:
            _logger.error(Err)
            status = f'Jira error: {Err}'
        
        return status



    def normalise_string(self, input_str:str) -> str:
        '''
        Remove unwanted charaters/strings
        '''
        outstr:str = ''

        if input_str:
            outstr = input_str.replace('\n','')
            outstr = outstr.replace('\r','')

        return outstr


    def add_origin_data(self, custom_field:str = 'RFE #'):
        '''
        Add comment with original RFE, and timestamps
        '''
        status:bool = False

        rfe = self.src.issue.key
        created = self.src.issue.fields.created
        updated = self.src.issue.fields.updated
        if hasattr(self.src.issue.fields.reporter, 'displayName'):
            reporter = self.src.issue.fields.reporter.displayName
            self.copy_reporter()
        else:
            reporter = ''

        # Update 'RFE #' custom field
        if self.dst.update_field(field=custom_field, value=rfe):
            _logger.info(f'Added RFE {rfe} to field {custom_field}')
        
            # Build comment
            comment = ( f'Origin: {rfe}, \nCreated by: {reporter}, '
                        f'\nCreated: {created}, \nLast updated: {updated}' )
            # Add comment
            if self.dst.add_comment(comment=comment):
                status = True
            else:
                _logger.error(f'Failed to add origin data')
                status = False

        else:
            _logger.error(f'Failed to add RFE {rfe} to field {custom_field}')
            status = False

        return status


    def get_versions(self) -> list:
        '''
        Retrieve current versions or create a default response
        '''
        src_versions:list = []

        if hasattr(self.src.issue.fields, 'versions'):
            versions = self.src.issue.fields.versions
            if versions:
                for version in versions:
                    if hasattr(version, 'name'):
                        if self.check_version(version.name):
                            src_versions.append({ 'name': version.name })
                        else:
                            src_versions.append({ 'name': 'Unknown' })
                    else:
                            src_versions.append({ 'name': 'Unknown' })
            else:
                src_versions = [ { 'name': 'Unknown' } ]
        else:
            src_versions = [ { 'name': 'Unknown' } ]

        _logger.debug(f'Processed versions: {src_versions}')
        
        return src_versions


    def check_version(self, version):
        '''
        '''
        allowed:bool = False
        allowed_versions:list = self.get_allowed_versions()

        if version in allowed_versions:
            allowed = True
        else:
            allowed = False
        
        return allowed


    def get_allowed_versions(self):
        '''
        '''
        allowed_versions:list = []

        versions:list = self.required_fields.get('versions').get('allowedValues')
        for v in versions:
            allowed_versions.append(v.get('name'))

        return allowed_versions
    

    def get_allowed_components(self):
        '''
        Get the allowed component values 
        '''
        allowed:list = []
        fields = self.required_fields

        if fields.get('components'):
            values = fields.get('components').get('allowedValues')
            if values:
                for comp in values:
                    allowed.append(comp.get('name'))

        return allowed


    def build_components(self) -> dict:
        '''
        Build the components from the source or set a default value
        '''
        components:list = []

        for component in self.src.issue.fields.components:
            if component.name in self.allowed_components:
                components.append({ 'name': component.name })
        
        # Need a holding component if there are no matches, need to consider
        # translating some of the existing names
        if not components:
            components = [ { 'name': 'DNS' } ]

        return components


    def get_req_custom_fields(self) -> dict:
        '''
        '''
        custom_fields:dict = {}
        fields:dict = self.required_fields

        for field, field_value in fields.items():
            if 'customfield' in field_value.get('key'):
                custom_fields.update( { field_value['key']: field_value } )

        return custom_fields


    def get_all_custom_fields(self) -> dict:
        '''
        '''
        custom_fields:dict = {}
        fields:dict = self.required_fields

        for field, field_value in fields.items():
            if 'customfield' in field_value.get('key'):
                custom_fields.update( { field_value['key']: field_value } )

        return custom_fields


    def build_custom_fields(self) -> dict:
        '''
        '''
        custom_fields:dict = {}

        required = self.get_req_custom_fields()

        for cf in required.keys():
            custom_fields.update(self.process_custom_field(cf))

        return custom_fields
    

    def add_additional_fields(self, fieldlist:list) -> bool:
        '''
        '''
        status:bool = False
        custom_fields:dict = {}

        for f in fieldlist:
            fname = self.dst.field_map.get(f)
            custom_fields.update(self.process_custom_field(fname))
        
        _logger.debug(f'Additional field results: {custom_fields}')

        # Consider putting check for self.dst.issue before calling
        try:
            self.dst.issue.update(fields=custom_fields)
            status = True
        except jira.exceptions.JIRAError as err:
            _logger.error(f'Adding additional fields failed: {err}')
            status = False
        
        return status


    def process_custom_field(self, custom_field_id) -> dict:
        '''
        '''
        processed_field:dict = {}
        src_value = None

        field_type = self.get_custom_field_type(custom_field_id)
        if field_type == 'string':
            remap = self.remap_field(custom_field_id)
            if hasattr(self.src.issue.fields, remap):
                src_value = getattr(self.src.issue.fields, remap)
            else:
                if hasattr(self.src.issue.fields, custom_field_id):
                    src_value = getattr(self.src.issue.fields, alternate)
                else:
                    src_value = 'Not defined in RFE'

            if not src_value:
                src_value = 'Not defined in RFE'

            processed_field.update( { custom_field_id: src_value } )

        elif field_type == 'option':
            if hasattr(self.src.issue.fields, custom_field_id):
                field_obj = getattr(self.src.issue.fields, custom_field_id)
            else:
                field_obj = None

            if field_obj:
                src_value = { 'value': self.remap_option(field_obj.value)}
            else:
                alternate = self.remap_field(custom_field_id)
                if hasattr(self.src.issue.fields, alternate):
                    field_obj = getattr(self.src.issue.fields, alternate)
                    src_value = self.remap_option(field_obj.value)

            # processed_field.update( { custom_field_id: { 'value': src_value } } )
            processed_field.update( { custom_field_id: src_value } )

        return processed_field


    def get_custom_field_type(self, custom_field_id:str) -> str:
        '''
        '''
        # Get the custom field details
        field_type:str 
        if 'customfield' in custom_field_id:
            mapped_field:str = self.dst.field_map.get(custom_field_id)
        else:
            mapped_field = custom_field_id

        if self.issue_fields.get(mapped_field):
            field_type = self.issue_fields.get(mapped_field).get('schema').get('type')
        else:
            field_type = 'String'
        
        return field_type


    def remap_field(self, field:str) -> str:
        '''
        '''
        mapped_field:str

        alt_mappings:dict = {
                             # 'Product': 'Product (migrated)',
                             'Product Family': 'Product (migrated)',
                             'Support Cases': 'Support Cases (migrated)',
                             'Prospects/Customers': 'Prospects/Customers (migrated)'
                            }

        if 'customfield' in field:
            newfield = alt_mappings.get(self.src.field_map.get(field))
        else:
            newfield = alt_mappings.get(field)

        if newfield:
            mapped_field = self.src.field_map.get(newfield)
        else:
            mapped_field = field
        
        return mapped_field


    def remap_option(self, option):
        '''
        Remap option values or return unchanged
        '''
        mappings:dict = {
                            "ActiveTrust Cloud": "BloxOne TD"
                            # "BloxOne DDI": "UDDI",
                            # "BloxOne TD": "Infoblox Threat Defense",
                            # "Network Insight": "NIOS"
                        }

        if option in mappings.keys():
            remapped = mappings.get(option)
        else:
            remapped = option

        return remapped


    def copy_comments(self):
        '''
        Copy comments from source to destination
        '''
        if self.src.issue and self.dst.issue:
            comments = self.src.get_comments()
            # Add comments to the target issue
            for comment in comments:
                author = comment.author.displayName
                body = ( f"Comment by {author} on "
                         f"{comment.created}:\n\n{comment.body}" )
                self.dst.jira_session.add_comment(self.dst.issue.key, body)

        return


    def copy_reporter(self):
        '''
        Copy reporter from the src to dst
        '''
        status:bool = False
        accountId:str
        issue:str

        if self.src.issue and self.dst.issue:
            accountId = self.src.get_reporter_id()
        else: 
            issue = self.migrated()
            if self.dst.get_issue(issue):
                accountId = self.src.get_reporter_id()
                _logger.debug(f'Account ID: {accountId}')
            else:
                accountId = ''
                _logger.debug(f'Issue {issue} not found.')
        
        if accountId:
            status = self.dst.update_reporter(accountId)
            if status:
                _logger.info('Successfully updated reporter')
            else:
                _logger.warning('Failed to update reporter')
        else:
            _logger.error(f'Issue {self.src.issue.key} has not been migrated')
            status = False
        
        return status
    

### Main ###
if __name__ == '__main__':
    exitcode = main()
    exit(exitcode)
## End Main ###
