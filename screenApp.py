#Author: Paul Bokslag, Ties Bakker
#In name of U.S.S. Proton 2019

from __future__ import print_function
import datetime
import pickle
import logging
import os.path
import configparser
import io
import time
import math
import urllib.request


from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from kivy.core.window import Window
from kivy.loader import Loader
from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.uix.relativelayout import RelativeLayout
from kivy.properties import StringProperty
from kivy.properties import NumericProperty
from kivy.properties import BooleanProperty
from kivy.uix.image import AsyncImage
from kivy.uix.image import Image

from kivy.uix.screenmanager import ScreenManager, Screen


#from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

# Get the config
config = configparser.ConfigParser(interpolation=None)
config.read('config.ini')


#page = urllib.request.urlopen('https://ussproton.nl/files/foto/ditiseenbeetjeeenrarebestandsnaammaarzoishetlastigerteraden.php?QWACaIbr5bBnexpBa0Mj=ijheVgsq7tWhtUW0UafE&rtJMWzYjtEj0meQpXoKx=Tmml2CShQPlJGB8jcwWq')
#urlListStr = page.read().decode('utf-8')

#print(urlListStr)

urlList = configparser.ConfigParser(interpolation=None)


urlList.read('url.ini')
#urlList.read_string(urlListStr)



#gloabals
FPS = int(config['other']['fps'])
scrollAmount = 1.0
screenTime = 0.0
photoTime = 0.0
currentAlbum = 0
albumCount = 3
currentPoster = 0
eventLabelHeight = 1000
prepareTime = 1 # the time in seconds (i  think)
prepared = False

#set the screen managers
sm = ScreenManager() #used for the "main screen types (home/ slideshow/ poster)
pm = ScreenManager() #used to scroll through the pictures for the slideshow

#magic to determine how many photo's are in an album
def getPhotoCount(album):
    keyList = urlList.options('photo_url')
    try:
        currentAlbumPhotos = int(keyList[keyList.index(str(album + 1) + '-1') - 1][len(str(album) + '-'):])
    except ValueError:
        currentAlbumPhotos = int(keyList[len(keyList)-1][len(str(album) + '-'):])
        
    return currentAlbumPhotos
    
#gets the amount of posters
def getPosterCount():
    posterCount = urlList.options('poster_url')[-1]
    return int(posterCount)

#gets the date in isoformat
def getDate():
    return datetime.datetime.now().isoformat()[0:10]
    
#gets the time in isoformat, give seconds, minutes, or millis as an argument to change the detail
def getTime(resolution="seconds"):
    if resolution == "seconds":
        return datetime.datetime.now().isoformat()[11:19]
    elif resolution == "minutes":
        return datetime.datetime.now().isoformat()[11:16]
    elif resolution == "millis":
        return datetime.datetime.now().isoformat()[11:22]
    
#this gets the amount the window should scroll each frameupdate
def scroll(dt):
    global scrollAmount
    if scrollAmount < 0:
        scrollAmount = 1
    else:
        scrollAmount -= dt*int(config['start_screen']['speed'])/eventLabelHeight
    return scrollAmount

#markup the text with different properties from the config file. Kivy has better ways to handle this, but I didn't know about them when I wrote this code. This could be an improvement for later.
def markup(string, labelId): #the label id should match the id in the config.ini file

    if config[labelId]['bold'] == 'yes':
        string = '[b]' + string + '[/b]'
    
    if config[labelId]['italic'] == 'yes':
        string = '[i]' + string + '[/i]'
    
    if config[labelId]['underlined'] == 'yes':
        string = '[u]' + string + '[/u]'
        
    if config[labelId]['strikethrough'] == 'yes':
        string = '[s]' + string + '[/s]'
        
    string = '[color=#' + config[labelId]['color'] + ']' + string + '[/color]'
    string = '[size=' + config[labelId]['size'] + ']' + string + '[/size]'

    return string

#gets the birthdays from the google calendar
def getBirthdayList():
    birthdayList = ''
    # Call the Calendar API
    now = (datetime.datetime.now() + datetime.timedelta(days=-1)).isoformat() + 'Z' # 'Z' indicates UTC time why the -1
    nowPlusHour = (datetime.datetime.now() + datetime.timedelta(hours=1)).isoformat() + 'Z'
    #HIER WORDEN DE VERJAARDAGEN OPGEHAALD
    birthdayResults = getService().events().list(calendarId='cus9h91mlj8ck2t07n8q69hgeg@group.calendar.google.com', #'primary' is alle, hier moet de verjaardagscalender id staan.
                                        timeMin=now,
                                        timeMax=nowPlusHour,
                                        singleEvents=True,
                                        orderBy='startTime').execute()
                                        
                                        
                                        
    birthdays = birthdayResults.get('items', [])
    birthdayList = "Vandaag jarig: \n"
    for birthday in birthdays:
        birthdayList = birthdayList + '- ' + birthday['summary'] + '\n'
        
    return birthdayList

#gets the event list from the google calendar
def getEventList():
    eventSeparator = markup(config['event_label_separation']['string'], 'event_label_separation') + '\n'
    eventList = eventSeparator
    
    # Call the Calendar API
    now = datetime.datetime.now().isoformat() + 'Z' # 'Z' indicates UTC time
    maxInterval = (datetime.datetime.now() + datetime.timedelta(weeks=int(config['start_screen']['maximum_time']))).isoformat() + 'Z'
    
    #HIER WORDEN DE EVENEMENTEN OPGEHAALD
    eventResults = getService().events().list(calendarId='bestuurproton@gmail.com', #hetzelfde als verjaardag maar dan met evenementen
                                        timeMin=now,
                                        timeMax=maxInterval,
                                        maxResults=int(config['start_screen']['maximum_events']),
                                        singleEvents=True,
                                        orderBy='startTime').execute()
    events = eventResults.get('items', [])
    

    if not events:
        print('Geen evenementen gevonden')
    for event in events:
        startDate = markup(event['start'].get('dateTime', event['start'].get('date'))[0:10], 'event_label_date') + '\n'
        eventTitle = markup(event['summary'], 'event_label_title') + '\n'
        try:
            eventDescription = markup(event['description'], 'event_label_description') + '\n'
        except KeyError:
            eventDescription = markup('Geen omschrijving', 'event_label_description') + '\n'
        
        eventList = eventList + startDate + eventTitle + eventDescription+ eventSeparator
        
    eventList = '\n\n' + eventList    
        
    return eventList
    
#Gets the calendar id's, can be handy for determining the id's. This is not actively used but needed to configure the screen
def printCalendarId():
    print('Getting the calendars connected to this account') 
    calendar_list = getService().calendarList().list().execute()

    for calendar in calendar_list['items']:
        print(calendar['summary'], calendar['id'])
    
#connects with the google api
def getService():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('calendar', 'v3', credentials=creds)
    service = build('calendar', 'v3', credentials=creds)

#sets the next screen
def nextScreen():
    global screenTime, prepared
    prepared = False
    screenTime = 0
    logging.info("Changing to the " + sm.next())
    sm.current = sm.next()

def prepareScreen():
    nextScreenName = sm.next()
    logging.info("now preparing: " + str(nextScreenName))
    global prepared
    if nextScreenName == 'start_screen':
        sm.get_screen('start_screen').birthdayUpdate()
        sm.get_screen('start_screen').eventUpdate()

    if nextScreenName == 'poster_screen':
        sm.get_screen('poster_screen').loadNewPoster()

    if nextScreenName  == 'photo_screen':
        global photoTime
        photoTime = 0
        nextAlbum()
        print("next album loaded")

    prepared = True

def log(string, type="notification"):
    logging.info("[" + getDate() + " " + getTime("millis") + "] " + str(string))

#The screen used to display the events and birthdays etc.
class StartScreen(Screen):
    #Kivy has two ways of changing properties in the kivy file, and I think these ....Properties work the best and are clear. Maybe for some cases another way would be better (using objects maybe)
    birthdayText = StringProperty()
    birthdayBackgroundColor = StringProperty()
    eventBackgroundColor = StringProperty()
    backgroundUrl = StringProperty()
    birthdayUrl = StringProperty()
    header = StringProperty()
    

    dateText = StringProperty()
    timeText = StringProperty()
    eventText = StringProperty()
    scroll = NumericProperty()
    contentLabelHeight = NumericProperty()
    #printCalendarId()
    
    header = markup(config['header']['text'], 'header')
    backgroundUrl = config['url_files']['start_background']
    birthdayUrl = config['url_files']['birthday_background']
    birthdayBackgroundColor = '#' + config['background_color']['birthday_color']
    eventBackgroundColor = '#' + config['background_color']['event_color']

    #sets the total height of the label displaying the text
    def setEventLabelHeight(self, h):
        global eventLabelHeight
        eventLabelHeight = h + 200 #200 pixels padding to read the last event description
        
    #updates every frame
    def frameUpdate(self, dt):
        global prepared

        #when it's time, change to the next screen
        if float(config['start_screen']['time_spend']) < (screenTime + prepareTime + 4) and not prepared:
            prepareScreen()
            print("prepare for photo's")
        if float(config['start_screen']['time_spend']) < screenTime:
            nextScreen()
            return
            
        self.scroll = scroll(dt)
        self.dateText = markup(getDate(), 'start_date_label')
        self.timeText = markup(getTime(), 'start_time_label')
        
    def eventUpdate(self):
        logging.info("Updating events")
        self.eventText = getEventList()
        
    def birthdayUpdate(self):
        logging.info("Updating birthdays")
        self.birthdayText = markup(getBirthdayList(), 'birthday_label')

#this empty class is needed because a screenmanager cannot be added to a screenmanager but only to a screen.
#class PhotoScreenManager(ScreenManager):
#    pass
    
#removes the current photos from the photoscreenmanager and adds the new ones
def nextAlbum():
    global currentAlbum
    
    currentAlbum += 1
    
    if currentAlbum > 3: #maak een albumcount functie
        currentAlbum = 1
    
    logging.info("Loading photo album " + str(currentAlbum))
    #remove all screens/ photos from the manager, ugly but works
    #print("Pre removal: " + str(pm.screen_names))
    for removedScreen in pm.screen_names:
        print("Screen to be removed: " + str(removedScreen))
        pm.remove_widget(pm.get_screen(removedScreen))
        print("After removal: " + str(pm.screen_names))

    
    #makes a new screen for each photo in the current photo album and adds this photo to the screen
    for i in range(0, getPhotoCount(currentAlbum)):
        #print('Adding a photoScreen called: photo_' + str(i + 1))
        photoScreen = Screen(name='photo_' + str(i + 1))
        #add the photo to the screen
        photoScreen.add_widget(AsyncImage(source=urlList['photo_url'][str(currentAlbum) + '-' + str(i + 1)][1:-1].replace(' ', '%20'), allow_stretch=True))
        #add the screen to the screenmanager
        pm.add_widget(photoScreen)

#this is the code for changing photos in albums, I think something's wrong here and the code is still wip
class PhotoScreen(Screen):
    global currentAlbum
    
    dateText = markup(getDate(), 'photo_date_label')
    timeText = markup(getTime(), 'photo_time_label')

    def frameUpdate(self, dt):
        global photoTime, prepared
        global currentAlbum
        #print("Now displaying: " + str(currentAlbum) + ", " + str(pm.current))
        photoTime += dt
        #loading a new photo
        if pm.current == 'photo_' + str(getPhotoCount(currentAlbum)) and not prepared:
            prepareScreen()

        if int(config['photo_screen']['time_spend']) < photoTime:
            
            #going to the poster screen and setting the new album
            if pm.current == 'photo_' + str(getPhotoCount(currentAlbum)): #heeeeel inefficient

                nextScreen()
                return
            photoTime = 0
            #going to the next photo
            pm.current = pm.next()
                        
        self.ids.date_label.text = markup(getDate(), 'photo_date_label')
        self.ids.time_label.text = markup(getTime(), 'photo_time_label')
        

#this is the posterscreen
class PosterScreen(Screen):
    global currentPoster
    posterBackgroundUrl = StringProperty()
    posterBackgroundUrl = config['url_files']['poster_background'].replace(' ', '%20')
    posterUrl = StringProperty()
    
    def loadNewPoster(self):
        global currentPoster
        currentPoster += 1
        
        if currentPoster > getPosterCount():
            currentPoster = 1
        
        logging.info("Loading poster " + str(currentPoster))
        self.posterUrl = urlList['poster_url'][str(currentPoster)][1:-1].replace(' ', '%20')
        print('new poster loaded: ' + self.posterUrl)
        
    def frameUpdate(self, dt):
        global screenTime, currentPoster, prepared
        screenTime += dt
        if int(config['poster_screen']['time_spend']) < screenTime + prepareTime and not prepared:
            prepareScreen()
        if int(config['poster_screen']['time_spend']) < screenTime:
            nextScreen()
        
#the main app
class MainApp(App):
    Builder.load_file('layout.kv')
    Loader.loading_image = 'chrome_dino.jpg'


    def frameUpdate(self, dt):
        global screenTime

        sm.get_screen(sm.current).frameUpdate(dt)
        screenTime += dt

    #adding all widgets to the screens and screenmanager
    def build(self):
        sm.add_widget(StartScreen(name='start_screen'))
        sm.add_widget(PhotoScreen(name='photo_screen'))
        sm.add_widget(PosterScreen(name='poster_screen'))
        

        sm.get_screen('photo_screen').add_widget(pm, 5) #index is higher so the photos are drawn under the clock
        
        Clock.schedule_interval(self.frameUpdate, 1.0 / FPS)
        
        #Initialising the start screen
        log("Initialising the start screen")
        sm.get_screen('start_screen').birthdayUpdate()
        sm.get_screen('start_screen').eventUpdate()
        
        return sm


def main():
    #Starting the gui
    Window.size = (1920, 1080)
    Window.fullscreen = True
    
    MainApp().run()
    
if __name__ == '__main__':
    main()
