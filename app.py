import streamlit as st
import pandas as pd
import datetime

st.set_page_config(page_title="競馬収支管理", layout="wide")
st.title("🏇 競馬収支管理アプリ（Streamlit Cloud対応）")

DATA_FILE = "keiba_records.csv"

def load_data():
    try:
        df = pd.read_csv(DATA_FILE)
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        return df
    except FileNotFoundError:
        return pd.DataFrame(columns=[
            'date', 'region', 'racecourse', 'grade', 'surface', 'distance', 'bet_type', 'purchase', 'payout'
        ])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

records = load_data()

menu = st.sidebar.radio("ページを選択", ["記録ページ", "一覧ページ", "収支ページ"])

if menu == "記録ページ":
    st.header("記録の入力")
    with st.form("form"):
        racecourse_dict = {
            "中央": ["東京", "中山", "京都", "阪神", "小倉", "札幌", "函館", "新潟", "中京"],
            "地方": ["大井", "川崎", "船橋", "浦和", "名古屋", "笠松", "園田", "姫路", "高知", "佐賀", "盛岡", "水沢", "金沢", "帯広"],
            "海外": ["香港", "ドバイ", "アメリカ", "イギリス", "フランス", "オーストラリア"]
        }

        region = st.selectbox("区分", ["中央", "地方", "海外"], key="region_select")
        if 'last_region' not in st.session_state:
            st.session_state.last_region = region

        if st.session_state.last_region != region:
            st.session_state.racecourse_select = None
            st.session_state.last_region = region

        racecourse = st.selectbox("競馬場", racecourse_dict[region], key="racecourse_select")

        date = st.date_input("日付", datetime.date.today())
        grade = st.selectbox("グレード", ["G1", "G2", "G3", "OP", "条件戦", "未勝利", "重賞", "A級", "B級", "C級", "一般"])
        surface = st.radio("芝・ダート", ["芝", "ダート"])
        distance = st.number_input("距離(m)", 100, 4000, step=100)
        bet_type = st.selectbox("式別", ["単勝", "複勝", "枠連", "馬連", "馬単", "ワイド", "三連複", "三連単"])
        purchase = st.number_input("購入金額", min_value=0, step=100)
        payout = st.number_input("払戻金額", min_value=0, step=100)
        submit = st.form_submit_button("記録")

        if submit:
            new = pd.DataFrame([{
                'date': date, 'region': region, 'racecourse': racecourse, 'grade': grade, 'surface': surface,
                'distance': distance, 'bet_type': bet_type, 'purchase': purchase, 'payout': payout
            }])
            records = pd.concat([records, new], ignore_index=True)
            save_data(records)
            st.success("記録を保存しました")

elif menu == "一覧ページ":
    st.header("全データ一覧（条件フィルター付き）")
    if not records.empty:
        with st.expander("🔍 条件フィルター"):
            selected_region = st.multiselect("区分", records['region'].unique())
            selected_grade = st.multiselect("グレード", records['grade'].unique())
            selected_surface = st.multiselect("芝・ダート", records['surface'].unique())
            selected_bet = st.multiselect("式別", records['bet_type'].unique())

        filtered = records.copy()
        if selected_region:
            filtered = filtered[filtered['region'].isin(selected_region)]
        if selected_grade:
            filtered = filtered[filtered['grade'].isin(selected_grade)]
        if selected_surface:
            filtered = filtered[filtered['surface'].isin(selected_surface)]
        if selected_bet:
            filtered = filtered[filtered['bet_type'].isin(selected_bet)]

        st.dataframe(filtered.sort_values("date", ascending=False))
    else:
        st.info("記録がまだありません。")

elif menu == "収支ページ":
    st.header("分析・収支サマリー")
    if not records.empty:
        records['balance'] = records['payout'] - records['purchase']
        records['year'] = records['date'].dt.year
        records['month'] = records['date'].dt.to_period('M')
        records['week'] = records['date'].dt.to_period('W')

        year_filter = st.sidebar.selectbox("年", ["全て"] + sorted(records['year'].dropna().unique().tolist()))
        bet_filter = st.sidebar.selectbox("式別", ["全て"] + sorted(records['bet_type'].dropna().unique().tolist()))

        filtered = records.copy()
        if year_filter != "全て":
            filtered = filtered[filtered['year'] == int(year_filter)]
        if bet_filter != "全て":
            filtered = filtered[filtered['bet_type'] == bet_filter]

        col1, col2, col3 = st.columns(3)
        col1.metric("通算収支", f"{filtered['balance'].sum():,} 円")
        col2.metric("購入総額", f"{filtered['purchase'].sum():,} 円")
        roi = (filtered['payout'].sum() / filtered['purchase'].sum() * 100) if filtered['purchase'].sum() > 0 else 0
        col3.metric("回収率", f"{roi:.1f}%")

        st.subheader("月別収支")
        st.bar_chart(filtered.groupby('month')['balance'].sum())

        st.subheader("週別収支")
        st.line_chart(filtered.groupby('week')['balance'].sum())
    else:
        st.info("データがありません。記録を追加してください。")
