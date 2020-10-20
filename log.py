import datetime

class Log():
    @staticmethod
    def get_date():
        return datetime.datetime.now().isoformat()

    @staticmethod
    def INFO():
        return Log.get_date() + ' \033[36m[Info]\033[0m '

    @staticmethod
    def WARN():
        return Log.get_date() + ' \033[33m[Warn]\033[0m '

    @staticmethod
    def ERROR():
        return Log.get_date() + ' \033[31m[Error]\033[0m '
