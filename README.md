# Plant Badger
Application for Pimoroni Badger 2040 W. Connects to Home Assistant to fetch
a plant's status and displays it on the Badger.

## Install dependencies

If you only manage this project from a shell, then you only need these dependencies.
```shell
pip install -r requirements.txt
```

When running with PyCharm, instead use `requirements-pycharm.txt`:
```shell
pip install -r requirements-pycharm.txt
```

This will install dependencies required by PyCharm to run its MicroPython tools.

## Invoke tasks
```shell
invoke --list
# Start by getting your board id
inv list
# Then provision the board
inv provision-all
# After that, just update the code when changes are made locally
inv update-code <board_id>
```
