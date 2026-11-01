#!/bin/bash
#SBATCH --job-name=strpsearch_parallel
#SBATCH --output=slurm-%A_%a.out
#SBATCH --error=slurm-%A_%a.err
#SBATCH --cpus-per-task=4
#SBATCH --mem=4g
#SBATCH --time=1:00:00
#SBATCH --array=1-3919

# Change to the STRPsearch directory
cd /home/pkwon2/STRPsearch

# Initialize conda in the shell and activate the environment
eval "$(conda shell.bash hook)"
conda activate strpsearch_env

# Get list of chunk files sorted (SLURM_ARRAY_TASK_ID is 1-indexed)
chunks=(splits/x*)
chunk=${chunks[$SLURM_ARRAY_TASK_ID-1]}
echo "Running chunk file: $chunk"
bash "$chunk"
