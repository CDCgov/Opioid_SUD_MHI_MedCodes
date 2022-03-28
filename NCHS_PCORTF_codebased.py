# -*- coding: utf-8 -*-
"""
For the code-based algorithm for FY19 (SUD and MHI). This is the portion
that searches the condition table. For Github release,
make one script that takes a table as input, a file for what codes you want
to search and what category they are mapped to, which column to search.

@author: oxf7
"""
from collections import defaultdict
import configparser
import csv
import logging
from pathlib import Path
import sys

import numpy as np
import pandas as pd

pd.options.mode.chained_assignment = None

def search(arglist):
    input_type, cnxn_string, cursor_execute_string, input_filepath, codes_dictionary, \
    higher_groups, results_file, logging_file, column_to_search, columns_to_keep, \
    inclusions_dict, exclusions_dict, output_zeros = arglist

    
    cols_to_keep = columns_to_keep + list(codes_dictionary.keys()) +  [x[0] for x in higher_groups]
    #eval columns will be those that we look at for purposes of determining which rows
    #should be output depending on user setting of output_zeros
    zeros_columns = list(codes_dictionary.keys())
#    print(cols_to_keep)
    chunksize = 10000
    
    #if input type is DB, connect to server and start a cursor. Will iterate over cursor
    #if input type is CSV, open file and get a DictReader. Will iterate over rows as dicts
    #if input type is SAS, get a df iterable 
    #input specifications are all read in as strings, including digits which will be strings and not int
    #in order to accommodate this, read in everything as a string.
    
    if input_type == "DB":
        import pyodbc
        logging.info("Connecting to SQL DB...")
        cnxn = pyodbc.connect(cnxn_string)        
        df_iter = pd.read_sql(cursor_execute_string, cnxn, chunksize=chunksize)
        logging.info(f"Connected to db with execute string {cursor_execute_string}")   
        
    elif input_type== "CSV":
        df_iter = pd.read_csv(input_filepath, chunksize=chunksize)
        
    elif input_type == "SAS":        
        df_iter = pd.read_sas(input_filepath, encoding='iso-8859-1', chunksize=chunksize)
        
    

    logging.info(f"Processing dataframes in chunks of {chunksize} rows")
    for counter, df in enumerate(df_iter):
        if df[column_to_search].dtype=="O":
            df[column_to_search] = df[column_to_search].str.replace(".", "", regex=False)
        print(f"Processed df {counter}")
        logging.info(f"Processed df {counter}")
        for k, v in inclusions_dict.items():
            df = df.loc[df[k].isin(v)]
        for k, v in exclusions_dict.items():
            df = df.loc[~df[k].isin(v)]
        for k, v in codes_dictionary.items():
            df[k] = np.where(df[column_to_search].isin(v), 1, 0)
        for group in higher_groups:
            new_col = group[0]
            child_groups = group[1:]
            df[new_col] = np.where(df[child_groups].max(axis=1)==1, 1, 0)
            
        df = df[cols_to_keep]
        if not output_zeros: #if output_zeros is False, which is default
            df = df.loc[df[zeros_columns].max(axis=1)==1]
    #
        if counter == 0:
            df.to_csv(results_file, mode='w', index=False)
        else:
            df.to_csv(results_file, mode='a', index=False, header=False)
        logging.info(f"Appended additional rows {len(df)}")

    print("Search complete")
    logging.info("COMPLETE")


def parse_and_run(configfile):
    config = configparser.ConfigParser()   
    config.read(configfile)    
    required_headers = ['OUTPUT_SETTINGS', 'INPUT_SETTINGS', 'CODES', 'SEARCH_OPTIONS']
    for req in required_headers:
        if req not in config:
            raise KeyError(f"Required configuration option {req} is unspecified. See ReadMe for guidance.")
            
          
    #OUTPUT. Let's start here to get logfile up and running
    if "results_file" not in config['OUTPUT_SETTINGS'] or "logging_file" not in config['OUTPUT_SETTINGS']:
        raise KeyError("You must specify results_file path and logging_file path")
    results_file = config['OUTPUT_SETTINGS']['results_file'].strip()
    logging_file = config['OUTPUT_SETTINGS']['logging_file'].strip()
    if results_file == '' or logging_file == '':
        raise ValueError("You must specify results_file and logging_file")
    results_file = Path(results_file)
    logging_file = Path(logging_file)
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s',
                        level=logging.INFO, filemode='w', filename=logging_file) 
    logging.info(f"Your output file has been specified as: {results_file.name}")

    
    #INPUT_SETTINGS
    if 'input_type' not in config['INPUT_SETTINGS'] or \
    config['INPUT_SETTINGS']['input_type'].strip().lower() not in ("csv", 'sas', 'db'):
        raise ValueError("Input type unspecified or improperly specified")
        
        
    if config['INPUT_SETTINGS']['input_type'].upper().strip() == "DB":
        input_type="DB"
        if ("cnxn_string" not in config['INPUT_SETTINGS']) or ("cursor_execute_string" not in config["INPUT_SETTINGS"]):
            raise KeyError("You specified input type as DB but did not specify cnxn_string or did not specify cursor_execute_string")

        cnxn_string = config['INPUT_SETTINGS']['cnxn_string'].strip()
        cursor_execute_string = config['INPUT_SETTINGS']['cursor_execute_string'].strip()
        
        if cnxn_string =='' or cursor_execute_string=="":
            raise ValueError("You have not specified cnxn_string or cursor_execute_string")
        input_filepath = None            

    elif config['INPUT_SETTINGS']['input_type'].upper().strip() in ("CSV", "SAS"):
        input_type=config['INPUT_SETTINGS']['input_type'].upper().strip()
        
        if "input_filepath" not in config["INPUT_SETTINGS"]:
            raise KeyError("You specified input type as CSV or SAS but did not specify input_filepath for it")
        input_filepath = config['INPUT_SETTINGS']['input_filepath'].strip()
        if input_filepath=="":
            raise ValueError("You have specified input_type as CSV or SAS but did not specified csv_input_file")
            
        input_filepath = Path(input_filepath)
        cnxn_string = None
        cursor_execute_string = None
    else:
        raise ValueError("You must specify input_type as db, csv, or sas")
        
    logging.info(f"Your input type has been specified as {input_type}")   
    #CODES
    if "codes_filepath" not in config['CODES']:
        raise KeyError("You must specify path to codes you are searching for")
    codes_filepath = config['CODES']["codes_filepath"].strip()
    if codes_filepath =='':
        raise ValueError("You must enter the path for codes you are searching for")
    codes_filepath = Path(codes_filepath)
    codes_dictionary = defaultdict(set)
    with codes_filepath.open(encoding='utf-8', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            codes_dictionary[row['CATEGORY'].strip()].add(row['CODE'].strip())
        

    if "groups_filepath" not in config['CODES'] or\
    config['CODES']['groups_filepath'].strip() == '':
        higher_groups = []
        logging.info("No additional umbrella variables will be created")
    else:
        grouping_file = config['CODES']['groups_filepath'].strip()
        grouping_file = Path(grouping_file)
        higher_groups = []#list of lists, 1st position is new category to create, 2nd is column names used to build
        with grouping_file.open(newline='') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                higher_groups.append([x for x in row if x.strip()])    
        
    #SEARCH_OPTIONS
    if "column_to_search" not in config['SEARCH_OPTIONS'] or \
    config['SEARCH_OPTIONS']['column_to_search'].strip() == '':
        raise ValueError("You have not specified the column to search for your codes in")
    column_to_search = config['SEARCH_OPTIONS']['column_to_search'].strip()
    if "columns_to_keep" not in config['SEARCH_OPTIONS'] or \
    config['SEARCH_OPTIONS']["columns_to_keep"].strip() == '':
        columns_to_keep = []
        logging.info("No columns other than the variable flags created will be kept")
    else:
        columns_to_keep_s = config['SEARCH_OPTIONS']["columns_to_keep"].strip()
        columns_to_keep = [x.strip() for x in columns_to_keep_s.split(',') if x.strip()]
    inclusion_specs = [x for x in config['SEARCH_OPTIONS'] if x.startswith("inclusion")]
    if inclusion_specs==[]:
        inclusions_dict = None
    else:
        inclusions_dict = defaultdict(set)
        for spec_key in inclusion_specs:
            inclusion_spec_string = config['SEARCH_OPTIONS'][spec_key].strip()
            if inclusion_spec_string=="":
                continue
            incl_components_init = [x.strip() for x in inclusion_spec_string.split(",") if x.strip()]
            incl_col = incl_components_init[0]
            incl_vals = []
            for x in incl_components_init[1:]:
                try:
                    incl_vals.append(float(x))
                except ValueError:
                    incl_vals.append(x)                  
            inclusions_dict[incl_col].update(set(incl_vals))
            
    exclusion_specs = [x.strip() for x in config['SEARCH_OPTIONS'] if x.startswith("exclusion")]
    if exclusion_specs==[]:
        exclusions_dict = None
    else:
        exclusions_dict = defaultdict(set)
        for spec in exclusion_specs:
            print(f"Exclusion spec {spec}")
            if config['SEARCH_OPTIONS'][spec].strip()=="":
                continue
            excl_components_init = [x.strip() for x in config['SEARCH_OPTIONS'][spec].split(",") if x.strip()]
            excl_col = excl_components_init[0]
            excl_vals = []
            for x in excl_components_init[1:]:
                try:
                    excl_vals.append(float(x))
                except ValueError:
                    excl_vals.append(x)
            exclusions_dict[excl_col].update(set(excl_vals))            
    for k, v in inclusions_dict.items():
        logging.info(f"At column {k} including only values: {v}")
    for k, v in exclusions_dict.items():
        logging.info(f"At column {k} excluding values: {v}")
    #change default behavior of only outputting rows with at least one '1' flag
    if 'output_zeros' in config['SEARCH_OPTIONS'] and config['SEARCH_OPTIONS']['output_zeros'].lower().strip()=="true":
        output_zeros = True
    else:
        output_zeros = False
        
    return([input_type, cnxn_string, cursor_execute_string,
           input_filepath, codes_dictionary, higher_groups,
           results_file, logging_file, column_to_search, columns_to_keep,
           inclusions_dict, exclusions_dict, output_zeros])
        
           

if __name__ == "__main__":
    #Windows paths need the r for raw string, to handle the backslashes.
    configfile = Path(r"codebased_config.txt")
    if len(sys.argv) > 1:
        configfile = Path(sys.argv[1].strip())
        print(f"Configfile read in as {configfile}")

    else: #if not via command line, specify configfile path here
        configfile = configfile
        print(f"Config file hard-coded and specified as {configfile}")
    if not configfile:
        raise ValueError("You must specify a config file either hard-coded in main or via a config file")
        
    arglist = parse_and_run(configfile)
    search(arglist)
