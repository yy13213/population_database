# -*-coding:utf-8-*-
"""
身份证OCR识别系统 - Streamlit Web界面
使用GPT-4 Vision识别身份证信息，并存入数据库
支持单张身份证OCR识别和Excel批量导入
"""
import io
import os
import json
import base64
import pymysql
import pandas as pd
import streamlit as st
from datetime import datetime, date
from openai import OpenAI
from PIL import Image

# 页面配置
st.set_page_config(
    page_title="身份证OCR识别系统",
    page_icon="🪪",
    layout="wide"
)

# 数据库配置
MYSQL_CONFIG = {

}

# OpenAI配置
@st.cache_resource
def get_openai_client():
    return OpenAI(
        base_url="",
        api_key=""
    )

@st.cache_data
def load_province_data():
    """加载省份地址码数据"""
    with open('./province_data.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def save_id_card_photo(image, id_no):
    """
    保存身份证照片到images目录
    :param image: PIL Image对象
    :param id_no: 身份证号
    :return: 照片存储路径
    """
    # 确保images目录存在
    images_dir = 'images'
    if not os.path.exists(images_dir):
        os.makedirs(images_dir)
    
    # 生成文件名：身份证号_存储时间.jpg
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{id_no}_{timestamp}.jpg"
    filepath = os.path.join(images_dir, filename)
    
    # 如果图片是RGBA模式（包含透明通道），转换为RGB
    if image.mode in ('RGBA', 'LA', 'P'):
        # 创建白色背景
        background = Image.new('RGB', image.size, (255, 255, 255))
        # 如果有透明通道，使用alpha合成
        if image.mode == 'RGBA':
            background.paste(image, mask=image.split()[3])  # 使用alpha通道作为mask
        else:
            background.paste(image)
        image = background
    elif image.mode != 'RGB':
        # 其他模式直接转换为RGB
        image = image.convert('RGB')
    
    # 保存图片
    image.save(filepath, 'JPEG', quality=95)
    
    # 返回相对路径
    return filepath

def parse_id_card_number(id_no):
    """从身份证号中解析信息"""
    area_code = id_no[0:6]
    
    birth_str = id_no[6:14]
    birth_year = int(birth_str[0:4])
    birth_month = int(birth_str[4:6])
    birth_day = int(birth_str[6:8])
    birth_date = f"{birth_year}-{birth_month:02d}-{birth_day:02d}"
    
    gender_code = int(id_no[16])
    gender = "男" if gender_code % 2 == 1 else "女"
    
    return area_code, birth_date, gender

def find_address_by_code(area_code, province_data):
    """根据地址码查找对应的省市区"""
    for province_name, province_info in province_data.items():
        address_codes = province_info.get('地址码', {})
        for code, address_str in address_codes.items():
            if code == area_code:
                parts = address_str.split('-')
                if len(parts) >= 3:
                    return parts[0], parts[1], parts[2]
                elif len(parts) == 2:
                    return parts[0], parts[1], ''
                else:
                    return parts[0], '', ''
    return '', '', ''

def parse_address(address_str):
    """从地址字符串中提取省市区"""
    parts = address_str.replace('省', '省|').replace('市', '市|').replace('区', '区|').replace('县', '县|').split('|')
    parts = [p.strip() for p in parts if p.strip()]
    
    province = parts[0] if len(parts) >= 1 else ''
    city = parts[1] if len(parts) >= 2 else ''
    district = parts[2] if len(parts) >= 3 else ''
    
    return province, city, district

def recognize_id_card(image_bytes):
    """使用GPT-4 Vision识别身份证信息"""
    client = get_openai_client()
    
    image_base64 = base64.b64encode(image_bytes).decode()
    
    prompt = """
请识别这张身份证图片中的信息，并以JSON格式返回。

要求：
1. 仔细识别身份证上的所有文字信息
2. 身份证号码必须准确，18位数字
3. 地址要完整，包含省市区
4. 返回纯JSON格式，不要有其他文字

返回格式示例：
{
    "id_no": "110101199001011234",
    "name": "张三",
    "ethnicity": "汉族",
    "address": "北京市东城区某某街道某某号"
}

注意：
- id_no: 18位身份证号码
- name: 姓名
- ethnicity: 民族
- address: 住址（尽可能详细）
"""
    
    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        }
                    }
                ]
            }
        ],
        max_tokens=500
    )
    
    result_text = response.choices[0].message.content
    
    # 提取JSON
    if "```json" in result_text:
        result_text = result_text.split("```json")[1].split("```")[0].strip()
    elif "```" in result_text:
        result_text = result_text.split("```")[1].split("```")[0].strip()
    
    return json.loads(result_text)

def process_id_card_data(ocr_result, province_data, source_code, photo_path=None):
    """处理OCR识别结果，生成完整的人口数据"""
    id_no = ocr_result.get('id_no', '')
    
    if not id_no or len(id_no) != 18:
        raise Exception("身份证号码格式错误")
    
    area_code, birth_date, gender = parse_id_card_number(id_no)
    hukou_province, hukou_city, hukou_district = find_address_by_code(area_code, province_data)
    
    address_str = ocr_result.get('address', '')
    cur_province, cur_city, cur_district = parse_address(address_str)
    
    person_data = {
        'id_no': id_no,
        'name': ocr_result.get('name', ''),
        'former_name': None,
        'gender': gender,
        'birth_date': birth_date,
        'ethnicity': ocr_result.get('ethnicity', ''),
        'marital_status': None,
        'education_level': None,
        'hukou_province': hukou_province,
        'hukou_city': hukou_city,
        'hukou_district': hukou_district,
        'housing': None,
        'cur_province': cur_province,
        'cur_city': cur_city,
        'cur_district': cur_district,
        'hukou_type': None,
        'income': None,
        'processed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'source': source_code,  # 使用用户输入的source
        'id_card_photo': photo_path  # 身份证照片路径
    }
    
    return person_data

def save_to_database(person_data):
    """保存数据到数据库"""
    connection = pymysql.connect(**MYSQL_CONFIG)
    cursor = connection.cursor()
    
    sql = """
    INSERT INTO population 
    (id_no, name, former_name, gender, birth_date, ethnicity, marital_status, 
     education_level, hukou_province, hukou_city, hukou_district, housing, 
     cur_province, cur_city, cur_district, hukou_type, income, processed_at, source, id_card_photo)
    VALUES 
    (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    data = (
        person_data['id_no'], person_data['name'], person_data['former_name'],
        person_data['gender'], person_data['birth_date'], person_data['ethnicity'],
        person_data['marital_status'], person_data['education_level'],
        person_data['hukou_province'], person_data['hukou_city'], person_data['hukou_district'],
        person_data['housing'], person_data['cur_province'], person_data['cur_city'],
        person_data['cur_district'], person_data['hukou_type'], person_data['income'],
        person_data['processed_at'], person_data['source'], person_data.get('id_card_photo')
    )
    
    cursor.execute(sql, data)
    connection.commit()
    connection.close()

def parse_excel_file(uploaded_file):
    """解析Excel文件"""
    try:
        # 读取Excel文件
        df = pd.read_excel(uploaded_file, sheet_name='人口信息表')
        
        # 删除说明行（如果存在）
        if '18位身份证号' in str(df.iloc[0, 0]):
            df = df.iloc[1:]
        
        # 删除空行
        df = df.dropna(how='all')
        
        # 重置索引
        df = df.reset_index(drop=True)
        
        return df
    except Exception as e:
        raise Exception(f"Excel文件解析失败: {str(e)}")

def validate_excel_data(df):
    """验证Excel数据"""
    errors = []
    
    for idx, row in df.iterrows():
        row_num = idx + 2  # Excel行号（从1开始，加上表头）
        
        # 验证必填字段
        if pd.isna(row['身份证号码']) or str(row['身份证号码']).strip() == '':
            errors.append(f"第{row_num}行：身份证号码为空")
        elif len(str(row['身份证号码']).strip()) != 18:
            errors.append(f"第{row_num}行：身份证号码长度不正确")
        
        if pd.isna(row['姓名']) or str(row['姓名']).strip() == '':
            errors.append(f"第{row_num}行：姓名为空")
        
        if pd.isna(row['性别']) or str(row['性别']).strip() not in ['男', '女']:
            errors.append(f"第{row_num}行：性别必须是'男'或'女'")
    
    return errors

def excel_to_person_data(row, source_code):
    """将Excel行数据转换为person_data格式"""
    
    # 处理空值
    def safe_str(val):
        return None if pd.isna(val) or str(val).strip() == '' else str(val).strip()
    
    def safe_float(val):
        try:
            return None if pd.isna(val) else float(val)
        except:
            return None
    
    person_data = {
        'id_no': safe_str(row['身份证号码']),
        'name': safe_str(row['姓名']),
        'former_name': safe_str(row['曾用名']),
        'gender': safe_str(row['性别']),
        'birth_date': safe_str(row['出生年月日']),
        'ethnicity': safe_str(row['民族']),
        'marital_status': safe_str(row['婚姻状况']),
        'education_level': safe_str(row['受教育程度']),
        'hukou_province': safe_str(row['户籍所在地-省']),
        'hukou_city': safe_str(row['户籍所在地-市']),
        'hukou_district': safe_str(row['户籍所在地-区']),
        'housing': safe_str(row['住房情况']),
        'cur_province': safe_str(row['现居住地-省']),
        'cur_city': safe_str(row['现居住地-市']),
        'cur_district': safe_str(row['现居住地-区']),
        'hukou_type': safe_str(row['户籍登记类型']),
        'income': safe_float(row['收入情况(元/月)']),
        'processed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'source': source_code,  # 使用用户输入的source
        'id_card_photo': None  # Excel导入不包含照片
    }
    
    return person_data

def batch_save_to_database(data_list):
    """批量保存到数据库"""
    connection = pymysql.connect(**MYSQL_CONFIG)
    cursor = connection.cursor()
    
    success_count = 0
    fail_count = 0
    errors = []
    
    sql = """
    INSERT INTO population 
    (id_no, name, former_name, gender, birth_date, ethnicity, marital_status, 
     education_level, hukou_province, hukou_city, hukou_district, housing, 
     cur_province, cur_city, cur_district, hukou_type, income, processed_at, source)
    VALUES 
    (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    for idx, person_data in enumerate(data_list):
        try:
            data = (
                person_data['id_no'], person_data['name'], person_data['former_name'],
                person_data['gender'], person_data['birth_date'], person_data['ethnicity'],
                person_data['marital_status'], person_data['education_level'],
                person_data['hukou_province'], person_data['hukou_city'], person_data['hukou_district'],
                person_data['housing'], person_data['cur_province'], person_data['cur_city'],
                person_data['cur_district'], person_data['hukou_type'], person_data['income'],
                person_data['processed_at'], person_data['source']
            )
            
            cursor.execute(sql, data)
            connection.commit()
            success_count += 1
        
        except pymysql.err.IntegrityError as e:
            fail_count += 1
            if '1062' in str(e):
                errors.append(f"第{idx+1}条：身份证号 {person_data['id_no']} 已存在")
            else:
                errors.append(f"第{idx+1}条：{str(e)}")
        
        except Exception as e:
            fail_count += 1
            errors.append(f"第{idx+1}条：{str(e)}")
    
    connection.close()
    
    return success_count, fail_count, errors

# Streamlit界面
def main():
    st.title("🪪 人口信息录入系统")
    st.markdown("支持身份证OCR识别和Excel批量导入")
    st.markdown("---")
    
    # 侧边栏
    with st.sidebar:
        st.header("👤 数据输入者信息")
        
        # 数据来源输入
        source_input = st.text_input(
            "数据来源代号",
            value=st.session_state.get('source_code', ''),
            placeholder="请输入您的代号，例如: YY",
            help="此代号将作为source字段写入数据库",
            key="source_input"
        )
        
        # 保存到session state
        if source_input:
            st.session_state['source_code'] = source_input
            st.success(f"✅ 当前数据来源：{source_input}")
        else:
            st.warning("⚠️ 请先输入数据来源代号")
        
        st.markdown("---")
        
        st.header("📝 使用说明")
        
        st.subheader("方式1：OCR识别")
        st.markdown("""
        1. 上传身份证照片（PNG或JPG）
        2. 等待AI识别身份证信息
        3. 核对识别结果
        4. 确认后保存到数据库
        """)
        
        st.subheader("方式2：Excel批量导入")
        st.markdown("""
        1. 下载Excel模板
        2. 填写人口信息
        3. 上传Excel文件
        4. 核对数据后批量导入
        """)
        
        st.markdown("---")
        st.info("💡 OCR会自动从身份证号中解析性别、出生日期和户籍地址")
    
    # 创建两个标签页
    tab1, tab2 = st.tabs(["🪪 身份证OCR识别", "📊 Excel批量导入"])
    
    # ==================== 标签页1：OCR识别 ====================
    with tab1:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("📤 上传身份证照片")
            uploaded_file = st.file_uploader(
                "选择身份证图片",
                type=['png', 'jpg', 'jpeg'],
                help="支持PNG、JPG格式",
                key="ocr_uploader"
            )
            
            if uploaded_file is not None:
                # 显示上传的图片
                image = Image.open(uploaded_file)
                st.image(image, caption="上传的身份证照片")
                
            # 识别按钮
            if st.button("🔍 开始识别", type="primary", use_container_width=True):
                # 检查source是否输入
                if 'source_code' not in st.session_state or not st.session_state['source_code']:
                    st.error("❌ 请先在侧边栏输入数据来源代号！")
                else:
                    with st.spinner("正在识别身份证信息..."):
                        try:
                            # 转换为字节
                            img_byte_arr = io.BytesIO()
                            image.save(img_byte_arr, format='PNG')
                            image_bytes = img_byte_arr.getvalue()
                            
                            # OCR识别
                            province_data = load_province_data()
                            ocr_result = recognize_id_card(image_bytes)
                            
                            # 先获取身份证号，用于保存图片
                            id_no = ocr_result.get('id_no', '')
                            if id_no and len(id_no) == 18:
                                # 保存身份证照片
                                photo_path = save_id_card_photo(image, id_no)
                            else:
                                photo_path = None
                            
                            # 处理数据
                            source_code = st.session_state['source_code']
                            person_data = process_id_card_data(ocr_result, province_data, source_code, photo_path)
                            
                            # 存储到session state（包括原始图片，用于显示）
                            st.session_state['person_data'] = person_data
                            st.session_state['ocr_result'] = ocr_result
                            st.session_state['uploaded_image'] = image
                            
                            st.success("✅ 识别成功！照片已保存")
                            st.rerun()
                        
                        except Exception as e:
                            st.error(f"❌ 识别失败：{str(e)}")
        
        with col2:
            st.subheader("📋 识别结果")
            
            if 'person_data' in st.session_state:
                person_data = st.session_state['person_data']
                
                # 显示识别结果
                st.markdown("#### 基本信息")
                info_col1, info_col2 = st.columns(2)
                with info_col1:
                    st.text_input("身份证号码", person_data['id_no'], disabled=True)
                    st.text_input("性别", person_data['gender'], disabled=True)
                    st.text_input("民族", person_data['ethnicity'], disabled=True)
                with info_col2:
                    st.text_input("姓名", person_data['name'], disabled=True)
                    st.text_input("出生日期", person_data['birth_date'], disabled=True)
                    st.text_input("数据来源", person_data['source'], disabled=True)
                
                st.markdown("#### 户籍信息（从身份证号解析）")
                hukou_col1, hukou_col2, hukou_col3 = st.columns(3)
                with hukou_col1:
                    st.text_input("省份", person_data['hukou_province'], disabled=True, key="hukou_prov")
                with hukou_col2:
                    st.text_input("城市", person_data['hukou_city'], disabled=True, key="hukou_city")
                with hukou_col3:
                    st.text_input("区县", person_data['hukou_district'], disabled=True, key="hukou_dist")
                
                st.markdown("#### 现居住地（从身份证地址识别）")
                cur_col1, cur_col2, cur_col3 = st.columns(3)
                with cur_col1:
                    st.text_input("省份", person_data['cur_province'], disabled=True, key="cur_prov")
                with cur_col2:
                    st.text_input("城市", person_data['cur_city'], disabled=True, key="cur_city")
                with cur_col3:
                    st.text_input("区县", person_data['cur_district'], disabled=True, key="cur_dist")
                
                st.markdown("---")
                
                # 显示照片路径
                if person_data.get('id_card_photo'):
                    st.info(f"📸 身份证照片已保存至：{person_data['id_card_photo']}")
                
                # 显示完整的JSON数据
                with st.expander("📄 查看完整数据（JSON格式）"):
                    st.json(person_data)
                
                # 保存按钮
                st.markdown("### 💾 保存到数据库")
                col_save1, col_save2 = st.columns(2)
                
                with col_save1:
                    if st.button("✅ 确认保存", type="primary", use_container_width=True, key="ocr_save"):
                        try:
                            save_to_database(person_data)
                            st.success("✅ 数据已成功保存到数据库！")
                            # 清除session state
                            del st.session_state['person_data']
                            del st.session_state['ocr_result']
                        except pymysql.err.IntegrityError as e:
                            if '1062' in str(e):
                                st.error("❌ 该身份证号已存在于数据库中")
                            else:
                                st.error(f"❌ 保存失败：{str(e)}")
                        except Exception as e:
                            st.error(f"❌ 保存失败：{str(e)}")
                
                with col_save2:
                    if st.button("❌ 取消", use_container_width=True, key="ocr_cancel"):
                        del st.session_state['person_data']
                        del st.session_state['ocr_result']
                        st.info("已取消保存")
                        st.rerun()
            
            else:
                st.info("👈 请先上传身份证照片并点击识别")
    
    # ==================== 标签页2：Excel批量导入 ====================
    with tab2:
        st.subheader("📊 Excel批量导入")
        
        # 模板下载区域
        col_template1, col_template2 = st.columns([1, 1])
        
        with col_template1:
            st.markdown("#### 📥 第一步：下载模板")
            st.info("请先下载Excel模板，填写完整后再上传")
            
            # 提供模板下载链接
            template_info = st.expander("📋 模板说明", expanded=False)
            with template_info:
                st.markdown("""
                **必填字段**：
                - 身份证号码（18位）
                - 姓名
                - 性别（男/女）
                
                **可选字段**：
                - 其他所有字段均可选填
                - 空值将保存为NULL
                """)
        
        
        with col_template2:
            st.markdown("#### 📤 第二步：上传Excel文件")
            excel_file = st.file_uploader(
                "选择Excel文件",
                type=['xlsx', 'xls'],
                help="支持.xlsx和.xls格式",
                key="excel_uploader"
            )
            
            if excel_file is not None:
                st.success(f"✅ 已选择文件：{excel_file.name}")
                
                if st.button("📖 解析Excel文件", type="primary", use_container_width=True):
                    # 检查source是否输入
                    if 'source_code' not in st.session_state or not st.session_state['source_code']:
                        st.error("❌ 请先在侧边栏输入数据来源代号！")
                    else:
                        with st.spinner("正在解析Excel文件..."):
                            try:
                                # 解析Excel
                                df = parse_excel_file(excel_file)
                                
                                # 验证数据
                                errors = validate_excel_data(df)
                                
                                if errors:
                                    st.error(f"❌ 数据验证失败，发现 {len(errors)} 个错误：")
                                    for error in errors[:10]:  # 只显示前10个错误
                                        st.warning(error)
                                    if len(errors) > 10:
                                        st.warning(f"...还有 {len(errors)-10} 个错误未显示")
                                else:
                                    # 获取source_code
                                    source_code = st.session_state['source_code']
                                    
                                    # 转换为person_data格式
                                    data_list = []
                                    for _, row in df.iterrows():
                                        person_data = excel_to_person_data(row, source_code)
                                        data_list.append(person_data)
                                    
                                    # 存储到session state
                                    st.session_state['excel_data'] = data_list
                                    st.session_state['excel_df'] = df
                                    
                                    st.success(f"✅ 解析成功！共 {len(data_list)} 条数据")
                                    st.rerun()
                            
                            except Exception as e:
                                st.error(f"❌ 解析失败：{str(e)}")
        
        # 数据预览和导入区域
        if 'excel_data' in st.session_state:
            st.markdown("---")
            st.markdown("#### 📋 数据预览")
            
            df = st.session_state['excel_df']
            data_list = st.session_state['excel_data']
            
            # 显示数据表格
            st.dataframe(df, use_container_width=True, height=300)
            
            st.markdown(f"**共 {len(data_list)} 条记录**")
            
            # 导入按钮
            st.markdown("#### 💾 第三步：导入数据库")
            col_import1, col_import2, col_import3 = st.columns([1, 1, 1])
            
            with col_import1:
                if st.button("✅ 确认导入", type="primary", use_container_width=True):
                    with st.spinner("正在导入数据..."):
                        success_count, fail_count, errors = batch_save_to_database(data_list)
                        
                        # 显示结果
                        st.markdown("---")
                        st.markdown("#### 📈 导入结果")
                        
                        col_result1, col_result2, col_result3 = st.columns(3)
                        with col_result1:
                            st.metric("总数", len(data_list))
                        with col_result2:
                            st.metric("成功", success_count, delta=None, delta_color="normal")
                        with col_result3:
                            st.metric("失败", fail_count, delta=None, delta_color="inverse")
                        
                        if success_count > 0:
                            st.success(f"✅ 成功导入 {success_count} 条数据")
                        
                        if fail_count > 0:
                            st.error(f"❌ {fail_count} 条数据导入失败")
                            with st.expander("查看失败详情"):
                                for error in errors:
                                    st.warning(error)
                        
                        # 清除session state
                        if fail_count == 0:
                            del st.session_state['excel_data']
                            del st.session_state['excel_df']
            
            with col_import2:
                if st.button("❌ 取消导入", use_container_width=True):
                    del st.session_state['excel_data']
                    del st.session_state['excel_df']
                    st.info("已取消导入")
                    st.rerun()
            
            with col_import3:
                # 下载示例按钮
                st.markdown("")  # 占位

if __name__ == '__main__':
    main()

