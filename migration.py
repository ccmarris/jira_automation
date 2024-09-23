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
__version__ = '0.0.1'
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
                logging.error(f'Cannot find source Jira issue: {source}')
        return