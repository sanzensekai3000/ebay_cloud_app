import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from bs4 import BeautifulSoup
import re
import time
from datetime import datetime
import random
import json
import traceback

# Streamlitの設定
st.set_page_config(
    page_title="eBay商品検索",
    page_icon="🔍",
    layout="wide"
)

class EbayScraper:
    def __init__(self, requests_per_minute=3):  # 分あたりのリクエスト数を3に削減
        self.requests_per_minute = requests_per_minute
        self.delay = 60 / requests_per_minute
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.2277.128',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0'
        ]
        self.categories = self._get_categories()
        self.countries = self._get_countries()
        self.exchange_rate = 150  # USD to JPY exchange rate (仮の為替レート)
    
    def _get_categories(self):
        # eBayのカテゴリリスト（簡略化版）
        return {
            "すべてのカテゴリ": "",
            "アンティーク": "20081",
            "アート": "550",
            "ベビー": "2984",
            "本、コミック、雑誌": "267",
            "ビジネスと産業": "12576",
            "カメラ、写真": "625",
            "携帯電話、スマートフォン": "15032",
            "衣類、靴、アクセサリー": "11450",
            "コイン、紙幣": "11116",
            "コレクション": "1",
            "コンピュータ、タブレット": "58058",
            "家電製品": "293",
            "クラフト": "14339",
            "人形、ぬいぐるみ": "237",
            "DVDと映画": "11232",
            "eBayモーターズ": "6000",
            "エンターテイメントメモラビリア": "45100",
            "ギフトカード、チケット": "172008",
            "健康、美容": "26395",
            "家、庭、DIY": "11700",
            "ジュエリー、時計": "281",
            "音楽": "11233",
            "楽器、ギア": "619",
            "ペット用品": "1281",
            "陶器、ガラス": "870",
            "不動産": "10542",
            "スポーツ用品": "888",
            "スポーツメモラビリア": "64482",
            "おもちゃ、ホビー": "220",
            "旅行": "3252",
            "ビデオゲーム、コンソール": "1249"
        }
    
    def _get_countries(self):
        # 国のリスト
        return {
            "すべての国": "",
            "日本": "JP",
            "アメリカ": "US",
            "イギリス": "GB",
            "ドイツ": "DE",
            "フランス": "FR",
            "中国": "CN",
            "韓国": "KR",
            "オーストラリア": "AU",
            "カナダ": "CA",
            "イタリア": "IT",
            "スペイン": "ES",
            "香港": "HK",
            "シンガポール": "SG",
            "タイ": "TH"
        }
    
    def _get_random_user_agent(self):
        return random.choice(self.user_agents)
    
    def search(self, keyword, category="", min_price=None, max_price=None, condition=None, from_country=None, to_country=None, limit=50):
        search_url = "https://www.ebay.com/sch/i.html"
        params = {
            "_nkw": keyword,
            "_sacat": category,
            "_sop": "12",  # 終了日時: 近い順
            "_ipg": "50"  # 1ページあたりの結果数を50に減らす（負荷軽減）
        }
        
        if min_price and max_price:
            params["_udlo"] = min_price
            params["_udhi"] = max_price
        
        if condition:
            if condition == "新品":
                params["LH_ItemCondition"] = "1000"
            elif condition == "中古":
                params["LH_ItemCondition"] = "3000"
        
        # 発送元の国を指定
        if from_country and from_country != "":
            params["LH_PrefLoc"] = "2"  # 2 = specified location
            params["_fsradio"] = "&LH_LocatedIn=1"
            params["_fsradio2"] = "&LH_LocatedIn=1"
            params["_salic"] = from_country
        
        # 発送先の国を指定
        if to_country and to_country != "":
            params["LH_FS"] = "1"  # 1 = Will ship to selected location
            params["_fsct"] = to_country
        
        # モックデータの使用オプション
        use_mock_data = st.session_state.get('use_mock_data', False)
        if use_mock_data:
            # モックデータを返す
            return self._get_mock_data(keyword, limit)
        
        try:
            # リクエスト前の待機時間を大幅に増やす
            delay = self.delay + random.uniform(3, 8)  # 3～8秒のランダムな遅延を追加
            st.info(f"eBayにリクエストを送信します。{delay:.1f}秒お待ちください...")
            time.sleep(delay)
            
            headers = {
                'User-Agent': self._get_random_user_agent(),
                'Accept-Language': 'en-US,en;q=0.9,ja;q=0.8',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.8,image/webp,image/apng,*/*;q=0.5',
                'Referer': 'https://www.ebay.com/',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1',
                'Connection': 'keep-alive',
                'Cache-Control': 'max-age=0'
            }
            
            # リクエストを送信する前にCookieを取得する試み
            try:
                session = requests.Session()
                home_page = session.get('https://www.ebay.com/', headers=headers, timeout=15)
                # Cookieが設定されたセッションを使用
                response = session.get(search_url, params=params, headers=headers, timeout=20)
            except:
                # セッションアプローチが失敗した場合は通常のリクエストを試みる
                response = requests.get(search_url, params=params, headers=headers, timeout=20)
            
            response.raise_for_status()
            
            # デバッグ用に応答の内容を確認
            if "Robot Check" in response.text or "ロボットチェック" in response.text:
                st.error("eBayのロボット検出に引っかかりました。モックデータを使用します。")
                st.session_state['use_mock_data'] = True
                return self._get_mock_data(keyword, limit)
            
            soup = BeautifulSoup(response.content, 'html.parser')
            items = soup.select('li.s-item')
            
            # アイテムが見つからない場合の処理
            if not items:
                st.warning("検索結果が見つかりませんでした。モックデータを使用しますか？")
                st.warning(f"検索URL: {response.url}")
                use_mock = st.button("モックデータを使用")
                if use_mock:
                    st.session_state['use_mock_data'] = True
                    return self._get_mock_data(keyword, limit)
                return []
            
            results = []
            current_date = datetime.now().strftime("%Y-%m-%d")
            
            for item in items[:limit]:
                try:
                    title_elem = item.select_one('.s-item__title')
                    price_elem = item.select_one('.s-item__price')
                    link_elem = item.select_one('.s-item__link')
                    shipping_elem = item.select_one('.s-item__shipping')
                    location_elem = item.select_one('.s-item__location')
                    seller_elem = item.select_one('.s-item__seller-info-text')
                    
                    if all([title_elem, price_elem, link_elem]) and "Shop on eBay" not in title_elem.text:
                        title = title_elem.text.strip()
                        price_text = price_elem.text.strip()
                        
                        # リンクを安全に取得
                        link = link_elem.get('href', 'https://www.ebay.com').split('?')[0]
                        if not link or not link.startswith('http'):
                            link = 'https://www.ebay.com'
                        
                        # 価格情報の抽出 - 正規表現を改善
                        price_value = re.search(r'(\d+\.\d+)|(\d+)', price_text)
                        if price_value:
                            price_str = price_value.group(1) if price_value.group(1) else price_value.group(2)
                            price = float(price_str)
                        else:
                            price = 0.0
                        
                        # 円価格の計算
                        price_jpy = int(price * self.exchange_rate)
                        
                        # 配送情報
                        shipping = shipping_elem.text.strip() if shipping_elem else "不明"
                        
                        # 出品場所の取得
                        location = location_elem.text.strip() if location_elem else "不明"
                        
                        # 出品者情報の取得
                        seller = ""
                        shop_name = "N/A"
                        if seller_elem:
                            seller_text = seller_elem.text.strip()
                            seller_match = re.search(r'([a-zA-Z0-9._-]+)\s*\(', seller_text)
                            if seller_match:
                                seller = seller_match.group(1)
                            shop_match = re.search(r'\((.*?)\)', seller_text)
                            if shop_match:
                                shop_name = shop_match.group(1)
                        
                        # 画像URLの取得
                        img_elem = item.select_one('.s-item__image-img')
                        img_url = img_elem.get('src', '') if img_elem else ''
                        if not img_url or not img_url.startswith('http'):
                            img_url = 'https://via.placeholder.com/150'
                        
                        results.append({
                            'タイトル': title,
                            '価格': price,
                            '価格（円）': price_jpy,
                            '価格（表示）': price_text,
                            '配送': shipping,
                            '状態': condition_val if condition_val else "不明",
                            '場所': location,
                            '出品者': seller,
                            'ショップ名': [shop_name] if shop_name != "N/A" else "N/A",
                            '出品日時': current_date,
                            'リンク': link,
                            '画像URL': img_url
                        })
                except Exception as item_error:
                    # 個別のアイテム処理でのエラーをスキップ
                    st.debug(f"アイテム処理エラー: {str(item_error)}")
                    continue
            
            # 結果が0件の場合はモックデータの使用を提案
            if len(results) == 0:
                st.warning("検索条件に一致する商品が見つかりませんでした。モックデータを使用しますか？")
                use_mock = st.button("モックデータを使用", key="no_results_mock")
                if use_mock:
                    st.session_state['use_mock_data'] = True
                    return self._get_mock_data(keyword, limit)
                
            return results
        
        except Exception as e:
            st.error(f"検索中にエラーが発生しました: {str(e)}")
            st.error(traceback.format_exc())
            st.warning("eBayからのデータ取得に失敗しました。モックデータを使用しますか？")
            use_mock = st.button("モックデータを使用", key="error_mock")
            if use_mock:
                st.session_state['use_mock_data'] = True
                return self._get_mock_data(keyword, limit)
            return []
    
    def _get_mock_data(self, keyword, limit=10):
        """モックデータを生成する"""
        countries = ["Japan", "United States", "China", "United Kingdom", "Germany", "France"]
        sellers = ["yokitackle", "takuai", "active-sports-08", "gaku_jpshop", "japan-higasi-116"]
        shop_names = [["YOKI Fishing Gear Emporium"], ["Mother Lake Japan"], ["sparky-co-ltd"], ["gaku_jpshop"], "N/A"]
        conditions = ["新品", "中古", "不明"]
        current_date = datetime.now().strftime("%Y-%m-%d")
        mock_items = []
        
        for i in range(min(limit, 20)):
            price = round(random.uniform(20, 500), 2)
            price_jpy = int(price * self.exchange_rate)
            seller_idx = random.randint(0, len(sellers)-1)
            
            mock_items.append({
                'タイトル': f"{keyword} アイテム #{i+1} (モックデータ)",
                '価格': price,
                '価格（円）': price_jpy,
                '価格（表示）': f"US ${price}",
                '配送': random.choice(["送料無料", f"JPY {random.randint(5, 30)}00.0", "不明"]),
                '状態': random.choice(conditions),
                '場所': random.choice(countries),
                '出品者': sellers[seller_idx],
                'ショップ名': shop_names[seller_idx],
                '出品日時': current_date,
                'リンク': "https://www.ebay.com/",
                '画像URL': "https://via.placeholder.com/150"
            })
        return mock_items

def main():
    try:
        scraper = EbayScraper(requests_per_minute=3)  # 分あたりのリクエスト数を3に削減
        
        st.title("eBay商品検索アプリ")
        st.markdown("""
        このアプリでは、eBayの商品を簡単に検索・分析できます。
        以下の機能が利用可能です：
        - キーワードとカテゴリーによる商品検索
        - 発送元と発送先の国の指定
        - 検索結果の詳細表示とフィルタリング
        - 価格帯による絞り込み
        - 検索結果の保存とエクスポート
        """)
        
        # 為替レート設定
        with st.expander("為替レート設定"):
            new_rate = st.number_input("USD/JPY為替レート", min_value=1.0, max_value=1000.0, value=150.0, step=1.0, 
                                      help="ドル円の為替レート。現在の為替レートに合わせて調整してください。")
            scraper.exchange_rate = new_rate
            st.write(f"現在の為替レート: $1 = ¥{scraper.exchange_rate}")
        
        # 開発者モード（トラブルシューティング用）
        with st.expander("開発者オプション"):
            if st.button("モックデータを使用する"):
                st.session_state['use_mock_data'] = True
                st.success("モックデータを使用モードに設定しました")
            if st.button("実際のデータを使用する"):
                st.session_state['use_mock_data'] = False
                st.success("実際のデータを使用モードに設定しました")
            st.write(f"現在のモード: {'モックデータ' if st.session_state.get('use_mock_data', False) else '実際のデータ'}")
            
            # デバッグオプション
            debug_mode = st.checkbox("デバッグモード", value=False)
            if debug_mode:
                st.info("デバッグモードが有効になっています。エラーの詳細が表示されます。")
                # デバッグ関数の定義
                def st_debug(message):
                    if debug_mode:
                        st.text(f"DEBUG: {message}")
                st.debug = st_debug
            else:
                # 何もしないデバッグ関数
                st.debug = lambda x: None
        
        with st.form(key='search_form'):
            col1, col2 = st.columns(2)
            
            with col1:
                keyword = st.text_input("検索キーワード", placeholder="例: vintage camera")
                selected_category = st.selectbox(
                    "カテゴリー",
                    options=list(scraper.categories.keys()),
                    index=0
                )
                
                # 発送元と発送先の選択を追加
                from_country = st.selectbox(
                    "発送元",
                    options=list(scraper.countries.keys()),
                    index=0
                )
                
            with col2:
                col2_1, col2_2 = st.columns(2)
                with col2_1:
                    min_price = st.number_input("最低価格 ($)", min_value=0.0, step=10.0)
                with col2_2:
                    max_price = st.number_input("最高価格 ($)", min_value=0.0, step=10.0)
                
                condition = st.selectbox(
                    "商品の状態",
                    options=["すべて", "新品", "中古"],
                    index=0
                )
                
                # 発送先の選択
                to_country = st.selectbox(
                    "発送先",
                    options=list(scraper.countries.keys()),
                    index=0
                )
            
            submit_button = st.form_submit_button(label="検索")
        
        if submit_button and keyword:
            with st.spinner("検索中..."):
                category_id = scraper.categories[selected_category]
                condition_val = None if condition == "すべて" else condition
                from_country_code = scraper.countries[from_country]
                to_country_code = scraper.countries[to_country]
                
                search_results = scraper.search(
                    keyword=keyword,
                    category=category_id,
                    min_price=min_price if min_price > 0 else None,
                    max_price=max_price if max_price > 0 else None,
                    condition=condition_val,
                    from_country=from_country_code,
                    to_country=to_country_code
                )
                
                if search_results:
                    df = pd.DataFrame(search_results)
                    
                    # 検索結果の保存
                    st.session_state['search_results'] = df
                    
                    # タブを作成
                    tab1, tab2, tab3 = st.tabs(["テーブル表示", "カード表示", "グラフ"])
                    
                    with tab1:
                        # 安全にリンク列を処理
                        try:
                            # リンク列をマスク
                            df_display = df.copy()
                            # リンクを「商品ページ」というテキストに置き換え
                            df_display['リンク'] = ['商品ページ' for _ in range(len(df))]
                            
                            # 表示するカラムを設定
                            display_columns = ['タイトル', '価格', '価格（円）', '配送', '状態', '場所', '出品者', 'リンク']
                            st.dataframe(df_display[display_columns], use_container_width=True)
                        except Exception as e:
                            st.error(f"テーブル表示エラー: {str(e)}")
                            st.dataframe(df[['タイトル', '価格', '価格（円）', '配送', '状態', '場所', '出品者']], use_container_width=True)
                    
                    with tab2:
                        try:
                            # カード表示
                            for i in range(0, len(df), 3):
                                cols = st.columns(3)
                                for j in range(3):
                                    if i+j < len(df):
                                        with cols[j]:
                                            try:
                                                item = df.iloc[i+j]
                                                # 画像URLが有効か確認
                                                img_url = item['画像URL'] if item['画像URL'] and item['画像URL'].startswith('http') else "https://via.placeholder.com/150"
                                                st.image(img_url, width=150)
                                                
                                                # 商品タイトルを表示
                                                title = item['タイトル']
                                                if len(title) > 50:
                                                    title = title[:50] + "..."
                                                st.markdown(f"**{title}**")
                                                
                                                # 価格と配送情報
                                                st.markdown(f"価格: **{item['価格（表示）']}** (¥{item['価格（円）']})")
                                                st.markdown(f"配送: {item['配送']}")
                                                st.markdown(f"場所: {item['場所']}")
                                                st.markdown(f"出品者: {item['出品者']}")
                                                
                                                # リンクが有効か確認
                                                link = item['リンク'] if item['リンク'] and item['リンク'].startswith('http') else "https://www.ebay.com"
                                                st.markdown(f"[商品ページを開く]({link})")
                                            except Exception as card_error:
                                                st.warning(f"カード表示エラー: {str(card_error)}")
                        except Exception as e:
                            st.error(f"カード表示エラー: {str(e)}")
                    
                    with tab3:
                        try:
                            # 価格分布のヒストグラム
                            fig = px.histogram(df, x="価格", nbins=20, title="価格分布")
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # 発送元の円グラフ
                            if '場所' in df.columns:
                                fig_location = px.pie(df, names='場所', title="発送元の分布")
                                st.plotly_chart(fig_location, use_container_width=True)
                            
                            # 統計情報
                            stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
                            stats_col1.metric("平均価格", f"${df['価格'].mean():.2f}\n(¥{int(df['価格'].mean() * scraper.exchange_rate)})")
                            stats_col2.metric("最低価格", f"${df['価格'].min():.2f}\n(¥{int(df['価格'].min() * scraper.exchange_rate)})")
                            stats_col3.metric("最高価格", f"${df['価格'].max():.2f}\n(¥{int(df['価格'].max() * scraper.exchange_rate)})")
                            stats_col4.metric("商品数", f"{len(df)}")
                        except Exception as e:
                            st.error(f"グラフ表示エラー: {str(e)}")
                    
                    # CSVダウンロード
                    try:
                        # CSVエクスポート用のデータフレームを準備
                        export_df = df.copy()
                        
                        # CSVとして必要なカラムの名前マッピング
                        column_mapping = {
                            'タイトル': '商品名',
                            '配送': '送料'
                        }
                        
                        # 添付ファイルのカラム順を維持するためのマッピング
                        export_df = export_df.rename(columns=column_mapping)
                        
                        # 標準の出力カラム順を設定
                        export_columns = ['商品名', '価格', '価格（円）', '送料', '状態', '場所', '出品者', 'ショップ名', '出品日時']
                        
                        # 欠けているカラムがあれば追加
                        for col in export_columns:
                            if col not in export_df.columns:
                                export_df[col] = ""
                        
                        # カラム順を設定
                        export_df = export_df[export_columns]
                        
                        # CSVとしてエクスポート
                        csv = export_df.to_csv(index=False).encode('utf-8')
                        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
                        
                        st.download_button(
                            label="検索結果をCSVとして保存",
                            data=csv,
                            file_name=f"ebay_results_{current_time}.csv",
                            mime="text/csv",
                        )
                    except Exception as e:
                        st.error(f"CSVダウンロードエラー: {str(e)}")
                        st.error(traceback.format_exc())
                else:
                    st.warning("検索結果が見つかりませんでした。検索条件を変更してお試しください。")
    
    except Exception as e:
        st.error(f"アプリケーションエラー: {str(e)}")
        st.error(traceback.format_exc())

if __name__ == "__main__":
    # セッション状態の初期化
    if 'use_mock_data' not in st.session_state:
        st.session_state['use_mock_data'] = False
    
    main() 