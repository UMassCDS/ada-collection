#!/bin/bash

# If you use miniconda to manage your environments, uncomment the following line so that `conda activate` commands work
source ~/miniconda3/etc/profile.d/conda.sh

# Output folder for disaster data and predictions
WORKSPACE=$1

# Name of the disaster, matching MAXAR url
DISASTER=typhoon-mangkhut

# Path to the Caladrius code
CALADRIUS=caladrius

conda activate abdenv

#load-images --disaster $DISASTER --dest $WORKSPACE/images

#abd cover --raster $WORKSPACE/images/pre-event/*.tif --zoom 17 --out $WORKSPACE/abd/cover.csv
#abd tile --raster $WORKSPACE/images/pre-event/*.tif --zoom 17 --cover $WORKSPACE/abd/cover.csv --out $WORKSPACE/abd/images --format tif --no_web_ui --config ada_tools/config.toml

abd predict --dataset $WORKSPACE/abd --cover $WORKSPACE/abd/cover.csv --checkpoint neat-fullxview-epoch75.pth --out $WORKSPACE/abd/predictions --metatiles --keep_borders --config ada_tools/config.toml
abd vectorize --masks $WORKSPACE/abd/predictions --type Building --out $WORKSPACE/abd/buildings.geojson --config ada_tools/config.toml
filter-buildings --data $WORKSPACE/abd/buildings.geojson --dest $WORKSPACE/abd/buildings-clean.geojson

prepare-data --data $WORKSPACE/images --buildings $WORKSPACE/abd/buildings-clean.geojson --dest $WORKSPACE/caladrius
conda activate caladriusenv
CUDA_VISIBLE_DEVICES="0" python $CALADRIUS/caladrius/caladrius/run.py --run-name run --data-path $WORKSPACE/caladrius --model-type attentive --model-path best_model_wts.pkl --checkpoint-path $WORKSPACE/caladrius/runs --batch-size 2 --classification-loss-type f1 --output-type classification --inference
conda activate abdenv
final-layer --builds $WORKSPACE/abd/buildings-clean.geojson --damage $WORKSPACE/caladrius/runs/run-input_size_32-learning_rate_0.001-batch_size_2/predictions/run-split_inference-epoch_001-model_attentive-predictions.txt --out $WORKSPACE/buildings-predictions.geojson --thresh 1
setup-discount --input $WORKSPACE/buildings-predictions.geojson