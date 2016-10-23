########################################################
#!/usr/bin/python
# Filename: MyHistorianLib.py
import sys, array, os
from subprocess import call
import subprocess as subp
import time
import datetime
import math as math
from subprocess import Popen, PIPE
import numpy as np
import re
import json
import ROOT
import numexpr as ne
from ROOT import *

GAxisWidth = 200.
PlotWidth = 800.
PlotHeight = 400.
FilterSignificance = 30.

# set the filter significance
def SetFilterSignificance(significance):
    global FilterSignificance
    FilterSignificance = significance
    return

# check if a string is a number
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        pass
 
    try:
        import unicodedata
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass
 
    return False

# define reading of the list files
# return {ParNames, Alias}, Equations, Descriptions, Lower_Margins, Upper_Margins, ColorAtts
def ReadList(filename):
    fin = open(filename)
    lines = fin.readlines()
    fin.close()
    ParNameAliases = {}
    Equations = []
    Descriptions = []
    LowerMarginPercentages = []
    UpperMarginPercentages = []
    ColorAtts = []
    for line in lines:
        contents = re.split("[\t \n]+", line[:-1])
        if (not len(contents)==2) and (not len(contents)==5):
            continue
        elif len(contents)==2:
            ParNameAliases[str(contents[0])] = contents[1]
        elif (not is_number(contents[2])) or (not is_number(contents[3])) or (not is_number(contents[4])):
            continue
        else:
            Equations.append(contents[0])
            Descriptions.append(contents[1])
            LowerMarginPercentages.append(float(contents[2]))
            UpperMarginPercentages.append(float(contents[3]))
            ColorAtts.append(int(contents[4]))
    return (
                 ParNameAliases,
                 Equations,
                 Descriptions,
                 LowerMarginPercentages,
                 UpperMarginPercentages,
                 ColorAtts
                )

# Get unixtime from time stamp
def GetUnixTimeFromTimeStamp(timestamp):
    if len(timestamp)<18:
        return None
    Contents = timestamp[0:17].split(" ")
    Month, Day, Year = Contents[0].split("/")
    Hour, Minute, Second = Contents[1].split(":")
    Year = "20"+Year
    dt = datetime.datetime(int(Year), int(Month), int(Day), int(Hour), int(Minute), int(Second))
    return time.mktime(dt.timetuple())

# from ParName to Branch name
def FromParNameToBranchName(ParName):
    BranchName = ""
    Contents = ParName.split(".")
    for content in Contents:
        BranchName = BranchName + content + "_"
    return BranchName[:-1]

# Get the raw data
def GetRawData(filename, ParNameAliases):
    fin = ROOT.TFile(filename)
    if not fin.IsOpen():
        raise ValueError("Cannot open file %s" % filename)
    RawData = {}
    for ParID, ParName in enumerate(ParNameAliases):
        tree = fin.Get(FromParNameToBranchName(ParName))
        if not tree:
            raise ValueError("Tree %s doesn't exist" % ParName)
        Values = []
        if ParID==0:
            UnixTimes = []
        for event_id in range(tree.GetEntries()):
            tree.GetEntry(event_id)
            Values.append(float(tree.value))
            if ParID==0:
                UnixTimes.append(GetUnixTimeFromTimeStamp(tree.timestamp))
        RawData[ParNameAliases[ParName]] = Values
        if ParID==0:
            RawData['UnixTime']=UnixTimes
    fin.Close()
    return RawData


# Get the Jumping list
def GetJumpingList(Values):
    List = []
    if len(Values)==0:
        return List
    previous = Values[0]
    for value in Values:
        List.append(np.abs(value - previous))
        previous = value
    return List

# Get the Jumping lower/upper
def GetJumpingRange(Values):
    JumpingList = GetJumpingList(Values)
    jumping_mean = np.median(JumpingList)
    return jumping_mean*FilterSignificance
    
# Get filtered Lists
def GetFilteredList(UnixTimes, Values):
    JumpMean = GetJumpingRange(Values)
    PreviousValue = Values[0]
    FilteredUnixTimes = []
    FilteredValues = []
    counter = 0
    for unixtime, value in zip(UnixTimes, Values):
        if np.abs(value-PreviousValue) > JumpMean:
            PreviousValue = value
            counter = counter + 1
            continue
        if counter < len(Values)-1:
            if np.abs(value - Values[counter+1]) > JumpMean:
                PreviousValue = value
                counter = counter + 1
                continue
        FilteredUnixTimes.append(unixtime)
        FilteredValues.append(value)
        PreviousValue = value
        counter = counter + 1
    return (FilteredUnixTimes, FilteredValues)

# contruct TGraph
def ConstructGraph(UnixTimes,
                                 Values,
                                 Description,
                                 LowerMarginPercentage,
                                 UpperMarginPercentage,
                                 xlower,
                                 xupper,
                                 ylower,
                                 yupper,
                                 ColorAtt,
                                 Counter
                                 ):
    g = ROOT.TGraph()
    UnixTimes, Values = GetFilteredList(UnixTimes, Values)
    ValueMin = np.amin(Values)
    ValueMax = np.amax(Values)
    # re-calculate
    TrueValueMin = (
        LowerMarginPercentage*ValueMax - UpperMarginPercentage*ValueMin
        ) / (LowerMarginPercentage - UpperMarginPercentage)
    TrueValueMax = (ValueMin - ValueMax) / (LowerMarginPercentage - UpperMarginPercentage) + TrueValueMin
    if Counter==0:
        ylower = TrueValueMin
        yupper = TrueValueMax
    counter2 = 0
    scale_factor = (yupper - ylower) / (TrueValueMax - TrueValueMin)
    shift = ylower - TrueValueMin*scale_factor
    for unixtime, value in zip(UnixTimes, Values):
        g.SetPoint(counter2, unixtime, value*scale_factor + shift)
        counter2 = counter2 + 1
    g.SetLineWidth(2)
    g.SetLineColor(ColorAtt)
    g.GetXaxis().SetLabelFont(132)
    g.GetXaxis().SetLabelSize(0.05)
    g.GetXaxis().SetTitleFont(132)
    g.GetXaxis().SetTitleSize(0.05)
    g.GetXaxis().CenterTitle()
    g.GetXaxis().SetTitle("Date time")
    g.GetXaxis().SetRangeUser(xlower, xupper)
    g.GetYaxis().SetLabelFont(132)
    g.GetYaxis().SetLabelSize(0.05)
    g.GetYaxis().SetLabelColor(ColorAtt)
    g.GetYaxis().SetTitleFont(132)
    g.GetYaxis().SetTitleSize(0.05)
    g.GetYaxis().CenterTitle()
    g.GetYaxis().SetTitleColor(ColorAtt)
    g.GetYaxis().SetTitle(Description)
    g.GetYaxis().SetRangeUser(ylower, yupper)
    g.GetXaxis().SetTimeDisplay(1)
    # print(str(ylower)+" "+str(yupper))
    if Counter==0:
        g.GetYaxis().SetRangeUser(TrueValueMin, TrueValueMax)
    if xupper-xlower<7200.:
        g.GetXaxis().SetTimeFormat("%H:%M %F 1970-01-01 00:00:00")
    elif xupper-xlower<3600.*24.:
        g.GetXaxis().SetTimeFormat("%Hh %F 1970-01-01 00:00:00")
    elif xupper-xlower<3600.*24.*30:
        g.GetXaxis().SetTimeFormat("%d-%Hh %F 1970-01-01 00:00:00")
    elif xupper-xlower<3600.*24.*365:
        g.GetXaxis().SetTimeFormat("%m/%d %Hhr %F 1970-01-01 00:00:00")
    # gaxis construction
    GaxisTimeWidth = GAxisWidth/PlotWidth*(xupper - xlower)
    GaxisTime = GaxisTimeWidth*float(Counter - 1) + xupper
    gaxis = ROOT.TGaxis(GaxisTime, ylower, GaxisTime, yupper, TrueValueMin, TrueValueMax, 510, "+")
    gaxis.SetLineColor(ColorAtt)
    gaxis.SetLabelFont(132)
    gaxis.SetLabelSize(0.04)
    gaxis.SetLabelOffset(0.02)
    gaxis.SetLabelColor(ColorAtt)
    gaxis.SetTitleFont(132)
    gaxis.SetTitleSize(0.06)
    gaxis.SetTitleOffset(0.35)
    gaxis.SetTitleColor(ColorAtt)
    gaxis.CenterTitle()
    gaxis.SetTitle(Description)
    return (g, gaxis, TrueValueMin, TrueValueMax)    

# 
def IsFuncInEq(Equation):
    if Equation.find("first(")>=0:
        return True
    elif Equation.find("differential(")>=0:
        return True
    elif Equation.find("cumulative(")>=0:
        return True
    return False

# 
def GetFirst(Values):
    if len(Values)==0:
        raise ValueError("List cannot be empty")
    return Values[0]

# 
def GetDifferential(UnixTimes, Values):
    if len(Values)==0:
        raise ValueError("List cannot be empty")
    DifferentialValues = []
    PreviousTime = UnixTimes[0]
    PreviousValue = Values[0]
    for unixtime, value in zip(UnixTimes, Values):
        if unixtime==PreviousTime:
            DifferentialValues.append(0)
            continue
        DifferentialValues.append( (value-PreviousValue) / (unixtime - PreviousTime) )
        PreviousValue = value
        PreviousTime = unixtime
    DifferentialValues[0] = DifferentialValues[1]
    return DifferentialValues

def GetCumulative(UnixTimes, Values):
    if len(Values)==0:
        raise ValueError("List cannot be empty")
    CumulativeValues = []
    PreviousTime = UnixTimes[0]
    Sum = 0.
    for unixtime, value in zip(UnixTimes, Values):
        if unixtime==PreviousTime:
            Sum = Sum + value * (UnixTimes[1] - UnixTimes[0])
            CumulativeValues.append(Sum)
            continue
        Sum = Sum + value*(unixtime - PreviousTime)
        PreviousTime = unixtime
        CumulativeValues.append(Sum)
    return CumulativeValues

def GetFirstBottomSubEquation(Equation):
    Func = ""
    pos1 = Equation.find("first(")
    if pos1==-1:
        pos1 = len(Equation)
    pos2 = Equation.find("differential(")
    if pos2==-1:
        pos2 = len(Equation)    
    pos3 = Equation.find("cumulative(")
    if pos3==-1:
        pos3 = len(Equation)    
    if pos1== np.amin([pos1,pos2,pos3]):
        Func = "first"
        Equation = Equation[pos1+6:]
    elif pos2 == np.amin([pos1, pos2, pos3]):
        Func = "differential"
        Equation = Equation[pos2+13:]
    elif pos3 == np.amin([pos1, pos2, pos3]):
        Func = "cumulative"
        Equation = Equation[pos3+11:]
    IfFoundRightBracket = False
    # print(Equation)
    pos_left = -1
    pos_right = -1
    while not IfFoundRightBracket:
        pos_left = Equation.find("(", pos_left+1)
        pos_right = Equation.find(")", pos_right+1)
        if pos_right==-1:
            raise ValueError("Bracket error %s" % Equation)
        if pos_left==-1 or pos_right<pos_left:
            IfFoundRightBracket = True
            Equation = Equation[0:pos_right]
    # print(Func+" "+Equation)
    return (Func, Equation)

def GetBottomSubEquation(Equation):
    IfBottom = False
    Func = ""
    while not IfBottom:
        #print(Equation)
        if not IsFuncInEq(Equation):
            #print ("Not key func")
            IfBottom = True
            break
        Func, Equation = GetFirstBottomSubEquation(Equation)
        #print(Func+" -> "+Equation)
        if len(Equation)==0:
            raise ValueError("Equation somehow not correct!")
    return (Func, Equation)

# Calculate equation
# debug now so formula evaluating not implemented
def CalculateEquation(RawData, Equation):
    IfFuncInEq = True
    FuncCounter = 0
    while IfFuncInEq:
        if not IsFuncInEq(Equation):
            IfFuncInEq = False
        BottomFunc, BottomSubEquation = GetBottomSubEquation(Equation)
        BottomResultValues = ne.evaluate(BottomSubEquation, RawData)
        if BottomFunc == "first":
            Value = GetFirst(BottomResultValues)
            #print (BottomFunc+"("+BottomSubEquation+")")
            #print (Value)
            Equation = Equation.replace(BottomFunc+"("+BottomSubEquation+")", str(Value))
            #print (Equation)
        elif BottomFunc == "differential":
            Values = GetDifferential(RawData['UnixTime'], BottomResultValues)
            TmpAlias = "tmp"+str(FuncCounter)
            #print(BottomFunc+"("+BottomSubEquation+")")
            #print(Values)
            Equation = Equation.replace(BottomFunc+"("+BottomSubEquation+")", TmpAlias)
            RawData[TmpAlias] = Values
            FuncCounter = FuncCounter + 1
        elif BottomFunc == "cumulative":
            Values = GetCumulative(RawData['UnixTime'], BottomResultValues)    
            TmpAlias = "tmp"+str(FuncCounter)
            Equation = Equation.replace(BottomFunc+"("+BottomSubEquation+")", TmpAlias)
            RawData[TmpAlias] = Values
            FuncCounter = FuncCounter + 1      
    ResultValues = ne.evaluate(Equation, RawData)
    return ResultValues

import scipy as sp
from scipy.interpolate import interp1d
# Regulate the values using one reference unixtime
def GetRegulatedValues(ReferenceUnixtimes, Unixtimes, Values):
    Interpolator = interp1d(Unixtimes, Values, fill_value = "extrapolated")
    OutputValues = []
    for unixtime in ReferenceUnixtimes:
        value = Interpolator(unixtime)
        OutputValues.append( float(value) )
    return OutputValues

# End of MyHistorianLib.py
