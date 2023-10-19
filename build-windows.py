import PyInstaller.__main__
import shutil


APP_NAME = "MikroManager"

PyInstaller.__main__.run(
    [
        "entrypoint.py",
        "--clean",
        "--windowed",
        "--onedir",
        f"--name={APP_NAME}",
        "--noconfirm",
        "--additional-hooks-dir=hooks",
    ]
)

shutil.make_archive("./dist/MikroManager", "zip", "./dist/MikroManager")
print("Made archive")
