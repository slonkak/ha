#!/usr/bin/python3

# TODO: GUI, tiled buttons on multiple rows.  Last button split into settings/rescan.  Constant updating of lock status.  Settings has url, token, refresh rate, save, cancel.

import os, yaml, math, datetime, time
import tkinter as tk                        # GUI
import screeninfo                           # Work with multiple monitors

from homeassistant_api import Client        # Access HomeAssistant API
from yaml import load                       # Read config file
from requests.exceptions import SSLError    # Catch https errors
from tkinter import messagebox              # TK messageboxes
from tkinter import font                    # GUI fonts

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

lowBattery = 30
refreshRate = 30000

#
# FUNCTIONS
#

def drawscreen():
    # Reset the timer for refreshing the screen
    if window.aid is not None:
        window.after_cancel(window.aid)

    # If any widgets exist in the window, delete them (needed for looping)
    for w in window.winfo_children():
        w.destroy()

    # Declare these outside of the try/catch so the values persist even
    # when the Client dies
    buttonw = 0
    buttonh = 0

    # Because Client() excepts when the API can't be accessed, catch it
    try:
        with Client(api_url, token) as client:
            # Grab the entire list of items managed by HA and pull out all
            # locks into a new dictionary, but the actual lock entities are
            # in the "entities" attribute, so further drill down to that
            locks = {key: value for key, value in client.get_entities()["lock"]}["entities"]

            # Calc button dimensions
            countlocks = len(locks)
            rowlen = int(math.ceil(countlocks/2))
            buttonw = int(screenw / rowlen)
            buttonh = int(screenh / 2)

            r=0
            c=0
            # Loop through all locks
            for k, v in locks.items():
                if "battery_level" in v.state.attributes:
                    if v.state.attributes["battery_level"] < lowBattery:
                        if v.state.state.lower() == "locked":
                            i = images[0]
                        else:
                            i = images[1]
                    else:
                        if v.state.state.lower() == "locked":
                            i = images[2]
                        else:
                            i = images[3]
                else: # Can't read battery level
                    if v.state.state.lower() == "locked":
                        i = images[4]
                    else:
                        i = images[5]

                tk.Button(window, text=v.state.attributes["friendly_name"].replace(" ","\n"), font=f, image=i, bg=window['bg'], activebackground=window['bg'], width=buttonw, height=buttonh, padx=0, pady=0, bd=0, compound="c", command=lambda l=v.state.entity_id: togglelock(l)).grid(row=r, column=c, ipadx=0, ipady=0, sticky="nsew")
                c = c+1 if c<rowlen-1 else 0
                r = r+1 if c==0 else r

    except SSLError as e:
        print("* * * * * * * * * *\n" + str(datetime.datetime.now()) + ": Error connecting to API.  Is your HomeAssistant device powered on?\n* * * * * * * * * *\nDetails:\n" + str(e))

        # Set the screen to redraw after 3 seconds after error
        time.sleep(2)
        window.aid = window.after(1000, drawscreen)
        return

    # Draw the refresh button
    tk.Button(window, text="Refresh", font=f, image=images[6], bg=window['bg'], activebackground=window['bg'], width=buttonw, height=buttonh, padx=0, pady=0, bd=0, compound="c", command=lambda: redraw()).grid(row=r, column=c, ipadx=0, ipady=0, sticky="nsew")

    # Set the screen to redraw after refreshRate time so any changes
    # to locks are shown
    window.aid = window.after(refreshRate, drawscreen)

def togglelock(eid):
    try:
        with Client(api_url, token) as client:
            l = client.get_entity(entity_id=eid)
            #d = client.trigger_service(domain="lock", service="unlock", service_data="{\"target\": {\"entity_id\": eid}}")
            #print(d)
            drawscreen()
    except SSLError as e:
        print("error")

def redraw():
    drawscreen()

def get_mon_from_xy(x,y):
    monitors = screeninfo.get_monitors()

    for m in reversed(monitors):
        if m.x <= x <= m.width+m.x and m.y <= y <= m.height+m.y:
            return m
    return monitors[0]


#
# MAIN PROGRAM
#

if __name__ == '__main__':                  # Make sure we're not imported

    # Read the params from the config file
    config = yaml.safe_load(open("config/ha.yaml",'r'))
    token = config.get("token")
    api_url = config.get("api_url")
    refresh = config.get("refresh")

    # Die if the config variables couldn't be read
    assert api_url,token is not None

    # Draw the main window
    window = tk.Tk()
    window.attributes('-fullscreen', True)
    window.title("Door Manager")
    window.aid = None
    cur_mon = get_mon_from_xy(window.winfo_x(), window.winfo_y())
    screenw = cur_mon.width
    screenh = cur_mon.height
    f = font.Font(weight="bold", size=50)

    # Create list of images so they don't get garbage collected by
    # stupid Python
    images = []
    images.append(tk.PhotoImage(file="images/lock-red.png"))
    images.append(tk.PhotoImage(file="images/unlock-red.png"))
    images.append(tk.PhotoImage(file="images/lock-green.png"))
    images.append(tk.PhotoImage(file="images/lock-green.png"))
    images.append(tk.PhotoImage(file="images/lock-yellow.png"))
    images.append(tk.PhotoImage(file="images/lock-yellow.png"))
    images.append(tk.PhotoImage(file="images/refresh.png"))

    drawscreen()


    window.mainloop()
