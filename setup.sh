#!/bin/bash
# source ~/miniconda3/etc/profile.d/conda.sh

conda create --name abdenv python=3.8
conda activate abdenv

cd ada_tools
pip install .

cd ../abd_model
pip install .

git clone --branch ada-0.1 https://github.com/rodekruis/caladrius.git
cd caladrius
./caladrius_install.sh