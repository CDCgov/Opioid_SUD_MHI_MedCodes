# Opioid_SUD_MHI_MedCodes  

March 1, 2022 

Author: Nikki Adams; NAdams2@cdc.gov 

This is a Python version of the original SAS code used to analyze the 2016 National Hospital Care Survey (NHCS) data for the fiscal year (FY) 2018 and 2019 Office of the Secretary-Patient-Centered Outcomes Research Trust Fund-funded projects on the identification of patients with opioid-involved hospitalizations and emergency department (ED) visits. The National Center for Health Statistics conducts NHCS which involves the collection of a participating hospital’s (UB)-04 administrative claims records or electronic health records (EHR) in a 12-month period. The first algorithm identifies patients with opioid-involved hospitalizations and ED visits (FY18) by utilizing the structured coded medical data and analyzing free text in the EHR clinical notes. The second algorithm then identifies patients with opioid-involved hospitalizations or ED visits that have a co-occurring substance use disorder or a mental health issue (FY19). For a hospital to be eligible for NHCS, the hospital must be a non-federal, non-institutional hospital with 6 or more staffed inpatient beds. This is the release of the medical code-based algorithm, which analyzed the structured data. It specifies which codes map to which variables and how the child/parent variables were built. It searches structured data containing medical codes for opioid-involvement, including opioid overdose, substance use disorders, and selected mental health issues (primarily related to anxiety and depression).

For more information on methodology and development, please see the methodology report linked below. It describes the methodology for the FY18 project, but the FY19 methodology is similar: 

https://www.cdc.gov/nchs/data/series/sr_02/sr2-188.pdf

This repository contains mappings for child categories under the parent categories Opioid Involvement, Substance Use Disorder, and Mental Health Issues. It also contains a sample input data file. It should be possible to run this code on the sample data file, using the included sample config file as-is. To calculate the final counts for the parent categories, after running the code, these parent categories can be created by counting all observations where any value in the child category (e.g., SUD_NICOTINE) creates a positive flag in the parent category (e.g., SUD). For more information, see the data dictionary and description her:

FY18: https://www.cdc.gov/nchs/data/nhcs/Task-3-Doc-508.pdf

FY19: https://www.cdc.gov/nchs/data/nhcs/FY19-RDC-2021-06-01-508.pdf


**Usage**

Once the config file is properly set up, this code can be run, either by hard-coding in the config file in the main portion of the code or by passing in the config file, as a command line argument. 

Option 1 – Hard coded 
Look in the main code for these lines and put the path where indicated: 

```python 
configfile = Path(r"codebased_config.txt") 

 ```
Option 2 – Command line argument 

At a command line type: 

    python  NCHS_PCORTF_codebased.py codebased_config.txt 

An example input CSV file would contain the information below. Be aware, all periods in the column specified as the column to search for codes will be automatically stripped to match the formatting of the search codes provided. For example, "T14.91XA" will be stripped of its period to become "T1491XA" before it is searched. This does not change the source file, but if the CODE column below is specified as one of the output columns, the value will be the form without the periods, not its original form:

| UNIQUE_ID | ID_SETTING | STATE | CODE | MEDICARE |
| ----- | ----- | ----- | ----- | ----- |
| 123X | ED | ALASKA | T14.91XA | 0 |
| 456X | ED-to-IP | ALASKA | F322 | 1 |
| 835T | ED | NEW YORK | F15220 | 0 |

An example of the CSV mappings is shown below. 

| CODE | CATEGORY |
| ------ | ------ |
| F322 | CODE_DEPRESSION_SINGLE |
| T1491XA | CODE_SUICIDE_ATTEMPT |
| F15220 | CODE_SUD_OTH_STIMULANT |


Example output is shown below, with configuration options set to exclude MEDICARE = 1 and output_zeros = True so that even observations that have no positive flags for any variables still have an output:


| UNIQUE_ID | ID_SETTING | CODE_DEPRESSION_SINGLE | CODE_SUICIDE_ATTEMPT | CODE_SUD_OTH_STIMULANT |
| ------ | ------ | ------ | ------ | ------ |
| 123X | ED | 0 | 1 | 0 |
| 456X | ED-to-IP | 0 | 0 | 0 |
| 845T | ED | 0 | 0 | 1 |




**Package Requirements**

Running this code requires the software below. However, pyodbc is not needed if the input data is not coming through a SQL database connection, i.e. if it is coming from a SAS dataset or a CSV file: 

    python >= 3.4 
    pandas >=0.24.1
    pyodbc >=4.0
    


**Input and Output Files **
There will be 3-4 files to serve as input for this package (one is optional), and it will produce 2 output files 

_Input file #1_ – Source data 

This package will accept three types of input data: (1) a csv file, with column names as the first row, (2) a table in Microsoft SQL for Windows, or (3) a SAS .sas7bdat file. In theory, connecting to SQLite and possible other databases should work the same as connecting to SQL, with the code as we have currently written it. However, this theory has not been tested. 

_Input file #2_ – Code mapping 

This file is a csv file where the first column is the code to be searched and the second column is the output variable to be flagged if that code is found. Below is an example of the first 3 lines of what this file should look like: 

    CODE,CATEGORY 
    F324,CODE_DEPRESSION_SINGLE
    F3341,CODE_DEPRESSION_RECURRENT

_Input file Optional_ - groups_filepath

Parent or umbrella categories can be automatically created as well with this file. This is a csv file with no header, where for each line, the first variable name in the line is the parent variable and all items after that are the children that comprise that parent. For example, if the goal is for a flag in CODE_DEPRESSION_SINGLE or CODE_DEPRESSION_RECURRENT to trigger a flag in the parent category CODE_DEPRESSION, there should be a line like this:

    CODE_DEPRESSION,CODE_DEPRESSION_SINGLE,CODE_DEPRESSION_RECURRENT

Parent level variables can themselves be the child of another parent category. It is only required that the creation of parent variables be listed in the order that they would have to be built (i.e. Parent1 must be built first before it can subsequently be a child to Parent2).

_Input file #3_ – Config file 

This file specifies where the input files are, where the output files will go, and other allowed options. A sample config file is included in this repository, but we explain every option in the next section.  

_Output file #1_ – Results file 

This file will have the results of the term search 

_Output file #2_ – log file 

This file will print status updates on the search, printing an update every 100,000 rows of search, along with a final completion message.

**Setting Up Your Config File** 

Note that values should not include quotation marks. Below is an example of a properly formatted config file:

    [INPUT_SETTINGS]
    input_type = csv
    cnxn_string = 
    cursor_execute_string = 
    input_filepath = yourpath\example_input_file.txt

    [CODES]
    codes_filepath = yourpath\code_mappings.txt
    groups_filepath = yourpathcode_groupings.txt

    [OUTPUT_SETTINGS]
    results_file = yourpath\fy19_codebased_test_output.txt
    logging_file = \yourpath\fy19_codebased_test_log.txt

    [SEARCH_OPTIONS]
    column_to_search = CODE
    columns_to_keep = UNIQUE_ID, STATE
    inclusions_1 = ID_SETTING, IP, ED-to-IP, ED
    inclusions_2 = 
    exclusions_1 = MEDICARE, 1
    exclusions_2 = 
    output_zeros = False

Included above are all available options, with examples. The text below explains whether they are required or optional and what to specify:

    [INPUT_SETTINGS] 
    input_type: REQUIRED. Options are CSV, DB for database connection, or SAS for a .sas7bdat file. 
    cnxn_string: REQUIRED if input_type=DB. The string is used to connect to the database through pyodbc. 
    cursor_execute_string: REQUIRED if input_type=DB. This is the query select string. 
    input_filepath: REQUIRED if input_type is CSV or SAS. This is the path to the input file. 

    [CODES]
    codes_filepath: REQUIRED. This is the path to a 2-column csv file of code to be searched for and variable names to map to it. This file has a header of "CODE,CATEGORY", as shown in the example earlier and as seen in the code mappings file included with this release 
    groups_filepath: OPTIONAL. This is the path to a csv file with no header, where for each row, the first position is the parent category to be created and every position after that is a child to be included in that parent category.

    [OUTPUT] 
    results_file: REQUIRED. This is the path to the output file. Output is csv format. 
    logging_file: REQUIRED. This is the path where logging messages about output will print. 

    [SEARCH_CONFIG] 
    column_to_search: REQUIRED. This defines which column the code searches are performed in. Case-sensitive. 
    columns_to_keep: OPTIONAL. A comma-separated list of which columns (e.g. unique identifiers or linkage variables) to be output with each result. Case-sensitive. 

    inclusions_x: OPTIONAL. A comma-separated list of at least length 2. The first item is the column in which the exclusion is to be searched for. Every item after that contains the inclusion values. 
    There is no limit on inclusions within a line, but each inclusions_X line applies to only one column. For example:
        inclusions_1: COLUMN_1, inclusion1, inclusion2, inclusion3
        inclusions_2: COLUMN_2, inclusion4, inclusion5, inclusion6 

    As a more specific example: 
        STATE, ALABAMA, Alaska
    would include only rows for which the value in column STATE equals “ALABAMA” or “Alaska”. Case-sensitive. The value of the cell must equal the exclusion, i.e. this is not a substring search. 

    exclusions_x: OPTIONAL. This operates just as inclusions_x does, except it will not flag anything in rows where the exclusion applies. For example, entering:
        STATE, ALABAMA, Alaska
    here would exclude from search results any observations where the value in STATE is ALABAMA or Alaska (case-sensitive).

    output_zeros: OPTIONAL. Default will be false, so True must be specified. If true, there will be an output for every input observation, regardless of whether anything was found. If false, only rows where something was positively flagged will be output.


**Licenses and Disclaimers**

**Public Domain**

This repository constitutes a work of the United States Government and is not subject to domestic copyright protection under 17 USC § 105. This repository is in the public domain within the United States, and copyright and related rights in the work worldwide are waived through the [CC0 1.0 Universal public domain dedication](https://creativecommons.org/publicdomain/zero/1.0/). All contributions to this repository will be released under the CC0 dedication. By submitting a pull request you are agreeing to comply with this waiver of copyright interest.

**License**

The repository utilizes code licensed under the terms of the Apache Software License and therefore is licensed under ASL v2 or later.

This source code in this repository is free: you can redistribute it and/or modify it under the terms of the Apache Software License version 2, or (at your option) any later version.

This source code in this repository is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the Apache Software License for more details.

You should have received a copy of the Apache Software License along with this program. If not, see http://www.apache.org/licenses/LICENSE-2.0.html

The source code forked from other open source projects will inherit its license.

**Privacy**

This repository contains only non-sensitive, publicly available data and information. All material and community participation is covered by the Surveillance Platform [Disclaimer](https://github.com/CDCgov/template/blob/master/DISCLAIMER.md) and [Code of Conduct](https://github.com/CDCgov/template/blob/master/code-of-conduct.md). For more information about CDC's privacy policy, please visit http://www.cdc.gov/privacy.html.

**Contributing**

Anyone is encouraged to contribute to the repository by [forking](https://help.github.com/articles/fork-a-repo) and submitting a pull request. (If you are new to GitHub, you might start with a [basic tutorial](https://help.github.com/articles/set-up-git).) By contributing to this project, you grant a world-wide, royalty-free, perpetual, irrevocable, non-exclusive, transferable license to all users under the terms of the [Apache Software License v2](http://www.apache.org/licenses/LICENSE-2.0.html) or later.

All comments, messages, pull requests, and other submissions received through CDC including this GitHub page are subject to the [Presidential Records Act](http://www.archives.gov/about/laws/presidential-records.html) and may be archived. Learn more at http://www.cdc.gov/other/privacy.html.

**Records**

This repository is not a source of government records, but is a copy to increase collaboration and collaborative potential. All government records will be published through the [CDC web site](http://www.cdc.gov/).

**Notices**

Please refer to [CDC's Template Repository](https://github.com/CDCgov/template) for more information about [contributing to this repository](https://github.com/CDCgov/template/blob/master/CONTRIBUTING.md), [public domain notices and disclaimers](https://github.com/CDCgov/template/blob/master/DISCLAIMER.md), and [code of conduct](https://github.com/CDCgov/template/blob/master/code-of-conduct.md).

