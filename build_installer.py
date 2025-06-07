import subprocess
import sys
import os


def build():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(root_dir, "icon", "ALLtoCEF.ico")
    pyinstaller_cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconsole",
        "--onefile",
        f"--icon={icon_path}",
        os.path.join(root_dir, "main.py"),
    ]
    subprocess.run(pyinstaller_cmd, check=True)


if __name__ == "__main__":
    build()
