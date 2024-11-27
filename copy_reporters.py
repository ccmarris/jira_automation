#!/usr/bin/env python3
import migration
import issues

s = issues.ISSUES('/Users/marrison/Projects/configs/jira.ini')
d = issues.ISSUES('/Users/marrison/Projects/configs/jira.ini')

f = open('reporters.txt', 'w')

for n in range(2,615):
    d.get_issue(f'IFR-{n}')
    rfe = d.issue.fields.customfield_14487
    s.get_issue(rfe)
    id = s.get_reporter_id()
    if d.update_reporter(id):
        print(f'IFR-{n}: Success')
        print(f'IFR-{n}: Success', file=f) 
    else:
        print(f'IFR-{n}: Failed')
        print(f'IFR-{n}: Failed', file=f) 
    
    

