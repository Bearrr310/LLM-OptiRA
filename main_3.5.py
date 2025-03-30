import time
import json
import logging
import requests
import os
import random
import subprocess

# from gpt_predict import predict
from config import args
from GPTFactory.GPTFactory import GPTFactory



def call_gpt_from_sys(sys_prompt, user_prompt):
    gpt_interface = GPTFactory("gpt-3.5-turbo", args.api_key)
    gpt_interface.set_sys_conv(sys_prompt)
    gpt_interface.add_user_conv(user_prompt)
    result = gpt_interface.predict()
    return result


def pure_set_prompt(system_file, query_file):
    sys_prompt, user_prompt = "", ""
    
    sys_prompt_file, user_prompt_file = system_file, query_file

    if args.read_from_file:
        with open(args.default_prompt_position + sys_prompt_file, "r", encoding="UTF-8") as f:
            for idx, line in enumerate(f):
                sys_prompt = sys_prompt + line
        with open(args.default_prompt_position + user_prompt_file, "r", encoding="UTF-8") as f:
            for idx, line in enumerate(f):
                user_prompt = user_prompt + line       
    else:
        sys_prompt, user_prompt = args.default_prompt_position + sys_prompt_file, args.default_prompt_position + user_prompt_file
    return sys_prompt, user_prompt



def read_file(dist):
    text = ""
    with open(dist, "r", encoding="UTF-8") as f:
        for idx, line in enumerate(f):
            text = text + line
    return text



def generate_math(problem):
    math = ""
    user_prompt = "", ""
    while True:  # 添加循环
        # 替换用户提示中的输入
        user_prompt =read_file(args.default_prompt_position+"o_model_query.txt")
        user_prompt = user_prompt.replace("$input$", problem)
                # Call the model, clearly asking for optimization goal
        user_prompt += "\nPlease specify whether to maximize or minimize, using the format '[Optimization Flag: 1]' for maximize and '[Optimization Flag: 0]' for minimize."
        # 调用GPT生成数学公式
        math = call_gpt_from_sys("", user_prompt)
        
        # 使用GPT进行验证
        validation_prompt = f"请判断以下数学公式是否与问题描述一致。\n\n问题描述:\n{problem}\n\n生成的数学公式:\n{math}\n\n请返回'一致'或'不一致':"
        
        validation_result = call_gpt_from_sys("", validation_prompt)
        
        if "一致" in validation_result:
            #print("验证通过：生成的math与问题描述一致。")
            break  # 跳出循环
            # Extract optimization flag
    optimization_flag = None
    if "[Optimization Flag: 1]" in math:
        optimization_flag = 1  # Maximize
    elif "[Optimization Flag: 0]" in math:
        optimization_flag = 0  # Minimize
    return math,optimization_flag 

def transfer_convex(math):
    convex = ""
    sys_prompt, user_prompt = "", ""
    sys_prompt_file, user_prompt_file = "convex_example.txt", "convex_query.txt"
    sys_prompt, user_prompt = pure_set_prompt(sys_prompt_file, user_prompt_file)
    user_prompt = user_prompt.replace("$input$", math)
    convex = call_gpt_from_sys(sys_prompt, user_prompt)
    return convex

def generate_code(convex):
    code = ""
    sys_prompt, user_prompt = "", ""
    sys_prompt_file, user_prompt_file = "code_example.txt", "code_query.txt"
    sys_prompt, user_prompt = pure_set_prompt(sys_prompt_file, user_prompt_file)
    user_prompt = user_prompt.replace("$input$", convex)
    code = call_gpt_from_sys(sys_prompt, user_prompt)
    code = code.replace("```python", "")
    code = code.replace("```", "")
    with open(args.default_project_directory + "opt.py", "w", encoding="UTF-8") as f:
        f.write(code)
    return code

def execute_code():
    result = ""   
    # 运行.py文件并捕获输出
    result = subprocess.run(['python', 'opt.py'], capture_output=True, text=True)
    # 检查是否运行出错
    if result.returncode != 0:
        return 0, result.stderr  # 程序出错，返回0和错误信息
    # 获取返回值并处理输出
    output = result.stdout.strip().split('\n')
    # 检查输出是否为空
    if not output:
        return 0, "Output is empty."  # 输出为空，返回0和提示信息
    # 构建结果字典
    values = {}
    # 第一行作为目标函数值
    if len(output) > 0:
        try:
            values['objective'] = float(output[0].split(": ")[1])
        except (IndexError, ValueError):
            return 0, "Invalid format for minimum total power."  # 处理格式问题
    # 处理剩余行作为优化变量
    for line in output[1:]:
        if ": " in line:  # 确保这一行包含冒号
            var_name = line.split(": ")[0].strip()
            value = line.split(": ")[1].strip()
            values[var_name] = value  # 直接存储字符串，不使用 eval
    # 检查是否有效
    if 'objective' not in values or values['objective'] == float('inf'):
        return 0, "Invalid objective value."  # 无效情况返回0和提示信息
    return values, None  # 返回字典和无错误信息

def process_execution(code):
    max_attempts = 5  # 最大尝试次数
    attempts = 0  # 当前尝试次数
    objective = None  # 初始化目标函数
    variable_values = []  # 初始化优化变量值列表

    # with open("opt.py", "r", encoding="UTF-8") as f:
    #     code = f.read()

    while attempts < max_attempts:
        result, error_message = execute_code()

        if result == 0:
            print("程序出错或目标函数无效，结束程序。")
            print("错误信息:", error_message)  # 输出错误信息

            # 将错误信息追加到错误日志文件中
            with open("error_log.txt", "a", encoding="UTF-8") as f:
                f.write(f"错误信息: {error_message}\n")
                # 读取 error_example.txt 文件内容
            with open("error_example.txt", "r", encoding="UTF-8") as f:
                error_example_content = f.read()

            # 调用GPT处理错误信息和代码，只返回代码
            prompt = f"请根据以下错误信息和代码生成修复代码：\n错误信息: {error_message}\n，如果是目标函数invalid，你可以调整初值或者适当放宽一些约束；如果不符合DCP规则，请使用其他解法。代码:\n{code}\n\n只返回代码，不要其他文字。"
            gpt_response = call_gpt_from_sys(error_example_content, prompt)
            gpt_response = gpt_response.replace("```python", "")
            gpt_response = gpt_response.replace("```", "")
            
            # 生成新的代码（假设gpt_response是生成的代码）
            new_code = gpt_response  # 直接赋值为字符串
            if new_code:
                # 将新的代码写入opt.py，覆盖原有内容
                with open("opt.py", "w", encoding="UTF-8") as f:
                    f.write(new_code)

                # 直接执行新的代码
                code = new_code  # 更新代码为新的代码
                attempts += 1  # 增加尝试次数
                continue  # 继续执行新的代码
            else:
                print("未能生成新代码，结束程序。")
                break  # 退出循环，停止处理

        else:
            objective = result.get('objective', None)
            print("目标函数:", objective)   
            
            # 输出优化后的变量值
            variable_values = [value for var_name, value in result.items() if var_name != 'objective']
            for var_name, value in result.items():
                if var_name != 'objective':
                    print(f"{var_name}: {value}")        
        
            # 将优化变量的值追加到文件中
            with open("output.txt", "a", encoding="UTF-8") as f:
                f.write(f"目标函数: {objective}\n")
                for var_name, value in result.items():
                    if var_name != 'objective':
                        f.write(f"{var_name}: {value}\n")
                f.write("\n")  # 添加一个空行以分隔不同的运行结果

            break  # 成功执行后退出循环

    if attempts == max_attempts:
        print("达到最大尝试次数，程序结束。")
        return 0, []  # 返回0表示失败

    return objective, variable_values  # 返回目标函数和优化变量值

def check_feasibility(math,variable_values):
    # 准备输入给GPT
    variables_str = ', '.join([f"{value}" for value in variable_values])
    prompt = f"请根据以下优化问题和变量值判断解是否在可行域内：\n\n问题:\n{math}\n\n变量值:\n{variables_str}\n\n返回1如果在可行域内，返回0如果不在可行域内。只用返回数字即可"

    # 调用GPT
    gpt_response = call_gpt_from_sys("", prompt)

    # 假设gpt_response是返回的字符串
    return int(gpt_response.strip())

def refine_code(math, code, attempt, convex):
    new_code = ""
    user_prompt_file =read_file(args.default_prompt_position+"refine_query.txt")
    user_prompt_file = user_prompt_file.replace("$math$", math).replace("$code$", code).replace("$attempt$", str(attempt)).replace("$convex$",convex)
    # Call GPT to refine the code
    new_code = call_gpt_from_sys("", user_prompt_file)  # Using an empty string for sys_prompt
    new_code = new_code.replace("```python", "").replace("```", "")

    # Write the refined code to a file
    with open("opt.py", "w", encoding="UTF-8") as f:
        f.write(new_code)
    
    return new_code






if __name__ == '__main__':

    result = ""
    success_flag=0
    execute_flag=0
    problem = args.default_dataset_position
    #model,optimization_flag=generate_model(problem)
    math,optimization_flag=generate_math(problem)
    convex=transfer_convex(math)
    code=generate_code(convex)
    max_attempts = 4  # Maximum attempts to find a feasible solution
    attempt = 0
    current_objective = None
    current_values = None
    # current_objective = float('inf')  # 初始值设为无穷大
    # current_values = None  # 旧解初始值为 None

    objective, variable_values=process_execution(code)
    if objective == 0:
        print("未能找到有效解，程序结束。")
    else:
        execute_flag=1
        # Check feasibility of the initial solution
        feasibility_check_result = check_feasibility(math, variable_values)

        if feasibility_check_result == 1:
             print("初始解在可行域内。")
             success_flag = 1

        if feasibility_check_result == 0:
            print("初始解不在可行域内，调用 refine_code 函数生成新的代码。")
            for attempt in range(max_attempts):
                # On the first attempt, use the original code
                if attempt == 0:
                    new_code = refine_code(math, code, attempt, convex)  # Use the original generated `code`
                elif attempt>0 and attempt<max_attempts/2:
                    # On subsequent attempts, use the most recent `new_code`
                    new_code = refine_code(math, new_code, attempt, convex)  # Use the last generated `new_code`
                else:
                    convex = transfer_convex(math)
                    # Generate new code
                    new_code = generate_code(convex)

                new_objective, new_values = process_execution(new_code)
                feasibility_check_result = check_feasibility(math, new_values)

                if feasibility_check_result == 1:
                    current_objective = new_objective
                    current_values = new_values
                    print(f"真正的有效解，目标函数: {current_objective}, 变量值: {current_values}")
                    success_flag = 1
                    break
                else:
                    print(f"尝试 {attempt + 1} 失败，这一次的解仍不在可行域内。")
            else:
                print("达到最大尝试次数，仍未找到有效解，程序结束。")


    # 输出格式化结果
    print(f"{success_flag},{execute_flag}")
    #result = "\\"  + model +  "\n" 
    result = result + "\n\math_formulation\n" + math+  "\n" 
    result = result + "\n\transfer_convex\n" + convex+  "\n" 
    result = result + "\n\generate_code\n" + code+  "\n" 
    with open(args.default_prompt_position + "final_output.txt", "w", encoding="UTF-8") as f:
        f.write(result + '\n')

