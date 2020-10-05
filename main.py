import argparse
import threading
import time
import datetime
import traceback

from odpt import ODPT
from ledctrl import LEDCtrl

def get_date():
    return datetime.datetime.now().isoformat()

class Log():

    def get_date():
        return datetime.datetime.now().isoformat()

    def INFO():
        return get_date() + ' \033[36m[Info]\033[0m '

    def WARN():
        return get_date() + ' \033[33m[Warn]\033[0m '

    def ERROR():
        return get_date() + ' \033[31m[Error]\033[0m '

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
        self.args = self.parser.parse_args()

        self.lines = [self.args.ch0_lines, self.args.ch1_lines]

        self.odpt = ODPT()
        stations = self.odpt.get_stationtable()
        print(f"{Log.INFO()}Stations table is loaded!")

        self.leds = []
        for i in range(len(self.lines)):
            if self.lines[i] == []:
                self.leds.append([])
                continue
            led = LEDCtrl(stations, self.lines[i], i, self.odpt.update_freq)
            led.setup_strip()
            self.leds.append(led)

        print(f"{Log.INFO()}LED strips are setuped!")

    def showline(self):
        for i in range(len(self.lines)):
            if self.lines[i] == []:
                continue
            
            th = threading.Thread(
                target=self.__showline_thread, args=(self.lines[i], i, ))
            th.setDaemon(True)
            th.start()

            print(f"{Log.INFO()}Strip{i} thread is started!")

            time.sleep(1)
    
    def __showline_thread(self, lines, led_idx):
        # 例外カウント
        except_count = 0

        while True:
            trains = []

            for i in range(len(lines)):
                line = lines[i]

                while True:
                    try:
                        line_trains = self.odpt.get_train(line)
                        break

                    # 例外: json取得失敗など
                    except:
                        except_count += 1

                        print(traceback.format_exc())
                        print(f"{Log.WARN()}Line: {line} Could not get or decode json. Retry after 1 second...")
                        time.sleep(2)

                    # 5回以上失敗した場合，処理を終了
                    if except_count >= 5:
                        print(f"{Log.ERROR()}Processing failed 5 times. Press Ctrl + C to terminate the main thread.")
                        return False
                
                # 列車が存在しない場合
                if line_trains == []:
                    print(f"{Log.WARN()}Line: {line} There are no trains currently running!")
                else:
                    print(f"{Log.INFO()}Train data is updated. Line: {line} Date: {line_trains[0]['dc:date']}")
                trains.append(line_trains)
                time.sleep(0.2)

            self.leds[led_idx].show_strip(trains)
            # 例外カウント初期化
            except_count = 0

    def stop(self):
        for i in range(len(self.leds)):
            if self.leds[i]:
                self.leds[i].clear_strip()
                print(f"{Log.INFO()}Strip{i} is stopped.")
        print(f"{Log.INFO()}LEDs are stopped.")


if __name__ == "__main__":
    main = Main()
    main.showline()

    while 1:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            main.stop()
            break
