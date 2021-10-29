# Python Version 3.7.7
# bs4 Version 4.9.1
# csv Version 1.0

from bs4 import BeautifulSoup
from RowObject import RowObject #My own class
import csv
import os

# Global Variables 
depth = 0 # Stores highest indent-#, which will help determine the total # columns
level_names = []
level_text = []
global_list_row_obj = None # Only used for descendant-text

# Change base_path to match path to the folder holding the html file
base_path = '/Users/Ruairi/Documents/Fall 2021/Codifying Illinois Law'
path_law_book_html = os.path.join(base_path, 'wholebook_2020.html')

# Part 1: Read in html and construct a list of html rows we care about
# [3 functions to update global vars, read in data, and identify important tags]
def read_in_data(filename):
    """
    Input: Filepath for html
    Output: Soup object of parsed html
    Description: Function to read in data and output parsed soup object
    """
    with open(filename, 'r', encoding='utf-8') as f:
        contents = f.read()
    return BeautifulSoup(contents, "xml")

def indent_depth(html_rows):
    """
    Input: List of relevant html rows
    Output: None. Updates global variables
    Description: Function that reads through all relevant html rows and determines how many columns
    are required for the csv output (depth). 
    This updates the global variables (here and in RowObject.py)
    """
    all_classes = [row.attrs.get('class') for row in html_rows]
    indent_levels = [class_name.replace("INDENT-", '') for class_name in list(set(all_classes)) if class_name.startswith("INDENT")]
    reduced_indent_levels = [indent for indent in indent_levels if len(indent) <=2 and indent.isnumeric()]
    global depth
    depth = int(sorted(reduced_indent_levels)[-1])
    global level_names
    level_names = ["Level-" + str(num+1) for num in range(depth)]
    global level_text
    level_text = ["Level-" + str(num+1) + "-text" for num in range(depth)]
    # Need to add depth to RowObject.py class global var
    temp = RowObject("Temp","Indent-X") 
    temp.depth= depth
    
def tags_of_interest(filename=path_law_book_html, year=2020):
    """
    Input: Law book year (default 2020), html file (default path_law_book_html)
    Output: Cleaned list of html rows for all rows of interest
    Description:
    1) Uses the read_in_data function to make a list of all relevant
    html tags (still using HTML tags, nothing is RowObject yet).
    2) Makes some hard code corrections to the 'class' label for obvious errors
    I found. I've left space for future users to follow that format and change
    any obvious errors in the html 'class' tag
    3) Finally, deals with 5 cases to extract essentially all relevant html rows
    that will be RowObject-ified
    """
    #STEP 1: Read in Data and Find All p-tags (what we care about)
    soup = read_in_data(filename) 
    p_tags = soup.find_all('p') #Hardcode (maybe)
    indent_depth(p_tags) #Sets global variables to adjust table depth
    
    #STEP 2: Hardcode fixes for some errors in class labeling (indentation)
    if(year == 2020):
        for item in p_tags:
            if("Those arrests or charges that resulted in orders of supervision for a misdemeanor violation of subsection (a) of Section 11-503 of the Illinois Vehicle Code" in item.getText()):
                item['class'] = "INDENT-5"
            elif ("Dated (insert the date of publication)" in item.getText() and item['class'] == "INDENT-0"):
                item['class'] = "INDENT-1"
            elif(item['class'] == "INDENT-0-bot"):
                 item['class'] = "INDENT-1"
            elif("5 grams or more but less than 15 grams of any substance listed in paragraph" in item.getText()):
                item['class'] = "INDENT-3"
            elif("Aggravated violation of paragraph" in item.getText()): 
                item['class'] = "INDENT-2"
            elif("aggravated home repair fraud" in item.getText() and ('(e)' in item.getText() or '(f)' in item.getText())):
                item['class'] = "INDENT-2"
            elif(item['class'] == "INDENT-0"):
                item['class'] = "INDENT-2"

    else:
        #Insert hardcode to fix indentation (class) tag errors for future years
        pass

    #STEP 3: Re-Loop through to Filter out essential tags
    """
    Cases: SECMAIN, History, Indent, Source, and IMG
    These 5 classes house almost all important info
    This may change in different years
    There's a few indent's we don't need I found manually(tempForbidden)
    And History tags are a little weird
    """
    tempForbidden = ["INDENT-1-ALIGN-RIGHT", "INDENT-1c", "INDENT-c",
                     "INDENT_S", "INDENT-2-top"] # Excluded these rare classes
    importantHtmlRows = [] ## Holds important rows in html format -- will turn into rowObjects 
    for i in range(0, len(p_tags)):
        currentClass = p_tags[i].attrs.get('class')
        if(currentClass == "SECMAIN"):
            if("ILCS" in p_tags[i].getText() or "Rule" in p_tags[i].getText()):
                importantHtmlRows.append(p_tags[i])
        elif(p_tags[i-1].attrs.get('class') == "HISTORY"): #HTML History tags are weird
            p_tags[i]['class'] = "HISTORY"
            importantHtmlRows.append(p_tags[i])
        elif(currentClass.startswith("INDENT") or currentClass == "SOURCE"):
            if(currentClass not in tempForbidden): # Excludes weird exceptions (5 or 6 rows)
                importantHtmlRows.append(p_tags[i])
        elif(currentClass.startswith("IMG")):
            p_tags[i].string = "Image" #Images get the text "Image"
            p_tags[i]['class'] = importantHtmlRows[-1].attrs.get('class') #And are given the same indentation level as the previous html row
            importantHtmlRows.append(p_tags[i])

    return importantHtmlRows  

# Part 2: Turn HTML rows into RowObjects
# [4 helper functions; rowobjectify is main function]

def identify_text_body(text):
    """
    Input: Text
    Output: Integer of where the text body starts
    Description: Identifies using stat patterns of text like '(7)' or '7.'
    Ex. “(7) The law…” would return 4
    """
    if(text.startswith('(') and ')' in text[:6]): 
        start = text[:6].find(')') + 1 
    elif(text[0].isnumeric() and '.' in text[:5]):
        start = text[:5].find('.') + 1
    else:
        start = 0
    return start

def parent_child_relationship(parent, child):
    """
    Input: Two RowObjects, one parent and one child
    Description: Does the assignment and inheritance using built 
    """
    parent.set_child(child)
    child.set_parent(parent)
    child.inherit_parent_attributes()

def check_in_text_numeral(currRowObj):
    """
    Input: Row to check if it contains valid in-text subsection of the type (i), (1), or (A)
    Output: "Roman", "Numeric", "Alphabet", or None
    
    Helper function for row_objectify that will check the text of each row 
    """
    text = currRowObj.get_text()
    #hardcoded
    possible = {"Roman": ['(i)', '(ii)', '(iii)'], 
                "Numeric": ['(1)', '(2)', '(3)'], 
                "Alphabet": ['(A)', '(B)', '(C)']}
    final = {}
    for key, value in possible.items():
        breaks_of_interest = value
        text_body_start = identify_text_body(text)
        text_body = text[text_body_start:] #2 or 3??
        first_sub = text_body.find(breaks_of_interest[0]) + text_body_start
        second_sub = text_body.find(breaks_of_interest[1]) + text_body_start
        third_sub = text_body.find(breaks_of_interest[2]) + text_body_start
        result = True
        
        if(breaks_of_interest[0] not in text_body): # Must have (i) or (1) or (A)
            result = False
        elif(breaks_of_interest[1] not in text_body):# Must have (ii) or (2) or (B)
            result = False
        elif(second_sub != (-1+text_body_start) and second_sub < first_sub): # Note: I add 2 earlier so if the numeral isn't in the text, the index is 1 not -1
            result = False
        elif(third_sub != (-1+text_body_start) and third_sub < first_sub):
            result = False
        elif(')' in text[first_sub-3:first_sub] and first_sub > text_body_start+2):
            result = False
        elif('(' in text[first_sub+3:first_sub+6]):
            result = False
        elif((second_sub - first_sub) < 10 and ('and' in text[first_sub+3:second_sub] or 'or' in text[first_sub+3:second_sub])):
            result = False
        elif( '(' in text[first_sub+3:first_sub+10] and ('and' in text[first_sub+3:first_sub+10] or 'or' in text[first_sub+3:first_sub+10]) ):
            result = False
        elif('paragraph' in text[first_sub-10] or 'paragraph' in text[second_sub-10]):
            result = False
        final[key] = result
        
    check_result = None
    for key, value in final.items():
        if value:
            check_result = key
    return check_result

def parse_in_text_numerals(currRowObj, subsection_type = "Roman"):
    """
    Input: RowObject identified as having within-text numeral subsections (i),(1), or (A) -- (default to roman numerals)
    Output: List of multiple RowObjects that for each subsection within text
    Description: Takes a row object and the type of subsection that is identified within the 
    text and returns a list of RowObjects, one for each subsection (with parent/child relationships correctly defined)
    """
    text = currRowObj.get_text()
    # Start by finding the type of subsections in the original text 
    if(subsection_type == "Roman"):
        numerals = ['(i)', '(ii)', '(iii)', '(iv)', '(v)', '(vi)','(vii)', '(viii)', '(ix)', '(x)'] #hardcoded
    elif(subsection_type == "Numeric"):
        numerals = ['(1)', '(2)', '(3)', '(4)', '(5)', '(6)', '(7)', '(8)',
                    '(9)', '(10)', '(11)', '(12)', '(13)', '(14)', '(15)', 
                    '(16)', '(17)', '(18)', '(19)', '(20)'] #hardcoded (longest text I found had 17 subsections)
    elif(subsection_type == "Alphabet"):
        numerals = ['(A)', '(B)', '(C)', '(D)', '(E)', '(F)', '(G)', '(H)',
                    '(I)', '(J)', '(K)', '(L)', '(M)', '(N)', '(O)', '(P)'] #hardcoded
    numerals_within_text = [numeral for numeral in numerals if numeral in text[3:]]
    
    list_new_subsection_rows = []
    for i in range(len(numerals_within_text)):
        start_ind = text[3:].find(numerals_within_text[i]) + 3 #Find it in text body (after initial parentheses), and reindex for entire text
        if(i < len(numerals_within_text)-1):
            end_ind = text[3:].find(numerals_within_text[i+1]) + 3 
            list_new_subsection_rows.append(RowObject(text[start_ind:end_ind], "INDENT" + '-' + str(currRowObj.get_level()+1)))
        elif(i == len(numerals_within_text)-1):
            list_new_subsection_rows.append(RowObject(text[start_ind:], "INDENT" + '-' + str(currRowObj.get_level()+1)))
    for rowobj in list_new_subsection_rows:
        parent_child_relationship(currRowObj, rowobj)
    currRowObj.set_in_text_numeral(subsection_type) 
    return list_new_subsection_rows 

def row_objectify(list_html_objects):
    """
    Input: List of HTML rows
    Output: List of RowObjects structured by family
    Description: The meat of the process. Turns html rows into RowObjects based on numerous conditions.
    """
    global global_list_row_obj
    listRowObjects = []
    for i in range(len(list_html_objects)):
        currRowObj = RowObject(list_html_objects[i].getText(), list_html_objects[i].attrs.get('class'))
        if(i != 0 and currRowObj.get_level() != 0): ##For all rows that are not SECMAIN
            j = len(listRowObjects)-1
            #CASE 1: Deals with the case where a row does not start with an identifiable subsection '(#)' by merging it with the previous row 
            if(listRowObjects[j].get_level() != 0 and currRowObj.get_level() < 10 and not ((currRowObj.get_text().startswith("(") and currRowObj.get_text()[:6].find(')') != -1) or (currRowObj.get_text()[0].isnumeric() and currRowObj.get_text()[:5].find('.') != -1))):
                listRowObjects[j].merge_text(currRowObj)
                continue
            
            #CASE 2: Deals with the case of source tags, will not append to listRowObjects
            elif(currRowObj.get_level() == 10): #Case of source tags, will not append to listRowObjects
                k = len(listRowObjects) - 1 
                currSource = currRowObj.get_text().replace('§', '?').replace(u'\u2002', ' ').replace('§', '?') #Changes weird chars in source
                while(listRowObjects[k].get_level() > 0): ##This while-loop identifies the parent of the current row and sets the relationship.
                    listRowObjects[k].set_source(currSource)
                    k -=1
                listRowObjects[k].set_source(currSource)
                continue
            
            #CASE 3: Deals with the case of history tags, will not append to listRowObjects
            elif(currRowObj.get_level() == 11): 
                currHistory = currRowObj.get_text()
                m = len(listRowObjects) - 1
                while(listRowObjects[m].get_level() > 0):
                    listRowObjects[m].set_history(currHistory)
                    m -= 1
                listRowObjects[m].set_history(currHistory)
                continue
            
            #CASE 4: Deals with the case where the html line splits (Ex. 7. \n 5)
            elif(currRowObj.get_text()[0:4].find(')') != -1 and not currRowObj.get_text().startswith('(') and listRowObjects[-1].get_text()[-5:].find('(') != -1):
                start_index = listRowObjects[-1].get_text()[-5:].index('(')
                new_text = listRowObjects[-1].get_text()[-5:][start_index:] + currRowObj.get_text()
                currRowObj.set_text(new_text)
                #Find it's next sibling above
                par_index=1
                while(not listRowObjects[-par_index].get_text()[:2] == currRowObj.get_text()[:2]):
                    par_index+=1                
                #Give it the same attributes as sibling
                currRowObj.classAttr = listRowObjects[-par_index].classAttr
                parent_child_relationship(listRowObjects[-par_index].get_parent(), currRowObj)
                listRowObjects.append(currRowObj)
                continue

            #CASE 5: Deals with the case of in-text subsections (roman numerals, numbers, capital letters)
            elif(check_in_text_numeral(currRowObj)):
                l=-1
                while(listRowObjects[l].get_level() >= currRowObj.get_level()):
                    l-=1
                parent_child_relationship(listRowObjects[l], currRowObj)
                
                subsection_type = check_in_text_numeral(currRowObj)
                split_rows = parse_in_text_numerals(currRowObj, subsection_type)
                
                listRowObjects.append(currRowObj)
                for row in split_rows:                    
                    listRowObjects.append(row)
                continue 
            
            # CASE 6: Deals with two-parentheses cases  
            # [if a row starts like '(1)(A)' it creates 2 rows, (1) and (A)]
            elif(currRowObj.get_text()[:11].count('(') >= 2):
                #These are exceptions we can skip
                #hardcode
                restricted_values = ["blank", "Blank", "reserved", "n-(", "n-[1(", "spa ((", "(+ or", "1-(et",
                                     "3-(", "2-(", " (6a", "(n-[1-", "20-2 (", "20-1("] 
                restricted_check = ['1' if val in currRowObj.get_text()[:12].lower() else '0' for val in restricted_values]
                
                par_index=-1
                while(listRowObjects[par_index].get_level() >= currRowObj.get_level()):
                    par_index-=1
                parent_child_relationship(listRowObjects[par_index], currRowObj)
                
                if('1' not in restricted_check):
                    second_start = currRowObj.get_text()[1:12].index('(') + 1
                    #This captures all 2-parentheses openings, including any like '(8)(a) (Blank)'
                    if(currRowObj.get_text()[:15].count('(') == 2 or '(Blank)' in currRowObj.get_text()[0:15]):
                        second_row = RowObject(currRowObj.get_text()[second_start:], "INDENT" + '-' + str(currRowObj.get_level()+1))
                        #Gives the new row a proper ancestry
                        
                        parent_child_relationship(currRowObj, second_row)
                        
                        #Remove the second row's text from the original row 
                        currRowObj.set_text(currRowObj.get_text()[:second_start])
                        #Add the two rows to the master list of RowObjects
                        listRowObjects.append(currRowObj)
                        listRowObjects.append(second_row)
                        continue
                    elif(currRowObj.get_text()[:15].count('(') == 3):
                        #Captures the rare 3-parentheses (a)(1)(A)
                        third_start = currRowObj.get_text()[second_start+1:].index('(') + second_start+1
                        #Initialize second row
                        second_row = RowObject(currRowObj.get_text()[second_start:third_start], "INDENT" + '-' + str(currRowObj.get_level()+1))
                        parent_child_relationship(currRowObj, second_row)
                        
                        #Initialize third row
                        third_row = RowObject(currRowObj.get_text()[third_start:], "INDENT" + '-' + str(currRowObj.get_level()+1))                        
                        parent_child_relationship(second_row, third_row)                        

                        #Strip out unneccesary text from currRowObject
                        currRowObj.set_text(currRowObj.get_text()[:second_start])
                        #Append all three RowObjects to the master list
                        listRowObjects.append(currRowObj)
                        listRowObjects.append(second_row) 
                        listRowObjects.append(third_row)
                        continue
            else:        
                parent_index=-1
                while(listRowObjects[parent_index].get_level() >= currRowObj.get_level()): 
                    parent_index-=1    
                parent_child_relationship(listRowObjects[parent_index], currRowObj)
                
        #CASE 7: Deals with SECMAIN rows -- strips out class,act,section, and title    
        elif(currRowObj.get_level() == 0): 
            currRowObj.parse_secmain_text()
            
        #Append new RowObject to a master list
        listRowObjects.append(currRowObj)   
    
    global_list_row_obj = listRowObjects
    return listRowObjects

# Part 3: Use the master list of RowObjects to construct a CSV 

def RowObject_2_csv_row(row):
    """
    Input: A RowObject
    Output: A dictionary with keys that are row headers and values pulled 
    from the inputted row that will fill in the CSV row
    Description: A helper function that helps the iterative loop below it by 
    stripping the relevant information from the RowObject and putting it into 
    a dictionary that is then used to write a new csv
    """   
    #I pull these down because earlier in this code I strip the html for useful information to fill in the new csv
    global depth
    global level_names
    global level_text
    global global_list_row_obj
    
    ancestry_list = [None]*depth #Will be filled with RowObjects and Nones
    level = row.get_level()-1
    ancestry_list[level] = row
    while(level > 0):
        ancestry_list[level-1] = ancestry_list[level].get_parent()
        level -= 1   
            
    names = [None if not row else row.get_level_name() for row in ancestry_list]
    this_level_text = [row.get_text() if row else "" for row in ancestry_list]
    headers = ["Chapter", "Act", "Section", "Title", "Rule"] + level_names + ["Text", "History", "Source", "Ancestral-Text", "Descendant-Text"] + level_text + ["Hyphen_Statute_Code"]
    
    if(row.get_level() > 0): #Non-secmain rows
        #New: Next 4 lines of code are a fix for the clerk's data where we needed hyphenated statute codes
        hyphen_statute_code = str(row.get_chapter()) + " ILCS " + str(row.get_act()) + '/' + str(row.get_section())
        for name in names:
            if(name):
                hyphen_statute_code += '-' + str(name)
        values = [row.get_chapter(), row.get_act(),  row.get_section(), row.get_title().replace('“', '').replace('”',''), row.get_rule()] + [name for name in names] + [row.get_text().replace("’", "'").replace('“', '"'), row.get_history(), row.get_source(), row.get_ancestral_text(), row.get_descendant_text(global_list_row_obj)] + this_level_text + [hyphen_statute_code]
    elif(row.get_level() == 0): #Secmain rows
        values = [row.get_chapter(), row.get_act(),  row.get_section(), row.get_title().replace('“', '').replace('”',''), row.get_rule()] + [None]*(depth+2) + [row.get_source(), None, row.get_descendant_text(global_list_row_obj)] 
    return dict(zip(headers, values))
 
## Writes the final csv by initializing columns (as fieldnames) and running each of our
## relevant row objects through RowObject2csvRow to get them in the proper format
with open('CodifiedTable.csv', 'w', newline='') as csvfile:
    html_tags = tags_of_interest()
    listRowObjects = row_objectify(html_tags)
    fieldnames = ["Index", "Chapter", "Act", "Section", "Title", "Rule"] + level_names + ["Text", "History", "Source", "Ancestral-Text", "Descendant-Text"] + level_text + ["Hyphen_Statute_Code"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    b = {'Index': 1} #Used for indexing the csv
    for row in listRowObjects:
        if(row.get_level() < 10): #We're including SECMAIN rows as blank text (still skip source and history)
            data = {**b, **RowObject_2_csv_row(row)}
            writer.writerow(data)
            b["Index"] += 1

