import argparse
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

parser = argparse.ArgumentParser(description="Process some parameters.")

# 接收传递的参数
parser.add_argument("--problem", type=str, help="Problem description.")
parser.add_argument("--api_key", type=str, help="API key for GPT.")
parser.add_argument("--default_prompt_position", type=str, help="Directory of prompts.")
parser.add_argument("--default_dataset_position", type=str, help="Directory of dataset.")
parser.add_argument("--default_project_directory", type=str, help="Directory of project.")

args = parser.parse_args()


def call_gpt_from_sys(sys_prompt, user_prompt):
    gpt_interface = GPTFactory("gpt-4o-mini", args.api_key)
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
def extract_code(answer):
    # 假设代码部分以 ``` 开头和结尾
    code_parts = []
    in_code_block = False
    for line in answer.splitlines():
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            code_parts.append(line)
    return "\n".join(code_parts)
def plan_and_solve(problem_content):
    answer=""
    sys_prompt, user_prompt = "", ""
    sys_prompt_file, user_prompt_file = "ps_example.txt", "ps_query.txt"
    sys_prompt, user_prompt = pure_set_prompt(sys_prompt_file, user_prompt_file)
    user_prompt = user_prompt.replace("$input$", problem_content)
    answer = call_gpt_from_sys(sys_prompt, user_prompt)
    with open(args.default_prompt_position + "ps_answer.txt", "w", encoding="UTF-8") as f:
        f.write(answer + '\n')
    # 提取代码部分
    code = extract_code(answer)
    with open(args.default_project_directory + "opt.py", "w", encoding="UTF-8") as f:
        f.write(code)
    # with open(args.default_prompt_position + "model_output.txt", "w", encoding="UTF-8") as f:
    #     f.write(model + '\n')
    return answer


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
        # 打印执行成功信息
    #print("Execution successful.")
    return values, None  # 返回字典和无错误信息

def extract_math(answer):
    #prompt = f"请根据以下优化问题和变量值判断解是否在可行域内：\n\n问题:\n{math}\n\n变量值:\n{variables_str}\n\n返回1如果在可行域内，返回0如果不在可行域内。只用返回数字即可"
    # 调用GPT
    with open(args.default_prompt_position+"math_query_ps.txt", "r", encoding="UTF-8") as f:
        user_prompt = f.read()
    user_prompt = user_prompt.replace("$input$", answer)
    math = call_gpt_from_sys("", user_prompt)
    # 假设gpt_response是返回的字符串
    return math

def check_feasibility(math, variable_values):
    # Prepare the input for GPT
    variables_str = ', '.join([f"{value}" for value in variable_values])
    # print(variables_str)
    user_prompt_file =read_file(args.default_prompt_position+"feasibility_query.txt")
    user_prompt_file = user_prompt_file.replace("$math$", math).replace("$variables_str$", variables_str)
    # prompt = f"Based on the following optimization problem and variable values, please determine whether the solution lies within the feasible region.\n\nOptimization Problem:\n{math}\n\nVariable Values:\n{variables_str}\n\nIf the solution is within the feasible region, return 1. If not, return 0. Please only return the number without any additional text."

    # Call GPT
    gpt_response = call_gpt_from_sys("", user_prompt_file)
    # print(f"GPT response: {gpt_response}")  # 打印 GPT 返回的内容

    try:
        result = int(gpt_response.strip())
        if result in [0, 1]:
            return result
        else:
            print(f"Invalid response from GPT: {gpt_response}. Expected 0 or 1.")
            return None
    except ValueError:
        print(f"Invalid response from GPT: {gpt_response}. It cannot be converted to an integer.")
        return None





if __name__ == '__main__':

    result = ""
    success_flag=0
    execute_flag=0
    problem = args.problem
    answer=plan_and_solve(problem)   
    math=extract_math(answer)
    extract_code(answer)
    result, error_message = execute_code()
    if result == 0:
            print("程序出错或目标函数无效，结束程序。")
            print("错误信息:", error_message)  # 输出错误信息
    else:
        print("PLAN AND SOLVE 执行成功！")
        execute_flag=1
        objective = result.get('objective', None)
        variable_values = [value for var_name, value in result.items() if var_name != 'objective']      
    feasibility_check_result = check_feasibility(math, variable_values)
    # 检查新的解是否在可行域内
    if feasibility_check_result == 1:
        print(f"有效解，目标函数: {objective}, 变量值: {variable_values}")
        success_flag=1
    else:
        print("新的解仍不在可行域内，程序结束。")
    print(f"{success_flag},{execute_flag}")

