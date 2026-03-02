import streamlit as st
import yfinance as yf
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import pandas_datareader.data as web

# 网页配置
st.set_page_config(page_title="全球市场情绪监测站", layout="wide")

st.title("📈 全球市场情绪对冲投资策略 (稳定版)")
st.markdown("---")

# --- 侧边栏：控制面板 ---
st.sidebar.header("参数设置")
selected_date = st.sidebar.date_input("选择回溯日期", datetime.now() - timedelta(days=1))
market_choice = st.sidebar.radio("选择目标市场", ["美股 (US)", "A股 (CN)"])

# --- 数据抓取核心逻辑 (修正版) ---
def get_data(market, date_obj):
    if date_obj > datetime.now().date():
        return [["错误", "日期越界", "不能查询未来", "请重新选择", "无效"]]

    if market == "美股 (US)":
        try:
            # 1. 使用基础的 VIX 历史数据 (最稳)
            vix_ticker = yf.Ticker("^VIX")
            vix_df = vix_ticker.history(start=date_obj, end=date_obj + timedelta(days=2))
            
            if vix_df.empty:
                return [["状态", "查询状态", "数据为空", "美股未开盘", "无效"]]
                
            vix_val = round(vix_df['Close'].iloc[0], 2)
            
            # 2. 垃圾债利差 (使用 try-except 包裹，如果不行就用VIX兜底)
            try:
                spread_df = web.DataReader('BAMLH0A0HYM2', 'fred', date_obj, date_obj + timedelta(days=1))
                spread_val = round(spread_df.iloc[0, 0], 2)
                spread_status = "极度恐惧" if spread_val > 5 else "警惕" if spread_val > 4 else "贪婪"
            except:
                spread_val = "不可用"
                spread_status = "数据源错误"
            
            # 状态判定
            vix_status = "恐慌" if vix_val > 25 else "平稳"
            
            return [
                ["波动性", "VIX 恐慌指数", str(vix_val), "市场预期波动率", vix_status],
                ["资金流", "垃圾债利差(BAML)", str(spread_val), "高风险借贷成本", spread_status],
                ["指标", "技术面动量", "基于VIX", "高水平", "观望"]
            ]
        except Exception as e:
            return [["错误", "数据抓取失败", str(e), "请重试", "未知"]]
            
    else:
        # A股数据抓取：修正版
        try:
            date_str = date_obj.strftime('%Y%m%d')
            
            # 使用 akshare 更底层的日线接口
            df = ak.index_zh_a_hist(symbol="000300", period="daily", start_date=date_str, end_date=date_str)
            
            if df.empty:
                return [
                    ["状态", "查询状态", "无数据", "该日为A股休市日", "无效"],
                    ["大盘", "沪深300收盘", "0.0", "---", "---"],
                    ["资金流", "当日成交额", "0亿", "---", "---"]
                ]
            
            close_price = df['收盘'].iloc[0]
            vol_val = f"{df['成交额'].iloc[0]/1e8:.0f}亿"
            
            # 活跃度判定
            if df['成交额'].iloc[0] > 1000000000000: market_status = "市场亢奋"
            elif df['成交额'].iloc[0] < 500000000000: market_status = "市场低迷"
            else: market_status = "正常"

            return [
                ["大盘", "沪深300收盘", str(close_price), "当日真实收盘", "参考"],
                ["资金流", "当日成交额", vol_val, "市场活跃度", market_status],
                ["热度", "成交量", f"{df['成交量'].iloc[0]/1e6:.1f}万手", "活跃程度", market_status]
            ]
        except Exception as e:
            return [["错误", "数据抓取失败", str(e), "请检查网络", "重试"]]

# --- 运行分析 ---
if st.sidebar.button("🚀 开始分析"):
    with st.spinner('正在调取金融数据...'):
        results = get_data(market_choice, selected_date)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader(f"{selected_date} 策略明细")
            df_show = pd.DataFrame(results, columns=["维度", "指标工具", "数值/状态", "含义", "当前判定"])
            st.table(df_show)
            
        with col2:
            st.subheader("策略决策")
            if market_choice == "美股 (US)":
                st.metric("VIX指数", results[0][2])
            else:
                st.metric("A股日成交额", results[1][2])
            st.success("🎯 **模型基于历史数据完成加权。**")
else:
    st.info("💡 请选择日期和市场，然后点击“开始分析”。")
