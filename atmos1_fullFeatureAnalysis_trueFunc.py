# -*- coding: utf-8 -*-
"""
Created on Tue Jan 31 11:45:49 2017

@author: cssilva

Version
"""

# ATMOS 1 - plotting the spectral features of individual functionals within molecules

import sys
import math
import matplotlib.pyplot as plt
import numpy as np
from enum import Enum
import cPickle as pickle
import re

boltzmann = 1.38064852 * (10**(-23))
light_speed = 2.998 * 10**8
plank = 6.626070040 * (10**(-34))
cm1_joules = 5.03445 * 10**(22)

temperature = 300.0


# intensity_centre = 1.0
# freq_centre = 0.0
# bcon = float(10**(45)*(plank/(8*math.pi*math.pi*light_speed*5)))
# jmax = int(0.5 * (np.sqrt(((2*boltzmann*temperature)/(bcon*10**(-24))))) - 0.5)
# #
# for j in range(0, jmax):
#     dcon = (bcon * 10 ** (-3)) / (j + 1)
#     dcon_plus = (bcon * 10 ** (-3)) / (j + 2)
#     spacing = 2*bcon - ((4 * dcon_plus)*((j + 2)**3)) + ((4 * dcon)*((j + 1)**3))
#     intensity_j = intensity_centre * 5 * ((2 * j) + 1) * (10 ** (-2)) * np.e**(-(((bcon*10**(-24)) * (2 * j) * ((2*j) + 1)) / (boltzmann * temperature)))
#     position_j_pbranch = freq_centre - spacing
#     position_j_qbranch = freq_centre + spacing
#     print 'pbranch', j, position_j_pbranch, intensity_j
#     print 'qbranch', j, position_j_qbranch, intensity_j
# #




class Molecule:
    
    def __init__(self, code):
        self.code = code
        self.functionals = []

    def addFunctional(self, functional, number):
        self.functionals.append((functional, number))

    def contains(self, element_name):
        return self.code.contains(elements[element_name])

    def line_shapes(self):
        lines = []

        for functional_tuple in self.functionals:
            functional = functional_dictionary[functional_tuple[0]]
            for symmetry in functional.symmetries:
                for property in symmetry.properties:
                    x = np.linspace(property.low, property.high)
                    y = functional.line_function(x, property.frequency_average(), property.intensity.value)
                    lines.append((x, y))
                    
        return lines

    def branches(self):
        branches = []

        for functional_tuple in self.functionals:
            functional = functional_dictionary[functional_tuple[0]]
            for symmetry in functional.symmetries:
                for property in symmetry.properties:
                    branches.append(self.prBranches(property))

        return branches

    def atom_count(self):
        atoms = len(re.sub(r"[^A-Z]+",'',self.code))

        return atoms

    def prBranches(self, property):
        pr_branch_x = []
        pr_branch_y = []

        bcon = float(plank / (8 * math.pi * math.pi * light_speed * self.atom_count() * 10**(-44)))
        jmax = int(np.sqrt((boltzmann * temperature)/(2 * plank * light_speed * bcon)) - 0.5)

        for j in range(0, jmax):
            dcon = (bcon * 10 ** (-3)) / (j + 1)
            dcon_plus = (bcon * 10 ** (-3)) / (j + 2)
            spacing = 2 * bcon - ((4 * dcon_plus) * ((j + 2) ** 3)) + ((4 * dcon) * ((j + 1) ** 3))
            intensity_j = property.intensity.value * ((2* j) + 1) * np.e**(-((plank * light_speed * bcon * j * (j + 1))/(boltzmann * temperature)))

            position_j_pbranch = property.frequency_average() - spacing
            position_j_rbranch = property.frequency_average() + spacing
            pr_branch_x.append(position_j_pbranch)
            pr_branch_y.append(intensity_j)
            pr_branch_x.append(position_j_rbranch)
            pr_branch_y.append(intensity_j)

        return (pr_branch_x, pr_branch_y)

    def average_points(self):
        points = []

        for functional_tuple in self.functionals:
            functional_code = functional_tuple[0]
            if functional_code in functional_dictionary.keys():
                functional = functional_dictionary[functional_code]
                for symmetry in functional.symmetries:
                    for property in symmetry.properties:
                        points.append((property.frequency_average(), property.intensity.value))
                
        return points
    
    def high_and_low_frequencies(self):
        frequencies = []

        for functional_tuple in self.functionals:
            functional_code = functional_tuple[0]
            if functional_code in functional_dictionary.keys():
                functional = functional_dictionary[functional_code]
                for symmetry in functional.symmetries:
                    for property in symmetry.properties:
                        frequencies.append((property.low, property.high, property.intensity.value))
                    
        return frequencies
    

class Functional:
    
    def __init__(self, code, a = 1, b = 1):
        self.code = code
        self.a = a
        self.b = b
        self.symmetries = []

    def addSymmetry(self, symmetry):
        symmetry.functional = self
        self.symmetries.append(symmetry)

    def line_function(self, x, translateX, scaleY):
        print("Calculating graph for functional '" + self.code + "': using default f()")

        return (1/(1+pow((x - translateX),2))) * scaleY



# Specify a subclass of functional that has a different graphing function
class ExpFunctional(Functional):
    
    def line_function(self, x, translateX, scaleY):
        print("Calculating graph for functional '" + self.code + "': using exp f()")
        return (self.a * np.exp(-pow((x - translateX), 2))) * scaleY

class Symmetry:
    
    def __init__(self, type):
        self.type = type
        self.properties = []

    def addProperty(self, property):
        
        property.symmetry = self
        self.properties.append(property)

class Property:
    
    def __init__(self, low, high, intensity):
        self.low = low
        self.high = high
        self.intensity = intensity

    def frequency_average(self):
        return np.mean([self.high,self.low])
#        return self.low + ((self.high - self.low) / 2)

class Intensity(Enum):
    
    w,w_m,m,m_s,s = 1,1.5,2,2.5,3

    @classmethod
    def fromString(self, str):
        if str == 's':
            return Intensity.s
        elif str == 'm_s':
            return Intensity.m_s
        elif str == 'm':
            return Intensity.m        
        elif str == 'w_m':
            return Intensity.w_m
        elif str == 'w':
            return Intensity.w

# Load Functionals

# Example data
# COC C-O-C sbend 2500 2720 weak
# COC C-O-C abend 2800 2920 strong

functional_dictionary = {}
#functional_data = open('func_table_reliable.txt', "r")

with open('func_testvim.spaces') as f:
    functional_data = f.readlines()
    
print len(functional_data)
#this bit isnt working, maybe because the file does not have normal spacing?
for line in functional_data:
    columns = line.strip().split()
    
    code = columns[0]
#    name = columns[1]
    symmetry_name = columns[1]
    low = float(columns[2])
    high = float(columns[3])
    intensity = Intensity.fromString(columns[4])

    if not functional_dictionary.has_key(code):
        # Extra logic for determining which type of functional we are dealing with.
        if "CF" in code:
            f = ExpFunctional(code, 2) # in this case we are setting 'a' for this functional's graphing function to 2.
        else:
            f = Functional(code)

        functional_dictionary[code] = f

    symmetry = Symmetry(symmetry_name)
    
    property = Property(low, high, intensity)

    functional_dictionary[code].addSymmetry(symmetry)
    symmetry.addProperty(property)


#looks through all of the plottable molecules
plotables = []
plotable_molecules = open('plotable_molecules', "r")
for line in plotable_molecules:
    columns = line.strip().split()
    
    plotables.append(columns[0])
#print 'Plotables', plotables


# Load Molecules
#print functional_dictionary.keys()

molecules = {}
#molecule_dictionary = pickle.load(open("dict_sorted_results_func_intra_test2_numbers.p", "rb"))
molecule_dictionary = pickle.load(open("dict_sorted_results_func_intra_table_part.p", "rb"))
#print 'test molecule', molecule_dictionary['[H]OC([H])(C)C']
print 'Molecule dictionary sample', molecule_dictionary.items()[:5]
print 'Functionals for molecule C(C)NCC(O)', molecule_dictionary.get('C(C)NCC(O)')
print '\n', 'Number of molecules', len(molecule_dictionary.items())

# for molecule_code, molecule_functionals in molecule_dictionary.iteritems():
#     if len(molecule_dictionary.get(molecule_code)) >= 12:
#         if molecule_code in plotables:
#             print molecule_code, ' with ',len(molecule_dictionary.get(molecule_code)), ' functionals'
#         else:
#             print molecule_code, 'no linelist but these functionals:', molecule_dictionary.get(molecule_code)


#[H]OP([H])([!#1])=O
#Functional for HCN, specifically for the ≡C-H bending and stretching motions, is '[H]C#C[!#1]'

for molecule_code, molecule_functionals in molecule_dictionary.iteritems():
     if len(molecule_dictionary.get(molecule_code)) >= 1:
        if any('[H]OP(=O)(O[H])OC([H])([H])[H]' in s for s in molecule_dictionary.get(molecule_code)) :
            if molecule_code in plotables:
                print molecule_code, ' with ', len(molecule_dictionary.get(molecule_code)), ' functionals'
            else:
                print molecule_code, 'no linelist but these functionals:', molecule_dictionary.get(molecule_code)

molecules_with_triplebondCH = []
for molecule_code, molecule_functionals in molecule_dictionary.iteritems():
     if any('[H]C#C[!#1]' in s for s in molecule_dictionary.get(molecule_code)):
         #print molecule_code, 'has ≡C-H functional and all these other functionals:', molecule_dictionary.get(molecule_code)
         molecules_with_triplebondCH.append(molecule_code)

print len(molecules_with_triplebondCH), 'molecules have a similar ≡C-H functional'
print molecules_with_triplebondCH

molecules_with_triplebondCH_and_spectra = []
for molecule_code in molecules_with_triplebondCH:
    if molecule_code in plotables:
        print molecule_code, 'has spectra'
        molecules_with_triplebondCH_and_spectra.append(molecule_code)
    else:
        print molecule_code, 'no linelist '

print len(molecules_with_triplebondCH_and_spectra), 'molecules have a similar ≡C-H functional and spectra'
print molecules_with_triplebondCH_and_spectra

for molecule_code, molecule_functionals in molecule_dictionary.iteritems():
    molecule = Molecule(molecule_code)

    for functional_tuple in molecule_functionals:
        if '#' in functional_tuple[0]:
            
            functional_code = functional_tuple[0]
            functional_incidence = functional_tuple[1]
            molecule.addFunctional(functional_code, functional_incidence)

    molecules[molecule_code] = molecule

#co2 atmosphere
co2_atmosphere= [(420.4,524.0),(822.4,922.8),(992.8,1092.8),(1099.6,1890.0),(1941.6,2042.0),(2162.0,2262.0),
              (2420.0,3482.0),(3784.0,4736.0),(5172.0,6072.0),(6122.0,6222.0),(6266.0,6366.0),
              (6386.0,6892.0),(7014.0,8176.0),(8208.0,8308.0)]

#Earth atmosphere
earth_atmosphere = [(430.4,530.4),(530.8,630.8),(705.2,1335.6),(1344.0,1444.0),(1585.6,1685.6),
                    (1816.0,1916.0),(1928.0,2284.0),(2404.0,3504.0),(3514.0,3614.0),
                    (3976.0,5208.0),(5490.0,7116.0),(7132.0,7232.0)]
earth2_atmosphere = [(802.8,972.4),(2402.0,2796.0),(4434.0,4806.0),(5626.0,6702.0)] #plus out of range windows between 7540.0-14765.0



#Methane atmosphere
methane_atmosphere= [(420.4,1042.4),(1044.4,1144.4),(1861.6,2272.0),(3320.0,3636.0),
                    (4754.0,5082.0),(5158.0,5258.0),(6268.0,6610.0),(6612.0,6712.0),
                    (7704.0,8116.0),(8144.0,8244.0),(9058.0,11020.0)]

#features of HCN, approximately. See hcn.agr for spectra at three resolutions
hcn_regions= [(0.0,100.0),(600.0,820.0),(1340.0,1500.0),(3200.0,3400.0)]
hcn_strong = [(0.0,100.0),(600.0,820.0)]
hcn_strong_infrared = [(600.0,820.0)]

# print co2_windows[0][0] gives the first item of the first tuple (low freq of the first window)

# Finds all the strong features whose average frequency is within a window
atmosphere = hcn_strong_infrared
window_molecules = []
strong_window_molecules = []


for molecule_code in molecules:
    molecule = molecules[molecule_code]

#    for frequency in molecule.high_and_low_frequencies():
#            print frequency[0]
    for window in atmosphere:
        
        window_low = window[0]
        window_high = window[1]
        for molecule_point in molecule.high_and_low_frequencies():
            low_frequency = molecule_point[0]
            high_frequency = molecule_point[1]
            point_intensity = molecule_point[2]
            if window_low < low_frequency < window_high and window_low < high_frequency < window_high:
                window_molecules.append(molecule.code)
                if  point_intensity >= 3:
                    strong_window_molecules.append(molecule_code)
                    
print 'Window range: from ',atmosphere[0][0], ' to ', atmosphere[-1][1]
print 'Number of molecules in window', len(set(window_molecules))
print 'Number of strong molecules in window', len(set(strong_window_molecules))
                    
#                for point in window_filtered_list:
#  #      print point
#                window_molecules.append(molecule.code)
#                if point[1] >= 3:
                    
 #           window_filtered_list = list(filter(lambda x: ((window_low < low_frequency < window_high) and (window_low < high_frequency < window_high)), molecule.high_and_low_frequencies()))
            #print molecule.high_and_low_frequencies()[0][0],molecule.high_and_low_frequencies()[0][1], molecule.average_points()[0][0]
#    low_filtered_list = list(filter(lambda x: 600 < x[0] < 800, molecule.high_and_low_frequencies()[0]))
 

#and window_low < x[1] < window_high


#            print point
               
#    if len(window_filtered_list) > 0:
#        window_molecules.append(molecule.code)
#        print points
#        strong_filtered_list = list(filter(lambda y: y[1] == 3, points))
#        if len(strong_filtered_list) > 0:
#            strong_window_molecules.append(molecule_code)
        
#        print 'Molecule exits in window', molecule.code, (filtered_list)

#print 'List of Molecules', strong_window_molecules


#looks through all of the plottable molecules and sees which exist in window
count_exists = 0
count_doesnt_exist = 0
for mol in set(strong_window_molecules):
    if mol in plotables:
        count_exists = count_exists + 1
    else:
        count_doesnt_exist = count_doesnt_exist + 1
        
print count_doesnt_exist, 'do not have linelists'
print count_exists, 'have a linelist'


plotted_molecule = 'CN(OC#C)C'
example = molecules[plotted_molecule]
#print len(example.functionals)



# print example.atom_count()

# Plot points
xs, ys = zip(*example.average_points())
#print 'points', example.points()
#plt.plot(xs, ys, linestyle='None', marker='o', color='black', linewidth=2)

#window = range(3250, 3450)
filtered_list = list(filter(lambda x: 1600 < x[0] < 1900, example.average_points()))
#print 'filter:',(filtered_list)

print xs, ys
markerline, stemlines, baseline = plt.stem(xs, ys, '-')
plt.setp(baseline, 'color', 'r', 'linewidth', 1)

#Plot branches
#for line in example.branches():
#     x, y = line
#     markerline, stemlines, baseline = plt.stem(x, y, '-')
#     plt.setp(baseline, color='r', linewidth=1, marker='None')

#plt.xlim(1459,1459.5)
print 'Molecule below : ', plotted_molecule
plt.show()

# Plot lines
#for line in example.lines():
#    x, y = line

#    plt.plot(x, y)


