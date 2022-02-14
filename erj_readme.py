'''Following Docstring Convention: https://www.python.org/dev/peps/pep-0257/'''

import pandas as pd
import os
#THESE SETTINGS ESSENTIAL TO HAVE THE FIELDS TABLE SHOW UP CORRECTLY in the readme
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)


def create_fields_table(race_field_header_0, fields_dict_0, 
                        add_race_field_header_1 = '', fields_dict_1 = {}, 
                        add_race_field_header_2 = '', fields_dict_2 = {}, 
                        add_race_field_header_3 = '', fields_dict_3 = {}):
    '''Purpose: Create fields table used in readme based on field dictionary created separately
    Arguments:
        race_field_header_0: include asterisks "***text***" and label first set of fields
        fields_dict_0: the default dictionary for the primary file (statewide)
        add_race_field_header_1: include asterisks to draw attention to section - ex: "***additional_race_file_name_fields***"
        fields_dict_1: additional fields to go under add_race_field_header_1 header
        add_race_field_header_2 and _3: same use as add_race_field_header_1 - include as needed
        fields_dict_2 and _3: same use as fields_dict_1 - include as needed associated with corresponding add_race_field_header section
    '''
    fields_table_data = {'Field Name': ['',race_field_header_0]  + list(fields_dict_0.keys()) +
                         ['',add_race_field_header_1] + list(fields_dict_1.keys()) +
                         ['',add_race_field_header_2] + list(fields_dict_2.keys()) +
                         ['',add_race_field_header_3] + list(fields_dict_3.keys()),
                         'Description': ['',''] + list(fields_dict_0.values()) + 
                         ['',''] + list(fields_dict_1.values()) + 
                         ['',''] + list(fields_dict_2.values()) +
                         ['',''] + list(fields_dict_3.values())}
    fields_table = pd.DataFrame(fields_table_data)
    return fields_table

def erj_readme_template(stateabrv, state, year, election_type, additional_races, retrieval_date, vest_file_link, 
                        raw_data_source, state_erj_repo, office_codes, 
                        race_field_header_0, fields_dict_0, add_race_field_header_1 = '', fields_dict_1 = {}, add_race_field_header_2 = '', fields_dict_2 = {}, 
                        add_race_field_header_3 = '', fields_dict_3 = {},
                       additional_notes=' '):
    '''Purpose: standardize language in ERJ file README.txt
    Arguemts:
        fields_dict = used to create the fields table for the non-standardized/race fields fields. 
                    Key is the field/value is the field description
        stateabrv = two character state abbreviation capitalized, 
        state = state name, first letter capitalized, 
        year = election year (XXXX), 
        election_type = general, primary, special or runoff, 
        additional_races = the races that RDH added to the original vest file (not in VEST's og file), 
        retrieval_date = date RDH retrieved VEST file, 
        vest_file_link = link to dataverse page for VEST's precinct boundary and election results file, 
        raw_data_source = site description and link, 
        state_erj_repo = link to erj github repository for given state
        office_codes = codes used broken off of field names for easy viewing. 
            For SU/SL/CON, include ##, so SU## for office code
        race_field_header_0: include asterisks "***text***" and label first set of fields
        fields_dict_0: the default dictionary for the primary file (statewide)
        add_race_field_header_1: include asterisks to draw attention to section - ex: "***additional_race_file_name_fields***"
        fields_dict_1: additional fields to go under add_race_field_header_1 header
        add_race_field_header_2 and _3: same use as add_race_field_header_1 - include as needed
        fields_dict_2 and _3: same use as fields_dict_1 - include as needed associated with corresponding add_race_field_header section
        additional_notes = default set to empty, but fill in with string where applicable.
    '''
#First section of README
    readme_p1 = '''{year} {stateabrv} {election_type} election results

## RDH Date Retrieval
{retrieval_date}

## Sources
The RDH retrieved the VEST {year} {election_type} precinct boundary and election results shapefile from [VEST's Harvard Dataverse]({vest_file_link})
The RDH retrieved raw {year} {election_type} election results from {raw_data_source}

## Notes on Field Names (adapted from VEST):
Columns reporting votes generally follow the pattern: 
The first character is G for a general election, P for a primary, S for a special, and R for a runoff.
Characters 2 and 3 are the year of the election.*
Characters 4-6 represent the office type (see list below).
Character 7 represents the party of the candidate.
Characters 8-10 are the first three letters of the candidate's last name.
One example is:
G16PREDCLI

To fit within the GIS 10 character limit for field names, the naming convention is slightly different for the State Legislature and 
US House of Representatives. All fields are listed below with definitions.

Office Codes Used:
{office_codes}

## Fields:

'''.format(stateabrv= stateabrv, state= state, year=year, election_type=election_type, additional_races=additional_races,retrieval_date=retrieval_date, vest_file_link=vest_file_link, raw_data_source=raw_data_source, state_erj_repo=state_erj_repo, office_codes=office_codes)

#Second section of README
    fields_table = create_fields_table(race_field_header_0, fields_dict_0, add_race_field_header_1, fields_dict_1, add_race_field_header_2, fields_dict_2, 
                        add_race_field_header_3, fields_dict_3)
    readme_p2 = fields_table.to_string(formatters={'Description':'{{:<{}s}}'.format(fields_table['Description'].str.len().max()).format, 'Field Name':'{{:<{}s}}'.format(fields_table['Field Name'].str.len().max()).format}, index=False)

#Third section of README
    readme_p3 = '''
## Processing Steps
    
The RDH joined additional election results to VEST's existing precinct shapefile, including {additional_races} using Python.
For more information on the processing completed, visit our [Github repository]({state_erj_repo}) for Election Result Joins (ERJ) for {state}.

Where possible, the RDH validated the election results we processed against VEST's election results. For additional races the RDH manually checked state totals. For more information on this comparison, please see our processing on Github ({state_erj_repo}).

## Additional Notes
{additional_notes}

Please contact info@redistrictingdatahub.org for more information.
'''.format(stateabrv=stateabrv, state=state, year=year, election_type=election_type, additional_races=additional_races, state_erj_repo=state_erj_repo, office_codes=office_codes, additional_notes = additional_notes)
    
    full_readme = str(readme_p1)+str(readme_p2)+str(readme_p3)
    return full_readme

def export_readme(readme_name, state, election_type, full_readme_text):
    
    '''Purpose: Turn README string into a txt file in the ERJ folder
    Argument note:
        readme_name must include file path to readme within erj folder
        ex: 
        readme_name = './az_gen_20_prec/README.txt'
    '''
    with open(readme_name, 'x') as tf:
        tf.write(full_readme_text)
    print(state, election_type, " readme moved to folder")