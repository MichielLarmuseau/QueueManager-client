#!/bin/bash
#PBS -N Q239_72_1_28 

#PBS -m a

#PBS -q debug

#PBS -l walltime=71:59:00

#PBS -l nodes=1:ppn=1

module load Python/2.7.11-intel-2016a
module load ase/3.8.1
module load HighThroughput/devel-leuven
module load aconvasp


HTphase 
exit 0
