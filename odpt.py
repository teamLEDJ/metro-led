import requests
import json


class ODPT():
    '''APIデータ処理

    Parameters
    ----------
    service : str
        オープンデータのサービス("odpt" or "metro")
    jsonpath : str
        api_config.jsonのパス

    Attributes
    ----------
    service : str
        オープンデータのサービス
    update_freq : int
        APIデータの更新間隔
    '''

    def __init__(self, service, jsonpath="./config/api_config.json"):
        '''
        '''
        with open(jsonpath, 'r') as cf:
            config = json.load(cf)

        self.service = service
        self.update_freq = config["update_freq"]

        self.__key = config[service]["token"]
        self.__odpt_tra = config[service]["Train"]
        self.__odpt_rwy = config[service]["Railway"] + self.__key

    def get_railway(self):
        '''"service"で提供される路線情報を取得する

        Returns
        -------
        data : list of dict
            路線ごとの駅情報
        '''

        r = requests.get(self.__odpt_rwy)
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

        r = requests.get(self.__odpt_tra[line] + self.__key)
        train_data = r.json()
        
        return train_data


    def get_stationtable(self):
        '''静的ファイルから"service"の駅テーブルを取得する

        Returns
        -------
        sta_table : dict
            "service"の路線ごとの駅テーブル
        '''
        jsonpath = f"./data/{self.service}_stations.json"

        with open(jsonpath, 'r') as sta:
            sta_table = json.load(sta)

        return sta_table
