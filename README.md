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
Raspberry Piで使用できるハードウェアPWMのChannelが0, 1の2つまでであることから，同時に独立制御できるLEDテープは2本までです．  
そのため，1本のLEDテープで複数路線が制御できるように設計されています．  
| |PWM ch0|PWM ch1|
|--|--|--|
|**GPIO**|12 or 18|13 or 19|

#### led_config.jsonの設定
駅間のLEDのドット数は[config/led_config.json](config/led_config.json)内の`led_distance`の値で調整できます．初期状態では`6`なので，駅間のLEDのドット数は6個となります．  

#### Raspberry PiとLEDテープの接続
はじめに，LEDテープのGND, +5Vを電源に接続します．  
その後，LEDテープのGNDをRaspberry PiのGNDにも接続し，信号線"DATA IN"は設定したGPIOに接続します．  
> **注意**: LEDテープの電源をRaspberry Piの5vピンから取らないこと！LEDテープの消費電力が高いため，Raspberry Piが壊れます．  
必ず専用の5v電源を用意すること．

#### 丸ノ内線
丸ノ内線には，中野坂上駅 ～ 方南町駅の支線が存在します．この区間は，LEDテープ上の池袋駅(M-25)以降のLEDを用いて表現しています．  
路線図, 案内図のように分岐した表現をする場合，池袋駅のLEDの直後を切断し，以降のLEDを分岐点(中野坂上駅)まで移動させます．池袋駅のLEDの電源，信号線を切断部分まで延長することで，分岐の様子を表現することができます．  

#### 大江戸線
大江戸線は，都庁前駅 ～ 新宿西口駅 ～ 清澄白河駅 ～ 都庁前駅 ～ 光が丘駅のように，6の字運転をしています．新宿西口駅(E-01)を起点とした場合，プログラムの処理やLEDの加工が複雑になるため，光が丘(E-38)をLEDの起点としています．  
路線図，案内図のような表現をする場合，LEDテープ上の路線の末端に点灯する，ダミーの都庁前駅部分のLEDを切断します．切断部分を都庁前駅まで移動させることで，6の字運転の様子を表現することができます．

### ライブラリのインストール
以下コマンドでインストールしてください．  
```
sudo pip3 install rpi_ws281x
```

## Usage
```
usage: main.py [-h]
               [-ch0 [{G,M,H,T,C,Y,Z,N,F,A,I,S,E} [{G,M,H,T,C,Y,Z,N,F,A,I,S,E} ...]]]
               [-ch1 [{G,M,H,T,C,Y,Z,N,F,A,I,S,E} [{G,M,H,T,C,Y,Z,N,F,A,I,S,E} ...]]]

optional arguments:
  -h, --help            show this help message and exit
  -ch0 [{G,M,H,T,C,Y,Z,N,F,A,I,S,E} [{G,M,H,T,C,Y,Z,N,F,A,I,S,E} ...]], --ch0-lines [{G,M,H,T,C,Y,Z,N,F,A,I,S,E} [{G,M,H,T,C,Y,Z,N,F,A,I,S,E} ...]]
                        PWM Channel 0に表示する路線の路線記号. Default: G
  -ch1 [{G,M,H,T,C,Y,Z,N,F,A,I,S,E} [{G,M,H,T,C,Y,Z,N,F,A,I,S,E} ...]], --ch1-lines [{G,M,H,T,C,Y,Z,N,F,A,I,S,E} [{G,M,H,T,C,Y,Z,N,F,A,I,S,E} ...]]
                        PWM Channel 1に表示する路線の路線記号.
```
PWM Channel 0 (GPIO 12 or 18)に銀座線を表示する場合，以下コマンドで実行します．  
```
sudo python3 main.py -ch0 G
```

1つのLEDテープ(PWM Channel 0)に複数路線を同時に表示させる場合は，以下コマンドで実行します．以下は，銀座線と浅草線の場合です．  
```
sudo python3 main.py -ch0 G A
```
2つのPWM Channelにそれぞれ複数路線を表示させる場合は，以下コマンドで実行します．以下は，Channel 0に銀座線と丸ノ内線，Channel 1に浅草線と三田線を設定する場合です．  
```
sudo python3 main.py -ch0 G M -ch1 A I
```
## Others
### 路線ごとのLEDの明るさ・色調整
LEDテープによって個体差があるため，発色具合が良くない場合，[config/led_config.json](config/led_config.json)内の設定値を変更することで，明るさや色調整ができます．  
- brightness  
LED自体の明るさを調整できます(0~255). 各路線共通の設定です.  
- stationcolor [R, G, B]  
駅の色を調整できます(0~255)．
- traincolor [R, G, B]  
列車の色を調整できます(0~255)．  
- groundcolor [R, G, B]  
列車がいない場合の色を調整できます(0~255)．  
