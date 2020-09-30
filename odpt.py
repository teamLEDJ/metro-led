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
