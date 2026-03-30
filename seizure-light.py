import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import ipywidgets as ipy
import networkx as nx
from matplotlib.animation import FuncAnimation
# from machine import Pin

n = 5
G = nx.grid_2d_graph(n, n)

nx.set_node_attributes(G, False, 'active')       # whether electrical signal has been passed through it
nx.set_node_attributes(G, 'blue', 'colour')      # a visual representation of the signal
nx.set_node_attributes(G, 0, 'timer')            # localised time attribute
nx.set_node_attributes(G, False, 'refractory')   # activating the refractory period for cells after having activated the timer
nx.set_node_attributes(G, 3, 'refractory_timer') # associated refractory timer in which nothing can happen to it

pos = nx.kamada_kawai_layout(G)

fig, ax = plt.subplots(figsize=(8,8))
node_collection = nx.draw_networkx_nodes(G, pos, ax=ax, node_size=50, node_color='blue')
nx.draw_networkx_edges(G, pos, ax=ax, alpha=0.08)
ax.set_axis_off()

flattened_state = np.zeros(n*n, dtype=int) # making a global variable for the flattened state rather than trying to unpack it from the main function

def neuron_abstraction_I(frame, graph_object, background_excitation=0.1, neighbouring_excitation=0.5, activation_timer=5, refractory_stopclock=4):
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
            nodes[node_key]['refractory'] = False
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
    

    # raspberry pi logic
    global flattened_state
    flattened_state = np.array([1 if nodes[node]['active'] else 0 for node in graph_object.nodes()]).flatten()
    print(flattened_state)
    
    """
    Using the neoplex thing for LED arrays (and making sure all the wiring is correct for the pinout and it won't draw too much current in the flickering efect, do a conditional loop.
    
    if index == 1:
        led[index].on()
    else:
        led[index].off()
        
    It's going to be some really simple code (esp. in comparison to the other one)
    """  
    
anim = FuncAnimation(fig, neuron_abstraction_I, fargs=(G, ), cache_frame_data=False, interval=500, blit=False) # blitting only draws the dynamic aspects of the plot
plt.show()
