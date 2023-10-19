from mikro_manager.main import MMBridge
import pytest


@pytest.mark.qt
def test_fetch_from_windowed_grant(qtbot):
    widget = MMBridge()
    qtbot.addWidget(widget)
