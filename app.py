import streamlit as st
import pandas as pd
import datetime

st.set_page_config(page_title="競馬収支管理", layout="wide")
st.title("🏇 競馬収支管理アプリ（競馬場切替完全修正版）")

DATA_FILE = "keiba_records.csv"

def load_data():
    try:
        df = pd.read_csv(DATA_FILE)
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        return df
    except:
        return pd.DataFrame(columns=[
            'date', 'region', 'racecourse', 'race', 'grade', 'surface', 'distance',
            'bet_type', 'purchase', 'payout'
        ])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

records = load_data()

menu = st.sidebar.radio("ページを選択", ["記録ページ", "一覧ページ", "収支ページ"])

if menu == "記録ページ":
    st.header("記録の入力")

    racecourse_dict = {
        "中央": ["札幌", "函館", "福島", "中山", "東京", "新潟", "中京", "京都", "阪神", "小倉"],
        "地方": ["帯広", "門別", "盛岡", "水沢", "浦和", "船橋", "大井", "川崎", "金沢", "笠松", "名古屋", "園田", "姫路", "高知", "佐賀"],
        "海外": ["香港", "サウジアラビア", "アラブ", "フランス", "アメリカ", "イギリス", "アイルランド", "オーストラリア"]
    }

    # セッション管理による動的切替
    region = st.selectbox("区分", ["中央", "地方", "海外"], key="region")
    if "last_region" not in st.session_state:
        st.session_state.last_region = region
    if region != st.session_state.last_region:
        st.session_state.racecourse = racecourse_dict[region][0]
        st.session_state.last_region = region

    racecourse = st.selectbox("競馬場", racecourse_dict[region], key="racecourse")

    with st.form("form"):
        date = st.date_input("日付", datetime.date.today())
        race = st.selectbox("レース番号", [f"{i}R" for i in range(1, 13)])
        grade = st.selectbox("グレード", ["G1", "G2", "G3", "OP", "条件戦", "未勝利", "重賞", "A級", "B級", "C級", "一般"])
        surface = st.radio("芝・ダート", ["芝", "ダート"])
        distance = st.number_input("距離(m)", 100, 4000, step=100)
        bet_type = st.selectbox("式別", ["単勝", "複勝", "枠連", "馬連", "馬単", "ワイド", "三連複", "三連単"])
        purchase = st.number_input("購入金額", min_value=0, step=100)
        payout = st.number_input("払戻金額", min_value=0, step=100)
        submit = st.form_submit_button("記録")

        if submit:
            new = pd.DataFrame([{
                'date': pd.to_datetime(date),
                'region': region,
                'racecourse': racecourse,
                'race': race,
                'grade': grade,
                'surface': surface,
                'distance': distance,
                'bet_type': bet_type,
                'purchase': purchase,
                'payout': payout
            }])
            records = pd.concat([records, new], ignore_index=True)
            save_data(records)
            st.success("記録を保存しました")

else:
    st.info("この修正版は記録ページの競馬場リスト動的切り替え機能を完全対応しました。")
