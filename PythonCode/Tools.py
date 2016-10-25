import re
import numpy as np
import pandas as pd
import scipy as scp
import os, sys
import time, datetime



# Get unixtime from time stamp
def GetUnixTimeFromTimeStampTool(timestamp):
    if len(timestamp)<9:
        return None
    Contents = timestamp[0:9].split("_")
    #print(Contents)
    Year = "2016"
    Month = Contents[0][0:2]
    Day = Contents[0][2:4]
    #print(Day)
    Hour = Contents[1][0:2]
    Minute = Contents[1][2:4]
    Second = "0"
    dt = datetime.datetime(int(Year), int(Month), int(Day), int(Hour), int(Minute), int(Second))
    return time.mktime(dt.timetuple())

# Get unixtime from time stamp
# but also return the datetime object
def GetUnixTimeAndDatetimeFromTimeStampTool(timestamp):
    if len(timestamp)<11:
        return (None, None)
    Contents = timestamp[0:11].split("_")
    #print(Contents)
    Year = "20"+Contents[0][0:2]
    Month = Contents[0][2:4]
    Day = Contents[0][4:6]
    #print(Day)
    Hour = Contents[1][0:2]
    Minute = Contents[1][2:4]
    Second = "0"
    #print(Year)
    dt = datetime.datetime(int(Year), int(Month), int(Day), int(Hour), int(Minute), int(Second))
    return (dt,time.mktime(dt.timetuple()))


# Get the dictionary containing 
# 1) unixtime
# 2) values
# from pandas series
#Translate one time stamp to unixtime
#yyyy-mm-dd HH:MM:SS.subsec
def TranslateTimestampToUnixtime(timestamp):
    TimeStamp = timestamp
    #print(TimeStamp)
    TimeStamp = TimeStamp.split(".")[0]
    Date, Hours = TimeStamp.split(" ")
    Year, Month, Day = Date.split("-")
    Hour, Minute, Second = Hours.split(":")
    dt = datetime.datetime(int(Year), int(Month), int(Day), int(Hour), int(Minute), int(Second))
    return time.mktime(dt.timetuple())

#get the dictionary
# the series shall be pre-sorted already
def GetDictFromSeries(series):
    OutputData = {}
    Unixtimes = []
    Values = []
    for key, value in zip(series.keys(), series):
        # print(key)
        unixtime = TranslateTimestampToUnixtime(str(key))
        Unixtimes.append(unixtime)
        Values.append(value)
    OutputData['unixtimes'] = Unixtimes
    OutputData['values'] = Values
    return OutputData

# get region
def GetRegion(UnixTimes, LowerBoundaries, UpperBoundaries):
    if not len(LowerBoundaries)==len(UpperBoundaries):
        raise ValueError("Lists' length don't match")
    graph = TGraph()
    for i, (unixtime, lower) in enumerate(zip(UnixTimes,LowerBoundaries)):
        graph.SetPoint(i, unixtime, lower)
    for i, (unixtime, upper) in enumerate(zip(
                                                                      reversed(UnixTimes),
                                                                      reversed(UpperBoundaries)
                                                                     )):
        graph.SetPoint(i+len(UnixTimes), unixtime, upper)
    return graph

def PickupMCMCPosteriors(Samples, NumOfTrials):
    indexs = np.random.choice(len(Samples), NumOfTrials)
    OutputList = []
    for index in indexs:
        OutputList.append(Samples[index])
    return OutputList

# For Burn-In region
# count list depth
def depth(a):
    if type(a) is list or type(a) is np.ndarray:
        return 1+depth(a[0])
    return 0

# re-arrange the chain
# so that it become
# [Iteration][Walker_id][Par_id]
def ReshapeChain(chain, ndim, nwalkers, niterations):
    if not depth(chain)==3:
        raise ValueError("chain depth not standard!")
    OutputSamples = []
    # initialization
    # parameter loop
    for i in range(niterations):
        ListForAppend = []
        #walker loop
        for j in range(nwalkers):
            ListForAppend.append([])
        OutputSamples.append(ListForAppend)
    # fill the values
    # walker loop
    for i, SamplesOneWalker in enumerate(chain):
        #print(SamplesOneWalker)
        # iteration loop
        for k, SamplesOneIteration in enumerate(SamplesOneWalker):
            # Parameter loop
            for j, SampleOnePar in enumerate(SamplesOneIteration):
                #print(str(j)+"\t"+str(i)+"\t"+str(SampleOnePar))
                OutputSamples[k][i].append(SampleOnePar)
    return OutputSamples


# chain shall be a 3x3 vector
# [Par_id][Walker_id][Iteration]
def GetSamplesForPlot(chain, ndim, nwalkers, niterations):
    if not depth(chain)==3:
        raise ValueError("chain depth not standard!")
    OutputSamples = []
    # initialization
    # parameter loop
    for i in range(ndim):
        ListForAppend = []
        #walker loop
        for j in range(nwalkers):
            ListForAppend.append([])
        OutputSamples.append(ListForAppend)
    # fill the values
    # walker loop
    for i, SamplesOneWalker in enumerate(chain):
        #print(SamplesOneWalker)
        # iteration loop
        for SamplesOneIteration in SamplesOneWalker:
            # Parameter loop
            for j, SampleOnePar in enumerate(SamplesOneIteration):
                #print(str(j)+"\t"+str(i)+"\t"+str(SampleOnePar))
                OutputSamples[j][i].append(SampleOnePar)
    return OutputSamples

def GetBurnInCutoffSamples(chain, cutoff):
    OutputList = []
    #walker loop
    for SamplesOneWalker in chain:
        #print(SamplesOneWalker)
        # iteration loop
        for i, SamplesOneIteration in enumerate(SamplesOneWalker):
            if i<cutoff:
                continue
            OutputList.append(SamplesOneIteration)
    return OutputList

def GetBurnInCutoffSamplesV2(chain, cutofflower, cutoffupper):
    OutputList = []
    #walker loop
    for SamplesOneWalker in chain:
        #print(SamplesOneWalker)
        # iteration loop
        for i, SamplesOneIteration in enumerate(SamplesOneWalker):
            if i<cutofflower:
                continue
            if i>cutoffupper:
                continue
            OutputList.append(SamplesOneIteration)
    return OutputList


# function for checking the list percentile with np.inf in it
def PercentileWithInf(Values, deviation):
    TotalCounter = len(Values)
    InfCounter = 0
    NewValues = []
    # first get the new list and counter
    for value in Values:
        if value==np.inf:
            InfCounter += 1
        else:
            NewValues.append(value)
    Fraction = (1. - float(InfCounter) / float(TotalCounter)) * 100.
    if deviation>Fraction:
        return np.inf
    deviation_new = deviation / Fraction *100.
    return np.percentile(NewValues, deviation_new, axis=0)


    
