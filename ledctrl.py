import json
import time
from rpi_ws281x import *


class LEDCtrl():
    '''LED制御

    Parameters
    ----------
    stations : dict
        ODPT.get_stationtable()で得た駅テーブル
    jsonpath : str
        led_config.jsonのパス

    Attributes
    ----------
    stations : dict
        路線ごとの駅テーブル
    distance : int
        前駅を含む，次駅直前までのLEDのドット数
    sta_color : list of int
        駅を示すLEDの色(R, G, B)
    lines : dict
        路線ごとのLED設定
    '''

    def __init__(self, stations, jsonpath="./config/led_config.json"):
        with open(jsonpath, 'r') as cf:
            config = json.load(cf)

        self.__FREQ_HZ = 800000
        self.__DMA = 10
        self.__INVERT = False

        self.stations = stations

        self.distance = config["led_distance"]
        self.sta_color = config["stationcolor"]
        self.lines = config["lines"]

    def strip_setup(self, use_lines):
        '''各路線のLEDテープのセットアップ

        Parameters
        ----------
        use_lines : list
            接続したLEDテープの路線のlineCodeのリスト (例: ["G", "M"])
        '''

        for i in range(len(use_lines)):
            line_conf = self.lines[use_lines[i]]

            # 各路線の設定項目にstripを追加
            self.lines[use_lines[i]]["strip"] = Adafruit_NeoPixel(
                (len(self.stations[use_lines[i]])-1) *
                self.distance+1, line_conf["gpio"], self.__FREQ_HZ,
                self.__DMA, self.__INVERT, line_conf["brightness"], line_conf["pwm"])

            self.lines[use_lines[i]]["strip"].begin()

    def __set_background(self, line):
        '''路線の暗色をLEDに設定

        Parameters
        ----------
        line : str
            路線のlineCode
        '''

        for i in range((len(self.stations[line]) - 1) * self.distance):
            self.lines[line]["strip"].setPixelColor(
                i, Color(*self.lines[line]["groundcolor"]))
