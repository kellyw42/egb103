# Do not modify this file. 
# You don't need to understand or use anything in this file.

import termcolor  
import inspect
import copy
import ast
import math
import radon.complexity
import builtins
import hidden.test_correctness as test_correctness
import builtins



python_functions = set([name for name in dir(builtins) if callable(getattr(builtins, name))])

# worth 15 marks total
def score_correctness(correct, total):
    #print(f'score_correctness({correct}, {total}) ?')
    assert correct <= total
    if correct == total:
        return 'Criteria fully satisfied', correct, total
    elif correct == 0:
        return 'Criteria not satisfied', correct, total
    else:
        return 'Criteria particaly satisfied', correct, total        

# worth 2 marks total
def score_complexity(overly_complex, total):
    #print(f'score_complexity({overly_complex}, {total})')    
    if overly_complex == total:
        return 'Criteria not satisfied', 0, 2
    elif overly_complex > total/2:
        return 'Criteria particaly satisfied', 0.5, 2
    elif overly_complex > total/4:
        return 'Criteria partially satisfied', 1, 2
    elif overly_complex > 0:
        return 'Criteria partially satisfied', 1.5, 2
    else:
        return 'Criteria fully satisfied', 2, 2


# worth 4 marks total (20 calls expected)
def score_functions(missing_calls, expected_calls):
    print(f'score_functions({missing_calls}, {expected_calls})') # 
    correct = expected_calls - missing_calls
    mark = math.floor(8 * correct / expected_calls) / 2
    if correct > 0 and mark == 0:
        mark = 0.5  
    if mark == 4:
        return 'Criteria fully satisfied', 4, 4
    elif mark == 0:
        return 'Criteria not satisfied', 0, 4
    else:
        return f'Criteria partially satisfied ({correct} of {expected_calls} function calls)', mark, 4

# worth 3 marks total
def score_loops(unnecessary_count, correct_score, total_score):
    #print(f'score_loops({correct_score}, {total_score}) 3')    
    assert correct_score <= 2 and total_score == 3

    if unnecessary_count == 0:
        correct_score += 1
    elif unnecessary_count == 1:
        correct_score += 0.5
        
    if correct_score == total_score:
        return 'Criteria fully satisfied', 3, 3
    elif correct_score == 0:
        return 'Criteria not satisfied', 0, 3
    else:
        return 'Criteria partially satisfied', correct_score, 3


# worth 1 mark total
def score_ifs(actual, expected):
    #print(f'score_ifs({actual}, {expected}) 1')    
    if actual == expected:
        return 'Criteria fully satisfied', 1, 1
    elif actual > 1:
        return 'Criteria partially satisfied', 0.5, 1
    else:
        return 'Criteria not satisfied', 0, 1

# -----------------------------------------------------------------------------------

class Function :
    complexity = 1
    uses = {}
    ifStmt = False
    Loops = None
    
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


my_names = set(['adaptive_time_step', 'air_density', 'announce', 'artemis2_mission_timeline', 'atmosphere_rotation_velocity', 'celestial_body', 'celestial_body_position', 'convert_seconds_to_string', 'detect_perigee_and_apogee', 'drag_acceleration', 'earth', 'moon', 'earth_altitude', 'earth_gravitational_acceleration', 'earth_position_and_velocity', 'engine_acceleration', 'ephemeris_time', 'ephemeris_time_to_utc_string', 'EventKind', 'execute_mission', 'execute_mission_event', 'execute_next_mission_event_if_triggered', 'gravitational_acceleration', 'gravity_turn_direction', 'is_mission_complete', 'is_mission_event_triggered_now', 'log_interval', 'log_mission_state', 'math', 'max_mission_duration_hours','mission_elapsed_time','mission_event', 'mission_events', 'moon_gravitational_acceleration', 'moon_position', 'net_acceleration', 'next_mission_event', 'position', 'spacecraft', 'Spacecraft', 'time_step', 'mission_log', 'unit_vector', 'up_direction', 'update_position_and_velocity', 'utc_launch_time', 'utc_to_ephemeris_time', 'vector_add', 'vector_magnitude', 'vector_scale', 'vector_subtract', 'velocity_direction', 'zero_vector'])

            
expected = {
    'earth_altitude': Function(),
    'gravitational_acceleration':Function(uses=['unit_vector', 'vector_subtract', 'vector_scale', 'vector_magnitude']),
    'earth_gravitational_acceleration':Function(uses=['zero_vector', 'gravitational_acceleration']),
    'moon_gravitational_acceleration':Function(uses=['moon_position', 'gravitational_acceleration']),
    'drag_acceleration':Function(uses=['air_density', 'unit_vector', 'vector_magnitude', 'zero_vector', 'vector_scale', 'relative_air_velocity', 'earth_altitude'], ifStmt=True, complexity=2),
    'gravity_turn_direction':Function(uses=['vector_add', 'earth_altitude', 'vector_scale']),
    'engine_acceleration':Function(ifStmt=True, uses=['unit_vector', 'vector_scale', 'gravity_turn_direction', 'zero_vector'], complexity=4),
    'net_acceleration':Function(uses=['vector_add', 'engine_acceleration', 'earth_gravitational_acceleration', 'drag_acceleration', 'moon_gravitational_acceleration']),
    'update_position_and_velocity':Function(uses=['vector_add', 'net_acceleration', 'vector_scale']),
    'log_mission_state':Function(ifStmt=True, complexity=4),
    'is_mission_event_triggered_now':Function(uses=['earth_altitude'], complexity=5),
    'execute_mission_event':Function(ifStmt=True, uses=['earth_position_and_velocity'], complexity=7),
    'execute_next_mission_event_if_triggered':Function(ifStmt=True, uses = ['is_mission_event_triggered_now', 'announce', 'execute_mission_event'], complexity=3),
    'adaptive_time_step':Function(uses = [], ifStmt=True, complexity=2),
    'execute_mission':Function(Loops = 'WhileLoop', uses = ['adaptive_time_step', 'update_position_and_velocity', 'Spacecraft', 'log_mission_state', 'utc_to_ephemeris_time', 'execute_next_mission_event_if_triggered'], complexity=3),
    'detect_perigee_and_apogee':Function(Loops = 'RangeLoop', uses = ['ephemeris_time_to_utc_string', 'convert_seconds_to_string', 'earth_altitude'], ifStmt=True, complexity=5)
}


# -----------------------------------------------------------------------------------

def Pass(msg) :
    print(termcolor.colored(msg,'green'))
    
def Fail(msg) :
    print(termcolor.colored(msg, 'red'))
    return False

def Heading(msg) :
    print(termcolor.colored(msg, attrs=['bold'])) 

def AST(function):
    source = inspect.getsource(function)
    return ast.parse(source)    

grand_total = 0
possible_points = 0


def sum_score(msg, mark, total):
    global grand_total, possible_points
    grand_total += mark
    possible_points += total
    if 'fully satisfied' in msg:
        Pass(f'{msg} ({mark} out of {total})')    
        return True
    else:
        Fail(f'{msg} ({mark} out of {total})')
        return False


def if_statements(functions):
    def has_if(function):
        for node in ast.walk(AST(function)) :
            if isinstance(node, ast.If):
                return True
        return False
        
    correct_count = 0
    expected_count = 0
    for function in functions:
        if expected[function.__name__].ifStmt:
            expected_count += 1
            if has_if(function):
                correct_count += 1
            else:
                print(f'Expected to find an if statement in function {function.__name__}')
        else:
            if has_if(function):
                print(f'Did not expected to find an if statement in function {function.__name__}')
    sum_score(*score_ifs(correct_count, expected_count))

    
def loops(functions):      
    def is_for_loop(node) :
        return isinstance(node, ast.For)
    
    def is_while_loop(node) :
        return isinstance(node, ast.While)
        
    def is_range_loop(node) :
        return is_for_loop(node) and node.iter and isinstance(node.iter, ast.Call) and node.iter.func and isinstance(node.iter.func, ast.Name) and node.iter.func.id == 'range'
    
    def loop_score(function, expected_loops):
        whileLoops = 0
        rangeLoops = 0
        foreachLoops = 0
        nestedLoops = 0
        for node in ast.walk(AST(function)) :
            if isinstance(node, ast.While):
                whileLoops += 1
                for child in ast.walk(ast.Module(body=node.body)):
                    if isinstance(child, (ast.While, ast.For)):
                        nestedLoops += 1
            if isinstance(node, ast.For):
                for child in ast.walk(ast.Module(body=node.body)):
                    if isinstance(child, (ast.While, ast.For)):
                        nestedLoops += 1                
                if node.iter and isinstance(node.iter, ast.Call) and node.iter.func and isinstance(node.iter.func, ast.Name) and node.iter.func.id == 'range':
                    rangeLoops += 1
                else:
                    foreachLoops += 1

        totalLoops = whileLoops + rangeLoops + foreachLoops

        if expected_loops == None:
            if totalLoops > 0:
                print(f'Function {function.__name__} is not expected to include a loop.')
                return 0
            else:
                return 1
        
        if totalLoops == 0:
            print(f'Function {function.__name__} is expected to include a loop.')
            return 0    
        elif nestedLoops > 0 and not expected_loops.endswith('s'):
            print(f'Function {function.__name__} does not require nested loops.')
            return 0
        elif totalLoops > 1 and not expected_loops.endswith('s'):
            print(f'Function {function.__name__} does not require more than one loop.')
            return 0
        elif expected_loops == 'ForEach':
            if foreachLoops != 1:
                print(f'Function {function.__name__} is expected to include a single for each loop.')
                return 0
            else:
                return 1
        elif expected_loops == 'RangeLoop':
            if rangeLoops != 1:
                print(f'Function {function.__name__} is expected to include a single range loop.')
                return 0
            else:
                return 1
        elif expected_loops == 'RangeLoops':
            if rangeLoops != 2 or nestedLoops != 1:
                print(f'Function {function.__name__} is expected to include nested range loops.')
                return 0
            else:
                return 1    
        elif expected_loops == 'WhileLoop':
            if whileLoops != 1:
                print(f'Function {function.__name__} is expected to include a single while loop.')
                return 0
            else:
                return 1                
        else:
            raise Exception(f'Unexpected loop type {expected_loops}')
    correct_score = 0
    expected_count = 0
    unnecessary_count = 0
    implemented = False
    for function in functions:

        tree = AST(function)
        body = tree.body[0].body
        if len(body) > 1 or not isinstance(body[0], ast.Raise):
            implemented = True 
        
        expected_loops = expected[function.__name__].Loops
        if expected_loops:
            expected_count += 1
            correct_score += loop_score(function, expected_loops)
        else:
            if loop_score(function, None) == 0:
                unnecessary_count += 1

    if not implemented:
        print("No functions have been implemented yet, so their loop usage can't be assessed")
        unnecessary_count = 2
    
    sum_score(*score_loops(unnecessary_count, correct_score, expected_count+1))


def function_calls(functions):
    def function_uses(function):
        calls = set()
        for node in ast.walk(AST(function)) :
            if isinstance(node, ast.Call) and node.func and isinstance(node.func, ast.Name):
                calls.add(node.func.id)
        return calls

    expected_calls =  0
    missing_calls = 0
    for function in functions:
        expected_uses = set(expected[function.__name__].uses)
        actual_uses = function_uses(function) - python_functions
        
        missing = expected_uses - actual_uses       
        if missing:
           print(f'Function {function.__name__} was expected to make use of function(s): {", ".join(missing)}.')
            
        extra = actual_uses - expected_uses
        if extra:
            print(f'Function {function.__name__} was not expected to make use of function(s): {", ".join(extra)}.')
            
        expected_calls += len(expected_uses)
        missing_calls += len(missing)
    sum_score(*score_functions(missing_calls, expected_calls))      

   
def variables(functions):   
    idents = set()
    for function in functions:
        tree = AST(function)
        param_names = {arg.arg for arg in tree.body[0].args.args}
        for node in ast.walk(tree) :
            if isinstance(node, ast.Name):
                if not (node.id in param_names):
                    idents.add(node.id)
    idents = idents - set(dir(builtins)) - my_names
    print('Consider if all of your variable names are meaningful:', ', '.join(idents))
    print('(This criteria will be marked manually after submission).')

def maintainability(functions):
    print('Have you added comments where necessary inside your functions to make them easier to understand and used markdown cells to document your experimental observations?')
    print('(This criteria will be marked manually after submission).')    
    
def complexity(functions):
    def get_complexity(AST) :                
        for defn in radon.complexity.cc_visit(AST):
            return defn.complexity

    implemented = False
    errors = 0
    for function in functions:
        expect = expected[function.__name__]
        tree = AST(function)

        body = tree.body[0].body
        if len(body) > 1 or not isinstance(body[0], ast.Raise):
            implemented = True 

        complexity_score = get_complexity(tree)
        if complexity_score > expect.complexity:
            print(f'Function {function.__name__} is more complex than necessary (complexity score = {complexity_score}, ideal = {expect.complexity})')
            errors += 1

    if not implemented:
        print("No functions have been implemented yet, so their complexity can't be assessed")
        errors = len(functions)
        
    sum_score(*score_complexity(errors, len(functions)))

def correctness(functions, relies_on):
    correct = 0
    others = functions + relies_on
    for function in functions:
        if test_correctness.run_tests(function, explain=False, relies_on=others):
            print(f'\u2705 Passed {function.__name__}')
            correct += 1
        else:
            print(f'\u274C Failed {function.__name__}')
    return sum_score(*score_correctness(correct, len(functions)))

def analyse_assessment_criteria(functions, relies_on=[]):

    global grand_total, possible_points 
    grand_total = 0
    possible_points = 0

    Heading('Assessment Criteria 1: Functional correctness')
    correctness(functions, relies_on)
    print()
    
    Heading('Assessment Criteria 2a: Use of if statements')
    if_statements(functions)
    print()

    Heading('Assessment Criteria 2b: Appropriate use of loops')
    loops(functions)
    print()

    Heading('Assessment Criteria 2c: Functions make use of other appropriate functions')
    function_calls(functions)
    print()
    
    Heading('Assessment Criteria 3a: Meaningful variable names')
    variables(functions)
    print()
    
    Heading('Assessment Criteria 3b: Complexity of code')
    complexity(functions)
    print()

    Heading('Assessment Criteria 3c: Maintainability')
    maintainability(functions)
    print()    

    Heading(f'Part B Total: {grand_total} out of {possible_points}')
    print('(The remaining 3 marks for criteria 3a and 3c will be marked manually after submission)')