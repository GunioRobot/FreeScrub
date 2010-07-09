#!/bin/bash
#run tiff.py on all our tiff testimages
rm ../testimages/*.tiff-scr
for i in ../testimages/*.tiff
do
    ./tiff.py $i
done

