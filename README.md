# metro-led
東京の地下鉄のリアルタイム走行位置をLEDテープに表示させます．  

## Overview
公共交通オープンデータセンター 及び 東京メトロオープンデータで提供される地下鉄の情報とRaspberry Pi，LEDテープを用いて，地下鉄のリアルタイムな列車走行位置をLEDテープ上に表示させます．  
路線図のようにLEDテープを配置すれば，現在運転中の列車の様子を一目で見渡すことができます．  
現在，以下の路線に対応しています．  

- 東京メトロ (全線)  
銀座線, 丸ノ内線(支線含む), 日比谷線, 東西線, 千代田線, 有楽町線, 半蔵門線, 南北線, 副都心線
- 都営地下鉄 (全線)  
浅草線, 三田線, 新宿線, 大江戸線

本プログラムは，大江戸線を除き，[駅ナンバリング](https://ja.wikipedia.org/wiki/%E9%A7%85%E3%83%8A%E3%83%B3%E3%83%90%E3%83%AA%E3%83%B3%E3%82%B0#%E6%97%A5%E6%9C%AC%E3%81%A7%E3%81%AE%E4%BA%8B%E4%BE%8B)に従って，LEDテープの信号入力側がナンバリングが01の駅としています．  
また，大江戸線は，以下の都合上，光が丘駅(E-38)をLEDテープの信号入力側としています．  

> **注意**: 丸ノ内線，大江戸線は一般路線と運行形態が異なるため，LEDテープの加工が必要です．接続・加工方法は，後の章で説明します．

## Prerequisites
### 開発者サイトへの登録
以下のサイトにてユーザ登録を行い，アクセストークンを発行します．登録完了には数日かかる場合があります．  
[公共交通オープンデータセンター 開発者サイト](https://developer.odpt.org/)  
[東京メトロオープンデータ開発者サイト](https://developer.tokyometroapp.jp/info)  

登録完了後，発行されたトークンを[config/api_config.json](config/api_config.json)に設定します．  

### ハードウェア
Raspberry PiとLEDテープ**WS2812B**を用意します．  
Raspberry Piで使用できるハードウェアPWMのChannelが0, 1の2つまでであることから，現状同時に独立制御できるLEDテープは2本までです．  
そのため，1台のRaspberry Piで表示できる路線は2つまでとなっています．近日中に1本のLEDテープで複数路線が制御できるように改善する予定です．  
| |PWM ch0|PWM ch1|
|--|--|--|
|**GPIO**|12 or 18|13 or 19|

#### led_config.jsonの設定
接続する路線のLEDテープのpwmのch，GPIOの設定は[config/led_config.json](config/led_config.json)で変更します．  
各路線ごとに設定を行います．各路線は路線記号表記です．[こちら](https://ja.wikipedia.org/wiki/%E9%A7%85%E3%83%8A%E3%83%B3%E3%83%90%E3%83%AA%E3%83%B3%E3%82%B0#%E6%97%A5%E6%9C%AC%E3%81%A7%E3%81%AE%E4%BA%8B%E4%BE%8B)の東京地下鉄，都営地下鉄を参照してください．  
以下は銀座線(**G**)の設定例です．  

```json
"G": {
            "brightness": 70,
            "gpio": 18, <-- この2つを変更
            "pwm": 0,   <--
            "traincolor": [185, 90, 0],
            "groundcolor": [36, 12, 0],
            "strip": null,
            "cache": {}
        },
        ...
```

また，駅間のLEDのドット数は[config/led_config.json](config/led_config.json)内の`led_distance`の値で調整できます．初期状態では`6`なので，駅間のLEDのドット数は6個となります．  

#### Raspberry PiとLEDテープの接続
はじめに，LEDテープのGND, +5Vを電源に接続します．  
その後，LEDテープのGNDをRaspberry PiのGNDにも接続し，信号線"DATA IN"は設定したGPIOに接続します．  
> **注意**: LEDテープの電源をRaspberry Piの5vピンから取らないこと！LEDテープの消費電力が高いため，Raspberry Piが壊れます．  
必ず専用の5v電源を用意すること．

#### 丸ノ内線
丸ノ内線には，中野坂上 - 方南町の支線が存在します．この区間は，LEDテープ上の池袋駅(M-25)以降のLEDを用いて表現しています．路線図, 案内図のように分岐した表現をする場合，池袋駅のLEDの直後を切断し，以降のLEDを分岐点(中野坂上)まで移動させます．池袋駅のLEDの電源，信号線を切断部分まで延長することで，分岐の様子を表現することができます．  

#### 大江戸線
大江戸線は，都庁前 - 新宿西口 - 清澄白河 - 都庁前 - 光が丘のように，6の字運転をしています．そのため，起点を光が丘(E-38)として処理を行っています．路線図，案内図のような表現をする場合，LEDテープ上の路線の末端に点灯する，ダミーの都庁前駅部分のLEDを切断します．切断部分を都庁前駅まで移動させることで，6の字運転の様子を表現することができます．

### ライブラリのインストール
以下コマンドでインストールしてください．  
```
sudo pip3 install rpi_ws281x
```

## Usage
```
usage: main.py [-h]
               [-l [{G,M,H,T,C,Y,Z,N,F,A,I,S,E} [{G,M,H,T,C,Y,Z,N,F,A,I,S,E} ...]]]

optional arguments:
  -h, --help            show this help message and exit
  -l [{G,M,H,T,C,Y,Z,N,F,A,I,S,E} [{G,M,H,T,C,Y,Z,N,F,A,I,S,E} ...]], --lines [{G,M,H,T,C,Y,Z,N,F,A,I,S,E} [{G,M,H,T,C,Y,Z,N,F,A,I,S,E} ...]]
                        表示する路線の路線記号. 独立制御は2本まで. Default: G
```
銀座線を表示する場合，以下コマンドで実行します．  
```
sudo python3 main.py -l G
```

複数路線を同時に表示させる場合は，以下コマンドで実行します．以下は，銀座線と浅草線の場合です．  
> **注意**: PWMのChannelが異なる路線のみ指定してください！また，指定できる路線は2つまでです．
```
sudo python3 main.py -l G A
```

## Others
### 路線ごとのLEDの明るさ・色調整
[config/led_config.json](config/led_config.json)内の設定値を変更することで，明るさや色調整ができます．  
- stationcolor [R, G, B]  
駅の色を調整できます(0~255)．
- brightness  
LED自体の明るさを調整できます(0~100).  
- traincolor [R, G, B]  
列車の色を調整できます(0~255)．  
- groundcolor [R, G, B]  
列車がいない場合の色を調整できます(0~255)．  
