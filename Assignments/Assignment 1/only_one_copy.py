import json
import ast

expected_functions = {
        'howe_truss_top_left_vertex': 'def howe_truss_top_left_vertex(horizontal_segment_length):',
        'warren_truss_top_left_vertex': 'def warren_truss_top_left_vertex(horizontal_segment_length):',
        'evenly_spaced_horizontal_vertices': 'def evenly_spaced_horizontal_vertices(leftmost_vertex, horizontal_gap_between_vertices, number_of_vertices):',
        'position_warren_truss_vertices': 'def position_warren_truss_vertices(horizontal_span_length, number_of_segments):',
        'connect_warren_truss_vertices': 'def connect_warren_truss_vertices(bridge, top_vertices, bottom_vertices):',
        'build_warren_truss': 'def build_warren_truss(bridge, horizontal_span_length, number_of_segments):',
        'position_howe_truss_vertices': 'def position_howe_truss_vertices(horizontal_span_length, number_of_segments):',
        'connect_howe_truss_vertices': 'def connect_howe_truss_vertices(bridge, top_vertices, bottom_vertices):',
        'build_howe_truss': 'def build_howe_truss(bridge, horizontal_span_length, number_of_segments):',
        'apply_loads': 'def apply_loads(bridge, bottom_elements, total_weight):',
        'add_supports': 'def add_supports(bridge, bottom_vertices):',
        'build_bridge': 'def build_bridge(truss_design, horizontal_span_length, number_of_segments, weight_per_metre):',
        'total_element_length': 'def total_element_length(bridge):',
        'max_compression_force': 'def max_compression_force(bridge):',
        'max_tension_force': 'def max_tension_force(bridge):',
        'max_displacement': 'def max_displacement(bridge):',
        'is_safe': 'def is_safe(bridge):',
        'analyse_bridge': 'def analyse_bridge(truss_design, horizontal_span_length, number_of_segments, weight_per_metre, visualize):' }

def test(ipynb_filename) :
    file = open (ipynb_filename, encoding='utf-8')
    filesrc = file.read()
    file.close()

    seen = {}
    errors = False

    for cell in json.loads(filesrc)['cells'] :
        if cell['cell_type'] == 'code' :
            codesrc = ''.join(cell['source'])
            try :
                AST = ast.parse(codesrc)            
                for node in ast.walk(AST) :
                    if isinstance(node, ast.FunctionDef) :  
                        if node.name in seen :
                            errors = True
                            print('Error: multiple definitions of function', node.name)
                        else :
                            seen[node.name] = ast.unparse(node).splitlines()[0]
            except SyntaxError as e :
                errors = True;
                print('Error: syntax error in code cell')
                pass    
                
    for name in expected_functions :
        if not name in seen :
            errors = True
            print('Error: missing definition of function', name)
        elif seen[name] != expected_functions[name] :
            errors = True
            print('Error: function definition has been modified:');
            print('\texpected:', expected_functions[name])
            print('\tfound:   ', seen[name])
            
    if not errors :
        print('All good, well done!')