import time
from pathlib import Path

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
def initial_setup(c: Context, board_id: str):
    """Install dependencies and copy project files to the board."""
    with c.cd(SRC_DIR):
        if MICROPYTHON_DEPENDENCIES:
            deps = " ".join(MICROPYTHON_DEPENDENCIES)
            c.run(
                f"mpremote connect id:{board_id} "
                f"mip install {deps} + "
                "cp -r . : + "
                "reset",
                pty=True,
                echo=True,
            )
        else:
            c.run(
                f"mpremote connect id:{board_id} " "cp -r . : + " "reset",
                pty=True,
                echo=True,
            )


@task
def update_code(c: Context, board_id: str):
    """Update code on the board."""
    # mpremote connect id:e6614864d3269c34 \
    #   cp -r . : + \
    #   reset
    with c.cd(SRC_DIR):
        c.run(
            f"mpremote connect id:{board_id} " "cp -r . : + " "reset",
            pty=True,
            echo=True,
        )
