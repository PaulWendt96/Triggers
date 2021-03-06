## Triggers
Do weird stuff with weird looking decorators

## Installation
```bash
git clone https://www.github.com/PaulWendt96/Triggers
```

### Usage
Consider the following (extremely contrived) example:

```python
def fact(n):
  return n * fact(n - 1) if n else 1
```
    
Imagine that, whenever fact() is called, you want to see the provided argument 'n'. 
You could do this easily enough with a print statement

```python
def fact(n):
  print('fact({})'.format(n))
  return n * fact(n - 1) if n else 1
```
     
The print statement works, but it ruins the structure of fact() a bit. You'll have to remember that the print 
statement is in the function body, and that it needs to be removed at some point. 
You could also use Triggers to write this in a roundabout way as shown below. 

```python
@add_action_with_trigger(fact)
def print_first_arg(function_tuple):
  # function tuple is a named tuple consisting of (func, args, kwargs)
  print('{}({})'.format(func.__name__, args[0]))
  
@add_trigger
def fact(n):
  return n * fact(n - 1) if n else 1
```
  
This "solution" is less than ideal. You've added a few extra lines, two decorators, and have
achieved exactly the same result as putting in the print statement. However, using a decorator makes it a little
easier to remember to remove the print statment, so that is a win. Additionally, you've also opened the floodgate to 
using the print_first_arg function with any function that you add an @add_trigger decorator to. For instance, let's
add printing to the identity function as well.

```python
@add_action_with_trigger(fact, identity)
def print_first_arg(function_tuple):
  # function tuple is a named tuple consisting of (func, args, kwargs)
  print('{}({})'.format(func.__name__, args[0]))
  
@add_trigger
def fact(n):
  return n * fact(n - 1) if n else 1
  
@add_trigger
def identity(n):
  return n
```

Let's look at another example where Triggers is more useful. Consider the function below, which fails 5% of the time every time
with a ZeroDivisionError

```python
def fail(percent = .05):
  import random
  rand = random.random()
  return 1/0 if rand < percent else 0
```

We can use triggers to jump into fail() selectively when it fails.

```python
@add_trigger_with_action(enter_pdb_on_error)
def fail(percent = .05):
  import random
  rand = random.random()
  return 1/0 if rand < percent else 0
```

When fail() fails, @add_trigger_with_action(enter_pdb_on_error) will open pdb and enter a post-mortem analysis, allowing you to 
inspect fail() to see why it failed. 

Triggers has other functions provided with varying degrees of usefulness. Feel free to read the source for yourself to see these.

## Contributing
Pull requests are welcome. 
