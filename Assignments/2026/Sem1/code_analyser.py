import termcolor  
import inspect
import copy
import ast
import math
import radon.complexity
import builtins
import test_correctness

all_correct = False

# worth 15 marks total
def score_correctness(correct, total):
    #print(f'score_correctness({correct}, {total}) ?')
    global all_correct
    assert correct <= total
    if correct == total:
        all_correct = True
        return 'Criteria fully satisfied', correct, total
    elif correct == 0:
        return 'Criteria not satisfied', correct, total
    else:
        return 'Criteria particaly satisfied', correct, total        

# worth 2 marks total
def score_complexity(overly_complex, total):
    #print(f'score_complexity({overly_complex}, {total}) 2')    
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

# worth 1 mark total
def score_assignments(found):
    #print(f'score_assignments({len(found)}) 1')    
    if len(found) > 0:
        return 'Criteria fully satisfied', 1, 1
    else:
        return 'Criteria not satisfied', 0, 1

# worth 4 marks total (20 calls expected)
def score_functions(missing_calls, expected_calls):
    #print(f'score_functions({missing_calls}, {expected_calls}) 4')
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
def score_loops(correct_score, total_score):
    #print(f'score_loops({correct_score}, {total_score}) 3')    
    assert correct_score <= 7 and total_score == 7
    if correct_score == total_score:
        return 'Criteria fully satisfied', 3, 3
    elif correct_score == 0:
        return 'Criteria not satisfied', 0, 3
    else:
        wrong = total_score - correct_score
        score = 3 - wrong / 2 # lose 0.5 marks per incorrect function
        if score > 0:
            return 'Criteria partially satisfied', score, 3
        else:
            return 'Criteria partially satisfied', 0.5, 3 # minimum score if at least one correct

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

all_functions = ['zero_velocity_equilibrium', 'delta_x', 'delta_y', 'apply_fan_force', 'opposite_direction', 'compute_density', 'compute_velocity', 'compute_speed', 'compute_equilibrium', 'relax_towards', 'compute_width_and_height', 'apply_fan_and_collide_within_one_cell', 'apply_fan_and_collide_all_cells', 'get_upstream_cell', 'stream_or_bounce_one_cell', 'stream_or_bounce_all_cells', 'simulate', 'Direction', 'math', 'copy']

            
expected = {
    'relax_towards': Function(),
    'zero_velocity_equilibrium':Function(ifStmt=True, complexity=9),
    'delta_x':Function(ifStmt=True, complexity=9),
    'delta_y':Function(ifStmt=True, complexity=9),
    'opposite_direction':Function(ifStmt=True, complexity=9),
    'compute_density':Function(),
    'compute_velocity':Function(Loops = 'ForEach', complexity=2, uses = ['compute_density']),
    'compute_speed':Function(uses = ['compute_velocity']),
    'compute_equilibrium':Function(Loops = 'ForEach', uses = ['delta_x', 'delta_y', 'zero_velocity_equilibrium'], complexity=2),
    'compute_width_and_height':Function(),
    'get_upstream_cell':Function(uses = ['delta_x', 'delta_y', 'compute_width_and_height'], ifStmt=True, complexity=3),
    'apply_fan_force':Function(ifStmt=True,complexity=2),
    'apply_fan_and_collide_within_one_cell':Function(Loops = 'ForEach', uses = ['relax_towards', 'compute_velocity', 'compute_density', 'apply_fan_force', 'compute_equilibrium'], complexity=3),
    'apply_fan_and_collide_all_cells':Function(Loops = 'RangeLoops', uses = ['compute_width_and_height', 'apply_fan_and_collide_within_one_cell', 'is_fan_cell_function'], ifStmt=True, complexity=4),
    'stream_or_bounce_one_cell':Function(Loops = 'ForEach', uses = ['get_upstream_cell', 'opposite_direction'], ifStmt=True, complexity=3),
    'stream_or_bounce_all_cells':Function(Loops = 'RangeLoops', uses = ['compute_width_and_height', 'stream_or_bounce_one_cell'], ifStmt=True, complexity=4),    
    'simulate':Function(Loops = 'RangeLoop', uses = ['apply_fan_and_collide_all_cells', 'stream_or_bounce_all_cells', 'report_new_distribution'], complexity=2),
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
        else:
            raise Exception(f'Unexpected loop type {expected_loops}')
    correct_score = 0
    expected_count = 0
    for function in functions:
        expected_loops = expected[function.__name__].Loops
        if expected_loops:
            expected_count += 1
            correct_score += loop_score(function, expected_loops)
            
    sum_score(*score_loops(correct_score, expected_count))

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
        actual_uses = function_uses(function)
        missing = expected_uses - actual_uses       
        if missing:
           print(f'Function {function.__name__} was expected to make use of function(s): {", ".join(missing)}.')
        expected_calls += len(expected_uses)
        missing_calls += len(missing)
    sum_score(*score_functions(missing_calls, expected_calls))      
        
def assignments(functions):
    def contains_assignment(function):
        found = []
        for node in ast.walk(AST(function)) :
            if isinstance(node, ast.Assign):
                found.append(node)
        return found

    found = []
    for function in functions:
        found.extend(contains_assignment(function))
    sum_score(*score_assignments(found)) 


def variables(functions):   
    idents = set()
    for function in functions:
        tree = AST(function)
        param_names = {arg.arg for arg in tree.body[0].args.args}
        for node in ast.walk(tree) :
            if isinstance(node, ast.Name):
                if not (node.id in param_names):
                    idents.add(node.id)
    idents = idents - set(dir(builtins)) - set(all_functions)
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
        if len(body) > 1 or not isinstance(body[0], ast.Pass):
            implemented = True 

        complexity_score = get_complexity(tree)
        if complexity_score > expect.complexity:
            print(f'Function {function.__name__} is more complex than necessary (complexity score = {complexity_score}, ideal = {expect.complexity})')
            errors =+ 1

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
    working = correctness(functions, relies_on)
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

    #Heading('Assessment Criteria 2d: Use of assignment statements')
    #assignments(functions)
    #print()
    
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

    return working