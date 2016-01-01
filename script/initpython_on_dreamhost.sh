#!/bin/bash

#setting python env under dreamhost hosting service.
#to use geonameDB auto build scrips, you need PyMySQL, python-Levenshtein and requests.

#cd /home/cmsbuild/PyMySQL-master;export PYTHONPATH=$PYTHONPATH:/lib/python;export PYTHONPATH=$PYTHONPATH:$HOME/lib/python;python setup.py install --home=~
#cd /home/cmsbuild/python-Levenshtein-0.11.2;export PYTHONPATH=$PYTHONPATH:/lib/python;export PYTHONPATH=$PYTHONPATH:$HOME/lib/python;python setup.py install --home=~
#cd /home/cmsbuild/requests-master;export PYTHONPATH=$PYTHONPATH:/lib/python;export PYTHONPATH=$PYTHONPATH:$HOME/lib/python;python setup.py install --home=~

echo "setting PYTHONPATH..."
export PYTHONPATH=$PYTHONPATH:/lib/python;export PYTHONPATH=$PYTHONPATH:$HOME/lib/python
echo "Done."