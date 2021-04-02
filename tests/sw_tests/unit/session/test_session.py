import pytest
import chipscopy.api.session
from chipscopy.api.session import create_session, delete_session


def test_session_connection_refused():
    hw_url = "TCP:localhost:9998"
    cs_url = "TCP:localhost:9999"
    with pytest.raises(ConnectionRefusedError):
        create_session(hw_server_url=hw_url, cs_server_url=cs_url)


def test_session_create(mocker):
    mock_session = mocker.patch("chipscopy.api.session.Session")
    # This test verifies that the session is being constructed with given
    # arguments. Also makes sure no developer accidentally changes the
    # important default argument values without making a test fail as
    # a warning.
    assert mock_session is chipscopy.api.session.Session
    xvc_url = "TCP:localhost:9997"
    hw_url = "TCP:localhost:9998"
    cs_url = "TCP:localhost:9999"
    create_session(hw_server_url=hw_url, cs_server_url=cs_url, xvc_server_url=xvc_url)

    # Verify no non-kwargs exists
    session_args = mock_session.call_args[0]
    assert len(session_args) == 0

    session_kwargs = mock_session.call_args[1]
    assert session_kwargs["cs_server_url"] == cs_url
    assert session_kwargs["hw_server_url"] == hw_url
    assert session_kwargs["xvc_server_url"] == xvc_url
    assert session_kwargs["disable_core_scan"] is False


def test_session_delete(mocker):
    mocker.patch("chipscopy.api.session.Session")
    mock_disconnect = mocker.patch("chipscopy.api.session.disconnect")
    # assert mock_disconnect is chipscopy.client.disconnect
    hw_url = "TCP:localhost:9998"
    cs_url = "TCP:localhost:9999"
    mock_session = create_session(hw_server_url=hw_url, cs_server_url=cs_url)
    delete_session(mock_session)
    # This verifies that delete actually calls disconnect
    mock_disconnect.assert_called()
