#!/usr/bin/env python3
#vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
'''

 Description:

    CLI for Jira using the cmd module.
    This is a simple command line interface for interacting with Jira issues.

 Requirements:
   Python 3.8+

 Author: Chris Marrison

 Date Last Updated: 20250523

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
__version__ = '0.0.3'
__author__ = 'Chris Marrison'
__author_email__ = 'chris@infoblox.com'


import cmd
import shlex
import argparse
from rich import print
from issues import ISSUES
import migration

class JiraShell(cmd.Cmd):
    print(f'[bold green]Jira CLI v{__version__}[/bold green]')
    print(f'[bold blue]Author: {__author__}[/bold blue]')
    print(f'[bold blue]Email: {__author_email__}[/bold blue]')
    intro = "Welcome to the Jira CLI. Type help or ? to list commands.\n"
    prompt = "jira> "

    def __init__(self, inifile:str = 'jira.ini'):
        super().__init__(completekey='Tab', stdin=None, stdout=None)
        self.inifile = inifile
        self.issues = ISSUES(inifile=inifile)
        print(f'Connected to Jira: {self.issues.server}')
        self.current_issue = None
        return


    def do_reconnect(self, arg):
        "Reconnect to Jira: reconnect"
        self.issues = ISSUES(inifile=self.issues.inifile)
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
        if not self.current_issue:
            print("No issue loaded. Use get <ISSUE-KEY> first.")
            return
        if arg == 'all':
            self.issues.output_issue(all_fields=True)
        else:
            self.issues.output_issue(all_fields=False)
        return

    def do_status(self, arg):
        "Show the status of the current issue: status"
        if not self.current_issue:
            print("No issue loaded. Use get <ISSUE-KEY> first.")
            return
        print(self.issues.status())

    def do_summary(self, arg):
        "Show the summary of the current issue: summarise"
        if not self.current_issue:
            print("No issue loaded. Use get <ISSUE-KEY> first.")
            return
        print(self.issues.summarise_issue())

    def do_updfield(self, arg):
        "Update a field: updatefield <field> <value>\nUse quotes if your value contains spaces."
        try:
            parts = shlex.split(arg)
            if len(parts) < 2:
                print("Usage: updatefield <field> <value>")
                return
            field, value = parts[0], " ".join(parts[1:])
            if self.issues.update_field(field, value):
                print("Field updated.")
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