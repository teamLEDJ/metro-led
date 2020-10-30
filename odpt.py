import requests
import json


class ODPT():
    '''APIデータ処理

    Parameters
    ----------
    jsonpath : str
        api_config.jsonのパス

    Attributes
    ----------
    line_table : dict
        路線記号のテーブル
    update_freq : int
        APIデータの更新間隔
    '''

    def __init__(self, jsonpath="./config/api_config.json"):

        with open(jsonpath, 'r') as cf:
            config = json.load(cf)

        with open("./data/line_table.json", 'r') as li:
            self.line_table = json.load(li)

        self.update_freq = config["update_freq"]

        self.__odpt_key = config["odpt"]["token"]
        self.__metro_key = config["metro"]["token"]

        for k in config["odpt"]["Train"].keys():
            config["odpt"]["Train"][k] += self.__odpt_key

        for k in config["metro"]["Train"].keys():
            config["metro"]["Train"][k] += self.__metro_key

        self.__trains = {}
        self.__trains.update(**config["odpt"]["Train"], **config["metro"]["Train"])

        self.__odpt_tra = config["odpt"]["Trains"] + self.__odpt_key
        self.__metro_tra = config["metro"]["Trains"] + self.__metro_key

        self.__odpt_rwy = config["odpt"]["Railway"] + self.__odpt_key
        self.__metro_rwy = config["metro"]["Railway"] + self.__metro_key

    def get_railway(self, service):
        '''"service"で提供される路線情報を取得する

        Parameters
        ----------
        service : str
            オープンデータのサービス("odpt" or "metro")

        Returns
        -------
        data : list of dict
            路線ごとの駅情報
        '''
        if service == "odpt":
            r = requests.get(self.__odpt_rwy)
        elif service == "metro":
            r = requests.get(self.__metro_rwy)
        else:
            return None

        railway_data = r.json()

        return railway_data

    def get_train(self, line):
        '''列車走行位置を取得する

        Parameters
        ----------
        line : str
            路線のlineCode (例: 銀座線->"G")

        Returns
        -------
        data : list of dict
            指定した路線の列車走行位置情報
        '''

        r = requests.get(self.__trains[line])
        train_data = r.json()
        
        return train_data

    def get_lines_train(self, lines):
        '''指定した複数路線の列車走行位置を取得する

        Parameters
        ----------
        lines : list of str
            路線のlineCodeのリスト (例: 銀座線と浅草線->["G", "A"])

        Returns
        -------
        data : [[dict],[dict],...]
            複数路線の列車走行位置情報
        '''

        trains_data = []
        all_trains = self.__get_all_trains()

        for i in range(len(lines)):
            line_trains = []

            for j in range(len(all_trains)):
                if all_trains[j]["odpt:railway"] == self.line_table[lines[i]]:
                    line_trains.append(all_trains[j])
                    
            trains_data.append(line_trains)

        return trains_data

    def get_stationtable(self, jsonpath="./data/station_table.json"):
        '''静的ファイルから駅テーブルを取得する

        Returns
        -------
        sta_table : dict
            路線ごとの駅テーブル
        '''

        with open(jsonpath, 'r') as sta:
            sta_table = json.load(sta)

        return sta_table

    def get_stationtable_api(self, service):
        '''APIから"service"の駅テーブルを取得する

        Parameters
        ----------
        service : str
            オープンデータのサービス("odpt" or "metro")

        Returns
        -------
        sta_table : dict
            "service"の路線ごとの駅テーブル
        '''
        railway = self.get_railway(service)
        sta_table = {}

        for i in range(len(railway)):
            sta_order = railway[i]["odpt:stationOrder"]
            sta_table[railway[i]["odpt:lineCode"]] = {}

            for j in range(len(sta_order)):
                if service == "metro":
                    sta_table[railway[i]["odpt:lineCode"]].update([(sta_order[j]["odpt:station"], sta_order[j]["odpt:index"])])
                else:
                    sta_table[railway[i]["odpt:lineCode"]].update([(sta_order[j]["odpt:station"], sta_order[j]["odpt:index"] - 1)])

        return sta_table

    def __get_all_trains(self):
        odpt_r = requests.get(self.__odpt_tra)
        metro_r = requests.get(self.__metro_tra)
        
        odpt_data = odpt_r.json()
        metro_data = metro_r.json()
        
        return odpt_data + metro_data
