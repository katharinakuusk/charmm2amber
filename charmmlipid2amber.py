import os
import sys
import argparse

import numpy as np
import MDAnalysis as mda
from MDAnalysis.core.universe import Merge, Residue

def head_group_conversion(charmm_head_group):
    if charmm_head_group == 'PA':
        return 'PH-'
    elif charmm_head_group == 'PG':
        return 'PGR'
    elif charmm_head_group in ['PC', 'PE', 'PS']:
        return charmm_head_group

def acyl_chain_conversion(charmm_acyl_chain):
    if charmm_acyl_chain == 'A':
        return 'AR'
    elif charmm_acyl_chain == 'L':
        return 'LAL'
    elif charmm_acyl_chain == 'M':
        return 'MY'
    elif charmm_acyl_chain == 'O':
        return 'OL'
    elif charmm_acyl_chain == 'P':
        return 'PA'
    elif charmm_acyl_chain == 'S':
        return 'ST'
    elif charmm_acyl_chain == 'D':
        return 'DHA'

def chol(u):
    ref = mda.Universe(os.path.join(os.path.dirname(__file__), 'gro', 'CHL.gro'))
    new_ag = []
    for name in ref.atoms.names:
        ori_name = name
        if name in ['H31', 'H61', 'H81', 'H91', 'H141', 'H171', 'H201', 'H251']:
            name = name[:-1]
        elif name == "HO1":
            name = "H3'"
        elif name == "O1":
            name = 'O3'
        elif name[0] == 'H':
            name = name[:-1] + chr(64+int(name[-1]))
        new_atom = Merge(u.select_atoms('name {}'.format(name))).atoms
        new_atom.names = ori_name
        new_ag.append(new_atom)
    new_ag = Merge(*new_ag)
    new_ag.residues.resnames = 'CHL'
    return new_ag.atoms, 'CHL'

def lipid(u, resname, lipid_counter):
    chain_id = "L" + str(lipid_counter)
    charmm_head_group = resname[2:]
    amber_head_group = head_group_conversion(charmm_head_group)

    # Same acryl chain
    if resname[0] == 'D':
        charmm_acyl_A = charmm_acyl_B = resname[1]
    else:
        charmm_acyl_A = resname[0]
        charmm_acyl_B = resname[1]
    amber_acyl_A = acyl_chain_conversion(charmm_acyl_A)
    amber_acyl_B = acyl_chain_conversion(charmm_acyl_B)

    ref = mda.Universe(os.path.join(os.path.dirname(__file__), 'gro',
                                    '{}_{}_{}.gro'.format(amber_acyl_A, amber_head_group, amber_acyl_B)))
    new_ag = []
    # acyl rail 1
    for name in ref.select_atoms('resid 1').names:
        ori_name = name
        if name[0] == 'C':
            name = name[0] + '3' + name[2:]
        elif name[0] == 'H':
            if name[-1] == 'R':
                name = name[:-1] + 'X'
            elif name[-1] == 'S':
                name = name[:-1] + 'Y'
            elif name[-1] == 'T':
                name = name[:-1] + 'Z'
        new_atom = Merge(u.select_atoms('name {}'.format(name))).atoms
        new_atom.names = ori_name
        new_ag.append(new_atom)
    acyl_A = Merge(*new_ag)
    acyl_A.residues.resnames = amber_acyl_A
    acyl_A.residues.resids = 1

    # Head group
    new_ag = []
    for name in ref.select_atoms('resid 2').names:
        ori_name = name
        if name == 'HR':
            name = 'HX'
        elif name == 'HS':
            name = 'HY'
        elif name == 'HX':
            name = 'HS'
        elif name == 'P31':
            name = 'P'
        elif name == 'C3':
            name = 'C1'
        elif name == 'C1':
            name = 'C3'
        elif name == 'C11':
            name = 'C31'
        # PC
        elif name == 'N31':
            name = 'N'
        # PH-
        elif name == 'HO2A':
            name = 'H12'
        elif (amber_head_group in ['PS', 'PE']) and (name[:3] == 'HN1'):
            # Convert HN1A HN1B HN1C to HN1 HN2 HN3
            name = 'HN' + str(ord(name[-1]) - 64)
        elif (amber_head_group == 'PS') and (name in ['O35', 'O36']):
            if name == 'O35':
                name = 'O13A'
            elif name == 'O36':
                name = 'O13B'
        elif (amber_head_group == 'PGR') and (name in ['O35', 'O36', 'HO5A', 'HO6A']):
            if name == 'O35':
                name = 'OC2'
            elif name == 'O36':
                name = 'OC3'
            elif name == 'HO5A':
                name = 'HO2'
            elif name == 'HO6A':
                name = 'HO3'
        elif name[:2] == 'O1' and len(name) == 3:
            name = 'O3' + name[-1]
        elif name[:2] == 'O3' and len(name) == 3:
            name = 'O1' + name[-1]
        elif name[:2] == 'C3' and len(name) == 3:
            name = 'C1' + name[2]
        elif name[0] == 'H' and not name in ['HA', 'HB']:
            name = 'H1' + name[1:]
        new_atom = Merge(u.select_atoms('name {}'.format(name))).atoms
        new_atom.names = ori_name
        new_ag.append(new_atom)
    head_group = Merge(*new_ag)
    head_group.residues.resnames = amber_head_group
    head_group.residues.resids = 2

    # acyl rail 2
    new_ag = []

    for name in ref.select_atoms('resid 3').names:
        ori_name = name
        if name[0] == 'C':
            name = name[0] + '2' + name[2:]
        elif resname[0] != 'D' and resname[1] == 'O':
            if name == 'H10R':
                name = 'H101'
            elif name == 'H9R':
                name = 'H91'
        new_atom = Merge(u.select_atoms('name {}'.format(name))).atoms
        new_atom.names = ori_name
        new_ag.append(new_atom)

    acyl_B = Merge(*new_ag)
    acyl_B.residues.resnames = amber_acyl_B
    acyl_B.residues.resids = 3
#    res_id =  acyl_B.atoms[-1].resid
#   acyl_B.add_Residue(acyl_B.segments[0], resid=res_id+1,resname="TER", resnum=0)

    # add a TER
   #ter = acyl_B.atoms[-1:]
    """ter = mda.Universe.empty(1,
                             n_residues=1,
                             atom_resindex=(acyl_B.atoms[-1:].ids+1),
                             trajectory=False)
    ter.names = ["TER"]
    print(ter.__dict__)
    ter.residues.resids = 4
    ter.atoms.positions = [0, 0, 0]
    print(ter.atoms.ids)"""
    new = Merge(acyl_A.atoms, head_group.atoms, acyl_B.atoms)
    chain_arr = [chain_id] * len(new.atoms)
    new.atoms.chainIDs = chain_arr
    if new.atoms.chainIDs[0] == "L1":
        new.atoms.write("ter_check.pdb")
    assert len(new.atoms) == len(u.atoms)
    return new.atoms, '{}_{}_{}'.format(amber_acyl_A, amber_head_group, amber_acyl_B)

def resname2lipid17(mol, lipid_counter):
    resname = mol.resnames
    assert len(np.unique(resname)) == 1
    resname = np.unique(resname)[0]
    assert len(resname) == 4
    if resname == 'CHL1':
        return chol(mol)
    else:
        return lipid(mol, resname, lipid_counter)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", nargs=1, metavar="charmm_lipid.gro", help="Input file with charmm lipid.")
    parser.add_argument("-o", nargs=1, metavar="amber_lipid.gro", \
                        help="Output file for gromacs input with lipid name changed to amber lipid17.")
    parser.add_argument("-lipids", nargs="+", metavar="POPC", default="charmm_membrane_builder", \
                        help="Lipid names to check, seperated by space.")

    args = parser.parse_args(sys.argv[1:])



    default_set = ['CHL1', 'DLPA', 'DLPC', 'DLPE', 'DLPG', 'DLPS', 'DMPA', 'DMPC', 'DMPE', 'DMPG', 'DMPS', 'DOPA',
                   'DOPC', 'DOPE', 'DOPG', 'DOPS', 'DPPA', 'DPPC', 'DPPE', 'DPPG', 'DPPS', 'DSPA', 'DSPC', 'DSPE',
                   'DSPG', 'DSPS', 'POPA', 'POPC', 'POPE', 'POPG', 'POPS', 'SOPA', 'SOPC', 'SOPE', 'SOPG', 'SOPS', ]
    input_file = os.getcwd() + "/IFS1_membrane_90.pdb"                 #args.f[0]
    output_file = "output.pdb"                                         #args.o[0]
    lipid_set = args.lipids

    if lipid_set == "charmm_membrane_builder":
        lipid_set = default_set

    u = mda.Universe(input_file)
    new_u = []
    previous_lipid = None
    warning_lipids = []
    lipid_counter = 0

    for residue in u.residues:
        if residue.resname in lipid_set:
            lipid_counter += 1
            if not residue.resname in default_set:
                default_set.append(residue.resname)
                print("Lipid {} requested hasn't been tested. Please manually check the conversion.".format(residue.resname))

            new, new_name = resname2lipid17(residue.atoms, lipid_counter)
            new_u.append(new.atoms)
            if new_name != previous_lipid:
                if not previous_lipid is None:
                    print(previous_lipid, count)
                previous_lipid = new_name
                print(previous_lipid)
                count = 1
            else:
                count += 1
        else:
            new_u.append(residue.atoms)
    print(previous_lipid, count)
    final = Merge(*new_u)
    ter = final.select_atoms("name TER")
    final.atoms.write(output_file)








