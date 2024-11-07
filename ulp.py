import os
import re
import sys
import argparse
import platform
import time
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
from colorama import Fore, Style, init
from tqdm import tqdm
from queue import Queue

# Initialize colorama
init(autoreset=True)

def clear_console():
    os_system = platform.system()
    if os_system == "Windows":
        os.system('cls')
    else:
        os.system('clear')

def print_logo():
    logo = r"""
 _____ _                _____            _            
/  ___| |              /  ___|          | |           
\ `--.| |__   ___ _ __ \ `--.  ___  _ __| |_ ___ _ __ 
 `--. \ '_ \ / _ \ '_ \ `--. \/ _ \| '__| __/ _ \ '__|
/\__/ / | | |  __/ |_) /\__/ / (_) | |  | ||  __/ |   
\____/|_| |_|\___| .__/\____/ \___/|_|   \__\___|_|   
                 | |                                  
                 |_|                                  
    """
    print(f"{Fore.LIGHTRED_EX}{logo}{Style.RESET_ALL}")
    print(f"{Fore.LIGHTRED_EX}Author  : Guinness Shepherd{Style.RESET_ALL}")
    print(f"{Fore.LIGHTRED_EX}The fastest URL:Log:Pass Extractor{Style.RESET_ALL}")
    print(f"{Fore.LIGHTRED_EX}{'=' * 50}{Style.RESET_ALL}\n")

async def process_file(file_path, patterns, credentials, progress, lock):
    """
    Process each file asynchronously, applying regex patterns and storing found credentials.
    """
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
            content = file.read()
            found = False
            for pattern in patterns:
                matches = pattern.findall(content)  # findall works with compiled regex objects
                for match in matches:
                    if not isinstance(match, (tuple, list)):
                        match = [match]
                    match = [item.strip() for item in match]
                    credential_line = ':'.join(match)
                    with lock:
                        if credential_line not in credentials:
                            credentials.add(credential_line)
                            print(f"{Fore.GREEN}[+] Extracted: {credential_line}{Style.RESET_ALL}")
                            found = True
            if not found:
                print(f"{Fore.YELLOW}[!] No match found in {file_path}{Style.RESET_ALL}")
        progress.update(1)
    except Exception as e:
        print(f"{Fore.RED}[ERROR] Could not read file {file_path}: {e}{Style.RESET_ALL}")

async def handle_files(file_paths, patterns, credentials, lock):
    """
    Handles the asynchronous processing of file paths.
    """
    tasks = []
    progress = tqdm(total=len(file_paths), desc="Processing files", unit="file")

    for file_path in file_paths:
        task = asyncio.ensure_future(process_file(file_path, patterns, credentials, progress, lock))
        tasks.append(task)

    await asyncio.gather(*tasks)
    progress.close()

def search_files(directory, patterns, filename_keyword='pass', file_extension='.txt'):
    """
    Search for files in the directory that match the filename criteria and extract credentials using the provided patterns.
    """
    credentials = set()
    files_to_process = []

    # Collect all files to process
    for root, _, files in os.walk(directory):
        for file_name in files:
            if filename_keyword.lower() in file_name.lower() and file_name.lower().endswith(file_extension):
                file_path = os.path.join(root, file_name)
                files_to_process.append(file_path)

    return files_to_process, credentials

def write_output(credentials, output_file):
    """
    Write the extracted credentials to the output file.
    """
    try:
        with open(output_file, "w", encoding="utf-8", errors="ignore") as file:
            for credential in credentials:
                file.write(f"{credential}\n")
        print(f"{Fore.CYAN}[INFO] Credentials written to {output_file}{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}[ERROR] Could not write to output file {output_file}: {e}{Style.RESET_ALL}")

def main():
    parser = argparse.ArgumentParser(description='Ultimate URL:Log:Pass Extractor for Logs with Threading and Progress Indicator')
    parser.add_argument('-d', '--directory', type=str, default='.', help='Directory to search (default: current directory)')
    parser.add_argument('-o', '--output', type=str, default='credentials.txt', help='Output file for credentials (default: credentials.txt)')
    parser.add_argument('-k', '--keyword', type=str, default='pass', help="Keyword in filenames to search (default: 'pass')")
    parser.add_argument('-e', '--extension', type=str, default='.txt', help="File extension to search (default: '.txt')")
    args = parser.parse_args()

    clear_console()
    print_logo()

    # Compile regex patterns before using them
    patterns = [
        re.compile(r"URL[: ]+\s*(.*?)\s*(?:\n|$).*?(?:Username|Login|USER)[: ]+\s*(.*?)\s*(?:\n|$).*?(?:Password|PASS)[: ]+\s*(.*?)\s*(?:\n|$)"),
        re.compile(r"Host[: ]+\s*(.*?)\s*(?:\n|$).*?(?:Login|USER)[: ]+\s*(.*?)\s*(?:\n|$).*?(?:Password|PASS)[: ]+\s*(.*?)\s*(?:\n|$)"),
        re.compile(r"url[: ]+\s*(.*?)\s*(?:\n|$).*?login[: ]+\s*(.*?)\s*(?:\n|$).*?password[: ]+\s*(.*?)\s*(?:\n|$)"),
    ]

    # Search for files
    file_paths, credentials = search_files(args.directory, patterns, filename_keyword=args.keyword, file_extension=args.extension)

    start_time = time.time()

    # Use asyncio to handle file processing
    lock = threading.Lock()
    asyncio.run(handle_files(file_paths, patterns, credentials, lock))

    write_output(credentials, args.output)

    end_time = time.time()
    print(f"{Fore.CYAN}[INFO] Process completed in {end_time - start_time:.2f} seconds.{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
