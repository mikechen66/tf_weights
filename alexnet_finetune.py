###############################################################################################
#
#Mike Chen updates the script to be compatible with TensorFlow 2.x since the original
#script written in TensorFlow 1.7 could not be run on TensotFlow 2.x. 
#Giancarlo Zaccone and Md. Rezaul Karim
#Deep Learning with TensorFlow Second Edition
#Michael Guerzhoy and Davi Frossard, 2016
#AlexNet implementation in TensorFlow, with weights
#Details: 
#http://www.cs.toronto.edu/~guerzhoy/tf_alexnet/
#
#With code from https://github.com/ethereon/caffe-tensorflow
#Model from  https://github.com/BVLC/caffe/tree/master/models/bvlc_alexnet
#Weights from Caffe converted using https://github.com/ethereon/caffe-tensorflow
#
#The self-contained script includes most of the lines of code of  myalexnet_forward_tf2.py. It is 
#a headache that almost all the available alexnet finetune script found in Google could not be run
#or executed to generate many errors. Even Frederik Kratzert has not yet updated his finetune script
#written in 2017. The fact addresses the monthly changes of TensorFlow make some veteran developers 
#being far away from TensorFlow. 

#The script is an opportunity for users to learn from the classical model - AlexNet. It paves the 
#way for users to have a continuous attention on the AlexNet model and bridge between the past, the 
#present and the future. 
#
#There are some prerequisites as follows. 
#
#1.Download bvlc_alexnet.npy
#http://www.cs.toronto.edu/~guerzhoy/tf_alexnet/bvlc_alexnet.npy
#
#2.Download dogs-vs-cats data from Kaggle and unzip into a fileholder such as AlexNet-Finetune
#https://www.kaggle.com/c/dogs-vs-cats/data
#
#3.Put the script into the fileholder and then execute the script
# $ cd /home/user/Documents/AlexNet-Finetune
#
# $ python3  alexnet_finetune.py 
#
#It will run iterations and show a picture.
#
#####################################################################################
#import tensorflow as tf
import tensorflow.compat.v1 as tf
tf.compat.v1.disable_eager_execution()
from numpy import *
import os
import numpy as np
import time
import imageio
from skimage.transform import resize

import matplotlib.image as mpimg
from matplotlib import pyplot as plt
from scipy.ndimage import filters
import urllib
from numpy import random
from caffe_classes import class_names

##ADD 
from os import listdir
from os.path import isfile, join
from random import sample
from numpy import random


#Utility function
def next_batch(batch_size):
    path = os.getcwd()
    trainPath = path + "/trainDir/"
    files = [f for f in listdir(trainPath) if isfile(join(trainPath, f))]
    files = sample(files, len(files))
    batch_x = np.ndarray([batch_size,227, 227, 3])
    batch_y = np.zeros((batch_size, 2))
    i = 0
    for fname in files:
        img = (imageio.imread(join(trainPath, fname))[:,:,:3]).astype(float32)
        img = img - mean(img)
        #With the resize function in skimage, order=1 is defaulted as interp='bilinear'. 
        img = resize(img, (227,227,3), order=1, mode='reflect')
        batch_x[i] = img
        if "cat" in fname:
            batch_y[i][0] = 1
        if "dog" in fname:
            batch_y[i][1] = 1
        i+=1
        if i == batch_size:
            yield (batch_x, batch_y)
            batch_x = np.ndarray([batch_size,227, 227, 3])
            batch_y = np.zeros((batch_size, 3))
            i=0


#Define the output number of classes : dogs and cats
n_classes = 2

train_x = zeros((1, 227,227,3)).astype(float32)
train_y = zeros((1, n_classes))
xdim = train_x.shape[1:]
ydim = train_y.shape[1]


#ADD
learning_rate = 0.02
x = tf.placeholder(tf.float32, (None,) + xdim) # None = number of input images
y = tf.placeholder(tf.float32, [None,ydim])
keep_prob = tf.placeholder(tf.float32) #dropout (keep probability)


path = os.getcwd()
testPath1 = path + "/testDir/"
imlist = []
for i in range (1,100):
    filename = testPath1 + str(i)+".jpg"
    im = (imageio.imread(str(filename))[:,:,:3]).astype(float32)
    im = im - mean(im)
    imlist.append(im)
    

################################################################################

# (self.feed('data')
#         .conv(11, 11, 96, 4, 4, padding='VALID', name='conv1')
#         .lrn(2, 2e-05, 0.75, name='norm1')
#         .max_pool(3, 3, 2, 2, padding='VALID', name='pool1')
#         .conv(5, 5, 256, 1, 1, group=2, name='conv2')
#         .lrn(2, 2e-05, 0.75, name='norm2')
#         .max_pool(3, 3, 2, 2, padding='VALID', name='pool2')
#         .conv(3, 3, 384, 1, 1, name='conv3')
#         .conv(3, 3, 384, 1, 1, group=2, name='conv4')
#         .conv(3, 3, 256, 1, 1, group=2, name='conv5')
#         .fc(4096, name='fc6')
#         .fc(4096, name='fc7')
#         .fc(1000, relu=False, name='fc8')
#         .softmax(name='prob'))

#In Python 3.5, change this to the following line of code adapt to TensorFlow 2.x. 
net_data = np.load(open("bvlc_alexnet.npy", "rb"), encoding="latin1", allow_pickle=True).item()
#net_data = load("bvlc_alexnet.npy").item()


def conv(input, kernel, biases, k_h, k_w, c_o, s_h, s_w,  padding="VALID", group=1):
    '''From https://github.com/ethereon/caffe-tensorflow
    '''
    c_i = input.get_shape()[-1]
    assert c_i%group==0
    assert c_o%group==0
    convolve = lambda i, k: tf.nn.conv2d(i, k, [1, s_h, s_w, 1], padding=padding)
    
    
    if group==1:
        conv = convolve(input, kernel)
    else:
        input_groups =  tf.split(input, group, 3)   #tf.split(3, group, input)
        kernel_groups = tf.split(kernel, group, 3)  #tf.split(3, group, kernel) 
        output_groups = [convolve(i, k) for i,k in zip(input_groups, kernel_groups)]
        conv = tf.concat(output_groups, 3)          #tf.concat(3, output_groups)
    return  tf.reshape(tf.nn.bias_add(conv, biases), [-1]+conv.get_shape().as_list()[1:])


#Comment this line
#x = tf.placeholder(tf.float32, (None,) + xdim)


#conv1
#conv(11, 11, 96, 4, 4, padding='VALID', name='conv1')
k_h = 11; k_w = 11; c_o = 96; s_h = 4; s_w = 4
conv1W = tf.Variable(net_data["conv1"][0])
conv1b = tf.Variable(net_data["conv1"][1])
conv1_in = conv(x, conv1W, conv1b, k_h, k_w, c_o, s_h, s_w, padding="SAME", group=1)
conv1 = tf.nn.relu(conv1_in)

#lrn1
#lrn(2, 2e-05, 0.75, name='norm1')
radius = 2; alpha = 2e-05; beta = 0.75; bias = 1.0
lrn1 = tf.nn.local_response_normalization(conv1,
                                          depth_radius=radius,
                                          alpha=alpha,
                                          beta=beta,
                                          bias=bias)

#maxpool1
#max_pool(3, 3, 2, 2, padding='VALID', name='pool1')
k_h = 3; k_w = 3; s_h = 2; s_w = 2; padding = 'VALID'
maxpool1 = tf.nn.max_pool(lrn1, ksize=[1, k_h, k_w, 1], strides=[1, s_h, s_w, 1], padding=padding)


#conv2
#conv(5, 5, 256, 1, 1, group=2, name='conv2')
k_h = 5; k_w = 5; c_o = 256; s_h = 1; s_w = 1; group = 2
conv2W = tf.Variable(net_data["conv2"][0])
conv2b = tf.Variable(net_data["conv2"][1])
conv2_in = conv(maxpool1, conv2W, conv2b, k_h, k_w, c_o, s_h, s_w, padding="SAME", group=group)
conv2 = tf.nn.relu(conv2_in)


#lrn2
#lrn(2, 2e-05, 0.75, name='norm2')
radius = 2; alpha = 2e-05; beta = 0.75; bias = 1.0
lrn2 = tf.nn.local_response_normalization(conv2,
                                          depth_radius=radius,
                                          alpha=alpha,
                                          beta=beta,
                                          bias=bias)

#maxpool2
#max_pool(3, 3, 2, 2, padding='VALID', name='pool2')                                                  
k_h = 3; k_w = 3; s_h = 2; s_w = 2; padding = 'VALID'
maxpool2 = tf.nn.max_pool(lrn2, ksize=[1, k_h, k_w, 1], strides=[1, s_h, s_w, 1], padding=padding)

#conv3
#conv(3, 3, 384, 1, 1, name='conv3')
k_h = 3; k_w = 3; c_o = 384; s_h = 1; s_w = 1; group = 1
conv3W = tf.Variable(net_data["conv3"][0])
conv3b = tf.Variable(net_data["conv3"][1])
conv3_in = conv(maxpool2, conv3W, conv3b, k_h, k_w, c_o, s_h, s_w, padding="SAME", group=group)
conv3 = tf.nn.relu(conv3_in)

#conv4
#conv(3, 3, 384, 1, 1, group=2, name='conv4')
k_h = 3; k_w = 3; c_o = 384; s_h = 1; s_w = 1; group = 2
conv4W = tf.Variable(net_data["conv4"][0])
conv4b = tf.Variable(net_data["conv4"][1])
conv4_in = conv(conv3, conv4W, conv4b, k_h, k_w, c_o, s_h, s_w, padding="SAME", group=group)
conv4 = tf.nn.relu(conv4_in)


#conv5
#conv(3, 3, 256, 1, 1, group=2, name='conv5')
k_h = 3; k_w = 3; c_o = 256; s_h = 1; s_w = 1; group = 2
conv5W = tf.Variable(net_data["conv5"][0])
conv5b = tf.Variable(net_data["conv5"][1])
conv5_in = conv(conv4, conv5W, conv5b, k_h, k_w, c_o, s_h, s_w, padding="SAME", group=group)
conv5 = tf.nn.relu(conv5_in)

#maxpool5
#max_pool(3, 3, 2, 2, padding='VALID', name='pool5')
k_h = 3; k_w = 3; s_h = 2; s_w = 2; padding = 'VALID'
maxpool5 = tf.nn.max_pool(conv5, ksize=[1, k_h, k_w, 1], strides=[1, s_h, s_w, 1], padding=padding)

#fc6
#fc(4096, name='fc6')
fc6W = tf.Variable(net_data["fc6"][0])
fc6b = tf.Variable(net_data["fc6"][1])
fc6 = tf.nn.relu_layer(tf.reshape(maxpool5, [-1, int(prod(maxpool5.get_shape()[1:]))]), fc6W, fc6b)

#fc7
#fc(4096, name='fc7')
fc7W = tf.Variable(net_data["fc7"][0])
fc7b = tf.Variable(net_data["fc7"][1])
fc7 = tf.nn.relu_layer(fc6, fc7W, fc7b)

#fc8
#fc(1000, relu=False, name='fc8')


#comment these two following lines
#fc8W = tf.Variable(net_data["fc8"][0])
#fc8b = tf.Variable(net_data["fc8"][1])

#Define the variables for the last fully connected layer
fc8W = tf.Variable(tf.random_normal\
                   ([4096, n_classes]),\
                   trainable=True, name="fc8w")
fc8b = tf.Variable(tf.random_normal\
                   ([n_classes]),\
                   trainable=True, name="fc8b")
#end

fc8 = tf.nn.xw_plus_b(fc7, fc8W, fc8b)


#prob
#softmax(name='prob'))
prob = tf.nn.softmax(fc8)


#ADD
loss = tf.reduce_mean\
       (tf.nn.softmax_cross_entropy_with_logits_v2\
        (logits =prob, labels=y))
opt_vars = [v for v in tf.trainable_variables()\
            if (v.name.startswith("fc8"))]
optimizer = tf.train.AdamOptimizer\
            (learning_rate=learning_rate).minimize\
            (loss, var_list = opt_vars)


# Evaluation
correct_pred = tf.equal(tf.argmax(prob, 1), tf.argmax(y, 1))
accuracy = tf.reduce_mean(tf.cast(correct_pred, tf.float32))
                                                   
batch_size = 100
training_iters = 6000 
display_step = 1
dropout = 0.85 # Dropout, probability to keep units

init = tf.global_variables_initializer()
with tf.Session() as sess:
    sess.run(init)
    step = 1
    # Keep training until reach max iterations
    while step * batch_size < training_iters:
        batch_x, batch_y = \
                 next(next_batch(batch_size)) #.next()
        
        # Run optimization op (backprop)        
        sess.run(optimizer, \
                 feed_dict={x: batch_x, \
                            y: batch_y, \
                            keep_prob: dropout})                                
                
        if step % display_step == 0:
            # Calculate batch loss and accuracy
            cost, acc = sess.run([loss, accuracy],\
                                 feed_dict={x: batch_x, \
                                            y: batch_y, \
                                            keep_prob: 1.})
            print ("Iter " + str(step*batch_size) \
                   + ", Minibatch Loss= " + \
                  "{:.6f}".format(cost) + \
                   ", Training Accuracy= " + \
                  "{:.5f}".format(acc))              
            
        step += 1
    print ("Optimization Finished!")
        
    output = sess.run(prob, feed_dict = {x:imlist, keep_prob: 1.})
    result = np.argmax(output,1)
    testResult = [1,1,1,1,0,0,0,0,0,0,\
                  0,1,0,0,0,0,1,1,0,0,\
                  1,0,1,1,0,1,1,0,0,1,\
                  1,1,1,0,0,0,0,0,1,0,\
                  1,1,1,1,0,1,0,1,1,0,\
                  1,0,0,1,0,0,1,1,1,0,\
                  1,1,1,1,1,0,0,0,0,0,\
                  0,1,1,1,0,1,1,1,1,0,\
                  0,0,1,0,1,1,1,1,0,0,\
                  0,0,0,1,1,0,1,1,0,0]

    count = 0
    for i in range(0,99):
        if result[i] == testResult[i]:
            count=count+1

    print("Testing Accuracy = " + str(count) +"%")

    from random import randint
    j = randint(1, 100)
    filename = testPath1 + str(j)+".jpg"

    import matplotlib.image as mpimg
    image = mpimg.imread(filename)
    plt.imshow(image)
    plt.show()
    
    if result[j]== 0 :
        print("prevision is cat")
    else:
        print("prevision is dog")