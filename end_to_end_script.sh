#!/bin/bash
# source ~/miniconda3/etc/profile.d/conda.sh

WORKSPACE=$1
load-images --disaster typhoon-mangkhut --dest <workspace>/images
conda activate abdenv
abd cover --raster $WORKSPACE/images/pre-event/https:--opendata.digitalglobe.com-events-typhoon-mangkhut-pre-event-2018-04-09-103001007E413300-103001007E413300.tif --zoom 17 --out $WORKSPACE/abd/cover.csv
abd tile --raster $WORKSPACE/images/pre-event/https:--opendata.digitalglobe.com-events-typhoon-mangkhut-pre-event-2018-04-09-103001007E413300-103001007E413300.tif --zoom 17 --cover $WORKSPACE/abd/cover.csv --out $WORKSPACE/abd/images --format tif --no_web_ui --config ada_tools/config.toml

abd predict --dataset abd --cover $WORKSPACE/abd/cover.csv --checkpoint neat-fullxview-epoch75.pth --out $WORKSPACE/abd/predictions --metatiles --keep_borders --config ada_tools/config.toml
abd vectorize --masks $WORKSPACE/abd/predictions --type Building --out $WORKSPACE/abd/buildings.geojson --config ada_tools/config.toml
filter-buildings --data $WORKSPACE/abd/buildings.geojson --dest $WORKSPACE/abd/buildings-clean.geojson

prepare-data --data images --buildings $WORKSPACE/abd/buildings-clean.geojson --dest $WORKSPACE/caladrius
conda activate caladriusenv
CUDA_VISIBLE_DEVICES="0" python $WORKSPACE/caladrius/caladrius/run.py --run-name run --data-path $WORKSPACE/caladrius --model-type attentive --model-path best_model_wts.pkl --checkpoint-path $WORKSPACE/caladrius/runs --batch-size 2 --classification-loss-type f1 --output-type classification --inference
conda activate abdenv
final-layer --builds $WORKSPACE/abd/buildings-clean.geojson --damage $WORKSPACE/caladrius/runs/run-input_size_32-learning_rate_0.001-batch_size_2/predictions/run-split_inference-epoch_001-model_attentive-predictions.txt --out $WORKSPACE/buildings-predictions.geojson --thresh 1
setup-discount --input $WORKSPACE/buildings-predictions.geojson