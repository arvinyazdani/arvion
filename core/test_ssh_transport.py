from unittest.mock import call, patch, MagicMock

from django.test import SimpleTestCase

from ops import ssh_tcp_proxy


class SSHTransportTests(SimpleTestCase):
    def run_relay(self, readiness, incoming=(), outgoing=(), writes=None):
        sock = MagicMock()
        sock.__enter__.return_value = sock
        sock.recv.side_effect = incoming
        with patch('sys.argv', ['proxy', 'example.invalid', '22']), \
                patch.object(ssh_tcp_proxy.socket, 'socket', return_value=sock), \
                patch.object(ssh_tcp_proxy.select, 'select', side_effect=lambda *_: ([(sock if fd == 'socket' else 0) for fd in next(readiness)], [], [])), \
                patch.object(ssh_tcp_proxy.os, 'read', side_effect=outgoing), \
                patch.object(ssh_tcp_proxy.os, 'write', side_effect=writes) as write:
            ssh_tcp_proxy.main()
        return sock, write

    def test_mss_is_set_before_and_after_connect_and_socket_is_closed(self):
        sock, _ = self.run_relay(iter([['socket']]), incoming=[b''])
        segment = call.setsockopt(ssh_tcp_proxy.socket.IPPROTO_TCP, ssh_tcp_proxy.socket.TCP_MAXSEG, 512)
        sock.assert_has_calls([segment, call.connect(('example.invalid', 22)), segment])
        sock.__exit__.assert_called_once()

    def test_socket_data_is_fully_written_even_on_partial_pipe_write(self):
        _, write = self.run_relay(iter([['socket'], ['socket']]), incoming=[b'ab', b''], writes=[1, 1])
        self.assertEqual([bytes(c.args[1]) for c in write.call_args_list], [b'ab', b'b'])

    def test_stdin_is_relayed_and_eof_closes_connection(self):
        sock, _ = self.run_relay(iter([[0], [0]]), outgoing=[b'input', b''])
        sock.sendall.assert_called_once_with(b'input')
        sock.__exit__.assert_called_once()

    def test_invalid_port_is_rejected_before_opening_socket(self):
        with patch('sys.argv', ['proxy', 'example.invalid', '0']), \
                patch.object(ssh_tcp_proxy.socket, 'socket') as socket_factory, \
                patch('sys.stderr'), self.assertRaises(SystemExit):
            ssh_tcp_proxy.main()
        socket_factory.assert_not_called()
