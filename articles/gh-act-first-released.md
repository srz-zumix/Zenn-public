---
title: "GitHub Actions のローカル実行ツール（nektos/act）を便利にする gh extension を作った"
emoji: "🐙"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: [githubactions]
published: false
---

## gh-act をリリースしました

https://github.com/srz-zumix/gh-act

まだ開発途中ではありますがとりあえず v0.1 をリリースしました。
gh をインストール済みであれば、 `gh extension install srz-zumix/gh-act` でインストールできます。

使い方は README にも一応書いてありますが、この記事でも後述します。
その前にそもそも nektos/act とは？から説明します。

## nektos/act とは？

https://github.com/nektos/act

GitHub Actions の Workflow をローカル実行するツールです。
GitHub 公式のツールではなく、イベントをエミュレートしています。
手軽に Workflow をローカル実行できるのでワークフローをデバッグしたいときにはとても便利です。
ただし、このツールでは本家と完全に同じ環境・状態では実行できません。

### act の注意点

[雪猫](https://zenn.dev/snowcait) さんが act について書いているのでそちらも参考にしてください。  
[GitHub Actions のデバッグをローカルで行う](https://zenn.dev/snowcait/articles/2b4a903b9fd584#nektos%2Fact)

あと個人ブログにも act の記事を投稿しました。こちらもよろしければ是非。  
[ブログズミ: nektos/act で GitHub Actions のワークフローをローカル実行](https://srz-zumix.blogspot.com/2022/08/nektosact-github-actions.html)

* 実行環境
  * act が使用する Docker image に依存
    * https://github.com/nektos/act#runners
    * [act が提供するイメージ](https://github.com/catthehacker/docker_images/pkgs/container/ubuntu)は `ubuntu` のみサポート
    * Medium だと hosted runner と比べてインストール済みパッケージが少ない
    * Large だと image サイズが大きい  (image is extremely big, 20GB compressed, ~60GB extracted)
    * 利用用途別にある程度 image は用意されている
    * 任意のイメージを使うこともできるが runner の環境としてある程度整っている必要がある
  * サービスコンテナは使えません
    * `services` の内容は無視される
* secrets.GITHUB_TOKEN が未定義
  * https://github.com/nektos/act#github_token
  * `act -s GITHUB_TOKEN=<token>` のように `-s` オプションで設定が必要
* [github コンテキスト](https://docs.github.com/ja/actions/learn-github-actions/contexts)の event の中身がほぼ空っぽ
  * https://github.com/nektos/act#events
  * github.event.* を参照しているワークフローは失敗する可能性がある
  * `act pull_request -e pull-request.json` のように `-e` オプションで event の JSON をセットできる
* 挙動が本家と同じとは限らない
  * 環境や機能はもちろんのこと、挙動に関してもエミュレートなので全く同じではない
* `ACT` 環境変数が定義されている
  * この環境変数の有無で処理分け可能（e.g. `if: ${{ env.ACT }}`）
  * これにより本家でも act でも実行可能なワークフローを記述可能ではある
  * しかし、当然ながら本家との差分が大きくなるため、本末転倒な感じ

この中でも特に GITHUB_TOKEN と event JSON を設定するのが面倒くさいです。
そこで gh-act を書きました。

## gh-act ができること

### secrets.GITHUB_TOKEN の自動設定

GITHUB_TOKEN / GH_TOKEN / GH_ENTERPRISE_TOKEN が定義されていれば、gh-act が `-s` オプションをセットします。
環境変数が定義されていない場合、 gh のコンフィグディレクトリにある `hosts.yml` から TOKEN を取得してセットします。

gh 使っているのであればおそらく auth login 状態だと思うので、オプション指定を書く必要なく TOKEN が設定される想定です。

### event JSON の生成

`gh act pull_request` のように指定されたトリガーイベントに沿った event JSON を gh-act が生成します。JSON の内容はローカルリポジトリの状態を参照して設定されます。

`gh act pull_request -e pull_request.json` のように `-e` オプションでパスが指定された場合は、そのパスが存在すれば gh-act は何もせずにそのファイルが使用されます。
そのパスが存在しない場合は gh-act が生成し、指定されたパスに保存します。
つまり `pull_request.json` が存在しなかった場合、１回目の実行でファイルが作成され act が実行。２回目以降は最初に生成したファイルを使用して act が実行されます。

gh-act が生成する event JSON も本家とは全く同じではありません。
なにもしなくても大抵のケースはカバーできる気はしてますが、不備不足があれば都合が良い JSON に書き換えて使ってください。
それでも 0 から作成したり、他のワークフローの実行結果からコピペやダウンロードしたりするよりかは楽になると思います。

また、event JSON 生成する際に参照する PR 番号とかを指定できるようにもしてます。
gh-act が対応している event や環境変数の詳細は [README](https://github.com/srz-zumix/gh-act) を確認してください。

### act vs gh-act

参考までに act と gh-act で実行したときの差分を画像を貼っておきます。
左が act 、右が gh-act です。

![act vs gh-act](/images/gh-act/act-diff.png)

実行したワークフローはこちら
https://github.com/srz-zumix/gh-act/blob/main/.github/workflows/events.yml

こちらはコンテキストをダンプするワークフローになっており、スクリーンショットは `${{ toJson(github) }}` をダンプしているところです。小さくてわかりにくいですが、 act の方は event が空なのに対し、gh-act の方は中身があることがわかると思います。この部分を gh-act が生成してます。

### gh-act の注意点

* gh-act が生成する event JSON は本家のもとは完全一致ではない
  * event 中の action の type によって中身が変わるものに未対応
  * value の記述が若干違ったりする場合がある（時刻と null とか）
  * 固定値しか入ってないものがある
  * いくつかの event は gh-act のリポジトリで実行した差分を出してるので参考までに  
    https://github.com/srz-zumix/gh-act/actions/workflows/main.yml
* GitHub Actions や act の更新追従が手動
  * テンプレートを自動生成しているわけじゃないので、本家の変更についていける気がしません・・
  * テストもちゃんとしてるわけじゃないので、壊れても多分気付かない・・
  * 筆者が gh extension 作ってみたくて書いただけなので、モチベーション依存
* [GraphQL rate limit](https://github.com/srz-zumix/gh-act/actions/workflows/main.yml)
  * 5,000ポイント/1h
  * gh-act のリポジトリで検証してた際にも何回か超えることがありました
  * gh-act は内部で何回か gh コマンドを実行するので最適化の余地はあるかも
* ちょっと遅い
  * ちょっと遅いです
  * gh コマンドの呼び出し回数が少なくなるように、と思って書いてはいますが最適化の余地はあるかも
  * shell 芸じゃなくて go とかで書き直したほうがいいのかも？
    * （今のところ筆者は書き直す気はありません）
  * `-e` オプションで一度書き出して使うのをオススメ

## 最後に

要望とかあれば対応するつもりなので、なにかあれば issue なり PR なりいただければ幸いです。
https://github.com/srz-zumix/gh-act
