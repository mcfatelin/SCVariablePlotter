##########################
# For plotting the SC trend
# using the pickle from BatchQuery.py
##########################
# by Qing Lin
# @ 2016-10-22
##########################
import sys
import pickle
import numpy as np

if len(sys.argv)<2:
    print("============ Syntax ==========")
    print("python DrawPars.py .......")
    print("<pickle file>")
    print("<draw option list>")
    print("======= draw option list format: ========")
    print(" Two types of line can be put in there:")
    print("1) # Historian Tag \t...\t #Alias name")
    print("2) # formulat with alias \\t....\\t # title \\t...\\t <lowest y at xx of the whole canvas> \\t...\\t <uppermost y at xx of the whole canvas> \\t...\\t <python color>")
    print("Note that the different elements MUST be separated by \\t")
    exit()

PickleFile = sys.argv[1]
DrawOptList = sys.argv[2]

############################
## Get the alias dictionary
## And the function for drawing
############################
AliasDict = {}
DrawOpts = []

fin = open(DrawOptList)
lines = fin.readlines()
fin.close()

for line in lines:
    line = line.replace("\n", "")
    line = line.replace("\t", "")
    contents = line.split(" ")
    Contents = []
    for content in contents:
        if len(content)>0:
            Contents.append(content)
    if len(Contents)==2:
        AliasDict[Contents[0]] = Contents[1]
    elif len(Contents)==5:
        TmpData = {}
        TmpData['function'] = Contents[0]
        TmpData['title'] = Contents[1]
        TmpData['ylower_frac'] = float(Contents[2])
        TmpData['yupper_frac'] = float(Contents[3])
        TmpData['color'] = Contents[4]
        DrawOpts.append(TmpData)

###############################
## Get the whole dict for raw SC data
###############################
RawSCData = pickle.load( open(PickleFile, 'rb') )


###############################
## get the unixtimes and values
## that is in the alias list
## first get the maximum unixtime list
## then regulate through all relevant values
###############################
RawData = {}
# get the maximum unixtime list
RegulatedUnixTimes = []
RegulatedSCName = ""
MaxUnixtimeListNum = 0
for SCItem in AliasDict:
    if len(RawSCData[SCItem]['unixtimes']) > MaxUnixtimeListNum:
        RegulatedSCName = SCItem
        MaxUnixtimeListNum = len(RawSCData[SCItem]['unixtimes'])
RegulatedUnixTimes = RawSCData[RegulatedSCName]['unixtimes']
RawData['UnixTime'] = RegulatedUnixTimes
# regulate all the relevant SC trend 
# store it in RawData
import MyHistorianLibV2
from MyHistorianLibV2 import GetRegulatedValues
for SCItem in AliasDict:
    AliasName = AliasDict[SCItem]
    RegulatedValues = GetRegulatedValues(
                                                                      RegulatedUnixTimes,
                                                                      RawSCData[SCItem]['unixtimes'],
                                                                      RawSCData[SCItem]['values'],
                                                                     )
    RawData[AliasName] = list(RegulatedValues)

################################
## Calculate the dates
################################
import datetime as dt
Dates = [dt.datetime.fromtimestamp(ts) for ts in RegulatedUnixTimes]
################################
## Draw
################################
import mpl_toolkits
import matplotlib
from mpl_toolkits.axes_grid1 import host_subplot
import mpl_toolkits.axisartist as AA
import matplotlib.pyplot as plt
import matplotlib.dates as md
from MyHistorianLibV2 import CalculateEquation
right_additive = 0.08

fig, host = plt.subplots(1)
#host = host_subplot(111, axes_class=AA.Axes)
RightMargin = 0.92 - float(len(DrawOpts) - 2)*right_additive
plt.subplots_adjust(right=RightMargin)
xfmt = md.DateFormatter('%Y-%m-%d')
host.xaxis.set_major_formatter(xfmt)
host.set_xlabel("Date", fontsize=30.)
host.tick_params(axis='x', labelsize=20)


for i, DrawOpt in enumerate(DrawOpts):
    ResultValues = CalculateEquation(RawData, DrawOpt['function'])
    MaxValue = np.max(ResultValues)
    MinValue = np.min(ResultValues)
    Color = DrawOpt['color']
    Title = DrawOpt['title']
    FracLower = DrawOpt['ylower_frac']
    FracUpper = DrawOpt['yupper_frac']
    YRangeLower = - (MaxValue*FracLower - MinValue*FracUpper) / (FracUpper - FracLower)
    YRangeUpper = (MaxValue - MinValue) / (FracUpper - FracLower) + YRangeLower
    if i==0:
        host.plot(Dates, ResultValues, color=Color, lw = 3.)
        host.set_ylim( [YRangeLower, YRangeUpper] )
        host.set_ylabel(Title, fontsize=30., color=Color)
        host.tick_params(axis='y', labelsize=20)
        host.yaxis.label.set_color(Color)
        for tl in host.get_yticklabels():
            tl.set_color(Color)
    elif i==1:
        par = host.twinx()
        par.set_navigate(True)
        par.plot(Dates, ResultValues, color=Color, lw=3.)
        par.set_ylim( [YRangeLower, YRangeUpper] )
        par.set_ylabel(Title, fontsize=30.)
        par.tick_params(axis='y', labelsize=20)
        par.yaxis.label.set_color(Color)
        for tl in par.get_yticklabels():
            tl.set_color(Color) 
    else:
        par = host.twinx()
        par.set_navigate(True)
        par.spines['right'].set_position(('axes', 1.+1.3*right_additive*float(i-1)))
        par.plot(Dates, ResultValues, color=Color, lw=3.)
        par.set_ylim( [YRangeLower, YRangeUpper] )
        par.set_ylabel(Title, fontsize=30.)
        par.tick_params(axis='y', labelsize=20)
        par.yaxis.label.set_color(Color)
        for tl in par.get_yticklabels():
            tl.set_color(Color)      


fig.autofmt_xdate()
plt.draw()
plt.show()

