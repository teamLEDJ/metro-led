import argparse
import threading
import time
import traceback

from odpt import ODPT
from ledctrl import LEDCtrl


class Main():
    def __init__(self):
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument("-l", "--lines", action="store",
                                 help="表示する路線(独立制御は2本まで). Default: G", default=["G"], type=str, nargs='*')
        self.args = self.parser.parse_args()

        self.lines = self.args.lines

        self.odpt = ODPT()
        stations = self.odpt.get_stationtable()

        self.led = LEDCtrl(stations)
        self.led.setup_strip(self.lines)

    def showline(self):
        for i in range(len(self.lines)):
            self.led.lines[self.lines[i]]["thread"] = threading.Thread(
                target=self.__showline_thread, args=(self.lines[i],))
            self.led.lines[self.lines[i]]["thread"].setDaemon(True)
            self.led.lines[self.lines[i]]["thread"].start()

    def __showline_thread(self, line):
        # 例外カウント
        except_count = 0

        while True:
            try:
                trains = self.odpt.get_train(line)
                self.led.show_strip(line, trains, self.odpt.update_freq)
                # 例外カウント初期化
                except_count = 0

            # 例外: json取得失敗など
            except:
                except_count += 1

                print(traceback.format_exc())
                print("Could not get or decode json.")
                print("Retry after 1 second...")
                time.sleep(1)

                # 5回以上失敗した場合，処理を終了
                if except_count >= 5:
                    print("Processing failed 5 times.")
                    print("Press Ctrl + C to terminate the main thread.")
                    break

    def stop(self):
        for i in range(len(self.lines)):
            self.led.clear_strip(self.lines[i])


if __name__ == "__main__":
    main = Main()
    main.showline()
    
    while 1:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            main.stop()
            print("\nExit")
            break
