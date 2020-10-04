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
        駅間のLEDのドット数
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

        self.distance = config["led_distance"] + 1
        self.sta_color = config["stationcolor"]
        self.lines = config["lines"]

    def setup_strip(self, use_lines, channel):
        '''各路線のLEDテープのセットアップ

        Parameters
        ----------
        use_lines : list
            接続したLEDテープの路線のlineCodeのリスト (例: ["G", "M"])
        channel : int
            PWMのChannel (0 or 1)

        Returns
        -------
        strip : Adafruit_NeoPixel()
            LEDテープのインスタンス
        '''
        # channel
        if channel == 0: gpio = 12
        elif channel == 1: gpio = 13

        # LEDのoffset
        offset = 0

        # LED長を計算
        for i in range(len(use_lines)):
            line_conf = self.lines[use_lines[i]]
            self.lines[use_lines[i]]["offset"] = offset
            offset = (len(self.stations[use_lines[i]])-1) * self.distance + 1 + offset

        # 各路線の設定項目にstripを追加
        strip = Adafruit_NeoPixel(
            offset, gpio, self.__FREQ_HZ,
            self.__DMA, self.__INVERT, line_conf["brightness"], channel)
        strip.begin()

        return strip

    def show_strip(self, strip, lines, trains, update_freq):
        '''LEDテープに列車位置を点灯

        Parameters
        ----------
        strip : Adafruit_NeoPixel()
            LEDテープのインスタンス
        lines : list of str
            路線のlineCodeを格納したリスト
        trains : list of list(ODPT.get_train())
            路線ごとの列車位置情報をまとめたリスト
        update_freq : int
            データの更新間隔
        '''
        for i in range(self.distance-1):
            for j in range(len(lines)):
                self.__set_background(strip, lines[j])
                self.__set_stationpos(strip, lines[j])
                cache = self.__set_trainpos(strip, 
                    lines[j], trains[j], self.lines[lines[j]]["cache"], i)
                # 最終ループ
                if i == self.distance - 2:
                    self.lines[lines[j]]["cache"] = cache

            strip.show()
            time.sleep(update_freq/(self.distance-1))

    def clear_strip(self, strip):
        '''LEDテープを消灯

        Parameters
        ----------
        strip : Adafruit_NeoPixel()
            LEDテープのインスタンス
        '''

        for i in range(strip.numPixels()):
            strip.setPixelColor(i, Color(0, 0, 0))
        strip.show()

    def __set_background(self, strip, line):
        '''路線の暗色をLEDに設定

        Parameters
        ----------
        strip : Adafruit_NeoPixel()
            LEDテープのインスタンス
        line : str
            路線のlineCode
        '''

        for i in range((len(self.stations[line]) - 1) * self.distance):
            strip.setPixelColor(
                i+self.lines[line]["offset"], Color(*self.lines[line]["groundcolor"]))

    def __set_stationpos(self, strip, line):
        '''路線の駅位置をLEDに設定

        Parameters
        ----------
        strip : Adafruit_NeoPixel()
            LEDテープのインスタンス
        line : str
            路線のlineCode
        '''
        for i in range(len(self.stations[line])):
            strip.setPixelColor(
                i*self.distance+self.lines[line]["offset"], Color(*self.sta_color))

    def __set_trainpos(self, strip, line, trains, cache, movingpos):
        '''
        Parameters
        ----------
        strip : Adafruit_NeoPixel()
            LEDテープのインスタンス
        line : str
            路線のlineCode
        trains : list
            ODPT.get_train()で得られた, 指定した路線の列車走行位置情報
        cache : dict
            列番ごとの位置情報と点灯中のLEDの番号
            LEDCtrl.lines[line]["cache"]を指定
        movingpos : int
            駅間移動に使用する
            0 ~ LEDCtrl.distanceまでインクリメントした値

        Returns
        -------
        cache_new : dict
            列番ごとの位置情報と点灯中のLEDの番号が格納された新しいキャッシュ
        '''

        cache_new = {}    # 次回更新時用キャッシュ

        for i in range(len(trains)):
            # 駅停車時
            if trains[i]["odpt:toStation"] == None:
                from_sta_index = self.stations[line][trains[i]
                                                     ["odpt:fromStation"]]
                lednum = from_sta_index*self.distance
                strip.setPixelColor(
                    lednum + self.lines[line]["offset"], Color(*self.lines[line]["traincolor"]))

            # 駅間(キャッシュに列車番号存在)
            # キャッシュから列車番号を検索
            elif trains[i]["odpt:trainNumber"] in cache:
                # 駅間情報がキャッシュと新しい情報で一致 (更新前と更新後で列車位置が同じ)
                if cache[trains[i]["odpt:trainNumber"]]["odpt:fromStation"] == trains[i]["odpt:fromStation"] \
                    and cache[trains[i]["odpt:trainNumber"]]["odpt:toStation"] == trains[i]["odpt:toStation"]:

                    from_sta_index = self.stations[line][trains[i]
                                                         ["odpt:fromStation"]]
                    to_sta_index = self.stations[line][trains[i]
                                                       ["odpt:toStation"]]

                    # キャッシュからLED点灯位置取得
                    lednum = cache[trains[i]["odpt:trainNumber"]]["nowled"]

                    # LED点灯位置を据え置く
                    # 大江戸線 新宿西口 -> 都庁前
                    if line == "E" \
                        and trains[i]["odpt:fromStation"] == "odpt.Station:Toei.Oedo.ShinjukuNishiguchi" \
                        and trains[i]["odpt:toStation"] == "odpt.Station:Toei.Oedo.Tochomae":
                        self.__set_strip_betw_sta(strip, line, lednum, 1)
                    # ナンバリング正方向
                    elif from_sta_index < to_sta_index:
                        self.__set_strip_betw_sta(strip, line, lednum, 1)
                    # ナンバリング負方向
                    else:
                        self.__set_strip_betw_sta(strip, line, lednum, -1)

                # 駅間列車位置更新時
                else:
                    # 丸ノ内線支線入線時 (中野坂上 -> 中野新橋)
                    if line == "M" \
                        and trains[i]["odpt:fromStation"] == "odpt.Station:TokyoMetro.Marunouchi.NakanoSakaue" \
                        and trains[i]["odpt:toStation"] == "odpt.Station:TokyoMetro.MarunouchiBranch.NakanoShimbashi":

                        lednum = self.__set_maruouchi_betw_sta(
                            strip, line, trains, i, movingpos)

                    # 大江戸線特定区間 (新宿西口 -> 都庁前)
                    elif line == "E" \
                        and trains[i]["odpt:fromStation"] == "odpt.Station:Toei.Oedo.ShinjukuNishiguchi" \
                        and trains[i]["odpt:toStation"] == "odpt.Station:Toei.Oedo.Tochomae":

                        from_sta_index = self.stations[line][trains[i]["odpt:fromStation"]]
                        lednum = from_sta_index * self.distance + movingpos
                        self.__set_strip_betw_sta(strip, line, lednum, 1)

                    # 大江戸線特定区間 (都庁前 -> 新宿西口)
                    elif line == "E" \
                        and trains[i]["odpt:fromStation"] == "odpt.Station:Toei.Oedo.Tochomae" \
                        and trains[i]["odpt:toStation"] == "odpt.Station:Toei.Oedo.ShinjukuNishiguchi":

                        lednum = self.__set_oedo_betw_sta(strip, line, trains, i, movingpos)

                    else:
                        lednum = self.__set_normal_betw_sta(
                            strip, line, trains, i, movingpos)

            # 駅間
            else:
                # 丸ノ内線支線入線時 (中野坂上 -> 中野新橋)
                if line == "M" \
                    and trains[i]["odpt:fromStation"] == "odpt.Station:TokyoMetro.Marunouchi.NakanoSakaue" \
                    and trains[i]["odpt:toStation"] == "odpt.Station:TokyoMetro.MarunouchiBranch.NakanoShimbashi":
                    
                    lednum = self.__set_maruouchi_betw_sta(
                        strip, line, trains, i, movingpos)

                # 大江戸線特定区間 (新宿西口 -> 都庁前)
                elif line == "E" \
                    and trains[i]["odpt:fromStation"] == "odpt.Station:Toei.Oedo.ShinjukuNishiguchi" \
                    and trains[i]["odpt:toStation"] == "odpt.Station:Toei.Oedo.Tochomae":

                    from_sta_index = self.stations[line][trains[i]["odpt:fromStation"]]
                    lednum = from_sta_index * self.distance + movingpos
                    self.__set_strip_betw_sta(strip, line, lednum, 1)
                
                # 大江戸線特定区間 (都庁前 -> 新宿西口)
                elif line == "E" \
                    and trains[i]["odpt:fromStation"] == "odpt.Station:Toei.Oedo.Tochomae" \
                    and trains[i]["odpt:toStation"] == "odpt.Station:Toei.Oedo.ShinjukuNishiguchi":

                    lednum = self.__set_oedo_betw_sta(strip, line, trains, i, movingpos)

                else:
                    lednum = self.__set_normal_betw_sta(
                        strip, line, trains, i, movingpos)

            # キャッシュ生成
            self.__set_traincache(cache_new, trains[i], lednum)

        return cache_new

    def __set_strip_betw_sta(self, strip, line, lednum, direction):
        '''LEDテープに駅間の列車を描画
        '''

        strip.setPixelColor(
            lednum + self.lines[line]["offset"], Color(*self.lines[line]["traincolor"]))
        strip.setPixelColor(
            lednum + direction + self.lines[line]["offset"], Color(*self.lines[line]["traincolor"]))

    def __set_normal_betw_sta(self, strip, line, trains, i, movingpos):
        '''通常時の駅間の列車の位置設定
        '''

        from_sta_index = self.stations[line][trains[i]["odpt:fromStation"]]
        to_sta_index = self.stations[line][trains[i]["odpt:toStation"]]

        # ナンバリング正方向
        if from_sta_index < to_sta_index:
            lednum = from_sta_index*self.distance + movingpos
            self.__set_strip_betw_sta(strip, line, lednum, 1)

        # ナンバリング負方向
        else:
            lednum = from_sta_index*self.distance - movingpos
            self.__set_strip_betw_sta(strip, line, lednum, -1)

        return lednum

    def __set_maruouchi_betw_sta(self, strip, line, trains, i, movingpos):
        '''丸ノ内線特定区間の列車の位置設定
        '''

        # 中野坂上 -> 中野新橋のみ
        from_sta_index = self.stations[line][trains[i]["odpt:fromStation"]]
        to_sta_index = self.stations[line][trains[i]["odpt:toStation"]]

        # 出発直後: 中野坂上駅のledと支線の最初のLEDを点灯
        if movingpos == 0:
            lednum = from_sta_index*self.distance
            strip.setPixelColor(
                lednum + self.lines[line]["offset"], Color(*self.lines[line]["traincolor"]))
            strip.setPixelColor(
                to_sta_index*self.distance - self.distance + 1 + self.lines[line]["offset"], Color(*self.lines[line]["traincolor"]))

        # それ以降
        else:
            lednum = to_sta_index*self.distance - self.distance + movingpos
            self.__set_strip_betw_sta(strip, line, lednum, 1)

        return lednum

    def __set_oedo_betw_sta(self, strip, line, trains, i, movingpos):
        '''大江戸線特定区間の列車の位置設定
        '''

        # 都庁前 -> 新宿西口
        from_sta_index = self.stations[line][trains[i]["odpt:fromStation"]]
        to_sta_index = self.stations[line][trains[i]["odpt:toStation"]]

        # 出発直後: 都庁前駅のledと都庁前-新宿西口間の最初のLEDを点灯
        if movingpos == 0:
            lednum = from_sta_index*self.distance
            strip.setPixelColor(
                lednum + self.lines[line]["offset"], Color(*self.lines[line]["traincolor"]))
            strip.setPixelColor(
                to_sta_index*self.distance + self.distance - 1 + self.lines[line]["offset"], Color(*self.lines[line]["traincolor"]))

        # それ以降
        else:
            lednum = to_sta_index*self.distance + self.distance - movingpos
            self.__set_strip_betw_sta(strip, line, lednum, -1)

        return lednum

    def __set_traincache(self, cache, train, lednum):
        '''列車ごとのキャッシュを設定
        '''

        train_data = {
            "odpt:fromStation": train["odpt:fromStation"], "odpt:toStation": train["odpt:toStation"], "nowled": lednum}
        cache.update([(train["odpt:trainNumber"], train_data)])
