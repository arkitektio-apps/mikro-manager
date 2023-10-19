import PyInstaller.__main__
import shutil


app = "MikroManager"

PyInstaller.__main__.run(
    [
        "entrypoint.py",
        "--clean",
        "--windowed",
        "--onedir",
        f"--name={app}",
        "--noconfirm",
        "--additional-hooks-dir=hooks",
    ]
)

shutil.make_archive("./dist/MikroManager", "zip", "./dist/MikroManager")
print("Made archive")
