# if it doesn't work
# try
# sudo rmmod uvcvideo
# sudo modprobe uvcvideo nodrop=1 timeout=5000 quirks=0x80
# thanks nuts and volts!

# sudo apt-get install libcv-dev
# sudo apt-get install python-opencv opencv-apps
['CV_CAP_PROP_BRIGHTNESS', 'CV_CAP_PROP_CONTRAST', 'CV_CAP_PROP_CONVERT_RGB', 'CV_CAP_PROP_EXPOSURE', 'CV_CAP_PROP_FORMAT', 'CV_CAP_PROP_FOURCC', 'CV_CAP_PROP_FPS', 'CV_CAP_PROP_FRAME_COUNT', 'CV_CAP_PROP_FRAME_HEIGHT', 'CV_CAP_PROP_FRAME_WIDTH', 'CV_CAP_PROP_GAIN', 'CV_CAP_PROP_HUE', 'CV_CAP_PROP_MODE', 'CV_CAP_PROP_OPENNI_BASELINE', 'CV_CAP_PROP_OPENNI_FOCAL_LENGTH', 'CV_CAP_PROP_OPENNI_FRAME_MAX_DEPTH', 'CV_CAP_PROP_OPENNI_OUTPUT_MODE', 'CV_CAP_PROP_OPENNI_REGISTRATION', 'CV_CAP_PROP_POS_AVI_RATIO', 'CV_CAP_PROP_POS_FRAMES', 'CV_CAP_PROP_POS_MSEC', 'CV_CAP_PROP_RECTIFICATION', 'CV_CAP_PROP_SATURATION']

import cv2
from cv2 import cv
from Adafruit_BBIO import GPIO
GPIO.setup("P9_24", GPIO.OUT)
from numpy import array, int16, uint8, clip

cap = cv2.VideoCapture(0)
opened = cap.isOpened()
if not opened :
    print "no video stream! exiting.."
    exit()

WIDTH = 160.
HEIGHT = 120.

cap.set(cv.CV_CAP_PROP_FRAME_WIDTH, WIDTH)
cap.set(cv.CV_CAP_PROP_FRAME_HEIGHT, HEIGHT)
if (cap.get(3), cap.get(4)) != (WIDTH, HEIGHT) :
    print "can't set resolution to %d by %d, exiting.." % (WIDTH, HEIGHT)
    exit()

import time

import threading

class AcquireThread(threading.Thread) :
    def __init__(self, lt) :
        threading.Thread.__init__(self)
        self.daemon = True # this thread will be stopped abruptly when the program exits.
        self.lt = lt
        self.tavg = 0.04

    def run(self) :
        self.im0 = array(cap.read()[1], dtype=int16)
        self.im1 = array(cap.read()[1], dtype=int16)
        self.start=time.time()
        while True :
            self.im0[:,:,:] = cap.read()[1][:,:,:]
            self.im1[:,:,:] = cap.read()[1][:,:,:]
            self.lt.notify() # notify the led thread we want another pair
            self.end = time.time()
            self.tdiff = self.end - self.start
            self.tavg += 0.05 * (self.tdiff - self.tavg)
            self.fps = 2.0 / self.tavg
            self.idiff = clip((self.im0 - self.im1), 0, 255)
            self.start = self.end

def show(img) :
    """
    make an 8 bit copy of the image.
    swap the red and the green pixels.
    XXX this will mess up the timing of the other threads
    """
    icop = array(img, dtype=uint8)
    icop[:,:,0] = img[:,:,2]
    icop[:,:,2] = img[:,:,0]
    imshow(icop, interpolation="nearest")
            
class LedThread(threading.Thread) :
    # separate thread that turns the LED on and off
    def __init__(self, delay, ontime) :
        threading.Thread.__init__(self)
        self.delay = delay
        self.ontime = ontime
        self.request = threading.Event()
        self.result = threading.Event()
        self.daemon = True # this thread will be stopped abruptly when the program exits.
    def run(self) :
        self.start=time.time()
        while True :
            # continuous loop. wait until sync is called 
            self.request.wait()
            time.sleep(self.delay)
            wake = time.time()
            self.sleeptime = wake - self.start
            GPIO.output("P9_24", 1)
            time.sleep(self.ontime)
            off = time.time()
            self.ot = off - wake
            GPIO.output("P9_24", 0)
            self.request.clear()
            self.start = time.time()

    def notify(self) :
        # video thread calls this to ask for another LED pulse.
        self.request.set()
        
lt = LedThread(delay=0.01, ontime=0.005)
at = AcquireThread(lt)
lt.start()        
at.start()

"""
def test(N=10) :
    for i in range(5) :
        cap.read() # flush
    start = time.time()
    f = []
    raw = []
    times = []
    for i in range(N) :
        lt.sync()
        rv, im0 = cap.read()
        im0 = array(im0, dtype=int16)
        lt.wait()
        lt.sync()
        rv, im1 = cap.read()
        im1 = array(im1, dtype=int16)
        lt.wait()
        f.append(clip((im0 - im1), 0, 255))
        raw.append((im0, im1))
        times.append(time.time())
    end = time.time()
    print 2*N / (end-start), "frames per second"
    t = array(times)
    return f, raw, t[1:]-t[:-1]

def rawspeed(N=10) :
    times = []
    for i in range(5) :
        cap.read() # flush anything in the queue
    start = time.time()
    for i in range(N) :
        cap.read()
        times.append(time.time())
    end = time.time()
    print N / (end-start), "frames per second"
    t = array(times)
    return t[1:]-t[:-1]
"""

from pylab import interactive, imshow
interactive(True)

