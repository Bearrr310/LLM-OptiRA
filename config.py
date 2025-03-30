import argparse


def parse_arguments():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--api_key", default="", help="api key for gpt3.5"
    )
    parser.add_argument(
        "--utilized_model", default = "gpt-3.5-turbo", help = "the model you use"
    )
    parser.add_argument(
        "--max_length", default = 16000, help = "max input+output tokens"
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
         "--read_from_file", default=True, action=argparse.BooleanOptionalAction, help = "use file to read"
     )
    #添加 --problem 参数
    parser.add_argument("--problem", default="D:\\SEU\\LLM\\OptiRA\\problem1.txt",required=True, help="Problem content as a string")
    parsed_args = parser.parse_args()
    return parsed_args


args = parse_arguments()
