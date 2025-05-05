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

# def generate_math(problem):
#     problem_format=""
#     user_prompt = ""
#     user_prompt =read_file(args.default_prompt_position+"math_query.txt")
#     user_prompt = user_prompt.replace("$input$", problem)
#             # Call the model, clearly asking for optimization goal
#      # 调用GPT生成数学公式
#     math = call_gpt_from_sys("", user_prompt)
#     return problem_format

def generate_math(problem):
    math = ""
    user_prompt = "", ""
    while True:  # Add loop
        # Replace the input in the user prompt
        user_prompt =read_file(args.default_prompt_position+"math_query.txt")
        user_prompt = user_prompt.replace("$input$", problem)
        # Call GPT to generate the mathematical formula
        math = call_gpt_from_sys("", user_prompt)
        
        # Use GPT for validation
        validation_prompt = f"Please determine whether the following mathematical formula is consistent with the problem description.\n\nProblem description:\n{problem}\n\nGenerated mathematical formula:\n{math}\n\nPlease return 'Consistent' or 'Inconsistent':"
        
        validation_result = call_gpt_from_sys("", validation_prompt)
        
        if "Consistent" in validation_result:
            # print("Validation passed: The generated math is consistent with the problem description.")
            break  # Break out of the loop
         # Extract optimization flag
    optimization_flag = None
    if "[Optimization Flag: 1]" in math:
        optimization_flag = 1  # Maximize
    elif "[Optimization Flag: 0]" in math:
        optimization_flag = 0  # Minimize
    return math,optimization_flag 


def generate_code(math):
    code = ""
    user_prompt =read_file(args.default_prompt_position+"o_convex_code.txt")
    user_prompt = user_prompt.replace("$input$", math)
    code = call_gpt_from_sys("", user_prompt)
    code = code.replace("```python", "")
    code = code.replace("```", "")
    with open(args.default_project_directory + "opt.py", "w", encoding="UTF-8") as f:
        f.write(code)
    return code

def execute_code():
    result = ""   
    # Run the .py file and capture output
    result = subprocess.run(['python', 'opt.py'], capture_output=True, text=True)
    # Check if execution encountered an error
    if result.returncode != 0:
        return 0, result.stderr  # Program error, return 0 and error message
    # Retrieve the return value and process the output
    output = result.stdout.strip().split('\n')
    # Check if output is empty
    if not output:
        return 0, "Output is empty."  # Output is empty, return 0 and a prompt message
    # Construct the result dictionary
    values = {}
    # First line as the objective function value
    if len(output) > 0:
        try:
            values['objective'] = float(output[0].split(": ")[1])
        except (IndexError, ValueError):
            return 0, "Invalid format for minimum total power."  # Handle format issues
    # Process remaining lines as optimization variables
    for line in output[1:]:
        if ": " in line:  # Ensure the line contains a colon
            var_name = line.split(": ")[0].strip()
            value = line.split(": ")[1].strip()
            values[var_name] = value  # Store as string directly, without using eval
    # Check validity
    if 'objective' not in values or values['objective'] == float('inf'):
        return 0, "Invalid objective value."  # Return 0 and prompt message for invalid cases
    return values, None  # Return dictionary and no error message


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

def refine_code(math, code, attempt):
    new_code = ""
    user_prompt_file =read_file(args.default_prompt_position+"refine_query_o_convex.txt")
    user_prompt_file = user_prompt_file.replace("$math$", math).replace("$code$", code).replace("$attempt$", str(attempt))
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
    problem = args.problem
    math,optimization_flag=generate_math(problem)
    code=generate_code(math)


    objective, variable_values = process_execution(code)
    if objective == 0:
        print("Failed to find a valid solution, terminating the program.")
    else:
        execute_flag = 1
        feasibility_check_result = check_feasibility(math, variable_values)

        if feasibility_check_result == 1:
            print("The initial solution is within the feasible region.")
            success_flag = 1
            
    # Output formatted results
    print(f"{success_flag},{execute_flag}")
    result = result + "\n\math_formulation\n" + math + "\n"
    result = result + "\n\generate_code\n" + code + "\n"
    with open(args.default_prompt_position + "final_opitimus.txt", "w", encoding="UTF-8") as f:
        f.write(result + '\n')
