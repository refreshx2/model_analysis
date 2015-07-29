
# Categorizes the voronoi polyhedra according to the input parameter file, 
# which must be the first arg passed to this script.
# The second arg must be a _index.out file.
# Output is printed to screen.

import sys, math, copy
from collections import OrderedDict
from znum2sym import z2sym
import vor
from model import Model
from voronoi_3d import voronoi_3d
from vor import Vor, fortran_voronoi_3d
from recenter_model import recenter_model
from nearest_atoms import find_center_atom

""" Functions:
load_index_file(indexfile)
load_param_file(paramfile)
generate_atom_dict(indexes,vp_dict)
categorize_atoms(m,paramfile)
categorize_index(ind, vp_dict)
set_atom_vp_types(model,vp_dict)
vor_stats(m)
print_all(m)
save_vp_cluster_with_index(m,index) """


def load_index_file(indexfile):
    """ Simply reads in an index file into a list and returns it """
    with open(indexfile) as f:
        index = f.readlines()
    return index

def load_param_file(paramfile):
    """ Returns a dictionary in the form:
        {'Crystal-like': [[0, 4, 4, '*'], [0, 5, 2, '*']], 
        'Icosahedra-like': [[0, 2, 8, '*'], [0, 1, 10, '*'], [0, 0, 12, 0], [0, 0, 12, 2]],
        'Mixed': [[0, 3, 6, '*'], [0, 3, 7, 2], [1, 2, 5, 4]]} """
    # Open the input parameter file. Should be of the form:
    # Crystal:
    #     0,2,8,*
    #with open(paramfile) as f:
    #    vp_params = [line.split(',') for line in f]
    vp_params = open(paramfile).readlines()
    # For each voronoi polyhedra 'structure', change it to an int if it's not a *
    vp_dict = {}
    for line in vp_params:
        if(':' in line): # Title line
            current_entry = line.strip()[:-1]
            vp_dict[current_entry] = []
        else: # Index line
            vps = line.strip().split(',')
            vps = [x.strip() for x in vps] # remove spaces if ", " rather than just ","
            for i in range(len(vps)):
                if(vps[i] != '*'):
                    vps[i] = int(vps[i])
            vp_dict[current_entry].append(vps)
    return vp_dict

def generate_atom_dict(model):
    """ Generate a new dictionary to store all the atoms that are crystalline, icosahedra, etc.
    Returns a dictionary in the form:
    { 'Mixed:': [list of mixed atoms], 'Crystal-like:', [list of crystal-like atoms], etc}.
    All atoms must be assigned a VP type prior to this function. """
    atom_dict = {}
    for atom in model.atoms:
        atom_dict[atom.vp.type] = atom_dict.get(atom.vp.type,[]) + [atom]
    return atom_dict


def categorize_atoms(m,paramfile):
    """ Shortcut to run load_param_file
    and set_atom_vp_types in one function.
    Also stores vp_dict in the model. """
    vp_dict = load_param_file(paramfile)
    set_atom_vp_types(m,vp_dict)
    m.vp_dict = vp_dict

def categorize_index(ind, vp_dict):
    """ ind should be an integer list
    vp_dict is returned by load_param_file.
    This function returns the type of index
    that ind is given vp_dict. """
    for key in vp_dict:
        for vps in vp_dict[key]:
            found = True
            for i in range(0,4):
                if(vps[i] != '*' and vps[i] != ind[i]):
                    found = False
            if(found):
                return key
    return 'Undef'

def set_atom_vp_types(model,vp_dict):
    """ saves the voronoi polyhedra type for each atom to the atom in the model """
    for atom in model.atoms:
        atom.vp.type = categorize_index(atom.vp.index,vp_dict)


def vor_stats(m):
    """ Prints the number of atoms in each VP category """
    cats = {}
    for atom in m.atoms:
        if atom.vp.type not in cats:
            cats[atom.vp.type] = {}
        cats[atom.vp.type][atom.sym] = cats[atom.vp.type].get(atom.sym,0) + 1
        cats[atom.vp.type]["Total"] = cats[atom.vp.type].get("Total",0) + 1
    # Print
    for key in sorted(cats):
        print("{0}:\nTotal:\t{1}\t{2}%".format(key,cats[key]["Total"], round(100.0*cats[key]["Total"]/m.natoms,2)))
        for elem in sorted(cats[key]):
            #if(elem != "Total"): print("   {0}: {1}".format(elem,cats[key][elem]))
            if(elem != "Total"):
                print("{0}:\t{1}\t{2}%".format(elem, cats[key][elem],
                    round(100.0*cats[key][elem]/cats[key]['Total'],2)))
    return cats

def index_stats(m):
    """ Prints the number of atoms in each VP index"""
    cats = {}
    for atom in m.atoms:
        #if atom.sym == 'Zr' or atom.sym == 'Al': continue
        #if atom.sym == 'Zr' or atom.sym == 'Cu': continue
        if atom.vp.index not in cats:
            cats[atom.vp.index] = OrderedDict()
            for typ in sorted([z2sym(x) for x in m.atomtypes], reverse=True):
                cats[atom.vp.index][typ] = 0
        cats[atom.vp.index][atom.sym] = cats[atom.vp.index].get(atom.sym,0) + 1
        cats[atom.vp.index]["Total"]  = cats[atom.vp.index].get("Total",0) + 1
    # Print
    for val,key in sorted( ((v,k) for k,v in cats.iteritems()), key=lambda t: t[0]['Total']): 
        #for atom in m.atoms:
        #    if(atom.vp.index == key):
        #        typ = atom.vp.type
        #        break
        #print("{0}: \t{1}\t{2}".format(key,val,typ))
        #if list(key)[0:4] != [0,2,8,0]:
        #    continue
        if val['Total'] < m.natoms*0.005: continue
        val = [(k,value) for k,value in val.items()]
        val = [str(x) for row in val for x in row]
        val = '\t'.join(val)
        print("{0}: \t{1}".format(key,val))
        #print("{0}: \t{1}\t{2}".format(key,val,round(val['Total']/float(m.natoms)*100,3)))
    return cats



def print_all(m):
    """ Prints the index and type of each atom in m """
    for atom in m.atoms:
        print("{0} {1} {2}".format(atom,atom.vp.index,atom.vp.type))

def save_vp_cluster_with_index(m,index):
    """ Index should be a 4-list, e.g. [0,0,12,0].
    This function goes thru the model and finds all
    atoms with index "index" and saves that atom's
    VP as a new model, with name "temp{atom.id}.cif """
    for atom in m.atoms:
        if(atom.vp.index[0:4] == index):
            temp_model = Model("VP with index {0}".format(index), m.lx, m.ly, m.lz, atom.neighs+[atom])
            temp_model.write_cif("temp{0}.cif".format(atom.id))
            print("Saved VP cluster to modelfile temp{0}.cif".format(atom.id))


def dist(atom1,atom2):
    x = (atom1.coord[0] - atom2.coord[0])
    y = (atom1.coord[1] - atom2.coord[1])
    z = (atom1.coord[2] - atom2.coord[2])
    return math.sqrt(x**2+y**2+z**2)

def fix_cluster_pbcs(m):
    # First recenter to first octant
    recenter_model(m)
    meanx, meany, meanz = m.lx/4.0, m.ly/4.0, m.lz/4.0
    for atom in m.atoms[1:]:
        atom.coord = (atom.coord[0]+meanx-m.atoms[0].coord[0], atom.coord[1]+meany-m.atoms[0].coord[1], atom.coord[2]+meanz-m.atoms[0].coord[2])
    m.atoms[0].coord = (m.atoms[0].coord[0]+meanx-m.atoms[0].coord[0], m.atoms[0].coord[1]+meany-m.atoms[0].coord[1], m.atoms[0].coord[2]+meanz-m.atoms[0].coord[2])

    # See if we need to fix
    fix = False
    for atom in m.atoms[1:]:
        if round(m.dist(m.atoms[0], atom)) != round(dist(m.atoms[0], atom)):
            fix = True
            break
    else:
        recenter_model(m)
        return m
    # If so, fix
    for atom in m.atoms:
        new = []
        if round(m.dist(m.atoms[0], atom)) != round(dist(m.atoms[0], atom)):
            for c in atom.coord:
                if c < 0:
                    new.append(c+m.lx)
                elif c > m.lx:
                    new.append(c-m.lx)
                else:
                    new.append(c)
            atom.coord = copy.copy(new)
    recenter_model(m)
    return m

def normalize_bond_distances(m):
    """ Rescales a cluster so that the average bond length is 1.0 """
    center = find_center_atom(m)
    for atom in m.atoms:
        atom.coord = (atom.coord[0]-center.coord[0], atom.coord[1]-center.coord[1], atom.coord[2]-center.coord[2])

    avg = 0.
    for atom in m.atoms:
        if atom.id != center.id:
            avg += m.dist(center, atom)
    avg /= (m.natoms-1)
    for atom in m.atoms:
        if atom.id != center.id:
            atom.coord = (atom.coord[0]/avg, atom.coord[1]/avg, atom.coord[2]/avg)
    recenter_model(m)
    return avg


def main():
    # sys.argv == [categorize_parameters.txt, modelfile]
    if(len(sys.argv) <= 2): sys.exit("\nERROR! Fix your inputs!\n\nArg 1:  input param file detailing each voronoi 'structure'.\nShould be of the form:\nCrystal:\n    0,2,8,*\n\nArg2: a model file.\n\nOutput is printed to screen.")

    paramfile = sys.argv[1]
    modelfile = sys.argv[2]

    m = Model(modelfile)

    cutoff = {}
    cutoff[(40,40)] = 3.6
    cutoff[(13,29)] = 3.6
    cutoff[(29,13)] = 3.6
    cutoff[(40,13)] = 3.6
    cutoff[(13,40)] = 3.6
    cutoff[(29,40)] = 3.6
    cutoff[(40,29)] = 3.6
    cutoff[(13,13)] = 3.6
    cutoff[(29,29)] = 3.6

    cutoff[(41,41)] = 3.7
    cutoff[(28,28)] = 3.7
    cutoff[(41,28)] = 3.7
    cutoff[(28,41)] = 3.7

    cutoff[(46,46)] = 3.45
    cutoff[(14,14)] = 3.45
    cutoff[(46,14)] = 3.45
    cutoff[(14,46)] = 3.45

    voronoi_3d(m,cutoff)
    #m = fortran_voronoi_3d(modelfile,3.5)

    #vorrun = vor.Vor()
    #m = vorrun.runall(modelfile,3.5)
    #vorrun.set_atom_vp_indexes(m)

    vp_dict = load_param_file(paramfile)
    set_atom_vp_types(m,vp_dict)

    #atom_dict = generate_atom_dict(vorrun.index,vp_dict)
    #vor_cats.load_index_file(sys.argv[2])
    #printVorCats(atom_dict,vp_dict)

    vor_stats(m) # Prints what you probably want
    cats = index_stats(m)
    count = 4314
    for atom in m.atoms:
        #if atom.vp.type == 'Undef':
        #if atom.vp.index[:4] == (0, 0, 12, 0):
        if atom.vp.index[:4] == (0, 2, 8, 2):
            #print(atom.vp.index, cats[atom.vp.index]['Total'])
            #new = Model('0,0,12,0; number of atoms is {0};'.format(count), m.lx, m.ly, m.lz, atom.neighs + [atom])
            new = Model('0,2,8,2; number of atoms is {0};'.format(count), m.lx, m.ly, m.lz, atom.neighs + [atom])
            fix_cluster_pbcs(new)
            val = normalize_bond_distances(new)
            #new.comment = '0,0,12,0; number of atoms is {0}; bond length scaling factor is {1}'.format(count,val)
            new.comment = '0,2,8,2; number of atoms is {0}; bond length scaling factor is {1}'.format(count,val)
            center = find_center_atom(new)
            new.remove(center)
            new.add(center)
            #new.write('icosahedron.00120.{0}.xyz'.format(count))
            new.write('0282.{0}.xyz'.format(count))
            count += 1
    print(count)
    cn = 0.0
    for atom in m.atoms:
        cn += atom.cn
    cn = float(cn)/m.natoms
    print(cn)
    return 0

    xtal_atoms = []
    atoms = []
    for i,atom in enumerate(m.atoms):
        #if(atom.vp.type == 'Crystal-like'):
        #    xtal_atoms.append(atom)
        #    m.atoms[i].z = 0
        #elif(atom.vp.type == 'Icosahedra-like'):
        #    m.atoms[i].z = 1
        #elif(atom.vp.type == 'Mixed'):
        #    m.atoms[i].z = 2
        index = (1,2,5,4,0,0,0,0)
        if(atom.vp.index == index):
            print(i,atom.vp.index)
            atoms = [atom] + atom.vp.neighs
            temp = Model('',m.lx,m.ly,m.lz,atoms)
            temp.write_real_xyz('temp{0}.xyz'.format(i))
            #if(i>13):
            #    break
    #xtal_model = Model('comment',m.lx,m.ly,m.lz,xtal_atoms)
    #xtal_model.write_real_xyz('temp.xyz')
    #m.write_real_xyz('temp.xyz')
    return 0

    l = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 100, 101, 102, 103, 107, 108, 110, 111, 113, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 145, 146, 147, 151, 152, 153, 154, 157, 159, 160, 161, 162, 163, 164, 165, 166, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 192, 193, 194, 195, 196, 197, 198, 199, 200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219, 220, 221, 222, 223, 224, 225, 226, 227, 228, 229, 230, 231, 232, 233, 234, 235, 236, 237, 238, 239, 240, 241, 242, 243, 244, 245, 246, 247, 248, 249, 250, 251, 252, 253, 254, 255, 256, 257, 258, 259, 260, 261, 262, 263, 264, 265, 266, 267, 268, 269, 270, 271, 272, 273, 274, 275, 276, 277, 278, 279, 280, 281, 282, 283, 284, 285, 287, 288, 289, 290, 291, 292, 293, 294, 295, 296, 297, 298, 299, 300, 301, 302, 303, 304, 305, 306, 307, 308, 309, 310, 311, 312, 313, 314, 315, 316, 317, 318, 319, 320, 321, 322, 323, 324, 326, 327, 328, 329, 330, 331, 332, 333, 334, 335, 336, 337, 338, 339, 340, 341, 342, 343, 344, 345, 346, 347, 348, 349, 350, 351, 352, 353, 355, 356, 358, 359, 360, 362, 363, 366, 367, 368, 369, 370, 372, 373, 374, 375, 376, 377, 378, 379, 380, 381, 382, 383, 384, 385, 386, 387, 388, 389, 390, 391, 392, 393, 394, 395, 396, 398, 399, 400, 401, 402, 405, 406, 409, 411, 412, 413, 414, 415, 416, 418, 419, 420, 421, 422, 423, 424, 425, 426, 427, 428, 429, 430, 431, 432, 433, 434, 435, 436, 437, 438, 439, 440, 441, 442, 443, 445, 447, 448, 450, 451, 452, 453, 454, 455, 456, 457, 458, 459, 460, 461, 462, 463, 464, 465, 466, 467, 468, 469, 470, 471, 472, 473, 474, 475, 476, 477, 478, 479, 480, 481, 482, 483, 484, 485, 486, 487, 488, 489, 490, 491, 492, 493, 494, 495, 496, 497, 498, 499, 500, 501, 502, 503, 504, 505, 506, 507, 508, 509, 510, 511, 512, 513, 514, 515, 516, 517, 518, 519, 520, 521, 522, 523, 524, 525, 527, 528, 529, 530, 531, 532, 533, 534, 535, 536, 537, 538, 539, 540, 541, 542, 543, 544, 545, 546, 547, 548, 549, 550, 551, 552, 553, 554, 555, 556, 557, 558, 559, 560, 561, 562, 563, 564, 565, 566, 567, 568, 569, 570, 571, 573, 574, 575, 579, 581, 582, 583, 584, 585, 586, 587, 588, 589, 590, 591, 592, 593, 594, 595, 596, 597, 598, 599, 600, 601, 602, 603, 604, 605, 606, 607, 608, 609, 610, 611, 612, 613, 614, 615, 616, 618, 622, 623, 625, 629, 630, 632, 634, 635, 636, 637, 638, 639, 640, 641, 642, 643, 644, 645, 646, 647, 648, 649, 650, 651, 652, 653, 654, 655, 656, 658, 660, 663, 665, 668, 669, 670, 671, 673, 674, 675, 676, 677, 678, 679, 680, 681, 682, 683, 684, 685, 686, 687, 688, 689, 690, 691, 692, 693, 694, 695, 696, 697, 698, 699, 700, 701, 703, 704, 705, 706, 707, 708, 709, 710, 711, 712, 713, 714, 715, 716, 717, 718, 719, 720, 721, 722, 723, 724, 725, 726, 727, 728, 729, 730, 731, 732, 733, 734, 735, 736, 737, 738, 739, 740, 741, 742, 743, 744, 745, 746, 747, 748, 749, 750, 751, 752, 753, 754, 755, 756, 757, 758, 759, 760, 761, 762, 763, 764, 765, 766, 767, 768, 769, 770, 771, 772, 773, 774, 775, 776, 777, 778, 779, 780, 781, 782, 783, 784, 785, 786, 787, 788, 789, 790, 791, 792, 793, 794, 795, 796, 797, 798, 799, 800, 801, 802, 803, 804, 805, 806, 807, 808, 809, 810, 811, 812, 813, 814, 815, 816, 817, 818, 819, 820, 821, 822, 823, 824, 825, 826, 827, 828, 829, 830, 831, 832, 833, 834, 835, 836, 837, 838, 839, 840, 841, 842, 843, 844, 845, 846, 847, 848, 849, 850, 851, 852, 853, 854, 855, 856, 857, 858, 859, 860, 861, 862, 863, 864, 865, 866, 867, 869, 874, 878, 879, 880, 882, 883, 884, 885, 886, 887, 888, 889, 890, 891, 892, 893, 894, 895, 896, 897, 898, 899, 900, 901, 902, 903, 904, 905, 906, 907, 908, 909, 910, 911, 913, 915, 916, 918, 919, 921, 922, 923, 924, 925, 926, 927, 928, 929, 930, 931, 932, 933, 934, 935, 936, 937, 938, 939, 940, 941, 942, 943, 944, 945, 946, 948, 949, 950, 952, 953, 954, 955, 956, 960, 961, 963, 964, 965, 966, 967, 968, 969, 970, 971, 972, 973, 974, 975, 976, 977, 978, 979, 980, 981, 982, 983, 984, 985, 986, 987, 988, 989, 990, 991, 992, 993, 994, 995, 996, 997, 998, 999, 1000, 1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008, 1009, 1010, 1011, 1012, 1013, 1014, 1015, 1016, 1017, 1018, 1019, 1020, 1021, 1022, 1023, 1024, 1025, 1026, 1027, 1028, 1029, 1030, 1031, 1032, 1033, 1034, 1035, 1036, 1037, 1038, 1039, 1041, 1042, 1043, 1044, 1045, 1046, 1047, 1048, 1049, 1050, 1051, 1052, 1053, 1054, 1055, 1056, 1057, 1058, 1059, 1060, 1061, 1062, 1063, 1064, 1065, 1066, 1067, 1068, 1069, 1070, 1071, 1072, 1074, 1075, 1076, 1077, 1079, 1080, 1081, 1082, 1083, 1084, 1085, 1086, 1088, 1089, 1090, 1091, 1092, 1093, 1094, 1095, 1096, 1097, 1098, 1099, 1100, 1101, 1102, 1103, 1104, 1105, 1106, 1107, 1108, 1109, 1110, 1111, 1112, 1113, 1114, 1115, 1116, 1118, 1119, 1120, 1122, 1129, 1130, 1131, 1132, 1134, 1135, 1136, 1137, 1138, 1139, 1140, 1141, 1142, 1143, 1144, 1145, 1146, 1147, 1148, 1150, 1151, 1152, 1153, 1154, 1155, 1156, 1157, 1159, 1160, 1161, 1162, 1163, 1165, 1166, 1167, 1169, 1171, 1172, 1173, 1174, 1175, 1176, 1177, 1178, 1179, 1180, 1181, 1182, 1183, 1184, 1185, 1186, 1187, 1188, 1189, 1190, 1191, 1192, 1193, 1194, 1195, 1196, 1197, 1198, 1199, 1200, 1201, 1202, 1203, 1204, 1205, 1206, 1207, 1208, 1210, 1211, 1212, 1213, 1214, 1215, 1216, 1217, 1218, 1219, 1220, 1221, 1222, 1223, 1224, 1225, 1226, 1227, 1228, 1229, 1230, 1231, 1232, 1233, 1234, 1235, 1236, 1237, 1238, 1239, 1240, 1241, 1242, 1243, 1244, 1245, 1246, 1247, 1248, 1249, 1250, 1251, 1252, 1253, 1254, 1255, 1256, 1257, 1258, 1259, 1260, 1261, 1262, 1263, 1264, 1265, 1266, 1267, 1268, 1269, 1270, 1271, 1272, 1273, 1274, 1275, 1276, 1277, 1278, 1279, 1280, 1281, 1282, 1283, 1284, 1285, 1286, 1287, 1288, 1289, 1290, 1291, 1292, 1293, 1294, 1295, 1296, 1297, 1298, 1299, 1300, 1301, 1302, 1303, 1304, 1305, 1306, 1307, 1308, 1309, 1310, 1311, 1312, 1313, 1314, 1315, 1316, 1317, 1318, 1319, 1320, 1321, 1322, 1324, 1325, 1326, 1327, 1328, 1329, 1330, 1331, 1332, 1333, 1334, 1335, 1336, 1337, 1339, 1340, 1341, 1342, 1343, 1344, 1345, 1346, 1347, 1348, 1349, 1350, 1352, 1353, 1354, 1355, 1356, 1357, 1358, 1361, 1362, 1363, 1365, 1368, 1369, 1370, 1371, 1372, 1373, 1375, 1376, 1377, 1378, 1379, 1380, 1381, 1382, 1383, 1384, 1385, 1386, 1387, 1388, 1389, 1390, 1391, 1392, 1393, 1394, 1395, 1396, 1397, 1398, 1399, 1400, 1401, 1402, 1406, 1408, 1409, 1410, 1412, 1413, 1414, 1415, 1416, 1417, 1418, 1419, 1420, 1421, 1422, 1423, 1424, 1425, 1426, 1427, 1428, 1429, 1430, 1431, 1432, 1433, 1434, 1435, 1436, 1437, 1438, 1439, 1440, 1441, 1442, 1443, 1444, 1445, 1446, 1447, 1448, 1449, 1451, 1452, 1453, 1454, 1455, 1456, 1457, 1458, 1459, 1460, 1461, 1462, 1463, 1464, 1465, 1466, 1467, 1468, 1469, 1470, 1471, 1472, 1473, 1474, 1475, 1476, 1477, 1478, 1479, 1480, 1481, 1482, 1483, 1484, 1485, 1486, 1487, 1488, 1489, 1490, 1491, 1492, 1493, 1494, 1495, 1496, 1497, 1498, 1499, 1500, 1501, 1502, 1503, 1504, 1505, 1506, 1507, 1508, 1509, 1510, 1511, 1512, 1513, 1514, 1515, 1516]
    #l = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 91, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 123, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194, 195, 196, 198, 199, 200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219, 220, 221, 222, 223, 224, 225, 226, 227, 228, 229, 230, 231, 232, 233, 234, 235, 236, 237, 238, 239, 240, 241, 242, 243, 244, 245, 246, 247, 248, 249, 251, 252, 253, 254, 256, 257, 258, 259, 260, 261, 262, 263, 264, 265, 266, 267, 268, 270, 271, 272, 273, 274, 275, 276, 277, 278, 279, 280, 281, 282, 283, 284, 285, 286, 287, 288, 289, 290, 291, 293, 294, 295, 296, 299, 300, 301, 304, 305, 306, 307, 308, 309, 310, 311, 312, 313, 314, 315, 316, 317, 318, 319, 320, 322, 323, 324, 325, 326, 327, 328, 330, 331, 334, 335, 336, 337, 339, 340, 341, 342, 343, 344, 345, 346, 347, 348, 349, 350, 351, 352, 353, 354, 355, 356, 357, 358, 359, 360, 362, 363, 364, 365, 366, 367, 369, 370, 371, 372, 373, 374, 375, 376, 377, 378, 379, 380, 381, 382, 383, 384, 385, 386, 387, 388, 389, 390, 391, 392, 393, 394, 395, 396, 397, 398, 400, 401, 402, 403, 404, 405, 406, 407, 408, 409, 410, 411, 413, 414, 415, 416, 417, 418, 419, 420, 421, 422, 423, 424, 425, 426, 427, 428, 429, 430, 431, 432, 433, 434, 435, 436, 437, 438, 439, 440, 441, 442, 443, 444, 445, 446, 447, 448, 449, 450, 451, 452, 453, 454, 455, 456, 457, 458, 459, 460, 461, 462, 463, 464, 465, 466, 467, 468, 469, 470, 471, 472, 473, 474, 475, 476, 477, 478, 479, 480, 481, 482, 483, 484, 485, 486, 487, 488, 489, 490, 491, 492, 493, 494, 495, 496, 497, 498, 499, 500, 501, 502, 503, 504, 505, 507, 508, 509, 510, 511, 512, 513, 515, 517, 519, 520, 521, 522, 523, 524, 525, 526, 527, 528, 529, 530, 531, 532, 533, 534, 535, 537, 539, 540, 541, 544, 545, 546, 548, 549, 550, 553, 554, 557, 558, 559, 560, 561, 562, 563, 564, 565, 566, 567, 568, 569, 571, 572, 573, 574, 575, 576, 577, 578, 579, 580, 581, 582, 583, 584, 585, 587, 588, 589, 590, 591, 592, 593, 594, 595, 596, 597, 598, 599, 600, 601, 602, 603, 604, 605, 606, 607, 608, 609, 610, 611, 612, 613, 614, 615, 616, 617, 618, 619, 620, 621, 622, 623, 624, 625, 626, 627, 628, 629, 630, 631, 632, 633, 634, 635, 636, 637, 638, 639, 640, 641, 642, 643, 644, 645, 646, 647, 648, 649, 650, 651, 652, 653, 654, 655, 656, 657, 658, 659, 660, 661, 662, 663, 664, 665, 666, 667, 668, 669, 670, 671, 672, 673, 674, 675, 676, 677, 678, 679, 680, 681, 682, 684, 685, 686, 687, 688, 692, 693, 694, 695, 696, 697, 698, 699, 700, 701, 702, 703, 704, 705, 706, 708, 709, 710, 711, 712, 713, 714, 715, 716, 718, 719, 721, 722, 723, 725, 726, 728, 729, 730, 731, 732, 733, 734, 735, 736, 737, 738, 739, 740, 741, 742, 743, 744, 745, 746, 748, 749, 751, 752, 753, 754, 755, 756, 757, 759, 760, 761, 763, 764, 765, 766, 767, 768, 769, 770, 771, 772, 773, 774, 776, 778, 782, 784, 785, 786, 787, 789, 790, 792, 793, 794, 795, 796, 797, 798, 799, 800, 801, 802, 803, 804, 805, 806, 807, 808, 809, 810, 811, 812, 813, 814, 815, 816, 817, 818, 819, 820, 821, 822, 823, 824, 825, 826, 827, 828, 829, 830, 831, 832, 833, 834, 835, 836, 837, 838, 839, 840, 841, 842, 843, 844, 845, 846, 847, 848, 849, 850, 851, 852, 853, 854, 855, 856, 857, 858, 859, 860, 861, 862, 863, 864, 865, 866, 867, 868, 869, 870, 871, 872, 873, 874, 875, 876, 877, 878, 879, 881, 882, 883, 884, 885, 887, 888, 889, 890, 891, 892, 893, 894, 895, 896, 898, 899, 900, 901, 902, 903, 904, 905, 906, 907, 908, 909, 910, 911, 913, 914, 915, 916, 917, 918, 919, 920, 921, 922, 925, 926, 927, 929, 930, 931, 932, 933, 934, 935, 936, 937, 938, 939, 940, 941, 942, 943, 944, 945, 947, 948, 949, 950, 951, 952, 955, 956, 957, 958, 959, 960, 961, 962, 963, 964, 965, 966, 967, 968, 969, 970, 971, 972, 973, 974, 975, 976, 977, 978, 979, 980, 981, 982, 983, 984, 985, 986, 987, 988, 989, 990, 991, 992, 995, 996, 997, 998, 999, 1000, 1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008, 1009, 1010, 1011, 1012, 1013, 1014, 1015, 1016, 1017, 1018, 1019, 1020, 1021, 1022, 1023, 1024, 1025, 1026, 1027, 1028, 1029, 1030, 1031, 1032, 1033, 1034, 1035, 1036, 1037, 1038, 1039, 1040, 1041, 1042, 1043, 1044, 1045, 1046, 1047, 1048, 1049, 1050, 1051, 1052, 1053, 1054, 1055, 1056, 1057, 1059, 1060, 1061, 1062, 1063, 1064, 1065, 1066, 1067, 1068, 1069, 1070, 1071, 1072, 1073, 1074, 1075, 1076, 1077, 1078, 1079, 1080, 1081, 1082, 1083, 1084, 1085, 1086, 1087, 1088, 1089, 1090, 1091, 1092, 1093, 1094, 1095, 1096, 1097, 1098, 1099, 1100, 1101, 1102, 1103, 1104, 1105, 1106, 1107, 1108, 1109, 1110, 1112, 1113, 1114, 1115, 1116, 1117, 1118, 1119, 1120, 1121, 1122, 1123, 1126, 1127, 1129, 1130, 1131, 1132, 1134, 1135, 1136, 1137, 1138, 1139, 1140, 1141, 1142, 1143, 1144, 1145, 1146, 1147, 1148, 1149, 1150, 1151, 1152, 1153, 1154, 1156, 1158, 1159, 1160, 1161, 1162, 1163, 1164, 1165, 1168, 1169, 1170, 1171, 1172, 1173, 1174, 1175, 1176, 1177, 1178, 1179, 1180, 1181, 1182, 1183, 1184, 1185, 1186, 1187, 1188, 1189, 1190, 1191, 1192, 1194, 1195, 1196, 1198, 1199, 1200, 1201, 1202, 1203, 1204, 1205, 1206, 1207, 1208, 1209, 1210, 1211, 1212, 1213, 1214, 1215, 1216, 1217, 1218, 1219, 1220, 1221, 1222, 1223, 1224, 1225, 1226, 1227, 1228, 1229, 1230, 1231, 1232, 1233, 1234, 1235, 1236, 1237, 1238, 1239, 1240, 1241, 1242, 1243, 1244, 1245, 1246, 1247, 1248, 1249]
    l = [i for i in range(1517) if i not in l]
    for i in l:
        index = ','.join([str(x) for x in m.atoms[i].vp.index])
        print('{0}  \t{1}'.format(index, m.atoms[i].vp.type))

    return

    #m.generate_neighbors(3.5)
    #save_vp_cluster_with_index(m,[0,0,12,0])

    #cutoff = 3.5
    #m2 = Model(sys.argv[3])
    #vor_instance = Vor()
    #vor_instance.runall(modelfile,cutoff)
    #vor_instance.set_atom_vp_indexes(m)
    #nbins = 6
    #del_bin = 100.0/nbins
    #fracs = []
    #for atom in m2.atoms:
    #    fracs.append((float(m.atoms[m.atoms.index(atom)].vp.index[2])/float(sum(m.atoms[m.atoms.index(atom)].vp.index))*100.0))
    #    bin =    int((float(m.atoms[m.atoms.index(atom)].vp.index[2])/float(sum(m.atoms[m.atoms.index(atom)].vp.index))*100.0) /(100.0/(nbins-1)))
    #    atom.z = bin+1
    #fracs.sort()
    #print('Min %: {0}. Max %: {1}'.format(min(fracs),max(fracs)))
    #for atom in m2.atoms:
    #    atom.vp.type = m.atoms[m.atoms.index(atom)].vp.type
    #atoms = []
    #for atom in m2.atoms:
    #    if(atom.vp.type == "Icosahedra-like"):
    #        atoms.append(atom)
    #m3 = Model(str(len(atoms)),m.lx,m.ly,m.lz,atoms)
    #m3.write_real_xyz()


    #print_all(m)
    index_stats(m) # Prints index version of vor_stats
    vor_stats(m) # Prints what you probably want
    for atom in m.atoms:
        if( atom.vp.type == "Undef"):
            print( atom.vp.index )
    print( "")
    for atom in m.atoms:
         if( atom.vp.type == "Crystal-like"):
             print(atom.vp.index )
    print (m.atoms[163].vp.index)
    print (m.atoms[163].vp.neighs)
    print (m.atoms[163].coord)
    print (m.atoms[163].id)

if __name__ == "__main__":
    main()
