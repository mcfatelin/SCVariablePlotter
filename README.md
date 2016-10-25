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

======= variable list =========

Basically it is just a file contain all the historian tags you want in your query. The file shall be sth like:

Tag#1

Tag#2

.....

You can check-out List/LXeFilling_IDList.txt for an example

======= draw option list format: ========

The draw option list consists of two pars:

1) define the alias for the historian tags:

Tag#1        Alias#1

Tag#2        Alias#2

......

2) Then define the variable you want to draw, it can be a function of the aliases you just defined:

Variable#1         Description#1          Y_Fraction_lower#1            Y_Fraction_lower#1          Color#1

........

Note:
     Description contains no space.
     
     Y_Fraction_lower and Y_Fraction_upper limit the curve in (Y_Fraction_lower, Y_Fraction_upper) of the whole canvas.
     
     Color is python color notation.

