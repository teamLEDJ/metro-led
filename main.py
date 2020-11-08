import argparse
import threading
import time
import datetime
import traceback

from odpt import ODPT
from ledctrl import LEDCtrl
from log import Log

class Main():
    def __init__(self):
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument("-ch0", "--ch0-lines", action="store",
                                help="PWM Channel 0に表示する路線の路線記号. Default: G", default=["G"],
                                type=str, choices=["G", "M", "H", "T", "C", "Y", "Z", "N", "F", "A", "I", "S", "E"],
                                nargs='*')
        self.parser.add_argument("-ch1", "--ch1-lines", action="store",
                                help="PWM Channel 1に表示する路線の路線記号. ", default=[],
                                type=str, choices=["G", "M", "H", "T", "C", "Y", "Z", "N", "F", "A", "I", "S", "E"],
                                nargs='*')
        self.parser.add_argument("-l", "--led-config", action="store",
                                help="LEDの設定ファイル. Default: ./config/led_config.json", default="./config/led_config.json",
                                type=str)
        self.parser.add_argument("-s", "--station-table", action="store",
                                help="駅番号の定義ファイル. Default: ./data/station_table.json", default="./data/station_table.json",
                                type=str)
        self.parser.add_argument("-a", "--animation",  action='store',
                                help="起動時にLEDアニメーションを行う. 13線全ての路線表示を行う場合，history，routenumを選択可能． \
                                normal: 接続順に点灯, history: 開業順に点灯, routenum: 路線番号順に点灯",
                                default="", choices=["normal", "history", "routenum"])

        self.args = self.parser.parse_args()
        self.anim_param = self.args.animation
        self.cf_path = self.args.led_config
        self.st_path = self.args.station_table
        self.lines = [self.args.ch0_lines, self.args.ch1_lines]

        self.odpt = ODPT()
        stations = self.odpt.get_stationtable(self.st_path)
        print(f"{Log.INFO()}Loaded Station table!")

        self.leds = []
        for i in range(len(self.lines)):
            if self.lines[i] == []:
                self.leds.append([])
                continue
            led = LEDCtrl(stations, self.lines[i], i, self.odpt.update_freq, self.cf_path)
            led.setup_strip()
            self.leds.append(led)

        print(f"{Log.INFO()}Setuped LED strips!")

        # アニメーション
        if self.anim_param:
            self.anim_test(self.anim_param)

    def anim_test(self, param=""):
        # normal用の表示順リストを作成
        line_list = self.args.ch0_lines + self.args.ch1_lines

        # 全路線が選択された場合のみ. historyもしくはroutenumを適用
        if len(line_list) < 13 and param != "normal":
            param = "normal"
            print(f"{Log.WARN()}Must select all lines (13 lines) to set animation mode \"history\" and \"routenum\". Set animation mode \"normal\".")

        elif param == "history":
            line_list = ["G", "M", "A", "H", "T", "I", "C", "Y", "Z", "S", "N", "E", "F"]

        elif param == "routenum":
            line_list = ["A", "H", "G", "M", "T", "I", "N", "Y", "C", "S", "Z", "E", "F"]

        print(f"{Log.INFO()}Show animation! Mode: {param}")

        # 表示
        for i in range(len(line_list)):
            if line_list[i] in self.args.ch0_lines: ch = 0
            else: ch = 1
            self.leds[ch].wipe_strip(line_list[i])

    def showline(self):
        for i in range(len(self.lines)):
            if self.lines[i] == []:
                continue
            
            th = threading.Thread(
                target=self.__showline_thread, args=(self.lines[i], i, ))
            th.setDaemon(True)
            th.start()

            time.sleep(1)
    
    def __showline_thread(self, lines, led_idx):
        print(f"{Log.INFO()}Strip{led_idx}: Started thread!")

        # 例外カウント
        except_count = 0

        print(f"{Log.INFO()}Strip{led_idx}: Started real-time display!")

        while True:
            try:
                # 表示路線の列車位置を取得
                trains = self.odpt.get_lines_train(lines)
            except:
                # 取得失敗時
                except_count += 1
                print(traceback.format_exc())
                print(f"{Log.WARN()}Strip{led_idx}: Could not get or decode json. Retry after 2 second...")
                time.sleep(2)

                # 5回以上失敗した場合，処理を終了
                if except_count >= 5:
                    print(f"{Log.ERROR()}Strip{led_idx}: Processing failed 5 times. Press Ctrl + C to terminate the main thread.")
                    return False

                continue
            
            # ログ出力
            for i in range(len(lines)):
                # 列車が存在しない場合
                if trains[i] == []:
                    print(f"{Log.WARN()}Line {lines[i]}: There are no trains currently running!")
                else:
                    print(f"{Log.INFO()}Line {lines[i]}: Updated Train data. Date: {trains[i][0]['dc:date']}")
            
            self.leds[led_idx].show_strip(trains)
            # 例外カウント初期化
            except_count = 0

    def stop(self):
        for i in range(len(self.leds)):
            if self.leds[i]:
                self.leds[i].clear_strip()
                print(f"{Log.INFO()}Strip{i}: Stopped LEDs.")
        print(f"{Log.INFO()}Stopped all LEDs. Exit")


if __name__ == "__main__":
    main = Main()
    main.showline()

    while 1:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            main.stop()
            break
