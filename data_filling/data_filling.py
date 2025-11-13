# -*-coding:utf-8-*-
import json
import random
import pymysql
from datetime import datetime, date, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from threading import Lock
import sys

# 数据库配置
MYSQL_CONFIG = {

}

# 人口缩放比例
SCALE_RATIO = 10000

# 线程锁，用于统计信息
stats_lock = Lock()
stats = {
    'success': 0,
    'failed': 0,
    'retry': 0
}

# 加载民族列表
def load_ethnicities():
    with open('ethnicity.md', 'r', encoding='utf-8') as f:
        content = f.read()
        ethnicities = eval(content)
    return ethnicities

# 加载省份数据
def load_province_data():
    with open('province_data.json', 'r', encoding='utf-8') as f:
        return json.load(f)

# 生成随机中文姓氏
def first_name():
    first_name_list = ['赵', '钱', '孙', '李', '周', '吴', '郑', '王', '冯', '陈', '褚', '卫', '蒋', '沈', '韩', '杨', '朱', '秦', '尤', '许',
                '何', '吕', '施', '张', '孔', '曹', '严', '华', '金', '魏', '陶', '姜', '戚', '谢', '邹', '喻', '柏', '水', '窦', '章',
                '云', '苏', '潘', '葛', '奚', '范', '彭', '郎', '鲁', '韦', '昌', '马', '苗', '凤', '花', '方', '俞', '任', '袁', '柳',
                '酆', '鲍', '史', '唐', '费', '廉', '岑', '薛', '雷', '贺', '倪', '汤', '滕', '殷', '罗', '毕', '郝', '邬', '安', '常',
                '乐', '于', '时', '傅', '皮', '卞', '齐', '康', '伍', '余', '元', '卜', '顾', '孟', '平', '黄', '和', '穆', '萧', '尹',
                '姚', '邵', '堪', '汪', '祁', '毛', '禹', '狄', '米', '贝', '明', '臧', '计', '伏', '成', '戴', '谈', '宋', '茅', '庞',
                '熊', '纪', '舒', '屈', '项', '祝', '董', '梁']
    return random.choice(first_name_list)

# 生成随机中文字符
def GBK2312():
    head = random.randint(0xb0, 0xba)
    body = random.randint(0xa1, 0xf9)
    val = '%s%s' % (hex(head).replace('0x',''), hex(body).replace('0x',''))
    st = bytes.fromhex(val).decode('gb2312')
    return st

# 生成随机名字中间字
def second_name():
    return GBK2312() if random.randint(0, 1) else ''

# 生成随机名字最后一个字
def last_name():
    return GBK2312()

# 生成姓名
def genName():
    return first_name() + second_name() + last_name()

# 生成身份证（指定前6位地址码）
def genIdCard(area_code, age, gender):
    """
    生成身份证号码
    :param area_code: 6位地址码
    :param age: 年龄
    :param gender: 性别 0=女 1=男
    :return: 18位身份证号
    """
    # 验证并清理地址码
    area_code_str = str(area_code).strip()
    # 只保留数字
    area_code_str = ''.join(filter(str.isdigit, area_code_str))
    
    # 如果地址码不是6位，填充或截取
    if len(area_code_str) < 6:
        area_code_str = area_code_str.ljust(6, '0')
    elif len(area_code_str) > 6:
        area_code_str = area_code_str[:6]
    
    id_code_list = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
    check_code_list = [1, 0, 'X', 9, 8, 7, 6, 5, 4, 3, 2]
    
    # 生成出生日期
    birth_year = date.today().year - age
    # 确保年份不会太早（避免负数）
    if birth_year < 1900:
        birth_year = 1900
    datestring = str(date(birth_year, 1, 1) + timedelta(days=random.randint(0, 364))).replace("-", "")
    
    # 生成顺序码（3位）
    rd = random.randint(1, 999)
    if gender == 0:  # 女性，偶数
        gender_num = rd if rd % 2 == 0 else (rd + 1 if rd < 999 else rd - 1)
    else:  # 男性，奇数
        gender_num = rd if rd % 2 == 1 else (rd - 1 if rd > 1 else rd + 1)
    
    # 组合前17位
    result = area_code_str + datestring + str(gender_num).zfill(3)
    
    # 确保是17位
    if len(result) != 17:
        raise ValueError(f"身份证前17位长度错误: {result}, 长度: {len(result)}")
    
    # 计算校验码
    check_sum = sum([a * b for a, b in zip(id_code_list, [int(a) for a in result])]) % 11
    check_code = check_code_list[check_sum]
    
    id_card = result + str(check_code)
    
    # 最终验证
    if len(id_card) != 18:
        raise ValueError(f"身份证号长度错误: {id_card}, 长度: {len(id_card)}")
    
    return id_card

# 从身份证号解析信息
def parse_id_card(id_no):
    """
    从身份证号中解析出生日期和性别
    :param id_no: 18位身份证号
    :return: (birth_date, gender)
    """
    # 提取出生日期（7-14位）
    birth_str = id_no[6:14]  # YYYYMMDD
    birth_year = int(birth_str[0:4])
    birth_month = int(birth_str[4:6])
    birth_day = int(birth_str[6:8])
    birth_date = date(birth_year, birth_month, birth_day)
    
    # 提取性别（第17位，奇数=男，偶数=女）
    gender_code = int(id_no[16])
    gender = "男" if gender_code % 2 == 1 else "女"
    
    return birth_date, gender

# 解析地址
def parse_address(address_str):
    """
    解析地址字符串，返回省、市、区
    例如："河北省-石家庄市-长安区" -> ("河北省", "石家庄市", "长安区")
    """
    parts = address_str.split('-')
    if len(parts) >= 3:
        return parts[0], parts[1], parts[2]
    elif len(parts) == 2:
        return parts[0], parts[1], ''
    else:
        return parts[0], '', ''

# 生成单个人口记录
def generate_person_data(area_code, address_str, ethnicities):
    """
    生成单个人口记录
    注意：先生成身份证号，然后从身份证号中解析出生日期和性别，确保数据一致性
    """
    # 随机年龄和性别用于生成身份证
    age = random.randint(0, 100)
    gender_code = random.randint(0, 1)  # 0=女，1=男
    
    # 生成身份证号（包含地址码、出生日期、性别信息）
    id_no = genIdCard(area_code, age, gender_code)
    
    # 从身份证号中解析真实的出生日期和性别（确保一致性）
    birth_date, gender = parse_id_card(id_no)
    
    # 生成姓名
    name = genName()
    
    # 随机民族 - 91%汉族，9%其他民族
    rand = random.random()
    if rand < 0.91:
        ethnicity = '汉族'
    else:
        # 从其他民族中随机选择（排除汉族）
        other_ethnicities = [e for e in ethnicities if e != '汉族']
        ethnicity = random.choice(other_ethnicities) if other_ethnicities else '汉族'
    
    # 随机教育程度
    education_levels = ['未上过学', '小学', '初中', '高中', '大专', '本科', '硕士及以上']
    education_level = random.choice(education_levels)
    
    # 解析户籍地址（从地址字符串中解析，地址码已经包含在身份证号中）
    province, city, district = parse_address(address_str)
    
    # 随机户籍登记类型
    hukou_type = random.choice(['家庭户', '集体户'])
    
    # 处理时间
    processed_at = datetime.now()
    
    # 数据来源
    source = 'YY'
    
    return {
        'id_no': id_no,           # 身份证号（包含地址码、出生日期、性别）
        'name': name,
        'former_name': None,
        'gender': gender,          # 从身份证号解析（与身份证一致）
        'birth_date': birth_date,  # 从身份证号解析（与身份证一致）
        'ethnicity': ethnicity,
        'marital_status': None,
        'education_level': education_level,
        'hukou_province': province,    # 解析自地址字符串（对应身份证前6位地址码）
        'hukou_city': city,
        'hukou_district': district,
        'housing': None,
        'cur_province': None,
        'cur_city': None,
        'cur_district': None,
        'hukou_type': hukou_type,
        'income': None,
        'processed_at': processed_at,
        'source': source
    }

# 批量插入数据到数据库
def batch_insert_to_db(records, max_retries=3):
    """
    批量插入记录到数据库，带重试机制和去重功能
    """
    if not records:
        return True, 0
    
    # 批次内去重：保留第一次出现的身份证号
    seen_ids = set()
    unique_records = []
    duplicate_count = 0
    
    for record in records:
        id_no = record['id_no']
        if id_no not in seen_ids:
            seen_ids.add(id_no)
            unique_records.append(record)
        else:
            duplicate_count += 1
    
    if duplicate_count > 0:
        print(f"  ⚠️ 批次内发现 {duplicate_count} 条重复记录已过滤")
    
    if not unique_records:
        return True, 0
    
    retry_count = 0
    
    while retry_count < max_retries:
        connection = None
        try:
            connection = pymysql.connect(**MYSQL_CONFIG)
            cursor = connection.cursor()
            
            # 使用 INSERT IGNORE 自动跳过数据库中已存在的记录
            sql = """
            INSERT IGNORE INTO population 
            (id_no, name, former_name, gender, birth_date, ethnicity, marital_status, 
             education_level, hukou_province, hukou_city, hukou_district, housing, 
             cur_province, cur_city, cur_district, hukou_type, income, processed_at, source)
            VALUES 
            (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            data = [
                (r['id_no'], r['name'], r['former_name'], r['gender'], r['birth_date'],
                 r['ethnicity'], r['marital_status'], r['education_level'],
                 r['hukou_province'], r['hukou_city'], r['hukou_district'], r['housing'],
                 r['cur_province'], r['cur_city'], r['cur_district'], r['hukou_type'],
                 r['income'], r['processed_at'], r['source'])
                for r in unique_records
            ]
            
            cursor.executemany(sql, data)
            affected_rows = cursor.rowcount  # 实际插入的行数
            connection.commit()
            
            # 计算跳过的记录数（数据库中已存在）
            skipped_in_db = len(unique_records) - affected_rows
            if skipped_in_db > 0:
                print(f"  ℹ️ 跳过数据库中已存在的 {skipped_in_db} 条记录")
            
            with stats_lock:
                stats['success'] += affected_rows
                stats['skipped'] = stats.get('skipped', 0) + skipped_in_db
            
            return True, affected_rows
            
        except pymysql.err.IntegrityError as e:
            # 主键冲突错误 - 使用 INSERT IGNORE 后这种情况应该很少见
            error_code = e.args[0]
            if error_code == 1062:  # Duplicate entry
                print(f"  ⚠️ 批次仍有主键冲突（这不应该发生），跳过此批次")
                with stats_lock:
                    stats['failed'] += len(unique_records)
                return False, 0
            else:
                raise  # 其他完整性错误，继续重试
                
        except Exception as e:
            retry_count += 1
            with stats_lock:
                stats['retry'] += 1
            
            if retry_count < max_retries:
                time.sleep(1 * retry_count)  # 指数退避
                print(f"  🔄 批次插入失败，正在重试 {retry_count}/{max_retries}... 错误: {str(e)}")
            else:
                with stats_lock:
                    stats['failed'] += len(unique_records)
                print(f"  ❌ 批次插入失败，已达最大重试次数。错误: {str(e)}")
                return False, 0
        
        finally:
            if connection:
                connection.close()
    
    return False, 0

# 处理单个省份的数据生成和插入
def process_province(province_name, province_info, ethnicities, batch_size=1000):
    """
    处理单个省份的数据生成和插入
    """
    population = province_info['人口数']
    area_codes = province_info['地址码']
    
    # 计算需要生成的人口数（缩放）
    scaled_population = int(population / SCALE_RATIO)
    
    if scaled_population == 0:
        print(f"省份 {province_name} 缩放后人口为0，跳过")
        return 0
    
    print(f"开始处理 {province_name}，原始人口: {population:,}，缩放后: {scaled_population:,}")
    
    # 准备地址码列表，过滤掉无效的地址码
    area_code_list = []
    for code, address in area_codes.items():
        # 只保留6位纯数字的地址码
        clean_code = ''.join(filter(str.isdigit, str(code)))
        if len(clean_code) == 6:
            area_code_list.append((clean_code, address))
    
    if not area_code_list:
        print(f"省份 {province_name} 没有有效的6位地址码，跳过")
        return 0
    
    total_inserted = 0
    batch = []
    
    for i in range(scaled_population):
        # 随机选择该省的一个地址码
        area_code, address_str = random.choice(area_code_list)
        
        try:
            # 生成人口数据
            person = generate_person_data(area_code, address_str, ethnicities)
            batch.append(person)
            
            # 当批次达到指定大小时，插入数据库
            if len(batch) >= batch_size:
                success, count = batch_insert_to_db(batch)
                if success:
                    total_inserted += count
                batch = []
                
        except Exception as e:
            print(f"生成数据时出错: {str(e)}")
            continue
    
    # 插入剩余的数据
    if batch:
        success, count = batch_insert_to_db(batch)
        if success:
            total_inserted += count
    
    print(f"{province_name} 完成，成功插入 {total_inserted:,} 条记录")
    return total_inserted

# 主函数
def main(parallel_workers=4, batch_size=1000):
    """
    主函数
    :param parallel_workers: 并行工作线程数
    :param batch_size: 每批次插入的记录数
    """
    print("=" * 60)
    print("人口数据填充脚本")
    print("=" * 60)
    print(f"缩放比例: {SCALE_RATIO}:1")
    print(f"并行线程数: {parallel_workers}")
    print(f"批次大小: {batch_size}")
    print("=" * 60)
    
    # 加载数据
    print("正在加载配置数据...")
    ethnicities = load_ethnicities()
    province_data = load_province_data()
    print(f"加载完成：{len(ethnicities)} 个民族，{len(province_data)} 个省份")
    
    # 测试数据库连接
    print("正在测试数据库连接...")
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        conn.close()
        print("数据库连接成功！")
    except Exception as e:
        print(f"数据库连接失败: {str(e)}")
        return
    
    # 开始计时
    start_time = time.time()
    
    # 使用线程池并行处理
    print(f"\n开始生成和插入数据...")
    print("-" * 60)
    
    with ThreadPoolExecutor(max_workers=parallel_workers) as executor:
        # 提交所有任务
        futures = {
            executor.submit(process_province, prov_name, prov_info, ethnicities, batch_size): prov_name
            for prov_name, prov_info in province_data.items()
        }
        
        # 等待所有任务完成
        for future in as_completed(futures):
            province_name = futures[future]
            try:
                result = future.result()
            except Exception as e:
                print(f"处理 {province_name} 时发生错误: {str(e)}")
    
    # 结束计时
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    # 打印统计信息
    print("-" * 60)
    print("数据填充完成！")
    print("=" * 60)
    print(f"总用时: {elapsed_time:.2f} 秒")
    print(f"✅ 成功插入: {stats['success']:,} 条")
    print(f"⏭️ 跳过重复: {stats.get('skipped', 0):,} 条")
    print(f"❌ 失败: {stats['failed']:,} 条")
    print(f"🔄 重试次数: {stats['retry']:,} 次")
    if elapsed_time > 0:
        print(f"⚡ 平均速度: {stats['success']/elapsed_time:.2f} 条/秒")
    print("=" * 60)

if __name__ == '__main__':
    # 可以通过命令行参数设置并行线程数和批次大小
    if len(sys.argv) > 1:
        workers = int(sys.argv[1])
    else:
        workers = 2  # 默认4个线程
    
    if len(sys.argv) > 2:
        batch = int(sys.argv[2])
    else:
        batch = 1000  # 默认每批1000条
    
    main(parallel_workers=workers, batch_size=batch)

