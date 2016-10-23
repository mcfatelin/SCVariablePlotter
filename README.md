# SCVariablePlotter
Python code for query and plotting SC variables

Basic usage

------------------ Query the SC variables into pickle ---------------------

The code is for extracting the SC variables

from the SC database Chris made:

https://xecluster.lngs.infn.it/dokuwiki/lib/exe/fetch.php?media=xenon:xenon1t:analysis:meetings:my_sc_adventure.html

========== Syntax: =============

python BatchQuerySC.py 

[variable list]

[start time in yymmdd_HHMM]

[end time in yymmdd_HHMM]

[output pickle file]



The query needs the support from hax (https://github.com/XENON1T/pax)

------------------ Plotting the desired variable trends using the pickle output of the query ---------------------------

python DrawPars.py .......

[pickle file]

[draw option list]

======= draw option list format: ========

 Two types of line can be put in there:
 
1) # Historian Tag 	...	 #Alias name

2) # formulat with alias \t....\t # title \t...\t [lowest coordinate of the whole canvas] \t...\t [uppermost y coordinate of the whole canvas] \t...\t [python color]

Note that the different elements MUST be separated by \t

