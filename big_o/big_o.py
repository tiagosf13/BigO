#from timeit import Timer
from exectimeit import timeit
import numpy as np, logging
from complexities import ALL_CLASSES, Constant, Linear, Linearithmic, Logarithmic
from DTOs.TestDTO import TestDTO
from DTOs.ComplexityDTO import ComplexityDTO
from DTOs.ClassDTO import ClassDTO
from DTOs.InputDTO import InputDTO
from DTOs.OutputDTO import OutputDTO

root_logger = logging.getLogger()


def measure_execution_time(func, function_definition, data_generator,
                            min_n=100, max_n=100000, n_measures=10,
                            n_repeats=1, verbose=False):
    """
    Measure the execution time of a function for increasing N with multiple inputs.

    Input:
    ------
    func -- Function of which the execution time is measured.
            The function is called as func(*data), where data is returned
            by the argument `data_generator`.

    data_generator -- Function returning input data of 'length' N.
                        Input data for the argument `func` is created as
                        `data_generator(N)`. It should return a tuple of data.

    min_n, max_n, n_measures -- The execution time of func is measured
                                at `n_measures` points between `min_n` and
                                `max_n` (included).

    n_repeats -- Number of times func is called to compute execution time
                    (return the cumulative time of execution).

    n_timings -- Number of times the timing measurement is repeated.
                    The minimum time for all the measurements is kept.

    Output:
    -------
    n -- List of N's used as input to `data_generator`.
    time -- List of total execution time for each N in seconds.
    results -- List of results returned by `func` for each N.
    """
    
    func_timed = timeit.exectime(n_repeats)(func)

    # Wrapper to handle multiple inputs and capture function output
    class func_wrapper(object):

        def __init__(self, n):
            # TODO VERIFICAR TAMANHOS DE ENTRADA
            self.data = data_generator(function_definition, n)
            self.result = None
            self.time = None
            self.variation = None

        def __call__(self):
            # Create a copy of the data to avoid side effects
            data_copy = tuple(arg.copy() if isinstance(arg, list) else arg for arg in self.data)
            self.time, self.variation, self.result = func_timed(*data_copy)
            self.result = func(*data_copy)  # Pass the copied data to avoid mutation

    #ns = np.linspace(min_n, max_n, n_measures).astype('int64').flatten()
    ns = np.linspace(min_n, max_n, n_measures).astype('int64')  # Ensure integer dtype for N
    execution_time = np.empty(n_measures)
    tests = [] # List of TestDTOs

    progress = 0
    for i, n in enumerate(ns):
        n = int(n)
        wrapper = func_wrapper(n)
        if verbose:
            root_logger.info(f"----------------------------------------------------------")
            root_logger.info(f"Generated input for N={n}: {wrapper.data}\n")
            root_logger.info(f"Execution Number: {i+1} of {n_measures}")
        
        wrapper() # Call the function, which will be timed via the decorator
        # Repeat the measure until time is not negative
        while wrapper.time < 0:
            root_logger.info(f"Negative time detected for N={n}. Repeating measure...")
            wrapper()
        execution_time[i] = wrapper.time  # Use the timing recorded by the decorator
        
        if verbose:
            root_logger.info(f"Execution time for N={n}: {execution_time[i]}\n")
            root_logger.info(f"Function result for N={n}: {wrapper.result}")
        
        # Create a TestDTO for each test
        tests.append(
            TestDTO(
                input=InputDTO(
                    value=str(wrapper.data)
                ),
                output=OutputDTO(
                    value=str(wrapper.result)
                ),
                executionTime=execution_time[i]
            )
        )
        if verbose:
            progress  = (i+1) / n_measures * 100
            root_logger.info(f"Progress: {progress:.2f}%")
            root_logger.info(f"----------------------------------------------------------")
    
    return ns, execution_time, tests


def infer_big_o_class(ns, time, classes=ALL_CLASSES, verbose=False, simplicity_bias=1e-7):
    """Infer the complexity class from execution times.

    Input:
    ------

    ns -- Array of values of N for which execution time has been measured.

    time -- Array of execution times for each N in seconds.

    classes -- The complexity classes to consider. This is a list of subclasses
               of `big_o.complexities.ComplexityClass`.
               Default: all the classes in `big_o.complexities.ALL_CLASSES`

    verbose -- If True, print parameters and residuals of the fit for each
               complexity class

    simplicity_bias -- Preference toward choosing simpler methods when
                       the difference between residuals is less than the
                       simplicity_bias. If simplicity_bias is 0, the
                       complexity class with the lowest residuals is
                       always chosen.

    Output:
    -------

    best_class -- Object representing the complexity class that best fits
                  the measured execution times.
                  Instance of `big_o.complexities.ComplexityClass`.

    fitted -- A dictionary of fittest complexity classes to the fit residuals
    """

    best_residuals = np.inf
    complexities = []
    repeatTests = False
    best = None
    for class_ in classes:
        inst = class_()
        residuals = inst.fit(ns, time)

        # Create a ComplexityDTO for each class
        complexity = ComplexityDTO(
            class_=ClassDTO(
                name=inst.__class__.__name__,
                uuid=inst.__class__.__name__.upper()
            ),
            executionTime=time,
            meanExecutionTime=np.mean(time),
            standardDeviation=np.std(time),
            residual=residuals,
            best=False
        )
        # NOTE: subtract bias for tiny preference for simpler methods
        # TODO: improve simplicity bias (AIC/BIC)?
        #if residuals < best_residuals - simplicity_bias:
        if residuals < best_residuals - simplicity_bias:
            best_residuals = residuals
            repeatTests = isinstance(inst, (Constant, Linear, Logarithmic))
            best = complexity
        if verbose:
            root_logger.info('%s (r=%f)', inst, residuals)
        complexities.append(complexity)
    # Finalize best flag assignment
    for c in complexities:
        c.best = (c.class_.name == best.class_.name)

    return complexities, repeatTests


def big_o(func, function_definition, data_generator,
          min_n=256, max_n=4096, min_n_reinforcement=256, max_n_reinforcement=40960, n_measures=10, n_measures_reinforcement=100,
          n_repeats=1, classes=ALL_CLASSES, verbose=False, return_raw_data=False):
    """ Estimate time complexity class of a function from execution time with multiple inputs.

    Input:
    ------
    func -- Function of which the execution time is measured.
            The function is called as func(*data), where data is returned
            by the argument `data_generator`

    data_generator -- Function returning input data of 'length' N.
                      Input data for the argument `func` is created as
                      `data_generator(N)`. It should return a tuple of data.

    min_n, max_n, n_measures -- The execution time of func is measured
                                at `n_measures` points between `min_n` and
                                `max_n` (included)

    n_repeats -- Number of times func is called to compute execution time
                 (return the cumulative time of execution)

    n_timings -- Number of times the timing measurement is repeated.
                 The minimum time for all the measurements is kept.

    classes -- The complexity classes to consider. This is a list of subclasses
               of `big_o.complexities.ComplexityClass`.
               Default: all the classes in `big_o.complexities.ALL_CLASSES`

    verbose -- If True, print parameters and residuals of the fit for each
               complexity class

    return_raw_data -- If True, the function returns the measure points and its
                       corresponding execution times as part of the fitted dictionary
                       of complexity classes.

    Output:
    -------
    best_class -- Object representing the complexity class that best fits
                  the measured execution times.

    fitted -- A dictionary of fittest complexity classes to the fit residuals
    """
    try:

        def measure_and_infer(min_n: int, max_n: int, n_measures, max_retries=1, verbose=False):
            """Helper function to measure execution time and infer complexity."""
            repeatTests = True
            MAX_RETRIES = 1
            retries = 0
            while repeatTests and retries <= MAX_RETRIES:
                if retries > 0 and verbose:
                    root_logger.info(f"Repeating tests: {retries+1} of {MAX_RETRIES}")
                repeatTests = False
                ns, times, tests = measure_execution_time(func, function_definition, data_generator,
                                                            min_n, max_n, n_measures, n_repeats, verbose=verbose)
                complexities, repeatTests = infer_big_o_class(ns, times, classes, verbose=verbose)
                retries += 1
            return ns, times, tests, complexities
        
        # Initial measurement
        _, _, tests, complexities = measure_and_infer(min_n, max_n, n_measures)

        return complexities, tests
    except Exception as e:
        root_logger.error(f"Error during Big-O analysis: {e}", exc_info=True)
        return None, None
    
