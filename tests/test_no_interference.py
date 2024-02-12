from mikro_manager.main import MikroManager
import pytest


@pytest.mark.qt
def test_fetch_from_windowed_grant(qtbot):
    widget = MikroManager()
    qtbot.addWidget(widget)
