
"""
These objects will contain the information about each row of html including:
1. html class attribute: Obtained directly from the html (ex. SECMAIN,
INDENT-1, SOURCE, etc.) which we re-designated a numeric level so we can
keep track of the indentations in the law book.
2. Text: Legal text for a given row
3. Direct parent and children: Which creates a tree structure so we can
keep track of the order and lineage of the rows of law
4. Chapter, Act, Section, and Title of each row object: which they will inherit
from their highest "ancestor" (their section heading in the law book)
5. Source: Inhereted from "youngest ancestor" since it appears at the end of
each section
"""
class RowObject:   
    def __init__(self, text, classAttr):
        self.text = text
        self.classAttr = classAttr
        self.parent = None 
        self.children = []
        self.chapter = None
        self.act = None
        self.section = ""
        self.title = ""
        self.source = ""
        self.rule = ""
        self.history = ""
        self.ancestral_text = ""
        self.descendant_text = ""
        self.ancestry_list = [None]
        self.level_name = None
        self.in_text_numeral = False
 
## Getters and Setters
    def get_text(self):
        return self.text

    def get_class(self):
        return self.level

    def get_level(self):
        if(self.classAttr.startswith("INDENT")):
            return int(self.classAttr[-1]) #Integer
        elif(self.classAttr == "SECMAIN"):
            return 0  #Hardcode
        elif(self.classAttr == "SOURCE"):
            return 10 #Hardcode
        elif(self.classAttr == "HISTORY"):
            return 11 #Hardcode
    
    def get_parent(self):
        return self.parent
    
    def get_children(self):
        return self.children

    def get_chapter(self):
        return self.chapter

    def get_act(self):
        return self.act

    def get_section(self):
        return self.section
    
    def get_title(self):
        return self.title
    
    def get_source(self):
        return self.source

    def get_rule(self):
        return self.rule

    def get_history(self):
        return self.history
    
    def get_ancestral_text(self):
        self.gen_ancestral_text()
        return self.ancestral_text
    
    def get_descendant_text(self, global_list_row_obj):
        self.gen_descendant_text(global_list_row_obj)
        return self.descendant_text
    
    def get_in_text_numeral(self):
        return self.in_text_numeral
    
    # def get_two_parentheses(self):
    #     return self.two_parentheses
    
    def get_level_name(self):
        self.gen_level_names()
        return self.level_name
    
    def set_child(self, newChild):
        self.children.append(newChild)

    def set_parent(self, parent):
        self.parent = parent

    def set_chapter(self, ch):
        self.chapter = ch

    def set_act(self, act):
        self.act = act

    def set_section(self, section):
        self.section = section

    def set_title(self, title):
        self.title = title

    def set_source(self, source):
        self.source = source

    def set_rule(self, rule):
        self.rule = rule

    def set_history(self, history):
        self.history = history
        
    def set_text(self, text):
        self.text = text
        
    def set_new_level(self, level):
        self.classAttr = "INDENT" + str(level)
        
    def set_in_text_numeral(self, check_result):
        self.in_text_numeral = check_result
 
##  Generate functions that help getters by executing some process and then set an object variable
    def gen_ancestral_text(self):
        # First line makes sure ancestral text is blank for SECMAIN rows 
        # and starts one level above for children of in-text numeral rows
        full_text = self.text if self.get_level() > 0 and not self.get_parent().get_in_text_numeral() else "" 
        parent = self.parent
        while parent and parent.get_level() != 0:
            full_text = parent.get_text() + ' ' + full_text
            parent = parent.get_parent()
        self.ancestral_text = full_text
        
    def gen_descendant_text(self, global_list_row_obj):
        # NOTE: Here I exploit the properties of the global list of row objects to solve this here, 
        # but it likely has a recursive solution. 
        # It takes the list of all rows in the order they appear in html and runs through until it hits a row of the same indentation
        text = self.text + " " if self.classAttr != "SECMAIN" else ""
        index = global_list_row_obj.index(self) + 1 
        if(index < len(global_list_row_obj)-1):
            while(global_list_row_obj[index].get_level() > self.get_level() and index < len(global_list_row_obj)-1 and global_list_row_obj[index].get_text() not in text):
                text = text + global_list_row_obj[index].get_text() + " "
                index += 1
        self.descendant_text = text
           
    def gen_level_names(self):
        """
        ADD NOTES
        Only works for rows with content (Indent-# tags, not SECMAIN, Source, History, etc.)
        """
        if(len(self.text) >= 5):
            if(self.text[:5].find(')') == -1):
                if(self.text[0].isnumeric() and self.text[:5].find('.') != -1):
                    level_name = self.text[:self.text.find('.')]
                else:
                    level_name = None
            else:
                level_name = self.text[self.text.find('(')+1:self.text.find(')')]
        else:
            if(len(self.text) >= 3 and self.text[0] == '('):
                level_name = self.text[1:self.text.find(')')]
            else:
                level_name = None
        self.level_name = level_name
        
## Other useful functions for a RowObject   
    def merge_text(self, mergingRow):
        if(not isinstance(mergingRow, RowObject)):
            print("This is not a Row Object")
        else:
            self.text = self.text + " " + mergingRow.get_text()
            #Could merge with '\n' too if you think it's clearer

    def inherit_parent_attributes(self):
        if(self.get_level() != 0): ##Make sure this row has a parent (by ensuring it is not a SECMAIN)
            pointer = self
            while(pointer.get_level() != 0): ##While loop walks back until it finds the top SECMAIN for this row 
                pointer = pointer.get_parent()          
            self.chapter = pointer.get_chapter()
            self.act = pointer.get_act()
            self.section = pointer.get_section()
            self.title = pointer.get_title()
            self.rule = pointer.get_rule()  
            
    def parse_secmain_text(self):
        """
        Takes the text of SECMAIN of the form 
        "§ 5 ILCS 100/1-5. Applicability" -> "§ CHAPTER ILCS ACT/SECTION. TITLE"
        and strips it into its components
        """
        assert self.get_level() == 0, "RowObject not a SECMAIN Row"
        curr_text = self.text
        if("ILCS" in curr_text):
            #CHAPTER 
            chapter_long = curr_text[:curr_text.find("I")]
            curr_Ch = ""
            for character in chapter_long:
                if(character.isnumeric()):
                    curr_Ch = curr_Ch + character
            #ACT
            curr_Act = ""
            j = curr_text.find('/') - 1
            while(curr_text[j] != " "):
                curr_Act = curr_text[j] + curr_Act
                j -= 1
            #SECTION/TITLE
            reduced = curr_text[(curr_text.find('/') + 1):]
            dot_space_index = reduced.find(". ")
            if(dot_space_index != -1):
                curr_Sec = reduced[:dot_space_index]
                curr_Title = reduced[dot_space_index+2:-1]
            else:
                curr_Sec = reduced[:-1] #-1 removes last period
                curr_Title = "" #If there is no ". " then there is no title
    
            self.chapter = int(curr_Ch)
            self.act = int(curr_Act)
            self.section = curr_Sec
            self.title = curr_Title
            
        elif("Rule" in curr_text): # and "ILCS" not in curr_text):
            if("through" in curr_text): #Rules use format "1 through 10" instead of "1-10"
                first_val_start = curr_text.find('s')+2 #Finds the first value after the word "Rules"
                first_val_end = first_val_start + curr_text[first_val_start:].find(' ')
                rule = curr_text[first_val_start:first_val_end] + "-"
                period_index = curr_text[first_val_end+9:].find('.') #+9 to skip "through"
                if(period_index == -1):
                    rule = rule + curr_text[first_val_end+9:]
                    title = ""
                else:
                    rule = rule + curr_text[first_val_end+9:first_val_end+9+period_index]
                    title = curr_text[first_val_end+period_index+11:] 
            else:
                rule = curr_text[curr_text.find('e') + 2:curr_text.find('.')]
                title = curr_text[curr_text.find('.')+2:]
                
            self.rule = rule
            self.title = title



