import logging

import sys
from arkitekt.builders import publicqt
from arkitekt.qt.magic_bar import MagicBar, ProcessState


from qtpy import QtCore, QtGui, QtWidgets
from mikro_manager.env import get_asset_file

logger = logging.getLogger(__name__)

from .bridge import MMBridge



class MikroManager(QtWidgets.QMainWindow):
    """The main window of the Gucker application

    This window is the main window of the Gucker application. It is responsible for
    watching a directory and uploading new files to the server.
    """

    is_watching = QtCore.Signal(bool)
    is_uploading = QtCore.Signal(str)
    has_uploaded = QtCore.Signal(str)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        # self.setWindowIcon(QtGui.QIcon(os.path.join(os.getcwd(), 'share\\assets\\icon.png')))
        self.setWindowIcon(QtGui.QIcon(get_asset_file("logo.ico")))

        self.setStyleSheet("background-color: #1e1e1e; color: #ffffff;")
        self.settings = QtCore.QSettings("github.io.jhnnsrs.mikro-manager", "0.0.1")
        self.base_dir = self.settings.value("base_dir", "")
        self.export_dir = self.settings.value("export_dir", "")

        self.grace_period = 2
        # Create a bitmap to use toggle for the watching state
        self.watching = False
        self.watching_bitmap = QtGui.QPixmap(get_asset_file("idle.png"))
        self.idle_bitmap = QtGui.QPixmap(get_asset_file("idle.png"))
       

        self.center_label = QtWidgets.QLabel()
        self.center_label.setPixmap(self.idle_bitmap)
        self.center_label.setScaledContents(True)


        self.app = publicqt(
            identifier="github.io.jhnnsrs.mikro-manager",
            version="0.0.1",
            parent=self,
            settings=self.settings,
        )


        self.magic_bar = MagicBar(self.app, dark_mode=True)
        self.magic_bar.app_state_changed.connect(
            lambda: self.button.setDisabled(
                self.magic_bar.process_state == ProcessState.PROVIDING
            )
        )
        self.magic_bar.magicb.setDisabled(True)
        self.button = QtWidgets.QPushButton("Connect")
        self.button.clicked.connect(self.on_connect)

        self.statusBar = QtWidgets.QStatusBar()
        self.setStatusBar(self.statusBar)

        self.centralWidget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.center_label)
        layout.addWidget(self.button)
        layout.addWidget(self.magic_bar)
        self.centralWidget.setLayout(layout)
        self.setCentralWidget(self.centralWidget)



        self.bridge = MMBridge()

        self.app.rekuest.register()(self.bridge.snap_image)
        self.app.rekuest.register()(self.bridge.acquire_2d)
        self.app.rekuest.register()(self.bridge.acquire_3d)
        self.app.rekuest.register()(self.bridge.retrieve_positions)
        self.app.rekuest.register()(self.bridge.move_to_position_xy)
        self.app.rekuest.register()(self.bridge.set_auto_focusoffset)
        self.setWindowTitle("Mikro-Manager")

        self.connected = False
        self.on_connect()



    def on_connect(self):
        try:
            self.bridge.start()
            self.button.setText("Open Settings")
            self.connected = True
            self.magic_bar.magicb.setDisabled(False)
        except:
            self.button.setText("Re-Connect")
            logger.error("Could not connect-to Mikro Manager", exc_info=True)
            self.statusBar.showMessage("Could not connect to MicroManager. Is it running?")
            self.connected = False
            self.magic_bar.magicb.setDisabled(True)

    


    


def main(**kwargs) -> None:
    """Entrypoint for the application"""
    qtapp = QtWidgets.QApplication(sys.argv)
    main_window = MikroManager(**kwargs)
    main_window.show()
    sys.exit(qtapp.exec_())


if __name__ == "__main__":
    main()
