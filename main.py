import time
import json
import logging
import requests
import os
import random
import subprocess

from config import args
from GPTFactory.GPTFactory import GPTFactory



def call_gpt_from_sys(sys_prompt, user_prompt):
    gpt_interface = GPTFactory("gpt-4o-mini", args.api_key)
    gpt_interface.set_sys_conv(sys_prompt)
    gpt_interface.add_user_conv(user_prompt)
    result = gpt_interface.predict()
    return result


def pure_set_prompt(system_file, query_file):
    sys_prompt, user_prompt = "", ""
    
    sys_prompt_file, user_prompt_file = system_file, query_file

    if True:
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

# def generate_math(problem):
#     math = ""
#     while True:  # Add loop
#         # Replace the input in the user prompt
#         sys_prompt, user_prompt = "", ""
#         sys_prompt_file, user_prompt_file = "math_example.txt", "math_query.txt"
#         sys_prompt, user_prompt = pure_set_prompt(sys_prompt_file, user_prompt_file)
#         # user_prompt = read_file(args.default_prompt_position + "math_query.txt")
#         # Read the problem from the folder
#         # problem = read_file(args.default_dataset_position + "problem16.txt")
#         # user_prompt = user_prompt.replace("$input$", problem)
#         # Read the problem uniformly
#         user_prompt = user_prompt.replace("$input$", problem)
#         # Call the model, clearly asking for optimization goal
#         # user_prompt += "\nPlease specify whether to maximize or minimize, using the format '[Optimization Flag: 1]' for maximize and '[Optimization Flag: 0]' for minimize."
#         # Call GPT to generate the mathematical formula
#         math = call_gpt_from_sys(sys_prompt, user_prompt)

#         # Use GPT for validation
#         validation_prompt = f"Please determine whether the following mathematical formula is consistent with the problem description.\n\nProblem description:\n{problem}\n\nGenerated mathematical formula:\n{math}\n\nPlease return 'Consistent' or 'Inconsistent':"

#         validation_result = call_gpt_from_sys("", validation_prompt)

#         if "Consistent" in validation_result:
#             # print("Validation passed: The generated math is consistent with the problem description.")
#             break  # Break out of the loop
#     math = math.replace("```json", "")
#     math = math.replace("```", "")
#     math_dict = json.loads(math)  # 解析 JSON 字符串
#     optimization_flag = math_dict.get("optimization_flag", None)  # 直接获取 flag
#     # print("optiflag is {}".format(optimization_flag))
#     return math, optimization_flag

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
    #setup=read_file(args.default_prompt_position+"problem_input.txt")
    user_prompt = user_prompt.replace("$input$", convex)
    code = call_gpt_from_sys(sys_prompt, user_prompt)
    code = code.replace("```python", "")
    code = code.replace("```", "")
    with open(args.default_project_directory + "opt.py", "w", encoding="UTF-8") as f:
        f.write(code)
    return code

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
            with open("error_log.txt", "a", encoding="UTF-8") as f:
                f.write(f"Error message: {error_message}\n")
            # Read the content of the error_example.txt file
            with open("error_example.txt", "r", encoding="UTF-8") as f:
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

# def check_feasibility(math, variable_values):
#     # Prepare the input for GPT
#     variables_str = ', '.join([f"{value}" for value in variable_values])
#     prompt = f"Please determine whether the solution is within the feasible region based on the following optimization problem and variable values:\n\nProblem:\n{math}\n\nVariable values:\n{variables_str}\n\nReturn 1 if it is within the feasible region, and return 0 if it is not. Just return the number."

#     # Call GPT
#     gpt_response = call_gpt_from_sys("", prompt)

#     # Assume gpt_response is the returned string
#     return int(gpt_response.strip())
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
    #problem=read_file(args.default_dataset_position+"problem16.txt")
    #model,optimization_flag=generate_model()
    math,optimization_flag=generate_math(problem)
    convex=transfer_convex(math)
    code=generate_code(convex)
    max_attempts = 0  # Maximum attempts to find a feasible solution
    attempt = 0
    current_objective = None
    current_values = None


    objective, variable_values = process_execution(code)
    if objective == 0:
        print("Failed to find a valid solution. The program ends.")
    else:
        execute_flag = 1
        # Check feasibility of the initial solution
        feasibility_check_result = check_feasibility(math, variable_values)

        if feasibility_check_result == 1:
            print("The initial solution is within the feasible region.")
            success_flag = 1

        if feasibility_check_result == 0:
            print("The initial solution is not within the feasible region. Call the refine_code function to generate new code.")
            for attempt in range(max_attempts):
                # On the first attempt, use the original code
                if attempt == 0:
                    new_code = refine_code(math, code, attempt, convex)  # Use the original generated `code`
                elif attempt > 0 and attempt < max_attempts / 2:
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
                    print(f"Found a valid solution.")
                    success_flag = 1
                    break
                else:
                    print(f"Attempt {attempt + 1} failed. The solution is still not within the feasible region.")
            else:
                print("Reached the maximum number of attempts. Still failed to find a valid solution. The program ends.")



    print(f"{success_flag},{execute_flag}")
    result = result + "\n\math_formulation\n" + math+  "\n" 
    result = result + "\n\ transfer_convex\n" + convex+  "\n" 
    result = result + "\n\generate_code\n" + code+  "\n" 
    with open(args.default_prompt_position + "final_output.txt", "w", encoding="UTF-8") as f:
        f.write(result + '\n')


