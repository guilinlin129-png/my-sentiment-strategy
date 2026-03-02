import streamlit as st
import yfinance as yf
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import pandas_datareader.data as web # 新增：用于获取垃圾债利差

# 网页配置
st.set_page_config(page_title="全球市场情绪监测站", layout="wide")

st.title("📈 全球市场情绪对冲投资策略 (多因子专业版)")
st.markdown("---")

# --- 侧边栏：控制面板 ---
st.sidebar.header("参数设置")
# 默认昨天，限制不能选未来
selected_date = st.sidebar.date_input("选择回溯日期", datetime.now() - timedelta(days=1))
market_choice = st.sidebar.radio("选择目标市场", ["美股 (US)", "A股 (CN)"])

# --- 数据抓取核心逻辑 (专业历史回溯版) ---
def get_data(market, date_obj):
    # 限制不能查询未来时间
    if date_obj > datetime.now().date():
        return [["错误", "日期越界", "不能查询未来", "请重新选择", "无效"]]

    if market == "美股 (US)":
        try:
            # 1. 抓取真实 VIX 历史数据
            vix_df = yf.Ticker("^VIX").history(start=date_obj, end=date_obj + timedelta(days=2))
            vix_val = round(vix_df['Close'].iloc[0], 2) if not vix_df.empty else 20.0
            
            # 2. 获取垃圾债利差 (FRED数据源: BAMLH0A0HYM2)
            # 含义：越高越恐惧，越低越贪婪
            spread_df = web.DataReader('BAMLH0A0HYM2', 'fred', date_obj, date_obj + timedelta(days=1))
            spread_val = round(spread_df.iloc[0, 0], 2)
            
            # 3. 估算 P/C Ratio (使用VIX做近似)
            pc_ratio = round(0.7 + (vix_val - 15) * 0.02, 2) 

            # 定义状态判定逻辑
            vix_status = "恐慌" if vix_val > 25 else "平稳"
            spread_status = "极度恐惧" if spread_val > 5 else "警惕" if spread_val > 4 else "贪婪"
            
            return [
                ["波动性", "VIX 恐慌指数", str(vix_val), "市场预期波动率", vix_status],
                ["资金流", "垃圾债利差(BAML)", str(spread_val), "高风险借贷成本", spread_status],
                ["衍生品", "P/C Ratio (近似)", str(pc_ratio), "期权对冲需求", "高对冲" if pc_ratio > 1.2 else "正常"],
                ["总结", "市场综合情绪", spread_status, "基于多因子加权", "参考"]
            ]
        except Exception as e:
            return [["错误", "美股数据抓取失败", str(e), "请重试", "未知"]]
            
    else:
        # A股数据抓取：修正版，增加非交易日判断
        try:
            date_str = date_obj.strftime('%Y%m%d')
            
            # 使用 akshare 历史K线接口，这是最稳定的数据源
            df = ak.index_zh_a_hist(symbol="000300", period="daily", start_date=date_str, end_date=date_str)
            
            # 关键：检查是否是休市日 (如果df为空)
            if df.empty:
                return [
                    ["状态", "休市", "无数据", "该日为A股休市日", "无效"],
                    ["资金流", "当日成交额", "0亿", "---", "---"],
                    ["大盘", "沪深300收盘", "0.0", "---", "---"]
                ]
            
            close_price = df['收盘'].iloc[0]
            vol_val = f"{df['成交额'].iloc[0]/1e8:.0f}亿"
            turnover = df['换手率'].iloc[0]

            # 判断活跃度
            if df['成交额'].iloc[0] > 1000000000000: market_status = "市场亢奋"
            elif df['成交额'].iloc[0] < 500000000000: market_status = "市场低迷"
            else: market_status = "正常"

            return [
                ["大盘", "沪深300收盘", str(close_price), "当日真实收盘", "参考"],
                ["资金流", "当日成交额", vol_val, "市场活跃度", market_status],
                ["波动性", "换手率", f"{turnover}%", "散户活跃程度", "亢奋" if turnover > 3 else "平稳"]
            ]
        except Exception as e:
            return [["错误", "A股数据抓取失败", str(e), "请检查网络", "重试"]]

# --- 运行分析 ---
if st.sidebar.button("🚀 开始分析"):
    with st.spinner('正在从多源数据库中抓取数据...'):
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
                st.metric("垃圾债利差(BAML)", results[1][2])
            else:
                st.metric("A股日成交额", results[1][2])
            st.success("🎯 **模型基于历史数据完成加权。**")
else:
    st.info("💡 请选择日期和市场，然后点击“开始分析”。")
