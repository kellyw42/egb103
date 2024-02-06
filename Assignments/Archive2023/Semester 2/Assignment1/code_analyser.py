# Do not modify this file!!!

import inspect
import ast
import math
import sys
import builtins
import termcolor  

grand_total = 0

try :
  import radon.complexity
  import radon.metrics
except ModuleNotFoundError :
  pass

def Pass(msg) :
    print(termcolor.colored(msg,'green'))
    
def Fail(msg) :
    print(termcolor.colored(msg, 'red'))
    
def Heading(msg) :
    print(termcolor.colored(msg, attrs=['bold']))    
    
def retrieve_nodes(function, predicate, select = lambda  node : node) :
    nodes = []
    if function :
        src = inspect.getsource(function)
        AST = ast.parse(src)       
        count = 0
        for node in ast.walk(AST) :
            if predicate(node) :
                nodes.append(select(node))
    return nodes

def count_node(function, predicate) :
    return len(retrieve_nodes(function, predicate))

def exists_node(function, predicate) :
    return count_node(function, predicate) > 0
  
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

def is_range_loop_index(node) :
    return is_range_loop(node) and isinstance(node.target, ast.Name)

def is_foreach_loop(node) :
    return is_for_loop(node) and not is_range_loop(node)    
    
def no_loops(function) :
    total_loops = count_node(function, is_loop)
    if total_loops > 0 :
        Fail(function.__name__ + " does not require any loops")
    return total_loops == 0
    
def foreach_loop(function) :
    total_loops = count_node(function, is_loop)
    if total_loops < 1 :
        Fail(function.__name__ + " needs a loop")    
    if total_loops > 1 :
        Fail(function.__name__ + " does not require that many loops")
    if exists_node(function, is_range_loop) or exists_node(function, is_while_loop) :
        Fail(function.__name__ + " does not require such a complex form of loop")
    return total_loops == 1 and exists_node(function,  is_foreach_loop)

def range_loop(function) :
    total_loops = count_node(function, is_loop)
    if total_loops < 1 :
        Fail(function.__name__ + " needs a loop")
    if total_loops > 1 :
        Fail(function.__name__ + " does not require that many loops")
    if exists_node(function, is_while_loop) :
        Fail(function.__name__ + " does not require such a complex form of loop")
    return total_loops >= 1 and exists_node(function, is_range_loop)

def range_loops(function) :
    total_loops = count_node(function, is_loop)
    if total_loops < 1 :
        Fail(function.__name__ + " needs a loop")
        return False
    if total_loops > 3 :
        Fail(function.__name__ + " does not require that many loops")
        return False
    if exists_node(function, is_while_loop) :
        Fail(function.__name__ + " does not require such a complex form of loop")
        return False
    if exists_node(function, is_range_loop) :
        return True
    else :
        Fail(function.__name__ + " needs a range loop")
        return False

def appropriate_loop(function) :
    name = function.__name__
    if name == 'compute_fuel_used' or name == 'tyre_grip' or name == 'compute_lap_time' :
        return no_loops(function)
    elif name == 'compute_strategy_time'or name == 'find_best_one_stop_strategy' :
        return foreach_loop(function)
    elif name == 'compute_stint_time' :
        return range_loop(function)    
    elif name == 'enumerate_one_stop_strategies' :
        return range_loops(function)

def if_statement(function) :
    return exists_node(function, lambda node : isinstance(node, ast.If))

def assignment_statement(function) :
    return exists_node(function, lambda node : isinstance(node, ast.Assign))

def list_method(function) :
      return exists_node(function, lambda node : isinstance(node, ast.Call) and node.func and isinstance(node.func, ast.Attribute) and node.func.attr and node.func.attr in dir([]))

def indexing(function) :
    return exists_node(function, lambda node : isinstance(node, ast.Subscript))
    
def uses(function, call_list) :
    called = 0
    calls = retrieve_nodes(function, is_function_call, lambda call: call.func.id)
    for other_function in call_list :
        if other_function in calls :
            called += 1    
    if len(call_list) != called :
        Fail(function.__name__ + ' does not use appropriate other functions')
    return called
    
def use(function) :
    name = function.__name__
    if name == 'compute_lap_time' :
        return uses(function, ['tyre_grip'])
    elif name == 'compute_stint_time' :
        return uses(function, ['compute_lap_time', 'compute_fuel_used'])        
    elif name == 'compute_strategy_time' :
        return uses(function, ['compute_stint_time'])        
    elif name == 'find_best_one_stop_strategy' :
        return uses(function, ['enumerate_one_stop_strategies', 'compute_strategy_time'])       
    else :
        return 0

def identifiers(function) :  
    names = set(retrieve_nodes(function, lambda node: isinstance(node, ast.Name), lambda node : node.id))
    return names.difference(range_indexes(function))

def range_indexes(function) :
    return set(retrieve_nodes(function, is_range_loop_index, lambda loop : loop.target.id))


def expected_complexity(function) :
    name = function.__name__
    if name == 'compute_fuel_used' or name == 'tyre_grip' or name == 'compute_lap_time' :
        return 1
    elif name == 'compute_stint_time' or name == 'compute_strategy_time' :
        return 2
    elif name == 'find_best_one_stop_strategy' :
        return 3
    elif name == 'enumerate_one_stop_strategies' :
        return 5
    else :
        return 0

def complexity(function) :
    if function :
        src = inspect.getsource(function)
        AST = ast.parse(src)    
        for defn in radon.complexity.cc_visit(AST):
            if defn.complexity > expected_complexity(function) :
                Fail(function.__name__ + ' could be made less complex')
                return False
        return True
    else :
        return False

def maintainability(function) :
    if function :
        src = inspect.getsource(function)
        score = radon.metrics.mi_visit(src,True)
        if score < 80 :
             Fail(f'  Perhaps {function.__name__} could be made more maintainable (score: {score:.0f}/100*)')
             return False
        else :
            return True
    else :
        return False
    
def clear() :
    global functions
    functions = []
    
def register(input) :
    global functions
    if not input in functions :
        functions.append(input)
        
def appropriate_loops(total_marks) :  
    global grand_total
    correct = 0
    for function in functions :
        if appropriate_loop(function) :
            correct += 1
    if correct == 7 :
        grand_total += total_marks
        Pass(f"Criteria fully satisfied ({total_marks} out of {total_marks} marks)")
    else :
        wrong = 7 - correct
        mark = total_marks - wrong
        if mark < 0 :
            mark = 0
        grand_total += mark
        Fail(f"Failed to fully satisfy criteria ({mark} out of {total_marks} marks)") 

def if_statements(marks) :
    global grand_total    
    for function in functions :
        if if_statement(function) :
            grand_total += marks
            Pass("Criteria fully satisfied (1 out of 1 marks)")
            return      
    Fail('No if statements found (0 out of 1 marks)')
    
def assignment_statements(total_marks) :
    global grand_total
    for function in functions :
        if assignment_statement(function) :
            grand_total += total_marks
            Pass(f"Criteria fully satisfied ({total_marks} out of {total_marks} marks)")
            return   
    Fail(f'No assignment statements found (0 out of {total_marks} marks)')

def list_methods() :
    for function in functions :
        if list_method(function) :
            return True           
    return False

def list_indexing() :
    for function in functions :
        if indexing(function) :
            return True         
    return False
    
def list_indexing_and_methods(marks) :
    global grand_total
    if list_indexing() :
        if list_methods() :
            grand_total += 1.0
            Pass("Criteria fully satisfied (1 out of 1 marks)")
        else :
            grand_total += 0.5
            Fail('No list methods found (0.5 out of 1 marks)')  
    else :
        if list_methods() :
            grand_total += 0.5            
            Fail('No list indexing found (0.5 out of 1 marks)')
        else :
            Fail('No list indexing or methods found (0 out of 1 marks)')  

def function_use(total_marks) :
    global grand_total
    calls = 0
    for function in functions :
        calls += use(function)   
    if calls == 6 :
        grand_total += total_marks
        Pass(f"Criteria fully satisfied ({total_marks} out of {total_marks} marks)")
    else :
        mark = total_marks * (calls/6)
        mark = int(mark * 2) / 2
        if calls > 0 and mark == 0 :
            mark = 0.5
        grand_total += mark
        Fail(f"Failed to fully satisfy criteria ({mark} out of {total_marks} marks)")

def follows_guidelines(name) :
    for ch  in name :
        if ch.isupper() :
            return False
    return True

def meaningful_names() : 
    names = set()
    for function in functions :
        names.update(identifiers(function)) 
    exclude = ['abrasion','assert_equal','assess_criteria','bahrain','baku','C0','C1','C2','C3','C4','C5','code_analyser','compute_fuel_used','compute_lap_time','compute_stint_time','compute_strategy_time','distance','distance_travelled','enumerate_one_stop_strategies','find_best_one_stop_strategy','fuel_load','hard','initial_fuel_load','jeddah','lap_distance','lap_time','laps','medium','melbourne','miami','monaco','monza','pit_stop_time','silverstone','soft','speed','stint_laps','strategy','track_abrasion','track_data','tyre_data','tyre_grip','tyre_name','tyre_option_names']
    exclude.extend(dir(builtins))
    unique = names.difference(set(exclude))
    for name in unique :
        if not follows_guidelines(name) :
            Fail(f"Variable name {name} doesn't follow Python naming conventions")
            return
    print('Is it entirely clear what each of the following variable names means?')
    print('    ' + ', '.join(sorted(unique)))
    
def range_loop_indexes() : 
    names = set()
    for function in functions :
         names.update(range_indexes(function))  
    for name in names :
        if not follows_guidelines(name) :
            Fail(f"Variable name {name} doesn't follow Python naming conventions")
            return        
    print('Index variables used in range loops:', ', '.join(sorted(set(names))))

def test_complexity(total_marks) :
    global grand_total
    try :
        good1 = 0
        for function in functions :
            if complexity(function) :
                good1 += 1

        if good1 == 7 :
            grand_total += total_marks
            Pass(f'All functions are as simple as possible ({total_marks} out of {total_marks} marks)')
        elif good1 > 3 :
            mark = int(total_marks * (good1/7) * 2) / 2
            grand_total += mark
            Fail(f'Criteria not fully satisfied ({mark} out of {total_marks} marks)')
        else :
            Fail(f'Criteria not satified (0 out of {total_marks} marks)')
    except NameError :
        Fail('Need to install radon module in order to assess code complexity and maintainability')            
        
def test_maintainability(total_marks) :
    global grand_total
    global possible
    good2 = 0
    for function in functions :
        if maintainability(function) :
            good2 += 1
                
    if good2 == 7 :
        grand_total += total_marks
        Pass(f'All functions are maintainable ({total_marks} out of {total_marks} marks)')          
    else :
        possible -= 1
        Fail('* Please note that these automatically generated maintainability metrics are not entirely reliable (and will we reassessed by a tutor)')
              
        
def test_equal(x, y) :
    if isinstance(x, float) :
        if math.isnan(x) :
            return math.isnan(y)
        else :
            return math.isclose(x, y)
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
    
def assert_equal(actual, expected, test='test') :
    global test_results
    if test_equal(actual, expected) :
        test_results[test] = 'Pass'
        Pass('Pass')
    else :
        test_results[test] = 'Fail'
        Fail('Fail:')
        Fail(f'  expected result: {expected}')
        Fail(f'  actual result:   {actual}')
        
def summarize_results(test_name, test_count, total_marks = 1) :
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
        marks = 0
        Fail("Some tests for this function have not be executed, try again once they've been tested")
    else :
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
          
def assess_criteria(list) :
    global grand_total   
    global functions
    global possible
    functions = list

    grand_total = 0  
    possible = 27

    Heading('Evaulation of your code with respect to assessment criteria:')

    print() 
    Heading('Assessment Criteria 1: Design and Implement simple algorithms and ensure software is correct (13 marks total)')      
    print() 
    
    Heading('Assessment Criteria 1a: compute_fuel_used function implemented correctly') 
    summarize_results('testa', 10)
    
    Heading('Assessment Criteria 1b: tyre_grip function implemented correctly') 
    summarize_results('testb', 14)
        
    Heading('Assessment Criteria 1c: compute_lap_time function implemented correctly') 
    summarize_results('testc', 13)
    
    Heading('Assessment Criteria 1d: compute_stint_time function implemented correctly') 
    summarize_results('testd', 8, 2)
    
    Heading('Assessment Criteria 1e: enumerate_one_stop_strategies function implemented correctly') 
    summarize_results('teste', 3, 3)
    
    Heading('Assessment Criteria 1f: compute_strategy_time function implemented correctly') 
    summarize_results('testf', 15, 2)
    
    Heading('Assessment Criteria 1g: find_best_one_stop_strategy function implemented correctly') 
    summarize_results('testg', 8, 3)       
   
    print() 
    Heading('Assessment Criteria 2: Learn a programming language and apply software development principles (12 marks total)')           
    print() 
    
    Heading('Assessment Criteria 2a: Use of if statements')
    if_statements(1)
    print()
    
    Heading('Assessment Criteria 2b: Use of lists and indexing')   
    list_indexing_and_methods(1)
    print()
    
    Heading('Assessment Criteria 2c: Appropriate use of loops')   
    appropriate_loops(4)
    print()
    
    Heading('Assessment Criteria 2d: Functions make use of other appropriate functions')   
    function_use(4)
    print()
    
    Heading('Assessment Criteria 2e: Use markdown cells to record your identity and observations')   
    print('* This assessment criteria is marked manually by your tutors')
    print()
    
    Heading('Assessment Criteria 2f: Use of assignment statements')   
    assignment_statements(1)
    print()
    
    print() 
    Heading('Assessment Criteria 3: Ensure software is clear and maintainable (5 marks total)')     
    print() 
        
    Heading('Assessment Criteria 3a: Meaning variable names (2 marks)')   
    meaningful_names()
    range_loop_indexes()
    print('* This assessment criteria is marked manually by your tutors')
    print()  
    
    Heading('Assessment Criteria 3b: Complexity of code')   
    test_complexity(2)
    print()   
    
    Heading('Assessment Criteria 3c: Maintainability of code (1 mark)')   
    test_maintainability(1)
    print()       
                 
    Heading(f'Grand Total = {grand_total} out of {possible} (*the remaining {30-possible} marks will be assessed manually by tutors)')