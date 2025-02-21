#!/usr/bin/env python3

__author__ = 'Chris Marrison'
__email__ = 'chris@infoblox.com'
__version__ = '0.0.1'

import argparse
import logging
import time
import csv
import sys
import issues

_logger = logging.getLogger(__name__)


class UpdateReporter:
    '''
    '''
    def __init__(self, inifile:str = 'jira.ini', server:str = None):
        '''
        '''
        self.issue = issues.ISSUES(inifile=inifile, server=server)

        return

    def update_reporter(self, issue_key:str, email:str):
        '''
        '''
        status:bool = False

        try:
            if self.issue.get_issue(issue_key):
                _logger.info(f"Found issue {issue_key}")

                # Update the reporter
                if self.issue.update_reporter(email=email):
                    _logger.info(f"Successfully updated reporter for issue {issue_key} to {email}")
                    status = True
                else:
                    _logger.error(f"Failed to update reporter for issue {issue_key}: {e}")

            else:
                _logger.error(f"Failed to find issue {issue_key}")

        except Exception as e:
            _logger.error(f"Failed to update reporter for issue {issue_key}: {e}")
        
        return status


    def bulk_update_reporters(self, csv_filename:str):
        '''
        '''
        try:
            with open(csv_filename, mode='r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    self.update_reporter(row['key'], row['email'])

        except Exception as e:
            _logger.error(f"Failed to perform bulk update: {e}")
        
        return


    
def parseargs():
    '''
    Parse Arguments Using argparse

    Parameters:
        None

    Returns:
        Returns parsed arguments
    '''
    parse = argparse.ArgumentParser(description="Update the reporter for a Jira issue.")
    parse.add_argument('-c', '--config', type=str, default='jira.ini',
                       help="Input file")
    parse.add_argument('-i', '--issue', type=str, 
                       help="The issue key to update.")
    parse.add_argument('-e', '--email', type=str, 
                       help="The email address of the new reporter.")
    parse.add_argument('-v', '--csv', type=str, 
                       help="CSV file with issue keys and email addresses for bulk update.")
    parse.add_argument('-s', '--sandbox', action='store_true',
                       help="Connect to the Jira Sandbox server.")
    parse.add_argument('-S', '--silent', action='store_true', 
                       help="Suppress output to stdout.")
    parse.add_argument('-d', '--debug', action='store_true', 
                       help="Enable debug messages")

    return parse.parse_args()


def main():
    '''
    '''
    exitcode = 0
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
    
    # Instantiate the class
    update = UpdateReporter(inifile=args.config, server=server)

    if args.issue and args.email:
        update.update_reporter(args.issue, args.email)
    elif args.csv:
        update.bulk_update_reporters(args.csv)
    else:
        print("Please provide either --issue and --email for a single update or --csv for a bulk update.")
        exitcode = 1

    return exitcode


### MAIN ###
if __name__ == "__main__":
    exitcode = main()
    exit(exitcode)
## End Main ###