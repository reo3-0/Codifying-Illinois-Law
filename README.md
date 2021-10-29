# Codifying-Illinois-Law
This code takes the 2020 Illinois Compiled Statutes (ILCS) in html format and converts it to a csv.
This code was part of a project done with the Data Team at the Cook County State's Attorney's Office (SAO)
and was part of a larger effort to pair stautory language with existing SAO cases to increase accuracy
of case classification. 


## Included Files
This repository contains 2 python files:
1) RowObject.py which houses the class Rowobject which holds key information about a given csv row, 
including column information and family tree structure (parents and children)
2) Codifying_ILCS.py which reads in the html file, parses out the important html rows, 
turns those rows into RowObjects, and puts the RowObjects together in a csv file.

This repository contains 1 html file:
wholebook.html which contains the 2020 Illinois Compiled statutes book. 
This html can be substituted for a later ILCS book and the code 
should be relatively generalized.

This repository contains 1 csv file:
This is the final table for ILCS 2020. It is the csv output from Codifying_ILCS.py

## About the code

#### RowObject.py

The RowObject class creates an instance of an object that holds all of the relevant information
for a single row in the final dataset. This includes the chapter, act, section, and text of that
row which will be put into the appropriate corresponding column of the csv. Additionally, RowObject
instances hold familial information about the immediate parent and children for that object. 

For example, the RowObject for 

#### [INSERT NAME HERE]


