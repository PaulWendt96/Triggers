# Triggers
Perform actions when certain functions are called under certain conditions

Yes, the title is super vague. But the Triggers.py module is useful (at least to me).
I find Triggers useful because it allows you to perform actions on select functions either before or after 
they are called. This is useful for debugging, and also opens the door to some more
interesting mischief.

For instance, consider the following (extremely contrived) example:

def fact(n):
  return n * fact(n - 1) if n else 1
    
Let's imagine that, whenever fact() is called, you want to see the provided argument 'n'. 
You could do this easily enough with print statements

def fact(n):
  print('fact({})'.format(n))
  return n * fact(n - 1) if n else 1
     
However, this does run the structure of fact() a bit. You'll have to remember that the print 
statement is in the function body, and that it needs to be removed at some point. 
You could also use Triggers to write this in a roundabout way as shown below.

@add_action_with_trigger(fact)
def print_first_arg(function_tuple):
  # function tuple is a named tuple consisting of (func, args, kwargs)
  print('{}({})'.format(func.__name__, args[0]))
  
@add_trigger
def fact(n):
  return n * fact(n - 1) if n else 1
  
This "solution", in its current form, is more of a problem. You've added a few extra lines, two decorators, and have
achieved exactly the same purpose. Put bluntly, this solution sucks. However, the decorator makes it a little
easier to remember to remove the print statment, so that is a win. Additionally, you've also opened the floodgate to 
using the print_first_arg function with any function that you add an @add_trigger decorator to. For instance, let's
add printing to the identity function as well.

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

This solution still sucks. Like I said, this is a contrived example. However, it isn't hard to imagine a situation in which, given
enough functions, this becomes useful. 

Let's look at another example where Triggers actually become useful. Consider the function below, which fails 5% of the time every time
with a ZeroDivisionError

def fail(percent = .05):
  import random
  rand = random.random()
  return 1/0 if rand < percent else 0

We can use triggers to jump into fail() selectively when it fails.

@add_trigger_with_action(enter_pdb_on_error)
def fail(percent = .05):
  import random
  rand = random.random()
  return 1/0 if rand < percent else 0

When fail() inevitably fails, @add_trigger_with_action(enter_pdb_on_error) will open pdb, allowing you to inspect fail() to see why it failed. 
Pretty rad.

There are a multitude of other examples for which Triggers may not be the worst solution in the world. Feel free to read the source for yourself - 
it is only 300 lines long, but is a little messy. 
