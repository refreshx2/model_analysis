import random
import math

# This function generates a random model with natoms atoms. Below you can specify natoms, the composition, the box size, the cutoff distance, and the output filename.
# This function is completely random. No monte carlo or other type of algorithm is used. That means this may not be the best way to make a model if the cutoff distance, model size, and number of atoms doesn't leave much extra space available. A MC approach would be better.
def main():
    # NTS: Did not use this to generate the 10k atom box for Zr50, I used the script in the 'OdieCode/Zr50.../starting_model/generate...10k.py file
    natoms = 1250*8
    al_natoms = int(round(0.15 * natoms))
    cu_natoms = int(round(0.35 * natoms))
    zr_natoms = natoms - al_natoms - cu_natoms #Fill up whats left here
    #zr_natoms = 0.50
    print(str(al_natoms))
    print(str(cu_natoms))
    print(str(zr_natoms))
    print(str(natoms))

    cutoff = 2.2

    lx = 56.56856
    ly = 56.56856
    lz = 56.56856
    atoms = []
    f = open('Zr54Cu38Al8_10000atoms_random.xyz','w')
    f.write('Zr54Cu38Al8 10000atoms random\n')
    f.write( str(lx) + ' ' + str(ly) + ' ' + str(lz) + "\n")

    i = 0
    while(i<al_natoms):
        good = True
        x = random.uniform(-lx/2,lx/2)
        y = random.uniform(-ly/2,ly/2)
        z = random.uniform(-lz/2,lz/2)
        for atom in atoms:
            xx = atom[1]-x
            yy = atom[2]-y
            zz = atom[3]-z
            xx = xx-lx*int(round(xx/lx))
            yy = yy-ly*int(round(yy/ly))
            zz = zz-lz*int(round(zz/lz))
            r2 = xx**2 + yy**2 + zz**2
            r = math.sqrt(r2)
            if( r < cutoff ):
                good = False
        if(good):
            atoms.append( (13, x,y,z) )
            i+=1
        else:
            print("Stuck at "+ str(i))
            #print(atoms)

    while(i<al_natoms+cu_natoms):
        good = True
        x = random.uniform(-lx/2,lx/2)
        y = random.uniform(-ly/2,ly/2)
        z = random.uniform(-lz/2,lz/2)
        for atom in atoms:
            xx = atom[1]-x
            yy = atom[2]-y
            zz = atom[3]-z
            xx = xx-lx*int(round(xx/lx))
            yy = yy-ly*int(round(yy/ly))
            zz = zz-lz*int(round(zz/lz))
            r2 = xx**2 + yy**2 + zz**2
            r = math.sqrt(r2)
            if( r < cutoff ):
                good = False
        if(good):
            atoms.append( (29, x,y,z) )
            i+=1
        else:
            print("Stuck at "+ str(i))

    while(i<al_natoms+cu_natoms+zr_natoms):
        good = True
        x = random.uniform(-lx/2,lx/2)
        y = random.uniform(-ly/2,ly/2)
        z = random.uniform(-lz/2,lz/2)
        for atom in atoms:
            xx = atom[1]-x
            yy = atom[2]-y
            zz = atom[3]-z
            xx = xx-lx*int(round(xx/lx))
            yy = yy-ly*int(round(yy/ly))
            zz = zz-lz*int(round(zz/lz))
            r2 = xx**2 + yy**2 + zz**2
            r = math.sqrt(r2)
            if( r < cutoff ):
                good = False
        if(good):
            atoms.append( (40, x,y,z) )
            i+=1
        else:
            print("Stuck at "+ str(i))

    for atom in atoms:
        f.write( str(atom[0]) + " " + str(atom[1]) + " " + str(atom[2]) + " " + str(atom[3]) + "\n" )
    f.write("-1")

    f.close()


    

if __name__ == "__main__":
    main();
