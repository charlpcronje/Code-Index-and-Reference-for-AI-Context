import os
import re
import json
import javalang

def camel_case_split(identifier):
    # Splitting camel case strings into words
    """
    Splits a camel case identifier into separate words.
    Args:
        identifier (str): The camel case string to split.

    Returns:
        list: A list of words extracted from the camel case string.
    """
    matches = re.finditer('.+?(?:(?<=\\b[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)', identifier)
    return [m.group(0) for m in matches]
    """
    # Example usage for camel_case_split
    identifier = "sampleCamelCaseIdentifier"
    print(camel_case_split(identifier))
    """

def update_numeric_references(word, numeric_references, next_ref):
    """
    Updates the numeric references dictionary with a new word if not already present.
    """
    if word.lower() not in numeric_references:
        numeric_references[word.lower()] = next_ref
        return next_ref + 1
    return next_ref

def apply_numeric_references(identifier, numeric_references):
    """
    Applies numeric references to an identifier.
    """
    words = camel_case_split(identifier)
    return ''.join(['^' + str(numeric_references[word.lower()]) if word.istitle() else '~' + str(numeric_references[word.lower()]) for word in words])

def parse_java_file(file_path, numeric_references, next_ref):
    with open(file_path, 'r') as file:
        content = file.read()
    tree = javalang.parse.parse(content)

    for _, node in tree.filter(javalang.tree.ClassDeclaration):
        class_name = node.name
        next_ref = update_numeric_references(class_name, numeric_references, next_ref)
        class_name_with_refs = apply_numeric_references(class_name, numeric_references)

        # Process superclass
        if node.extends:
            for superclass in node.extends:
                superclass_name = superclass.name
                next_ref = update_numeric_references(superclass_name, numeric_references, next_ref)

        # Process interfaces
        if node.implements:
            for interface in node.implements:
                interface_name = interface.name
                next_ref = update_numeric_references(interface_name, numeric_references, next_ref)

        # Process methods
        for method in node.methods:
            method_name = method.name
            next_ref = update_numeric_references(method_name, numeric_references, next_ref)
            method_name_with_refs = apply_numeric_references(method_name, numeric_references)

            return_type = method.return_type.name if method.return_type else "void"
            next_ref = update_numeric_references(return_type, numeric_references, next_ref)
            return_type_with_refs = apply_numeric_references(return_type, numeric_references)

            parameters_info = []
            for parameter in method.parameters:
                param_name = parameter.name
                param_type = parameter.type.name
                next_ref = update_numeric_references(param_name, numeric_references, next_ref)
                next_ref = update_numeric_references(param_type, numeric_references, next_ref)
                param_name_with_refs = apply_numeric_references(param_name, numeric_references)
                param_type_with_refs = apply_numeric_references(param_type, numeric_references)

                parameters_info.append({
                    'name': param_name_with_refs,
                    'type': param_type_with_refs
                })

        # Process fields/properties
        for field in node.fields:
            for field_decl in field.declarators:
                field_name = field_decl.name
                field_type = field.type.name
                next_ref = update_numeric_references(field_name, numeric_references, next_ref)
                next_ref = update_numeric_references(field_type, numeric_references, next_ref)
                field_name_with_refs = apply_numeric_references(field_name, numeric_references)
                field_type_with_refs = apply_numeric_references(field_type, numeric_references)

                # Store or process field information
                # Example: {"name": field_name_with_refs, "type": field_type_with_refs}

        # Process constructors
        for constructor in node.constructors:
            constructor_name = constructor.name
            constructor_parameters = []
            for parameter in constructor.parameters:
                param_name = parameter.name
                param_type = parameter.type.name
                next_ref = update_numeric_references(param_name, numeric_references, next_ref)
                next_ref = update_numeric_references(param_type, numeric_references, next_ref)
                param_name_with_refs = apply_numeric_references(param_name, numeric_references)
                param_type_with_refs = apply_numeric_references(param_type, numeric_references)
                constructor_parameters.append({"name": param_name_with_refs, "type": param_type_with_refs})
            
            # Store or process constructor information
            # Example: {"name": constructor_name, "parameters": constructor_parameters}

        # Process inner classes/interfaces
        for inner in node.classes + node.interfaces:
            inner_name = inner.name
            next_ref = update_numeric_references(inner_name, numeric_references, next_ref)
            inner_name_with_refs = apply_numeric_references(inner_name, numeric_references)

            # Additional processing for the inner class/interface
            # Example: {"inner_name": inner_name_with_refs, "type": "class" or "interface"}

    return next_ref

def scan_java_project(config, numeric_references):
    project_path = config['root_path']
    next_ref = 1
    indexed_data = {}
    combined_code = ""

    for root, dirs, files in os.walk(project_path):
        dirs[:] = [d for d in dirs if d in config['include_folders']]
        dirs[:] = [d for d in dirs if d not in config['exclude_folders']]

        for file_name in files:
            if file_name.endswith('.java'):
                file_path = os.path.join(root, file_name)
                relative_path = os.path.relpath(file_path, project_path)
                combined_code += f"\n// File: {relative_path}\n"
                file_start_line = len(combined_code.split('\n'))
                
                with open(file_path, 'r') as file:
                    content = file.read()
                    combined_code += content
                    next_ref = parse_java_file(content, numeric_references, next_ref, indexed_data, file_start_line, relative_path)

    # Save the combined code to a file
    with open(config['output_directory'] + '/combined.java', 'w') as file:
        file.write(combined_code)

    # Save the index to a separate file
    with open(config['output_directory'] + '/index.java.json', 'w') as file:
        json.dump(indexed_data, file, indent=4)

    return indexed_data

def load_config(config_file):
    """
    Loads configuration from a JSON file.
    """
    with open(config_file, 'r') as file:
        return json.load(file)

if __name__ == '__main__':
    config = load_config('config.java.json')
    scan_java_project(config)