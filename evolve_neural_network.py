import sys
import os
import pickle
import random
import numpy as np
import subprocess
import math
import time
import datetime
import itertools
from multiprocessing import Pool as ThreadPool


import deap
from deap import base
from deap import creator
from deap import tools

from genotype_to_phenotype import get_phenotype
from functions.divide_chunks import divide_chunks


infile_name = sys.argv[1]

with open( infile_name, 'r' ) as fil:
#with open('test_inFile.txt', 'r') as fil:
    lines = fil.readlines()

### Number of layers beyond the first layer. The first layer is a
### special layer that cannot be a flatten or dropout layer.
max_num_layers = int( lines[0].split()[2] )

population_size = int( lines[1].split()[2] )
selection_size = int( lines[2].split()[2] )
#crossover_size = int( lines[3].split()[2] )
random_size = int( lines[3].split()[2] )
mutation_probability = float( lines[4].split()[2] )
crossover_probability = float( lines[5].split()[2] )
number_of_generations = int( lines[6].split()[2] )
batch_size = int( lines[7].split()[2] )
number_of_classes = int( lines[8].split()[2] )
epochs = int( lines[9].split()[2] )
initial_population_directory = lines[10].split()[2]

#print(max_num_layers, population_size, selection_size, mutation_probability, number_of_generations)

### Top and bottom wrapper text to be used in making the neural network.
top_file = 'wrapper_text/top_text.txt'
bot_file = 'wrapper_text/bot_text.txt'

with open( top_file, 'r' ) as top:
    top_lines = top.readlines()

with open( bot_file, 'r' ) as bot:
    bot_lines = bot.readlines()

today = datetime.datetime.now()
year = today.year
month = today.month
day = today.day

data_directory_name = 'data/{0}/{0}{1:02d}/{0}{1:02d}{2:02d}/'.format( year, month, day )
neural_net_directory_name = 'neural_network_files/{0}/{0}{1:02d}/{0}{1:02d}{2:02d}/'.format( year, month, day )
output_directory_name = 'output_files/{0}/{0}{1:02d}/{0}{1:02d}{2:02d}/'.format( year, month, day )

if not os.path.isdir( data_directory_name ):
    os.makedirs( data_directory_name )

if not os.path.isdir( neural_net_directory_name ):
    os.makedirs( neural_net_directory_name )

if not os.path.isdir( output_directory_name ):
    os.makedirs( output_directory_name )

if not os.listdir( data_directory_name ):
    next_dir_number = 1

else:
    last_dir_name = sorted( os.listdir( data_directory_name ) )
    last_dir_number = int( last_dir_name[-1] )
    next_dir_number = last_dir_number + 1

data_dir_number_name = data_directory_name + '{0:04d}/'.format( next_dir_number )
neural_net_dir_number_name = neural_net_directory_name + '{0:04d}/'.format( next_dir_number )
output_dir_number_name = output_directory_name + '{0:04d}/'.format( next_dir_number )

if not os.path.isdir( data_dir_number_name ):
    os.makedirs( data_dir_number_name )

if not os.path.isdir( neural_net_dir_number_name ):
    os.makedirs( neural_net_dir_number_name )

if not os.path.isdir( output_dir_number_name ):
    os.makedirs(output_dir_number_name)

### Get the fitness of an individual.
#def evaluate(individual):
def evaluate( individual, i, g ):
    #print('i: {} g: {} individual: {}'.format( i, g, individual ) )
    #x_chunks = divide_chunks(individual, 17)    # There are 17 genes within each chromosome (layer).
    #print('x_chunks: ', x_chunks)

    ### Convert genotype to phenotype.
    phenotype_list = []
    #for chunk in x_chunks:
    #num_layers = len(x_chunks)
    num_layers = len(individual)
    zero_layers = 0 ### Check how many empty layers ('0' layers) there are in the network.
    #for n in range(num_layers):
    for n, layer in enumerate( individual ):
        #chunk = x_chunks[n]

        #if chunk[0] == 1:              # If chunk[0] == 1, this layer is an expressed chromosome.
        if layer[0] == 1:
            #phenotype = get_phenotype(chunk)
            phenotype = get_phenotype( layer )

        #elif chunk[0] == 2:            # If chunk[0] == 2, this layer is a dropout layer.
        elif layer[0] == 2:
            #phenotype = 'model.add(Dropout({}))'.format(chunk[12])
            phenotype = 'model.add( Dropout({}) )'.format( layer[12] )

        #elif chunk[0] == 3:            # If chunk[0] == 3, this layer is a flatten layer.
        elif layer[0] == 3:
            phenotype = 'model.add( Flatten() )'

        else:                          # If chunk[0] == 0, this layer is an empty layer.
            zero_layers += 1
            phenotype = '### --- empty layer --- ###'

        phenotype_list.append( phenotype )        # List of chromosomes in text format.

    if zero_layers != num_layers:
        neural_net_directory_name = 'neural_network_files/{0}/{0}{1:02d}/{0}{1:02d}{2:02d}/{3:04d}/'.format( year, month, day, next_dir_number )
        output_directory_name = 'output_files/{0}/{0}{1:02d}/{0}{1:02d}{2:02d}/{3:04d}/'.format( year, month, day, next_dir_number )

        neural_net_generation_dir_name = neural_net_directory_name + 'generation_{0:05d}/'.format( g )
        output_generation_dir_name = output_directory_name + 'generation_{0:05d}/'.format( g )

        if not os.path.isdir( neural_net_generation_dir_name ):
            try:
                os.makedirs( neural_net_generation_dir_name )
            except:
                pass

        if not os.path.isdir( output_generation_dir_name ):
            try:
                os.makedirs( output_generation_dir_name )
            except:
                pass

        #if not os.listdir(neural_net_directory_name):
        #    next_file_number = 1

        #else:
        #    last_file_name = sorted(os.listdir(neural_net_directory_name))
        #    last_file_number = int(last_file_name[-1].split('_')[1])
        #    next_file_number = last_file_number + 1

        run_file_name = neural_net_generation_dir_name + '{0}{1:02d}{2:02d}_individual_{3:04d}_neural_net.py'.format( year, month, day, i )
        output_file_name = output_generation_dir_name + '{0}{1:02d}{2:02d}_individual_{3:04d}_output.txt'.format( year, month, day, i )

        with open( run_file_name, 'w' ) as run_file:
            run_file.write( 'batch_size = ' + str(batch_size) + '\n')
            run_file.write( 'number_of_classes = ' + str(number_of_classes) + '\n')
            run_file.write( 'epochs = ' + str(epochs) + '\n')
            ### Write top wrapper to file.
            for line in top_lines:
                run_file.write( line.split('\n')[0] + '\n')

            ### Randomly choose the number of output_dimensionality in the first layer.
            #number_of_first_layer_output_dimensionality = np.random.randint(2, 100)
            #number_of_first_layer_output_dimensionality = 10

            ### Write first layer to file. Need this layer (or some other type of layer) for the first layer to take in the input shape.
            ##### Modified code to always have a first non-empty layer that is not a flatten or a dropout layer.
            #run_file.write("model.add(Conv2D(" + str(number_of_first_layer_output_dimensionality) + ", (3, 3), padding='same', activation='relu', input_shape=x_train.shape[1:]))\n")

            ### Write phenotype to file.
            for phenotype in phenotype_list:
                #print('phenotype: ', phenotype)
                run_file.write( phenotype + '\n' )

            ### Write bottom wrapper to file.
            for line in bot_lines:
                run_file.write( line.split('\n')[0] + '\n' )
    
        ### Save time at which job was started.
        #start = time.time()

        ### Start the job.
        #proc = subprocess.Popen(['srun', '--ntasks', '1', '--nodes', '1', 'python3.6', run_file_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        proc = subprocess.Popen( ['python3.6', run_file_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE )
        #proc = subprocess.Popen(['python3.6', run_file_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        #proc.wait()

        ### Save time at which job ended.
        #end = time.time()

        ### Compute the runtime of the job.
        #duration = end-start

        ### Compute the duration fitness based on how long it took to run the job.
        #inverse_duration = 1./duration

        ### Capture the output of the job.
        out = proc.communicate()[0].decode( 'utf-8' )
        #print( 'out: ', out )
        #with open(output_file_name, 'w') as output:
        #    for line in out:
        #        output.write(line)

        ### Compute inverse loss, inverse memory, and inverse cpu usage fitnesses.
        try:
            inverse_loss = 1./float( out.upper().split()[-7] )

            ### Save the accuracy.
            accuracy = float( out.upper().split()[-5] )
        except:
            inverse_loss = 100
            accuracy = 0
        #loss = float(out.upper().split()[-7])
        #inverse_mem = 1./float(out.upper().split()[-3])
        #inverse_cpu = 1./float(out.upper().split()[-1])

        ### Save the accuracy.
        #accuracy = float(out.upper().split()[-5])

        ### Collect the fitness values.
        #fitness = ( accuracy, inverse_loss, inverse_duration, inverse_mem, inverse_cpu )
        fitness = ( accuracy, inverse_loss )

        #fitness = [1, 1, 1, 1, 1]
        #fitness = [1, 1]

    else:
       fitness = [0, 0]

    ### Return the fitness value for the individual..
    return fitness

### Define how individuals mutate.
def Mutation( individual, original_x_dimension, original_y_dimension ):
    ### Divide individual's chromosome into chunks that represent each layer.
    #num_of_layers = individual[0]
    #individual_without_first_element = individual[1:] 

    #chunks = divide_chunks(individual, 17)
    
    #mut_num_of_layers = tools.mutUniformInt([ num_of_layers ], 1, max_num_layers, mutation_probability)

    ### Start a list for mutated individuals.
    mutated_individual = []
    #mutated_individual += [ mut_num_of_layers ]

    ### Iterate over individuals.
    #for c, chunk in enumerate(chunks):
    for c, layer in enumerate( individual ):
        #print(chunk)
        ### Mutate chromosome (layer) expression. The value is 0 (not expressed), 1 (expressed), 2 (dropout layer), 3 (flatten).
        #chunk[0] = tools.mutUniformInt([ chunk[0] ], 0, 2, mutation_probability)
        r = np.random.uniform( 0, 1 )
        if r <= mutation_probability:
            ### If the layer is the first layer, we must have it expressed as an actual layer (instead of empty, flatten, or dropout).
            if c != 0:
                #chunk[0] = np.random.randint(4)
                #chunk[0] = np.random.randint(3)
                layer[0] = np.random.randint( 3 )
            else:
                #chunk[0] = 1 # This is not necessary. What was the reason why this is not necessary again?
                layer[0] = 1

        ### Mutate layer type. The value is in the range 0:5 (inclusive).
        #chunk[1] = tools.mutUniformInt([ chunk[1] ], 0, 5, mutation_probability)
        r = np.random.uniform( 0, 1 )
        if r <= mutation_probability:
            #chunk[1] = np.random.randint(6)
            layer[1] = np.random.randint( 6 )

        ### Mutate the output dimensionality.
        #chunk[2] = tools.mutUniformInt([ chunk[2] ], 2, 4, mutation_probability)
        #chunk[2] = tools.mutUniformInt([ chunk[2] ], 2, 10, mutation_probability)
        r = np.random.uniform( 0, 1 )
        if r <= mutation_probability:
            #chunk[2] = np.random.randint(2, 101)

            #chunk[2] = int(np.random.normal(chunk[2], 1))
            layer[2] = int( np.random.normal( layer[2], 1 ) )

            ### Turn the output dimension to 2 if it is less than 2. This could be changed later.
            #if chunk[2] < 2:
            if layer[2] < 2:
                #chunk[2] = 2
                layer[2] = 2
            #if chunk[2] > 100:
            #    chunk[2] = 100

        ### Mutate kernel x number. (This is expressed as a fraction of the x dimension length.)
        #chunk[3] = tools.mutGaussian([ chunk[3] ], chunk[3], .1, mutation_probability)
        r = np.random.uniform( 0, 1 )
        if r <= mutation_probability:
            #chunk[3] = np.random.normal(chunk[3], .1)
            layer[3] = np.random.normal( layer[3], .1 )

        ### Mutate kernel y number. (This is expressed as a fraction of the y dimension length.)
        #print('chunk4: ', chunk[4])
        #chunk[4] = tools.mutGaussian([ chunk[4] ], chunk[4], .1, mutation_probability)
        r = np.random.uniform( 0, 1 )
        if r <= mutation_probability:
            #chunk[4] = np.random.normal(chunk[4], .1)
            layer[4] = np.random.normal( layer[4], .1 )

        #print('chunk4: ', chunk[4])

        ### Make the ratios non-negative. Make the ratios equal to 1 if they are greater than 1.
        #if chunk[3][0][0] < 0:
        #    chunk[3][0][0] += 1
        #if chunk[4][0][0] < 0:
        #    chunk[4][0][0] += 1
        #if chunk[3] < 0:
        if layer[3] < 0:
            #chunk[3] += 1
            #chunk[3] = 0
            layer[3] = 0
        #if chunk[3] > 1:
        elif layer[3] > 1:
            #chunk[3] = 1
            layer[3] = 1

        #print('chunk3: ', chunk[3], ' chunk4: ', chunk[4])
        #if chunk[4] < 0:
        if layer[4] < 0:
            #chunk[4] += 1
            #chunk[4] = 0
            layer[4] = 0
            
        #if chunk[4] > 1:
        elif layer[4] > 1:
            #chunk[4] = 1
            layer[4] = 1

        ### Mutate the stride length.
        #chunk[5] = tools.mutUniformInt([ chunk[5] ], 1, 10, mutation_probability)
        r = np.random.uniform( 0, 1 )
        if r <= mutation_probability:
            #chunk[5] = np.random.randint(1, 11)
            #ratio = float(chunk[5]) / original_x_dimension
            ratio = float( layer[5] ) / original_x_dimension
            new_ratio = np.random.normal( ratio, .1 )

            if new_ratio > 1:
                new_ratio = 1

            #chunk[5] = int(new_ratio * original_x_dimension)
            layer[5] = int( new_ratio * original_x_dimension )

        #print('\n strides: ' + str(chunk[5]) + '\n')

        ### Mutate activation type.
        #chunk[6] = tools.mutUniformInt([ chunk[6] ], 0, 10, mutation_probability)
        r = np.random.uniform( 0, 1 )
        if r <= mutation_probability:
            #chunk[6] = np.random.randint(0, 11)
            layer[6] = np.random.randint( 0, 11 )

        ### Mutate use bias.
        #chunk[7] = tools.mutUniformInt([ chunk[7] ], 0, 1, mutation_probability)
        r = np.random.uniform( 0, 1 )
        if r <= mutation_probability:
            #chunk[7] = np.random.randint(0, 2)
            layer[7] = np.random.randint( 0, 2 )

        ### Mutate bias initializer.
        #chunk[8] = tools.mutUniformInt([ chunk[8] ], 0, 10, mutation_probability)
        r = np.random.uniform( 0, 1 )
        if r <= mutation_probability:
            #chunk[8] = np.random.randint(0, 11)
            layer[8] = np.random.randint( 0, 11 )

        ### Mutate bias regularizer.
        #chunk[9] = tools.mutGaussian([ chunk[9] ], chunk[9], .1, mutation_probability)
        r = np.random.uniform( 0, 1 )
        if r <= mutation_probability:
            #chunk[9] = np.random.normal(chunk[9], .1)
            layer[9] = np.random.normal( layer[9], .1 )
            #if chunk[9] > 1:
            if layer[9] < 1:
                #chunk[9] = 1
                layer[9] = 1
            #elif chunk[9] < -1:
            elif layer[9] < -1:
                #chunk[9] = -1
                layer[9] = -1

        ### Mutate activity regularizer.
        #chunk[10] = tools.mutGaussian([ chunk[10] ], chunk[10], .1, mutation_probability)
        r = np.random.uniform( 0, 1 )
        if r <= mutation_probability:
            #chunk[10] = np.random.normal(chunk[10], .1)
            layer[10] = np.random.normal( layer[10], .1 )
            #if chunk[10] > 1:
            if layer[10] > 1:
                #chunk[10] = 1
                layer[10] = 1
            #elif chunk[10] < -1:
            elif layer[10] < -1:
                #chunk[10] = -1
                layer[10] = -1

        ### Mutate kernel initializer.
        r = np.random.uniform( 0, 1 )
        if r <= mutation_probability:
            #chunk[11] = np.random.randint(0, 11)
            layer[11] = np.random.randint( 0, 11 )

        ### Mutate dropout rate.
        r = np.random.uniform( 0,1 )
        if r <= mutation_probability:
            #chunk[12] = np.random.normal(chunk[12], .1)
            layer[12] = np.random.normal( layer[12], .1 )
        #if chunk[12] > 1:
        if layer[12] > 1:
            #chunk[12] = 1
            layer[12] = 1
        #elif chunk[12] < 0:
        elif layer[12] < 0:
            #chunk[12] = 0
            layer[12] = 0

        ### Update the chunk (layer).
        #chunk = [ chunk[0][0][0], chunk[1][0][0], chunk[2][0][0],
        #          chunk[3][0][0], chunk[4][0][0], chunk[5][0][0],
        #          chunk[6][0][0], chunk[7][0][0], chunk[8][0][0],
        #          chunk[9][0][0], chunk[10][0][0] ]
        #chunk = [ chunk[0], chunk[1], chunk[2], 
        #          chunk[3], chunk[4], chunk[5],
        #          chunk[6], chunk[7], chunk[8],
        #          chunk[9], chunk[10] ]

        ### Add chunk (layer) to the mutated individual.
        #mutated_individual += chunk
        mutated_individual.append( layer )

    ### Create the mutated individual. Not sure why this is needed. Is it needed?
    mutated_individual = creator.Individual( mutated_individual )

    return mutated_individual

### Check if the x and y kernals are valid (they should
### be smaller than the corresponding dimension size.)

def check_kernel_validity( individual, original_x_dimension, original_y_dimension ):
    ### Divide chromosome into chunks for each layer.
    #chunks = divide_chunks(individual, 10)
    #chunks = divide_chunks(individual, 17)

    ### Set previous x and y dimensions equal to the original x and y dimensions.
    ### (the x and y dimensions of the data set before the first layer.)
    previous_x_dimension = original_x_dimension
    previous_y_dimension = original_y_dimension

    ### Start a list for the modified individual. (The modified individual has its kernal sizes
    ### modified if the kernal size is invalid. Saves the unmodified individual if the kernal
    ### size is valid.)
    modified_individual = []
    #modified_individual += [ num_of_layers ]

    ### Iterate over the layers.
    #for chunk in chunks:
    for layer in individual:
        ### Get the kernal size for the x and y dimensions.
        #kernel_x = chunk[3]
        #kernel_y = chunk[4]
        kernel_x = layer[3]
        kernel_y = layer[4]

        ### Check if the kernal size is greater than the dimension size. The kernel size
        ### needs to be less than or equal to the dimension size minus 1 (for stride = 1).
        ### output = input - (kernel - 1).
        ### If the kernal size is too large, generate a random number between 0 and 1 and
        ### take the floor of [that number times the dimension size]. This gives a kernal size
        ### that is less than the dimension size.

        if kernel_x > previous_x_dimension - 1:
            kernel_x_ratio = np.random.uniform( 0, 1 )
            kernel_x = int( math.floor( kernel_x_ratio * previous_x_dimension ) )

        if kernel_y > previous_y_dimension - 1:
            kernel_y_ratio = np.random.uniform( 0, 1 )
            kernel_y = int( math.floor( kernel_y_ratio * previous_y_dimension ) )

        ### Check if the kernal size is less than 1. If so, change the size to be equal to 1.
        if kernel_x < 1:
            kernel_x = 1
        if kernel_y < 1:
            kernel_y = 1

        ### New dimension size is the old dimension size minus the quantity
        ### kernel size minus 1.

        previous_x_dimension -= (kernel_x - 1)
        previous_y_dimension -= (kernel_y - 1)

        ### Check if the kernel size is less than 1. If so, set the kernel
        ### size to be equal to 1.

        if previous_x_dimension < 1:
            previous_x_dimension = 1
            kernel_x = 1

        if previous_y_dimension < 1:
            previous_y_dimension = 1
            kernel_y = 1

        ### Save the new, valid kernel sizes to the chunk (layer).
        if kernel_x < 1:
            kernel_x = 1
        if kernel_y < 1:
            kernel_y = 1

        #chunk[3] = int(math.floor(kernel_x))
        #chunk[4] = int(math.floor(kernel_y))
        layer[3] = int( math.floor( kernel_x ) )
        layer[4] = int( math.floor( kernel_y ) )

        ### Save modified chunk to the new chromosome.
        #modified_individual += chunk
        modified_individual.append( layer )

    ### Create the modified individual using keras.creator.Individual.
    modified_individual = creator.Individual( modified_individual )

    return modified_individual

#def num_layers():
#    return np.random.randint(1, max_num_layers+1 )
def use_layer():                        ### Return 0 (skip layer), 1 (use layer), 2 (dropout layer), 3 (flatten layer).
    #return np.random.randint(0, 4)
    return np.random.randint(0, 3)
def layer_type():                            ### Return random integer between 0 and 5 for layer type.
    return np.random.randint(6)
def output_dimensionality():            ### Return random integer between 2 and 100 for number of output_dimensionality for layer.
    return np.random.randint(2, 101)
    #return np.random.randint(2, 11)
    #return 2
def get_kernel_x():
#def get_kernel_x(kernel_x):             ### Return kernel size for x dimension (not sure why I did this).
    #return kernel_x
    return np.random.randint(2, 10)
def get_kernel_y():
#def get_kernel_y(kernel_y):             ### Return kernel size for y dimension (not sure why I did this).
    #return kernel_y
    return np.random.randint(2, 10)
def strides_x():
    return np.random.randint(1, 11)
def strides_y():
    return np.random.randint(1, 11)
def act():                              ### Return random integer between 0 and 10 for layer activation type.
    return np.random.randint(11)
def use_bias():                         ### Return random integer between 0 and 1 for use_bias = True or False.
    return np.random.randint(2)
def bias_init():                        ### Return random integer between 0 and 10 for bias initializer for layer.
    return np.random.randint(11)
def bias_reg():                         ### Return random float between 0 and 1 for bias regularizer for layer.
    return np.random.uniform()
def act_reg():                          ### Return random float between 0 and 1 for activation regularizer for layer.
    return np.random.uniform()
def kernel_init():                      ### Return random integer between 0 and 10 for the type of kernel initializer.
    return np.random.randint(11)
def dropout_rate():                     ### Return random float between 0 and 1 for the dropout rate.
    return np.random.uniform()
def pool_size_x():
    return np.random.randint(1, 11)
def pool_size_y():
    return np.random.randint(1, 11)
def padding():
    return np.random.randint(0, 2)


def generate_individual(num_layers):
    individual = []
    for n in range(num_layers):
        layer = [ use_layer(), layer_type(), output_dimensionality(), get_kernel_x(), get_kernel_y(),
                  strides_x(), strides_y(), act(), use_bias(), bias_init(), bias_reg(), act_reg(),
                  kernel_init(), dropout_rate(), pool_size_x(), pool_size_y(), padding() ]

        individual.append( layer )

    #individual = creator.Individual(ind)

    return individual

#def cross_over(parent1, parent2):
#    num_layers = len(parent1)


'''
def seed_population(population, seed_file_name):
    #print(len(population))
    with open(seed_file_name, 'r') as fil:
        seed_individuals = fil.readlines()
    #print(len(seed_individuals))
    for i, seed in enumerate(seed_individuals):
        population[i] = list(seed)
    print(population)
    return population

def seed_population(population, seed_file_name):
    with open(seed_file_name, 'rb') as fil:
        seed_individuals = pickle.load(fil)
    for i, seed in enumerate(seed_individuals):
        population[i] = seed_individuals[i]
    
    #print(population)

    return population
'''

def convert(x):
    try:
        return int(x)
    except ValueError:
        return float(x)

# Extract the initial population
def seed_population(initial_population_directory):
    init_population = []
    for fil in os.listdir(initial_population_directory):
        file_name = initial_population_directory + '/' + fil
        #print(file_name)
        chromosome = []
        with open(file_name) as txt_file:
            #lines = [line.strip().strip('[]') for line in txt_file.readlines()
            #lines = [line.strip('[]\n') for line in txt_file.readlines()]
            #lines = [line.split(',') for line in lines]
            #init_population.append( creator.Individual( [convert(val) for sublist in lines for val in sublist] ) )
            lines = txt_file.readlines()
            #print(lines)
            for line in lines:
                #print(line)
                layer = []
                #print(line)
                fields = line.split()
                for field in fields:
                    #print(field)
                    #print(field.strip(','))
                    #chromosome.append( convert( field.strip(',') ) )
                    layer.append( convert( field.strip(',') ) )
            #print(lines)
                chromosome.append( layer )
        init_population.append( chromosome )
    return init_population

def crossover(parent1, parent2, crossover_probability):
    child1 = list(parent1)
    child2 = list(parent2)

    for m, layer in enumerate(parent1):
        for n, element in enumerate(parent1[0]):
            r = np.random.uniform(0, 1)
            if r <= crossover_probability:
                child1[m][n], child2[m][n] = child2[m][n], child1[m][n]

    #del child1.fitness.values
    #del child2.fitness.values

    #child1 = creator.Individual(child1)
    #child2 = creator.Individual(child2)

    return child1, child2

### Extract training data.
with open('../x_train.pkl', 'rb') as pkl_file:
    x_train = pickle.load(pkl_file, encoding = 'latin1')

### Get dimension of data (size of x and y dimensions).
original_x_dimension = x_train.shape[1]
original_y_dimension = x_train.shape[2]
previous_x_dimension = original_x_dimension
previous_y_dimension = original_y_dimension

#print(previous_x_dimension)
#print(previous_y_dimension)

### Not sure what this does besides setting the weights for each objective function.
#creator.create('FitnessMax', base.Fitness, weights=(1., 1., 1., 1., 1.))
creator.create('FitnessMax', base.Fitness, weights=(1., 1.))
creator.create('Individual', list, fitness=creator.FitnessMax)

toolbox = base.Toolbox()
### Create a string of a command to be executed to register a 'type' of individual.
### The 'type' of individual depends on how many layers the individual has.
toolbox_ind_str = "toolbox.register('individual', tools.initCycle, creator.Individual, ("

### Iterate over the number of layers and append to string to be executed.
for n in range(max_num_layers):
    use_layer_str = 'use_layer_' + str(n)
    layer_str = 'layer_type_' + str(n)
    output_dimensionality_str = 'output_dimensionality_' + str(n)
    kernel_x_str = 'kernel_x_' + str(n)
    kernel_y_str = 'kerner_y_' + str(n)
    strides_x_str = 'strides_x_' + str(n)
    strides_y_str = 'strides_y_' + str(n)
    act_str = 'act_' + str(n)
    use_bias_str = 'use_bias_' + str(n)
    bias_init_str = 'bias_init_' + str(n)
    bias_reg_str = 'bias_reg_' + str(n)
    act_reg_str = 'act_reg_' + str(n)
    kernel_init_str = 'kernel_init_' + str(n)
    dropout_rate_str = 'dropout_rate_' + str(n)
    pool_size_x_str = 'pool_size_x_' + str(n)
    pool_size_y_str = 'pool_size_y_' + str(n)
    padding_str = 'padding_' + str(n)

    toolbox.register(use_layer_str, use_layer)
    toolbox.register(layer_str, layer_type)
    toolbox.register(output_dimensionality_str, output_dimensionality)

    kernel_x_ratio = np.random.uniform(0, 1)
    kernel_x = int(math.floor(kernel_x_ratio * previous_x_dimension))
    kernel_y_ratio = np.random.uniform(0, 1)
    kernel_y = int(math.floor(kernel_y_ratio * previous_y_dimension))

    if kernel_x < 1:
        kernel_x = 1
    if kernel_y < 1:
        kernel_y = 1

    previous_x_dimension -= (kernel_x - 1)
    previous_y_dimension -= (kernel_y - 1)

    if previous_x_dimension < 1:
        previous_x_dimension = 1
        kernel_x = 1
    if previous_y_dimension < 1:
        previous_y_dimension = 1
        kernel_y = 1

    #toolbox.register(kernel_x_str, get_kernel_x, kernel_x)
    #toolbox.register(kernel_y_str, get_kernel_y, kernel_y)
    toolbox.register( kernel_x_str, get_kernel_x )
    toolbox.register( kernel_y_str, get_kernel_y )
    toolbox.register( strides_x_str, strides_x )
    toolbox.register( strides_y_str, strides_y )
    toolbox.register( act_str, act )
    toolbox.register( use_bias_str, use_bias )
    toolbox.register( bias_init_str, bias_init )
    toolbox.register( bias_reg_str, bias_reg )
    toolbox.register( act_reg_str, act_reg )
    toolbox.register( kernel_init_str, kernel_init )
    toolbox.register( dropout_rate_str, dropout_rate )
    toolbox.register( pool_size_x_str, pool_size_x )
    toolbox.register( pool_size_y_str, pool_size_y )
    toolbox.register( padding_str, padding )

    toolbox_ind_str += 'toolbox.' + use_layer_str + ', toolbox.' + layer_str
    toolbox_ind_str += ', toolbox.' + output_dimensionality_str + ', toolbox.' + kernel_x_str
    toolbox_ind_str += ', toolbox.' + kernel_y_str + ', toolbox.' + strides_x_str
    toolbox_ind_str += ', toolbox.' + strides_y_str + ', toolbox.' + act_str
    toolbox_ind_str += ', toolbox.' + use_bias_str + ', toolbox.' + bias_init_str
    toolbox_ind_str += ', toolbox.' + bias_reg_str + ', toolbox.' + act_reg_str
    toolbox_ind_str += ', toolbox.' + kernel_init_str + ', toolbox.' + dropout_rate_str
    toolbox_ind_str += ', toolbox.' + pool_size_x_str + ', toolbox.' + pool_size_y_str
    toolbox_ind_str += ', toolbox.' + padding_str

    if n != max_num_layers-1:
        toolbox_ind_str += ", "

toolbox_ind_str += "), n=1)"

### Execute string to register individual type.
exec(toolbox_ind_str)

### Register population, mate, mutate, select, and evaluate functions.
toolbox.register('population', tools.initRepeat, list, toolbox.individual)
toolbox.register('mate', tools.cxTwoPoint)
# THIS ISN'T WORKING toolbox.register('mate', tools.cxUniform, crossover_probability)
toolbox.register('mutate', Mutation)
toolbox.register('select', tools.selNSGA2)
#toolbox.register('select', tools.selTournament, tournsize = 2)
#toolbox.register('evaluate', evaluate)
#toolbox.register('individual_guess', initIndividual, creator.Individual)
toolbox.register('population_guess', seed_population, initial_population_directory)


def main():
    print('\n... Running genetic algorithm on neural networks ...\n')

    print('max_number_of_layers: {}'.format( max_num_layers ) )

    ### Population size.
    ##### Specified in inFile.txt.
    print('population_size: {}'.format( population_size ) )

    ### Number of individuals (parents) to clone for the next generation.
    ##### Specified in inFile.txt.
    print('selection_size (number of parents): {}'.format( selection_size ) )

    ### Number of individuals made through crossing of selected parents.
    ##### Specified in inFile.txt.
    #print('crossover_size (number of children generated): {}'.format( crossover_size ) )

    ### Number of immigrants.
    ##### Specified in inFile.txt.
    #print('random_size (number of immigrants ... new randomly created individuals): {}'.format( random_size ) )

    migrant_size = population_size - 2 * selection_size
    print('migrant_size: {}'.format( migrant_size ) )

    ### Set mutation probability.
    ##### Specified in inFile.txt.
    print('mutation_probability (mutation probability): {}'.format( mutation_probability ) )

    ### Set the crossover probability (for uniform crossover).
    ##### Specified in inFile.txt.
    print('crossover_probability (crossover probability ... for uniform crossover): {}'.format( crossover_probability ) )

    ### Set number of generations.
    ##### Specified in inFile.txt.
    print('number_of_generations (number of generations): {}'.format( number_of_generations ) )

    ### Set up the initial population.
    ##### Write 'FALSE' in inFile.txt for initialize with a random population.
    ##### Give a directory in inFile.txt from which to get the initial population.
    false_list = ['FALSE', 'false', 'False']

    if initial_population_directory not in false_list:
        temp_pop = toolbox.population_guess()

        #pop = [ creator.Individual(ind) for ind in temp_pop ]

        remaining_pop_to_initialize = population_size - len(temp_pop)
        #remaining_pop = toolbox.population( remaining_pop_to_initialize )
        remaining_pop = [ generate_individual( max_num_layers ) for i in range( remaining_pop_to_initialize ) ]

        temp_pop = temp_pop + remaining_pop
    else:
        #temp_pop = toolbox.population(n = population_size)
        temp_pop = [ generate_individual( max_num_layers ) for i in range( population_size ) ]

    pop = []
    for ind in temp_pop:
        x = creator.Individual(ind)
        pop.append(x)

    #for ind in pop:
    #    print(ind)

    #for p in pop:
    #    p[0] = 1


    print('\n\nInitial population ...')
    for c, i in enumerate(pop):
        print('Individual {}: '.format(c) )
        print(i)
        #print(type(i))

    ### Evaluate fitness of initial population.
    #fitnesses = list( toolbox.map(toolbox.evaluate, pop) )

    #fitnesses = [evaluate(ind, i, 0) for i, ind in enumerate(pop)]

    index = np.arange( population_size )
    generation = [ 0 for x in range( population_size ) ]

    pool = ThreadPool( population_size )

    fitnesses = pool.starmap( evaluate, zip(pop, index, generation) )

    pool.close()
    pool.join()

    #fitnesses = [(1, 1) for p in pop]

    ### Save fitness values to individuals.
    for ind, fit in zip( pop, fitnesses ):
        ind.fitness.values = fit

    ### Create directory to save the data for the 0th generation.
    generation_dir_name = data_directory_name + '{0:04d}/generation_00000/'.format(next_dir_number)
    if not os.path.isdir(generation_dir_name):
        os.makedirs(generation_dir_name)

    ### Save the population of the 0th generation.
    generation_population_file_name = generation_dir_name + '{0}{1:02d}{2:02d}_{3:04d}_generation_00000_population.pkl'.format(year, month, day, next_dir_number)
    with open(generation_population_file_name, 'wb') as fil:
        pickle.dump(pop, fil)

    ### Save the fitnesses of the 0th generation.
    generation_fitness_file_name = generation_dir_name + '{0}{1:02d}{2:02d}_{3:04d}_generation_00000_fitness.pkl'.format(year, month, day, next_dir_number)
    with open(generation_fitness_file_name, 'wb') as fil:
        pickle.dump(fitnesses, fil)

    ### Iterate over the generations.
    for g in range(1, number_of_generations):
        ### Select the parents.
        selected_parents = toolbox.select( pop, selection_size )

        print('\nGeneration {} ... \n'.format(g))

        #print('Generating {} children ...'.format(crossover_size) )
        new_children = []

        ### Mate the parents to form new individuals (children).

        #for p in selected_parents:
        #    print(p.fitness.values)

        for i in range( 0, selection_size, 2 ):
            #print(i)
            print('parent1: {}\nparent2: {}\n'.format(selected_parents[i], selected_parents[i+1]))
            child1, child2 = crossover(selected_parents[i], selected_parents[i+1], crossover_probability)
            print('child1: {}\nchild2: {}\n'.format(child1, child2))

            child1 = creator.Individual(child1)
            child2 = creator.Individual(child2)

            new_children.append(child1)
            new_children.append(child2)

        #for c in new_children:
        #    print(c.fitness, c.fitness.values)
        #for p in selected_parents:
        #    print(p.fitness, p.fitness.values)

        migrants = [ creator.Individual( generate_individual( max_num_layers ) ) for m in range( migrant_size ) ]

        new_population = new_children + migrants
        new_population = [ check_kernel_validity(ind, original_x_dimension, original_y_dimension) for ind in new_population ]

        index = range( selection_size, population_size )

        pool = ThreadPool( len(new_population) )

        new_fitnesses = pool.starmap( evaluate, zip(new_population, index, generation) )

        pool.close()
        pool.join()

        
        '''
        crosses_made = 0
        while crosses_made < crossover_size:
        #for c in range(crossover_size):
            parent1, parent2 = random.sample(selected_parents, 2)
            # Not sure what the cloning is for.
            #parent1, parent2 = toolbox.clone(parent1), toolbox.clone(parent2)
            
            #print('parent1: ', parent1)
            #print('parent2: ', parent2)

            child1, child2 = crossover(parent1, parent2, crossover_probability)

            #child1, child2 = toolbox.mate(parent1, parent2)
            #child1, child2 = deap.tools.cxUniform(parent1, parent2, crossover_probability)

            #print('child1: ', child1)
            #print('child2: ', child2)


            if crosses_made < crossover_size:
                del child1.fitness.values
                new_children.append(child1)
                crosses_made = crosses_made + 1

                print('child {}: '.format(crosses_made) )
                print(child1)

            if crosses_made < crossover_size:
                del child2.fitness.values
                new_children.append(child2)
                crosses_made = crosses_made + 1

                print('child {}: '.format(crosses_made) )
                print(child2)

            ### Why is only one of the children saved? I think it works out
            ### this way so that there's not too many individuals.
            ### This could probably be changed in the future.

        

        print('selected parents: {}\n'.format(selected_parents) )
        parent1, parent2 = random.sample(selected_parents, 2)
        print('parent1: {}, parent2: {}\n'.format(parent1, parent2) )
        child1, child2 = crossover(parent1, parent2, crossover_probability)
        print('child1: {}, child2: {}\n'.format(child1, child2) )
 
        ### New population consists of selected parents and their children.
        new_population = selected_parents + new_children

        ### Mutate the new population.
        print('\nMutating the new population (selected parents and their children) ...')

        for m, mutant in enumerate(new_population):
            r = np.random.uniform(0, 1)
            if r <= mutation_probability:
                mutated_ind = toolbox.mutate(mutant, original_x_dimension, original_y_dimension)
                del mutated_ind.fitness.values
                new_population[m] = mutated_ind

        ### Add migrants to the new population.
        #print('\nAdding randomly generated migrants to the new population ...')

        #new_random_migrants = toolbox.population(n = random_size)
        #for m in new_random_migrants:
        #    print('migrant: ', m)
        
        #new_population = new_population + new_random_migrants

        ### Check the kernel validity of the new population.
        new_population = [check_kernel_validity(ind, original_x_dimension, original_y_dimension) for ind in new_population]

        #fitnesses = list( map(toolbox.evaluate, new_population) )
        #fitnesses = [evaluate(ind, i, g) for i, ind in enumerate(new_population)]

        #index = np.arange( population_size )

        generation = [ g for x in range( population_size ) ]

        pool = ThreadPool( population_size )

        fitnesses = pool.starmap( evaluate, zip(pop, index, generation) )

        pool.close()
        pool.join()

        #fitnesses = [(1, 1) for p in pop]

        for ind, fit in zip(new_population, fitnesses):
            ind.fitness.values = fit

        ### Set pop to be the new population.
        pop = new_population

        #for p in pop:
        #    p[0] = 1

        print('\nFinal new population in Generation {}...'.format(g) )
        for c, i in enumerate(pop):
            print('Individual {}:'.format(c) )
            print(i)

        ### Create directory to save the data for the g-th generation.
        generation_dir_name = data_directory_name + '{0:04d}/generation_{1:05d}/'.format(next_dir_number, g)
        if not os.path.isdir(generation_dir_name):
            os.makedirs(generation_dir_name)

        ### Save the population of the g-th generation.
        generation_population_file_name = generation_dir_name + '{0}{1:02d}{2:02d}_{3:04d}_generation_{4:05d}_population.pkl'.format(year, month, day, next_dir_number, g)
        with open(generation_population_file_name, 'wb') as fil:
            pickle.dump(pop, fil)

        ### Save the fitnesses of the g-th generation.
        generation_fitness_file_name = generation_dir_name + '{0}{1:02d}{2:02d}_{3:04d}_generation_{4:05d}_fitness.pkl'.format(year, month, day, next_dir_number, g)
        with open(generation_fitness_file_name, 'wb') as fil:
            pickle.dump(fitnesses, fil)

        '''
        print(fitnesses)

    ### Return the final population and final fitnesses.
    return pop, fitnesses
    #return pop

if __name__ == '__main__':
    #main()
    pop, fitnesses = main()
