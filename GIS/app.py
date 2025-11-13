"""
人口GIS可视化Web应用
使用Streamlit创建交互式界面
"""

import streamlit as st
import streamlit.components.v1 as components
from data_statistics import PopulationStatistics
from gis_visualize import GISVisualization
from pyecharts.globals import ThemeType
import pandas as pd
import os

# 页面配置
st.set_page_config(
    page_title="中国人口GIS可视化系统",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS
st.markdown("""
<style>
    .main-title {
        text-align: center;
        color: #1f77b4;
        font-size: 3rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .sub-title {
        text-align: center;
        color: #666;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    .stat-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 1rem 0;
    }
    .stat-value {
        font-size: 2rem;
        font-weight: bold;
        color: #1f77b4;
    }
    .stat-label {
        font-size: 1rem;
        color: #666;
    }
</style>
""", unsafe_allow_html=True)

# 缓存数据获取函数
@st.cache_data(ttl=3600)
def load_statistics():
    """加载统计数据（缓存1小时）"""
    stats = PopulationStatistics()
    data = stats.get_comprehensive_statistics()
    stats.close()
    return data

@st.cache_resource
def get_visualization():
    """获取可视化对象"""
    return GISVisualization(theme=ThemeType.LIGHT)

def render_chart(chart, height=800):
    """渲染pyecharts图表"""
    html = chart.render_embed()
    components.html(html, height=height, scrolling=True)

def main():
    # 标题
    st.markdown('<h1 class="main-title">🗺️ 中国人口GIS可视化系统</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">基于人口信息数据库的交互式地理信息系统</p>', unsafe_allow_html=True)
    
    # 侧边栏
    st.sidebar.title("📊 功能导航")
    st.sidebar.markdown("---")
    
    # 选择可视化类型
    viz_type = st.sidebar.selectbox(
        "选择可视化类型",
        [
            "📈 概览统计",
            "🗺️ 人口分布图",
            "📍 人口密度图",
            "💑 结婚人口图",
            "🚀 人口迁移图",
            "👫 性别比例分析",
            "🎂 年龄分布分析",
            "🌈 民族分布分析",
            "📊 数据表格"
        ]
    )
    
    st.sidebar.markdown("---")
    st.sidebar.info("""
    **使用说明：**
    - 鼠标悬停在地图上查看详细信息
    - 可以缩放和拖动地图
    - 数据每小时自动刷新
    """)
    
    # 加载数据
    with st.spinner("🔄 正在加载数据..."):
        try:
            stats_data = load_statistics()
            vis = get_visualization()
        except Exception as e:
            st.error(f"❌ 数据加载失败：{str(e)}")
            st.info("💡 请检查数据库连接和配置")
            return
    
    st.sidebar.success(f"✅ 数据已加载\n\n更新时间：{stats_data['update_time']}")
    
    # 根据选择显示不同内容
    if viz_type == "📈 概览统计":
        show_overview(stats_data)
    
    elif viz_type == "🗺️ 人口分布图":
        st.header("🗺️ 人口分布图")
        st.markdown("---")
        if stats_data.get('population'):
            chart = vis.create_population_map(stats_data['population'])
            render_chart(chart)
        else:
            st.warning("暂无数据")
    
    elif viz_type == "📍 人口密度图":
        st.header("📍 人口密度图")
        st.markdown("---")
        if stats_data.get('density'):
            chart = vis.create_density_map(stats_data['density'])
            render_chart(chart)
        else:
            st.warning("暂无数据")
    
    elif viz_type == "💑 结婚人口图":
        st.header("💑 结婚人口分布图")
        st.markdown("---")
        if stats_data.get('marriage'):
            chart = vis.create_marriage_map(stats_data['marriage'])
            render_chart(chart)
            
            # 显示详细表格
            st.subheader("📊 详细数据")
            df = pd.DataFrame(stats_data['marriage']).T
            df = df.sort_values('married_count', ascending=False)
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("暂无结婚数据")
    
    elif viz_type == "🚀 人口迁移图":
        st.header("🚀 人口迁移流向图")
        st.markdown("---")
        if stats_data.get('migration'):
            chart = vis.create_migration_map(stats_data['migration'])
            render_chart(chart)
            
            # 显示迁移数据表格
            st.subheader("📊 主要迁移流向")
            df = pd.DataFrame(stats_data['migration'][:20])
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("暂无迁移数据")
    
    elif viz_type == "👫 性别比例分析":
        st.header("👫 性别比例分析")
        st.markdown("---")
        if stats_data.get('gender'):
            chart = vis.create_gender_bar(stats_data['gender'])
            render_chart(chart, height=700)
            
            # 性别比表格
            st.subheader("📊 性别比统计")
            df = pd.DataFrame(stats_data['gender']).T
            df = df.sort_values('ratio', ascending=False)
            st.dataframe(df, use_container_width=True)
            
            # 说明
            st.info("📌 性别比 = (男性人口 / 女性人口) × 100，正常范围为103-107")
        else:
            st.warning("暂无数据")
    
    elif viz_type == "🎂 年龄分布分析":
        st.header("🎂 年龄分布分析")
        st.markdown("---")
        
        if stats_data.get('age'):
            # 选择省份
            provinces = ['全国'] + list(stats_data['age'].keys())
            selected_province = st.selectbox("选择省份", provinces)
            
            if selected_province == '全国':
                chart = vis.create_age_pie(stats_data['age'], province=None)
            else:
                chart = vis.create_age_pie(stats_data['age'], province=selected_province)
            
            render_chart(chart, height=700)
            
            # 年龄分布表格
            st.subheader("📊 各省年龄分布")
            df = pd.DataFrame(stats_data['age']).T
            df = df[['0-18', '18-35', '35-60', '60+']]
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("暂无数据")
    
    elif viz_type == "🌈 民族分布分析":
        st.header("🌈 民族分布分析")
        st.markdown("---")
        
        if stats_data.get('ethnicity'):
            # 选择省份
            provinces = list(stats_data['ethnicity'].keys())
            selected_province = st.selectbox("选择省份", provinces)
            
            if selected_province in stats_data['ethnicity']:
                ethnicity_data = stats_data['ethnicity'][selected_province]
                
                # 创建饼图
                from pyecharts.charts import Pie
                from pyecharts import options as opts
                
                pie_data = [(k, v) for k, v in ethnicity_data.items()]
                pie = (
                    Pie(init_opts=opts.InitOpts(width="1000px", height="600px"))
                    .add(
                        series_name="民族",
                        data_pair=pie_data,
                        radius=["30%", "75%"],
                        rosetype="area"
                    )
                    .set_global_opts(
                        title_opts=opts.TitleOpts(
                            title=f"{selected_province}民族分布",
                            pos_left="center"
                        ),
                        legend_opts=opts.LegendOpts(
                            orient="vertical",
                            pos_left="left",
                            pos_top="center"
                        )
                    )
                    .set_series_opts(
                        label_opts=opts.LabelOpts(formatter="{b}: {d}%")
                    )
                )
                render_chart(pie, height=700)
                
                # 民族表格
                st.subheader("📊 详细数据")
                df = pd.DataFrame(list(ethnicity_data.items()), columns=['民族', '人口数'])
                df = df.sort_values('人口数', ascending=False)
                st.dataframe(df, use_container_width=True)
        else:
            st.warning("暂无数据")
    
    elif viz_type == "📊 数据表格":
        show_data_tables(stats_data)
    
    # 页脚
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 2rem;'>
        <p>📊 数据来源：人口信息数据库</p>
        <p>🔧 技术支持：Python + Streamlit + PyEcharts</p>
        <p>© 2025 中国人口GIS可视化系统</p>
    </div>
    """, unsafe_allow_html=True)

def show_overview(stats_data):
    """显示概览统计"""
    st.header("📈 数据概览")
    st.markdown("---")
    
    # 统计卡片
    col1, col2, col3, col4 = st.columns(4)
    
    total_population = sum(stats_data['population'].values()) if stats_data.get('population') else 0
    num_provinces = len(stats_data['population']) if stats_data.get('population') else 0
    total_married = sum([v['married_count'] for v in stats_data['marriage'].values()]) if stats_data.get('marriage') else 0
    num_migrations = len(stats_data['migration']) if stats_data.get('migration') else 0
    
    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{total_population:,}</div>
            <div class="stat-label">📊 总人口数</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{num_provinces}</div>
            <div class="stat-label">🗺️ 省级行政区</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{total_married:,}</div>
            <div class="stat-label">💑 已婚人口</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{num_migrations:,}</div>
            <div class="stat-label">🚀 迁移流向</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # TOP排行
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏆 人口数量TOP10")
        if stats_data.get('population'):
            top_10 = sorted(stats_data['population'].items(), key=lambda x: x[1], reverse=True)[:10]
            df = pd.DataFrame(top_10, columns=['省份', '人口数'])
            df['排名'] = range(1, len(df) + 1)
            df = df[['排名', '省份', '人口数']]
            st.dataframe(df, use_container_width=True, hide_index=True)
    
    with col2:
        st.subheader("🏆 人口密度TOP10")
        if stats_data.get('density'):
            top_10 = sorted(stats_data['density'].items(), key=lambda x: x[1], reverse=True)[:10]
            df = pd.DataFrame(top_10, columns=['省份', '密度(人/km²)'])
            df['排名'] = range(1, len(df) + 1)
            df = df[['排名', '省份', '密度(人/km²)']]
            st.dataframe(df, use_container_width=True, hide_index=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 迁移流向
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🚀 主要迁入地TOP10")
        if stats_data.get('migration'):
            migration_in = {}
            for item in stats_data['migration']:
                to_prov = item['to']
                migration_in[to_prov] = migration_in.get(to_prov, 0) + item['count']
            top_10 = sorted(migration_in.items(), key=lambda x: x[1], reverse=True)[:10]
            df = pd.DataFrame(top_10, columns=['省份', '迁入人口'])
            df['排名'] = range(1, len(df) + 1)
            df = df[['排名', '省份', '迁入人口']]
            st.dataframe(df, use_container_width=True, hide_index=True)
    
    with col2:
        st.subheader("🚀 主要迁出地TOP10")
        if stats_data.get('migration'):
            migration_out = {}
            for item in stats_data['migration']:
                from_prov = item['from']
                migration_out[from_prov] = migration_out.get(from_prov, 0) + item['count']
            top_10 = sorted(migration_out.items(), key=lambda x: x[1], reverse=True)[:10]
            df = pd.DataFrame(top_10, columns=['省份', '迁出人口'])
            df['排名'] = range(1, len(df) + 1)
            df = df[['排名', '省份', '迁出人口']]
            st.dataframe(df, use_container_width=True, hide_index=True)

def show_data_tables(stats_data):
    """显示数据表格"""
    st.header("📊 详细数据表格")
    st.markdown("---")
    
    tab1, tab2, tab3, tab4 = st.tabs(["人口统计", "婚姻统计", "性别统计", "年龄统计"])
    
    with tab1:
        st.subheader("各省人口统计")
        if stats_data.get('population') and stats_data.get('density'):
            data = []
            for province in stats_data['population'].keys():
                data.append({
                    '省份': province,
                    '人口数': stats_data['population'][province],
                    '人口密度(人/km²)': stats_data['density'].get(province, 0)
                })
            df = pd.DataFrame(data)
            df = df.sort_values('人口数', ascending=False)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # 下载按钮
            csv = df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 下载数据",
                data=csv,
                file_name="population_stats.csv",
                mime="text/csv"
            )
    
    with tab2:
        st.subheader("各省婚姻统计")
        if stats_data.get('marriage'):
            df = pd.DataFrame(stats_data['marriage']).T
            df = df.reset_index()
            df.columns = ['省份', '已婚人数', '结婚率(%)', '总人口']
            df = df.sort_values('已婚人数', ascending=False)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            csv = df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 下载数据",
                data=csv,
                file_name="marriage_stats.csv",
                mime="text/csv"
            )
    
    with tab3:
        st.subheader("各省性别统计")
        if stats_data.get('gender'):
            df = pd.DataFrame(stats_data['gender']).T
            df = df.reset_index()
            df.columns = ['省份', '男性', '女性', '性别比']
            df = df.sort_values('性别比', ascending=False)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            csv = df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 下载数据",
                data=csv,
                file_name="gender_stats.csv",
                mime="text/csv"
            )
    
    with tab4:
        st.subheader("各省年龄统计")
        if stats_data.get('age'):
            df = pd.DataFrame(stats_data['age']).T
            df = df.reset_index()
            df.columns = ['省份', '0-18岁', '18-35岁', '35-60岁', '60岁以上']
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            csv = df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 下载数据",
                data=csv,
                file_name="age_stats.csv",
                mime="text/csv"
            )


if __name__ == '__main__':
    main()

