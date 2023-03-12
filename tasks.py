import time
from pathlib import Path

from PIL import Image
from invoke import task, Context

BASE_DIR = Path(__file__).parent.resolve(strict=True)
SRC_DIR = BASE_DIR / "src"

MICROPYTHON_DEPENDENCIES = [
    # "github:miguelgrinberg/microdot/src/microdot.py",
    # "github:miguelgrinberg/microdot/src/microdot_asyncio.py",
]


@task
def wipe(c: Context, board_id: str):
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
def list(c: Context):
    """List connected boards with mpremote."""
    c.run("mpremote devs", pty=True, echo=True)


@task
def download_image(c: Context):
    import requests
    import sys

    sys.path.insert(0, str(SRC_DIR))
    from secrets import HA_ACCESS_TOKEN, HA_BASE_URL, HA_PLANT_ID

    url = HA_BASE_URL + "/states/" + HA_PLANT_ID
    headers = {"Authorization": "Bearer " + HA_ACCESS_TOKEN}
    res = requests.get(url, headers=headers)
    data = res.json()
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


@task(pre=[download_image])
def initial_setup(c: Context, board_id: str):
    """Install dependencies and copy project files to the board."""
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
def update_code(c: Context, board_id: str):
    """Update code on the board."""
    with c.cd(SRC_DIR):
        c.run("find . -name '.DS_Store' -delete", pty=True, echo=True)
        c.run(
            f"mpremote connect id:{board_id} cp -r . : + reset",
            pty=True,
            echo=True,
        )
