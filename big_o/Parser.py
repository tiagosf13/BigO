import ast
from DTOs.ArgumentDTO import ArgumentDTO
from DTOs.TypeDTO import TypeDTO

class Parser:
    """ This is a costum parser for the code, does more than a traditional parser """

    def __init__(self, code):
        self.code = code
        self.ast, self.ast_error = self.__get_ast(code)

    def __get_ast(self, function_code : str):
        try:
            # Parse the code into an abstract syntax tree
            tree = ast.parse(function_code)
            # Check if the first node in the tree is a FunctionDef (a Python function definition)
            return tree, None
        except SyntaxError as s:
            return False, s

    def __getFunctionCalls(self, node):
        calls = set()
        for child in ast.walk(node):
            if isinstance(child, ast.Call) and hasattr(child.func, 'id'):
                calls.add(child.func.id)
            else:
                for grandchild in ast.iter_child_nodes(child):
                    calls.update(self.__getFunctionCalls(grandchild))
        return calls
    
    def getFunctionArgs(self, function_definition):
        args = []
        
        for arg in function_definition.args.args:
            argType, first_type = self.getFunctionArgType(arg.annotation) if arg.annotation else ("Any", "Any")
            args.append(ArgumentDTO(
                name=arg.arg,
                firstType=TypeDTO(
                    name=first_type,
                    uuid=first_type.upper() # This is a placeholder for the uuid
                ),
                type= argType
            ))

        return args
    
    def getFunctionArgType(self, annotation: ast.arg, first=True):
        first_type = "Any" # Default type
        if not hasattr(annotation, 'value') and not hasattr(annotation, 'slice') and hasattr(annotation, 'id'):
            if first:
                first_type = annotation.id
                return annotation.id, first_type
            else:
                return annotation.id
        elif hasattr(annotation, 'dims'):
            str_dims = ""
            for tp in annotation.dims:
                if hasattr(tp, 'id'):
                    str_dims += f"{tp.id},"
                else:
                    str_dims += f"{self.getFunctionArgType(tp, first=False)},"
            return str_dims[:-1] # Remove the last comma
        if annotation.value and annotation.slice and first:
            first_type = annotation.value.id
            return f"{annotation.value.id}[{self.getFunctionArgType(annotation.slice,first=False)}]", first_type
        elif annotation.value and annotation.slice:
            return f"{annotation.value.id}[{self.getFunctionArgType(annotation.slice,first=False)}]" 
        elif annotation.value and not annotation.slice:
            if first:
                first_type = annotation.value.id
                return str(annotation.value.id), first_type
            else:
                return str(annotation.value.id)
        elif not annotation.value and annotation.slice:
            if first:
                first_type = annotation.slice.id
                return str(annotation.slice.id), first_type
            else:
                return str(annotation.slice.id)
        else:
            return "Any", "Any"
        
    def __getFunctionDefinitions(self):
        return [node for node in self.ast.body if isinstance(node, ast.FunctionDef)] 
    
    def getFunctionDependencies(self):
        dependent_functions = []
        independent_functions = []

        functions = self.__getFunctionDefinitions()
        function_names = [function.name for function in functions]

        for function in functions:
            # Remove the function that is being defined
            functionCalls = [call for call in self.__getFunctionCalls(function) if call != function.name]

            # Get the function calls that are in functions
            common_calls = [call for call in functionCalls if call in function_names]
            independent_functions.extend(common_calls)
        
        dependent_functions = [func for func in function_names if func not in independent_functions]

        return dependent_functions, independent_functions, functions



