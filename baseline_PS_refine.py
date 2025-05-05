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
def plan_and_solve(problem):
    answer=""
    sys_prompt_file, user_prompt_file = "ps_example.txt", "ps_query.txt"
    sys_prompt, user_prompt = pure_set_prompt(sys_prompt_file, user_prompt_file)
    #setup=read_file(args.default_dataset_position+"problem.txt")
    user_prompt = user_prompt.replace("$input$", problem)
    # user_prompt += "\nPlease specify whether to maximize or minimize, using the format '[Optimization Flag: 1]' for maximize and '[Optimization Flag: 0]' for minimize."
    answer = call_gpt_from_sys(sys_prompt, user_prompt)
    with open(args.default_prompt_position + "ps_answer.txt", "w", encoding="UTF-8") as f:
        f.write(answer + '\n')
    optimization_flag = None
    if "[Optimization Flag: 1]" in answer:
        optimization_flag = 1  # Maximize
    elif "[Optimization Flag: 0]" in answer:
        optimization_flag = 0  # Minimize
    # 提取代码部分
    code = extract_code(answer)
    with open(args.default_project_directory + "opt.py", "w", encoding="UTF-8") as f:
        f.write(code)
    return answer, code, optimization_flag


def execute_code():
    result = ""
    # Run the .py file and capture the output
    result = subprocess.run(['python', 'opt.py'], capture_output=True, text=True)
    # Check if an error occurred during execution
    if result.returncode != 0:
        return 0, result.stderr  # The program encountered an error, return 0 and the error message
    # Get the return value and process the output
    output = result.stdout.strip().split('\n')
    # Check if the output is empty
    if not output:
        return 0, "Output is empty."  # The output is empty, return 0 and a prompt message
    # Build the result dictionary
    values = {}
    # Use the first line as the objective function value
    if len(output) > 0:
        try:
            values['objective'] = float(output[0].split(": ")[1])
        except (IndexError, ValueError):
            return 0, "Invalid format for minimum total power."  # Handle format issues
    # Process the remaining lines as optimization variables
    for line in output[1:]:
        if ": " in line:  # Ensure the line contains a colon
            var_name = line.split(": ")[0].strip()
            value = line.split(": ")[1].strip()
            values[var_name] = value  # Store the string directly without using eval
    # Check if it is valid
    if 'objective' not in values or values['objective'] == float('inf'):
        return 0, "Invalid objective value."  # Return 0 and a prompt message for invalid cases
    return values, None  # Return the dictionary and no error message


def extract_math(answer):
    #prompt = f"请根据以下优化问题和变量值判断解是否在可行域内：\n\n问题:\n{math}\n\n变量值:\n{variables_str}\n\n返回1如果在可行域内，返回0如果不在可行域内。只用返回数字即可"
    # 调用GPT
    with open(args.default_prompt_position+"math_query_ps.txt", "r", encoding="UTF-8") as f:
        user_prompt = f.read()
    user_prompt = user_prompt.replace("$input$", answer)
    math = call_gpt_from_sys("", user_prompt)
    # 假设gpt_response是返回的字符串
    return math
def process_execution(code):
    max_attempts = 5  # Maximum number of attempts
    attempts = 0  # Current number of attempts
    objective = None  # Initialize the objective function
    variable_values = []  # Initialize the list of optimized variable values

    while attempts < max_attempts:
        result, error_message = execute_code()

        if result == 0:
            print("The program encountered an error or the objective function is invalid, ending the program.")
            # print("Error message:", error_message)  # Output the error message

            # Append the error message to the error log file
            with open(args.default_prompt_position +"error_log.txt", "a", encoding="UTF-8") as f:
                f.write(f"Error message: {error_message}\n")
            # Read the content of the error_example.txt file
            with open(args.default_prompt_position +"error_example.txt", "r", encoding="UTF-8") as f:
                error_example_content = f.read()

            # Call GPT to process the error message and code, and only return the code
            prompt = f"Please generate fixed code based on the following error message and code:\nError message: {error_message}\n. If the objective function is invalid, you can adjust the initial values or relax some constraints appropriately; if it does not conform to the DCP rules, please use other solutions. Code:\n{code}\n\nOnly return the code, no other text."
            gpt_response = call_gpt_from_sys(error_example_content, prompt)
            gpt_response = gpt_response.replace("```python", "")
            gpt_response = gpt_response.replace("```", "")

            # Generate new code (assuming gpt_response is the generated code)
            new_code = gpt_response  # Assign directly as a string
            if new_code:
                # Write the new code to opt.py, overwriting the original content
                with open("opt.py", "w", encoding="UTF-8") as f:
                    f.write(new_code)

                # Execute the new code directly
                code = new_code  # Update the code to the new code
                attempts += 1  # Increase the number of attempts
                continue  # Continue executing the new code
            else:
                print("Failed to generate new code, ending the program.")
                break  # Exit the loop and stop processing

        else:
            objective = result.get('objective', None)
            print("Objective function:", objective)

            # Output the optimized variable values
            variable_values = [value for var_name, value in result.items() if var_name != 'objective']
            for var_name, value in result.items():
                if var_name != 'objective':
                    print(f"{var_name}: {value}")

            # Append the values of the optimized variables to the file
            with open("output.txt", "a", encoding="UTF-8") as f:
                f.write(f"Objective function: {objective}\n")
                for var_name, value in result.items():
                    if var_name != 'objective':
                        f.write(f"{var_name}: {value}\n")
                f.write("\n")  # Add a blank line to separate different running results

            break  # Exit the loop after successful execution

    if attempts == max_attempts:
        print("Reached the maximum number of attempts, the program ends.")
        return 0, []  # Return 0 to indicate failure

    return objective, variable_values  # Return the objective function and optimized variable values

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
    answer,code, optimization_flag=plan_and_solve(problem) 
    math=extract_math(answer)
    #extract_code(answer)
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
        else:
            print("初始解不在可行域内，调用 refine_code 函数生成新的代码。")
            for attempt in range(max_attempts):
                # On the first attempt, use the original code
                new_answer,new_code, optimization_flag=plan_and_solve(problem)
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

    print(f"{success_flag},{execute_flag}")
    result = result + "\n\ answer\n" + answer+  "\n" 
    result = result + "\n\math_formulation\n" + math+  "\n" 
    result = result + "\n\generate_code\n" + code+  "\n" 
    with open(args.default_prompt_position + "psfinal_output.txt", "w", encoding="UTF-8") as f:
        f.write(result + '\n')

