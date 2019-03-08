# Code developed by Marco Velliscig (marco.velliscig AT gmail.com)
# for the dutch Red Cross
# released under GNU GENERAL PUBLIC LICENSE Version 3

import numpy as np
import pandas as pd
from os import listdir
from os.path import isfile, join
import difflib
import re


###################################################
# SPECIFY FILES TO PCODE + COLUMNS + ADMIN-LEVELS #
###################################################

#assuming you have different files to pcode
if_to_pcode = {'file1' : True,
               'file2' : False,}

#input names
dict_filename_to_pcode= {'file1'  : 'MeaslesReport_Feb282019 (1).csv',
                         'file2'    : 'Glenda-Hagupit---Dec-1-12-2014---TAB-C---DAMAGED-HOUSES.csv',
}
#output names
dict_pcoded_sav_name={'file1'  : 'measles-test.csv',
                      'file2'    : 'Glenda-output.csv',
}

#specify 1, 2 or 3 levels in the files to be pcoded (Note that L1, L2, L3 should correspond with admin-levels as specified for admin-file just below here)
level_tag = ['L1','L2'] #['L1','L2','L3']

#name columns in input file with corresponding admin level
dict_col_names_to_pcode={'file1'  :  {'REGION/PROVINCE/CITY': 'L1_name',
					},
                         'file2'    :  {'Province': 'L1_name',
                                        'Municipality': 'L2_name'
                                        },
}


#######################################################
# SPECIFY TEMPLATE (ONLY CHANGE FOR DIFFERENT COUNTRY #
#######################################################

#specify namefile of pcode template 
filename_template='pcode_template_philippines_new.csv'

#specify which columns names correspond to (for template) >> Change the left column, not L1_code, L1_name, etc.
dict_raw_template  = {'Pcode2_province':     'L1_code',
                      'Name2_province':      'L1_name', 
                      'Pcode3_municipality': 'L2_code',
                      'Name3_municipality':  'L2_name',
                      'Pcode4_barangay':     'L3_code',
                      'Name4_barangay':      'L3_name'}


##################################
# SPECIFY INTERACTION PARAMETERS #
##################################

#specify the threshold score below which an imput from the user is requested
ask_below_score =  {'L1':0.9, 'L2':0.9, 'L3':0.8}
# if the score is below the reject level it is considered not found 
reject_below_score= {'L1':0.9, 'L2':0.9, 'L3':0.55}

              

########################
# RUN PCODER ALGORITHM #
########################
                        
def pcode_file(filename_template ,  dict_raw_template , filename ,sav_name,  dict_raw , ask_below_score , reject_below_score, level_tag ,sheet_excel_name = 0, known_matches={}, name_tricks = True) :


        df_raw_template = pd.read_csv('templates/'+filename_template,delimiter=';')

        df_template = df_raw_template[dict_raw_template.keys()]
        df_template.columns = dict_raw_template.values()
        df_template = df_template.drop_duplicates()
        #########################################################################

        
        print filename.split(".")[-1]

        df_raw = read_file_in_df(filename)
        print 'columns in df_raw' , df_raw.columns
        # make the df_raw uppercase for merging pourposes 
        # see the end of the code
        for i in range(len(dict_raw)) : df_raw[dict_raw.keys()[i]]=df_raw[dict_raw.keys()[i]].str.upper()

        #rename columns
        df = df_raw[dict_raw.keys()]
        df.columns = dict_raw.values()
        df = df.drop_duplicates()

        #########################################################################
        name_per_tag = ['_name', '_code']

        #keep from the template only the relevant admin levels
        columns_template = [x + y for x in level_tag for y in name_per_tag ]
        df_template = df_template[columns_template]
        df_template = df_template.drop_duplicates()



        for admin_level in level_tag: 
                df_template[admin_level+'_name']=df_template[admin_level+'_name'].str.upper()
                df[admin_level+'_name']=df[admin_level+'_name'].str.upper()
                #df[admin_level+'_code'] = np.NaN 
                df[admin_level+'_best_match_name'] = np.NaN 

        level_tag_name = [ ] 
        for tag in level_tag : level_tag_name.append(tag+'_name') 


        #### a simple join is tried first for exact matches

        df = pd.merge(df , df_template , on = level_tag_name   , how = 'left')

        ### 
        #forward and backward pass
        df = match_against_template(df , df_template, level_tag,ask_below_score, reject_below_score, reverse = False)
        df = match_against_template(df , df_template, level_tag,ask_below_score, reject_below_score, reverse = True)



        # saving the known matches so they can be loaded and modified
        # later version the known matches file can be specified in the options
        # warm_start

        df_known_matches = pd.DataFrame.from_dict(known_matches, orient='index')
        #df_known_matches.reset_index()
        #df_known_matches.columns = [ 'name_raw' , 'name_match' ] 
        #name_km_sav = 'known_matches_' + sav_name
        #df_known_matches.to_csv(name_km_sav,encoding='utf-8' )
        #df_dummy = pd.read_csv(name_km_sav,encoding='utf-8')


        #merge it back to the original file
        df_pcoded = pd.merge(df_raw, df, 
                             left_on =dict_raw.keys(), 
                             right_on=dict_raw.values(), 
                             how = 'inner')
        df_pcoded.to_csv('files_output/'+sav_name)#,encoding='windows-1251')

        print ' list of no matches' , sum(df[level_tag[-1]+'_code'].isnull())
        print ' list of matches ' , sum(df[level_tag[-1]+'_code'].notnull())

def construct_known_match_tag(name , upper_level):
        """ Function that creates a tag with the name and the previus level
        to be added to the list of known matches
        """
        if (not isinstance(name, basestring)) | ( not isinstance(upper_level, basestring)) : print name , upper_level
        return str(name) + ' ' + upper_level

def find_best_match_user_input( poss_matches , 
                                name_to_match,  
                                upper_level , 
                                score_threshold, 
                                reject_threshold, 
                                known_matches , 
                                use_tricks=False):
        """ record linkage function that selects from a list of candidates name
        the best match for a given name applying string metrics 
        a list of known matches is also passed
        thresholds can be specified
        """
        
        known_match_tag = construct_known_match_tag(name_to_match , upper_level)
        #try first if the target is in the known matches dictionary
        try :
                best_match = known_matches[known_match_tag]
        except:
                if use_tricks :
                    #trim the strings from words like city and capital that can reduce 
                    # the accuarcy of the match
                    poss_matches_trim = [poss_matches[i].replace('CITY','').replace('OF','').replace('POB.','').strip() for i in range(len(poss_matches))]
                    for i in range(len(poss_matches_trim)):
                        if len(poss_matches_trim[i]) > 9 :
                            if poss_matches_trim[i][-9] == 'POBLACION':
                                poss_matches_trim[i] = poss_matches_trim[i].replace('POBLACION','').strip()								
                    regex = re.compile(".*?\((.*?)\)")
                    poss_matches_trim = [re.sub("[\(\[].*?[\)\]]", "", poss_matches_trim[i]) for i in range(len(poss_matches))]
                    poss_matches_trim = [poss_matches_trim[i].strip() for i in range(len(poss_matches))]
                    name_to_match_trim = name_to_match.replace('CITY','').replace('OF','').strip()
                    if len(name_to_match_trim) > 9 :
                        if name_to_match_trim[-9:] == 'POBLACION':
                            name_to_match_trim = name_to_match_trim.replace('POBLACION','').strip()
                    name_to_match_trim = re.sub("[\(\[].*?[\)\]]", "", name_to_match_trim)
                    name_to_match_trim =      name_to_match_trim.strip()               

                else:
                    poss_matches_trim = poss_matches
                    name_to_match_trim= name_to_match

                ratio = [(difflib.SequenceMatcher(None,poss_matches_trim[i], name_to_match_trim)).ratio() \
                         for i in range(len(poss_matches))]
                #vector containing all possibilities with their score
                vec_poss = np.array(zip(poss_matches, ratio))
                vec_poss_sorted = np.array(sorted(vec_poss ,key=lambda x: x[1], reverse=True))
                try: 
                        most_prob_name_match = vec_poss_sorted[0,0]

                except:
                        print 'error'
                        print 'name to match ', name_to_match
                        print 'poss matches' , poss_matches
                        most_prob_name_match  = 'error'
                        return most_prob_name_match

                best_ratio = vec_poss_sorted[0,1]

                if float(best_ratio) <= reject_threshold:
                        most_prob_name_match  = 'Not found'
                        
                elif (float(best_ratio) > reject_threshold) & \
                     (float(best_ratio) < score_threshold): 
                    #ask if the possible match is right
                        print 'is ' , most_prob_name_match , 'the right match for ' , name_to_match , '(score:',best_ratio , ')'
                        respond = raw_input('press return for yes, everything else for no : ')

                        if respond != '' : 
                                sorted_prob_name_match =vec_poss_sorted[:,0]
                                sorted_prob_name_match_numbered = np.array(zip(sorted_prob_name_match, range(len(sorted_prob_name_match))))
                                print '\n select from the best match for ' ,name_to_match ,' from this list: \n',  sorted_prob_name_match_numbered

                                while True : 
                                        selected_index = raw_input('select the right choice by number, press return for not found : ')
                                        if selected_index == '' :
                                                most_prob_name_match  = 'Not found'
                                                break

                                        elif selected_index.isdigit():
                                                most_prob_name_match = sorted_prob_name_match_numbered[int(selected_index),0]
                                                break
                                        else:
                                                continue
                #update the known matched dictionary
                known_matches[known_match_tag] = most_prob_name_match 
                print '==' , most_prob_name_match , 'is the right match for ' , name_to_match , best_ratio , '\n'
                best_match=most_prob_name_match

        return best_match 


def match_against_template(df , df_template, level_tag ,ask_below_score, reject_below_score,exception = [] , reverse = False, verbose = False, name_tricks=True):
        
        

        # the code usually does the matching from the shallower to the deeper level
        # but it can also go the other way around even if it is less efficient this way
        # if you combine the 2 approaches you should account for most cases
        known_matches={}
        counter =0
        n_perfect_matches =0 
        n_no_matches =0 
        if reverse : 
                level_tag_use = list(reversed(level_tag))
        else:
                level_tag_use = level_tag 
        # do the search only for those line where the deepest 
        # admin level is null
        for index in  df.loc[df[level_tag[-1]+'_code'].isnull()].index :

                df_template_matches = df_template
                upper_level = ''
                for admin_level in level_tag_use :
                        if verbose : 
                                print 'len template dataframe level', admin_level\
                                        , len(df_template_matches)
                                print df_template_matches.describe()
                        
                        #gets the name of the admin level for the index entry
                        name_admin_level = df.loc[index][admin_level+'_name']
                        if name_admin_level in  exception : continue
                        # it tries to get a perfect match straight away
                        # !!!! this is not needed if a match is made by merge first
                        
                        n_matches_current_level = sum(df_template_matches[admin_level+'_name']==
                                              name_admin_level)
                        if verbose : print 'num matches', admin_level ,  n_matches_current_level
                


                        if (n_matches_current_level) > 0 :
                                if verbose : print ''

                        elif (n_matches_current_level) == 0 :
                                print "perc completed " , ((float(counter)/len(df.index))*100),'\n'
                                poss_matches = (df_template_matches[admin_level+'_name'].drop_duplicates()).values
                                score_threshold=ask_below_score[admin_level]     
                                reject_threshold=reject_below_score[admin_level]       

                                best_match  = find_best_match_user_input( poss_matches , name_admin_level,  upper_level , score_threshold, reject_threshold, known_matches, use_tricks = name_tricks) 
                                if best_match == 'Not found' :  
                                       n_no_matches +=1 
                                       #print '************* Not found, doing full search **********'
                                       print df.loc[index]
                                       #add here the full search instead 
                                       
                                       #break 
                                elif best_match == 'error' :         
                                       n_no_matches +=1 
                                       print '************* error admin ' , admin_level , name_admin_level
                                       print df.loc[index]

                                       break
                                #print 'admin ' , admin_level , name_admin_level ,  'bestmatch ' , best_match , score_m , 'edit dist' , edit_distance(best_match , name_admin_level), '\n'
                                name_admin_level = best_match
                                n_matches_current_level = sum(df_template_matches[admin_level+'_name']==
                                                      name_admin_level)

                        df_template_matches = df_template_matches.loc[
                                df_template_matches[admin_level+'_name']==name_admin_level]

                        if (n_matches_current_level) == 0 & (admin_level== level_tag[-1]):
                                n_no_matches +=1 
                        if n_matches_current_level == 1 :

                                n_perfect_matches +=1
                                if verbose : print df_template_matches
                                for admin_level_tag in level_tag: 

                                        df.loc[index,admin_level_tag+'_code']=(df_template_matches[admin_level_tag+'_code'].values[0])
                                        df.loc[index,admin_level_tag+'_best_match_name']=(df_template_matches[admin_level_tag+'_name'].values[0])
                        upper_level += admin_level + df.loc[index][admin_level+'_name']
                        #add dictionary with known matches
                counter+=1

        return df


#def infer_separator(filename):

def read_file_in_df(filename):
    #read the file to pcode
    if filename.split(".")[-1] == 'csv' :
        
        df = pd.read_csv('files_input/'+filename,  delimiter=';')
        print 'number of columns' , len(df.columns) 
        if len(df.columns) == 1 :
             df = pd.read_csv('files_input/'+filename)

        
    elif filename.split(".")[-1] == 'xlsx' :
        df = pd.read_excel('files_input/'+filename, sheetname=0)
    return df

#the list of files are the keys in the dict of files to load
list_files = dict_filename_to_pcode.keys()
index = 0
for file_type in list_files :
    if if_to_pcode[file_type]:
        print 'pcoding ' , dict_filename_to_pcode[file_type]
        print dict_col_names_to_pcode[file_type]
        pcode_file(filename_template ,  
                dict_raw_template, 
                dict_filename_to_pcode[file_type] , 
                dict_pcoded_sav_name[file_type],  
                dict_col_names_to_pcode[file_type] , 
                ask_below_score , 
                reject_below_score, 
                level_tag 
                )

        
        



