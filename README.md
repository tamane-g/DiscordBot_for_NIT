# これは何ですか？

Discord Bot「廸無導（みちなし しるべ）」です。
高専生活に役立つさまざまな機能を提供したいと考えています。
現在はGoogle,Wikipediaでの検索、時間割の通知、学校ホームページのニュースの取得などの機能があります。

# このコードを改変したり修正したいです

開発の方法についてです。

前提知識：

- 分散バージョン管理システム『Git』
- 上項を用いたこのWebサービス『GitHub』
- VoIP,IMフリーウェア『Discord』
- 形態素解析エンジン『Janome』
- Webスクレイピングライブラリ『Beautiful Soup 4』

## 開発環境を構築するのに必要なソフトウェア

- Python3
- Git
- お好みのテキストエディタ(Windowsの『メモ帳』含む)

## 開発環境構築手順

以下のコマンドを1行ずつ実行して下さい。
なおコマンドリストの `/path/your/directory` の部分は各自手元の開発端末に合わせて書き換えて下さい。

他、『GitHub』や `git` コマンドを用いた際のエラーについては、各自で対処して下さい。

``` bash
cd /path/your/directory
git clone https://github.com/tamane-g/DiscordBot_for_NIT.git
cd DiscordBot_for_NIT
pip install -r requirements.txt
```

# よくある質問(F.A.Q) <!--『よくありそうな質問』でも可-->

- `git clone` ができません！
  - エラーメッセージは **ただ** あなたに「 `Git` です。ちょっと僕には判断できないので検討して下さい」と言ってるだけです。私に尋ねるより『Google』や『DuckDuckGo』で検索して下さい。オナシャス！！