# Do not modify this file!!!

import ast
import termcolor  
import ipykernel
import os
import urllib.request
from pathlib import Path
import json
import math
import radon.complexity
import radon.metrics
from IPython.display import display, HTML

expected_functions = {
    'brisbane_wind_rose': 'def brisbane_wind_rose():',
    'unzip': 'def unzip(layout):',
    'evaluate_turbine_layout': 'def evaluate_turbine_layout(layout):',
    'visualize_layout': 'def visualize_layout(layout):',
    'create_grid_layout': 'def create_grid_layout(number_of_rows, number_of_columns, minimum_gap_between_turbines):',
    'create_hexagonal_layout': 'def create_hexagonal_layout(number_of_rows, number_of_columns, minimum_gap_between_turbines):',
    'rotate_single_location': 'def rotate_single_location(location, angle_degrees):',
    'rotate_layout': 'def rotate_layout(layout, angle_degrees):',
    'find_best_rotation': 'def find_best_rotation(layout):',
    'zero_yaw': 'def zero_yaw(layout):',
    'evaluate_single_direction_with_yaws': 'def evaluate_single_direction_with_yaws(layout, wind_direction, yaw_angles):',
    'visualize_flow_with_yaws': 'def visualize_flow_with_yaws(layout, wind_direction, yaw_angles, axis=None):',
    'greedy_optimize_yaw_angle_for_just_one_turbine': 'def greedy_optimize_yaw_angle_for_just_one_turbine(turbine_number, layout, wind_direction, yaw_angles):',
    'distance_downwind': 'def distance_downwind(turbine_location, wind_direction_degrees):',
    'sort_turbines_by_distance_downwind': 'def sort_turbines_by_distance_downwind(list_of_distances):',
    'orderby_downwind': 'def orderby_downwind(layout, wind_direction):',
    'optimize_all_yaw_angles': 'def optimize_all_yaw_angles(layout, wind_direction):', 
    'visualize_before_and_after_yaw_optimization': 'def visualize_before_and_after_yaw_optimization(layout, wind_direction):'}

grand_total = 0

def test_only_one_copy(code_cells) :
    ok = True
    seen = {}
    for src, AST in code_cells :    
        for node in ast.walk(AST) :
            if isinstance(node, ast.FunctionDef) :  
                if node.name in seen :
                    ok = False
                    Fail(f'Error: multiple definitions of function {node.name}')
                else :
                    seen[node.name] = ast.unparse(node).splitlines()[0]
                  
    for name in expected_functions :
        if not name in seen :
            ok = False
            Fail(f'Error: missing definition of function {name}')
        elif seen[name] != expected_functions[name] :
            ok = False
            Fail('Error: function definition has been modified:');
            Fail(f'\texpected: {expected_functions[name]}')
            Fail(f'\tfound:    {seen[name]}')
    return ok

def find_only_one(code_cells, name) :
    seen = None
    ok = True
    for src, AST in code_cells :    
        for node in ast.walk(AST) :
            if isinstance(node, ast.FunctionDef) :  
                if node.name == name :
                    first_line = ast.unparse(node).splitlines()[0]
                    if seen != None :
                        ok = False
                        Fail(f'Error: multiple definitions of function {name}')
                    else :
                        seen = src, node
                        if first_line != expected_functions[name] :
                            ok = False
                            Fail('Error: function definition has been modified:');
                            Fail(f'\texpected: {expected_functions[name]}')
                            Fail(f'\tfound:    {first_line}')
    if seen == None :
        ok = False
        Fail(f'Error: missing definition of function {name}')
    
    if ok :
        return seen
    else :
        return None, None

def test_imports_and_features(code_cells):
    ok = True
    for src, AST in code_cells :    
        for node in ast.walk(AST) :
            if isinstance(node, ast.Import) :
                for name in node.names :
                    if name.name not in ['math', 'code_analyser', 'matplotlib', 'numpy', 'numpy', 'floris', 'floris.layout_visualization'] :
                        ok = False
                        Fail(f'Error: not allowed to {ast.unparse(node)}')
                    if name.asname :
                        ok = False
                        Fail(f'Error: alias is not allowed when performing import: {ast.unparse(node)}')
            if isinstance(node, ast.ImportFrom) :
                ok = False
                Fail(f'Error: this style of import is not allowed: {ast.unparse(node)}')  
            if isinstance(node, ast.ListComp):
                ok = False
                Fail(f'Error: not allowed to use list comprehensions: {ast.unparse(node)}')
            if isinstance(node, ast.Match):
                ok = False
                Fail(f'Error: not allowed to use match statements: {ast.unparse(node)}')                
    return ok
    
def read_current_notebook() :
    token = os.environ["JUPYTERHUB_API_TOKEN"]    
    connection_file = Path(ipykernel.get_connection_file()).stem
    kernel_id = connection_file.split('-', 1)[1]
    with open('/tmp/.jupyter-runtime/jpserver-7.json', 'r') as file:
        session = json.load(file)
    root_dir = session['root_dir']
    url = session['url'] + 'api/sessions?token=' + token
    with urllib.request.urlopen(url, timeout=0.5) as req:
        sessions = json.load(req)
    for sess in sessions:
        if sess['kernel']['id'] == kernel_id:
            path = sess['path']
    ipynb_filename = root_dir + '/' + path  
    #print('Checking',  ipynb_filename)
    with open(ipynb_filename, encoding='utf-8') as file:
        return file.read()

def code_cells() :
    cells = []
    filesrc = read_current_notebook()
    for cell in json.loads(filesrc)['cells'] :
        if cell['cell_type'] == 'code' :
            codesrc = ''.join(cell['source'])
            try :
                cells.append((codesrc, ast.parse(codesrc)))
            except SyntaxError as e :
                pass
    
    return cells
    
def test_rules_and_restrictions() :
    cells = code_cells()
    if test_only_one_copy(cells) and test_imports_and_features(cells) :
        Pass('Pass') 
        return True
    else:
        return False
    
def test_equal(x, y) :
    if isinstance(x, float) :
        if math.isnan(x) :
            return math.isnan(y)
        else :
            return math.isclose(x, y, rel_tol = 1e-07, abs_tol = 1e-15)
    elif isinstance(x, list) or isinstance(x, tuple) :
        if len(x) != len(y) :
            return False
        for i in range(len(x)) :
            if not test_equal(x[i], y[i]) :
                return False
        return True
    else :
        return (x == y)  
    
test_results = { }


def Pass(msg) :
    print(termcolor.colored(msg,'green'))
    
def Fail(msg) :
    print(termcolor.colored(msg, 'red'))
    return False

def Heading(msg) :
    print(termcolor.colored(msg, attrs=['bold']))  

def assert_equal(actual, expected, test='') :
    print("Test " + test, end=": ")
    try :
        if test_equal(actual, expected) :
            test_results[test] = 'Pass'
            Pass('Pass')
        else :
            test_results[test] = 'Fail'
            Fail('Fail:')
            Fail(f'  expected result: {expected}')
            Fail(f'  actual result:   {actual}')
    except:
        test_results[test] = 'Fail'
        Fail('Failed due to exception')
        raise


def retrieve_nodes(AST, predicate, select = lambda  node : node) :
    nodes = [] 
    for node in ast.walk(AST) :
        if predicate(node) :
            nodes.append(select(node))
    return nodes

def is_range_loop_index(node) :
    return is_range_loop(node) and isinstance(node.target, ast.Name)

def is_function_call(node) :
    return isinstance(node, ast.Call) and node.func and isinstance(node.func, ast.Name)
    
def is_for_loop(node) :
    return isinstance(node, ast.For)

def is_while_loop(node) :
    return isinstance(node, ast.While)

def is_loop(node) :
    return is_for_loop(node) or is_while_loop(node)    
    
def is_range_loop(node) :
    return is_for_loop(node) and node.iter and isinstance(node.iter, ast.Call) and node.iter.func and isinstance(node.iter.func, ast.Name) and node.iter.func.id == 'range'

def is_foreach_loop(node) :
    return is_for_loop(node) and not is_range_loop(node)

def is_nested_range_loop(node) :   
    if is_range_loop(node) :
        for child in node.body :
            if exists_node(child, is_range_loop) :
                return True
    return False

def count_node(defn, predicate) :
    return len(retrieve_nodes(defn, predicate))

def exists_node(function, predicate) :
    return count_node(function, predicate) > 0

def no_loops(defn) :
    if count_node(defn, is_loop) :
        return Fail(f'No loops are need to implement function {defn.name}')
    else:
        return True

def implemented(defn):
    if len(defn.body) == 1 and isinstance(defn.body[0], ast.Return) and isinstance(defn.body[0].value, ast.Constant) and defn.body[0].value.value == None :
        return Fail(f'Function {defn.name} has not been implemented yet')
    return True

def single_loop(defn) :
    loops = retrieve_nodes(defn, is_loop)
    if len(loops) == 0:
        return Fail(f'Expected to use a loop to implement function {defn.name}')
    elif len(loops) > 1:
        return Fail(f'Don\'t need more than one loop to implement function {defn.name}')
    else :
        return loops[0]
        
def single_range_loop(defn):
    loop = single_loop(defn)
    if loop:
        if is_while_loop(loop) :
            return Fail(f'Using a while loop for function {defn.name} is unnecessary (use a simpler form of loop instead).')
        else :
            return True
        
def single_foreach_loop(defn):
    loop = single_loop(defn)
    if loop:
        if is_while_loop(loop) :
            return Fail(f'Using a while loop for function {defn.name} is unnecessary (use a simpler form of loop instead).')
        elif is_range_loop(loop) :
            return Fail(f'A range loop was not expected in function {defn.name}')
        else :
            return True     

def nested_range_loops(defn):
    loops = retrieve_nodes(defn, is_loop)
    if len(loops) < 2:
        return Fail(f'Need at least two loops to implement function {defn.name}')
    elif len(loops) > 4 :
        return Fail(f'You don\'t need more than 4 loops to implement function {defn.name}')
    else :
        for loop in loops :
            if is_while_loop(loop) :
                return Fail(f'Using a while loop for function {defn.name} is unnecessary (use a simpler form of loop instead).')
            elif is_foreach_loop(loop) :
                return Fail(f'Not expected to use a foreach loop for function {defn.name} (consider using range loop(s) instead).')
            elif is_nested_range_loop(loop) :
                return True
        return Fail(f'Need nested range loops for function {defn.name}')

def complex(AST, expected_complexity) :                
    for defn in radon.complexity.cc_visit(AST):
        if defn.complexity > expected_complexity :
            Fail(f'Function {defn.name} could be made less complex ({defn.complexity})')
            return True
    return False

def maintainable(src, name) :     
    score = radon.metrics.mi_visit(src,True)
    if score < 90 :
        Fail(f'Function {name} could be made more maintainable (score: {score:.0f}/100*)')
        return False
    else :
        return True

def identifiers(function) :  
    names = set(retrieve_nodes(function, lambda node: isinstance(node, ast.Name), lambda node : node.id))
    return names.difference(range_indexes(function))
    
def range_indexes(function) :
    return set(retrieve_nodes(function, is_range_loop_index, lambda loop : loop.target.id))


def uses_functions(function, call_list) :
    called = 0
    calls = retrieve_nodes(function, is_function_call, lambda call: call.func.id)
    names = retrieve_nodes(function, lambda node: isinstance(node, ast.Name), lambda node : node.id)
    for other_function in call_list :
        if other_function in calls or other_function in names :
            called += 1    
        else :
            Fail(f'Function {function.name} should make use of the {other_function} function')     
    return called

def follows_guidelines(name) :
    for ch  in name :
        if ch.isupper() :
            return False
    return True

def names_follow_guidelines(function) : 
    ok = True
    for name in identifiers(function) :
        if not follows_guidelines(name) :
            ok = False
            Fail(f"Variable name {name} doesn't follow Python naming conventions")
    return ok


def summarise_result(mark, out_of):
    global grand_total
    
    grand_total += mark
    if mark == out_of :
        Pass(f"Criteria fully satisfied ({mark} out of {out_of} marks)") 
    elif mark > 0:
        Fail(f'Criteria partically satisfied ({mark} out of {out_of} marks)')              
    else:
        Fail(f'Criteria not satisfied ({mark} out of {out_of} marks)')     

def function_use(code):
    correct = 0
    
    for src, AST in code :
        for defn in ast.walk(AST) :
            if isinstance(defn, ast.FunctionDef) and implemented(defn) :  
                match defn.name:
                    case 'rotate_layout':
                        correct += uses_functions(defn, ['rotate_single_location'])
                    case 'find_best_rotation':
                        correct += uses_functions(defn, ['rotate_layout', 'evaluate_turbine_layout'])
                    case 'greedy_optimize_yaw_angle_for_just_one_turbine':
                        correct += uses_functions(defn, ['evaluate_single_direction_with_yaws'])
                    case 'orderby_downwind':
                        correct += uses_functions(defn, ['distance_downwind', 'sort_turbines_by_distance_downwind'])
                    case 'optimize_all_yaw_angles':
                        correct += uses_functions(defn, ['zero_yaw', 'orderby_downwind', 'greedy_optimize_yaw_angle_for_just_one_turbine'])
    summarise_result(correct/3, 3)
        
def appropriate_loops(code):
    correct = 0
    for src, AST in code :
        for defn in ast.walk(AST) :
            if isinstance(defn, ast.FunctionDef) and implemented(defn) :  
                match defn.name:
                    case 'create_grid_layout' | 'create_hexagonal_layout':
                        if nested_range_loops(defn):
                            correct+=1
                    case 'rotate_single_location' | 'distance_downwind':
                        if no_loops(defn):
                            correct+=1
                    case 'rotate_layout' | 'orderby_downwind' | 'optimize_all_yaw_angles':
                        if single_foreach_loop(defn):
                            correct+=1
                    case 'find_best_rotation' | 'greedy_optimize_yaw_angle_for_just_one_turbine' :
                        if single_range_loop(defn):
                            correct+=1                
    if correct == 9:
        marks = 2
    elif correct >= 7:
        marks = 1.5
    elif correct >= 5:
        marks = 1
    elif correct >= 3:
        marks = 0.5
    else:
        marks = 0
    summarise_result(marks, 2)   

def test_maintainability(code):
    correct = 0
    for src, AST in code :
        for defn in ast.walk(AST) :
            if isinstance(defn, ast.FunctionDef) and defn.name in student_provided and implemented(defn) and maintainable(src, defn.name) :
                correct += 1
            
    if correct == 9:
        mark = 0.5
    elif correct > 4:
        mark = 0.25
    else:
        mark = 0
    summarise_result(mark, 0.5)       
        
def test_complexity(code):
    correct = 0
    for src, AST in code :
        for defn in ast.walk(AST) :
            if isinstance(defn, ast.FunctionDef) and implemented(defn):  
                match defn.name:
                    case 'rotate_single_location' | 'distance_downwind':
                        if not complex(defn, 1):
                            correct += 1
                    case 'orderby_downwind' | 'rotate_layout' | 'optimize_all_yaw_angles' :
                        if  not complex(defn, 2):
                            correct += 1
                    case 'create_grid_layout' | 'find_best_rotation' | 'greedy_optimize_yaw_angle_for_just_one_turbine' :
                        if not complex(defn, 3):
                            correct += 1
                    case 'create_hexagonal_layout':
                        if not complex(defn, 4):
                            correct += 1            
    if correct == 9:
        marks = 1.5
    elif correct >= 6:
        marks = 1.0
    elif correct >= 3:
        marks = 0.5
    else:
        marks = 0
    summarise_result(marks, 1.5)    

def test_non_functional_requirements_create_grid_layout():
    code = code_cells()
    src, defn = find_only_one(code, 'create_grid_layout')
    if all([defn, nested_range_loops(defn), maintainable(src, defn.name), not complex(defn, 3), names_follow_guidelines(defn), implemented(defn)]) :
        Pass('Pass')

def test_non_functional_requirements_create_hexagonal_layout():
    code = code_cells()
    src, defn = find_only_one(code, 'create_hexagonal_layout')
    if all([defn, nested_range_loops(defn), maintainable(src, defn.name), not complex(defn, 4), names_follow_guidelines(defn), implemented(defn)]) :
        Pass('Pass')
    
def test_non_functional_requirements_rotate_single_location():
    code = code_cells()
    src, defn = find_only_one(code, 'rotate_single_location')
    if all([defn and no_loops(defn), maintainable(src, defn.name), not complex(defn, 1), names_follow_guidelines(defn), implemented(defn)]) :
        Pass('Pass')
    
def test_non_functional_requirements_rotate_layout():
    code = code_cells()
    src, defn = find_only_one(code, 'rotate_layout')
    if all([defn, single_foreach_loop(defn), maintainable(src, defn.name), not complex(defn, 2), names_follow_guidelines(defn), uses_functions(defn, ['rotate_single_location']), implemented(defn)]) :
        Pass('Pass')
    
def test_non_functional_requirements_find_best_rotation():
    code = code_cells()
    src, defn = find_only_one(code, 'find_best_rotation')
    if all([defn, single_range_loop(defn), maintainable(src, defn.name), not complex(defn, 3), names_follow_guidelines(defn), uses_functions(defn, ['rotate_layout', 'evaluate_turbine_layout']), implemented(defn)]) :
        Pass('Pass')
    
def test_non_functional_requirements_greedy_optimize_yaw_angle_for_just_one_turbine():
    code = code_cells()
    src, defn = find_only_one(code, 'greedy_optimize_yaw_angle_for_just_one_turbine')
    if all([defn, single_range_loop(defn), maintainable(src, defn.name), not complex(defn, 3), names_follow_guidelines(defn), uses_functions(defn, ['evaluate_single_direction_with_yaws']), implemented(defn)]) :
        Pass('Pass')
    
def test_non_functional_requirements_distance_downwind():
    code = code_cells()
    src, defn = find_only_one(code, 'distance_downwind')
    if all([defn, no_loops(defn), maintainable(src, defn.name), not complex(defn, 1), names_follow_guidelines(defn), implemented(defn)]) :
        Pass('Pass')
    
def test_non_functional_requirements_orderby_downwind():
    code = code_cells()
    src, defn = find_only_one(code, 'orderby_downwind')
    if all([defn, single_foreach_loop(defn), maintainable(src, defn.name), not complex(defn, 2), names_follow_guidelines(defn), uses_functions(defn, ['distance_downwind', 'sort_turbines_by_distance_downwind']), implemented(defn)]) :
        Pass('Pass')
    
def test_non_functional_requirements_optimize_all_yaw_angles():
    code = code_cells()
    src, defn = find_only_one(code, 'optimize_all_yaw_angles')
    if all([defn, single_foreach_loop(defn), maintainable(src, defn.name), not complex(defn, 2), names_follow_guidelines(defn), uses_functions(defn, ['zero_yaw', 'orderby_downwind', 'greedy_optimize_yaw_angle_for_just_one_turbine']), implemented(defn)]):
        Pass('Pass')

def assignment_statement(function) :
    return exists_node(function, lambda node : isinstance(node, ast.Assign))

def if_statement(function) :
    return exists_node(function, lambda node : isinstance(node, ast.If))

def if_statements(code_cells):
    global grand_total
    for src,AST in code_cells:
        for defn in ast.walk(AST) :
            if isinstance(defn, ast.FunctionDef) and defn.name in student_provided and if_statement(defn) :
                print(defn.name)
                grand_total += 1
                Pass("Criteria fully satisfied (1 out of 1 marks)")
                return      
    Fail('No if statements found (0 out of 1 marks)')


def meaningful_names(code):
    for src,defn in code:    
        names_follow_guidelines(defn)
        
def assignment_statements(code) :
    global grand_total
    for src,AST in code :
        for defn in ast.walk(AST) :
            if isinstance(defn, ast.FunctionDef) and defn.name in student_provided and assignment_statement(defn) :
                grand_total += 1
                Pass(f"Criteria fully satisfied (1 out of 1 marks)")
                return   
    Fail(f'No assignment statements found (0 out of 1 marks)')

def list_method(function) :
      return exists_node(function, lambda node : isinstance(node, ast.Call) and node.func and isinstance(node.func, ast.Attribute) and node.func.attr and node.func.attr in dir([]))

def indexing(function) :
    return exists_node(function, lambda node : isinstance(node, ast.Subscript))
    
def list_indexing_and_methods(code) :
    global grand_total

    seen_indexing = seen_methods = False
    
    for src, AST in code :
        for defn in ast.walk(AST) :
            if isinstance(defn, ast.FunctionDef) and defn.name in student_provided :
                if list_method(defn):
                    seen_methods = True
                if indexing(defn):
                    seen_indexing = True

    if seen_indexing :
        if seen_methods :
            grand_total += 1.0
            Pass("Criteria fully satisfied (1 out of 1 marks)")
        else :
            grand_total += 0.5
            Fail('No list methods found (0.5 out of 1 marks)')  
    else :
        if seen_methods :
            grand_total += 0.5            
            Fail('No list indexing found (0.5 out of 1 marks)')
        else :
            Fail('No list indexing or methods found (0 out of 1 marks)')  


student_provided = ['create_grid_layout', 'create_hexagonal_layout', 'rotate_single_location', 'rotate_layout', 'find_best_rotation', 'greedy_optimize_yaw_angle_for_just_one_turbine', 'distance_downwind', 'orderby_downwind', 'optimize_all_yaw_angles'] 


def summarize_results(test_name, test_count, total_marks = 2) :
    global grand_total
    
    passes = 0
    fails = 0
    for test in test_results :
        if test.startswith(test_name) :
            if test_results[test] == 'Pass' :
                passes += 1
            else :
                fails += 1
    untested = test_count - passes - fails
    
    if untested > 0 :
        Fail("Some tests for this function have not be executed (or crashed), try again once they've been tested")
        
    fraction = passes / test_count             
    if fraction == 1 :
        marks = total_marks
        Pass(f'Passed all tests ({marks} out of {total_marks} marks)')
    elif fraction == 0 :
        marks = 0     
        Fail(f'Failed all tests ({marks} out of {total_marks} marks)')
    else :
        marks = int(fraction * total_marks * 2) / 2
        if fraction > 0 and marks == 0 :
            marks = 0.5
        Fail(f'Passed {passes} tests, but failed {fails} tests  ({marks} out of {total_marks} marks)')
    print()
                 
    grand_total += marks  


def summary_feedback():
    global grand_total
    code = code_cells()

    grand_total = 0
    
    Heading('Evaluation of your code with respect to assessment criteria ...')

    print() 
    Heading('Check Rules and Restrictions')      
    code = code_cells()
    if test_rules_and_restrictions():
        print()
        display(HTML('<hr>'))
        print()
        display(HTML('<h1>Part A (due week 3):</h1>'))
        print()
        
        Heading('Task 1: markdown to list your name and previous programming experience')   
        print('* This assessment criteria is marked manually by your tutors')
        print()
        
        Heading('Task 5: rotate_single_location function implemented correctly') 
        summarize_results('test3', 12, 1)
    
        Heading('Task 10: distance_downwind function implemented correctly') 
        summarize_results('test7', 12, 1)
    
        Heading(f'Sub Total (for Part A) = {grand_total} out of 2 (*the remaining 1 mark will be assessed manually by tutors)')
    
        print()
        display(HTML('<hr>'))    
        print()
        display(HTML('<h1>Part B (due week 6):</h1>'))
        
        print() 
        Heading('Assessment Criteria 1: Design and Implement simple algorithms and ensure software is correct (14 marks total)')      
        print()
    
        Heading('Assessment Criteria 1a: create_grid_layout function implemented correctly') 
        summarize_results('test1', 4)
        
        Heading('Assessment Criteria 1b: create_hexagonal_layout function implemented correctly') 
        summarize_results('test2', 4)
            
        Heading('Assessment Criteria 1c: rotate_layout function implemented correctly') 
        summarize_results('test4', 4)
        
        Heading('Assessment Criteria 1d: find_best_rotation function implemented correctly') 
        summarize_results('test5', 2)
        
        Heading('Assessment Criteria 1e: greedy_optimize_yaw_angle_for_just_one_turbine function implemented correctly') 
        summarize_results('test6', 4)
        
        Heading('Assessment Criteria 1f: orderby_downwind function implemented correctly') 
        summarize_results('test8', 6)
        
        Heading('Assessment Criteria 1g: optimize_all_yaw_angles function implemented correctly') 
        summarize_results('test9', 2)
        
        display(HTML('<hr>')) 
        Heading('Assessment Criteria 2: Learn a programming language and apply software development principles (9 marks total)')           
        print() 
        
        Heading('Assessment Criteria 2a: Use of if statements')
        if_statements(code)
        print()
        
        Heading('Assessment Criteria 2b: Use of lists and indexing')   
        list_indexing_and_methods(code)
        print()
        
        Heading('Assessment Criteria 2c: Appropriate use of loops')   
        appropriate_loops(code)
        print()
        
        Heading('Assessment Criteria 2d: Functions make use of other appropriate functions')   
        function_use(code)
        print()
        
        Heading('Assessment Criteria 2e: Use markdown cells to record your observations')   
        print('* This assessment criteria is marked manually by your tutors')
        print()
        
        Heading('Assessment Criteria 2f: Use of assignment statements')   
        assignment_statements(code)
        print()
        
        display(HTML('<hr>')) 
        Heading('Assessment Criteria 3: Ensure software is clear and maintainable (4 marks total)')     
        print() 
            
        Heading('Assessment Criteria 3a: Meaning variable names (2 marks)')   
        meaningful_names(code)
        print('* This assessment criteria is marked manually by your tutors')
        print()  
        
        Heading('Assessment Criteria 3b: Complexity of code')   
        test_complexity(code)
        print()   
        
        Heading('Assessment Criteria 3c: Maintainability of code')   
        test_maintainability(code)
        print()       
    
        display(HTML('<hr>'))     
        Heading(f'Grand Total = {grand_total} out of 26 (*the remaining 4 marks will be assessed manually by tutors)')
