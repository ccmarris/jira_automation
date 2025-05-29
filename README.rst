Jira Automation Tools
=====================

Overview
--------
This repository contains command-line tools and modules for automating Jira
issue management and migration tasks. The main modules are:

- **issues.py**: Provides a Python interface for interacting with Jira issues
                 (create, update, comment, transition, etc.).
- **migration.py**: Supports migration of issues or data between Jira
                    instances or projects.

Interactive CLI
---------------
An interactive CLI (`jira_cli.py`) is provided for convenient management of Jira
issues from the terminal. It uses the `cmd` module for a shell-like experience.

Features
--------
- List, view, create, update, and comment on Jira issues.
- Transition issues and update custom fields.
- Support for quoted arguments (e.g., summaries or descriptions with spaces).
- JQL (Jira Query Language) support for searching issues.
- Output redirection: send command output to a file using `> filename`.
- Migration utilities for bulk or cross-instance operations.

Usage
-----

**Interactive CLI:**

.. code-block:: bash

    python jira_cli.py [-i JIRA_INI_FILE]

Example commands inside the CLI:

.. code-block:: text

    get ISSUE-123
    show
    create "Summary with spaces" "Description with details"
    comment "This is a comment"
    updatefield customfield_10010 "New Value"
    query "project = MYPROJECT AND status = Open" > ~/tmp/report.txt
    status
    quit

You can redirect output to a file using `>`:

.. code-block:: text

    query "project = MYPROJECT AND status = Open" > ~/tmp/report.txt
    show > details.txt

You can use `~` or relative paths in filenames; these will be expanded to absolute paths.

**Scripting with issues.py:**

You can import `issues.py` in your own scripts:

.. code-block:: python

    from issues import ISSUES

    issues = ISSUES(inifile='jira.ini')
    issues.get_issue('ISSUE-123')
    issues.add_comment('This is a comment.')

**Migration:**

Refer to `migration.py` for migration-related functions and usage. Typical
usage involves importing the module and calling migration functions with
appropriate parameters.

Configuration
-------------
The tools require a Jira configuration file (INI format) with server and
authentication details. By default, `jira.ini` is used, but you can specify
another file with the `-i` option.

Dependencies
------------
- Python 3.8+
- `jira` Python library
- `rich` (for colored CLI output)

Install dependencies with:

.. code-block:: bash

    pip install jira rich

License
-------
BSD 2-Clause License (see source files for details).

Author
------
Chris Marrison / Infoblox

Acknowledgements
----------------
This project is inspired by the need for efficient Jira issue management and
migration. It is designed to simplify common tasks and provide a flexible
interface for both interactive use and scripting.

Thanks to Steve Makousky for testing and feedback.

Support
-------
For questions or contributions, please contact the author or open an issue in
this repository.