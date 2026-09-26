# Install GAME

- git clone [git@git.crysys.hu:jozsef.sandor/game.git](https://github.com/CrySyS/GAME.git)
- python3 -m venv .venv
- source .venv/bin/activate
- pip install -r requirements.txt
- pip install -e .

# Run GAME

- download source binaries from: https://cloud.crysys.hu/s/GBkzsSpkJi7dkfR
- unzip it to project root folder
- possibly set hyperparameter values in src/config.py
- python3 src/genetic/ga.py


# Measurements

- you can download the measurement artifacts from: https://cloud.crysys.hu/s/e5aH4qeX38oA4sc


## Models
- Simbiota with similarity threshold 40
- Simbiota-ML with Random Forest, Simbiota-ML with Logistic Regression (w/ hyperparams by Niki's paper) 
- ARM, MIPS 

## Data set:
- train set - 10K-10K MW-BN (ml-sample-pack-medium, see csv files in data/ folder)
- seek the hardest circumstances for generating advex, we want to prove the effectiveness of GAME
- any other setup would make easier to generate advex with GAME
- from train set 1K MW -> all of them was shown to the model, so it recognizes all of them (test it though)
- NOT from train set 1K BN -> if we would take from the training set, it would be easier to generate advex, because the model would known for sure that it is BN part
- in binaries folder


## Visuals

### Dataframe
- naming: samples_[arch]_[model].csv
- columns: mw (sha256), tlsh, size, entropy, elf_modifier, ratio_sampler, data_generator, run_id, adv_tlsh, tlsh_diff, size_increase, entropy_diff, detected (YES/NO), fitness


### Similarity graph
- ARM/MIPS x 3 models -> 6 graphs
- for every malware select 1 advex from samples_[arch]_[model].csv -> 1000 advex
- build a similarity graph w/ networkx: 2 nodes are connected if the tlsh diff between them <= 40
- coloring nodes
- export from networkx to be visualized with gephi
- In gephi use the following settings:
    - Force Atlas 2, stronger gravity, gravity=0.3, prevent overlap, no approximate repulsion
    - Expansion if needed
- It will show how similar are advex samples to each other. We know that original malware samples are clustered, now we will see whether it is true or not for advex samples.


### Distribution of best strategies
- ARM/MIPS x 3 models -> 6 figures
- 1000 strategies
- percentage of best strategies (63 possible combination)


### Fitness of best strategies
- ARM/MIPS x 3 models -> 6 figures
- for every malware generate 12 advex with the corresponding best strategy
- average the per advex fitness (because the strategy has fitness, not the generated samples)
- distr strategies based on fitness between 0-10-...-80-90-100 (1000 strategies)
- histogram
- worst best strategies? how many detected samples?


### Cost of successful attack
- ARM/MIPS x 3 models -> 6 figures
- advex from 1000 MW with best strategy, 12 advex for each -> 12K advex, keep undetected samples
- x-axis: size increase
- y-axis: tlsh diff from the original malware
- scatter plot, coloring by strategy

-> discussion
- there are outliers in some of the cases

### Discussion

- GAME uses tlsh distance as an important indicator, so it is inherently best against SIMBIoTA, but based on our measurements it also works against the variants of SIMBIoTA-ML.

- Was there a malware for which we weren't able to generate advex??
    - yes, but only for mips: 2 for SIMBIoTA-ML-RF and 46 for SIMBIoTA-ML-LR


# TODO

- write unit tests for the created classes and functions!
- try igraph instead of networkx
- LIEF related warning: Can't access content of segment LOAD:0xaddress
e.g., b7ed95be1ac32bd82c04fe73f8b390ab72756a63a7f795939a3594327f4e1c80; e28732ea9be75ca2617a045d9ab6980813cb5c9df831977299d94e5486b3772a
- check size-increase outliers
