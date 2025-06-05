#!/usr/bin/env python3
#vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
'''

 Description:

    CLI for Jira using the cmd module.
    This is a simple command line interface for interacting with Jira issues.

 Requirements:
   Python 3.8+

 Author: Chris Marrison

 Date Last Updated: 20250604

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
__version__ = '0.1.8'
__author__ = 'Chris Marrison'
__author_email__ = 'chris@infoblox.com'


import logging
import os
import cmd
import shlex
import readline  # For command history
import argparse
from rich import print
from issues import ISSUES
import migration

_logger = logging.getLogger(__name__)

class JiraShell(cmd.Cmd):
    print(f'[bold green]Jira CLI v{__version__}[/bold green]')
    print(f'[bold blue]Author: {__author__}[/bold blue]')
    print(f'[bold blue]Email: {__author_email__}[/bold blue]')
    intro = "Welcome to the Jira CLI. Type help or ? to list commands.\n"
    prompt = "jira> "

    def __init__(self, inifile:str = 'jira.ini'):
        # super().__init__(completekey='tab', stdin=None, stdout=None)
        super().__init__()
        self.inifile = inifile
        self.issues = ISSUES(inifile=inifile)
        print(f'Connected to Jira: {self.issues.server}')
        self.current_issue = None
        return

    def preloop(self):
        # Load history file if you want persistence
        try:
            readline.read_history_file('.jira_cli_history')
        except FileNotFoundError:
            pass
        return

    def postloop(self):
        # Save history file
        readline.write_history_file('.jira_cli_history')
        return

    def do_debug(self, arg):
        "Enable or disable debug mode: debug [on|off]"
        if arg.lower() == 'on':
            logging.basicConfig(level=logging.DEBUG)
            _logger.setLevel(logging.DEBUG)
            print("Debug mode enabled.")
        elif arg.lower() == 'off':
            logging.basicConfig(level=logging.INFO)
            _logger.setLevel(logging.INFO)
            print("Debug mode disabled.")
        else:
            print("Usage: debug [on|off]")
        return


    def parse_redirection(self, arg):
        '''
        Splits arg into (real_args, filename) if '>' is present.
        Returns (real_args, filename or None)
        '''
        if '>' in arg:
            parts = arg.split('>')
            real_args = parts[0].strip()
            filename = parts[1].strip()
        else:
            real_args = arg
            filename = None
        
        _logger.debug(f'Parsed args: {real_args}, filename: {filename}')
        
        return real_args, filename


    def expand_path(self, path):
        # Expands ~ and returns absolute path
        return os.path.abspath(os.path.expanduser(path))


    def write_output(self, text, filename=None):
        '''
        Writes output to a file if filename is provided, otherwise prints to stdout.
        '''
        if filename:
            filename = self.expand_path(filename)
            with open(filename, 'a') as f:
                f.write(text + '\n')
                print(text)
        else:
            print(text)
        
        return

    def output_fields(self, fields, filename=None, comsole_output=False):
        '''
        Outputs fields to a file if filename is provided, otherwise prints to stdout.
        '''
        if filename:
            filename = self.expand_path(filename)
            with open(filename, 'a') as f:
                for key, value in fields.items():
                    f.write(f"{key}: {value}\n")
                    print(f"{key}: {value}")
        else:
            for key, value in fields.items():
                print(f"{key}: {value}")
        
        return

    def do_reconnect(self, arg):
        "Reconnect to Jira: reconnect"
        self.issues = ISSUES(inifile=self.inifile)
        print(f'Connected to Jira: {self.issues.server}')
        return


    def do_get(self, arg):
        "Get an issue by key: get <ISSUE-KEY>"
        if arg:
            if self.issues.get_issue(arg):
                self.current_issue = arg
                print(f"Issue {arg} loaded.")
            else:
                print(f"Issue {arg} not found.")
        else:
            print("Usage: get <ISSUE-KEY>")
        return


    def do_list(self, arg):
        "List issues assigned to you or matching a filter: list [assignee[=user]|]reporter[=<user>]|all|<JQL>]\nUse 'list' to see issues assigned to you."
        '''
        List issues assigned to you or matching a filter: list [<subcommand>|<JQL>]
        Subcommands:
        reporter   - issues where you are the reporter
        assigned   - issues assigned to you (default)
        all        - all issues visible to you
        '''

        # Map subcommands to JQL queries
        default_queries = {
            'reporter': 'reporter = {value} ORDER BY updated DESC',
            'assigned': 'assignee = {value} ORDER BY updated DESC',
            'all': 'ORDER BY updated DESC'
        }

        real_args, filename = self.parse_redirection(arg)
        query:str = None
        parts:list = []
        summary:bool = False

        if real_args:
            parts = shlex.split(real_args)
            subcmd = parts[0].strip().lower()
            value = 'currentUser()'
        
            # Check for subcommand=value pattern
            if '=' in subcmd:
                # If subcmd is in the form of 'field=value', split it
                subcmd, value = subcmd.split('=', 1)
                subcmd = subcmd.strip()
                # Quote value
                value = f"'{value.strip()}'"

            if subcmd in default_queries:
                query = default_queries[subcmd].format(value=value)
            else:
                # Default: issues assigned to current user
                query = default_queries['assigned'].format(value='currentUser()')
        else:
            # Default: issues assigned to current user
            query = default_queries['assigned'].format(value='currentUser()')

        if len(parts) > 1: 
            for part in parts[1:]:
                part = part.strip().lower()
                if part == 'summary':
                    # If 'summary' is provided, list issues with summary
                    summary = True
                    _logger.debug(f'Setting summary')
                elif 'project' in part:
                    # If 'project' is provided, filter by project
                    project = part.split('=')[1].strip() if '=' in part else None
                    query += ' project = ' + project if project else ''
                    _logger.debug(f'Appending project to query: {query}')
                else:
                    print(f"Unknown parameter '{part}', ignoring.")
        else: 
            # Check for summary parameter
            if 'summary' in real_args:
                summary = True
                _logger.debug(f'Setting summary to True')

        # Quote the query to pass JQL to do_query add summary parameter if requested
        if summary:
            # If summary is requested, modify the query to include summary
            query = f'"{query}" summary'
        else:
            # If summary is not requested, just use the query as is
            query = f'"{query}"'

        _logger.debug(f'Parsed query: {query}')
        # If redirection is specified, append it to the query
        if filename:
            query = f'{query} > {filename}'
            _logger.debug(f'Redirection to file: {filename}')

        # Execute the query
        _logger.debug(f'Executing query with parameters: {query}')
        self.do_query(query)

        return
    

    def do_create(self, arg):
        "Create an issue: create <summary> | <description>\nUse quotes if your summary or description contains spaces."
        try:
            # Use shlex to support spaces in quoted arguments
            parts = shlex.split(arg)
            if len(parts) < 2:
                print("Usage: create <summary> | <description>")
            else:
                # Support both '|' separator and two quoted arguments
                if '|' in arg:
                    summary, description = arg.split('|', 1)
                    summary = summary.strip()
                    description = description.strip()
                else:
                    summary, description = parts[0], " ".join(parts[1:])
                issue_dict = self.issues.create_issue_dict(summary, description)
                if self.issues.create_issue(issue_dict):
                    print("Issue created successfully.")
                else:
                    print("Failed to create issue.")
        except ValueError:
            print("Usage: create <summary> | <description>")
        
        return


    def do_comment(self, arg):
        "Add a comment to the current issue: comment <text>\nUse quotes if your comment contains spaces."
        if self.current_issue:
            # Use shlex to support spaces in quoted arguments
            comment = arg if arg else ""
            if self.issues.add_comment(comment):
                print("Comment added.")
            else:
                print("Failed to add comment.")
        else:
            print("No issue loaded. Use get <ISSUE-KEY> first.")
        
        return


    def do_show(self, arg):
        "Show fields for the current issue: show <all>"
        real_args, filename = self.parse_redirection(arg)
        if not self.current_issue:
            print("No issue loaded. Use get <ISSUE-KEY> first.")
            return
        if real_args == 'all':
            data = self.issues.output_issue(all_fields=True)
            self.output_fields(data, filename=filename)
        else:
            data = self.issues.output_issue(all_fields=False)
            self.output_fields(data, filename=filename)
        return


    def do_status(self, arg):
        "Show the status of the current issue: status"
        if not self.current_issue:
            print("No issue loaded. Use get <ISSUE-KEY> first.")
        else:
            print(self.issues.status())
        return


    def do_summary(self, arg):
        "Show the summary of the current issue: summarise"
        real_args, filename = self.parse_redirection(arg)
        if not self.current_issue or real_args:
            print("No issue loaded. Use get <ISSUE-KEY> first.")
        else:
            summary = self.issues.summarise_issue()
            if summary:
                self.output_fields(summary,
                                   filename=filename,
                                   comsole_output=True)
            else:
                print("No summary available for this issue.")
        return
    

    def do_updfield(self, arg):
        "Update a field: updatefield <field> <value>\nUse quotes if your value contains spaces."
        real_args, filename = self.parse_redirection(arg)
        try:
            parts = shlex.split(real_args)
            if len(parts) < 2:
                print("Usage: updatefield <field> <value>")
                return
            field, value = parts[0], " ".join(parts[1:])
            if self.issues.update_field(field, value):
                self.write_output("Field updated.")
            else:
                print("Failed to update field.")
        except ValueError:
            print("Usage: updatefield <field> <value>")


    def do_updrfe(self, arg):
        "Update the RFE # field: update_rfe <field> <value>\nUse quotes if your value contains spaces."
        if not self.current_issue:
            print("No issue loaded. Use get <ISSUE-KEY> first.")
            return
        if 'IFR' in self.current_issue:
            try:
                if self.issues.update_field('RFE #', arg):
                    print("Field updated.")
                else:
                    print("Failed to update field.")
            except ValueError:
                print("Usage: update_rfe <field> <value>")
        else:
            print("This is not an IFR issue. Use get <ISSUE-KEY> first.")
        return
    

    def do_updreporter(self, arg):
        "Update the reporter: update_reporter <email>\nUse quotes if your email contains spaces."
        if not self.current_issue:
            print("No issue loaded. Use get <ISSUE-KEY> first.")
            return
        try:
            if self.issues.update_reporter(arg):
                print("Reporter updated.")
            else:
                print("Failed to update reporter.")
        except ValueError:
            print("Usage: update_reporter <email>")
        return
    

    def do_query(self, arg):
        "Query issues: query <JQL> <summary>\nUse quotes if your JQL contains spaces."
        summary:bool = False
        issue_summary:str = ''
        header:str = 'key,status,Summary,Reporter,Product,RFE #'

        real_args, filename = self.parse_redirection(arg)
        if real_args:
            parts = shlex.split(real_args)
            if len(parts) > 1:
                query = parts[0]
                command = " ".join(parts[1:])
                if command == 'summary':
                    summary = True
                else:
                    summary = False

            else:
                query = parts
            try:
                print("Executing JQL query...")
                issues = self.issues.jql_query(query)
            except Exception as e:
                print(f"Error executing JQL query: {e}")

            if issues:
                # Check if filename is provided
                if filename:
                    print(f"Writing output to {filename}")
                if summary:
                    # Output CSV Header
                    self.write_output(header, filename=filename)

                for issue in issues:
                    # self.issues.get_issue(issue)
                    status = issue.fields.status.name
                    issue_summary = issue.fields.summary
                    if summary:
                        reporter = issue.fields.reporter.displayName
                        # Check if custom field exists
                        if hasattr(issue.fields, 'customfield_10114'):
                            product = issue.fields.customfield_10114
                        else:
                            product = 'N/A'
                        # Check if custom field exist
                        if hasattr(issue.fields, 'customfield_14487'):
                            rfe = issue.fields.customfield_14487
                        else:
                            rfe = 'N/A'

                        issue_output = f'{issue.key},{status},{issue_summary},{reporter},{product},{rfe}'
                    else:
                        issue_output = f'{issue}: {status}, {issue_summary}'
                    self.write_output(issue_output, filename=filename)

                # Output stats line
                self.write_output(f"Found {len(issues)} issues", 
                                  filename=filename)
            else:
                self.write_output("No issues found.", filename=filename)
        else:
            print("Usage: query <JQL> <summary>")
        return


    def do_migrate(self, arg):
        "Migrate the current issue (RFEs only): migrate"
        status = False
        if not self.current_issue:
            print("No issue loaded. Use get <ISSUE-KEY> first.")
            return
        elif 'RFE' in self.current_issue:
            JIRA = migration.MIGRATE_ISSUE(issue=self.current_issue,
                                           inifile=self.issues.inifile,
                                           server=self.issues.server)
            if JIRA:
                response = JIRA.mrate_issue()
                if response:
                    if 'previously' not in response:
                        print(f"Successfully submitted {JIRA.src.issue.key} to {JIRA.dst.issue.key}")
                        status = True
                    else:
                        print(f'{response}')
                        status = True
                        
                else:
                    print(f'Failed to submit issue: {self.current_issue}')
                    status = False
            else:
                print(f'Failed to migrate issue: {self.current_issue}')
                status = False
        else:
            print("This is not an RFE issue. Use get <ISSUE-KEY> first.")

        return status

    def do_quit(self, arg):
        "Exit the CLI"
        print("Goodbye!")
        return True

    def do_EOF(self, arg):
        print()
        return self.do_quit(arg)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Jira CLI")
    parser.add_argument('-i', '--inifile', type=str, default='jira.ini', help='Path to the INI file')
    args = parser.parse_args()
    inifile = args.inifile
    JiraShell(inifile=inifile).cmdloop()