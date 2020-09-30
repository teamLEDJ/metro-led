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
