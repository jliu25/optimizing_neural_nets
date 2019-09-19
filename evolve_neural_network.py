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

from deap import base
from deap import creator
from deap import tools

from genotype_to_phenotype import get_phenotype
from functions.divide_chunks import divide_chunks


today = datetime.datetime.now()
year = today.year
month = today.month
day = today.day

### Top and bottom wrapper text to be used in making the neural network.
top_file = 'wrapper_text/top_text.txt'
bot_file = 'wrapper_text/bot_text.txt'

with open(top_file, 'r') as top:
    top_lines = top.readlines()
with open(bot_file, 'r') as bot:
    bot_lines = bot.readlines()

### Get the fitness of an individual.
def evaluate(individual):
    '''
    x_chunks = divide_chunks(individual, 9)

    ### Convert genotype to phenotype.
    phenotype_list = []
    for chunk in x_chunks:
        phenotype = get_phenotype(chunk)
        phenotype_list.append(phenotype)

    neural_net_directory_name = 'neural_network_files/{0}/{0}{1:02d}/{0}{1:02d}{2:02d}/'.format(year, month, day)
    if not os.path.isdir(neural_net_directory_name):
        os.makedirs(neural_net_directory_name)

    if not os.listdir(neural_net_directory_name):
        next_file_number = 1

    else:
        last_file_name = sorted(os.listdir(neural_net_directory_name))
        last_file_number = int(last_file_name[-1].split('_')[1])
        next_file_number = last_file_number + 1

    temp_file_name = neural_net_directory_name + '{0}{1:02d}{2:02d}_{3:06d}_neural_net.py'.format(year, month, day, next_file_number)    

    with open(temp_file_name, 'w') as tempfile:
        ### Write top wrapper to file.
        for line in top_lines:
            tempfile.write( line.split('\n')[0] + '\n')

        ### Randomly choose the number of nodes in the first layer.
        #number_of_first_layer_nodes = np.random.randint(2, 100)
        number_of_first_layer_nodes = 2

        ### Write first layer to file.
        tempfile.write("model.add(Conv2D(" + str(number_of_first_layer_nodes) + ", (3, 3), padding='same', activation='relu', input_shape=x_train.shape[1:]))\n")

        ### Write phenotype to file.
        for phenotype in phenotype_list:
            tempfile.write(phenotype + '\n')

        ### Write bottom wrapper to file.
        for line in bot_lines:
            tempfile.write( line.split('\n')[0] + '\n' )

    ### Save time at which job was started.
    start = time.time()

    #print(sys.path)

    ### Start the job.
    #proc = subprocess.Popen(['srun', '--ntasks', '1', '--nodes', '1', 'python3.6', temp_file_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    proc = subprocess.Popen(['python3.6', temp_file_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    ### Save time at which job ended.
    end = time.time()

    ### Compute the runtime of the job.
    duration = end-start

    ### Compute the duration fitness based on how long it took to run the job.
    inverse_duration = 1./duration

    ### Capture the output of the job.
    #print(proc.communicate())
    out = proc.communicate()[0].decode('utf-8')
#    with open('test_johnson.txt', 'w') as fil:
#        fil.write(out)
#    print(out)

    ### Compute loss, memory, and cpu usage fitnesses.
    inverse_loss = 1./float(out.upper().split()[-7])
    inverse_mem = 1./float(out.upper().split()[-3])
    inverse_cpu = 1./float(out.upper().split()[-1])

    ### Save the accuracy.
    accuracy = float(out.upper().split()[-5])

    ### Collect the fitness values.
    fitness = ( accuracy, inverse_loss, inverse_duration, inverse_mem, inverse_cpu )
#    print(fitness)
    '''

    fitness = [1, 1, 1, 1, 1]

    ### Return the fitness values.
    return fitness

### Define how offspring mutate.
def myMutation(individual):
    #print('individual: ', individual)

    ### Divide individual's chromosome into chunks that represent each layer.
    chunks = divide_chunks(individual, 9)
    #print('chunks:', chunks)

    ### Start a list for mutated individuals.
    mutated_individual = []

    ### Iterate over individuals.
    #print(chunks)
    for chunk in chunks:
        ### Mutate layer type.
        chunk[0] = tools.mutUniformInt([ chunk[0] ], 0, 2, .5)

        ### Mutate kernel x number. (This is expressed as a fraction of the x dimension length.)
        chunk[1] = tools.mutGaussian([ chunk[1] ], chunk[1], .1, .5)

        ### Mutate kernel y number. (This is expressed as a fraction of the y dimension length.)
        chunk[2] = tools.mutGaussian([ chunk[2] ], chunk[2], .1, .5)

        ### Make the ratios positive.
        if chunk[1][0][0] < 0:
            chunk[1][0][0] += 1
        if chunk[2][0][0] < 0:
            chunk[2][0][0] += 1

        ### Mutate number of nodes.
        chunk[3] = tools.mutUniformInt([ chunk[3] ], 2, 4, .5)

        ### Mutate activation type.
        chunk[4] = tools.mutUniformInt([ chunk[4] ], 0, 10, .5)
 
        ### Mutate use bias.
        chunk[5] = tools.mutUniformInt([ chunk[5] ], 0, 1, .5)

        ### Mutate bias initializer.
        chunk[6] = tools.mutUniformInt([ chunk[6] ], 0, 10, .5)

        ### Mutate bias regularizer.
        chunk[7] = tools.mutGaussian([ chunk[7] ], chunk[7], .1, .5)

        ### Mutate activity regularizer.
        chunk[8] = tools.mutGaussian([ chunk[8] ], chunk[8], .1, .5)

        ### Update the chunk (layer).
        chunk = [ chunk[0][0][0], chunk[1][0][0], chunk[2][0][0],
                  chunk[3][0][0], chunk[4][0][0], chunk[5][0][0],
                  chunk[6][0][0], chunk[7][0][0], chunk[8][0][0] ]

        ### Add chunk (layer) to the mutated individual.
        mutated_individual += chunk

    ### Create the mutated individual.
    mutated_individual = creator.Individual(mutated_individual)

    return mutated_individual

### Check if the x and y kernals are valid (they should
### be smaller than the corresponding dimension size.)

def check_kernel_validity(individual, original_x_dimension, original_y_dimension):
    ### Divide chromosome into chunks for each layer.
    chunks = divide_chunks(individual, 9)
    #print('chunks: ', chunks)

    ### Set previous x and y dimensions equal to the original x and y dimensions.
    ### (the x and y dimensions of the data set before the first layer.)

    previous_x_dimension = original_x_dimension
    previous_y_dimension = original_y_dimension

    ### Start a list for the modified individual. (The modified individual has its kernal sizes
    ### modified if the kernal size is invalid. Saves the unmodified individual if the kernal
    ### size is valid.)
    modified_individual = []

    ### Iterate over the layers.
    for chunk in chunks:
        ### Get the kernal size for the x and y dimensions.
        kernel_x = chunk[2]
        kernel_y = chunk[3]

        ### Check if the kernal size is greater than the dimension size. The kernel size
        ### needs to be less than or equal to the dimension size minus 1. If the kernal
        ### size is too large, generate a random number between 0 and 1 and take the floor
        ### of that number times the dimension size. This gives a kernal size that is
        ### less than the dimension size.

        if kernel_x > previous_x_dimension - 1:
            kernel_x_ratio = np.random.uniform(0, 1)
            kernel_x = int(math.floor(kernel_x_ratio * previous_x_dimension))
        if kernel_y > previous_y_dimension - 1:
            kernel_y_ratio = np.random.uniform(0, 1)
            kernel_y = int(math.floor(kernel_y_ratio * previous_y_dimension))

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

        chunk[2] = kernel_x
        chunk[3] = kernel_y

        ### Save modified chunk to the new chromosome.
        modified_individual += chunk

    ### Create the modified individual using keras.creator.Individual.
    modified_individual = creator.Individual(modified_individual)

    return modified_individual


def layer():                            ### Return random integer between 0 and 2 for layer type.
    return np.random.randint(3)
def nodes():                            ### Return random integer between 2 and 100 for number of nodes for layer.
    #return np.random.randint(2, 101)
    return 2
def get_kernel_x(kernel_x):             ### Return kernel size for x dimension (not sure why I did this).
    return kernel_x
def get_kernel_y(kernel_y):             ### Return kernel size for y dimension (not sure why I did this).
    return kernel_y
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

### Extract training data.
with open('../x_train.pkl', 'rb') as pkl_file:
    x_train = pickle.load(pkl_file, encoding = 'latin1')

### Get dimension of data (size of x and y dimensions).
original_x_dimension = x_train.shape[1]
original_y_dimension = x_train.shape[2]
previous_x_dimension = original_x_dimension
previous_y_dimension = original_y_dimension

### Not sure what this does besides setting the weights for each objective function.
#creator.create('FitnessMax', base.Fitness, weights=(1, 1, 1))
creator.create('FitnessMax', base.Fitness, weights=(1., 1., 1., 1., 1.))
creator.create('Individual', list, fitness=creator.FitnessMax)

toolbox = base.Toolbox()
### Create a string of a command to be executed to register a 'type' of individual.
### The 'type' of individual depends on how many layers the individual has.
toolbox_ind_str = "toolbox.register('individual', tools.initCycle, creator.Individual, ("

### Set number of layers.
#num_layers = 10
num_layers = 1
#num_layers = 20

### Iterate over the number of layers and append to string to be executed.
for n in range(num_layers):
    layer_str = 'layer_' + str(n)
    nodes_str = 'nodes_' + str(n)
    kernel_x_str = 'kernel_x_' + str(n)
    kernel_y_str = 'kerner_y_' + str(n)
    act_str = 'act_' + str(n)
    use_bias_str = 'use_bias_' + str(n)
    bias_init_str = 'bias_init_' + str(n)
    bias_reg_str = 'bias_reg_' + str(n)
    act_reg_str = 'act_reg_' + str(n)

    toolbox.register(layer_str, layer)
    toolbox.register(nodes_str, nodes)

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

    toolbox.register(kernel_x_str, get_kernel_x, kernel_x)
    toolbox.register(kernel_y_str, get_kernel_y, kernel_y)
    toolbox.register(act_str, act)
    toolbox.register(use_bias_str, use_bias)
    toolbox.register(bias_init_str, bias_init)
    toolbox.register(bias_reg_str, bias_reg)
    toolbox.register(act_reg_str, act_reg)

    toolbox_ind_str += 'toolbox.' + layer_str + ', toolbox.' + nodes_str + ', toolbox.' + kernel_x_str + ', toolbox.' + kernel_y_str + ', toolbox.' + act_str + ', toolbox.' + use_bias_str + ', toolbox.' + bias_init_str + ', toolbox.' + bias_reg_str + ', toolbox.' + act_reg_str
    if n != num_layers-1:
        toolbox_ind_str += ", "

toolbox_ind_str += "), n=1)"

### Execute string to register individual type.
exec(toolbox_ind_str)

### Register population, mate, mutate, select, and evaluate functions.
toolbox.register('population', tools.initRepeat, list, toolbox.individual)
toolbox.register('mate', tools.cxTwoPoint)
toolbox.register('mutate', myMutation)
toolbox.register('select', tools.selNSGA2)
toolbox.register('evaluate', evaluate)

### Create lists to keep track of the population and fitnesses.
population_list = []
fitness_list = []

data_directory_name = 'data/{0}/{0}{1:02d}/{0}{1:02d}{2:02d}/'.format(year, month, day)
if not os.path.isdir(data_directory_name):
    os.makedirs(data_directory_name)

if not os.listdir(data_directory_name):
    next_dir_number = 1

else:
    last_dir_name = sorted(os.listdir(data_directory_name))
    last_dir_number = int(last_dir_name[-1])
    next_dir_number = last_dir_number + 1

data_date_dir_name = 'data/{0}/{0}{1:02d}/{0}{1:02d}{2:02d}/'.format(year, month, day)

def main():
    population_size = 8
    selection_size = 4
    cross_over_size = population_size - selection_size

    print('Setting up population.\n')

    ### Set population size.
    pop = toolbox.population(n=population_size)
    print('init pop: ')
    for p in pop:
        print(p)

    '''
    population_indices = np.arange(0, selection_size)
    possible_pairs_of_parents = list(itertools.permutations(population_indices, 2))
    print(possible_pairs_of_parents)
    '''

    ### Set crossover probability, mutation probability, and number of generations.
    MUTPB, NGEN = .5, 2

    fitnesses = list( toolbox.map(toolbox.evaluate, pop) )

    for ind, fit in zip(pop, fitnesses):
        ind.fitness.values = fit

    ####generation_dir_name = data_date_dir_name + '{0:04d}/generation_00000/'.format(next_dir_number)
    ####if not os.path.isdir(generation_dir_name):
    ####    os.makedirs(generation_dir_name)

    ####generation_population_file_name = generation_dir_name + '{0}{1:02d}{2:02d}_{3:04d}_generation_00000_population.pkl'.format(year, month, day, next_dir_number)
    ####with open(generation_population_file_name, 'wb') as fil:
    ####    pickle.dump(pop, fil)

    ####generation_fitness_file_name = gneration_dir_name + '{0}{1:02d}{2:02d}_{3:04d}_generation_00000_fitness.pkl'.format(year, month, day, next_dir_number)
    ####with open(generation_fitness_file_name, 'wb') as fil:
    ####    pickle.dump(fitnesses, fil)

    ### Iterate over the generations.
    for g in range(1, NGEN):

        selected_parents = toolbox.select( pop, selection_size )
        print('selected_parents: ')
        for s in selected_parents:
            print(s)

        print('Generation {} ... \n'.format(g))

        #print(possible_pairs_of_parents)
        ### Select offspring.
        #mating_pair_indices = random.sample(possible_pairs_of_parents, int(float(selection_size)/2) )

        new_children = []
        '''
        for p, pair in enumerate([ (selected_parents[m[0]], selected_parents[m[1]]) for m in mating_pair_indices]):
            r = np.random.uniform(0, 1)
            if r <= CXPB:
                child1, child2 = toolbox.mate(pair[0], pair[1])
                child1, child2 = toolbox.clone(child1), toolbox.clone(child2)
                del child1.fitness.values
                del child2.fitness.values
                new_children.append(child1)
                new_children.append(child2)
            else:
                clone1, clone2 = toolbox.clone(pair[0]), toolbox.clone(pair[1])
                del clone1.fitness.values
                del clone2.fitness.values
                new_children.append(clone1)
                new_children.append(clone2)
        '''
        for c in range(cross_over_size):
            parent1, parent2 = random.sample(selected_parents, 2)
            parent1, parent2 = toolbox.clone(parent1), toolbox.clone(parent2)
            child1, child2 = toolbox.mate(parent1, parent2)
            new_children.append(child1)

        #print('new_children: ')
        #for c in new_children:
        #    print(c)

        #for p in pop:
        #    print(p)
        #print('\n\n')

        #pop = selected_parents + new_children

        print('selected_parents: ')
        for s in selected_parents:
            print(s)
        print('new_children: ')
        for c in new_children:
            print(c)

        for p in pop:
            if p in selected_parents:
                print('yes selected')
            elif p in new_children:
                print('yes new')

        for p in pop:
            print(p)

        #for m, mutant in enumerate(new_children):
        #    r = np.random.uniform(0, 1)
        #    if r <= MUTPB:
        #        new_children[m] = toolbox.mutate(mutant)

        new_children = [check_kernel_validity(ind, original_x_dimension, original_y_dimension) for ind in new_children]

        #for ind in pop:
            #print(ind, ind.fitness.values)
            #print(ind)

        #fitnesses = list( map(toolbox.evaluate, selected_pop) )
        #for ind, fit in zip(pop, fitnesses):
        #    ind.fitness.values = fit

    ####return pop, fitnesses
    return pop
    #return population_list, fitness_list

# main()
####pop, fitnesses = main()
pop = main()
#population_list, fitness_list = main()
#data = [population_list, fitness_list]


#print('final_population: {}'.format(pop) )
#print('final_fitnesses: {}'.format(fitnesses) )