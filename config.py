import argparse


def parse_arguments():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--api_key", default="", help="api key for gpt3.5"
    )
    parser.add_argument(
        "--max_length", default = 16000, help = "max input+output tokens"
    )
    parser.add_argument(
        "--default_prompt_position", default="Yourpath\LLM-OptiRA\Prompt", help="use to redirect to default prompt"
    )
    parser.add_argument(
        "--default_dataset_position", default="Yourpath\LLM-OptiRA\Dataset", help="use to redirect to default prompt"
    )
    parser.add_argument(
        "--default_project_directory", default="Yourpath\LLM-OptiRA", help="use to redirect to default prompt"
    )
    parser.add_argument(
         "--read_from_file", default=True, action=argparse.BooleanOptionalAction, help = "use file to read"
     )
    parser.add_argument("--problem", default="",required=False, help="already defined in code")
    parser.add_argument("--start_idx", type=int,default=1,required=False)
    parser.add_argument("--end_idx", type=int,default=2,required=False)
    parser.add_argument("--runs_per_problem", type=int,default=1,required=False)
    parsed_args = parser.parse_args()
    return parsed_args


args = parse_arguments()
