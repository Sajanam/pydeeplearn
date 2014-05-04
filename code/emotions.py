""" The aim of this file is to contain all the function
and the main which have to do with emotion recognition, especially
with the Kanade database."""

import argparse
# import DimensionalityReduction
import cPickle as pickle
from sklearn import cross_validation

import matplotlib.pyplot as plt
import numpy as np

import deepbelief as db
import restrictedBoltzmannMachine as rbm

from common import *
from readfacedatabases import *

parser = argparse.ArgumentParser(description='digit recognition')
parser.add_argument('--rbmnesterov', dest='rbmnesterov',action='store_true', default=False,
                    help=("if true, rbms are trained using nesterov momentum"))
parser.add_argument('--save',dest='save',action='store_true', default=False,
                    help="if true, the network is serialized and saved")
parser.add_argument('--train',dest='train',action='store_true', default=False,
                    help=("if true, the network is trained from scratch from the"
                          "traning data"))
parser.add_argument('--rbm', dest='rbm',action='store_true', default=False,
                    help=("if true, the code for traning an rbm on the data is run"))
parser.add_argument('--dbKanade', dest='dbKanade',action='store_true', default=False,
                    help=("if true, the code for training a deepbelief net on the"
                          "data is run, where the supervised data is the Kanade DB"))
parser.add_argument('--dbPIE', dest='dbPIE',action='store_true', default=False,
                    help=("if true, the code for training a deepbelief net on the"
                          "data is run, where the supervised data is the PIE DB"))
parser.add_argument('--trainSize', type=int, default=10000,
                    help='the number of tranining cases to be considered')
parser.add_argument('--testSize', type=int, default=1000,
                    help='the number of testing cases to be considered')
parser.add_argument('netFile', help="file where the serialized network should be saved")
parser.add_argument('--nesterov', dest='nesterov',action='store_true', default=False,
                    help=("if true, the deep belief net is trained using nesterov momentum"))
parser.add_argument('--rmsprop', dest='rmsprop',action='store_true', default=False,
                    help=("if true, rmsprop is used when training the deep belief net."))
parser.add_argument('--rbmrmsprop', dest='rbmrmsprop',action='store_true', default=False,
                    help=("if true, rmsprop is used when training the rbms."))
parser.add_argument('--cv', dest='cv',action='store_true', default=False,
                    help=("if true, do cross validation"))
parser.add_argument('--cvPIE', dest='cvPIE',action='store_true', default=False,
                    help=("if true, do cross validation"))
parser.add_argument('--facedetection', dest='facedetection',action='store_true', default=False,
                    help=("if true, do face detection"))
parser.add_argument('--maxEpochs', type=int, default=1000,
                    help='the maximum number of supervised epochs')
parser.add_argument('--miniBatchSize', type=int, default=10,
                    help='the number of training points in a mini batch')
parser.add_argument('--validation',dest='validation',action='store_true', default=False,
                    help="if true, the network is trained using a validation set")
parser.add_argument('--equalize',dest='equalize',action='store_true', default=False,
                    help="if true, the input images are equalized before being fed into the net")
parser.add_argument('--relu', dest='relu',action='store_true', default=False,
                    help=("if true, trains the RBM or DBN with a rectified linear unit"))

# DEBUG mode?
parser.add_argument('--debug', dest='debug',action='store_false', default=False,
                    help=("if true, the deep belief net is ran in DEBUG mode"))

# Get the arguments of the program
args = parser.parse_args()

# Set the debug mode in the deep belief net
db.DEBUG = args.debug

SMALL_SIZE = ((40, 30))

def rbmEmotions(big=False, reconstructRandom=False):
  # data, labels = readKanade(big)

  data, labels = readMultiPIE()
  print "data.shape"
  print data.shape

  trainData = data[0:-1, :]

  if args.relu:
    activationFunction = relu
  else:
    activationFunction = T.nnet.sigmoid

  # Train the network
  if args.train:
    # The number of hidden units is taken from a deep learning tutorial
    # The data are the values of the images have to be normalized before being
    # presented to the network
    nrVisible = len(data[0])
    nrHidden = 800
    # use 1 dropout to test the rbm for now
    net = rbm.RBM(nrVisible, nrHidden, 0.001, 1, 1,
                  binary=1-args.relu,
                  visibleActivationFunction=activationFunction,
                  hiddenActivationFunction=activationFunction,
                  rmsprop=args.rbmrmsprop,
                  nesterov=args.rbmnesterov)
    net.train(trainData)
    t = visualizeWeights(net.weights.T, SMALL_SIZE, (10,10))
  else:
    # Take the saved network and use that for reconstructions
    f = open(args.netFile, "rb")
    t = pickle.load(f)
    net = pickle.load(f)
    f.close()

  # get a random image and see it looks like
  # if reconstructRandom:
  #   test = np.random.random_sample(test.shape)

  # Show the initial image first
  test = data[-1, :]
  print "test.shape"
  print test.shape

  plt.imshow(vectorToImage(test, SMALL_SIZE), cmap=plt.cm.gray)
  plt.axis('off')
  plt.savefig('initialface.png', transparent=True)

  recon = net.reconstruct(test.reshape(1, test.shape[0]))
  print recon.shape

  plt.imshow(vectorToImage(recon, SMALL_SIZE), cmap=plt.cm.gray)
  plt.axis('off')
  plt.savefig('reconstructface.png', transparent=True)

  # Show the weights and their form in a tile fashion
  # Plot the weights
  plt.imshow(t, cmap=plt.cm.gray)
  plt.axis('off')
  if args.rbmrmsprop:
    st='rmsprop'
  else:
    st = 'simple'
  plt.savefig('weights' + st + '.png', transparent=True)
  print "done"

  if args.save:
    f = open(args.netFile, "wb")
    pickle.dump(t, f)
    pickle.dump(net, f)


"""
  Arguments:
    big: should the big or small images be used?
"""
def deepbeliefKanadeCV(big=False):
  data, labels = readKanade(big, None)

  data, labels = shuffle(data, labels)

  print "data.shape"
  print data.shape
  print "labels.shape"
  print labels.shape

  if args.relu:
    activationFunction = relu
  else:
    activationFunction = T.nnet.sigmoid

  # TODO: try boosting for CV in order to increase the number of folds
  params =[(0.1, 0.1, 0.9), (0.1,  0.5, 0.9),  (0.5, 0.1, 0.9),  (0.5, 0.5, 0.9),
           (0.1, 0.1, 0.95), (0.1, 0.5, 0.95), (0.5, 0.1, 0.95), (0.5, 0.5, 0.95),
           (0.1, 0.1, 0.99), (0.1, 0.5, 0.99), (0.5, 0.1, 0.99), (0.5, 0.5, 0.99)]

  unsupervisedData = buildUnsupervisedDataSetForKanadeLabelled()

  kf = cross_validation.KFold(n=len(data), k=len(params))
  bestCorrect = 0
  bestProbs = 0

  fold = 0
  for train, test in kf:

    trainData = data[train]
    trainLabels = labels[train]

    # TODO: this might require more thought
    net = db.DBN(5, [1200, 1500, 1500, 1500, 7],
               binary=1-args.relu,
               activationFunction=activationFunction,
               unsupervisedLearningRate=params[fold][0],
               supervisedLearningRate=params[fold][1],
               momentumMax=params[fold][2],
               nesterovMomentum=args.nesterov,
               rbmNesterovMomentum=args.rbmnesterov,
               rmsprop=args.rmsprop,
               miniBatchSize=args.miniBatchSize,
               hiddenDropout=0.5,
               rbmHiddenDropout=0.5,
               visibleDropout=0.8,
               rbmVisibleDropout=1)

    net.train(trainData, trainLabels,
              maxEpochs=args.maxEpochs,
              validation=args.validation,
              unsupervisedData=unsupervisedData)

    probs, predicted = net.classify(data[test])

    actualLabels = labels[test]
    correct = 0
    errorCases = []

    for i in xrange(len(test)):
      print "predicted"
      print "probs"
      print probs[i]
      print predicted[i]
      print "actual"
      actual = actualLabels[i]
      print np.argmax(actual)
      if predicted[i] == np.argmax(actual):
        correct += 1
      else:
        errorCases.append(i)

    print "correct for " + str(params[fold])
    print correct

    if bestCorrect < correct:
      bestCorrect = correct
      bestParam = params[fold]
      bestProbs = correct * 1.0 / len(test)

    fold += 1

  print "bestParam"
  print bestParam

  print "bestProbs"
  print bestProbs


def deepbeliefKanade(big=False):
  data, labels = readKanade(big,None)

  data, labels = shuffle(data, labels)

  print "data.shape"
  print data.shape
  print "labels.shape"
  print labels.shape

  # Random data for training and testing
  kf = cross_validation.KFold(n=len(data), n_folds=5)
  for train, test in kf:
    break

  if args.relu:
    activationFunction = relu
    unsupervisedLearningRate = 0.05
    supervisedLearningRate = 0.01
    momentumMax = 0.95
  else:
    activationFunction = T.nnet.sigmoid
    unsupervisedLearningRate = 0.5
    supervisedLearningRate = 0.1
    momentumMax = 0.95

  trainData = data[train]
  trainLabels = labels[train]

  # TODO: this might require more thought
  net = db.DBN(5, [1200, 1500, 1500, 1500, 7],
             binary=1-args.relu,
             activationFunction=activationFunction,
             rbmActivationFunctionVisible=T.nnet.sigmoid,
             rbmActivationFunctionHidden=T.nnet.sigmoid,
             unsupervisedLearningRate=unsupervisedLearningRate,
             # is this not a bad learning rate?
             supervisedLearningRate=supervisedLearningRate,
             momentumMax=momentumMax,
             nesterovMomentum=args.nesterov,
             rbmNesterovMomentum=args.rbmnesterov,
             rmsprop=args.rmsprop,
             miniBatchSize=args.miniBatchSize,
             hiddenDropout=0.5,
             rbmHiddenDropout=0.5,
             visibleDropout=0.8,
             rbmVisibleDropout=1)

  unsupervisedData = buildUnsupervisedDataSetForKanadeLabelled()


  net.train(trainData, trainLabels, maxEpochs=args.maxEpochs,
            validation=args.validation,
            unsupervisedData=unsupervisedData)

  probs, predicted = net.classify(data[test])

  actualLabels = labels[test]
  correct = 0
  errorCases = []

  for i in xrange(len(test)):
    print "predicted"
    print "probs"
    print probs[i]
    print "predicted"
    print predicted[i]
    print "actual"
    actual = actualLabels[i]
    print np.argmax(actual)
    if predicted[i] == np.argmax(actual):
      correct += 1
    else:
      errorCases.append(i)

  print "correct"
  print correct

  print "percentage correct"
  print correct  * 1.0/ len(test)


def buildUnsupervisedDataSetForKanadeLabelled():
  return np.vstack((
    # readCroppedYale(),
    readAttData(args.equalize),
    readJaffe(args.facedetection, args.equalize),
    # readNottingham(),
    readAberdeen(args.facedetection, args.equalize),
    readMultiPIE()[0]))

def buildUnsupervisedDataSetForPIE():
  return None

# TODO: you need to be able to map the emotions between each other
# but it might be the case that you won't get higher results which such a big
#dataset
def buildSupervisedDataSet():
  dataKanade, labelsKanade = readKanade()
  dataMPie, labelsMPie = readMultiPIE()
  print dataMPie.shape
  print dataKanade.shape

  data = np.vstack((dataKanade, dataMPie))
  labels = labelsKanade + labelsMPie
  return data, labels

def deepbeliefMultiPIE(big=False):
  data, labels = readMultiPIE()

  data, labels = shuffle(data, labels)

  print "data.shape"
  print data.shape
  print "labels.shape"
  print labels.shape

  # Random data for training and testing
  kf = cross_validation.KFold(n=len(data), n_folds=5)
  for train, test in kf:
    break

  if args.relu:
    activationFunction = relu
    unsupervisedLearningRate = 0.05
    supervisedLearningRate = 0.01
    momentumMax = 0.95
  else:
    activationFunction = T.nnet.sigmoid
    unsupervisedLearningRate = 0.05
    supervisedLearningRate = 0.01
    momentumMax = 0.9

  trainData = data[train]
  trainLabels = labels[train]

  # TODO: this might require more thought
  net = db.DBN(5, [1200, 1500, 1500, 1500, 6],
             binary=1-args.relu,
             activationFunction=activationFunction,
             rbmActivationFunctionVisible=T.nnet.sigmoid,
             rbmActivationFunctionHidden=T.nnet.sigmoid,
             unsupervisedLearningRate=unsupervisedLearningRate,
             # is this not a bad learning rate?
             supervisedLearningRate=supervisedLearningRate,
             momentumMax=momentumMax,
             nesterovMomentum=args.nesterov,
             rbmNesterovMomentum=args.rbmnesterov,
             rmsprop=args.rmsprop,
             miniBatchSize=args.miniBatchSize,
             hiddenDropout=0.5,
             rbmHiddenDropout=0.5,
             visibleDropout=0.8,
             rbmVisibleDropout=1)

  unsupervisedData = buildUnsupervisedDataSetForPIE()

  net.train(trainData, trainLabels, maxEpochs=args.maxEpochs,
            validation=args.validation,
            unsupervisedData=unsupervisedData)

  probs, predicted = net.classify(data[test])

  actualLabels = labels[test]
  correct = 0
  errorCases = []

  for i in xrange(len(test)):
    print "predicted"
    print "probs"
    print probs[i]
    print "predicted"
    print predicted[i]
    print "actual"
    actual = actualLabels[i]
    print np.argmax(actual)
    if predicted[i] == np.argmax(actual):
      correct += 1
    else:
      errorCases.append(i)

  print "correct"
  print correct

  print "percentage correct"
  print correct  * 1.0/ len(test)

def deepbeliefPIECV(big=False):
  data, labels = readMultiPIE()

  data, labels = shuffle(data, labels)

  # for d, l in zip(data, labels):
  #   plt.imshow(d.reshape(SMALL_SIZE), cmap=plt.cm.gray)
  #   plt.show()
  #   print "label"
  #   print l

  print data[0]

  print "data.shape"
  print data.shape
  print "labels.shape"
  print labels.shape

  if args.relu:
    activationFunction = relu
  else:
    activationFunction = T.nnet.sigmoid

  # TODO: try boosting for CV in order to increase the number of folds
  params =[(0.1, 0.1, 0.9),  (0.1, 0.5, 0.9),  (0.5, 0.1, 0.9),  (0.5, 0.5, 0.9),
           (0.1, 0.1, 0.95), (0.1, 0.5, 0.95), (0.5, 0.1, 0.95), (0.5, 0.5, 0.95),
           (0.1, 0.1, 0.99), (0.1, 0.5, 0.99), (0.5, 0.1, 0.99), (0.5, 0.5, 0.99)]

  unsupervisedData = buildUnsupervisedDataSetForPIE()

  kf = cross_validation.KFold(n=len(data), k=len(params))
  bestCorrect = 0
  bestProbs = 0

  fold = 0
  for train, test in kf:

    trainData = data[train]
    trainLabels = labels[train]

    # TODO: this might require more thought
    net = db.DBN(5, [1200, 1500, 1500, 1500, 6],
               binary=1-args.relu,
               activationFunction=activationFunction,
               rbmActivationFunctionVisible=activationFunction,
               rbmActivationFunctionHidden=activationFunction,
               unsupervisedLearningRate=params[fold][0],
               supervisedLearningRate=params[fold][1],
               momentumMax=params[fold][2],
               nesterovMomentum=args.nesterov,
               rbmNesterovMomentum=args.rbmnesterov,
               rmsprop=args.rmsprop,
               miniBatchSize=args.miniBatchSize,
               hiddenDropout=0.5,
               rbmHiddenDropout=0.5,
               visibleDropout=0.8,
               rbmVisibleDropout=1)

    net.train(trainData, trainLabels,
              maxEpochs=args.maxEpochs,
              validation=args.validation,
              unsupervisedData=unsupervisedData)

    probs, predicted = net.classify(data[test])

    actualLabels = labels[test]
    correct = 0
    errorCases = []

    for i in xrange(len(test)):
      print "predicted"
      print "probs"
      print probs[i]
      print predicted[i]
      print "actual"
      actual = actualLabels[i]
      print np.argmax(actual)
      if predicted[i] == np.argmax(actual):
        correct += 1
      else:
        errorCases.append(i)

    print "correct for " + str(params[fold])
    print correct

    if bestCorrect < correct:
      bestCorrect = correct
      bestParam = params[fold]
      bestProbs = correct * 1.0 / len(test)

    fold += 1

  print "bestParam"
  print bestParam

  print "bestProbs"
  print bestProbs

def svmMNIST():
  with open(args.netFile, "rb") as f:
    dbnNet = pickle.load(f)

  data, labels = readMultiPIE()

  # Random data for training and testing
  kf = cross_validation.KFold(n=len(data), n_folds=5)
  for train, test in kf:
    break

  training = data[train]
  trainLabels = labels[train]

  testing = data[test]
  testLabels = labels[test]

  svm.SVMCV(dbnNet, training, trainLabels, testing, testLabels)


def main():
  if args.rbm:
    rbmEmotions()
  if args.cv:
    deepbeliefKanadeCV()
  if args.dbKanade:
    deepbeliefKanade()
  if args.dbPIE:
    deepbeliefMultiPIE()
  if args.cvPIE:
    deepbeliefPIECV()


# You can also group the emotions into positive and negative to see
# if you can get better results (probably yes)
if __name__ == '__main__':
  import random
  print "FIXING RANDOMNESS"
  random.seed(6)
  np.random.seed(6)
  main()