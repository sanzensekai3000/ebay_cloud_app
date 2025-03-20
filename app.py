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

# Streamlitの設定
st.set_page_config(
    page_title="eBay商品検索",
    page_icon="🔍",
    layout="wide"
)

class EbayScraper:
    def __init__(self, requests_per_minute=5):
        self.requests_per_minute = requests_per_minute
        self.delay = 60 / requests_per_minute
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'
        ]
        self.categories = self._get_categories()
    
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
    
    def _get_random_user_agent(self):
        return random.choice(self.user_agents)
    
    def search(self, keyword, category="", min_price=None, max_price=None, condition=None, limit=50):
        search_url = "https://www.ebay.com/sch/i.html"
        params = {
            "_nkw": keyword,
            "_sacat": category,
            "_sop": "12",  # 終了日時: 近い順
            "_ipg": "100"  # 1ページあたりの結果数を100に減らす
        }
        
        if min_price and max_price:
            params["_udlo"] = min_price
            params["_udhi"] = max_price
        
        if condition:
            if condition == "新品":
                params["LH_ItemCondition"] = "1000"
            elif condition == "中古":
                params["LH_ItemCondition"] = "3000"
        
        # モックデータの使用オプション
        use_mock_data = st.session_state.get('use_mock_data', False)
        if use_mock_data:
            # モックデータを返す
            return self._get_mock_data(keyword, limit)
        
        try:
            # リクエスト前の待機時間を増やす
            delay = self.delay + random.uniform(1, 3)  # 1～3秒のランダムな遅延を追加
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
                'Upgrade-Insecure-Requests': '1'
            }
            
            response = requests.get(search_url, params=params, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            items = soup.select('li.s-item')
            
            if not items:
                st.warning("検索結果が見つかりませんでした。モックデータを使用しますか？")
                st.session_state['use_mock_data'] = st.button("モックデータを使用")
                if st.session_state.get('use_mock_data', False):
                    return self._get_mock_data(keyword, limit)
                return []
            
            results = []
            
            for item in items[:limit]:
                title_elem = item.select_one('.s-item__title')
                price_elem = item.select_one('.s-item__price')
                link_elem = item.select_one('.s-item__link')
                shipping_elem = item.select_one('.s-item__shipping')
                
                if all([title_elem, price_elem, link_elem]) and "Shop on eBay" not in title_elem.text:
                    title = title_elem.text.strip()
                    price_text = price_elem.text.strip()
                    link = link_elem.get('href', '').split('?')[0]
                    
                    # 価格情報の抽出
                    price_value = re.search(r'(\d+\.\d+)', price_text)
                    price = float(price_value.group(1)) if price_value else 0.0
                    
                    # 配送情報
                    shipping = shipping_elem.text.strip() if shipping_elem else "不明"
                    
                    # 画像URLの取得
                    img_elem = item.select_one('.s-item__image-img')
                    img_url = img_elem.get('src', '') if img_elem else ''
                    
                    results.append({
                        'タイトル': title,
                        '価格': price,
                        '価格（表示）': price_text,
                        '配送': shipping,
                        'リンク': link,
                        '画像URL': img_url
                    })
            
            return results
        
        except Exception as e:
            st.error(f"検索中にエラーが発生しました: {str(e)}")
            st.warning("eBayからのデータ取得に失敗しました。モックデータを使用しますか？")
            st.session_state['use_mock_data'] = st.button("モックデータを使用")
            if st.session_state.get('use_mock_data', False):
                return self._get_mock_data(keyword, limit)
            return []
    
    def _get_mock_data(self, keyword, limit=10):
        """モックデータを生成する"""
        mock_items = []
        for i in range(min(limit, 20)):
            price = round(random.uniform(20, 500), 2)
            mock_items.append({
                'タイトル': f"{keyword} アイテム #{i+1} (モックデータ)",
                '価格': price,
                '価格（表示）': f"US ${price}",
                '配送': random.choice(["送料無料", "$10.00", "$5.99", "不明"]),
                'リンク': "https://www.ebay.com/",
                '画像URL': "https://via.placeholder.com/150"
            })
        return mock_items

def main():
    try:
        scraper = EbayScraper(requests_per_minute=5)
        
        st.title("eBay商品検索アプリ")
        st.markdown("""
        このアプリでは、eBayの商品を簡単に検索・分析できます。
        以下の機能が利用可能です：
        - キーワードとカテゴリーによる商品検索
        - 検索結果の詳細表示とフィルタリング
        - 価格帯による絞り込み
        - 検索結果の保存とエクスポート
        """)
        
        # 開発者モード（トラブルシューティング用）
        with st.expander("開発者オプション"):
            if st.button("モックデータを使用する"):
                st.session_state['use_mock_data'] = True
                st.success("モックデータを使用モードに設定しました")
            if st.button("実際のデータを使用する"):
                st.session_state['use_mock_data'] = False
                st.success("実際のデータを使用モードに設定しました")
            st.write(f"現在のモード: {'モックデータ' if st.session_state.get('use_mock_data', False) else '実際のデータ'}")
        
        with st.form(key='search_form'):
            col1, col2 = st.columns(2)
            
            with col1:
                keyword = st.text_input("検索キーワード", placeholder="例: vintage camera")
                selected_category = st.selectbox(
                    "カテゴリー",
                    options=list(scraper.categories.keys()),
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
            
            submit_button = st.form_submit_button(label="検索")
        
        if submit_button and keyword:
            with st.spinner("検索中..."):
                category_id = scraper.categories[selected_category]
                condition_val = None if condition == "すべて" else condition
                
                search_results = scraper.search(
                    keyword=keyword,
                    category=category_id,
                    min_price=min_price if min_price > 0 else None,
                    max_price=max_price if max_price > 0 else None,
                    condition=condition_val
                )
                
                if search_results:
                    df = pd.DataFrame(search_results)
                    
                    # 検索結果の保存
                    st.session_state['search_results'] = df
                    
                    # タブを作成
                    tab1, tab2, tab3 = st.tabs(["テーブル表示", "カード表示", "グラフ"])
                    
                    with tab1:
                        st.dataframe(df[['タイトル', '価格（表示）', '配送', 'リンク']], use_container_width=True)
                    
                    with tab2:
                        # カード表示
                        for i in range(0, len(df), 3):
                            cols = st.columns(3)
                            for j in range(3):
                                if i+j < len(df):
                                    with cols[j]:
                                        st.image(df.iloc[i+j]['画像URL'], width=150)
                                        st.markdown(f"**{df.iloc[i+j]['タイトル'][:50]}...**")
                                        st.markdown(f"価格: **{df.iloc[i+j]['価格（表示）']}**")
                                        st.markdown(f"配送: {df.iloc[i+j]['配送']}")
                                        st.markdown(f"[商品ページを開く]({df.iloc[i+j]['リンク']})")
                    
                    with tab3:
                        # 価格分布のヒストグラム
                        fig = px.histogram(df, x="価格", nbins=20, title="価格分布")
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # 統計情報
                        stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
                        stats_col1.metric("平均価格", f"${df['価格'].mean():.2f}")
                        stats_col2.metric("最低価格", f"${df['価格'].min():.2f}")
                        stats_col3.metric("最高価格", f"${df['価格'].max():.2f}")
                        stats_col4.metric("商品数", f"{len(df)}")
                    
                    # CSVダウンロード
                    csv = df.to_csv(index=False).encode('utf-8')
                    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
                    st.download_button(
                        label="検索結果をCSVとして保存",
                        data=csv,
                        file_name=f"ebay_search_{keyword}_{current_time}.csv",
                        mime="text/csv",
                    )
                else:
                    st.warning("検索結果が見つかりませんでした。検索条件を変更してお試しください。")
    
    except Exception as e:
        st.error(f"アプリケーションエラー: {str(e)}")

if __name__ == "__main__":
    # セッション状態の初期化
    if 'use_mock_data' not in st.session_state:
        st.session_state['use_mock_data'] = False
    
    main() 