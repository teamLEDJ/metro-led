import argparse
import threading
import time
import traceback

from odpt import ODPT
from ledctrl import LEDCtrl


class Main():
    def __init__(self):
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument("-s", "--service", action="store",
                                 help="使用するサービス. Default: metro", default="metro", type=str, choices=["odpt", "metro"])
        self.parser.add_argument("-l", "--lines", action="store",
                                 help="表示する路線(独立制御は2本まで). Default: G", default=["G"], type=str, nargs='*')
        self.args = self.parser.parse_args()

        service = self.args.service
        self.lines = self.args.lines

        self.odpt = ODPT(service)
        stations = self.odpt.get_stationtable()

        self.led = LEDCtrl(stations)
        self.led.setup_strip(self.lines)


if __name__ == "__main__":
    main = Main()
