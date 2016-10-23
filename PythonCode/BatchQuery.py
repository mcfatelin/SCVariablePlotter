#########################
# For extracting Xe1T SC parameter
# Output to a pickle file, 
# which contains the trend for each variable in query
#########################
# by Qing Lin
# @ 2016-10-22
#########################
import sys
import pickle
import numpy as np
import pandas
import datetime
import hax
from hax import slow_control
import Tools
from Tools import GetUnixTimeAndDatetimeFromTimeStampTool
from Tools import GetDictFromSeries

if len(sys.argv)<2:
    print("################################")
    print("# The code is for extracting the SC variables")
    print("# from the SC database Chris made:")
    print("# https://xecluster.lngs.infn.it/dokuwiki/lib/exe/fetch.php?media=xenon:xenon1t:analysis:meetings:my_sc_adventure.html")
    print("========== Syntax: =============")
    print("python BatchQuerySC.py ")
    print("<variable list>")
    print("<start time in yymmdd_HHMM>")
    print("<end time in yymmdd_HHMM>")
    print("<output pickle file>")
    exit()

VariableList = sys.argv[1]
StartTimeStamp = sys.argv[2]
EndTimeStamp = sys.argv[3]
OutputFile = sys.argv[4]

#######################################
# from VariableList file 
# to Tags
#######################################
Tags = []
fin = open(VariableList)
lines = fin.readlines()
fin.close()

for line in lines:
    line = line.replace(" ","")
    line = line.replace("\n","")
    if len(line)<1:
        continue
    Tags.append(line)




#######################################
# check if the time stamp inputed are standard
#######################################
if not len(StartTimeStamp)==11:
    print("Start time stamp in format of yymmdd_HHMM")
if not len(EndTimeStamp)==11:
    print("End time stamp in format of yymmdd_HHMM")


######################################
# Get the time range
######################################
TimeRangeLower, UnixTimeLower = GetUnixTimeAndDatetimeFromTimeStampTool(StartTimeStamp)
TimeRangeUpper, UnixTimeUpper = GetUnixTimeAndDatetimeFromTimeStampTool(EndTimeStamp)
TimeRange = (TimeRangeLower, TimeRangeUpper)

#######################
# Get the dictionary data
#######################
Data = {}
for Key in Tags:
    series = slow_control.get_series(Key, time_range=TimeRange)
    Data[Key] = GetDictFromSeries(series)

#####################################
# dump it to pickle
#####################################
pickle.dump(Data, open(OutputFile, 'wb'))
