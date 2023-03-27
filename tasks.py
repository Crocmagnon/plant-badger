import ast
import os
import subprocess
import time
from pathlib import Path

import yaml
from PIL import Image
from invoke import task, Context

BASE_DIR = Path(__file__).parent.resolve(strict=True)
SRC_DIR = BASE_DIR / "src"
TESTS_DIR = BASE_DIR / "test"

MICROPYTHON_DEPENDENCIES = [
    # "github:miguelgrinberg/microdot/src/microdot.py",
    # "github:miguelgrinberg/microdot/src/microdot_asyncio.py",
]


@task
def test(c: Context) -> None:
    """Run tests."""
    with c.cd(BASE_DIR):
        path = os.getenv("PYTHONPATH", "")
        c.run(
            "pytest",
            pty=True,
            echo=True,
            env={"PYTHONPATH": f"{SRC_DIR}:{path}"},
        )


@task(name="list")
def list_boards(c: Context) -> None:
    """List connected boards with mpremote."""
    c.run("mpremote devs", pty=True, echo=True)


@task
def provision_all(c: Context, *, initial: bool = True) -> None:
    """Provision all connected boards sequentially."""
    ids = get_all_board_ids()

    for board_id in ids:
        provision(c, board_id, initial=initial)


@task
def provision(c: Context, board_id: str, *, initial: bool = True) -> None:
    """Install dependencies and copy project files to the board."""
    prepare(board_id)
    download_image(c, board_id)
    if initial:
        wipe(c, board_id)
        with c.cd(SRC_DIR):
            if MICROPYTHON_DEPENDENCIES:
                deps = " ".join(MICROPYTHON_DEPENDENCIES)
                c.run(
                    f"mpremote connect id:{board_id} " f"mip install {deps}",
                    pty=True,
                    echo=True,
                )
    update_code(c, board_id)


@task
def download_image(c: Context, board_id: str) -> None:
    """Download and prepare the proper plant picture for the board."""
    provisioning = get_provisioning(board_id)
    plant_id = provisioning["HA_PLANT_ID"]

    data = query_ha_state(plant_id)
    image_url = data["attributes"]["entity_picture"]
    image_path = SRC_DIR / "images" / "plant.jpg"
    c.run(f"curl -o {image_path} {image_url}", pty=True, echo=True)

    # resize image_path to 128x128 with Pillow
    image = Image.open(image_path)
    image = image.resize((128, 128))

    # crop image to 104x128, centered
    left = int((image.width - 104) / 2)
    top = 0
    right = left + 104
    bottom = top + 128
    image = image.crop((left, top, right, bottom))

    # convert image to grayscale
    image = image.convert("L")
    image.save(image_path)


def query_ha_state(entity_id):
    import requests
    import sys

    sys.path.insert(0, str(SRC_DIR))
    from secrets import HA_ACCESS_TOKEN, HA_BASE_URL

    url = HA_BASE_URL + "/states/" + entity_id
    headers = {"Authorization": "Bearer " + HA_ACCESS_TOKEN}
    res = requests.get(url, headers=headers)
    data = res.json()
    return data


@task
def wipe(c: Context, board_id: str) -> None:
    """Wipe the board with mpremote."""
    c.run(
        f'mpremote connect id:{board_id} exec --no-follow "'
        "import os, machine, rp2;"
        "os.umount('/');"
        "bdev = rp2.Flash();"
        "os.VfsLfs2.mkfs(bdev, progsize=256);"
        "vfs = os.VfsLfs2(bdev, progsize=256);"
        "os.mount(vfs, '/');"
        'machine.reset()"',
        pty=True,
        echo=True,
    )
    print("Board wiped, waiting for it to reboot...")
    time.sleep(3)
    print("Done!")


@task
def update_code(c: Context, board_id: str) -> None:
    """Update code on the board."""
    with c.cd(SRC_DIR):
        c.run("find . -name '.DS_Store' -delete", pty=True, echo=True)
        c.run(
            "find . -name '.pytest_cache' -type d -exec rm -r {} +", pty=True, echo=True
        )
        c.run(
            "find . -name '__pycache__' -type d -exec rm -r {} +", pty=True, echo=True
        )
        c.run(
            f"mpremote connect id:{board_id} cp -r . : + reset",
            pty=True,
            echo=True,
        )


def prepare(board_id: str) -> None:
    """Update secrets.py with the correct values for the board."""
    provisioning = get_provisioning(board_id)

    with (SRC_DIR / "secrets.py").open() as f:
        secrets = f.read()

    secrets = ast.parse(secrets)
    for node in secrets.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                var_name = target.id
                if var_name in provisioning:
                    node.value = ast.Constant(provisioning[var_name])
                elif var_name.lower() in provisioning:
                    state = query_ha_state(provisioning[var_name.lower()])
                    value = int(state.get("state", -1))
                    node.value = ast.Constant(value)

    with (SRC_DIR / "secrets.py").open("w") as f:
        f.write(ast.unparse(secrets))


def get_all_board_ids():
    # Here's an example output of `mpremote devs`:
    # /dev/cu.Bluetooth-Incoming-Port None 0000:0000 None None
    # /dev/cu.usbmodem101 e6614864d35f9934 2e8a:0005 MicroPython Board in FS mode
    # /dev/cu.usbmodem112201 e6614864d3417f36 2e8a:0005 MicroPython Board in FS mode
    output = subprocess.run(["mpremote", "devs"], stdout=subprocess.PIPE).stdout.decode(
        "utf-8"
    )
    lines = output.splitlines()
    ids = []
    for line in lines:
        if "Bluetooth" not in line:
            ids.append(line.split()[1])
    return ids


def get_provisioning(board_id: str) -> dict[str, str]:
    # load provisioning.yaml
    with (BASE_DIR / "provisioning.yaml").open() as f:
        provisioning = yaml.safe_load(f)
    provisioning = provisioning.get(board_id)
    if not provisioning:
        msg = "Couldn't find board %s in provisioning.yaml" % board_id
        raise ValueError(msg)
    return provisioning
