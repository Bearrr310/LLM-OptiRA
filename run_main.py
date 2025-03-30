import os
import re
import argparse
import time

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--api_key", default="", help="api key for gpt3.5"
    )
    parser.add_argument(
        "--utilized_model", default="gpt-3.5-turbo", help="the model you use"
    )
    parser.add_argument(
        "--max_length", default=16000, help="max input+output tokens"
    )
    parser.add_argument(
        "--default_prompt_position", default="D:\\SEU\\LLM\\OptiRA\\Prompt\\", help="use to redirect to default prompt"
    )
    parser.add_argument(
        "--default_dataset_position", default="D:\\SEU\\LLM\\OptiRA\\Dataset\\", help="use to redirect to default prompt"
    )
    parser.add_argument(
        "--default_project_directory", default="D:\\SEU\\LLM\\OptiRA\\", help="use to redirect to default prompt"
    )
    parser.add_argument(
        "--read_from_file", default=True, action=argparse.BooleanOptionalAction, help="use file to read"
    )
    parsed_args = parser.parse_args()
    return parsed_args

args = parse_arguments()

dataset_position = args.default_dataset_position  # 问题文件的目录
program_directory = args.default_project_directory  # 程序文件的目录

# 定义问题范围，集中管理
problem_range = range(51, 55)

# 动态生成问题文件列表，使用问题范围
problem_files = [os.path.join(dataset_position, f"problem{i}.txt") for i in problem_range]

# 定义要执行的程序
programs = [
    os.path.join(program_directory,'main.py'), 
    # os.path.join(program_directory,'Optimus.py'),
    os.path.join(program_directory,'main_COT_refine.py'),
    os.path.join(program_directory,'main_PS_refine.py'),
    #os.path.join(program_directory,'main_COT.py'), 
    #os.path.join(program_directory,'main_PS.py')
]

# 存储结果
results = {program: [] for program in programs}
# 用于存储每个问题的成功和执行标志总和
flags_summary = {program: {problem: [0, 0] for problem in problem_range} for program in programs}  
# 用于存储每个程序每次运行的时间
run_times = {program: [] for program in programs}  

# 循环执行 5 次
runs_per_problem=5
for i in range(runs_per_problem):
    print(f"运行第 {i + 1} 次")
    for problem_file in problem_files:
        with open(problem_file, 'r', encoding="utf-8") as f:
            problem_content = f.read().strip()
        
        for program in programs:
            start_time = time.time()  # 记录开始时间
            output = os.popen(f'python "{program}" --problem "{problem_content}"').read().strip()
            end_time = time.time()  # 记录结束时间
            run_time = end_time - start_time  # 计算运行时间
            run_times[program].append(run_time)

            print(f"{program} 输出: {output}")
            print(f"{program} 运行时间: {run_time} 秒")  # 打印运行时间

            # 提取 success_flag 和 execute_flag
            match = re.search(r'(\d),(\d)', output)
            if match:
                success_flag, execute_flag = map(int, match.groups())
                results[program].append((success_flag, execute_flag))
                
                # 从文件名提取问题编号，假设问题编号在文件名中
                problem_num = int(re.search(r'problem(\d+)', problem_file).group(1))

                # 累加成功和执行标志
                flags_summary[program][problem_num][0] += success_flag  # 累加成功标志
                flags_summary[program][problem_num][1] += execute_flag  # 累加执行标志
            else:
                results[program].append((None, None))

# 汇总输出并写入文件
output_file = os.path.join(dataset_position, "results_summary.txt")

with open(output_file, 'w') as f:
    f.write("汇总结果:\n")
    
    # 写入每个程序的输出
    for program, outputs in results.items():
        # 确保输出格式化时，None 值不会引发问题
        formatted_outputs = [
            f"[{success_flag if success_flag is not None else 'None'}," 
            f"{execute_flag if execute_flag is not None else 'None'}]"
            for success_flag, execute_flag in outputs
        ]
        f.write(f"{program} 输出: {formatted_outputs}\n")
        print(f"{program} 输出: {formatted_outputs}")  # 也打印到控制台

    # # 写入每个程序的运行时间
    # f.write("\n每个程序的运行时间:\n")
    # for program, times in run_times.items():
    #     f.write(f"{program} 运行时间: {times}\n")
    #     print(f"{program} 运行时间: {times}")  # 也打印到控制台

    # # 计算并写入每个程序的平均运行时间
    # f.write("\n每个程序的平均运行时间:\n")
    # for program, times in run_times.items():
    #     average_time = sum(times) / len(times) if times else 0
    #     f.write(f"{program} 平均运行时间: {average_time} 秒\n")
    #     print(f"{program} 平均运行时间: {average_time} 秒")

    # 写入每个问题的标志计数
    f.write("\n每个问题的标志计数:\n")
    for program in programs:
        for problem in problem_range:
            success_count, execute_count = flags_summary[program][problem]
            f.write(f"{program} - 问题 {problem} 的成功标志总和: {success_count}, 执行标志总和: {execute_count}\n")
            print(f"{program} - 问题 {problem} 的成功标志总和: {success_count}, 执行标志总和: {execute_count}")  # 也打印到控制台

    # 计算并写入每个程序的成功率和执行率
    f.write("\n每个程序的成功率和执行率:\n")
    for program in programs:
        program_total_success = sum([flags_summary[program][problem][0] for problem in problem_range])
        program_total_execute = sum([flags_summary[program][problem][1] for problem in problem_range])
        program_total_tries = len(problem_range) * runs_per_problem
        program_success_rate = program_total_success / program_total_tries if program_total_tries > 0 else 0
        program_execute_rate = program_total_execute / program_total_tries if program_total_tries > 0 else 0
        f.write(f"{program} 的成功率: {program_success_rate}, 执行率: {program_execute_rate}\n")
        print(f"{program} 的成功率: {program_success_rate}, 执行率: {program_execute_rate}")
print(f"结果已写入 {output_file}")