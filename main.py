import os
import re
import argparse
import subprocess
import time
from config import args


dataset_position = args.default_dataset_position  # Directory of problem files
program_directory = args.default_project_directory  # Directory of program files
prompt_directory=args.default_prompt_position
api_key=args.api_key

# Define problem range, manage centrally
problem_range = range(args.start_idx, args.end_idx)

# Dynamically generate the list of problem files using the problem range
problem_files = [os.path.join(dataset_position, f"problem{i}.txt") for i in problem_range]


# Define the programs to be executed
programs = [
    os.path.join(program_directory,'OptiRA.py'), 
    # os.path.join(program_directory,'baseline_Optimus.py'),
    # os.path.join(program_directory,'baseline_COT_refine.py'),
    # os.path.join(program_directory,'baseline_PS_refine.py'),
    # os.path.join(program_directory,'baseline_COT.py'), 
    # os.path.join(program_directory,'baseline_PS.py')
]


# Store the results
results = {program: [] for program in programs}
# Used to store the success and execution flag totals for each problem
flags_summary = {program: {problem: [0, 0] for problem in problem_range} for program in programs}  
# Used to store the runtime for each program during each execution
run_times = {program: [] for program in programs}  


# Loop to execute 
for i in range(args.runs_per_problem):
    print(f"Running the {i + 1} time(s)")
    for problem_file in problem_files:
        with open(problem_file, 'r', encoding="utf-8") as f:
            problem_content = f.read().strip()
        
        for program in programs:
            start_time = time.time()  # Record start time
            # prompt_directory=escape_backslash(prompt_directory)
            # dataset_position=escape_backslash(dataset_position)
            # program_directory=escape_backslash(program_directory)
            # print("prompt:"+prompt_directory)
            command = [
                "python", "OptiRA.py",
                "--problem", problem_content,
                "--api_key", api_key,
                "--default_prompt_position", prompt_directory,
                "--default_dataset_position", dataset_position,
                "--default_project_directory", program_directory
            ]
            result = subprocess.run(command, capture_output=True, text=True)
            output=result.stdout 
            end_time = time.time()  # Record end time
            run_time = end_time - start_time  # Calculate runtime
            run_times[program].append(run_time)

            print(f"{program} output: {output}")
            # print(f"{program} runtime: {run_time} seconds")  # Print runtime

            # Extract success_flag and execute_flag
            match = re.search(r'(\d),(\d)', output)
            if match:
                success_flag, execute_flag = map(int, match.groups())
                results[program].append((success_flag, execute_flag))
                
                # Extract problem number from the file name, assuming the problem number is in the file name
                problem_num = int(re.search(r'problem(\d+)', problem_file).group(1))

                # Accumulate success and execution flags
                flags_summary[program][problem_num][0] += success_flag  # Accumulate success flag
                flags_summary[program][problem_num][1] += execute_flag  # Accumulate execution flag
            else:
                results[program].append((None, None))

# Summarize the output and write to file
output_file = os.path.join(dataset_position, "results_summary.txt")


with open(output_file, 'w') as f:
    # Write the summary results
    f.write("Summary of Results:\n")

    # Write the output for each program
    for program, outputs in results.items():
        formatted_outputs = [
            f"[{success_flag if success_flag is not None else 'None'},"
            f"{execute_flag if execute_flag is not None else 'None'}]"
            for success_flag, execute_flag in outputs
        ]
        f.write(f"{program} output: {formatted_outputs}\n")
        print(f"{program} output: {formatted_outputs}")

    # Write the flag counts for each problem
    f.write("\nFlag counts for each problem:\n")
    for program in programs:
        for problem in problem_range:
            success_count, execute_count = flags_summary[program][problem]
            f.write(f"{program} - Total success flags for problem {problem}: {success_count}, Total execute flags: {execute_count}\n")
            print(f"{program} - Total success flags for problem {problem}: {success_count}, Total execute flags: {execute_count}")

    # Calculate and write the success rate and execution rate for each program
    f.write("\nSuccess rate and execution rate for each program:\n")
    for program in programs:
        program_total_success = sum([flags_summary[program][problem][0] for problem in problem_range])
        program_total_execute = sum([flags_summary[program][problem][1] for problem in problem_range])
        program_total_tries = len(problem_range) * args.runs_per_problem
        program_success_rate = program_total_success / program_total_tries if program_total_tries > 0 else 0
        program_execute_rate = program_total_execute / program_total_tries if program_total_tries > 0 else 0
        f.write(f"{program}'s success rate: {program_success_rate}, execution rate: {program_execute_rate}\n")
        print(f"{program}'s success rate: {program_success_rate}, execution rate: {program_execute_rate}")

print(f"Results have been written to {output_file}")

