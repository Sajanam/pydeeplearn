""" This class defines activation function that can be used with the nets in this project"""

from theano import tensor as T
from theano.tensor.shared_randomstreams import RandomStreams

import theano
import numpy as np


theanoFloat  = theano.config.floatX

class Sigmoid(object):

  def __init__(self):
    self.theanoGenerator = RandomStreams(seed=np.random.randint(1, 1000))

  def nonDeterminstic(self, x):
    val = self.deterministc(x)
    return self.theanoGenerator.binomial(size=val.shape,
                                            n=1, p=val,
                                            dtype=theanoFloat)

  def deterministc(self, x):
    return T.nnet.sigmoid(x)

class Rectified(object):

  def __init__(self):
    pass

  def nonDeterminstic(self, x):
    return self.deterministc(x)

  def deterministc(self, x):
    return x * (x > 0.0)

class RectifiedNoisy(object):

  def __init__(self):
    self.theanoGenerator = RandomStreams(seed=np.random.randint(1, 1000))

  def nonDeterminstic(self, x):
    x += self.theanoGenerator.normal(avg=0.0, std=T.nnet.ultra_fast_sigmoid(x))
    return self.deterministc(x)

  def deterministc(self, x):
    return x * (x > 0.0)

class RectifiedNoisyVar1(object):

  def __init__(self):
    self.theanoGenerator = RandomStreams(seed=np.random.randint(1, 1000))

  def nonDeterminstic(self, x):
    x += self.theanoGenerator.normal(avg=0.0, std=1.0)
    return self.deterministc(x)

  def deterministc(self, x):
    return x * (x > 0.0)