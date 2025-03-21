# eBay商品検索アプリ

eBay商品検索アプリは、eBayの商品を簡単に検索・分析できるWebアプリケーションです。Streamlitを使用して構築されており、ユーザーフレンドリーなインターフェースを提供します。

## 機能

- キーワードとカテゴリーによる商品検索
- 検索結果の詳細表示とフィルタリング
- 価格帯による絞り込み
- 商品の状態（新品/中古）による絞り込み
- 検索結果の保存とCSVエクスポート
- 価格分布のグラフ表示

## 使用方法

1. 検索キーワードを入力します
2. 必要に応じてカテゴリー、価格帯、商品の状態を選択します
3. 「検索」ボタンをクリックします
4. 検索結果を確認します（テーブル表示/カード表示/グラフ表示）
5. 必要に応じて検索結果をCSVファイルとしてダウンロードします

## ローカルでの実行方法

```bash
# 必要なライブラリをインストール
pip install -r requirements.txt

# アプリケーションを実行
streamlit run app.py
```

## Streamlit Cloudでのデプロイ方法

1. GitHubアカウントを作成し、このリポジトリをフォークまたはクローンします
2. [Streamlit Cloud](https://streamlit.io/cloud) にログインします
3. 「New app」をクリックし、GitHubリポジトリを選択します
4. main branchとapp.pyファイルを選択します
5. 「Deploy」をクリックしてアプリケーションをデプロイします

## 注意事項

- このアプリケーションはeBayのウェブサイトをスクレイピングしています。過度な使用は避けてください。
- eBayのウェブサイト構造が変更された場合、アプリケーションが正常に動作しなくなる可能性があります。
- 商用利用する場合は、eBayのAPI利用規約を確認してください。 