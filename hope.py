# need to understand clearer the logic-shift converter and how to properly connect up the wires, the outgoing power line is confusing to me and I do not know if this code words with simple tests which needs to be tested with. 
# https://www.youtube.com/watch?v=4oA4KKxxBXE&t=110s
"""
Components used: 
- raspberry pi pico 2w
LEDs (find the strip on kitronik)
3.3 to 5 converter

The only issue would be how they are connected together

"""

from neopixel import Neopixel
import utime
import random

# SETUP
numpix = 49
state_machine = 0
pin_num = 28 # this is distinct to the GPIO pin, but adjust the pin number to ensure that this is the case

strip = Neopixel(numpix, state_machine, pin_num, "RGB")

white = (255, 255, 255)
blank = (0, 0, 0)

delay = 3
strip.brightness(50)

n = 7

# graph setup that replaces networkx by being a clearer dictionary format
nodes = {
    (i, j): {
        'active': False,
        'timer': 0,
        'refractory': False,
        'refractory_timer': 3
    }
    for i in range(n) for j in range(n)
}

def get_neighbors(node):
    i, j = node
    result = []
    for di, dj in [(-1,0),(1,0),(0,-1),(0,1)]:
        ni, nj = i+di, j+dj
        if 0 <= ni < n and 0 <= nj < n:
            result.append((ni, nj))
    return result


# SEIZURE MODEL
def neuron_abstraction_I(nodes, background_excitation=0.1, neighbouring_excitation=0.5, activation_timer=5, refractory_stopclock=4):

    for node in nodes:
        if nodes[node]['refractory']:
            nodes[node]['refractory_timer'] -= 1
            if nodes[node]['refractory_timer'] <= 0:
                nodes[node]['refractory'] = False
                nodes[node]['refractory_timer'] = refractory_stopclock

        if nodes[node]['active']:
            nodes[node]['timer'] += 1
            if nodes[node]['timer'] >= activation_timer:
                nodes[node]['active'] = False
                nodes[node]['refractory'] = True
                nodes[node]['timer'] = 0

    # background excitation 
    for node in nodes:
        if not nodes[node]['refractory'] and not nodes[node]['active']:
            if random.random() <= background_excitation:
                nodes[node]['active'] = True
                nodes[node]['timer'] = 0

    # neighbouring excitation
    all_active = [node for node in nodes if nodes[node]['active']]
    neighbours_to_activate = set()

    for neuron in all_active:
        for neigh in get_neighbors(neuron):
            if not nodes[neigh]['active'] and not nodes[neigh]['refractory']:
                if random.random() <= neighbouring_excitation:
                    neighbours_to_activate.add(neigh)

    for neighbour in neighbours_to_activate:
        nodes[neighbour]['active'] = True
        nodes[neighbour]['refractory'] = False
        nodes[neighbour]['timer'] = 0

    flattened_state = [1 if nodes[node]['active'] else 0 for node in nodes]
    return flattened_state


# PROGRAM LOOP
print("start, debugging test")
while True:
    output_state = neuron_abstraction_I(nodes)

    for i in range(len(output_state)):
        if output_state[i] == 1:
            colour = white
        else:
            colour = blank
        strip.set_pixel(i, colour)

    strip.show()
    print("instance")
    utime.sleep(delay)
