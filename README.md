# PCoder
A python script that uses string comparison methods to apply the humanitarian PCodes to any dataset with administrative area names.

The Pcoder was developed by [Marco Velliscig](https://github.com/MarcoVelliscig/Red_Cross_NL/tree/master/Pcoder) @ 510 a data initiative by the Netherlands Red Cross.
Code is available under the [GPL license](https://github.com/rodekruis/Pcoder/blob/master/LICENSE)

![alt tag](http://510.global/wp-content/uploads/2015/06/510-opengraph.png)

# How to Use

## Prerequisites

* You need Python2 to run this code
* Install pandas and numpy libraries e.g. through pip

## For existing country (e.g. Philippines)

* Enter the file (csv/xlsx) to pcode in /files_input
* Open pcoder.py and change the settings at the top accordingly
1. You can specify multiple files, but can also uncomment some by setting if_to_pcode=False
2. Name of the input-file
3. Name of the ouput-file
4. Specify on which levels you want to Pcode: i.e. L1 and L2 if the file contains province and municipality names.
5. Names of the relevant columns in the input-file: i.e. name of province-column, municipality-column, etc.

* Run the file, e.g. from a terminal (already pointed to the location of pcoder.py)
```
C:/python27/python pcoder.py
```
or wherever the path to your python2 installation is.

## For new country

* If you want to use this for a new country, you need to make/add a template with both pcodes and names to folder /templates first.
* Look at the examples for format.
* At the top of pcoder.py change the template settings as well
1. Name of template file
2. Name of relevant columns in template file.
* Run in same way as above

## Advanced
* You can play with the parameters ask_below_score and reject_below_score to play with the interactivity. Generally the idea is that if the algorithm finds either a 100% text match or a text match which is certain enough, then it accepts the answer (higher than ask_below_score). If there is no close match at all (lower than reject_below_score), it will simply leave the line empty and move in. In between these two, the machine will check with you. First it proposes the best match and you say yes/no. If no, it shows a list of all options and you can choose one. Or you can reject and it will move on. 
* Say that you have a column which can contain names of multiple levels: both provinces and municipality names. Then you can run the algorithm first for level_tag=['L1'] only. This will find matches for the province names. And sill simply give a lot of empty rows for the municipality names. Then run the algorithm again for level_tag=['L2'] to get the municipality names. Either save the 2nd under a different name and combine manually. Or move your output from the first run back to the input-folder and use it as input for the second run.
* In this example there will be a lot of non-matches. So in this case, you might want to avoid all the interactivity noise. You can do so by setting ask_below_score exactly equal to reject_below_score (for the level you are looking at). 
 

