# Do not modify this file!!!

import inspect
import ast
import math
import sys
import builtins
import termcolor  
import anastruct

grand_total = 0

rel_tol = 1e-07

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
    if name == 'warren_truss_top_left_vertex' or name == 'position_warren_truss_vertices' or name == 'position_howe_truss_vertices' or name == 'build_bridge' :
        return no_loops(function)
    elif name == 'evenly_spaced_horizontal_vertices' :
        return range_loop(function)    
    elif name == 'connect_warren_truss_vertices' or name == 'connect_howe_truss_vertices' :
        return range_loops(function)
    else :
        return False

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
    
    names = retrieve_nodes(function, lambda node: isinstance(node, ast.Name), lambda node : node.id)
    
    for other_function in call_list :
        if other_function in calls or other_function in names :
            called += 1    
    if len(call_list) != called :
        Fail(function.__name__ + ' does not use appropriate other functions')
    return called
    
def use(function) :
    name = function.__name__
    if name == 'position_warren_truss_vertices' :
        return uses(function, ['evenly_spaced_horizontal_vertices', 'warren_truss_top_left_vertex'])
    elif name == 'position_howe_truss_vertices' :
        return uses(function, ['evenly_spaced_horizontal_vertices', 'howe_truss_top_left_vertex'])        
    elif name == 'build_bridge' :
        return uses(function, ['build_warren_truss', 'build_howe_truss', 'add_supports', 'apply_loads'])             
    else :
        return 0

def identifiers(function) :  
    names = set(retrieve_nodes(function, lambda node: isinstance(node, ast.Name), lambda node : node.id))
    return names.difference(range_indexes(function))

def range_indexes(function) :
    return set(retrieve_nodes(function, is_range_loop_index, lambda loop : loop.target.id))


def expected_complexity(function) :
    name = function.__name__
    if name == 'warren_truss_top_left_vertex' or name == 'position_warren_truss_vertices' or name == 'position_howe_truss_vertices' :
        return 1
    elif name == 'evenly_spaced_horizontal_vertices' :
        return 2
    elif name == 'connect_warren_truss_vertices' or name == 'build_bridge' :
        return 3
    elif name == 'connect_howe_truss_vertices' :
        return 6
    else :
        return 0

def complexity(function) :
    if function :
        src = inspect.getsource(function)
        AST = ast.parse(src)    
        
        defns = retrieve_nodes(function, lambda node : isinstance(node, ast.FunctionDef) and node.name ==function.__name__, lambda defn : defn.body)
        if len(defns) == 1 and len(defns[0]) == 1  and isinstance(defns[0][0], ast.Pass) :
            Fail(function.__name__ + f' has not been implemented')
            return False
        
        for defn in radon.complexity.cc_visit(AST):
            if defn.complexity > expected_complexity(function) :
                Fail(function.__name__ + f' could be made less complex ({defn.complexity})')
                return False
        return True
    else :
        return False

def maintainability(function) :
    if function :
        src = inspect.getsource(function)
        
        defns = retrieve_nodes(function, lambda node : isinstance(node, ast.FunctionDef) and node.name ==function.__name__, lambda defn : defn.body)
        if len(defns) == 1 and len(defns[0]) == 1  and isinstance(defns[0][0], ast.Pass) :
            Fail(function.__name__ + f' has not been implemented')
            return False        
        
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
    if calls == 8 :
        grand_total += total_marks
        Pass(f"Criteria fully satisfied ({total_marks} out of {total_marks} marks)")
    else :
        mark = total_marks * (calls/8)
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
    exclude = ['anastruct', 'math', 'add_supports','apply_loads','bottom_vertices','bridge','build_bridge','build_howe_truss','build_warren_truss','connect_howe_truss_vertices','connect_warren_truss_vertices','evenly_spaced_horizontal_vertices','horizontal_gap_between_vertices','horizontal_segment_length','horizontal_span_length','howe_truss_top_left_vertex','leftmost_vertex','number_of_segments','number_of_vertices','position_howe_truss_vertices','position_warren_truss_vertices','top_vertices','truss_design','warren_truss_top_left_vertex','weight_per_metre']
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
            return math.isclose(x, y, rel_tol = rel_tol)
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
        
        

        
def inspect_bridge(actual_bridge, actual_bottom_elements, expected_vertices, expected_edges, test_name) :
           
    print("Test " + test_name, end=": ")
    try :
        close_enough = 1e-6 

        def is_close(coord1, coord2):
            x1,y1 = coord1
            x2,y2 = coord2
            return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2) < close_enough

        def closest_node(coord):
            for (id,node) in actual_bridge.node_map.items() :
                if is_close(coord, (node.vertex.x, node.vertex.y)) :
                    return id
            return None

        def find_edge(src_node_id, dst_node_id) :
            for id,element in actual_bridge.element_map.items() :  
                if (element.node_id1 == src_node_id and element.node_id2 == dst_node_id) or (element.node_id1 == dst_node_id and element.node_id2 == src_node_id) :
                    return True
            return False

        def find_vertex(vertex) :
            for i in range(len(expected_vertices)) :
                if is_close(expected_vertices[i], (vertex.x, vertex.y)) :
                    return i
            return None
        
        correct = True
        
        if isinstance(actual_bridge, anastruct.SystemElements) :
            
            if len(actual_bridge.element_map) > 0 :
                actual_bridge.show_structure()

                vertex_map = {}
                for i in range(len(expected_vertices)) :
                    vertex_map[i] = closest_node(expected_vertices[i])

                for (src,dst) in expected_edges :
                    if not find_edge(vertex_map[src], vertex_map[dst]) :
                        correct = False
                        Fail(f'Fail: Missing edge from {expected_vertices[src]} to {expected_vertices[dst]}')

                if len(actual_bridge.element_map) > len(expected_edges) :
                    for id,element in actual_bridge.element_map.items() :
                        v1 = find_vertex(element.vertex_1)
                        v2 = find_vertex(element.vertex_2)
                        if not ((v1,v2) in expected_edges or (v2,v1) in expected_edges) :
                            correct = False
                            Fail(f'Fail: Extra unexpected edge from {element.vertex_1} to {element.vertex_2}') 

                if actual_bottom_elements :
                    for element_id in actual_bottom_elements :
                        if element_id in actual_bridge.element_map :
                            element = actual_bridge.element_map[element_id]
                            if element.vertex_1.y != 0 or element.vertex_2.y != 0 :
                                correct = False
                                Fail(f'Fail: Element from {element.vertex_1} to {element.vertex_2} should not be returned in the list of bottom elements')
                        else :
                            Fail(f'Fail: Returned bottom element id {element_id} is not contained in the bridge model')

                    for (id,element) in actual_bridge.element_map.items() :
                        if element.vertex_1.y == 0 and element.vertex_2.y == 0 and not id in actual_bottom_elements :
                            correct = False
                            Fail(f'Fail: Element {id} should be returned in the list of bottom elements')
                else :
                    total_load = 0
                    for (id,element) in actual_bridge.element_map.items() :
                        if (element.vertex_1.y != 0 or element.vertex_2.y != 0) and element.q_load[0] != 0 :
                            correct = False
                            Fail(f'Fail: Load should not applied to non bottom element from {element.vertex_1} to {element.vertex_2}')

                        if element.vertex_1.y == 0 and element.vertex_2.y == 0 :
                            total_load += element.q_load[0]
                            if element.q_load[0] == 0 :
                                correct = False
                                Fail(f'Fail: Load has not been applied to bottom element from {element.vertex_1} to {element.vertex_2}')

                    span = max(actual_bridge.nodes_range('x'))
                    if not test_equal(total_load, span * 115) :
                        correct = False
                        Fail(f'Fail: Incorrect total distributed load: expected {span*115}, actual {total_load}')                

                    if len(actual_bridge.supports_fixed) == 0 :
                        correct = False
                        Fail('Fail: Fixed support has not been added')
                    elif len(actual_bridge.supports_fixed) > 1 :
                        correct = False
                        Fail('Fail: There should be only one fixed support (and one roll support)')

                    if len(actual_bridge.supports_roll) == 0 :
                        correct = False
                        Fail('Fail: Roll support has not been added')
                    elif len(actual_bridge.supports_roll) > 1 :
                        correct = False
                        Fail('Fail: There should be only one roll support (and one fixed support)')
            else :
                correct = False
                Fail('Fail: Bridge contains no elements')
        else :
            correct = False
            Fail(f'Fail: Expected an anastruct.SystemElements object but got {actual_bridge}')

        if correct :
            test_results[test_name] = 'Pass'
            Pass('Pass')
        else :
            test_results[test_name] = 'Fail'
    except:
        test_results[test_name] = 'Fail'
        Fail('Failed due to exception')
        raise
        
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
    possible = 26

    Heading('Evaulation of your code with respect to assessment criteria:')

    print() 
    Heading('Assessment Criteria 1: Design and Implement simple algorithms and ensure software is correct (13 marks total)')      
    print() 
    
    Heading('Assessment Criteria 1a: warren_truss_top_left_vertex function implemented correctly') 
    summarize_results('a', 4, 1)
    
    Heading('Assessment Criteria 1b: evenly_spaced_horizontal_vertices function implemented correctly') 
    summarize_results('b', 4)
        
    Heading('Assessment Criteria 1c: position_warren_truss_vertices function implemented correctly') 
    summarize_results('c', 6)
    
    Heading('Assessment Criteria 1d: connect_warren_truss_vertices function implemented correctly') 
    summarize_results('d', 20)
    
    Heading('Assessment Criteria 1e: position_howe_truss_vertices function implemented correctly') 
    summarize_results('e', 6)
    
    Heading('Assessment Criteria 1f: connect_howe_truss_vertices function implemented correctly') 
    summarize_results('f', 8)
    
    Heading('Assessment Criteria 1g: build_bridge function implemented correctly') 
    summarize_results('g', 16)       
   
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
    appropriate_loops(3)
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