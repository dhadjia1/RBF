import inspect
import weakref
from collections import OrderedDict

import numpy as np


def assert_shape(a,shape,label):
  ''' 
  Raises an error if *a* does not have the specified shape. If an 
  element in *shape* is *None* then that axis can have any length.
  '''
  ashape = np.shape(a)
  if len(ashape) != len(shape):
    raise ValueError(
      '*%s* is a %s dimensional array but it should be a %s '
      'dimensional array' % (label, len(ashape), len(shape)))

  for axis,(i,j) in enumerate(zip(ashape,shape)):
    if j is None:
      continue

    if i != j:
      raise ValueError(
        'axis %s of *%s* has length %s but it should have length %s.' %
        (axis,label,i,j))

  return


def get_arg_count(func):
  ''' 
  Returns the number of arguments that can be specified positionally
  for a function. If this cannot be inferred then -1 is returned.
  '''
  # get the function parameters
  params = inspect.signature(func).parameters
  # if a parameter has kind 2, then it is a variable positional
  # argument
  if any(p.kind == 2 for p in params.values()):
    return -1

  # if a parameter has kind 0 then it is a a positional only argument
  # and if kind is 1 then it is a positional or keyword argument.
  # Count the 0's and 1's
  out = sum((p.kind == 0) | (p.kind == 1) for p in params.values())
  return out


class Memoize(object):
  ''' 
  Memoizing decorator specifically for functions that take only numpy
  arrays as input. The output for calls to decorated functions will be
  cached and reused if the function is called again with the same
  arguments.

  Parameters
  ----------
  fin : function
    Function that takes arrays as input.
  
  Returns
  -------
  fout : function
    Memoized function.
  
  Notes
  -----
  1. Caches can be cleared with the module-level function
  `clear_caches`.
      
  '''
  # variable controlling the maximum cache size for all memoized 
  # functions
  MAX_CACHE_SIZE = 100
  # collection of weak references to all instances
  INSTANCES = []

  def __init__(self,fin):
    self.fin = fin
    self.cache = OrderedDict()
    Memoize.INSTANCES += [weakref.ref(self)]

  def __call__(self,*args):
    ''' 
    Calls the decorated function with `args` if the output is not 
    already stored in the cache. Otherwise, the cached value is 
    returned.
    '''
    key = tuple(a.tobytes() for a in args)
    if key not in self.cache:
      # make sure there is room for the new entry
      while len(self.cache) >= Memoize.MAX_CACHE_SIZE:
        self.cache.popitem(0)

      self.cache[key] = self.fin(*args)

    return self.cache[key]

  def __repr__(self):
    return self.fin.__repr__()


def clear_caches():
  ''' 
  Dereferences the caches for all memoized functions. 
  '''
  for i in Memoize.INSTANCES:
    if i() is not None:
      # `i` will be done if it has no references. If references still 
      # exists, then give it a new empty cache.
      i().cache = OrderedDict()
