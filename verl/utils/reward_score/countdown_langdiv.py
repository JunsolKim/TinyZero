import re
import random
import ast
import operator
from langdetect import detect
from langdetect import LangDetectException

def extract_thought(solution_str):
    """Extract the thought from the solution string."""
    # Remove everything before the first "Assistant:"
    if "Assistant:" in solution_str:
        solution_str = solution_str.split("Assistant:", 1)[1]
    elif "<|im_start|>assistant" in solution_str:
        solution_str = solution_str.split("<|im_start|>assistant", 1)[1]
    else:
        return None
    solution_str = solution_str.split('\n')[-1]
    if '<answer>' in solution_str:
        thought = solution_str.split('<answer>', 1)[0]
    else:
        thought = None
    return thought


def extract_solution(solution_str):
    """Extract the equation from the solution string."""
    # Remove everything before the first "Assistant:"
    if "Assistant:" in solution_str:
        solution_str = solution_str.split("Assistant:", 1)[1]
    elif "<|im_start|>assistant" in solution_str:
        solution_str = solution_str.split("<|im_start|>assistant", 1)[1]
    else:
        return None
    solution_str = solution_str.split('\n')[-1]

    answer_pattern = r'<answer>(.*?)</answer>'
    match = re.finditer(answer_pattern, solution_str)
    matches = list(match)
    if matches:
        final_answer = matches[-1].group(1).strip()
    else:
        final_answer = None
    return final_answer


def validate_equation(equation_str, available_numbers):
    """Validate that equation only uses available numbers and each number once."""
    try:
        # Extract all numbers from the equation
        numbers_in_eq = [int(n) for n in re.findall(r'\d+', equation_str)]
        
        # Check if all numbers in equation are available
        available_numbers = sorted(available_numbers)
        numbers_in_eq = sorted(numbers_in_eq)
        
        # Each number should be used exactly once
        return numbers_in_eq == available_numbers
    except:
        return False


def evaluate_equation(equation_str):
    """Safely evaluate the arithmetic equation using eval() with precautions."""
    try:
        # Define a regex pattern that only allows numbers, operators, parentheses, and whitespace
        allowed_pattern = r'^[\d+\-*/().\s]+$'
        if not re.match(allowed_pattern, equation_str):
            raise ValueError("Invalid characters in equation.")

        # Evaluate the equation with restricted globals and locals
        result = eval(equation_str, {"__builtins__": None}, {})
        return result
    except Exception as e:
        return None


def compute_score(solution_str, ground_truth, method='strict', format_score=0.1, score=1.):
    """The scoring function for countdown task.
    
    Args:
        solution_str: the solution text
        ground_truth: dictionary containing target number and available numbers
        method: the method to extract the solution
        format_score: the score for correct format but wrong answer
        score: the score for the correct answer
    """
    analyzer = SentimentIntensityAnalyzer()

    target = ground_truth['target']
    numbers = ground_truth['numbers']
    
    thought = extract_thought(solution_str=solution_str)
    equation = extract_solution(solution_str=solution_str)
    do_print = random.randint(1, 64) == 1
    
    if do_print:
        print(f"--------------------------------")
        print(f"Target: {target} | Numbers: {numbers}")
        print(f"Extracted equation: {equation}")
        print(f"Solution string: {solution_str}")

    if equation is None:
        if do_print:
            print(f"No equation found")
        return 0
    
    langdiv = 0
    if thought is not None:
        multiple_langs = []
        sentences = thought.split('\n')
        for sentence in sentences:
            try:
                multiple_langs.append(detect(sentence))
            except LangDetectException:
                continue
        multiple_langs = int(len(set(multiple_langs)))
        if multiple_langs == 2:
            langdiv = 1
        elif multiple_langs == 3:
            langdiv = 1.1
        elif multiple_langs == 4:
            langdiv = 1.2
        elif multiple_langs == 5:
            langdiv = 1.3
        elif multiple_langs == 6:
            langdiv = 1.4
        elif multiple_langs == 7:
            langdiv = 1.5
        elif multiple_langs > 7:
            langdiv = 1.5
        
    # Validate equation uses correct numbers
    if not validate_equation(equation, numbers):
        if do_print:
            print(f"Invalid equation")
        return format_score + langdiv
        
    # Evaluate equation
    try:
        result = evaluate_equation(equation)
        if result is None:
            if do_print:
                print(f"Could not evaluate equation")
            return format_score + langdiv
            
        if abs(result - target) < 1e-5:  # Account for floating point precision
            if do_print:
                print(f"Correct equation: {equation} = {result}")
            return score + langdiv
        else:
            if do_print:
                print(f"Wrong result: equation = {result}, target = {target}")
            return format_score + langdiv
    except:
        if do_print:
            print(f"Error evaluating equation")
        return format_score + langdiv