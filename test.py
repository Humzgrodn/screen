from kivy.properties import StringProperty
from kivy.lang import Builder
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import ScreenManager, Screen

url = 'https://ussproton.nl/files/2019-02/smoelenposter-staand-2-.jpg'
sm = ScreenManager()

kv = Builder.load_string('''
<Controller>:
    AsyncImage:
        id: im
        source: root.photoUrl
        nocache: True
    Button:
        size_hint: 0.5, 0.5
        id: changeButton
        text: 'change photo source'
        on_press: root.nextUrl(im)
''')

class Controller(FloatLayout):
    photoUrl = StringProperty('https://ussproton.nl/files/2019-02/smoelenposter-staand-2-.jpg')
    
    def urlFunc(self):
        global url
        return url
        
    def nextUrl(self, im):
        pass 
    
class Test(App):
    def build(self):
        c = Controller()
        sm.add_widget(Screen(name='screen_1'))
        sm.remove_widget(sm.get_screen(sm.screen_names[0]))
        sm.add_widget(Screen(name='screen_1'))
        c.add_widget(sm)
        return c
        
if __name__=='__main__':
    Test().run()
