#!/usr/bin/env python3
import re

def csv_to_dict(file_path):
    """
    Reads a 2 column-CSV file and converts it into a list of dictionaries.

    Args:
        file_path (str): The path to the CSV file.

    Returns:
        list: A list of dictionaries, where each dictionary represents a row of the CSV file.
        {row[0]: row[1]}
    """

    with open(file_path, "r") as f:
        data = [line.strip().split(",") for line in f]

    return [{row[0]: row[1]} for row in data]

def bus_stop_raw_to_dict(file_path):
    """
    Reads a CSV file and converts it into a list of dictionaries.

    Args:
        file_path (str): The path to the CSV file.

    Returns:
        list: A list of dictionaries, where each dictionary represents a row of the CSV file.
    """

    with open(file_path, "r") as f:
        data = [line.strip().split(",") for line in f]
    data_dict = {}
    for row in data:
        data_dict.update({row[0]: row[1] + "-" + row[2]})
    
    return data_dict

def extract_function_info(text: str):
    '''
    ----
    Input: 'FUNCTION_0'
    Output: FUNCTION_0, []
    ----
    Input: 'FUNCTION_1<arg1>'
    Output: FUNCTION_1, [arg1]
    ----
    Input: 'FUNCTION_2<arg1><arg2>'
    Output: FUNCTION_2, [arg1, arg2]
    ----
    '''
    pattern = r"(\w+)((?:<([^<>]+)>)*)"
    # pattern = r"(\w+)((?:<(\w+)>)*)"
    match = re.match(pattern, text)

    if match:
        function_name = match.group(1)
        args = re.findall(r"<([^<>]+)>", match.group(2)) 
        # args = re.findall(r"<(\w+)>", match.group(2))  # Find all arguments inside <>
        return function_name, args
    else:
        return None, None

if __name__ == "__main__":
    # Example usage:
    text0 = "FUNCTION_0"
    text1 = "FUNCTION_1<arg1>"
    text2 = "FUNCTION_2<arg1><arg2>"
    text3 = "FUNCTION_3<arg1><arg2><arg3><arg4><arg5>"

    function_name, args = extract_function_info(text0)
    print(function_name, args)  # Should print: FUNCTION_0 []

    function_name, args = extract_function_info(text1)
    print(function_name, args)  # Should print: FUNCTION_1 ['arg1']

    function_name, args = extract_function_info(text2)
    print(function_name, args)  # Should print: FUNCTION_2 ['arg1', 'arg2']

    function_name, args = extract_function_info(text3)
    print(function_name, args)
