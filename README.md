# LLM-OptiRA: LLM-Driven Optimization of Resource Allocation for Non-Convex Problems in Wireless Communications

This repository provides the implementation for our paper:

📎 **Paper Link:** [[arXiv/IEEE/DOI link]](https://arxiv.org/abs/2505.02091)

## **📌 Abstract**

Solving non-convex resource allocation problems poses significant challenges in wireless communication systems, often beyond the capability of traditional optimization techniques. To address this issue, we propose LLM-OptiRA, the first framework that leverages large language models (LLMs) to automatically detect and transform non-convex components into solvable forms, enabling fully automated resolution of non-convex resource allocation problems in wireless communication systems. LLM-OptiRA not only simplifies problem-solving by reducing reliance on expert knowledge, but also integrates error correction and feasibility validation mechanisms to ensure robustness. Experimental results show that LLM-OptiRA achieves an execution rate of 96% and a success rate of 80% on GPT-4, significantly outperforming baseline approaches in complex optimization tasks across diverse scenarios.

## **🗺️ Overview**

![main.png](assets/main.png)

**Figure 1: Overview of the LLM-OptiRA Framework**

This figure demonstrates the LLM-OptiRA framework's process for optimizing wireless resource allocation using the GEO satellite user-beam allocation example, covering steps from problem description to result validation.

## **🚀 Installation**

Clone the repository and install dependencies:

```bash
git clone https://github.com/Bearrr310/LLM-OptiRA
cd LLM-OptiRA
pip install -r requirements.txt

```

## **⚙️ Usage**

To run the main script:

linux:

```bash
export OPENAI_KEY=""

python main.py \
    --default_prompt_position Yourpath/OptiRA/Prompt/ \
    --default_dataset_position Yourpath/OptiRA/Dataset/ \
    --default_project_directory Yourpath/OptiRA/ \
    --api_key $OPENAI_KEY \
    --start_idx 0 \
    --end_idx 1 \
    --runs_per_problem 1

```

windows:

```bash
set OPENAI_KEY=

python main.py ^
    --default_prompt_position "Yourpath\LLM-OptiRA\Prompt" ^
    --default_dataset_position "Yourpath\LLM-OptiRA\Dataset" ^
    --default_project_directory "Yourpath\LLM-OptiRA" ^
    --api_key %OPENAI_KEY% ^
    --start_idx 0 ^
    --end_idx 1 ^
    --runs_per_problem 1


```

### Parameters Description

To run `main.py`, the following parameters should be provided:

- `-default_prompt_position`: The directory where the prompt templates are stored.
    - Example: `Yourpath/OptiRA/Prompt/`
- `-default_dataset_position`: The directory where the dataset files are stored.
    - Example: `Yourpath/OptiRA/Dataset/`
- `-default_project_directory`: The root directory of the project.
    - Example: `Yourpath/OptiRA/`
- `-api_key`: The OpenAI API key used for GPT-based computations.
    - Set this environment variable before running the script:
        
        ```bash
        export OPENAI_KEY="your-api-key"
        
        ```
        
- `-start_idx`: The starting index of the dataset problems to be processed.
- `-end_idx`: The ending index (exclusive) of the dataset problems to be processed.
    - The script processes problems in the range `[start_idx, end_idx)`.
    - Example: `-start_idx 1 --end_idx 3` will process problems indexed at `1` and `2`, but not `3`.
- `-runs_per_problem`: The number of times each problem should be executed.
    - Example: `5` (each problem in the selected range will be executed 5 times).

### 🏃‍♂️ Selecting Programs to Execute(Modify in `main.py`**)**

In `main.py`, the `programs` variable specifies which programs to run. You can execute the OptiRA approach and its baseline methods in parallel. By default, the code runs the following programs:

- `OptiRA.py`: Our OptiRA approach.
- `baseline_Optimus.py`: **OptiMUS**, a framework utilizing LLMs to formulate and solve Mixed Integer Linear Programming (MILP) problems from natural language descriptions.
- `baseline_COT_refine.py`: **Chain-of-Thought (CoT)**, which generates a step-by-step reasoning process, encouraging the model to break down complex problems into smaller steps. It is enhanced with a **refine** stage from the LLM-OptiRA framework, which includes the ECL and FDC process.
- `baseline_PS_refine.py`: **Plan-and-Solve (PS)**, which enhances LLMs' reasoning by dividing problem-solving into two stages: "planning" and "solving." This baseline method is paired with a **refine** stage from the LLM-OptiRA framework.
- `baseline_COT.py`: A basic version of **Chain-of-Thought (CoT)** without the refine stage.
- `baseline_PS.py`: A basic version of **Plan-and-Solve (PS)** without the refine stage.

To enable or disable specific baseline methods, you can modify the `programs` variable directly in `main.py`. For example, if you want to compare `OptiRA` with `baseline_PS_refine.py`, you can change it like this:

```python
programs = [
    os.path.join(program_directory, 'OptiRA.py'),
    os.path.join(program_directory, 'baseline_PS_refine.py')
]

```

## **📊 Results & Visualization**

### Main Result

![exp1.png](assets/exp1.png)

**Figure 2: Comparison of Execution and Success Rates for Different Schemes using GPT-4 and GPT-3.5 Models**

This figure shows that LLM-OptiRA outperforms baseline methods in execution and success rates on both GPT-4 and GPT-3.5 models, highlighting its effectiveness in solving non-convex problems.

![heatmap.png](assets/heatmap.png)

**Figure 3: Impact of Omitting Key Components of the LLM-OptiRA Framework on Success and Execution Rates across GPT4 and GPT-3.5**

This figure reveals that removing components like convexification, ECL, or FDC significantly reduces the success and execution rates, emphasizing their importance in the framework.

![iteration.png](assets/iteration.png)

**Figure 4: Success and Execution Rates for LLM-OptiRA under Different Maximum Iteration Counts for ECL and FDC**

This figure indicates that ECL and FDC improve success and execution rates, with ECL being effective in early iterations and FDC enhancing the success rate steadily as iterations increase.


## **📬 Contact**

For questions, please open an issue or reach out to bearrr310@outlook.com
