import argparse
import threading
import time
import datetime
import traceback

from odpt import ODPT
from ledctrl import LEDCtrl


class Main():
    def __init__(self):
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument("-l", "--lines", action="store",
                                help="表示する路線の路線記号. 独立制御は2本まで. Default: G", default=["G"],
                                type=str, choices=["G", "M", "H", "T", "C", "Y", "Z", "N", "F", "A", "I", "S", "E"],
                                nargs='*')
        self.args = self.parser.parse_args()

        self.lines = self.args.lines

        self.odpt = ODPT()
        stations = self.odpt.get_stationtable()
        print(f"{datetime.datetime.now().isoformat()} [Info] Stations table is loaded!")

        self.led = LEDCtrl(stations)
        self.led.setup_strip(self.lines)
        print(f"{datetime.datetime.now().isoformat()} [Info] LED strips are setuped!")

    def showline(self):
        for i in range(len(self.lines)):
            self.led.lines[self.lines[i]]["thread"] = threading.Thread(
                target=self.__showline_thread, args=(self.lines[i],))
            self.led.lines[self.lines[i]]["thread"].setDaemon(True)
            self.led.lines[self.lines[i]]["thread"].start()

            print(f"{datetime.datetime.now().isoformat()} [Info] Line: {self.lines[i]} thread is started!")

    def __showline_thread(self, line):
        # 例外カウント
        except_count = 0

        while True:
            try:
                trains = self.odpt.get_train(line)
                print(f"{datetime.datetime.now().isoformat()} [Info] Train data is updated. Line: {line} Date: {trains[0]['dc:date']}")
                self.led.show_strip(line, trains, self.odpt.update_freq)
                # 例外カウント初期化
                except_count = 0

            # 例外: json取得失敗など
            except:
                except_count += 1

                print(traceback.format_exc())
                print(f"{datetime.datetime.now().isoformat()} [Warn] Line: {line} Could not get or decode json. Retry after 1 second...")
                time.sleep(1)

                # 5回以上失敗した場合，処理を終了
                if except_count >= 5:
                    print(f"{datetime.datetime.now().isoformat()} [Error] Processing failed 5 times. Press Ctrl + C to terminate the main thread.")
                    break

    def stop(self):
        for i in range(len(self.lines)):
            self.led.clear_strip(self.lines[i])
            print(f"{datetime.datetime.now().isoformat()} [Info] Line: {self.lines[i]} is stopped.")


if __name__ == "__main__":
    main = Main()
    main.showline()

    while 1:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            main.stop()
            print(f"{datetime.datetime.now().isoformat()} [Info] LEDs are stopped.")
            break
