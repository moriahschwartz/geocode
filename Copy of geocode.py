import os
import sys
import geopy
from geopy.geocoders import GoogleV3
from geopy.distance import vincenty
import pandas as pd
from pandas import DataFrame, read_csv
import tkinter
from tkinter import Tk
from tkinter.filedialog import askopenfilename


print("\nThis program geocodes addresses in a csv file and returns the latitude and longitude associated with the address, "
      "as well as the county in which it is located.\n")

next = input("\nPress enter to continue.")

#Creates a dataframe from the apikey csv included with program files
apifile = r'apikey.csv'
apidf = pd.read_csv(apifile)
key = apidf['API Key'][0]

response = 'empty'
#If an API key has been used and saved with this program (from a previous use of the program)
if key != 'na':
    response = input('You have already entered a Google API key for use with this program. If you would like to use a '
                     'different one, enter "1". Otherwise, just press enter to continue. ')
#If no API keys have been used and saved before (first use)
else:
    getkey = input('Request a Google API key at https://developers.google.com/maps/documentation/javascript/get-api-key.'
                ' When you have obtained one, press enter.')
    response = '1'
if response == '1':
    key = input('Please enter your Google API key here. ')
    apidf['API Key'][0] = key
    apidf.to_csv('apikey.csv')

geolocator = GoogleV3(api_key=str(key), timeout=1)

filein = False
#Ask the user to select a file until they have selected a valid one
while filein == False:
    print('\nSelect the file containing the data you want to geocode.')
    #Open Windows file explorer box and save path of file user selects
    file = askopenfilename()
    #file = easygui.fileopenbox()
    try:
        df = pd.read_csv(file, encoding='iso-8859-1')
        filein = True
    except:
        print('There was an error. Try again or select another file.')

#Create lists to store information below
key_list = []
address_list = []
latitude_list = []
longitude_list = []
county_list = []
error_list = []

#Checks to see if user enters a column name that is actually in the dataset
def get_and_validate_column_name(prompt):
    userin = False
    error_msg = 'The column name you entered is invalid. Make sure spelling and capitalization are correct. '
    while not userin:
        user_input = input(prompt)
        if user_input in df.columns:
            userin = True
        else:
            print(error_msg)
    return user_input

#Asks the user whether the address is in a single column or split up into street, city, and state columns
#Then returns address column(s)
def get_address_type(type_prompt):
    typein = False
    while not typein:
        type_input = input(type_prompt)
        if type_input == "1":
            typein = True
            prompt = '\nEnter the name of the column in your file that records addresses exactly as it appears in the dataset. [Example: ProviderAddress] '
            #Return the address
            addresscol = get_and_validate_column_name(prompt)
            return addresscol
        elif type_input == "2":
            typein = True
            prompt = '\nEnter the name of the column in your file that records street address exactly as it appears in the dataset. [Example: ProviderStreet] '
            streetcol = get_and_validate_column_name(prompt)
            prompt = '\nEnter the name of the column in your file that records the city associated with the street address exactly as it appears in the dataset. [Example: ProviderCity] '
            citycol = get_and_validate_column_name(prompt)
            prompt = '\nEnter the name of the column in your file that records the state associated with the street address exactly as it appears in the dataset. [Example: ProviderState] '
            statecol = get_and_validate_column_name(prompt)
            #Return the address as a list
            addresscol = [streetcol, citycol, statecol]
            return addresscol
        else:
            print('Invalid response. Please enter "1" or "2".')

#Geocodes addresses
def geocode_and_create_dataframe(address_input, key_input):
    for i in range(len(df.index)):
        key = df[key_input][i]
        key_list.append(key)
        # If the address is a list (i.e., is made up of several columns)
        if isinstance(addresscol, list):
            street = df[address_input[0]][i]
            city = df[address_input[1]][i]
            state = df[address_input[2]][i]
            address = str(street) + " " + str(city) + " " + str(state)
        # If the address is not a list (i.e., is contained in a single column)
        else:
            address = df[address_input][i]
        address_list.append(address)
        try:
            location = geolocator.geocode(address)
            latitude_list.append(location.latitude)
            longitude_list.append(location.longitude)
            error_list.append(' ')
            # Iterate through the output of location.raw to obtain county information
            for i in range(len(location.raw['address_components'])):
                county = location.raw['address_components'][i]['long_name']
                types = location.raw['address_components'][i]['types']
                if 'administrative_area_level_2' and 'political' in types:
                    # In Louisiana, Parishes instead of Counties
                    if ' County' in county or ' Parish' in county:
                        county_list.append(county)
        except Exception as exception:
            # A particular address may have been entered wrong or left blank
            print("\nA geocoding error occurred.")
            # Record the type of exception that took place and save it to error_list
            etype = exception.__class__.__name__
            error_list.append(etype)
            # Record that an error occurred
            for listitem in [latitude_list, longitude_list, county_list]:
                listitem.append('ERROR')
    # Create a new Data Frame from the geocoding results
    df_new = pd.DataFrame({str(key_input): key_list, 'Address': address_list, 'Latitude': latitude_list, 'Longitude': longitude_list,
         'County': county_list, 'Error Type': error_list})
    return df_new

#Performs a left merge on two dataframes
def left_join(df_one, df_two, column):
    # Perform a left join using the primary key given by the user
    joiner = pd.merge(df, df_new, on=str(column), how='left')
    # Create a data frame containing the joined data
    joindf = pd.DataFrame(joiner)
    return joindf


#Obtain the primary key in the dataset from the user
prompt = '\nEnter the name of the column in your file that contains a primary key or ID number for each record in your dataset. [Example: ProviderID] '
key_input = get_and_validate_column_name(prompt)

#Obtain the address from the user depending on the way the database is structured
type_prompt = '\nAre the addresses (street, city, and state) in your dataset 1) Contained in a single column, or 2) Separated into street, city, and state columns? Please enter "1" or "2". '
addresscol = get_address_type(type_prompt)

#Geocode the addresses and obtain a new dataframe
df_new = geocode_and_create_dataframe(addresscol, key_input)
# Save the data frame as a csv to the same folder containing the original dataset
folder = os.path.dirname(file)

def create_csv(dataframe, folder, name):
    folder_clear = False
    while not folder_clear:
        try:
            dataframe.to_csv(folder + str(name))
            folder_clear = True
        except Exception as exception:
            etype = exception.__class__.__name__
            if etype == 'PermissionError':
                print('\nThere is already a file(s) in your folder that contains geocode results. Please change its name or move it'
                  ' to a different folder.')
                response = input('Press "Enter" AFTER you do this.')
    msg = '\nA new file called "' + str(name) + '" has been added to the same folder as your original dataset.'
    print(msg)

create_csv(df_new, folder, '\geocoderesults.csv')

yninput = False
#Ask the user if they would like the new dataset to be joined to their original file
while not yninput:
    response = input('\nWould you like this new dataset to be joined to your original file? Enter "yes" or "no" ')
    #If user responds yes, use the left_join function
    if response.lower() == 'yes':
        yninput = True
        joindf = left_join(df, df_new, key_input)
        '''
        joindf.to_csv(folder + '\geocodemerge.csv')
        print("\nA new file called 'geocodemerge.csv' has been added to the same folder as your original dataset.")
        '''
        create_csv(joindf, folder, '\geocodemerge.csv')
    elif response.lower() == 'no':
        yninput = True
    else:
        print('\nNot a valid response. Please type "yes" or "no". ')

print('\nDone. Feel free to close the program.')
sys.exit()