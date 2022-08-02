# Do not modify this file!!!

import inspect
import ast
import math
import sys
import builtins

try :
  import radon.complexity
  import radon.metrics
except ModuleNotFoundError :
  pass
    
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
        print(function.__name__, "does not require any loops", file=sys.stderr)
    return total_loops == 0
    
def foreach_loop(function) :
    total_loops = count_node(function, is_loop)
    if total_loops < 1 :
        print(function.__name__, "needs a loop", file=sys.stderr)    
    if total_loops > 1 :
        print(function.__name__, "does not require that many loops", file=sys.stderr)
    if exists_node(function, is_range_loop) or exists_node(function, is_while_loop) :
        print(function.__name__, "does not require such a complex form of loop", file=sys.stderr)
    return total_loops == 1 and exists_node(function,  is_foreach_loop)

def optional_foreach_loop(function) :
    total_loops = count_node(function, is_loop)
    if total_loops > 1 :
        print(function.__name__, "does not require that many loops", file=sys.stderr)
    if exists_node(function, is_range_loop) or exists_node(function, is_while_loop) :
        print(function.__name__, "does not require such a complex form of loop", file=sys.stderr)      
    return total_loops <= 1 and count_node(function, is_foreach_loop) <= 1 

def range_loop(function) :
    total_loops = count_node(function, is_loop)
    if total_loops < 1 :
        print(function.__name__, "needs a loop", file=sys.stderr)
    if total_loops > 1 :
        print(function.__name__, "does not require that many loops", file=sys.stderr)
    if exists_node(function, is_while_loop) :
        print(function.__name__, "does not require such a complex form of loop", file=sys.stderr)
    return total_loops == 1 and exists_node(function, is_range_loop) 

def appropriate_loop(function) :
    name = function.__name__
    if name == 'calculate_refrigeration' or name == 'calculate_coefficient_of_performance' or name == 'compute_performance_curve' :
        return no_loops(function)
    elif name == 'compute_coefficient_of_performance_vs_refrigeration' or name == 'group_into_bins' or name == 'compute_bin_averages' :
        return foreach_loop(function)
    elif name == 'create_empty_bins' :
        return range_loop(function)
    elif name == 'mean' :
        return optional_foreach_loop(function)

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
        print(function.__name__, 'does not use appropriate other functions', file=sys.stderr)
    return called
    
def use(function) :
    name = function.__name__
    if name == 'compute_coefficient_of_performance_vs_refrigeration' :
        return uses(function, ['calculate_refrigeration', 'calculate_coefficient_of_performance'])
    elif name == 'group_into_bins' :
        return uses(function, ['calculate_number_of_bins', 'create_empty_bins', 'calculate_bin_number'])
    elif name == 'compute_bin_averages' :
        return uses(function, ['mean'])        
    elif name == 'compute_performance_curve' :
        return uses(function, ['compute_coefficient_of_performance_vs_refrigeration', 'group_into_bins', 'compute_bin_averages'])  
    else :
        return 0

def identifiers(function) :  
    names = set(retrieve_nodes(function, lambda node: isinstance(node, ast.Name), lambda node : node.id))
    return names.difference(range_indexes(function))

def range_indexes(function) :
    return set(retrieve_nodes(function, is_range_loop_index, lambda loop : loop.target.id))

def expected_complexity(function) :
    name = function.__name__
    if name == 'calculate_refrigeration' or name == 'calculate_coefficient_of_performance' :
        return 1
    else :
        return 2

def complexity(function) :
    if function :
        src = inspect.getsource(function)
        AST = ast.parse(src)    
        for defn in radon.complexity.cc_visit(AST):
            if defn.complexity > expected_complexity(function) :
                print(function.__name__, 'could be made less complex', file=sys.stderr)
                return False
        return True
    else :
        return False

def maintainability(function) :
    if function :
        src = inspect.getsource(function)
        if radon.metrics.mi_visit(src,True) < 100 :
             print(function.__name__, 'could be made more maintainable', file=sys.stderr)
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
        
def appropriate_loops() :  
    correct = 0
    for function in functions :
        if appropriate_loop(function) :
            correct += 1
    if correct == 8 :
        print("Use of appropriate loops: Criteria fully satisfied, well done!")
    else :
        print("Use of appropriate loops: Failed to fully satisfy criteria", file=sys.stderr)
        print(correct / 4, ' out of 2 marks', file=sys.stderr) 

def if_statements() :
    for function in functions :
        if if_statement(function) :
            print("Use of if statements: Criteria fully satisfied, well done!")
            return      
    print('Use of if statements: Failed to satisfy criteria (no if statements found)', file=sys.stderr) 
    print('0 marks', file=sys.stderr)    

def assignment_statements() :
    for function in functions :
        if assignment_statement(function) :
            print("Use of assignment statements: Criteria fully satisfied, well done!")
            return   
    print('Use of assignment statements: Failed to satisfy criteria (no assignment statements found)', file=sys.stderr)
    print('0 marks', file=sys.stderr)

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
    
def list_indexing_and_methods() :
    if list_indexing() :
        if list_methods() :
            print("Use of list indexing and methods: Criteria fully satisfied, well done!")
        else :
            print('Use of list indexing: Failed to fully satisfy criteria (no list methods found)', file=sys.stderr)  
            print('0.5 marks', file=sys.stderr) 
    else :
        if list_methods() :
            print('Use of list indexing: Failed to fully satisfy criteria (no list indexing found)', file=sys.stderr)
            print('0.5 marks', file=sys.stderr) 
        else :
            print('Use of list indexing: Failed to fully satisfy criteria (no list indexing or methods found)', file=sys.stderr)  
            print('0 marks', file=sys.stderr)

def function_use() :
    calls = 0
    for function in functions :
        calls += use(function)      
    if calls > 0 :
        calls -= 1
    if calls == 8 :
        print("Use of appropriate functions: Criteria fully satisfied, well done!")
    else :
        print("Use of appropriate functions: Failed to fully satisfy criteria", file=sys.stderr)    
        print(calls / 4, 'marks', file=sys.stderr)

def follows_guidelines(name) :
    for ch  in name :
        if ch.isupper() :
            return False
    return True

def meaningful_names() : 
    names = set()
    for function in functions :
        names.update(identifiers(function)) 
    exclude = ['calculate_refrigeration', 'enter_temperature', 'leave_temperature', 'flow_rate', 'calculate_coefficient_of_performance', 'kilowatts_of_refrigeration', 'kilowatts_of_electricity', 'compute_coefficient_of_performance_vs_refrigeration', 'historical_data', 'create_empty_bins', 'number_of_bins', 'group_into_bins', 'xy_pairs', 'bin_size', 'mean', 'list_of_numbers', 'compute_bin_averages', 'bins', 'compute_performance_curve', 'historical_data', 'bin_size', 'calculate_bin_number', 'calculate_number_of_bins'] 
    exclude.extend(dir(builtins))
    unique = names.difference(set(exclude))
    for name in unique :
        if not follows_guidelines(name) :
            print('Variable name', name, "doesn't follow Python naming conventions", file=sys.stderr)
            return
    print('Is it entirely clear what each of the following variable names means?')
    print(', '.join(sorted(unique)))
    
def range_loop_indexes() : 
    names = set()
    for function in functions :
         names.update(range_indexes(function))  
    for name in names :
        if not follows_guidelines(name) :
            print('Variable name', name, "doesn't follow Python naming conventions", file=sys.stderr)
            return        
    print('Index variables used in range loops:', ', '.join(sorted(set(names))))

def test_complexity() :
    try :
        good = 0
        for function in functions :
            if complexity(function) and maintainability(function) :
                good += 1

        if good == 8 :
            print('Clear and simple functions: Criteria fully satisfied, well done!')
        else :
            print('Clear and simple functions: Failed to fully satisfy criteria', file=sys.stderr)
            print(good / 4, 'out of 2 marks', file=sys.stderr)
    except NameError :
        print('Need to install radon module in order to assess code complexity and maintainability', file=sys.stderr)
        
epsilon = 1e-10

def assert_equal(x, y, error = epsilon) :
    if isinstance(x, float) :
        if math.isnan(x) :
            return math.isnan(y)
        else :
            assert(abs(x-y) <= error)
    elif isinstance(x, list) or isinstance(x, tuple) :
        assert(len(x) == len(y))
        for i in range(len(x)) :
            assert_equal(x[i], y[i])
    else :
        if x != y :
            print(type(x), type(y))
            print(x, y)
        assert(x == y)