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

    def setup_strip(self, use_lines):
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

    def show_strip(self, line, trains, update_freq):
        '''LEDテープに列車位置を点灯

        Parameters
        ----------
        line : str
            路線のlineCode
        trains : list
            ODPT.get_train()で得られた, 指定した路線の列車走行位置情報
        update_freq : int
            データの更新間隔
        '''

        for i in range(self.distance-1):
            self.__set_background(line)
            self.__set_stationpos(line)
            cache = self.__set_trainpos(
                line, trains, self.lines[line]["cache"], i)
            self.lines[line]["strip"].show()
            time.sleep(update_freq/(self.distance-1))

        self.lines[line]["cache"] = cache

    def clear_strip(self, line):
        '''指定した路線のLEDテープを消灯

        Parameters
        ----------
        line : str
            路線のlineCode
        '''

        for i in range(self.lines[line]["strip"].numPixels()):
            self.lines[line]["strip"].setPixelColor(i, Color(0, 0, 0))
        self.lines[line]["strip"].show()

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

    def __set_stationpos(self, line):
        '''路線の駅位置をLEDに設定

        Parameters
        ----------
        line : str
            路線のlineCode
        '''
        for i in range(len(self.stations[line])):
            self.lines[line]["strip"].setPixelColor(
                i*self.distance, Color(*self.sta_color))

    def __set_trainpos(self, line, trains, cache, movingpos):
        '''
        Parameters
        ----------
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
                self.lines[line]["strip"].setPixelColor(
                    lednum, Color(*self.lines[line]["traincolor"]))

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
                        self.__set_strip_betw_sta(line, lednum, 1)
                    # ナンバリング正方向
                    elif from_sta_index < to_sta_index:
                        self.__set_strip_betw_sta(line, lednum, 1)
                    # ナンバリング負方向
                    else:
                        self.__set_strip_betw_sta(line, lednum, -1)

                # 駅間列車位置更新時
                else:
                    # 丸ノ内線支線入線時 (中野坂上 -> 中野新橋)
                    if line == "M" \
                        and trains[i]["odpt:fromStation"] == "odpt.Station:TokyoMetro.Marunouchi.NakanoSakaue" \
                        and trains[i]["odpt:toStation"] == "odpt.Station:TokyoMetro.MarunouchiBranch.NakanoShimbashi":

                        lednum = self.__set_maruouchi_betw_sta(
                            line, trains, i, movingpos)

                    # 大江戸線特定区間 (新宿西口 -> 都庁前)
                    elif line == "E" \
                        and trains[i]["odpt:fromStation"] == "odpt.Station:Toei.Oedo.ShinjukuNishiguchi" \
                        and trains[i]["odpt:toStation"] == "odpt.Station:Toei.Oedo.Tochomae":

                        from_sta_index = self.stations[line][trains[i]["odpt:fromStation"]]
                        lednum = from_sta_index * self.distance + movingpos
                        self.__set_strip_betw_sta(line, lednum, 1)

                    # 大江戸線特定区間 (都庁前 -> 新宿西口)
                    elif line == "E" \
                        and trains[i]["odpt:fromStation"] == "odpt.Station:Toei.Oedo.Tochomae" \
                        and trains[i]["odpt:toStation"] == "odpt.Station:Toei.Oedo.ShinjukuNishiguchi":

                        lednum = self.__set_oedo_betw_sta(line, trains, i, movingpos)

                    else:
                        lednum = self.__set_normal_betw_sta(
                            line, trains, i, movingpos)

            # 駅間
            else:
                # 丸ノ内線支線入線時 (中野坂上 -> 中野新橋)
                if line == "M" \
                    and trains[i]["odpt:fromStation"] == "odpt.Station:TokyoMetro.Marunouchi.NakanoSakaue" \
                    and trains[i]["odpt:toStation"] == "odpt.Station:TokyoMetro.MarunouchiBranch.NakanoShimbashi":
                    
                    lednum = self.__set_maruouchi_betw_sta(
                        line, trains, i, movingpos)

                # 大江戸線特定区間 (新宿西口 -> 都庁前)
                elif line == "E" \
                    and trains[i]["odpt:fromStation"] == "odpt.Station:Toei.Oedo.ShinjukuNishiguchi" \
                    and trains[i]["odpt:toStation"] == "odpt.Station:Toei.Oedo.Tochomae":

                    from_sta_index = self.stations[line][trains[i]["odpt:fromStation"]]
                    lednum = from_sta_index * self.distance + movingpos
                    self.__set_strip_betw_sta(line, lednum, 1)
                
                # 大江戸線特定区間 (都庁前 -> 新宿西口)
                elif line == "E" \
                    and trains[i]["odpt:fromStation"] == "odpt.Station:Toei.Oedo.Tochomae" \
                    and trains[i]["odpt:toStation"] == "odpt.Station:Toei.Oedo.ShinjukuNishiguchi":

                    lednum = self.__set_oedo_betw_sta(line, trains, i, movingpos)

                else:
                    lednum = self.__set_normal_betw_sta(
                        line, trains, i, movingpos)

            # キャッシュ生成
            self.__set_traincache(cache_new, trains[i], lednum)

        return cache_new

    def __set_strip_betw_sta(self, line, lednum, direction):
        '''LEDテープに駅間の列車を描画
        '''

        self.lines[line]["strip"].setPixelColor(
            lednum, Color(*self.lines[line]["traincolor"]))
        self.lines[line]["strip"].setPixelColor(
            lednum + direction, Color(*self.lines[line]["traincolor"]))

    def __set_normal_betw_sta(self, line, trains, i, movingpos):
        '''通常時の駅間の列車の位置設定
        '''

        from_sta_index = self.stations[line][trains[i]["odpt:fromStation"]]
        to_sta_index = self.stations[line][trains[i]["odpt:toStation"]]

        # ナンバリング正方向
        if from_sta_index < to_sta_index:
            lednum = from_sta_index*self.distance + movingpos
            self.__set_strip_betw_sta(line, lednum, 1)

        # ナンバリング負方向
        else:
            lednum = from_sta_index*self.distance - movingpos
            self.__set_strip_betw_sta(line, lednum, -1)

        return lednum

    def __set_maruouchi_betw_sta(self, line, trains, i, movingpos):
        '''丸ノ内線特定区間の列車の位置設定
        '''

        # 中野坂上 -> 中野新橋のみ
        from_sta_index = self.stations[line][trains[i]["odpt:fromStation"]]
        to_sta_index = self.stations[line][trains[i]["odpt:toStation"]]

        # 出発直後: 中野坂上駅のledと支線の最初のLEDを点灯
        if movingpos == 0:
            lednum = from_sta_index*self.distance
            self.lines[line]["strip"].setPixelColor(
                lednum, Color(*self.lines[line]["traincolor"]))
            self.lines[line]["strip"].setPixelColor(
                to_sta_index*self.distance - self.distance + 1, Color(*self.lines[line]["traincolor"]))

        # それ以降
        else:
            lednum = to_sta_index*self.distance - self.distance + movingpos
            self.__set_strip_betw_sta(line, lednum, 1)

        return lednum

    def __set_oedo_betw_sta(self, line, trains, i, movingpos):
        '''大江戸線特定区間の列車の位置設定
        '''

        # 都庁前 -> 新宿西口
        from_sta_index = self.stations[line][trains[i]["odpt:fromStation"]]
        to_sta_index = self.stations[line][trains[i]["odpt:toStation"]]

        # 出発直後: 都庁前駅のledと都庁前-新宿西口間の最初のLEDを点灯
        if movingpos == 0:
            lednum = from_sta_index*self.distance
            self.lines[line]["strip"].setPixelColor(
                lednum, Color(*self.lines[line]["traincolor"]))
            self.lines[line]["strip"].setPixelColor(
                to_sta_index*self.distance + self.distance - 1, Color(*self.lines[line]["traincolor"]))

        # それ以降
        else:
            lednum = to_sta_index*self.distance + self.distance - movingpos
            self.__set_strip_betw_sta(line, lednum, -1)

        return lednum

    def __set_traincache(self, cache, train, lednum):
        '''列車ごとのキャッシュを設定
        '''

        train_data = {
            "odpt:fromStation": train["odpt:fromStation"], "odpt:toStation": train["odpt:toStation"], "nowled": lednum}
        cache.update([(train["odpt:trainNumber"], train_data)])
