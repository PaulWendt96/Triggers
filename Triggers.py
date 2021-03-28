from functools import wraps
import sys
from collections import namedtuple
import inspect
from contextlib import contextmanager


func = namedtuple('func', 'function args kwargs')


def coro(f):
    '''
    Starts up a coroutine
    '''
    @wraps(f)
    def call(*args, **kwargs):
        coroutine = f(*args, **kwargs)
        next(coroutine)
        return coroutine
    return call


def funcs_equal(f, g):
    '''
    Equivalency check on __name__ attribute.
    Hacky but effective
    '''
    return f.__name__ == g.__name__


@coro
def action_on_triggers(func_to_wrap, *trigger):
    '''
    This wraps func_to_wrap, an action function, in a coroutine.
    This coroutine usually ends up being added to the ACTION
    list so it receives information regarding when trigger functions
    are called.
    '''
    while True:
        result = (yield)
        function = result.function
        funcs = any([funcs_equal(t, function) for t in trigger])
        if funcs:
            func_to_wrap(result)


@coro
def conditional_action_on_triggers(func_to_wrap, conditions, *trigger):
    '''
    Similar to func_trigger, but only triggers func_to_wrap when
    the function being called is in 'trigger' AND the resultant
    'result' that is sent to func_trigger_conditional matches all
    of the conditions provided by the 'conditions' argument
    '''
    while True:
        result = (yield)
        function = result.function
        funcs = any([funcs_equal(t, function) for t in trigger])
        conditions_met = all([condition(result) for condition in conditions])
        if funcs and conditions_met:
            func_to_wrap(result)


ACTIONS = []


def add_action(action):
    ACTIONS.append(action)


@contextmanager
def dump_and_restore():
    '''
    "Dumps" the ACTIONS global into a temporary local
    variable. ACTIONS global is restored later.
    Note that ACTIONS contains all of the coroutines
    that potentially execute, so "dumping" it means
    that none of the coroutines that would normally
    be registered will actually be triggered. This
    allows us to recursively examine code to look for
    errors and dive in right where the error occurs.
    We can also selectively gate for what functions
    we think might cause errors,and what errors we
    may need to handle, using enter_pdb_on_error
    '''
    global ACTIONS
    save_actions = ACTIONS
    ACTIONS = []
    yield
    ACTIONS = save_actions


def _broadcast_funccall(f, *args, **kwargs):
    for action in ACTIONS:
        function_info = func(f, args, kwargs)
        action.send(function_info)


def add_trigger(f):
    @wraps(f)
    def call(*args, **kwargs):
        _broadcast_funccall(f, *args, **kwargs)
        return f(*args, **kwargs)
    return call


def add_trigger_with_action(action):
    '''
    register_add allows a function to register itself to a certain
    "handler". for instance, say we have

    @register_add(enter_pdb_on_error)
    def another_div(a, b, c):
      return 1/0
    '''

    @wraps(action)
    def wrapped(f):
        trigger_func(action, f)
        @wraps(f)
        def call(*args, **kwargs):
            _broadcast_funccall(f, *args, **kwargs)
            return f(*args, **kwargs)
        return call
    return wrapped

def add_conditional_trigger_with_actions(conditions, action):
    @wraps(action)
    def wrapped(f):
        conditional_trigger_func(action, conditions, f)
        @wraps(f)
        def call(*args, **kwargs):
            _broadcast_funccall(f, *args, **kwargs)
            return f(*args, **kwargs)
        return call
    return wrapped


def add_conditional_trigger_with_actions_list(conditions, actions):
    '''
    Decorator with arguments gets called twice. As a result, the inner
    @wraps(f) is the only one we need to set to ensure that the function
    has appropriate metadata.
    '''
    def wrapped(f):
        for action in actions:
            conditional_trigger_func(action, conditions, f)
        @wraps(f)
        def call(*args, **kwargs):
            _broadcast_funccall(f, *args, **kwargs)
            return f(*args, **kwargs)
        return call
    return wrapped


def trigger_func(f, *triggers):
    '''
    func_trigger(f, *args) registers handler
    function f to be triggered when one of
    *args is called (assuming *args is also
    registered with @register).
    '''
    add_action(action_on_triggers(f, *triggers))


def conditional_trigger_func(f, conditions, *triggers):
    add_action(conditional_action_on_triggers(f, conditions, *triggers))


'''
Below example shows why it might be better to register conditional
triggers directly using a decorator. For instance, it would be
nice to do something like

@wrap_add_conditional_trigger_function(*triggers, *actions)
def inspect_even(f):
  return len(f.args) > 0 and f.args[0] % 2 == 0

Triggers here would be a list of registered trigger functions.
Actions are actions that are conditionally called when one
of the listed trigger functions is called
'''


def enter_pdb_on_error(result):
    '''
    This aims specifically to stop the debugger and enter
    tracing when the result raises whatever Exception
    the try-except construct can handle. This function
    is most useful when you expect an error at some
    point and want to examine what the function contents
    looked like before the Exception was raised.

    Note that this is just a jumping off point. You could,
    for instance, use this to monitor specific functions
    for specific errors that can be caught in realtime
    before they actually cause problems (note, however, that
    the recursive evaluation does cause the main process
    to hang until the recursion completes).

    You could also try and return a traceback that would
    allow you to jump right in. This would be good for
    functions that fail with some inputs but not with others.
    '''
    f = result.function
    args = result.args
    kwargs = result.kwargs
    with dump_and_restore():
        try:
            result = f(*args, **kwargs)
        except:
            import pdb
            pdb.post_mortem()


def enter_pdb(result):
    f = result.function
    args = result.args
    kwargs = result.kwargs
    import pdb
    pdb.set_trace()
    # don't recursively call function here ->
    # it is in the process of being called when
    # this function is executed (e.g if we were to look
    # at register_add(), we would be at the line
    # directly before return f(*args, **kwargs) is called
    return


@add_trigger_with_action(enter_pdb)
def enter_pdb_when_called():
    return 10


def add_action_with_trigger(*args):
    '''
    Allows a trigger function to register
    itself to be called on certain functions. Note
    that the functions themselves must be registered
    as well
    '''

    def wrapped(f):
        trigger_func(f, *args)
        def call(*args, **kwargs):
            return f(*args, **kwargs)
        return call
    return wrapped


def print_func_info(func):
    print(func)


@add_trigger
def fib(n):
    return 1 if n == 0 else n * fib(n - 1)


def inspect_even(f):
    return len(f.args) > 0 and f.args[0] % 2 == 0

@add_conditional_trigger_with_actions_list([inspect_even], [print_func_info for x in range(4)])
def fib2(n):
    return 1 if n == 0 else n * fib2(n - 1)


if __name__ == '__main__':
    fib(10)
    fib2(10)