'''Following Docstring Convention: https://www.python.org/dev/peps/pep-0257/'''

import pandas as pd
import os
#THESE SETTINGS ESSENTIAL TO HAVE THE FIELDS TABLE SHOW UP CORRECTLY in the readme
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)

     
def column_prefix_col(df, contest_col, election_type, election_year, cong_str='U.S. Representative in Congress', uss_str='U.S. Senator', pre_str='President', 
                      sll_str='State Representative', slu_str='State Senator', pro_str='Proposition', coc_str='Corporation', ssc_str='Supreme Court'):
    
    '''Purpose: standardize the RDH field naming conventions - 
    set up the prefix to use in next function (candidate names and districts added later)
    Sample Argument values:
        contest_col = 'contest'
        election_type = 'G'
        election_year = '20'
        cong_str = 'U.S. Representative in Congress'
        uss_str = 'U.S. Senator'
        pre_str = 'President'
        sll_str = 'State Representative'
        slu_str = 'State Senator'
        pro_str = 'Proposition'
        coc_str = 'Corporation'
        ssc_str = 'Supreme Court'
    '''
    
    df['contest_formatted'] = '0'
    pre_prefix = election_type+election_year
    df.loc[df[contest_col].map(lambda x: (cong_str in x)), 'contest_formatted'] = election_type+ 'CON'
    df.loc[df[contest_col].map(lambda x: (uss_str in x)), 'contest_formatted'] = pre_prefix+'USS'
    df.loc[df[contest_col].map(lambda x: (pre_str in x)), 'contest_formatted'] = pre_prefix+'PRE'
    df.loc[df[contest_col].map(lambda x: (sll_str in x)), 'contest_formatted'] = election_type+'SL' #State House
    df.loc[df[contest_col].map(lambda x: (slu_str in x)), 'contest_formatted'] = election_type+'SU' #State Senate 
    df.loc[df[contest_col].map(lambda x: (pro_str in x)), 'contest_formatted'] = pre_prefix+'PRO' 
    df.loc[df[contest_col].map(lambda x: (coc_str in x)), 'contest_formatted'] = pre_prefix+'COC'
    df.loc[df[contest_col].map(lambda x: (ssc_str in x)), 'contest_formatted'] = pre_prefix+'SSC'

    return df['contest_formatted']

def create_field_id(df, contest_col, election_type, election_year, cong_str='U.S. Representative in Congress', uss_str='U.S. Senator', pre_str='President', 
                      sll_str='State Representative', slu_str='State Senator', pro_str='Proposition', coc_str='Corporation', ssc_str='Supreme Court', party_1char='party', party_3char='party',choice_3char='choice', prop_number='contest', prop_choice='choice', 
                    sldl_dist='sldl_dist', sldl_zfill=2, sldu_dist='sldu_dist', sldu_zfill=2, con_dist='usrep_dist', ssc_yes_or_no='choice'):
    
    '''This fxn serves to standardize the RDH full field naming conventions 
    Use prefix from column_prefix_col() and candidate name/district info added as inputs.
    See defaults for sample variables, pull out of given file to use... Ask LF if more info needed
    '''
    
    df['contest_formatted'] = column_prefix_col(df, contest_col, election_type, election_year)
    #regular vote columns
    standard_format = df['contest_formatted'] + df[party_1char] + df[choice_3char]
    df.loc[df[contest_col].map(lambda x: (uss_str in x)|(pre_str in x)|(coc_str in x)), 'field_id'] = standard_format
    ssc_format = df['contest_formatted'] + df[ssc_yes_or_no] + df[choice_3char]
    df.loc[df[contest_col].map(lambda x: (ssc_str in x)), 'field_id'] = ssc_format
    proposition_format = df['contest_formatted'] + df[prop_number] + df[prop_choice]
    df.loc[df[contest_col].map(lambda x: (pro_str in x)), 'field_id'] = proposition_format

    sll_format = df['contest_formatted'] + df[sldl_dist].str.zfill(sldl_zfill) + df[party_1char] + df[choice_3char]
    slu_format = df['contest_formatted'] + df[sldu_dist].str.zfill(sldu_zfill) + df[party_1char] + df[choice_3char]
    con_format = df['contest_formatted'] + df[con_dist].str.zfill(2) + df[party_1char] + df[choice_3char]
    df.loc[df[contest_col].map(lambda x:(sll_str in x)), 'field_id'] = sll_format
    df.loc[df[contest_col].map(lambda x: (slu_str in x)), 'field_id'] = slu_format
    df.loc[df[contest_col].map(lambda x: (cong_str in x)), 'field_id'] = con_format
        
    owri_format = df['contest_formatted'] + 'OWRI'   
    df.loc[(df['is_write_in']=='true'), 'field_id'] = owri_format
    sll_owri = df['contest_formatted'] + df[sldl_dist].str.zfill(sldl_zfill) + 'OWRI'
    slu_owri = df['contest_formatted'] + df[sldu_dist].str.zfill(sldu_zfill) + 'OWRI'
    con_owri = df['contest_formatted'] + df[con_dist].str.zfill(2) + 'OWRI'
    df.loc[(df[contest_col].map(lambda x:(sll_str in x)))&(df['is_write_in']=='true'), 'field_id'] = sll_owri
    df.loc[(df[contest_col].map(lambda x: (slu_str in x)))&(df['is_write_in']=='true'), 'field_id'] = slu_owri
    df.loc[(df[contest_col].map(lambda x: (cong_str in x)))&(df['is_write_in']=='true'), 'field_id'] = con_owri

    return df['field_id']



def mk_precinct_district_id(df, precinct_key_col, sldl_dist_col, sldu_dist_col, usrep_dist_col):
    
    '''Purpose: create identifier that has precinct, state leg and congressional districts 
    to pivot on and check if any precincts were split by districts.
    
    Arguments:
        df: election results dataframe, pre-pivot
        precinct_key_col: unique precinct identifier - number or name
        sldl_dist_col: state leg lower district # col - listed in df with corresponding precinct key
        sldu_dist_col: state leg upper district # col - listed in df with corresponding precinct key
        usrep_dist_col: congressional district # col - listed in df with corresponding precinct key
    '''
    
    #Create column with precinct-district id for sldl, sldu and usrep
    df['prec_sldl_id_og'] = df['precinct_key'][df[sldl_dist_col]!='NA'] + '-'+df[sldl_dist_col][df[sldl_dist_col]!='NA']
    df['prec_sldu_id_og'] = df['precinct_key'][df[sldu_dist_col]!='NA'] + '-'+df[sldu_dist_col][df[sldu_dist_col]!='NA']
    df['prec_usrep_id_og'] = df['precinct_key'][df[usrep_dist_col]!='NA'] + '-'+df[usrep_dist_col][df[usrep_dist_col]!='NA']
    #Dictionary precinct_key: precinct_key with district
    sldl_prec_key_dict = {value : key for (key, value) in pd.Series(df['precinct_key'].values, index = df['prec_sldl_id_og']).to_dict().items()}
    sldu_prec_key_dict = {value : key for (key, value) in pd.Series(df['precinct_key'].values, index = df['prec_sldu_id_og']).to_dict().items()}
    usrep_prec_key_dict = {value : key for (key, value) in pd.Series(df['precinct_key'].values, index = df['prec_usrep_id_og']).to_dict().items()}
    #Create column for entire df with given district numbers
    df['prec_sldl_id_toall'] = df['precinct_key'].map(sldl_prec_key_dict)
    df['prec_sldu_id_toall'] = df['precinct_key'].map(sldu_prec_key_dict)
    df['prec_usrep_id_toall'] = df['precinct_key'].map(usrep_prec_key_dict)
    #Create column with single identifier with district numbers for every office
    df['prec_id_sldl_sldu_usrep'] = '['+df['prec_sldl_id_toall']+']['+df['prec_sldu_id_toall']+']['+df['prec_usrep_id_toall']+']'
    
    return df['prec_id_sldl_sldu_usrep']

def prec_split_check(sos_df, sos_precinct_id, vest_df, vest_precinct_id, sldl_dist_col, sldu_dist_col, usrep_dist_col, prec_id_sldl_sldu_usrep):
    
    '''Purpose: Make sure that the precinct IDs selected from SOS and VEST are the *unique* identifiers 
    (for VEST/pivoted results, make sure count of id matches length of file)
    '''
    
    sos_df[prec_id_sldl_sldu_usrep] = mk_precinct_district_id(sos_df, sos_precinct_id, sldl_dist_col, sldu_dist_col, usrep_dist_col)
    print('# vest unique precinct ids: ', vest_df[vest_precinct_id].nunique(), '\n # sos unique precinct ids: ', sos_df[sos_precinct_id].nunique(), 
          '\n # sos ids with districts attached: ', sos_df['prec_id_sldl_sldu_usrep'].nunique())
    if (vest_df[vest_precinct_id].nunique()==sos_df[sos_precinct_id].nunique())&(sos_df[sos_precinct_id].nunique()==sos_df[prec_id_sldl_sldu_usrep].nunique()):
        print('Counts match - no splits occurred!')
    elif (vest_df[vest_precinct_id].nunique()==sos_df[sos_precinct_id].nunique())&(sos_df[sos_precinct_id].nunique()!=sos_df[prec_id_sldl_sldu_usrep].nunique()):
        print('Split occurred!')
    elif (vest_df[vest_precinct_id].nunique()!=sos_df[sos_precinct_id].nunique()):
        print('unique id counts do not match!')
        
        
def statewide_totals_check(partner_df,source_df,column_list):
    """Compares the totals of two election result dataframes at the statewide total level

    Args:
      partner_df: DataFrame of election results we are comparing against
      source_df: DataFrame of election results we are comparing to
      column_list: List of races that there are votes for
 
    Returns:
      Nothing, only prints out an analysis
    """
    print("***Statewide Totals Check***")
    for race in column_list:
        if (partner_df[race].sum()- source_df[race].sum() != 0):
            print(race+" has a difference of "+str(partner_df[race].sum()-source_df[race].sum())+" votes")
            print("\tVEST: "+str(partner_df[race].sum())+" votes")
            print("\tSOURCES: "+str(source_df[race].sum())+" votes")
        else:
            print(race + " is equal", "\tVEST / RDH: " + str(partner_df[race].sum()))
            
            
def county_totals_check(partner_df,source_df,column_list,county_col,full_print=False):
    """Compares the totals of two election result dataframes at the county level

    Args:
      partner_df: DataFrame of election results we are comparing against
      source_df: DataFrame of election results we are comparing to
      column_list: List of races that there are votes for
      county_col: String of the column name that contains county information
      full_print: Boolean specifying whether to print out everything, including counties w/ similarities

    Returns:
      Nothing, only prints out an analysis
    """
    
    print("***Countywide Totals Check***")
    print("")
    diff_counties=[]
    for race in column_list:
        diff = partner_df.groupby([county_col]).sum()[race]-source_df.groupby([county_col]).sum()[race]
        for val in diff[diff != 0].index.values.tolist():
            if val not in diff_counties:
                diff_counties.append(val)
        if len(diff[diff != 0]!=0):   
            print(race + " contains differences in these counties:")
            for val in diff[diff != 0].index.values.tolist():
                county_differences = diff[diff != 0]
                print("\t"+val+" has a difference of "+str(county_differences[val])+" votes")
                print("\t\tVEST: "+str(partner_df.groupby([county_col]).sum().loc[val,race])+" votes")
                print("\t\tSOURCES: "+str(source_df.groupby([county_col]).sum().loc[val,race])+" votes")
            if (full_print):
                for val in diff[diff == 0].index.values.tolist():
                    county_similarities = diff[diff == 0]
                    print("\t"+val + ": "+ str(partner_df.groupby([county_col]).sum().loc[val,race])+" votes")
        else:
            print(race + " is equal across all counties")
            if (full_print):
                for val in diff[diff == 0].index.values.tolist():
                    county_similarities = diff[diff == 0]
                    print("\t"+val + ": "+ str(partner_df.groupby([county_col]).sum().loc[val,race])+" votes")
    if (len(diff_counties)>0):
        print()
        print(diff_counties)
        
        
def precinct_votes_check(merged_df,column_list,vest_on_left,name_col,print_level=0):
    """Checks a merged dataframe with two election results at the precinct level

    Args:
      merged_df: DataFrame with one set of election results joined to another
      column_list: List of races that there are votes for
      vest_on_left: Boolean specifying whether VEST data is on the left side of merged_df
      name_col: String of the column name to refer to precincts when a difference occurs
      print_level: Integer that specifies how large the vote difference in a precinct must be to be printed

    Returns:
      Nothing, only prints out an analysis
    """
    merged_df = merged_df.sort_values(by=[name_col],inplace=False)
    matching_rows = 0
    different_rows = 0
    diff_list=[]
    diff_values = []
    max_diff = 0
    for index,row in merged_df.iterrows():
        same = True
        for i in column_list:
            left_data = i + "_x"
            right_data = i + "_y"
            if ((row[left_data] is None) or (row[right_data] is None) or (np.isnan(row[right_data])or(np.isnan(row[left_data])))):
                print("FIX NaN value at: ", row[name_col])
                return;
            diff = abs(row[left_data]-row[right_data])
            if (diff>0):
                same = False
                diff_values.append(abs(diff))
                if (diff>max_diff):
                    max_diff = diff
            if(diff>print_level):
                if (vest_on_left):
                    print(i, "{:.>72}".format(row[name_col]), "(V)","{:.>5}".format(int(row[left_data]))," (S){:.>5}".format(int(row[right_data])),"(D):{:>5}".format(int(row[left_data]-row[right_data])))                           
                else:
                    print(i, "{:.>72}".format(row[name_col]), "(S)","{:.>5}".format(int(row[left_data]))," (V){:.>5}".format(int(row[right_data])),"(D):{:>5}".format(int(row[left_data]-row[right_data])))
        if(same != True):
            different_rows +=1
            diff_list.append(row[name_col])
        else:
            matching_rows +=1
    print("")
    print("There are ", len(merged_df.index)," total rows")
    print(different_rows," of these rows have election result differences")
    print(matching_rows," of these rows are the same")
    print("")
    print("The max difference between any one shared column in a row is: ", max_diff)
    if(len(diff_values)!=0):
        print("The average difference is: ", str(sum(diff_values)/len(diff_values)))
    count_big_diff = len([i for i in diff_values if i > 10])
    print("There are ", str(count_big_diff), "precinct results with a difference greater than 10")
    print("")
    print("All precincts containing differences:")
    diff_list.sort()
    print(diff_list)
    
    
from matplotlib.lines import Line2D

def compare_geometries(gdf_1,gdf_2,left_gdf_name,right_gdf_name,join_col_name,area_threshold=.1):
    '''
    Function that joins to GeoDataFrames on a column and reports area differences row-by-row.
    Should generally be used by grouping by the district assignments that we've made and comparing against an official map.
    '''
    gdf_1 = gdf_1.to_crs(3857)
    gdf_2 = gdf_2.to_crs(3857)
    both = pd.merge(gdf_1,gdf_2,how="outer",on=join_col_name,validate="1:1",indicator=True)
    if(both["_merge"].str.contains("_")).any():
        print("Non-unique merge values")
        raise ValueError
    left_geoms = gp.GeoDataFrame(both,geometry="geometry_x")
    right_geoms = gp.GeoDataFrame(both,geometry="geometry_y")
    left_geoms["geometry_x"]=left_geoms.buffer(0)
    right_geoms["geometry_y"]=right_geoms.buffer(0)
    if (left_geoms.is_valid==False).any():
        raise ValueError
    elif(right_geoms.is_valid==False).any():
        raise ValueError
    count = 0
    area_list = []
    print("Checking " + str(both.shape[0])+" districts for differences of greater than "+str(area_threshold)+" km^2")
    print()
    for index,row in both.iterrows():
        diff = left_geoms.iloc[[index]].symmetric_difference(right_geoms.iloc[[index]])
        intersection = left_geoms.iloc[[index]].intersection(right_geoms.iloc[[index]])
        area = float(diff.area/10e6)
        area_list.append(area)
        if (area > area_threshold):
            count += 1
            name = left_geoms.at[index,join_col_name]
            print(str(count)+") For " + name + " difference in area is " + str(area))
            if (intersection.iloc[0].is_empty):
                base = left_geoms.iloc[[index]].plot(color="orange",figsize=(10,10))
                right_geoms.iloc[[index]].plot(color="blue",ax=base)
                base.set_title(name)
                custom_lines = [Line2D([0], [0], color='green', lw=4),
                Line2D([0], [0], color='orange', lw=4),
                Line2D([0], [0], color='blue', lw=4)]
                base.legend(custom_lines, ['Overlap', left_gdf_name,right_gdf_name])
            else:
                base = left_geoms.iloc[[index]].plot(color="orange",figsize=(10,10))
                right_geoms.iloc[[index]].plot(color="blue",ax=base)
                intersection.plot(color="green",ax=base)
                base.set_title(name)
                custom_lines = [Line2D([0], [0], color='green', lw=4),
                Line2D([0], [0], color='orange', lw=4),
                Line2D([0], [0], color='blue', lw=4)]
                base.legend(custom_lines, ['Overlap', left_gdf_name,right_gdf_name])
                
                
    df = pd.DataFrame(area_list)
    print()
    print("Scroll down to see plots of any differences")
    print()
    print("Of the "+ str(both.shape[0])+" districts:")
    print()
    print(str(len(df[df[0]==0]))+" districts w/ a difference of 0 km^2")
    print(str(len(df[(df[0]<.1) & (df[0]>0)]))+ " districts w/ a difference between 0 and 0.1 km^2")
    print(str(len(df[(df[0]<.5) & (df[0]>=.1)]))+ " districts w/ a difference between 0.1 and 0.5 km^2")
    print(str(len(df[(df[0]<1) & (df[0]>=.5)]))+ " districts w/ a difference between 0.5 and 1 km^2")
    print(str(len(df[(df[0]<2) & (df[0]>=1)]))+ " districts w/ a difference between 1 and 2 km^2")
    print(str(len(df[(df[0]<5) & (df[0]>=2)]))+ " districts w/ a difference between 2 and 5 km^2")
    print(str(len(df[(df[0]>=5)]))+ " districts w/ a difference greater than 5 km^2")

def field_name_length_check(gdf_col_list):
    
    '''Purpose: Check to ensure all fields fit within GIS 10 character limit
    '''
    
    to_change = []
    for col in gdf_col_list:
        if len(col)>10:
            to_change.append(col)
    if to_change == []:
        print('All field names within GIS 10 character limit.')
    else:
        print('Change the following field names:', to_change)

def select_cols(df, prefix):
    
    '''Purpose: enable user to select colums by prefix substring,
    so for instance can grab all president columns using prefix = 'G20PRE' - enables easy
    re-ordering for the final erj file
    '''
    
    list = []
    for col in df:
        if prefix in col:
            list.append(col)
    return list

def format_erj_cols(location_desc_cols, election_columns, geo_col):
    '''Order columns to standardize
    Arguments:
        locatino_desc_cols: UNIQUE_ID, COUNTYFP, any other VEST cols
        election_columns: ex G20PREDBID
        geo_col: geometry
    '''
    
    col_formatted = location_desc_cols + election_columns + geo_col
    return col_formatted

def create_erj_shp(gdf, shp_name):
    
    '''Purpose: create directory (folder) to store ERJ shapefile and create file from gdf.
    In cases where separate election files, run once, then run "gdf.to_file()" 
    separately for each file going to the same directory.
    '''
    
    os.mkdir('./'+shp_name)
    gdf.to_file('./'+shp_name+'/'+shp_name+'.shp')
    print(shp_name, 'shapefile created.')

'''PH additions below
Notes + suggestions from LF:
- Add descriptions of arguments to remaining functions
- LF commented out the code outside of fxns as examples to keep all "active code" in fxns - pls reorganize as you see fit!
- Once edits/additions made can re-organize order fxns appear to group together steps (ex: geo check and id check for district splits together in ordering)
Like I said on the call, additions are a little more tedious now, but will made our documentation extra clear and adaptable for anyone else to use, and easy to show new team members if anyone new joins and needs to be oriented on the project or archived project (if far in the future)
'''

def allocate_absentee(df_receiving_votes,df_allocating,column_list,col_allocating,allocating_to_all_empty_precs=False):
    """Allocates votes proportionally to precincts, usually by share of precinct-reported vote

    Args:
      df_receiving_votes: DataFrame with precinct-level votes
      df_allocating: DataFrame with the votes to allocate
      column_list: List of races that votes are being allocated for
      col_allocating: String referring to what level the allocation occurs at (most often county)
      allocating_to_all_empty_precs: Boolean for special case where all votes in df_receiving_votes are 0

    Returns:
      The precinct-level votes dataframe (df_receiving_votes) with the allocated votes
    """
    
    #Fill any n/a values with 0
    df_receiving_votes = df_receiving_votes.fillna(0)
    #Grab the original columns, so we can filter back down to them later
    original_cols = list(df_receiving_votes.columns)
    
    #Add in the "Total Votes column"
    if (allocating_to_all_empty_precs):
        #In cases where every vote is 0, need to set the Total_Votes equal to 1 for proportional allocation
        df_receiving_votes.loc[:,"Total_Votes"]=1
    else:
        df_receiving_votes.loc[:,"Total_Votes"]=0
        for race in column_list:
            df_receiving_votes.loc[:,"Total_Votes"]+=df_receiving_votes.loc[:,race]
    
    #Create the needed dataframes
    precinct_specific_totals = pd.DataFrame(df_receiving_votes.groupby([col_allocating]).sum())
    precinct_specific_totals.reset_index(drop=False,inplace=True)
    to_dole_out_totals = pd.DataFrame(df_allocating.groupby([col_allocating]).sum())
    to_dole_out_totals.reset_index(drop=False,inplace=True)
    
    #Add in total sum check
    sum_dataframe = pd.DataFrame(columns=precinct_specific_totals.columns)
    for i in column_list:
        total_votes = precinct_specific_totals.loc[:,i].sum()+to_dole_out_totals.loc[:,i].sum()
        sum_dataframe.at[0,i]=total_votes.astype(int)
    
    #Check the allocating to empty precincts code
    if (allocating_to_all_empty_precs):
        for i in column_list:
            if(sum(precinct_specific_totals[i])!=0):
                print("Allocating to all empty precincts parameter incorrect")
                break
    
    #Print out any instances where the allocation, as written, won't work
    special_allocation_needed = []
    for index, row in precinct_specific_totals.iterrows():
        for race in column_list:
            if (row[race]==0):
                race_district = row[col_allocating]
                if race_district in to_dole_out_totals[col_allocating].unique():
                    to_allocate = int(to_dole_out_totals.loc[to_dole_out_totals[col_allocating]==race_district][race])
                    if (to_allocate != 0):
                        special_allocation_needed.append([race_district,race])
                        if(row["Total_Votes"]==0):
                            precinct_specific_totals.loc[index,"Total_Votes"]=1
                            col_val = row[col_allocating]
                            df_receiving_votes.loc[df_receiving_votes[col_allocating]==col_val,"Total_Votes"]=1

    #Create some new columns for each of these races to deal with the allocation
    for race in column_list:
        add_var = race+"_add"
        rem_var = race+"_rem"
        floor_var = race+"_floor"
        df_receiving_votes.loc[:,add_var]=0.0
        df_receiving_votes.loc[:,rem_var]=0.0
        df_receiving_votes.loc[:,floor_var]=0.0

    #Iterate over the rows
    #Note this function iterates over the dataframe two times so the rounded vote totals match the totals to allocate
    for index, row in df_receiving_votes.iterrows():
        if row[col_allocating] in to_dole_out_totals[col_allocating].unique():
            for race in column_list:
                add_var = race+"_add"
                rem_var = race+"_rem"
                floor_var = race+"_floor"
                #Grab the district
                county_id = row[col_allocating]
                if [county_id,race] in special_allocation_needed:
                    #Get the denominator for the allocation - the summed "total votes" for precincts in that grouping
                    denom = precinct_specific_totals.loc[precinct_specific_totals[col_allocating]==county_id]["Total_Votes"]
                    #Get one of the numerators, how many districtwide votes to allocate
                    numer = to_dole_out_totals.loc[to_dole_out_totals[col_allocating]==county_id][race]
                    #Get the "total votes" for this particular precinct
                    val = df_receiving_votes.at[index,"Total_Votes"]
                    #Get the vote share, the precincts % of total precinct votes in the district times votes to allocate
                else:
                    #Get the denominator for the allocation (the precinct vote totals)
                    denom = precinct_specific_totals.loc[precinct_specific_totals[col_allocating]==county_id][race]
                    #Get one of the numerators, how many districtwide votes to allocate
                    numer = to_dole_out_totals.loc[to_dole_out_totals[col_allocating]==county_id][race]
                    #Get the vote totals for this race in this precinct
                    val = df_receiving_votes.at[index,race]
                    #Get the vote share, the precincts % of total precinct votes in the district times votes to allocate
                if ((float(denom)==0)):
                    vote_share = 0
                else:
                    vote_share = (float(val)/float(denom))*float(numer)
                df_receiving_votes.at[index,add_var] = vote_share
                #Take the decimal remainder of the allocation
                df_receiving_votes.at[index,rem_var] = vote_share%1
                #Take the floor of the allocation
                df_receiving_votes.at[index,floor_var] = np.floor(vote_share)

    #After the first pass through, get the sums of the races by district to assist in the rounding            
    first_allocation = pd.DataFrame(df_receiving_votes.groupby([col_allocating]).sum())

    #Now we want to iterate district by district to work on rounding
    county_list = list(to_dole_out_totals[col_allocating].unique()) 

    #Iterate over the district
    for county in county_list:
        for race in column_list:
            add_var = race+"_add"
            rem_var = race+"_rem"
            floor_var = race+"_floor"
            #County how many votes still need to be allocated (because we took the floor of all the initial allocations)
            to_go = int(np.round((int(to_dole_out_totals.loc[to_dole_out_totals[col_allocating]==county][race])-first_allocation.loc[first_allocation.index==county,floor_var])))
            #Grab the n precincts with the highest remainders and round these up, where n is the # of votes that still need to be allocated
            for index in df_receiving_votes.loc[df_receiving_votes[col_allocating]==county][rem_var].nlargest(to_go).index:
                df_receiving_votes.at[index,add_var] = np.ceil(df_receiving_votes.at[index,add_var])

    #Iterate over every race again
    for race in column_list:
        add_var = race+"_add"
        #Round every allocation down to not add fractional votes
        df_receiving_votes.loc[:,add_var]=np.floor(df_receiving_votes.loc[:,add_var])
        df_receiving_votes.loc[:,race]+=df_receiving_votes.loc[:,add_var]
        df_receiving_votes.loc[:,race] = df_receiving_votes.loc[:,race].astype(int)
        #Check to make sure all the votes have been allocated
        if ((sum_dataframe.loc[:,race].sum()-df_receiving_votes.loc[:,race].sum()!=0)):
            print("Some issue in allocating votes for:", i)
            
    #Filter down to original columns
    df_receiving_votes = df_receiving_votes[original_cols]

    return df_receiving_votes

# Note: The below are all used together to deal with the precinct splits
    
def is_split_precinct(district_assignment_list):
    c = Counter([x[0] for x in district_assignment_list])
    greater_than_one = {x:[y[1] for y in district_assignment_list if y[0]==x] for x, count in c.items() if count > 1}
    if len(greater_than_one)==0:
        return 0
    else:
        return greater_than_one


def get_level_dist(column_name):
    zfill_level = 2
    if "Representative in Congress" in column_name:
        level = "CON"
    elif "State Senator" in column_name:
        level = "SU"
    elif "State Representative" in column_name:
        level = "SL"
        zfill_level = 3
    else:
        raise ValueError
    return_val = re.findall("District \S*",column_name) 
    if (len(return_val)!=0):
        dist = return_val[0].split(" ")[1]
        dist = dist.zfill(zfill_level)
    else:
        raise ValueError
    return level,dist


'''**get_level_dist() ex:
district_cols = [i for i in pivoted_2020.columns if "Representative" in i or "State Senator" in i]
precinct_mapping_dict = {}
split_precincts_list = {}
for index,row in pivoted_2020.iterrows():
    precinct_list = []
    for contest in district_cols:
        if(row[contest]!=0):
            precinct_info = get_level_dist(contest)
            if precinct_info not in precinct_list:
                precinct_list.append(get_level_dist(contest))
    is_split = is_split_precinct(precinct_list)
    if (is_split):
        split_precincts_list[row["pct_std"]]=is_split
    precinct_mapping_dict[row["pct_std"]]=precinct_list
    
keep_names = ['pct_std', 'County Code (Three-character abbreviation)', 'County Name','Total Registered Voters']
'''

def get_race(contest):
    if "President" in contest:
        level = "PRE"
    elif ("Representative in Congress" in contest or "State Senator" in contest or "State Representative" in contest):
        contest_info = get_level_dist(contest)
        level = contest_info[0]+contest_info[1]        
    else:
        print(contest)
        raise ValueError
    return level


def get_party(contest):
    if "PARTY:DEM" in contest:
        return "D"
    elif "PARTY:REP" in contest:
        return "R"
    elif "PARTY:LPF" in contest:
        return "L"
    ## Reform -> F
    elif "PARTY:REF" in contest:
        return "O"
    elif "PARTY:PSL" in contest:
        return "S"
    elif "PARTY:GRE" in contest:
        return "G"
    elif "PARTY:CPF" in contest:
        return "C"
    elif "PARTY:WRI" in contest:
        return "O"
    elif "PARTY:NPA" or "PARTY:NOP" in contest:
        return "N"
    else:
        print(contest)
        return ValueError

    
def get_name(contest):
    contest = contest.upper()
    name = contest.split("-")[1]
    likely_last = name.split(" ")[-1]
    if likely_last in ["JR","III","II","SR"]:
        return name.split(" ")[-2][0:3]
    else:
        return likely_last[0:3]
    

for contest in pivoted_2020.columns:
    if contest not in keep_names and "Amendment" not in contest and "Carlos G. Mu" not in contest and "President" not in contest:
        # Add in a condition about the 20
        value = "G"+ get_race(contest)+ get_party(contest)+ get_name(contest)
        contest_name_change_dict[contest] = value
    else:
        print("'"+contest+"':'',")


def return_cong_splits(split_dict):
    for val in split_dict.keys():
        if 'CON' in val:
            return split_dict['CON']
        

def district_splits(cd_list, level, old_name, elections_gdf, shps_gdf, unique_ID_col, district_ID, races_list):
    full_shape = elections_gdf.loc[elections_gdf[unique_ID_col]==old_name]
    for index in range(0,len(cd_list)):
        district = shps_gdf.loc[shps_gdf[district_ID]==cd_list[index]]
        new_prec = gp.overlay(full_shape, district, how='intersection',keep_geom_type=True)
        if(new_prec.empty):
            print("***Issue merging District: ",cd_list[index],"and prec:",old_name,"***")
            print(full_shape)
            ax = full_shape.boundary.plot(figsize=(20,20))
        new_prec = new_prec[list(elections_gdf.columns)]
        for column in new_prec:
            if column in races_list and cd_list[index] not in column:
                new_prec.loc[0:,column] = 0 
        new_prec[unique_ID_col]=old_name+"-("+level+"-"+cd_list[index]+")"
        elections_gdf = elections_gdf.append(new_prec)
        elections_gdf.reset_index(drop=True,inplace=True)        
    #Remove the precinct that was split
    elections_gdf = elections_gdf[elections_gdf[unique_ID_col] != old_name]
    elections_gdf.reset_index(drop=True,inplace=True)
    return elections_gdf


'''Ex:
pivoted_2020.rename(columns=contest_name_change_dict,inplace=True)


df = pd.DataFrame([(v, k) for k, v in contest_name_change_dict.items()], columns=['Candidate', 'Column'])
# Store the data into a csv file
#df.to_csv('./cand_dicts/oh_gen_20_st_prec.csv', sep=',')
        
cong_splits_dict = {i:return_cong_splits(split_precincts_list[i]) for i in split_precincts_list.keys() if return_cong_splits(split_precincts_list[i]) != None }

for val in join_attempt_two["UNIQUE_ID"]:
    cd_list = []
    if val in cong_splits_dict.keys() and val not in allocating_votes_id_list:
        print(val, "=>", cong_splits_dict[val])
        join_attempt_two = district_splits(cong_splits_dict[val],"CON",val, join_attempt_two, fl_cong_shapefile, "pct_std", "CD116FP", state_data_columns)
'''
