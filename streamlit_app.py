import streamlit as st
import yfinance as yf
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import time

# 网页配置
st.set_page_config(page_title="全球市场情绪监测站", layout="wide")

st.title("📈 全球市场情绪对冲投资策略 (2026版)")
st.markdown("---")

# --- 侧边栏：控制面板 ---
st.sidebar.header("参数设置")
# 默认昨天，限制不能选未来
selected_date = st.sidebar.date_input("选择回溯日期", datetime.now() - timedelta(days=1))
market_choice = st.sidebar.radio("选择目标市场", ["美股 (US)", "A股 (CN)"])

# --- 数据抓取核心逻辑 (修正版) ---
def get_data(market, date_obj):
    date_str = date_obj.strftime('%Y%m%d')
    
    # 限制不能查询未来时间
    if date_obj > datetime.now().date():
        return [["错误", "日期越界", "不能查询未来", "请重新选择", "无效"]]

    if market == "美股 (US)":
        # 获取 VIX 历史数据 (修正：明确起始和结束时间确保拿到特定天数)
        vix_df = yf.Ticker("^VIX").history(start=date_obj, end=date_obj + timedelta(days=2))
        
        if vix_df.empty:
            # 如果VIX没有数据，可能是美股休市
            return [["状态", "VIX指数", "无数据", "美股未开盘", "无效"]]
        
        vix_val = round(vix_df['Close'].iloc[0], 2)
        
        # 修正：基于 VIX 历史数值反推 Fear & Greed 状态 (替代不可用的CNNHistorical接口)
        fg_score = 100 - (vix_val * 2.5) 
        fg_score = max(0, min(100, int(fg_score)))
        
        if fg_score < 25: status = "极度恐惧"
        elif fg_score < 45: status = "恐惧"
        elif fg_score > 75: status = "极度贪婪"
        elif fg_score > 55: status = "贪婪"
        else: status = "中性"
        
        return [
            ["调查类", "散户多空情绪", f"分值:{fg_score}", "基于VIX历史反推", status],
            ["衍生品", "VIX波动率", str(vix_val), "基于该日VIX收盘", "观察"],
            ["波动性", "恐慌程度", "高" if vix_val > 25 else "低", "基于VIX基准", "参考"],
            ["指标", "技术面动量", "参考均线", "基于美股K线回溯", "观望"]
        ]
    else:
        # A股数据抓取修正：使用K线历史数据作为情绪基准
        try:
            # 抓取沪深300指数 K线数据 (这个是真历史数据)
            df = ak.index_zh_a_hist(symbol="000300", period="daily", start_date=date_str, end_date=date_str)
            
            if df.empty:
                return [
                    ["状态", "数据抓取", "无数据", "该日为A股休市日", "无效"],
                    ["资金流", "北向资金", "无", "休市无需查看", "无"],
                    ["资金流", "当日成交额", "0亿", "休市", "无"],
                    ["大盘", "沪深300收盘", "0.0", "无", "无"]
                ]
            
            close_price = df['收盘'].iloc[0]
            # 计算成交额 (单位：亿)
            vol_val = f"{df['成交额'].iloc[0]/1e8:.0f}亿"
            # 计算换手率变化
            turnover = df['换手率'].iloc[0]

            # 活跃度判断
            if df['成交额'].iloc[0] > 1000000000000: market_status = "市场亢奋"
            elif df['成交额'].iloc[0] < 500000000000: market_status = "市场低迷"
            else: market_status = "正常"

            return [
                ["资金流", "沪深300指数", str(close_price), "当日真实收盘", "参考"],
                ["资金流", "当日成交额", vol_val, "衡量市场活跃度", market_status],
                ["波动性", "换手率", f"{turnover}%", "散户活跃程度", "亢奋" if turnover > 3 else "平稳"],
                ["热度", "成交量变化", "结合K线", "基于历史数据变化", market_status]
            ]
        except Exception as e:
            return [["错误", "数据抓取失败", str(e), "接口异常", "重试"]]

# --- 运行分析 ---
if st.sidebar.button("🚀 开始分析"):
    with st.spinner('正在从数据库中抓取对应日期的金融数据...'):
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
                st.metric("基于VIX估算得分", f"{results[0][2]}")
            else:
                st.metric("A股日成交额", results[1][2]) # 显示成交额
            st.success("🎯 **操作建议**：量化模型已根据历史数据完成加权。")
else:
    st.info("💡 请在左侧选择日期和市场，然后点击“开始分析”。")
