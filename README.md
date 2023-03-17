# 寿司注文アプリ

## 事前準備

### 環境構築

``` sh
pip install -r requirements.txt
```

### LINE連携

LINEと連携を行う場合は、下記、環境変数の設定を行う  
(LINE送信を行わない場合は設定省略可)

- `LINE_CHANNEL_ACCESS_TOKEN`: `Line Messaging APIのチャンネルアクセストークン`

- `LINE_USER_ID`: `Line Messaging APIのチャンネル ユーザーID`

※ `LINE_USER_ID`については[https://webhook.site/](https://webhook.site/)からWebhookURLを発行し、MessagingAPI設定のWebhookURLに設定後、対象チャンネルへLINEメッセージを送信することでWebhookURL宛にBodyメッセージ含め送信されるので、そこで確認可能

**■ LINE連携用の環境変数は下記のスクリプトから実行可能です**

``` sh
source env_export.sh
```

## アプリ起動

``` sh
python app.py
```

アプリ起動後、[http://127.0.0.1:8550/](http://127.0.0.1:8550/)からアクセス可能です
