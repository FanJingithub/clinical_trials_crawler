import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re

headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Encoding':'gzip, deflate, br, zstd',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Cookie': 'acw_tc=0a472f5217456508681597486e0061b197c34a9dc86e1e31f820cfe54570b4; acw_sc__v2=680c84b43d3c7b245009dff0c34e7b1fdb24175c; tfstk=ghk-aDtzAnIJa8yMELOctD_93dKDIvnyM4o1Ky4lOq3xfc7uOUkHpynZxWautYcYJqUVEy2oxygKvDZ3rXmCvkgml2Fe4y4QJ2mIZnvMI0ozLJipSdvMDfURGYUC-JwzhPO2QHpMI0o7LJTMSdDH4kWURywQNWibGrr_ATgQOrtYAkb5OTgIcnU4AJaIRJtxcrrI1X648BaGpfrAgCxSxrBCdxEW8Pi8korqHuF85dzAd0DY27UsVABTZDrK1AFr5EfuPfhZWl0khT3tV4h_1Y_XkJom62EtFh1TJ4ojESMWx1r4LbG_FvLOPmu-zYlsVEfYDjioHSD6W9FrG4la9vYDQ8cijvPsFLQao5rKW8GvlT3148kiB7wlSPEhNnKAT6P70_sXHzRpo-V0DPxmP65UM1rYSndPT6P70oUMmMCFTSCN.; ssxmod_itna=QqfxBiGQeCqq0mDzxAxewnRAeG=m5qw5LvUQwQD/jYmDnqD=GFDK40oEOfrEmYiK7A4nGQejmiPGCQAjabaQbnrcDqfzBT4GIDeKG2DmeDyDi5GRD0FK6D4SKGwD0eG+DD4DWCqDt/frqDFUqtS0wdnQudcUqDEiwQDYq=DmLbDnhiVDltUbBtDG+bDzkiDf+QDIwNnDqGnD0QHrdRMD0f3TccroqGWWoUr5PGuBjQ0D0PZSMNnSa+xz036n3hWYGpxj0GpABhxSG4si3hUMikHURqLcAwT0idBxc+yuiD==; ssxmod_itna2=QqfxBiGQeCqq0mDzxAxewnRAeG=m5qw5LvUQqG9bH7DBqYvh5GajDEk16AL5GMB+iN8X3rnGdqWjpMav8oRO2Ppx=sro3=7MSnQgjCnbzmHHdKDdegU8cbtjFHAnU00FvtQbx7jbhB+7Fm0zg2qGKD08DY9q4D=='
}

def scrape_chictr_info(url):
    """
    从中国临床试验注册中心网站抓取项目信息
    """
    
    try:
        # 发送HTTP请求
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # 如果请求失败则抛出异常
        
        # 使用BeautifulSoup解析HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 查找研究疾病
        disease = None
        disease_section = soup.find(text=re.compile('研究疾病'))
        if disease_section:
            # 尝试找到研究疾病的具体内容
            disease_element = disease_section.find_next('td')
            if disease_element:
                disease = disease_element.get_text(strip=True)
        
        # 查找申请人所在单位
        institution = None
        institution_section = soup.find(text=re.compile('申请人所在单位'))
        if institution_section:
            # 尝试找到申请人所在单位的具体内容
            institution_element = institution_section.find_next('td')
            if institution_element:
                institution = institution_element.get_text(strip=True)
        
        return {
            '研究疾病': disease,
            '申请人所在单位': institution
        }
    
    except Exception as e:
        print(f"抓取过程中出现错误: {e}")
        return {
            '研究疾病': None,
            '申请人所在单位': None
        }

def fetch_page_data(page_num):
    """获取指定页码的数据"""
    
    url = "https://www.chictr.org.cn/searchproj.html"
    params = {
        'institution': '复旦大学附属中山医院',
        'country': '中国',
        'createyear': '2024',
        'page': page_num
    }
    
    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table', class_='table1')
        
        if not table:
            print(f"第{page_num}页未找到数据表格")
            return []
        
        trials_data = []
        rows = table.find_all('tr')[1:]  # 跳过表头行
        
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 5:
                link_element = cols[2].find('a')
                link = ''
                if link_element and 'href' in link_element.attrs:
                    link = 'https://www.chictr.org.cn/' + link_element['href']
                
                trial_data = {
                    '注册号': cols[1].text.strip(),
                    '注册题目': cols[2].text.strip(),
                    '研究类型': cols[3].text.strip(),
                    '注册时间': cols[4].text.strip(),
                    '详情链接': link
                }
                detail = scrape_chictr_info(link)
                trial_data = trial_data | detail
                trials_data.append(trial_data)
        
        print(f"成功获取第{page_num}页数据，共{len(trials_data)}条记录")
        return trials_data
        
    except requests.exceptions.RequestException as e:
        print(f"请求第{page_num}页时发生错误: {e}")
        return []
    except Exception as e:
        print(f"处理第{page_num}页时发生错误: {e}")
        return []

def fetch_all_clinical_trials():
    """获取所有页面的数据并保存到Excel"""
    all_trials_data = []
    
    # 遍历10页数据
    for page in range(1, 10):
        print(f"正在获取第{page}页数据...")
        page_data = fetch_page_data(page)
        all_trials_data.extend(page_data)
        
        # 添加延时，避免请求过于频繁
        time.sleep(2)
    
    if all_trials_data:
        # 创建DataFrame并保存
        df = pd.DataFrame(all_trials_data)
        output_file = 'chictr_zhongshan_100.xlsx'
        df.to_excel(output_file, index=False, encoding='utf-8')
        print(f"所有数据已保存到 {output_file}，共{len(all_trials_data)}条记录")
    else:
        print("未获取到任何数据")

if __name__ == "__main__":
    fetch_all_clinical_trials()