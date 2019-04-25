
base="/home/oliver/export/"
cmd="python -m main"

common="--lr 0.01  --input  'coco --path /local/storage/coco' --no_load --train_epochs 60 --crop_boxes --image_size 512 --batch_size 16 --epoch_size 8192 --log_dir /local/storage/logs/multiclass_coco/" 
prefix="/local/storage/export"

subset1="cow,sheep,cat,dog,zebra,giraffe,elephant,bear"
subset2="hotdog,pizza,donut,cake,cup,fork,knife,spoon"


for subset in $subset1 $subset2; 
do 
  bash -c "$cmd  $common --run_name $subset --model \"fcn --features 128\" --subset $subset"
  for i in $(echo $subset | sed "s/,/ /g")
  do 
    bash -c "$cmd  $common --run_name $i --subset $subset --keep_classes $i"
  done
done


