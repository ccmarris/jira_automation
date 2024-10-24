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
__version__ = '0.2.0'
__author__ = 'Chris Marrison'
__author_email__ = 'chris@infoblox.com'


import sys
import logging
import issues
import migration
import jira.exceptions
import datetime
import time
import argparse
import csv
from rich import print


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
        r = issues.ISSUES(inifile=config)
        r.get_issue(issue)
    
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
        r = issues.ISSUES(issue=issue, inifile=config)
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
    parse.add_argument('-o', '--output', type=str, 
                        help='Name of output file for CSV')
    parse.add_argument('-S', '--summary', action='store_true', 
                        help='Output summary information of input data')
    parse.add_argument('-m', '--migrate', action='store_true', 
                        help='Migrate issue(s)')
    parse.add_argument('-t', '--transition', type=str, 
                        help='Transition (case-sensitive)')
    parse.add_argument('-r', '--resolution', type=str, 
                        help='Transition resolution code, default="Field Cleanup May 2024"')
    parse.add_argument('-C', '--comment', type=str, default="Issue status modified via JiraAPI",
                        help='Transition comment')
    parse.add_argument('-s', '--silent', action='store_true', 
                        help='Silent mode')
    parse.add_argument('-b', '--sandbox', action='store_true', 
                        help="Enable debug messages")
    parse.add_argument('-d', '--debug', action='store_true', 
                        help="Enable debug messages")

    return parse.parse_args()


def summarise_issue(args, server):
    '''
    '''
    issue = issues.ISSUES(inifile=args.config, server=server)
    issue.get_issue(args.issue)
    print(issue.summarise_issue())

    return


def summarise_file(args, server):
    '''
    '''
    results:list = []

    JIRA  = issues.ISSUES(inifile=args.config, server=server)
    with open(args.file) as f:
        for line in f:
            line = line.rstrip()
            JIRA.get_issue(line)
            summary = JIRA.summarise_issue()
            results.append(summary)
            logging.info(summary)
    
    return results


def csv_output(data, out:str = ''):
    '''
    '''
    if out:
        outfile = open(out, 'w', newline='')
    else:
        outfile = sys.stdout
    
    csvkeys = data[0].keys()

    csvfile = csv.DictWriter(outfile, csvkeys)
    csvfile.writeheader()
    for line in data:
        csvfile.writerow(line)

    return


def issue_migration(args, server):
    '''
    '''
    status:bool = False

    JIRA = migration.MIGRATE_ISSUE(issue=args.issue,
                                    inifile=args.config,
                                    server=server)
    if JIRA.migrate_issue():
        logging.info(f"Successfully migrated {JIRA.src.issue.key} to {JIRA.dst.issue.key}")
        status = True
    else:
        logging.info(f'Failed to migrate issue: {JIRA.src.issue.key}')
        status = False

    return status

def bulk_migration(args, server):
    '''
    '''
    try:
        f = open(args.file)
        for line in f:
            line = line.rstrip()
            issue_migration(args, server)
    except FileNotFoundError:
        logging.error(f'File {args.file} not found.')
        raise

    return


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
    
    if args.sandbox:
        server = 'https://infoblox-sandbox-129.atlassian.net'
    else:
        server = None

    # Match args and process appropriately
    match (args.issue, args.file, args.summary, args.migrate, args.transition):

        # Summarise Issue
        case (args.issue, None, True, False, _):
            summarise_issue(args, server)
        
        # Summarise issues from file
        case (None, args.file, True, False, _):
            summary = summarise_file(args, server)
            csv_output(summary, out=args.output)
        
        # Migrate Issue
        case (args.issue, None, False, True, _):
            issue_migration(args, server)

        # Migrate issues from file
        case (None, args.file, False, True, _):
            bulk_migration(args, server)
        
        # Transition Issue
        case (args.issue, None, False, False, args.transition):
            process_issue(config=args.config,
                          issue=args.issue,
                          transition=args.transition,
                          resolution=args.resolution,
                          comment=args.comment)

        # Transition issues from file
        case (None, args.file, False, False, args.transition):
            process_file(in_file=arg.file,
                         config=args.config,
                         issue=args.issue,
                         transition=args.transition,
                         resolution=args.resolution,
                         comment=args.comment)

        case _:
            print('no matches')

    '''
    if args.issue:

    elif args.file:
        JIRA.migrate_issue()

    '''
    return


### Main ###
if __name__ == '__main__':
    exitcode = main()
    exit(exitcode)
## End Main ###