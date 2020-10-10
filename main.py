import argparse
import threading
import time
import datetime
import traceback

from odpt import ODPT
from ledctrl import LEDCtrl

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
        self.parser.add_argument("--test",  action='store_true', help="起動時にLED動作テストを行う.")

        self.args = self.parser.parse_args()
        self.test = self.args.test
        self.lines = [self.args.ch0_lines, self.args.ch1_lines]

        self.odpt = ODPT()
        stations = self.odpt.get_stationtable()
        print(f"{Log.INFO()}Loaded Station table!")

        self.leds = []
        for i in range(len(self.lines)):
            if self.lines[i] == []:
                self.leds.append([])
                continue
            led = LEDCtrl(stations, self.lines[i], i, self.odpt.update_freq)
            led.setup_strip()
            self.leds.append(led)

        print(f"{Log.INFO()}Setuped LED strips!")

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

        # 点灯確認
        if self.test:
            print(f"{Log.INFO()}Strip{led_idx}: Testing LEDs...")
            self.leds[led_idx].test_strip()
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
