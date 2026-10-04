import argparse
import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

"""负责注册参数后解析，比如:run_tests.py --suite all这样运行全部， --suite smoke只运行冒烟"""
def parse_args():
    parser = argparse.ArgumentParser(description="运行pytest接口自动化测试并生成报告")
    # 注册参数规则
    parser.add_argument("--suite",
                        choices=("all","smoke","regression"),default="all",help="选择要执行的测试集")
    parser.add_argument("--base-url",default="http://127.0.0.1:8000",help="被测API的基础地址")
    return parser.parse_args()

#负责启动pytest
def run_pytest(args):
    command = [sys.executable, "-m", "pytest", f"--base-url={args.base_url}"]
    if args.suite != "all":
        command.extend(["-m", args.suite])

    #subprocess.run()启动子进程并等待它结束，这里会等待pytest跑完再继续执行
    completed_process = subprocess.run(command, cwd=PROJECT_ROOT, check=False)
    return completed_process.returncode

def generate_allure_report():
    allure_args = ["allure", "generate", "allure-results", "-o", "allure-report", "--clean"]
    if sys.platform == "win32":
        command = ["cmd", "/c", *allure_args]
    else:
        command = allure_args
    completed_progress = subprocess.run(command, cwd=PROJECT_ROOT, check=False)
    return completed_progress.returncode

def main():
    #从parse_args()拿到命令行对象
    args = parse_args()
    test_exit_code = run_pytest(args)
    report_exit_code = generate_allure_report()

    #先跑pytest，所以把该状态码放在前面
    if test_exit_code != 0:
        raise SystemExit(test_exit_code)

    raise SystemExit(report_exit_code)

if __name__ == "__main__":
    main()