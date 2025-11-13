"""
GIS地图可视化模块
使用pyecharts创建交互式地图
"""

from pyecharts import options as opts
from pyecharts.charts import Map, Geo, Line, Bar, Pie, Grid, Page
from pyecharts.globals import ThemeType, ChartType
from typing import Dict, List
import json


class GISVisualization:
    """GIS可视化类"""
    
    def __init__(self, theme=ThemeType.LIGHT):
        self.theme = theme
    
    def create_population_map(self, data: Dict[str, int], title: str = "中国人口分布图") -> Map:
        """
        创建人口分布地图
        :param data: {省名: 人口数}
        :param title: 地图标题
        :return: Map对象
        """
        # 准备数据
        map_data = [(province, count) for province, count in data.items()]
        
        # 创建地图
        map_chart = (
            Map(init_opts=opts.InitOpts(
                theme=self.theme,
                width="1400px",
                height="800px"
            ))
            .add(
                series_name="人口数量",
                data_pair=map_data,
                maptype="china",
                is_map_symbol_show=False,
                label_opts=opts.LabelOpts(is_show=True, font_size=10),
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(
                    title=title,
                    subtitle="数据来源：人口信息数据库",
                    pos_left="center",
                    title_textstyle_opts=opts.TextStyleOpts(font_size=24)
                ),
                visualmap_opts=opts.VisualMapOpts(
                    min_=min(data.values()) if data else 0,
                    max_=max(data.values()) if data else 100,
                    range_text=["高", "低"],
                    is_piecewise=False,
                    orient="vertical",
                    pos_left="left",
                    pos_top="center",
                    textstyle_opts=opts.TextStyleOpts(font_size=12)
                ),
                tooltip_opts=opts.TooltipOpts(
                    trigger="item",
                    formatter="{b}<br/>人口数量: {c:,} 人"
                )
            )
        )
        
        return map_chart
    
    def create_density_map(self, data: Dict[str, float], title: str = "中国人口密度图") -> Map:
        """
        创建人口密度地图
        :param data: {省名: 密度}
        :param title: 地图标题
        :return: Map对象
        """
        map_data = [(province, density) for province, density in data.items()]
        
        map_chart = (
            Map(init_opts=opts.InitOpts(
                theme=self.theme,
                width="1400px",
                height="800px"
            ))
            .add(
                series_name="人口密度",
                data_pair=map_data,
                maptype="china",
                is_map_symbol_show=False,
                label_opts=opts.LabelOpts(is_show=True, font_size=10),
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(
                    title=title,
                    subtitle="单位：人/平方公里",
                    pos_left="center",
                    title_textstyle_opts=opts.TextStyleOpts(font_size=24)
                ),
                visualmap_opts=opts.VisualMapOpts(
                    min_=0,
                    max_=max(data.values()) if data else 100,
                    range_text=["高密度", "低密度"],
                    is_piecewise=False,
                    orient="vertical",
                    pos_left="left",
                    pos_top="center",
                    textstyle_opts=opts.TextStyleOpts(font_size=12),
                    range_color=["#FFFFE0", "#FFA500", "#FF4500", "#8B0000"]
                ),
                tooltip_opts=opts.TooltipOpts(
                    trigger="item",
                    formatter="{b}<br/>人口密度: {c} 人/km²"
                )
            )
        )
        
        return map_chart
    
    def create_marriage_map(self, data: Dict[str, Dict], title: str = "中国结婚人口分布图") -> Map:
        """
        创建结婚人口地图
        :param data: {省名: {'married_count': 数量, 'marriage_rate': 比例}}
        :param title: 地图标题
        :return: Map对象
        """
        map_data = [(province, info['married_count']) for province, info in data.items()]
        
        # 自定义tooltip格式
        tooltip_formatter = """
        function(params) {
            var data = """ + json.dumps(data) + """;
            var province = params.name;
            var info = data[province];
            if (info) {
                return province + '<br/>' +
                       '结婚人数: ' + info.married_count.toLocaleString() + ' 人<br/>' +
                       '结婚率: ' + info.marriage_rate + '%<br/>' +
                       '总人口: ' + info.total.toLocaleString() + ' 人';
            }
            return province;
        }
        """
        
        map_chart = (
            Map(init_opts=opts.InitOpts(
                theme=self.theme,
                width="1400px",
                height="800px"
            ))
            .add(
                series_name="结婚人数",
                data_pair=map_data,
                maptype="china",
                is_map_symbol_show=False,
                label_opts=opts.LabelOpts(is_show=True, font_size=10),
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(
                    title=title,
                    subtitle="鼠标悬停查看详细信息",
                    pos_left="center",
                    title_textstyle_opts=opts.TextStyleOpts(font_size=24)
                ),
                visualmap_opts=opts.VisualMapOpts(
                    min_=0,
                    max_=max([v['married_count'] for v in data.values()]) if data else 100,
                    range_text=["多", "少"],
                    is_piecewise=False,
                    orient="vertical",
                    pos_left="left",
                    pos_top="center",
                    textstyle_opts=opts.TextStyleOpts(font_size=12),
                    range_color=["#FFB6C1", "#FF69B4", "#FF1493", "#C71585"]
                ),
                tooltip_opts=opts.TooltipOpts(
                    trigger="item",
                    is_show=True
                )
            )
        )
        
        return map_chart
    
    def create_migration_map(self, data: List[Dict], title: str = "中国人口迁移流向图") -> Geo:
        """
        创建人口迁移流向图
        :param data: [{'from': 省名, 'to': 省名, 'count': 数量}]
        :param title: 地图标题
        :return: Geo对象
        """
        # 提取所有涉及的省份
        provinces = set()
        for item in data:
            provinces.add(item['from'])
            provinces.add(item['to'])
        
        # 准备省份坐标数据（用于标记）
        province_data = [(province, 1) for province in provinces]
        
        # 创建地理坐标图
        geo = (
            Geo(init_opts=opts.InitOpts(
                theme=self.theme,
                width="1400px",
                height="800px"
            ))
            .add_schema(maptype="china")
            .add(
                series_name="",
                data_pair=province_data,
                type_=ChartType.EFFECT_SCATTER,
                symbol_size=8,
                color="blue"
            )
        )
        
        # 添加迁移流向线
        for item in data[:50]:  # 只显示前50条，避免过于密集
            geo.add(
                series_name="",
                data_pair=[(item['from'], item['to'])],
                type_=ChartType.LINES,
                effect_opts=opts.EffectOpts(
                    symbol="arrow",
                    symbol_size=6,
                    color="#FF6347"
                ),
                linestyle_opts=opts.LineStyleOpts(
                    curve=0.2,
                    width=item['count'] / 20,  # 线宽根据人数调整
                    opacity=0.6
                ),
            )
        
        geo.set_global_opts(
            title_opts=opts.TitleOpts(
                title=title,
                subtitle="从户籍地迁移到现居住地",
                pos_left="center",
                title_textstyle_opts=opts.TextStyleOpts(font_size=24)
            ),
            tooltip_opts=opts.TooltipOpts(
                trigger="item",
                formatter="{b}"
            ),
            legend_opts=opts.LegendOpts(is_show=False)
        )
        
        return geo
    
    def create_gender_bar(self, data: Dict[str, Dict], title: str = "各省性别比例") -> Bar:
        """
        创建性别比例柱状图
        :param data: {省名: {'male': 数量, 'female': 数量, 'ratio': 性别比}}
        :param title: 标题
        :return: Bar对象
        """
        provinces = list(data.keys())[:15]  # 只显示前15个省份
        male_data = [data[p]['male'] for p in provinces]
        female_data = [data[p]['female'] for p in provinces]
        
        bar = (
            Bar(init_opts=opts.InitOpts(
                theme=self.theme,
                width="1400px",
                height="600px"
            ))
            .add_xaxis(provinces)
            .add_yaxis("男性", male_data, stack="stack1")
            .add_yaxis("女性", female_data, stack="stack1")
            .set_series_opts(
                label_opts=opts.LabelOpts(is_show=False),
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(
                    title=title,
                    pos_left="center",
                    title_textstyle_opts=opts.TextStyleOpts(font_size=20)
                ),
                xaxis_opts=opts.AxisOpts(
                    axislabel_opts=opts.LabelOpts(rotate=45)
                ),
                yaxis_opts=opts.AxisOpts(
                    name="人口数量",
                    axislabel_opts=opts.LabelOpts(formatter="{value}")
                ),
                tooltip_opts=opts.TooltipOpts(
                    trigger="axis",
                    axis_pointer_type="shadow"
                ),
                legend_opts=opts.LegendOpts(pos_top="5%")
            )
        )
        
        return bar
    
    def create_age_pie(self, data: Dict[str, Dict], province: str = None) -> Pie:
        """
        创建年龄分布饼图
        :param data: {省名: {'0-18': 数量, '18-35': 数量, '35-60': 数量, '60+': 数量}}
        :param province: 指定省份，如果为None则显示全国
        :return: Pie对象
        """
        if province and province in data:
            age_data = data[province]
            title = f"{province}年龄分布"
        else:
            # 汇总全国数据
            age_data = {'0-18': 0, '18-35': 0, '35-60': 0, '60+': 0}
            for prov_data in data.values():
                for age_group, count in prov_data.items():
                    age_data[age_group] += count
            title = "全国年龄分布"
        
        pie_data = [(age_group, count) for age_group, count in age_data.items()]
        
        pie = (
            Pie(init_opts=opts.InitOpts(
                theme=self.theme,
                width="800px",
                height="600px"
            ))
            .add(
                series_name="年龄段",
                data_pair=pie_data,
                radius=["30%", "75%"],
                rosetype="radius"
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(
                    title=title,
                    pos_left="center",
                    title_textstyle_opts=opts.TextStyleOpts(font_size=20)
                ),
                legend_opts=opts.LegendOpts(
                    orient="vertical",
                    pos_left="left",
                    pos_top="center"
                ),
                tooltip_opts=opts.TooltipOpts(
                    trigger="item",
                    formatter="{b}: {c} 人 ({d}%)"
                )
            )
            .set_series_opts(
                label_opts=opts.LabelOpts(formatter="{b}: {d}%")
            )
        )
        
        return pie
    
    def create_comprehensive_page(self, stats_data: Dict) -> Page:
        """
        创建综合统计页面
        :param stats_data: 综合统计数据
        :return: Page对象
        """
        page = Page(layout=Page.SimplePageLayout)
        
        # 1. 人口分布图
        if stats_data.get('population'):
            page.add(self.create_population_map(stats_data['population']))
        
        # 2. 人口密度图
        if stats_data.get('density'):
            page.add(self.create_density_map(stats_data['density']))
        
        # 3. 结婚人口图
        if stats_data.get('marriage'):
            page.add(self.create_marriage_map(stats_data['marriage']))
        
        # 4. 人口迁移图
        if stats_data.get('migration'):
            page.add(self.create_migration_map(stats_data['migration']))
        
        # 5. 性别比例图
        if stats_data.get('gender'):
            page.add(self.create_gender_bar(stats_data['gender']))
        
        # 6. 年龄分布图
        if stats_data.get('age'):
            page.add(self.create_age_pie(stats_data['age']))
        
        return page


if __name__ == '__main__':
    from data_statistics import PopulationStatistics
    
    print("=" * 60)
    print("🗺️  生成GIS可视化地图")
    print("=" * 60)
    
    # 获取统计数据
    print("\n📊 正在获取统计数据...")
    stats = PopulationStatistics()
    comprehensive_data = stats.get_comprehensive_statistics()
    stats.close()
    
    print("✅ 数据获取完成！")
    
    # 创建可视化
    print("\n🎨 正在生成可视化图表...")
    vis = GISVisualization(theme=ThemeType.LIGHT)
    
    # 1. 人口分布图
    print("   - 人口分布图")
    population_map = vis.create_population_map(comprehensive_data['population'])
    population_map.render("output/population_map.html")
    
    # 2. 人口密度图
    print("   - 人口密度图")
    density_map = vis.create_density_map(comprehensive_data['density'])
    density_map.render("output/density_map.html")
    
    # 3. 结婚人口图
    if comprehensive_data['marriage']:
        print("   - 结婚人口图")
        marriage_map = vis.create_marriage_map(comprehensive_data['marriage'])
        marriage_map.render("output/marriage_map.html")
    
    # 4. 人口迁移图
    if comprehensive_data['migration']:
        print("   - 人口迁移图")
        migration_map = vis.create_migration_map(comprehensive_data['migration'])
        migration_map.render("output/migration_map.html")
    
    # 5. 综合页面
    print("   - 综合统计页面")
    page = vis.create_comprehensive_page(comprehensive_data)
    page.render("output/comprehensive.html")
    
    print("\n" + "=" * 60)
    print("✅ 所有图表生成完成！")
    print("=" * 60)
    print("\n📁 文件保存在 output/ 目录:")
    print("   - population_map.html (人口分布图)")
    print("   - density_map.html (人口密度图)")
    print("   - marriage_map.html (结婚人口图)")
    print("   - migration_map.html (人口迁移图)")
    print("   - comprehensive.html (综合统计)")
    print("\n💡 用浏览器打开HTML文件即可查看交互式地图！")
    print("=" * 60)

