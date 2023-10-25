#!/bin/bash

# If you use miniconda to manage your environments, uncomment the following line so that `conda activate` commands work
source ~/miniconda3/etc/profile.d/conda.sh

conda create --name abdenv python=3.8 --yes
conda activate abdenv

cd ada_tools
pip install . 

cd ../abd_model
pip install .

cd ../
git clone --branch ada-0.1 https://github.com/rodekruis/caladrius.git
cd caladrius
./caladrius_install.sh