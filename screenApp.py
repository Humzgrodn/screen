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

#Setting variables
import os
os.environ['KIVY_GL_BACKEND'] = 'gl'
os.environ['KIVY_GRAPHICS'] = 'gles'


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
from kivy.logger import Logger
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.config import Config
Config.set("graphics", "show_cursor", 0)

#code needed to make the memory trace work
debug = True
import linecache
import tracemalloc

def display_top(snapshot, key_type='lineno', limit=10):
    snapshot = snapshot.filter_traces((
        tracemalloc.Filter(False, "<frozen importlib._bootstrap>"),
        tracemalloc.Filter(False, "<unknown>"),
    ))
    top_stats = snapshot.statistics(key_type)

    print("Top %s lines" % limit)
    for index, stat in enumerate(top_stats[:limit], 1):
        frame = stat.traceback[0]
        # replace "/path/to/module/file.py" with "module/file.py"
        filename = os.sep.join(frame.filename.split(os.sep)[-2:])
        print("#%s: %s:%s: %.1f KiB"
              % (index, filename, frame.lineno, stat.size / 1024))
        line = linecache.getline(frame.filename, frame.lineno).strip()
        if line:
            print('    %s' % line)

    other = top_stats[limit:]
    if other:
        size = sum(stat.size for stat in other)
        print("%s other: %.1f KiB" % (len(other), size / 1024))
    total = sum(stat.size for stat in top_stats)
    print("Total allocated size: %.1f KiB" % (total / 1024))
if debug == True:
    tracemalloc.start()

urlPage = 'https://ussproton.nl/files/foto/ditiseenbeetjeeenrarebestandsnaammaarzoishetlastigerteraden.php?QWACaIbr5bBnexpBa0Mj=ijheVgsq7tWhtUW0UafE&rtJMWzYjtEj0meQpXoKx=Tmml2CShQPlJGB8jcwWq&date=' + str(time.time()).replace(".", "")


# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

# Get the config
config = configparser.ConfigParser(interpolation=None)
fileDir = os.path.dirname(os.path.relpath(__file__)) + "/"
if str(fileDir) == "":
    config.read('config.ini')
else:
    config.read(str(fileDir) + 'config.ini')

page = urllib.request.urlopen(urlPage)
urlListStr = page.read().decode('utf-8')

urlList = configparser.ConfigParser(interpolation=None)

#only choose one of these 2
#urlList.read('url.ini')
urlList.read_string(urlListStr) #aan voor url van internet



#gloabals
FPS = int(config['other']['fps'])
screenTime = 0.0
photoTime = 0.0
currentAlbum = 0
albumCount = 3
photoCount = [0]*albumCount
currentPoster = 0
eventLabelHeight = 1000
prepareTime = 1 # the time in seconds (I think)
prepared = False
maxEventTextLength = int(config['start_screen']['max_scroll_text']) # fix for black scroll screen on Rpi, limits the displayed text to within the limits of Kivy.
photoUrlList = []
#set the screen managers
sm = ScreenManager() #used for the "main screen types (home/ slideshow/ poster)
pm = ScreenManager() #used to scroll through the pictures for the slideshow

#gives a normal timestamp for log
def log(string):
    time = datetime.datetime.now()
    time = str(time.strftime("%m/%d.%H:%M:%S.%f"))[:-4]
    Logger.info("timestamp: " + time +" "+ str(string))

#timeLog function: if you want to start a timer, give starStop = "start", this will log the startime, to end the timelog give the argument starStop = "stop"
# the id makes sure multiple timers can be run at the same time, and that 2 different strings can be logged for start/stop  of timer
startStopDict = {}
def timeLog(id, string, startStop = "start"):
    global startStopDict
    if startStop == "start":
        startTime = datetime.datetime.now()
        if id not in startStopDict:
            startStopDict[id] = startTime
            Logger.info("starttime: " + str(startTime.strftime("%m/%d.%H:%M:%S")) +" " + str(string))
            return

        else:
            oldStartTime = startStopDict[id]
            startTime = datetime.datetime.now()
            Logger.warning("starttime: id already exists ("+ str(id) +" "+ str(oldStartTime.strftime("%m/%d, %H:%M:%S"))+"), now overridden to " + str(startTime.strftime("%m/%d, %H:%M:%S")))
            return

    elif startStop == "stop":
        stopTime = datetime.datetime.now()
        try:
            startTime = startStopDict[id]
        except:
            Logger.info("no id: "+ str(stopTime) + str(string))
            return
        del startStopDict[id]
        delta = stopTime - startTime
        delta = str(delta)[:-4]
        Logger.info("timedelta: " + delta +" "+ str(string))
        return

    elif startStop != "start" and startStop != "stop":
        Logger.warning("timedelta: no start/stop" + str(string))

def updateGlobals():
    if debug == True:
        snapshot = tracemalloc.take_snapshot()
        display_top(snapshot)
    global photoCount, albumCount, config, urlListStr, urlList, prepareTime, maxEventTextLength, photoUrlList, urlPage

    # Get the config
    config = configparser.ConfigParser(interpolation=None)
    fileDir = os.path.dirname(os.path.relpath(__file__)) + "/"
    if str(fileDir) == "":
        config.read('config.ini')
    else:
        config.read(str(fileDir) + 'config.ini')
    urlPage = 'https://ussproton.nl/files/foto/ditiseenbeetjeeenrarebestandsnaammaarzoishetlastigerteraden.php?QWACaIbr5bBnexpBa0Mj=ijheVgsq7tWhtUW0UafE&rtJMWzYjtEj0meQpXoKx=Tmml2CShQPlJGB8jcwWq&date=' + str(time.time()).replace(".", "")
    page = urllib.request.urlopen(urlPage)
    urlListStr = page.read().decode('utf-8')
    urlList.read_string(urlListStr) #aan voor url van internet
    log("updated globals")
    #global urlList
    prepareTime = int(config['other']['prepare_time'])
    maxEventTextLength = int(config['start_screen']['max_scroll_text'])
    photoUrlList = urlList.options('photo_url')

    for album in range(albumCount):
        keyList = photoUrlList
        try:
            currentAlbumPhotos = int(keyList[keyList.index(str(album + 1) + '-1') - 1][len(str(album) + '-'):])
        except ValueError:
            currentAlbumPhotos = int(keyList[len(keyList)-1][len(str(album) + '-'):])
        photoCount[album] = currentAlbumPhotos

#magic to determine how many photo's are in an album
def getPhotoCount(album):
    return photoCount[album]

    
#gets the amount of posters
def getPosterCount():
    posterCount = urlList.options('poster_url')[-1]
    return int(posterCount)

#gets the date in isoformat
def getDate():
    return datetime.datetime.now().strftime("%d-%m-%Y")

#gets the time in isoformat, give seconds, minutes, or millis as an argument to change the detail
def getTime(resolution="minutes"):
    if resolution == "seconds":
        return datetime.datetime.now().isoformat()[11:19]
    elif resolution == "minutes":
        return datetime.datetime.now().isoformat()[11:16]
    elif resolution == "millis":
        return datetime.datetime.now().isoformat()[11:22]

#this gets the amount the window should scroll each frameupdate
def scroll(dt, scrollAmount):
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
    global maxEventTextLength
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
        log('Geen evenementen gevonden')
    for event in events:
        startDate = markup(event['start'].get('dateTime', event['start'].get('date'))[0:10], 'event_label_date') + '\n'
        eventTitle = markup(event['summary'], 'event_label_title') + '\n'
        try:
            eventDescription = markup(event['description'], 'event_label_description') + '\n'
            eventDescription = eventDescription.replace("[color=#" + config['event_label_description']['color'] + "]", "").replace("[/color]", "")
        except KeyError:
            eventDescription = markup('Geen omschrijving', 'event_label_description') + '\n'

        eventList = eventList + startDate + eventTitle + eventDescription + eventSeparator
        if len(eventList) > maxEventTextLength:
            log("breaking  event adding")
            break

    eventList = '\n\n' + eventList
    eventList = "[color=#" + config['event_label_description']['color'] + "]" + eventList + "[/color]"
    return eventList

#Gets the calendar id's, can be handy for determining the id's. This is not actively used but needed to configure the screen
def printCalendarId():
    log('Getting the calendars connected to this account')
    calendar_list = getService().calendarList().list().execute()

    for calendar in calendar_list['items']:
        log(calendar['summary'], calendar['id'])

#connects with the google api
def getService():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    fileDir = os.path.dirname(os.path.relpath(__file__)) + "/"
    if str(fileDir) != "":
        fileDir = fileDir + "/"
    if os.path.exists(fileDir + 'token.pickle'):
        with open(fileDir + 'token.pickle', 'rb') as token:
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
        with open(fileDir + 'token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('calendar', 'v3', credentials=creds)
    #service = build('calendar', 'v3', credentials=creds)

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
        updateGlobals()
        sm.get_screen('start_screen').birthdayUpdate()
        sm.get_screen('start_screen').eventUpdate()

    if nextScreenName == 'poster_screen':
        sm.get_screen('poster_screen').loadNewPoster()

    if nextScreenName  == 'photo_screen':
        global photoTime
        photoTime = 0
        timeLog("load photo", "start album load" , "start")
        sm.get_screen('photo_screen').nextAlbum()

    prepared = True

#The screen used to display the events and birthdays etc.
class StartScreen(Screen):
    scrollAmount = -1
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
            log("prepare for photo's")
        if float(config['start_screen']['time_spend']) < screenTime:
            nextScreen()
            return

        self.scroll = scroll(dt, self.scrollAmount)
        self.scrollAmount = self.scroll
        self.dateText = getDate()
        self.timeText = getTime()
        
    def eventUpdate(self):
        self.scrollAmount = 1
        logging.info("Updating events")
        self.eventText = getEventList()
        
    def birthdayUpdate(self):
        logging.info("Updating birthdays")
        self.birthdayText = markup(getBirthdayList(), 'birthday_label')


#removes the current photos from the photoscreenmanager and adds the new ones




#this is the code for changing photos in albums, I think something's wrong here and the code is still wip
class PhotoScreen(Screen):
    global currentAlbum
    
    dateText = markup(getDate(), 'photo_date_label')
    timeText = markup(getTime("minutes"), 'photo_time_label')

    def nextAlbum(self):
        global currentAlbum
        
        currentAlbum += 1
        
        if currentAlbum > 2: #maak een albumcount functie
            currentAlbum = 1
        
        logging.info("Loading photo album " + str(currentAlbum))
        #remove all screens/ photos from the manager, ugly but works
        for removedScreen in pm.screen_names:
            pm.remove_widget(pm.get_screen(removedScreen))

        
        #Initialise the first 3 photos
        for i in range(int(config['photo_screen']['buffer'])):
            photoScreen = Screen(name='photo_' + str(i + 1))
            #add the photo to the screen
            photoScreen.add_widget(AsyncImage(source=urlList['photo_url'][str(currentAlbum) + '-' + str(i + 1)][1:-1].replace(' ', '%20'), allow_stretch=True))
            #add the screen to the screenmanager
            pm.add_widget(photoScreen)
        timeLog('load photo',"Photo album loaded" , "stop")

    def nextPhoto(self):
        global currentAlbum

        #first set the new photo
        pm.current = pm.next()
        currentPhoto = int(pm.current[6:])
        #then remove the old one the if statement for when this function is accidentally called to early
        #if currentPhoto != 1:
        pm.remove_widget(pm.get_screen('photo_' + str(currentPhoto - 1)))

        #then if the whole album isn't loaded:
        if currentPhoto + int(config['photo_screen']['buffer']) - 2 < getPhotoCount(currentAlbum):
            photoScreen = Screen(name='photo_' + str(currentPhoto + int(config['photo_screen']['buffer']) - 1))
            #add the photo to the screen
            photoScreen.add_widget(AsyncImage(source=urlList['photo_url'][str(currentAlbum) + '-' + str(currentPhoto + int(config['photo_screen']['buffer']) - 1)][1:-1].replace(' ', '%20'), allow_stretch=True))
            #add the screen to the screenmanager
            pm.add_widget(photoScreen)


    def frameUpdate(self, dt):
        global photoTime, prepared, currentAlbum
        photoTime += dt
        #loading a new photo
        if pm.current == 'photo_' + str(getPhotoCount(currentAlbum)) and not prepared:
            prepareScreen()

        if int(config['photo_screen']['time_spend']) < photoTime:
            
            #If the last photo is shown go to next screen
            if pm.current == 'photo_' + str(getPhotoCount(currentAlbum)):
                photoTime = 0
                nextScreen()
                #pm.remove_widget(pm.current) #misschien nodig? niet vergeten iig
                return

            photoTime = 0
            #going to the next photo
            self.nextPhoto()
            

                        
        self.ids.date_label.text = getDate()
        self.ids.time_label.text = getTime("minutes")
        



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

        self.posterUrl = urlList['poster_url'][str(currentPoster)][1:-1].replace(' ', '%20')
        log('new poster loaded: ' + self.posterUrl)
        
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
    updateGlobals()
    Window.fullscreen = True
    MainApp().run()
    
if __name__ == '__main__':
    main()
