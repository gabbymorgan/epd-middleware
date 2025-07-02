from PIL import Image, ImageFont
import threading
from lib import epd2in13_V4
from lib import gt1151
import os
import time
import io


fontdir = os.path.join(os.path.dirname(
    os.path.realpath(__file__)), 'assets/fonts')


class EPaperInterface():
    # For hardware information, see documentation for Waveshare 2.13 inch touch e-paper device.
    # https://www.waveshare.com/wiki/2.13inch_Touch_e-Paper_HAT_Manual#Raspberry_Pi

    # hardware and library constants
    MAX_PARTIAL_REFRESHES = 30
    MAX_REFRESH_INTERVAL = 24 * 60 * 60
    MIN_REFRESH_INTERVAL = 1
    TIMEOUT_INTERVAL = 120

    # gesture enums
    SWIPE_LEFT = "left"
    SWIPE_RIGHT = "right"

    FONT_15 = ImageFont.truetype(os.path.join(fontdir, 'Font.ttc'), 15)
    FONT_12 = ImageFont.truetype(os.path.join(fontdir, 'Font.ttc'), 12)

    def __init__(self):
        try:
            self.display = epd2in13_V4.EPD()
            self.width = self.display.width
            self.height = self.display.height
            self.touch_interface = gt1151.GT1151()
            self.touch_interface_dev = gt1151.GT_Development()
            self.touch_interface_old = gt1151.GT_Development()
            self.canvas = None
            self.touch_flag = True
            self.display_thread_flag = True
            self.app_is_running = True
            self.screen_is_active = True
            self.should_render = False
            self.partial_refresh_counter = 0
            self.last_full_refresh = time.time()

            # touch event attributes
            self.last_touched = time.time()
            self.is_touching = False
            self.has_been_touching = False
            self.touch_start_x = None
            self.touch_start_y = None
            self.touch_end_x = None
            self.touch_end_y = None
            self.did_swipe = False
            self.swipe_direction = None
            self.did_tap = False
            self.tap_x = None
            self.tap_y = None

            self.base_touch_thread = threading.Thread(
                daemon=True, target=self.base_touch_loop)
            self.display_thread = threading.Thread(
                daemon=False, target=self.display_loop)

            self.reset_canvas()
            self.display.init(self.display.FULL_UPDATE)
            self.display.displayPartBaseImage(
                self.display.getbuffer(self.canvas))
            self.touch_interface.GT_Init()

            self.base_touch_thread.start()
            self.display_thread.start()

        except KeyboardInterrupt:
            self.shutdown()

        except Exception as e:
            print("An error occured in the EPaperInterface. Exception was:" + str(e))

    def base_touch_loop(self):
        while self.touch_flag:
            if (self.touch_interface.digital_read(self.touch_interface.INT) == 0):
                self.touch_interface_dev.Touch = 1
            else:
                self.touch_interface_dev.Touch = 0
            time.sleep(0.02)

    def display_loop(self):
        while self.display_thread_flag:
            now = time.time()
            if self.should_render:
                self.render()
            elif self.screen_is_active and (now - self.last_touched > self.TIMEOUT_INTERVAL):
                self.sleep()
            elif not self.screen_is_active and (now - self.last_touched < self.TIMEOUT_INTERVAL):
                self.awaken()
            elif now - self.last_full_refresh > self.MAX_REFRESH_INTERVAL:
                self.clear_screen()
            time.sleep(EPaperInterface.MIN_REFRESH_INTERVAL)

    def detect_screen_interaction(self):
        # y values go up as touch moves left
        # x values go up as touch moves down

        self.did_swipe = False
        self.did_tap = False

        self.touch_interface.GT_Scan(
            self.touch_interface_dev, self.touch_interface_old)
        self.is_touching = self.touch_interface_dev.TouchCount > 0

        if self.is_touching and not self.has_been_touching:
            self.last_touched = time.time()
            self.touch_start_x = self.touch_interface_dev.X[0]
            self.touch_start_y = self.touch_interface_dev.Y[0]

        if self.has_been_touching and not self.is_touching:
            self.touch_end_x = self.touch_interface_old.X[0]
            self.touch_end_y = self.touch_interface_old.Y[0]
            distance_horizontal = self.touch_start_y - self.touch_end_y
            self.did_swipe = abs(distance_horizontal) > 0

            if self.did_swipe:
                self.swipe_direction = EPaperInterface.SWIPE_RIGHT if distance_horizontal > 0 else EPaperInterface.SWIPE_LEFT
            else:
                self.did_tap = True
                self.tap_x = self.touch_start_x
                self.tap_y = self.touch_start_y

        self.has_been_touching = self.is_touching

        return {"last_touched": self.last_touched,
                "is_touching": self.is_touching,
                "has_been_touching": self.has_been_touching,
                "touch_start_x": self.touch_start_x,
                "touch_start_y": self.touch_start_y,
                "touch_end_x": self.touch_end_x,
                "touch_end_y": self.touch_end_y,
                "did_swipe": self.did_swipe,
                "swipe_direction": self.swipe_direction,
                "did_tap": self.did_tap,
                "tap_x": self.tap_x,
                "tap_y": self.tap_y}

    def shutdown(self):
        self.touch_flag = False
        self.display_thread_flag = False
        self.screen_is_active = False
        self.app_is_running = False
        self.sleep()
        self.display.Dev_exit()
        self.base_touch_thread.join()
        self.display_thread.join()

    def sleep(self):
        self.screen_is_active = False
        self.clear_screen()
        time.sleep(2)
        self.display.sleep()

    def awaken(self):
        self.screen_is_active = True
        self.display.init(self.display.PART_UPDATE)
        self.display.displayPartBaseImage(self.display.getbuffer(self.canvas))

    def clear_screen(self):
        self.display.init(self.display.FULL_UPDATE)
        self.display.Clear(0xFF)

    def reset_canvas(self):
        self.canvas = Image.new('1', (self.height, self.width), 255)
        self.canvas.rotate(90)  # landscape mode

    def render(self):
        self.should_render = False
        if not self.screen_is_active:
            return
        if self.partial_refresh_counter >= EPaperInterface.MAX_PARTIAL_REFRESHES:
            self.display.init(self.display.FULL_UPDATE)
            self.display.displayPartBaseImage(
                self.display.getbuffer(self.canvas))
            self.partial_refresh_counter = 0
        else:
            self.display.displayPartial(self.display.getbuffer(self.canvas))
            self.partial_refresh_counter += 1

    def request_render(self, image_data=None):
        self.canvas = Image.open(io.BytesIO(image_data))
        self.should_render = True

    def get_window(self):
        return WindowData(width=self.width, height=self.height)


class WindowData:
    def __init__(self, width=None, height=None):
        self.width = width
        self.height = height

