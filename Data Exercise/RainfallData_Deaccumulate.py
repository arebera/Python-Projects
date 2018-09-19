'''
Program to accept accumulated rainfall data and transform to de-accumulated format
Author : Mary Ann Rebera
Date : 19 September 2018
'''

import random
import time
import pandas as pd
from pathlib import Path
import os
import numpy as np

###Function Definitions follows

## Function to split a decimal number into specified number of constituents
def splitNumber(x,n):

    # Converting rainfall measurement to integer
    x = int(x * 100)
    i = 1
    splitList = list()

    # Find constituent values of a number
    while i < n:
        split = random.randrange(0, x)
        x = x - split
        i += 1
        split = float(split / 100)
        #print(split)
        splitList.append(split)

    x = float(x / 100)
    #print(x)
    splitList.append(x)
    return splitList

## Function to find the peak 30 minutes period within a user supplied time range
def findPeak(dfDeaccumRainfall,fromDate,toDate):
    from calendar import timegm
    import time
    import datetime
    import pandas as pd

    #Convert user input date time to epochs
    EST_FromTime = time.strptime(fromDate, "%Y-%m-%d %H:%M")
    epoch_FromTime = timegm(EST_FromTime)
    EST_ToTime = time.strptime(toDate, "%Y-%m-%d %H:%M")
    epoch_ToTime = timegm(EST_ToTime)

    dfPeakRain = pd.DataFrame()

    # Iterate through all the rows
    for index, row in dfDeaccumRainfall.iterrows():

        interval = time.strptime(str(row[0]), '%Y-%m-%d %H:%M:%S-%f:%W')
        #print("interval",interval)
        epoch_Interval = timegm(interval)
        #print("epoch interval",epoch_Interval)

        # Check if the user entered date time range is available in the file
        while (epoch_Interval >= epoch_FromTime) & (epoch_Interval <= epoch_ToTime):
            dfPeakRain = dfPeakRain.append(row)
            break
    if dfPeakRain.empty:
        print("Data not available for this time range")
    else:
        # If user input date time range is available, calculate the peak 30-minute period
        dfPeakRain.columns = ['DateTime', 'Rainfall']
        maxIndex = dfPeakRain['Rainfall'].idxmax()
        toTime = dfPeakRain.loc[maxIndex, "DateTime"]
        fromTime = datetime.datetime.strptime(str(toTime), '%Y-%m-%d %H:%M:%S-%f:%W') + datetime.timedelta(minutes=-30)

        # Formatting for date and time display
        dateFormat = "%Y-%m-%d"
        timeFormat = "%H:%M"

        # Display peak period and rainfall on the screen
        if dfPeakRain.loc[maxIndex, 'Rainfall'] == 0.0:
            print("No rainfall measured during this time range")
        else:
            print("Peak 30 minute period is between", fromTime.strftime(timeFormat), "and", toTime.strftime(timeFormat), "on",
                  toTime.strftime(dateFormat))
            print("Measured rainfall: ", dfPeakRain.loc[maxIndex, 'Rainfall'], "inches")

###Start of the program
## To accept input from csv file stored in the local machine
fileDirectory = 'D:\\MM\\DataExercise\\'
filename = 'accumRainfall2.csv'
file_to_open = os.path.join(Path(fileDirectory),filename)
dfSource = pd.read_csv(file_to_open)
#print(dfSource)
#print(dfSource.shape)

'''
## To accept input from a SQL Server database
import pyodbc
server = '<Server name>'
database = '<mydatabase>'
username = '<myusername>'
password = '<mypassword>'
dbConnection = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
cursor = dbConnection.cursor()

cursor.execute("<query>")
tableRow = cursor.fetchone()
while tableRow:
    dfSource = tableRow[0]
    tableRow = cursor.fetchone()
'''

'''
## To accept input from a JSON API
import json
apiPath = requests.get('<file location>')
apiData = apiPath.json()
dfSource = pd.DataFrame(apiData['column name'])
'''

# First observation datetime is extracted from the data source to calculate the date range
initDate = dfSource.iat[0,0]
initDate = initDate - 21600
startDate = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(initDate))

# Initialising data frames
dfDateTimeConvert = pd.DataFrame()
dfRainfall = pd.DataFrame()
dfDeaccumRainfall = pd.DataFrame()

# Iterating through all the rows in the input file
for index, row in dfSource.iterrows():
    dateTimeEST = row[0] - 14400
    rainfallValue = row[1]

    # Creating time series
    indexDateTimeSeries = pd.date_range(start = startDate,end = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(dateTimeEST)),tz='US/Eastern',freq='30min')

    dfDateTimeSeries = pd.DataFrame(indexDateTimeSeries)
    dfDateTimeSeries.columns = ['DateTimeInterval']
    dfDateTimeConvert = dfDateTimeConvert.append(dfDateTimeSeries)
    dfDateTimeConvert.index = np.arange(0, len(dfDateTimeConvert))
    lastIndex = len(dfDateTimeSeries.index)

    startDate = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(dateTimeEST))

    #Distributing rainfall measurement between the observation times
    dfRainfallMeasure = pd.DataFrame(splitNumber(rainfallValue,lastIndex))
    dfRainfallMeasure = dfRainfallMeasure.sample(frac=1)
    dfRainfallMeasure.columns = ['Rainfall']
    dfRainfall = dfRainfall.append(dfRainfallMeasure)

## Combine time series with de-accumulated rainfall measurement
dfDateTimeConvert.index = np.arange(0,len(dfDateTimeConvert))
dfRainfall.index = np.arange(0,len(dfRainfall))
listDeaccumRainfall = pd.concat([dfDateTimeConvert,dfRainfall],axis=1,sort=False)
dfDeaccumRainfall = pd.DataFrame(listDeaccumRainfall)

## Save the de-accumulated data in a csv file
resultPath = 'D:\\MM\\DataExercise\\'
resultFile = 'DeaccumRainfall.csv'
file_to_save = os.path.join(Path(resultPath),resultFile)
dfDeaccumRainfall.to_csv(file_to_save,encoding='utf-8',index=False)
print("Rainfall data de-accumulated and saved to csv file")

## To save the de-accumulated data into a SQL table
'''
Initially create the table in SQL Server
USE <Database name>;
GO
DROP TABLE IF EXISTS <Table name>
CREATE TABLE <Table name>
(
 [IndexNumber] INT
 ,[DateTimeInterval] DATE
 ,[Rainfall] DECIMAL(2,2)
)
'''
# Creating connection string and inserting values into the table
'''
# dbConnStr = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
# cursor = dbConnStr.cursor()
# for index, row in dfDeaccumRainfall.iterrows():
#           cursor.execute("INSERT INTO....")
#           dbConnStr.commit()
#cursor.close()
#dbConnStr.close()
'''


## Finding peak period within supplied time range

checkFlag = input("To calculate peak value enter Y : ")
if (checkFlag == 'y') | (checkFlag == 'Y'):
    fromDate = input("Input the From time in the format YYYY-MM-DD HH:MM : ")
    toDate = input("Input the To time in the format YYYY-MM-DD HH:MM : ")
    findPeak(dfDeaccumRainfall,fromDate,toDate)
else:
    print("Exiting the program")
    exit()
