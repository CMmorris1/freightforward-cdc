"""
Date: Feb 2026

Description: Postgres global variables for uploading data to database

Author: Christopher M. Morris

E-mail: cmorris.morris@gmail.com

Company: Freelance

Location: 

"""

tableExists_query = 'SELECT EXISTS(SELECT * FROM information_schema.tables WHERE table_name=%s)'

tableExistsinSchema_query = 'SELECT EXISTS(SELECT * FROM information_schema.tables WHERE table_schema=%s AND table_name=%s)'

schemaExists_query = 'SELECT EXISTS(SELECT * FROM information_schema.schemata WHERE schema_name=%s)'

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    INFO = '\033[96m'
    OKGREEN = '\033[32m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'