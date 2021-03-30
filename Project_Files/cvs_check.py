"""
Completed on Mar 29 2021
@author: Katerina Petrakis and Dimitri Petrakis
"""

#Timing - used to check for updates at a regular interval
import time
import threading

#Emailing - used to set up a connection with email as well as all its contents
import smtplib

#HTML generation - used to send in email as body
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

#JSON - used to read the CVS dictionary of info from link
import json

# Page fetching from url
# The try block attempts to import the Python3-compatible version
# of the import allows for the code to open a given link.
# If that import is not found, import the Python2-compatible version.
try: 
    from urllib.request import urlopen 
except ImportError:
    # Works on python 2.7
    from urllib2 import urlopen

# System - used in input_check() as sys.exit()
import sys

# Used to copy single inputted state to 1:1 mapped indices for zipping cities and states together
from itertools import cycle

#---------------------------------------------------------------------------------end imports---------------------------------------------------------------------------------


#---------------------------------------------------------------------------------begin user input----------------------------------------------------------------------------
"""
      ___  __   ___   /
|__| |__  |__) |__   / 
|  | |___ |  \ |___ .  
                       
""" 
'''                     
# Input the two-letter state abbreviation of states you are lookin for an appointment in ;
# For expample, if your state is Rhode Island, STATEINI = ['RI']
# If you wish to check multiple states, input them as follows: STATEINI = ['MA','NY','IL']
'''
STATEINI = ['MA']  

'''
If you would like to be notified of statewide appointments, leave this field empty. 
If you would like to only be notified of specific cities, list them below. 
Make sure all listed cities are from the same state as the one input above. 
For instructions on checking for specific cities in a multiple of states, please refer to the README located on github.
For a full list of valid cities, visit cvs.com/immunizations/covid-19-vaccine.
'''
CITIES = []

'''
Below you must set up a account from which to send alerts and an email that receives those alerts.
The sender and receiver can be the same email account, but it is not necessary. 
Be sure to check the spam folder.

Remember that you will have to lower your security settings if using a gmail account, and may have to so something similar with other accounts. 
'''
#email provider must be one of the following: gmail, outlook, yahoo, att, comcast, verizon
EMAIL_PROVIDER = ''
#Note: The SENDER email must have the same provider as the EMAIL_PROVIDER. The RECEIVER provider may be different.

# The account that SENDS the email. It must be in the following format: SENDER = "example@provider.com"
SENDER = ""
# The password for the SENDER account. Example: PASSWORD = "yourpasswordhere"
# Note that this code only runs locally on your machine, and that the password input will not be posted online anywhere or visible to anyone besides you, the user.
PASSWORD = ""
# The email account that receives the email alerts. It must be of the form RECEIVER = "example@example.com"
RECEIVER = "" 

# How often to refresh the page, in seconds
UPDATE_TIME = 60.0

"""
 __  ___  __   __  
/__`  |  /  \ |__) 
.__/  |  \__/ |    
"""
#--------------------------------------------------------------------------------end user input----------------------------------------------------------------------------

    
#----------------------------------------------------------------------- begin global varialbes----------------------------------------------------------------------------

# Link to all available appointments as a JSON
link ="https://www.cvs.com/immunizations/covid-19-vaccine/immunizations/covid-19-vaccine.vaccine-status.json?vaccineinfo"

# Make the initial set of available appointments to be empty
previous_appointments = set()

# Makes user-inputted string variables case-insensitive.
STATEINI = [x.upper() for x in STATEINI]
CITIES = [x.upper() for x in CITIES]
EMAIL_PROVIDER = EMAIL_PROVIDER.lower()

# In case where list of cities is not empty, and only one state is input, populate the 1:1 mapping with that one state.
if(CITIES and len(STATEINI) == 1): 
    CORRESPONDING_CITIES_STATES = list(zip(CITIES, cycle(STATEINI)))
# In the statewide search(es) case, the user provides 1:1 mapping
CORRESPONDING_CITIES_STATES = list(zip(CITIES, STATEINI))

# Dictionary to get the server ID and port number for each email provider.
EMAIL_DICT = {'gmail'  : ('smtp.gmail.com',        587),
              'outlook': ('smtp-mail.outlook.com', 587),
              'yahoo'  : ('smtp.mail.yahoo.com',   587),
              'att'    : ('smpt.mail.att.net',     465),
              'comcast': ('smtp.comcast.net',      587),
              'verizon': ('smtp.verizon.net',      465)}

#------------------------------------------------------------------------ end global varialbes-----------------------------------------------------------------------------


#--------------------------------------------------------------------begin user input formatting checks--------------------------------------------------------------------

def input_check():
    """
    This function checks to confirm that the user input is of the correct form.
    Quits the program and displays error message upon bad input.
    """

    all_states = get_states()
    all_states_set = set(all_states)
    all_cities = get_cities(all_states)

    # Error if no state is entered.
    if (not STATEINI):
        sys.exit("\nYou must enter at least one state.\n")

    if (not set(STATEINI).issubset(all_states_set)):
        sys.exit("\nOne or more state inputs are invalid.\n")
    
    if(not all(city in all_cities for city in CITIES)):
        sys.exit("\nOne or more cities entered are not correct. Please go to https://www.cvs.com/immunizations/covid-19-vaccine and click your state to see a list of viable options.\n")

   
    # In the case in which cities array is not empty, i.e. the search is NOT statewide, further checks are carried out.
    if (CITIES): 
        cities_len = len(CITIES)
        state_len = len(STATEINI)

        # The cities list must either have exactly one state, indicating that all cities being checked are in the same state, 
        # OR each city must have a 1:1 match it its state if checking across multiple states.
        if(not (cities_len == state_len or  state_len == 1)):
            sys.exit("\nCity entry error. If all appointments you are searching are in the same state, only enter that one state." 
                + "If you are checking in multiple states, make sure you enter the same number of states as you have cities \n")
        

        cit, st = zip(*CORRESPONDING_CITIES_STATES)
        if(cities_len == state_len):
            # confirm that each city is in the corresponding state listed
            for i in range(cities_len): 
                if(CITIES[i] not in get_cities(list(st))):
                      sys.exit("\nCity entry error. At least 1 City/State pairing is incorrect \n")

        if(state_len == 1):
            # confirm that each city is in the state listed           
            for i in range(cities_len):
                if(CITIES[i] not in get_cities(list(st))):
                    sys.exit("\nCity entry error. At least 1 City listed is not in the specified state. \n")



    if(not isinstance(UPDATE_TIME, (float,int))):
        sys.exit("\nUPDATE_TIME variable type must be a number.\n")


    if(not (isinstance(SENDER,str) and isinstance(PASSWORD,str) and isinstance(RECEIVER,str))):
        sys.exit("\nThe SENDER, PASSWORD, and RECEIVER fields must all be strings.\n")

    if(not ('@' in RECEIVER and '.' in RECEIVER)):
        sys.exit("\nThe RECEIVER must be a proper email containing an '@' character and a '.' character .\n")


    #The SENDER email must have the same provider as the EMAIL_PROVIDER
    at_ind = SENDER.find('@')
    dot_ind = SENDER.find('.')
    sender_suffix = SENDER[at_ind +1 : dot_ind]
    if(not sender_suffix  == EMAIL_PROVIDER):
        sys.exit("\nThe SENDER email must come from the same provider as the EMAIL_PROVIDER variable.\n")

#-------------------------------------------------------------------end user input formatting checks-----------------------------------------------------------------------


#----------------------------------------------------------------------------begin functions-------------------------------------------------------------------------------

def get_dictionary_from_link(link):
    # Get appointments as a single text string from the given link
    text = urlopen(link).read().decode("UTF-8")
    # Convert the string into a dictionary to access the bookings
    return json.loads(text) #returns the dictionary


def get_cities(list_states):
    """
    Given a list of states, this function returns a sorted list of all cities that appear in that state.
    """
    all_cities = []
    dictionary = get_dictionary_from_link(link)

    for state in list_states:
        state_dictionaries = dictionary["responsePayloadData"]["data"][state]
        for city_state_status in state_dictionaries:
            all_cities.append(city_state_status["city"])
    return sorted(all_cities)

def get_states():
    """
    This function returns a sorted list of states offered by the CVS website.
    """
    dictionary = get_dictionary_from_link()
    states = dictionary["responsePayloadData"]["data"].keys()
    return sorted(states)


def create_csv():
    """
    Creates an output string in a csv format with the Name,City,State,Color,Country
    fields. Remains unused in the project's current form but may be used to print out a csv
    that can then be used plot markers on something like ZeeMaps or generate a GeoJson on geocod.io
    """
    dictionary = get_dictionary_from_link(link)
    out = 'Name,City,State,Color,Country\n'
    all_states = get_states()
    for state in all_states:
        state_dictionaries = dictionary["responsePayloadData"]["data"][state]
        for city_state_status_dict in state_dictionaries:
            city = city_state_status_dict["city"]
            status = city_state_status_dict["status"]
            #out += f"{city},{city},{state},{'green' if status == 'Available' else 'red'},US\n" #comment this line back in to use,mcurrently only works in python 3
    # print(out) # can be commented back in if you with to print csv string to console
    return out


def get_available_appointments():
    """
    Gets the set of user specified cities (either specific cities, or all cities given a list of states)
    that have available appointments

    Container type from website = Dict[Str: Dict[Str: Dict[Str: List[Dict[Str: Str]]]]]
    Dict 1 keys = ["responsePayloadData", "responseMetaData"]
    Dict 2 keys = ["currentTime", "data", "isBookingCompleted"]
    Dict 3 keys = ["NY", "CA", "SC", "MA", "FL",  ... all state abbreviations]
    Dict 4 = {"city": "NEW YORK", "state": state abbreviation ex: "NY", "status": either "Available" or "Fully Booked"}
    """
    available_appointments = set()

    dictionary = get_dictionary_from_link(link)

    for state in STATEINI:
        # Get the list of dicts with city, state, and status
        state_dictionaries = dictionary["responsePayloadData"]["data"][state]

        # city_state_status_dict is of the form {"city":"ELEELE","state":"HI","status":"Available"}
        # state_dictionaries is a list of every city_state_status for a given state

        # Index into the list and add to available appointments (nothing will happen if it is a duplicate, as available appointments is a set)
        for city_state_status_dict in state_dictionaries:
            # Add to available appointments only if appointment is available

            # In the case where the CITIES array is empty, add to the appointments set all cities with available appointment.
            if(not CITIES):
                if city_state_status_dict["status"] == "Available":
                    available_appointments.add(city_state_status_dict["city"])  # .add makes it a SET and not a list
            # In the case where the user specifies which cities they want to be notified of, only add to the appointments set if 
            # an appointment is available AND if that city is one of the ones user wants to be notified of.
            else: #when we do list specific cities
                if ((city_state_status_dict["city"], state) in CORRESPONDING_CITIES_STATES and city_state_status_dict["status"] == "Available"):
                    available_appointments.add(city_state_status_dict["city"])
            
    return available_appointments


def send_email(msg):
    """
    Login via STMP and send an email with the given message and with the given email provider
    """

    # Get SMTP server ID and port for the given email type
    # SeverID sets which email type to sent from
    # Port used for web protocols, 587 for default web (supports TLS) or 465 for SSL
    serverID, port = EMAIL_DICT[EMAIL_PROVIDER]

    # Establish SMTP Connection
    s = smtplib.SMTP(host=serverID, port=port)

    # Start TLS based SMTP Session
    s.starttls()

    # Login using user-provided Email ID & PASSWORD
    s.login(SENDER, PASSWORD)

    # To Create Email Message in Proper Format
    m = MIMEMultipart()

    # Set Email Parameters
    m['From'] = SENDER
    m['To'] = RECEIVER
    m['Subject'] = "New Appointment(s) Available! - Looking in " + collection_2_sentence(set(STATEINI))
    
    # Add Message To Email Body And Specify html type
    m.attach(MIMEText(msg, 'html'))

    # Send the Email
    s.sendmail(SENDER, RECEIVER, m.as_string())

    # Terminate the SMTP Session
    s.quit()


# Set 2 String Functions
# ----------------------------------------------------------------------------------------------------------------------

def collection_2_listed_string(elems):
    """
    Given a Container (i.e. a Set, List, etc.) of strings, 
    returns an HTML string wherein each item has its own line, and all items are in alphabetical order.

    This will be used to help format and contsruct the email text body (as an HTML)
    in the build_email_msg function.
    """

    # if the set is empty, output that no appointments are available
    if not elems:
        return 'None Available' + '<br>'

    # Initialize emtpy string
    string = ""  

    # Sorts the set (converts to a list)
    sort = sorted(elems)

     # Loop over each city in the set and append the city to the HTML string
    for city in sort:                  
        string += city + '<br>'   

    # Returns the HTML string of a list of cities
    return string  


def collection_2_sentence(elems):
    """
    Given a Container (i.e. a Set, List, etc.) of strings, 
    returns a string wherein each item is listed as a sentence in alphabetical order.

    Ex1: {"LIVERPOOL"} -> LIVERPOOL
    Ex2: ["LIVERPOOL", "KINGSTON"] -> KINGSTON and LIVERPOOL
    Ex3: {LIVERPOOL", "KINGSTON", "BROOKLYN"} -> BROOKLYN, KINGSTON, and LIVERPOOL
    """

    # Gets the number of cities in the set
    num_cities = len(elems)

    # Sorts the set (converts to a list)
    cities = sorted(elems)


    # If the set is empty, return None
    if not elems:
        return 'None Available'
    # If the set has one city, return the string of the one city
    elif num_cities == 1:
        return cities[0]
    # If the set has two cities, return the two cities as "city1 and city2"
    elif num_cities == 2:
        return cities[0] + ' and ' + cities[1]

    # If the set has three or more cities, return cities like saying a list in a sentence "cityA, ... cityY, and cityZ"
    else:
        # Initialize emtpy string
        string = ""  

        # Loop over each city in the set except for the last one. 
        for i in range(num_cities - 1):  
            # Get the city string from the range of numbers and  # Add the city to the string with a comma and space
            string += cities[i] + ', '
        # Add the final city with an "and" and return the string
        return string + 'and ' + cities[-1]



# ------------------------calculation to determine which appointments found are new, and which are old.-----------------------------------------
def calculate_appointments(new_set, old_set):
    """
    Calculate different appointment types.  
    Used for making useful distinctions in the email message.

    new_set will be the fresh set of all available appointments at a given interval
    old_set will the previous appointments variable getting passed in.

    Ex1: Addition of HONEOYE
    new_set = {'LIVERPOOL', 'BROOKLYN', 'HONEOYE', 'KINGSTON'}
    old_set = {'LIVERPOOL', 'BROOKLYN', 'KINGSTON'}
    returns ->->
    new_appointments = {'HONEOYE'}
    all_appointments = {'LIVERPOOL', 'BROOKLYN', 'KINGSTON', HONEOYE}

    Ex2: No Changes
    new_set = {'LIVERPOOL', 'BROOKLYN', 'HONEOYE', 'KINGSTON'}
    old_set = {'LIVERPOOL', 'BROOKLYN', 'HONEOYE', 'KINGSTON'}
    returns ->->
    new_appointments = set() (empty set)
    all_appointments = {'LIVERPOOL', 'BROOKLYN', 'HONEOYE', 'KINGSTON'}

    """

    new_appointments = new_set.difference(old_set)          # set of All appointments minus set of Old appointments yields the set of New appointments
    old_appointments = new_set.intersection(old_set)        # New intersect Old. yields those appointments that  (intersect is equivalent the overlap in a venn diagram)
    return new_appointments, old_appointments               # Return new sets


def build_email_msg(new_appointments, all_appointments):
    """
    Given the set of new and all appointments, builds an HTML 
    string that will then be used in the email body.
    """
    # Initialize empty string
    out = ''
    # Adds New Appointments header
    out += ("<h3>New Appointments:</h3>")
   # Adds list of new appointments
    out += collection_2_listed_string(new_appointments)

    out += '\n<br>Go to https://www.cvs.com/immunizations/covid-19-vaccine to book an appointment.'
    
    # Adds All Appointments header
    out += ("<h3>All Available Appointments:</h3>")
    # Adds list of all appointments
    out += collection_2_listed_string(all_appointments) + '\n\n'

    return out


# ----------------------------------------------------------------------------------------------------------------------

def check_cvs(previous_appointments):
    """
    This function repeatedly reads the CVS website, and if any appointments are available in your state, it emails you.

    Terminology definitions:
    previous_appointments = set of available cites from previous check. is the empty set on the first update iteration when the program is run
    fresh_appointments = set of available cities after checking the link
    new_appointments = set of cities available that are available now but not in the previous check
    old_appointments = set of cities available that are available now but were also available in the previous check

    Note: old_appointments is currently not used in any meaningful way but is there for further customization
    """

    # Get all available appointments from the CVS website
    fresh_appointments = get_available_appointments()
    # Calculate different appointment types.  Used for making useful distinctions in the email message
    new_appointments, old_appointments = calculate_appointments(fresh_appointments, previous_appointments)

    # Sets the email as an HTML string to sent to the user
    email_message = build_email_msg(new_appointments, fresh_appointments)

    # send_email(email_message)      # Used for testing. This would send one email at every UPDATE iteration


    # Useful information to print to the terminal for some visuals
    brk = "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
    print(brk)
    print("Looking for appointments in [" + collection_2_sentence(set(STATEINI)) + "] at " + str(time.strftime('%H:%M:%S', time.localtime())) + '\n')


    # If there is a new city with appointments available that wasn't available in the last check, triggers an email send.
    if new_appointments:
   
        # Send email to user with given message
        send_email(email_message)

        # Notfify user in terminal.
        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Found an appointment!!! Email sent to " + RECEIVER + '\n\n')

    # Used for testing but also can print all cities on each check of the function if desired
    print("New Appointments: \n" + collection_2_sentence(new_appointments) + "\n")
    # print("Old Appointments:            ", collection_2_sentence(old_appointments))
    print("All Available Appointments: \n" + collection_2_sentence(fresh_appointments) + '\n' + brk + '\n\n')

    # Returns updated set of appointments to be inputted as previous_appointments in the next function run
    return fresh_appointments

#------------------------------------------------------------------------ end funcions----------------------------------------------------------------------------



#----------------------------------------------------------------------------main----------------------------------------------------------------------------------
if __name__ == '__main__':

    input_check()

    while True:
        try:
            previous_appointments = check_cvs(previous_appointments)
            time.sleep(UPDATE_TIME)
        except KeyboardInterrupt:
            break