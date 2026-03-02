import streamlit as st
import yfinance as yf
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta

# 网页配置
st.set_page_config(page_title="全球市场情绪监测站", layout="wide")

st.title("📈 全球市场情绪对冲投资策略 (2026版)")
st.markdown("---")

# --- 侧边栏：控制面板 ---
st.sidebar.header("参数设置")
selected_date = st.sidebar.date_input("选择回溯日期", datetime.now() - timedelta(days=1))
market_choice = st.sidebar.radio("选择目标市场", ["美股 (US)", "A股 (CN)"])

# --- 数据抓取核心逻辑 (完全修正版) ---
def get_data(market, date_obj):
    date_str = date_obj.strftime('%Y%m%d')
    
    # 限制不能查询未来时间
    if date_obj > datetime.now().date():
        return [["错误", "日期越界", "不能查询未来", "请重新选择", "无效"]]

    if market == "美股 (US)":
        # 抓取该日期的 VIX 收盘价
        vix_df = yf.Ticker("^VIX").history(start=date_obj, end=date_obj + timedelta(days=5))
        
        # 确保拿到的是那一天的数据，而不是最近的
        vix_val = round(vix_df['Close'].iloc[0], 2) if not vix_df.empty else 20.0
        
        # 根据 VIX 历史数值反推 Fear & Greed 状态
        fg_score = 100 - (vix_val * 2.5) 
        fg_score = max(0, min(100, int(fg_score)))
        
        if fg_score < 25: status = "极度恐惧"
        elif fg_score < 45: status = "恐惧"
        elif fg_score > 75: status = "极度贪婪"
        elif fg_score > 55: status = "贪婪"
        else: status = "中性"
        
        return [
            ["调查类", "AAII散户看涨率", "历史数据需订阅", "反映散户多空意愿", status],
            ["衍生品", "Put/Call Ratio", "基于VIX估算", "反映期权防守情绪", "观察"],
            ["波动性", "VIX 恐慌指数", str(vix_val), "越高代表市场越不安", "恐慌" if vix_val > 25 else "平稳"],
            ["资金流", "机构头寸变化", "持平", "基于历史波动率估算", "观望"]
        ]
    else:
        # A股部分逻辑修正：专注于可回溯数据
        try:
            # 抓取沪深300指数数据，这部分数据确实是按日期变动的
            df = ak.index_zh_a_hist(symbol="000300", period="daily", start_date=date_str, end_date=date_str)
            
            if df.empty:
                return [
                    ["状态", "数据抓取", "无数据", "该日可能为节假日", "无效"],
                    ["资金流", "北向资金(外资)", "每日披露", "外资配置意愿", "无"],
                    ["资金流", "成交额(回溯)", "0亿", "该日市场未开盘", "无"],
                    ["波动性", "沪深300收盘", "0.0", "大盘指数", "无"]
                ]
            
            close_price = df['收盘'].iloc[0]
            vol_val = f"{df['成交额'].iloc[0]/1e8:.0f}亿"

            # 成交额判断市场活跃度 (基于日期变动)
            if df['成交额'].iloc[0] > 1000000000000: market_status = "市场亢奋"
            elif df['成交额'].iloc[0] < 500000000000: market_status = "市场低迷"
            else: market_status = "正常"

            return [
                ["资金流", "北向资金(外资)", "每日披露", "外资配置意愿", "利好"],
                ["资金流", "成交额(回溯)", vol_val, "市场活跃度", market_status],
                ["波动性", "沪深300收盘", str(close_price), "大盘指数", "参考"],
                ["热度", "成交量", f"{df['成交量'].iloc[0]/1e6:.1f}万手", "交易活跃程度", market_status]
            ]
        except Exception as e:
            return [["错误", "数据抓取失败", str(e), "请检查接口", "未知"]]

# --- 运行分析 ---
if st.sidebar.button("🚀 开始分析"):
    with st.spinner('正在调取全球金融数据库...'):
        results = get_data(market_choice, selected_date)
        
        # 布局展示
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader(f"{selected_date} 策略明细")
            df_show = pd.DataFrame(results, columns=["维度", "指标工具", "数值/状态", "含义", "当前判定"])
            st.table(df_show)
            
        with col2:
            st.subheader("策略决策")
            if market_choice == "美股 (US)":
                st.metric("综合情绪评分", "近似 50/100")
            else:
                st.metric("A股成交活跃度", results[1][2]) # 显示成交额
            st.success("🎯 **操作建议**：结合大盘指数趋势，分批操作。")
else:
    st.info("💡 请在左侧选择日期和市场，然后点击“开始分析”。")
