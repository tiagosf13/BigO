import ast, random
from MockInputs.MockBooleanInputs import MockBooleanInputs
from MockInputs.MockDateTimeInputs import MockDateTimeInputs
from MockInputs.MockDictInputs import MockDictInputs
from MockInputs.MockFloatInputs import MockFloatInputs
from MockInputs.MockIntegerInputs import MockIntegerInputs
from MockInputs.MockListInputs import MockListInputs
from MockInputs.MockSetInputs import MockSetInputs
from MockInputs.MockStringInputs import MockStringInputs
from MockInputs.MockTupleInputs import MockTupleInputs
from DTOs.MockInputsDTO import MockInputsDTO

def get_mock_class(input_type):
    """Choose the mock data generator based on the input type."""
    generators = {
        "int": MockIntegerInputs,
        "float": MockFloatInputs,
        "bool": MockBooleanInputs,
        "str": MockStringInputs,
        "list": MockListInputs,
        "set": MockSetInputs,
        "dict": MockDictInputs,
        "tuple": MockTupleInputs,
        "datetime": MockDateTimeInputs,
    }

    if input_type not in generators:
        raise ValueError(f"Mock data generator for input type '{input_type}' is not defined.")
    elif input_type == "Any":
        # Return a random data generator for any type
        return random.choice(list(generators.values()))
    return generators[input_type]

def get_mock_data(function_definition, n):
    mock_data = ()
    for arg in function_definition.args.args:
        if arg.annotation:
            mock_data += (get_mock_data_for_arg(arg.annotation, n),)
        else:
            mock_data += (get_mock_data_for_arg("Any", n),)
    return mock_data

def get_mock_data_for_arg(annotation: ast.arg, n):

    value_present = hasattr(annotation, 'value')
    slice_present = hasattr(annotation, 'slice')
    id_present = hasattr(annotation, 'id')
    dims_present = hasattr(annotation, 'dims')

    if annotation == "Any":
        # Return a random data generator for any type
        return get_mock_class("Any").get_random_data()
    elif not value_present and not slice_present and id_present:
        return get_mock_class(annotation.id).get_random_data()
    elif value_present and slice_present:
        mock_class = get_mock_class(annotation.value.id)
        inst = mock_class()
        # See if it is a list or dict
        if annotation.value.id == "list":
            for i in range(n):
                inst.content.append(get_mock_data_for_arg(annotation.slice, n))
        elif annotation.value.id == "dict":
            for i in range(n):
                key, value = get_mock_data_for_arg(annotation.slice, n)
                inst.content.setdefault(key, value)
        else:
            inst.content = get_mock_data_for_arg(annotation.slice, n)
        return inst.content
    elif value_present and not slice_present:
        mock_class = get_mock_class(annotation.value.id)
        return mock_class.get_random_data()
    elif not value_present and slice_present:
        mock_class = get_mock_class(annotation.slice.id)
        return mock_class.get_random_data()
    elif dims_present:
        # This means its a tuple
        tup = ()
        for tp in annotation.dims:
            if hasattr(tp, 'id'):
                mock_class = get_mock_class(tp.id)
                tup += (mock_class.get_random_data(),)
            else:
                tup += (get_mock_data_for_arg(tp, n),)
        return tup
    else:
        return None
    

def get_input_sizes(args):
    """
    Generate mock inputs for all function arguments.

    Args:
        function_args (list[FunctionArgs]): List of argument metadata.

    Returns:
        callable: A callable that returns tuples of mock inputs.
    """
    
    if not args:
        return MockInputsDTO(min_n=100, max_n=100000)
    
    mock_classes = [get_mock_class(arg.firstType.name) for arg in args]

    mock_min_n = [mock_class.min_n for mock_class in mock_classes]
    for mock_class in mock_classes:
        if hasattr(mock_class, 'restrictions'):
            mock_min_n = mock_class.restrictions(mock_min_n)
    
    mock_max_n = [mock_class.max_n for mock_class in mock_classes]
    for mock_class in mock_classes:
        if hasattr(mock_class, 'restrictions'):
            mock_max_n = mock_class.restrictions(mock_max_n)

    return MockInputsDTO(
        min_n=min(mock_min_n),
        max_n=max(mock_max_n)
    )