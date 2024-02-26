import os
import re

# 正则表达式模式，用于匹配 PHP 包含语句
include_pattern = re.compile(r'include\(_once\)?|require\(_once\)?\s*\(?\s*[\'"]([^\'"]+)[\'"]')

# 函数：在目录下搜索包含了特定文件的 PHP 文件
def search_for_includes(directory, target_file, file_extension):
    files_including_target = set()
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(file_extension):
                full_path = os.path.join(root, file)
                with open(full_path, 'r', encoding='utf-8') as php_file:
                    try:
                        content = php_file.read()
                        # 搜索包含语句
                        matches = include_pattern.findall(content)
                        for match in matches:
                            included_file = match[1]
                            # 如果当前处理的包含语句包含目标文件
                            if included_file == target_file or included_file.endswith(target_file):
                                files_including_target.add(full_path)
                            
                    except UnicodeDecodeError:
                        # print(f"Could not read file: {full_path} due to an encoding error")
                        continue
                        
    return files_including_target


# 正则表达式模式，用于匹配以$开头的变量和跟随的$_REQUEST, $_POST, $_GET
user_input_pattern = re.compile(r'\$([a-zA-Z0-9_]*)\s*.*?(\$_REQUEST|\$_POST|\$_GET)', re.IGNORECASE)

# 正则表达式模式，用于匹配数据库查询语句
db_query_pattern = re.compile(r'(update|select|insert|delete).*?where.*?\$([a-zA-Z0-9_]*)', re.IGNORECASE)

# 函数：遍历检查目录下所有PHP文件
def search_php_files(directory, file_extension='.php'):
    user_input_variables = set()  # 存储用户可输入变量集合
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(file_extension):
                full_path = os.path.join(root, file)
                with open(full_path, 'r', encoding='utf-8') as php_file:
                    lines = php_file.readlines()
                    for line_number, line in enumerate(lines, start=1):
                        # 搜索用户输入变量
                        input_matches = user_input_pattern.findall(line)
                        for match in input_matches:
                            variable_name = match[0]
                            # 如果搜索到这样的变量，添加到集合中
                            if variable_name not in user_input_variables:
                                user_input_variables.add(variable_name)
                        
                    # 搜索所有包含这个文件的 PHP 文件中的用户输入变量被用于sql查询的位置
                    for variable in user_input_variables:
                        include_files = search_for_includes(directory, file, file_extension)
                        include_files.add(full_path)
                        for include_file in include_files:
                            with open(include_file, 'r',encoding='utf-8') as include_php_file:
                                include_lines = include_php_file.readlines()
                                for line_number, line in enumerate(include_lines, start=1):
                                    # 搜索数据库查询语句
                                    db_query_matches = db_query_pattern.findall(line)
                                    for match in db_query_matches:
                                        query_type = match[0]
                                        query_variable = match[1]
                                        # 如果查询语句中包含用户输入变量
                                        if query_variable == variable:
                                            # 检查line中所有的variable是否包含在intval中
                                            if line.replace(f"intval(${variable})", '').count(f"${variable}") == 0:
                                                continue
                                            print(f"SQL Position: {include_file}:{line_number}, User Input Var: {variable}")
                                            print(f"SQL Query: {line.strip()}")
                                            print("")

search_php_files('C:\\Pentest\\CodeReview\\EXAMPLES\\PHP\\bluecms')
