#!/bin/bash
#run tiff.py on all our tiff testimages
rm ../testimages/*.tiff-scr
for i in ../testimages/*.tiff
do
    echo $i
    ./tiff.py $i
done

