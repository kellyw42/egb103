# Do not modify this file!!!

import builtins
import inspect
import ast
import json
import math
import radon.complexity
import radon.metrics
import termcolor  
from IPython.display import display, HTML

# This section depends on the specific assignment task ...

def expected_complexity(function_name) :
    match function_name :
        case 'vector_sum' | 'induced_drag_magnitude' | 'simulate_multiple_time_steps' | 'update_engine_rpm' :
            return 2
        case _ :
            return 1

def expected_calls(function_name):
    match function_name :
        case 'magnitude_of_lift': 
            return 'angle_to_relative_airflow_radians', 'airspeed', 'compute_lift_coefficient', 'air_density',
        case 'induced_drag_force':
            return 'angle_to_relative_airflow_radians', 'induced_drag_magnitude', 'vector_from_magnitude_and_angle',
        case 'lift_force':
            return 'angle_to_relative_airflow_radians', 'vector_from_magnitude_and_angle',
        case 'linear_acceleration':
            return 'scale_vector', 'net_force',    
        case 'angular_acceleration':
            return 'net_moment',
        case 'air_density':
            return 'air_density_at',
        case 'airspeed':
            return 'vector_magnitude',
        case 'propeller_radians_per_second': 
            return 'propeller_rpm',
        case 'advance_ratio': 
            return 'airspeed', 'propeller_rpm',
        case 'propeller_torque_load': 
            return 'propeller_torque_coefficient', 'advance_ratio', 'air_density', 'propeller_radians_per_second',
        case 'engine_torque_load': 
            return 'propeller_torque_load',
        case 'engine_torque_generated': 
            return 'engine_torque',
        case 'net_engine_torque': 
            return 'engine_torque_generated', 'engine_torque_load',
        case 'engine_angular_acceleration': 
            return 'net_engine_torque',
        case 'update_engine_rpm': 
            return 'engine_angular_acceleration',
        case 'engine_thrust_force': 
            return 'propeller_thrust_coefficient', 'air_density', 'propeller_radians_per_second', 'vector_from_magnitude_and_angle', 'advance_ratio',
        case 'induced_drag_magnitude': 
            return 'air_density', 'airspeed',
        case 'total_aerodynamic_force': 
            return 'magnitude_of_lift', 'lift_force', 'induced_drag_force', 'vector_sum'
        case 'wing_aerodynamic_force': 
            return 'total_aerodynamic_force',
        case 'stabalizer_aerodynamic_force': 
            return 'total_aerodynamic_force',
        case 'parasitic_drag_force': 
            return 'air_density', 'airspeed', 'vector_from_magnitude_and_angle', 'angle_to_relative_airflow_radians',
        case 'net_force': 
            return 'vector_sum', 'engine_thrust_force', 'wing_aerodynamic_force', 'stabalizer_aerodynamic_force', 'parasitic_drag_force', 'weight_force', 'rolling_resistance_force',
        case 'update_linear_velocity_and_position':
            return 'scale_vector', 'linear_acceleration', 'vector_sum',
        case 'angle_to_relative_airflow_radians':
            return 'vector_angle_radians',
        case 'update_angular_velocity_and_pitch':
            return 'normalize_angle', 'angular_acceleration',
        case 'rolling_resistance_force' :
            return 'is_on_ground', 'weight_force',
        case 'compute_moment': 
            return 'component_of_vector_in_direction_radians',
        case 'wing_moment': 
            return 'compute_moment', 'wing_aerodynamic_force',
        case 'stabilizer_moment': 
            return 'compute_moment', 'stabalizer_aerodynamic_force',
        case 'update_angular_velocity_and_pitch': 
            return 'net_moment',
        case 'simulate_multiple_time_steps': 
            return 'simulate_one_time_step',
        case 'propeller_rpm' | 'is_on_ground' | 'vector_sum' | 'propeller_area': 
            return []    
        case _:
            print('unexpected!!!!', function_name)
            return []

def expected_loops(function_name):
    match function_name:
        case 'vector_sum':
            return 'one foreach loop'
        case 'simulate_multiple_time_steps':
            return 'one range loop'
        case _:
            return 'no loops'

# Following code should not depend on specific assignment task ...

def Pass(msg) :
    print(termcolor.colored(msg,'green'))
    
def Fail(msg) :
    print(termcolor.colored(msg, 'red'))
    return False

def Heading(msg) :
    print(termcolor.colored(msg, attrs=['bold']))  
   
def retrieve_nodes(AST, predicate, select = lambda  node : node) :
    nodes = [] 
    for node in ast.walk(AST) :
        if predicate(node) :
            nodes.append(select(node))
    return nodes

def is_function_call(node) :
    return isinstance(node, ast.Call) and node.func and isinstance(node.func, ast.Name)

def is_method_call(node) :
    return isinstance(node, ast.Call) and node.func and isinstance(node.func, ast.Attribute)    

def is_loop(node): return is_for_loop(node) or is_while_loop(node)
    
def is_for_loop(node) :
    return isinstance(node, ast.For)

def is_while_loop(node) :
    return isinstance(node, ast.While)
    
def is_range_loop(node) :
    return is_for_loop(node) and node.iter and isinstance(node.iter, ast.Call) and node.iter.func and isinstance(node.iter.func, ast.Name) and node.iter.func.id == 'range'

def is_foreach_loop(node):
    return is_for_loop(node) and not is_range_loop(node)

def count_node(defn, predicate) :
    return len(retrieve_nodes(defn, predicate))

def exists_node(function, predicate) :
    return count_node(function, predicate) > 0

def uses_functions(function) :
    return set(retrieve_nodes(function, is_function_call, lambda call: call.func.id))

def uses_methods(function) :
    return set(retrieve_nodes(function, is_method_call, lambda call: call.func.attr))
    
def function_use(code): 
    problems = []
    for function_name, function_AST in code.items() :
        actual = (uses_functions(function_AST) | uses_methods(function_AST)) - set(dir(math)) - set(dir(builtins))
        expected = set(expected_calls(function_name)) 
        if actual != expected :
            problems.append((function_name, actual, expected))
    return problems
        
def appropriate_loops(code):
    loop_problems = []
    unexpected_loops =[]
    for function_name, function_AST in code.items() :
        loops = retrieve_nodes(function_AST, is_loop)
        expected = expected_loops(function_name)
        if expected == 'no loops':
            if loops:  
                unexpected_loops.append(function_name)        
        else :
            if len(loops) == 0:
                loop_problems.append((function_name, 'missing')) 
            else :
                wrong_type = (expected == 'one foreach loop' and not exists_node(function_AST, is_foreach_loop)) or (expected == 'one range loop' and not exists_node(function_AST, is_range_loop))
                too_many = len(loops) > 1
                if wrong_type :
                    if too_many :
                        loop_problems.append((function_name, 'wrong type and too many'))
                    else:
                        loop_problems.append((function_name, 'wrong type'))
                else:
                    if too_many :
                        loop_problems.append((function_name, 'too many'))
    return loop_problems, unexpected_loops

def is_implemented(module) :
    node = module.body[0]
    if len(node.body) == 2:
        docstring_node = node.body[0]
        raise_node = node.body[1]
            
        if (isinstance(docstring_node, ast.Expr) and
            isinstance(docstring_node.value, ast.Constant) and
            isinstance(raise_node, ast.Raise) and
            isinstance(raise_node.exc, ast.Call) and
            isinstance(raise_node.exc.func, ast.Name) and
            raise_node.exc.func.id == 'NotImplementedError') :
            return False
    return True

def complexity(AST) :                
    for defn in radon.complexity.cc_visit(AST):
        return defn.complexity
    
def test_complexity(ASTs):
    overly_complex = []
    unimplemented = []
    for function_name, function_AST in ASTs.items() :
        if is_implemented(function_AST):
            if  complexity(function_AST) > expected_complexity(function_name) :
                overly_complex.append(f'{function_name} (complexity {complexity(function_AST)})')
        else :
            unimplemented.append(function_name)
    return overly_complex, unimplemented

def assignment_statement(function) :
    return exists_node(function, lambda node : isinstance(node, ast.Assign))

def if_statement(function) :
    return exists_node(function, lambda node : isinstance(node, ast.If))

def if_statements(ASTs):
    for function_AST in ASTs.values() :
        for node in ast.walk(function_AST) :
            if if_statement(node) :
                return True
    return False

def follows_guidelines(name) :
    for ch  in name :
        if ch.isupper() :
            return False
    return True

def identifiers(function) :  
    return set(retrieve_nodes(function, lambda node: isinstance(node, ast.Name), lambda node : node.id))
    
def names_follow_guidelines(function) : 
    bad_names = []
    for name in identifiers(function) :
        if (name != 'NotImplementedError') and not follows_guidelines(name) :
            bad_names.append(name)
    return bad_names

def meaningful_names(ASTs):
    for function_name, function_AST in ASTs.items():    
        bad_names = names_follow_guidelines(function_AST)
        if bad_names :
            print(function_name, bad_names)
        
def assignment_statements(ASTs) :
    for function_AST in ASTs.values() :
        for defn in ast.walk(function_AST) :
            if assignment_statement(defn) :
                return True
    return False
    
def get_ASTs(function_list):
    ASTs = {}
    for function in function_list :
        source_code = inspect.getsource(function)
        AST = ast.parse(source_code)
        name = AST.body[0].name 
        ASTs[name] = AST
    return ASTs

def criteria2a(ASTs):
    Heading('Assessment Criteria 2a: Use of if statements')
    if if_statements(ASTs) :
        Pass("Criteria fully satisfied")
    else :
        Fail('No if statements found')    
    print()

def criteria2b(ASTs):
    Heading('Assessment Criteria 2b: Appropriate use of loops')  
    loop_problems, unexpected_loops = appropriate_loops(ASTs)

    if not loop_problems and not unexpected_loops:
        Pass("Criteria fully satisfied")   
    else :
        for function_name, problem in loop_problems:
            match problem:
                case 'missing' :
                    Fail(f'Function {function_name} should include a loop')
                case 'wrong type':
                    Fail(f'Function {function_name} should use a different style of loop')
                case 'too many':
                    Fail(f'Function {function_name} has too many loops')                  
                case 'wrong type and too many':
                    Fail(f'Function {function_name} should use a different style of loop and has too many loops')                
        for function_name in unexpected_loops:
            Fail(f'Function {function_name} does not require a loop')
    print()     

def criteria2c(ASTs):
    Heading('Assessment Criteria 2c: Functions make use of other appropriate functions')   
    problems = function_use(ASTs)
    if len(problems) == 0 :
        Pass("Criteria fully satisfied")   
    else :
        for function_name, actual, expected in problems :
            if (expected - actual) :
                Fail(f'Function {function_name} should call: {",".join(expected - actual)}')
            if (actual - expected) :
                 Fail(f'Function {function_name} should not call: {",".join(actual - expected)}')           
    print()    

def criteria2d(ASTs):
    Heading('Assessment Criteria 2d: Use of assignment statements')   
    if assignment_statements(ASTs):
        Pass(f'Criteria fully satisfied ')
    else :
        Fail(f'No assignment statements found')    
    print()    

def criteria3a(ASTs):
    Heading('Assessment Criteria 3a: Meaning variable names')   
    meaningful_names(ASTs)
    print('* This assessment criteria is marked manually by your tutors')
    print()  

def criteria3b(ASTs):
    Heading('Assessment Criteria 3b: Complexity of code')   
    overly_complex, unimplemented = test_complexity(ASTs)
    if len(overly_complex) == 0 and len(unimplemented) == 0 :
        Pass(f"Criteria fully satisfied")
    elif len(overly_complex) > 0:
        Fail(f'The following functions are overly complex: {", ".join(overly_complex)}')
    elif len(unimplemented) > 0 :
        Fail(f'The following functions are not implemented yet: {", ".join(unimplemented)}')        
    print()   
    
def assess_part_b_and_c_of_assessment_criteria(*function_list):
    ASTs = get_ASTs(function_list)
    
    Heading('Assessment Criteria 2: Learn a programming language and apply software development principles')           
    print() 
    criteria2a(ASTs) # if statements
    criteria2b(ASTs) # loops
    criteria2c(ASTs) # calls
    criteria2d(ASTs) # assignment

    display(HTML('<hr>')) 
    Heading('Assessment Criteria 3: Ensure software is clear and maintainable')     
    print() 

    criteria3a(ASTs) # identifiers
    criteria3b(ASTs) # complexity