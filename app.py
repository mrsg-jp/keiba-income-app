import streamlit as st
import pandas as pd
import datetime

st.set_page_config(page_title="競馬収支管理", layout="wide")
st.title("🏇 競馬収支管理アプリ（表表示 & デフォルト強化）")

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

racecourse_dict = {
    "中央": ["札幌", "函館", "福島", "中山", "東京", "新潟", "中京", "京都", "阪神", "小倉"],
    "地方": ["帯広", "門別", "盛岡", "水沢", "浦和", "船橋", "大井", "川崎", "金沢", "笠松", "名古屋", "園田", "姫路", "高知", "佐賀"],
    "海外": ["香港", "サウジアラビア", "アラブ", "フランス", "アメリカ", "イギリス", "アイルランド", "オーストラリア"]
}

if menu == "記録ページ":
    st.header("記録の入力")

    region = st.selectbox("区分", ["中央", "地方", "海外"], key="region")
    if "last_region" not in st.session_state:
        st.session_state.last_region = region
    if region != st.session_state.last_region:
        st.session_state.racecourse = racecourse_dict[region][0]
        st.session_state.last_region = region

    racecourse = st.selectbox("競馬場", racecourse_dict[region], key="racecourse")

    with st.form("form"):
        date = st.date_input("日付", value=datetime.date.today())
        race = st.selectbox("レース番号", [f"{i}R" for i in range(1, 13)], index=10)  # default 11R (index=10)
        grade = st.selectbox("グレード", ["G1", "G2", "G3", "OP", "条件戦", "未勝利", "重賞", "A級", "B級", "C級", "一般"])
        surface = st.radio("芝・ダート", ["芝", "ダート"])
        distance = st.number_input("距離(m)", 100, 4000, value=1600, step=100)  # default 1600
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

elif menu == "一覧ページ":
    st.header("全データ一覧（表表示＋削除機能）")

    if records.empty:
        st.info("記録がまだありません。")
    else:
        st.subheader("🔍 フィルター")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            selected_regions = st.multiselect("区分", records["region"].unique())
        with col2:
            selected_courses = st.multiselect("競馬場", records["racecourse"].unique())
        with col3:
            selected_grades = st.multiselect("グレード", records["grade"].unique())
        with col4:
            selected_surface = st.multiselect("芝・ダート", records["surface"].unique())

        filtered = records.copy()
        if selected_regions:
            filtered = filtered[filtered["region"].isin(selected_regions)]
        if selected_courses:
            filtered = filtered[filtered["racecourse"].isin(selected_courses)]
        if selected_grades:
            filtered = filtered[filtered["grade"].isin(selected_grades)]
        if selected_surface:
            filtered = filtered[filtered["surface"].isin(selected_surface)]

        filtered = filtered.sort_values(by="date", ascending=False)

        st.subheader("📋 表形式で表示")
        st.dataframe(filtered.reset_index(drop=True), use_container_width=True)

        st.subheader("🗑 削除対象の選択")
        delete_indices = []
        for idx, row in filtered.iterrows():
            with st.expander(f"{row['date'].date() if pd.notnull(row['date']) else 'NaT'} | {row['region']} | {row['racecourse']} | {row.get('race','')}"):
                st.write(f"グレード: {row['grade']} | {row['surface']} | {row['distance']}m | {row['bet_type']}")
                st.write(f"購入: {row['purchase']}円 / 払戻: {row['payout']}円")
                if st.checkbox(f"削除対象にする", key=f"check_{idx}"):
                    delete_indices.append(idx)

        if delete_indices and st.button("✅ 選択した記録を削除"):
            records.drop(index=delete_indices, inplace=True)
            records.reset_index(drop=True, inplace=True)
            save_data(records)
            st.success(f"{len(delete_indices)} 件の記録を削除しました。再読み込みしてください。")

elif menu == "収支ページ":
    st.header("収支サマリー・分析")

    if records.empty:
        st.info("記録がありません。")
    else:
        records["balance"] = records["payout"] - records["purchase"]
        records["year"] = records["date"].dt.year
        records["month"] = records["date"].dt.to_period("M").astype(str)
        records["week"] = records["date"].dt.to_period("W").astype(str)

        st.sidebar.markdown("### フィルター")
        year_filter = st.sidebar.selectbox("年", ["全て"] + sorted(records["year"].dropna().unique().tolist()))
        racecourse_filter = st.sidebar.selectbox("競馬場", ["全て"] + sorted(records["racecourse"].dropna().unique()))
        grade_filter = st.sidebar.selectbox("グレード", ["全て"] + sorted(records["grade"].dropna().unique()))

        filtered = records.copy()
        if year_filter != "全て":
            filtered = filtered[filtered["year"] == int(year_filter)]
        if racecourse_filter != "全て":
            filtered = filtered[filtered["racecourse"] == racecourse_filter]
        if grade_filter != "全て":
            filtered = filtered[filtered["grade"] == grade_filter]

        st.metric("通算収支", f"{filtered['balance'].sum():,} 円")
        st.metric("購入総額", f"{filtered['purchase'].sum():,} 円")
        roi = (filtered["payout"].sum() / filtered["purchase"].sum() * 100) if filtered["purchase"].sum() > 0 else 0
        st.metric("回収率", f"{roi:.1f}%")

        st.subheader("月別収支（折れ線グラフ）")
        monthly = filtered.groupby("month")["balance"].sum().sort_index()
        st.line_chart(monthly)

        st.subheader("週別収支（折れ線グラフ）")
        weekly = filtered.groupby("week")["balance"].sum().sort_index()
        st.line_chart(weekly)
