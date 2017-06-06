import math
import serial
import matplotlib.pyplot as plt
from threading import Thread
from Tkinter import *

class NormalFile:
    def __init__(self,f):
        self.file = f
    
    def readline(self):
        return self.file.readline()
        
    def inWaiting(self):
        return 1

#DB-conversion

transformation_list = [28000,29600,29800,30000,30200,30500,30900,31100,31300,31500,32000,35000,39000,42000,45000,
            49000,53000,57000,61000,68000,73000,82000,90000,100000,111000,125000,140000,155000,168000,180000,200000,230000,
            260000,300000,340000,380000,420000,460000,500000,550000,600000,680000,760000,840000,940000,
            1150000,1350000,1500000,1650000,1850000,2100000,2400000,2700000,3000000,3300000,3600000,3900000]

start_with_db = 40

MIN = -1
MAX = -2

def db_is_low(raw_value):
    return raw_value < transformation_list[0]
        
def db_is_high(raw_value):
    return raw_value > transformation_list[-1]

def transform_to_db(raw_value):
    if db_is_low(raw_value):
        return MIN
    if db_is_high(raw_value):
        return MAX

    for idx, val in enumerate(transformation_list):
        if(raw_value < val):
            return start_with_db + idx -1;
    return MIN

def findLastIndex(value,values): #TODO use the last max??
    index = 0
    for idx, val in enumerate(values):
        if value == val:
            index = idx
    return index
    
    #return values.index(value)

def calculate_RT_range(values):
    max_db = max(values)
    max_db_index = findLastIndex(max_db,values)
    for idx,val in enumerate(values[max_db_index:-1]):
        if val <= max_db - 30:
            print(idx)
            print(max_db_index) 
            return idx
    return 0


def waitForToken(token,f):
    while True:
        #if(f.inWaiting() > 0):
            line = f.readline()
            if token in line:
                return

def readValuesUntil(token,f):
    values = []    
    while True:
        #if(f.inWaiting() > 0):
            line = f.readline()
            if token in line:
                return values
            else:
                if ";" in line:
                    value = int(line.split(";")[1])
                    values.append(value)
    return values
                
def readValues(partial_token,f):
    waitForToken("Start_" + partial_token,f)
    return readValuesUntil("Stop_" + partial_token,f)    

def writeValues(partial_token,f,raw_data):
    f.write("Start_" + partial_token + "\n")
    for idx,raw in enumerate(raw_data):
        f.write(str(idx) + ";" + str(raw) + "\n")
    f.write("Stop_" + partial_token +  "\n")    



#Plotting

dBSPL = []
dBFS = []
RT_list = []

raw_dBSPL = []
raw_dBFS = []
raw_rt_values = []


def plot_dBSPL(): #0 - 95 -> seconds
    plt.grid(True)

    #TODO mark areas
       
    #TODO indicate!!!
    #plt.scatter([1,2],[70,75],s=70,c=colormap[categories]) 
    
    plt.plot(dBSPL,marker='.')
    plt.ylabel('dBSPL')
    plt.xlabel('seconds')
    plt.ylim(0,95)
    plt.xlim(0,10)
    locs,labels = plt.xticks()
    plt.xticks(locs,map(lambda x: "%g" % (x * 2),locs))
    plt.show()

def plot_dBFS():
    plt.plot(dBFS,marker='.')
    plt.grid(True)
    plt.ylabel('dBFS')
    plt.ylim(0,-60)
    plt.xlim(0,100)
    plt.fill([0,0,100,100],[0,-1,-1,0], zorder = 10,alpha=.3,facecolor='red')
    plt.fill([0,0,100,100],[-1,-5,-5,-1], zorder = 10,alpha=.3,facecolor='orange')
    plt.fill([0,0,100,100],[-5,-15,-15,-5], zorder = 10,alpha=.3,facecolor='yellow')
    plt.fill([0,0,100,100],[-15,-60,-60,-15], zorder = 10,alpha=.3,facecolor='green') 
    plt.gca().invert_yaxis()
    locs,labels = plt.xticks()
    plt.xticks(locs,map(lambda x: "%g" % (x * 200),locs))
    plt.xlabel('ms')
    plt.show()

def plot_RT():
    plt.plot(RT_list,marker='.')
    plt.grid(True)
    plt.ylabel('dBSPL')
    plt.ylim(0,95)
    plt.xlim(0,200)
    plt.xlabel('ms')
    locs,labels = plt.xticks()
    plt.xticks(locs,map(lambda x: "%g" % (x * 100),locs))
    plt.show()
    

#GUI

def clear():
    dBSPLText.delete(1.0,END)
    dBFSText.delete(1.0,END)
    RTText.delete(1.0,END)

import tkFileDialog

win = Tk()

Label(text="Serial Device",font=20).grid(row=0,column=1)
serialText = Entry(text = "COM6")
serialText.grid(row=0,column=2)


Label(text="dBSPL",font=20).grid(row=1,column=1)
dBSPLText = Text(height=4,width=40)
dBSPLText.grid(row=1,column=2)
Button(text="Plot",font="20",command=plot_dBSPL).grid(row=1,column=3)


Label(text="dBFS",font=20).grid(row=2,column=1)
dBFSText = Text(height=15,width=40)
dBFSText.grid(row=2,column=2)
Button(text="Plot",font="20",command=plot_dBFS).grid(row=2,column=3)

Label(text="RT30",font=20).grid(row=3,column=1)
RTText = Text(height=4,width=40)
RTText.grid(row=3,column=2)
Button(text="Plot",font="20",command=plot_RT).grid(row=3,column=3)

# Reading the file

def transformAndFilterDbValues(values):
    return filter(lambda x:x > 0,map(transform_to_db,values))

def readAndUpdatedBSPL(f):
    global dBSPL
    global raw_dBSPL
    dBSPLText.delete(1.0,END)
    raw_dBSPL = readValues("dBSPL",f)
    dBSPL = transformAndFilterDbValues(raw_dBSPL)
    for value in dBSPL:
        dBSPLText.insert(END, str(value) + " ")

def readAndUpdatedBFS(f):
    global dBFS
    global raw_dBFS
    dBFSText.delete(1.0,END)
    raw_dBFS = readValues("dBFS",f)
    dBFS = map(lambda x: ((x / 91667)-60),raw_dBFS)
    for idx,value in enumerate(dBFS):
        if(idx % 10 == 0 and idx != 0):
            dBFSText.insert(END, "\n")                    
        dBFSText.insert(END, str(value) + " ")

def readAndUpdateRT(f):
    global RT_list
    global raw_rt_values
    RTText.delete(1.0,END)
    raw_rt_values = readValues("RT",f)
    RT_list = transformAndFilterDbValues(raw_rt_values)
    RT = calculate_RT_range(map(transform_to_db,raw_rt_values))
    RTText.insert(END, str( float(RT) / float(10)) + " sec")

def readValuesThread():
    #f = open(tkFileDialog.askopenfilename())
    f = open(serialText.get(),"r")
    ser = NormalFile(f)
    print("waiting for data")
    readAndUpdatedBSPL(ser)
    readAndUpdatedBFS(ser)
    readAndUpdateRT(ser)

def readSerialValuesThread():
    ser = serial.Serial(port=serialText.get(),
            baudrate=921600,
            bytesize=serial.EIGHTBITS,
                        parity=serial.PARITY_NONE,
                        stopbits=serial.STOPBITS_ONE,
                        timeout=1,
                        xonxoff=0,
                        rtscts=0)
    print("waiting for data")
    readAndUpdatedBSPL(ser)
    readAndUpdatedBFS(ser)
    readAndUpdateRT(ser)



def readValuesFromSerialDevice():
    Thread(target = readSerialValuesThread).start()

def readValuesFromFile():
    Thread(target = readValuesThread).start()
    
def writeToFile():
    file = tkFileDialog.asksaveasfile(mode="w")
    writeValues("dBSPL", file, raw_dBSPL)
    writeValues("dBFS", file, raw_dBFS)
    writeValues("RT", file, raw_rt_values)

menubar = Menu(win)
submenu = Menu(win,tearoff=0)
submenu.add_command(label = "Load from serial port",command = readValuesFromSerialDevice)
submenu.add_command(label = "Load fom file",command = readValuesFromFile)
submenu.add_command(label = "Save data to file",command = writeToFile)


menubar.add_cascade(label = "Data",menu=submenu,underline=0,accelerator="Ctrl+l")
menubar.add_command(label = "Quit",command=win.quit,underline=0,accelerator="Ctrl+Q")
win.config(menu=menubar)
    
Button(text="Load serial",font="20",command=readValuesFromSerialDevice).grid(row=0,column=3)


Label(text="Lenght:").grid(row=4,column=1)
length_text = Entry()
length_text.grid(row=4,column=2)


Label(text="Width:").grid(row=5,column=1)
width_text = Entry()
width_text.grid(row=5,column=2)

Label(text="Height:").grid(row=6,column=1)
height_text = Entry()
height_text.grid(row=6,column=2)



start=1
end=11

C = 172


class ModiResult:
    def __init__(self,x,y,z,L,W,H):
        self.x = x
        self.y = y
        self.z = z
        self.L = float(L)
        self.W = float(W)
        self.H = float(H)
            
    def calculateFrequency(self):
        xterm = math.pow((self.x / self.L),2)
        yterm = math.pow((self.y / self.W),2)
        zterm = math.pow((self.z / self.H),2)
        return float(C) * math.sqrt(xterm + yterm + zterm)
    
    def asCsv(self,previous):
        return "{0:.2f}".format(self.calculateFrequency()) + ";" +  str(self.x) + ";" +   str(self.y) + ";" + str(self.z) + ";" + "{0:.2f}".format(self.calculateFrequency() - previous)

    def printModi(self):
        print(self.asCsv())

def writeModisSortedByFrequency(f,results):
    previous = 0
    #f = open(file_name,"w")
    for result in sorted(results,key=lambda f: f.calculateFrequency()):
        f.write(result.asCsv(previous) + "\n")
        previous = result.calculateFrequency()
    f.close()
    

def calculateModi():
    results = []
    length = int(length_text.get())
    width = int(width_text.get())
    height = int(height_text.get())
    
    #axiale modus
    results.append(ModiResult(0,0,0,length,width,height))
    
    for i in range(start,end):
        results.append(ModiResult(i,0,0,length,width,height))
        
    for i in range(start,end):
        results.append(ModiResult(0,i,0,length,width,height))
        
    for i in range(start,end):
        results.append(ModiResult(0,0,i,length,width,height))    
    
    #axiale    
    writeModisSortedByFrequency(tkFileDialog.asksaveasfile(mode="w"),results)
    print("")
    
    results = []
    
    for i in range(1,11):
        for j in range(1,11):
            results.append(ModiResult(i,j,0,length,width,height))
    
    for i in range(1,11):
        for j in range(1,11):
            results.append(ModiResult(i,0,j,length,width,height))
            
    for i in range(1,11):
        for j in range(1,11):
            results.append(ModiResult(0,i,j,length,width,height))        
    
    writeModisSortedByFrequency(tkFileDialog.asksaveasfile(mode="w"),results)


    
Button(text="Modi",font="20",command=calculateModi).grid(row=7,column=3)

mainloop()
