from neopixel import Neopixel
import utime
import random
import numpy as np
import pandas as pd
import networkx as nx

# SETUP
'''
Defining the parameters for both the graph display (omitting the visualisation modules) and the raspberry pi
'''

## raspberry pi setup

numpix = 49
state_machine = 0 
pin_num = 28

strip = Neopixel(numpix, state_machine, PIN_NUM, "RGB")

white = (255, 255, 255)
blank = (0,0,0)

delay = 0.5 # seconds
strip.brightness(500) # what is this scale?

## graph setup
n = 5
G = nx.grid_2d_graph(n, n)

nx.set_node_attributes(G, False, 'active')       # whether electrical signal has been passed through it
nx.set_node_attributes(G, 'blue', 'colour')      # a visual representation of the signal
nx.set_node_attributes(G, 0, 'timer')            # localised time attribute
nx.set_node_attributes(G, False, 'refractory')   # activating the refractory period for cells after having activated the timer
nx.set_node_attributes(G, 3, 'refractory_timer') # associated refractory timer in which nothing can happen to it


# SEIZURE MODEL DEFININTION
'''
Defining the main seizure model, which will be called iteratively later
'''
def neuron_abstraction_I(graph_object, background_excitation=0.1, neighbouring_excitation=0.5, activation_timer=5, refractory_stopclock=4):
    """
    1. Check all activate cells without any changes and see if the timer has exceeded the limit and with the refractory period
    (refractory cells are effectively removed from this graph for this period e.g. available_neurons = [neuron['refractory'=False] for neuron in G])
    2. Apply the background activation
    3. Apply the neighbouring cell thing
    4. Update characteristics
    """
    nodes = graph_object.nodes()

    for node in nodes:
        # 'refractory_neuron' countdown
        if nodes[node]['refractory']:
            nodes[node]['refractory_timer'] -= 1
            if nodes[node]['refractory_timer'] <= 0:
                nodes[node]['refractory'] = False
                nodes[node]['refractory_timer'] = refractory_stopclock  # reset

        # 'active_neuron' timer
        if nodes[node]['active']:
            nodes[node]['timer'] += 1
            if nodes[node]['timer'] >= activation_timer:
                nodes[node]['active'] = False
                nodes[node]['colour'] = 'blue'
                nodes[node]['refractory'] = True
                nodes[node]['timer'] = 0

    inactive_non_refractory_neurons = [node for node in nodes if not nodes[node]['refractory']] # returns non-refractory neurons - not sure whether inactive ones should be included yet

    # For the background probability, I am going to apply a Bernoulli mask as shown in the percolation video
    neuron_array = np.array(nodes)
    n_neurons = len(neuron_array)
    rand_prob = np.random.rand(n_neurons)
    selection_mask = np.where(rand_prob <= background_excitation)[0]
    activation_mask = neuron_array[selection_mask]

    for node_array in activation_mask:
        node_key = tuple(node_array) # only tuples are hashable
        if not nodes[node_key]['refractory']:
            nodes[node_key]['active'] = True
            nodes[node_key]['colour'] = 'red'
            nodes[node_key]['timer'] = 0

    '''
    For neighbouring activation, find all active cells and make a list of all of their neighbours (which aren't active themselves)
    Then apply the same Bernoulli mask (different values, same principle) and activate them

    The issue with the initial function was that the for loop would be such that the neighbouring neurons could activate recursively, rather than having a mechanism that would store it to know which
    '''

    all_activated_neurons = [node for node in nodes if nodes[node]['active']]

    # Use a set to collect the keys of the neighbours to activate,
    # without recursively activating neighbours in a single time step
    neighbours_to_activate = set()

    if all_activated_neurons:
        for neuron in all_activated_neurons:
            eligible_neighbours = [
                neigh for neigh in graph_object.neighbors(neuron)
                if not nodes[neigh]['active'] and not nodes[neigh]['refractory']
            ]

            if not eligible_neighbours:
                continue # different to pass

            eligible_neighbours_array = np.array(eligible_neighbours, dtype=object) # dtype=object makes the array act like a typical pythonic list
            n_eligible = len(eligible_neighbours_array)

            # applying the bernoulli mask (as usual)
            rand_prob = np.random.rand(n_eligible)
            bernoulli_mask = np.where(rand_prob <= neighbouring_excitation)[0]

            eligible_neighbour_keys = eligible_neighbours_array[bernoulli_mask]
            for key in eligible_neighbour_keys:
                neighbours_to_activate.add(tuple(key))  # Convert array to tuple

    for neighbour in neighbours_to_activate:
        nodes[neighbour]['active'] = True
        nodes[neighbour]['colour'] = 'red'
        nodes[neighbour]['refractory'] = False
        nodes[neighbour]['timer'] = 0

    colours = [nodes[node]['colour'] for node in graph_object.nodes()]
    node_collection.set_color(colours)
    
    # raspberry pi logic -- just returns what is necessary for the raspberry pi logic
    flattened_state = np.array([1 if nodes[node]['active'] else 0 for node in graph_object.nodes()]).flatten()
    return flattened_state

# PROGRAM LOOP
'''
The actual main code for this.
'''

while True:
    # call function 
    output_state = neuron_abstraction_I(G)
    
    # assigning each of the colours to each other pixels
    # there should be a way to do this simultaneously but not too fussed
    for i in range(n):
        if output_state[i] == 1:
            colour = white # set brightness outside of loop
        if output[i] == 0:
            colour = blank # just set the colour to be nothing so (0,0,0)
        strip.set_pixel(i, colour)
        
    strip.show()
    utime.sleep(delay) # set a delay that is roughly the same (slightly longer than) the animate function
 

