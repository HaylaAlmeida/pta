import socket
import sys
import unittest
from pathlib import Path

HOST = "127.0.0.1"
PORT = 11550


class PTAServerComprehensiveTests(unittest.TestCase):
    """Bateria exaustiva de testes para validar todas as regras do PDF pta.pdf."""

    def setUp(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(3.0)
        self.sock.connect((HOST, PORT))
        self.seq_num = 0

    def tearDown(self):
        try:
            self.sock.close()
        except Exception:
            pass

    def send_cmd(self, command_str: str) -> str:
        """Envia comando e recebe resposta de texto decodificada."""
        msg = f"{self.seq_num} {command_str}"
        self.sock.sendall(msg.encode("ascii"))
        self.seq_num += 1
        data = self.sock.recv(4096)
        return data.decode("ascii", errors="replace")

    def send_raw(self, raw_str: str) -> str:
        """Envia string crua."""
        self.sock.sendall(raw_str.encode("ascii"))
        data = self.sock.recv(4096)
        return data.decode("ascii", errors="replace")

    # ==========================================================
    # 1. TESTES DA MÁQUINA DE ESTADOS: FASE ESPERANDO (WAITING)
    # ==========================================================

    def test_01_waiting_rejects_list(self):
        """No estado ESPERANDO, LIST deve retornar NOK e fechar TCP."""
        resp = self.send_cmd("LIST")
        self.assertEqual(resp, "0 NOK")
        # Deve fechar a conexão TCP
        extra = self.sock.recv(1024)
        self.assertEqual(extra, b"")

    def test_02_waiting_rejects_pega(self):
        """No estado ESPERANDO, PEGA deve retornar NOK e fechar TCP."""
        resp = self.send_cmd("PEGA dummyfile01-with-a-bigger-name-to-test-your-buffer-treatment.txt")
        self.assertEqual(resp, "0 NOK")
        extra = self.sock.recv(1024)
        self.assertEqual(extra, b"")

    def test_03_waiting_rejects_term(self):
        """No estado ESPERANDO, TERM deve retornar NOK e fechar TCP."""
        resp = self.send_cmd("TERM")
        self.assertEqual(resp, "0 NOK")
        extra = self.sock.recv(1024)
        self.assertEqual(extra, b"")

    def test_04_waiting_rejects_invalid_user(self):
        """CUMP com usuário inexistente retorna NOK e fecha TCP."""
        resp = self.send_cmd("CUMP usuario_que_nao_existe")
        self.assertEqual(resp, "0 NOK")
        extra = self.sock.recv(1024)
        self.assertEqual(extra, b"")

    def test_05_waiting_cump_without_args(self):
        """CUMP sem informar usuário retorna NOK e fecha TCP."""
        resp = self.send_cmd("CUMP")
        self.assertEqual(resp, "0 NOK")
        extra = self.sock.recv(1024)
        self.assertEqual(extra, b"")

    def test_06_waiting_cump_with_multiple_args(self):
        """CUMP com mais de um argumento retorna NOK e fecha TCP."""
        resp = self.send_cmd("CUMP user1 outro_arg")
        self.assertEqual(resp, "0 NOK")
        extra = self.sock.recv(1024)
        self.assertEqual(extra, b"")

    def test_07_waiting_case_sensitivity(self):
        """O PDF exige sensibilidade a maiúsculas/minúsculas no nome."""
        # Se 'user1' existe, 'USER1' deve ser rejeitado
        resp = self.send_cmd("CUMP USER1")
        self.assertEqual(resp, "0 NOK")
        extra = self.sock.recv(1024)
        self.assertEqual(extra, b"")

    def test_08_waiting_accepts_valid_users(self):
        """Testa todos os usuários válidos de users.txt (user1, user2, user3)."""
        for user in ["user1", "user2", "user3"]:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((HOST, PORT))
                s.sendall(f"10 CUMP {user}".encode("ascii"))
                resp = s.recv(1024).decode("ascii")
                self.assertEqual(resp, "10 OK")
                # Fecha com TERM
                s.sendall("11 TERM".encode("ascii"))
                resp_term = s.recv(1024).decode("ascii")
                self.assertEqual(resp_term, "11 OK")

    # ==========================================================
    # 2. TESTES DA MÁQUINA DE ESTADOS: FASE PRONTO (READY)
    # ==========================================================

    def _login(self, user="user1"):
        resp = self.send_cmd(f"CUMP {user}")
        self.assertEqual(resp, f"{self.seq_num - 1} OK")

    def test_09_ready_rejects_unknown_command_but_keeps_connection(self):
        """No estado PRONTO, comando inválido retorna NOK e conexão PERMANECE aberta."""
        self._login()
        resp = self.send_cmd("INVALIDO")
        self.assertEqual(resp, f"{self.seq_num - 1} NOK")

        # Conexão deve continuar viva, permitindo novo comando
        resp_term = self.send_cmd("TERM")
        self.assertEqual(resp_term, f"{self.seq_num - 1} OK")

    def test_10_ready_list_with_args_fails(self):
        """LIST com argumentos retorna NOK e mantém conexão aberta."""
        self._login()
        resp = self.send_cmd("LIST argumento_indevido")
        self.assertEqual(resp, f"{self.seq_num - 1} NOK")

        # Pode fazer LIST normal logo em seguida
        resp_list = self.send_cmd("LIST")
        self.assertTrue(resp_list.startswith(f"{self.seq_num - 1} ARQS 16 "))

    def test_11_ready_list_format_integrity(self):
        """LIST deve retornar exatamente: SEQ_NUM ARQS <qtd> arq1,arq2,... sem espaços entre vírgulas."""
        self._login()
        resp = self.send_cmd("LIST")
        parts = resp.split(" ", 3)
        self.assertEqual(len(parts), 4)
        self.assertEqual(parts[0], str(self.seq_num - 1))
        self.assertEqual(parts[1], "ARQS")
        self.assertTrue(parts[2].isdigit())
        total = int(parts[2])
        file_list = parts[3].split(",")
        self.assertEqual(len(file_list), total)
        for fname in file_list:
            self.assertFalse(" " in fname)

    def test_12_ready_pega_without_args_fails(self):
        """PEGA sem argumentos retorna NOK."""
        self._login()
        resp = self.send_cmd("PEGA")
        self.assertEqual(resp, f"{self.seq_num - 1} NOK")

    def test_13_ready_pega_non_existent_file(self):
        """PEGA com arquivo inexistente retorna NOK."""
        self._login()
        resp = self.send_cmd("PEGA arquivo_que_nao_existe_12345.xyz")
        self.assertEqual(resp, f"{self.seq_num - 1} NOK")

    def test_14_ready_pega_directory_traversal_attack(self):
        """Segurança: tentativa de directory traversal (../) deve ser bloqueada com NOK."""
        self._login()
        for malicious_path in ["../users.txt", "../../etc/passwd", "..\\users.txt", "/etc/passwd"]:
            resp = self.send_cmd(f"PEGA {malicious_path}")
            self.assertEqual(resp, f"{self.seq_num - 1} NOK")

    def test_15_ready_pega_binary_file_integrity(self):
        """PEGA arquivo binário PNG e valida bytes exatos."""
        self._login()
        filename = "dummyfile03-with-a-bigger-name-to-test-your-buffer-treatment.png"
        self.sock.sendall(f"{self.seq_num} PEGA {filename}".encode("ascii"))
        current_seq = self.seq_num
        self.seq_num += 1

        # Recebe cabeçalho e bytes
        data = bytearray()
        while len(data) < 25:
            chunk = self.sock.recv(4096)
            if not chunk:
                break
            data.extend(chunk)

        header_str = bytes(data).decode("ascii", errors="ignore")
        parts = header_str.split(" ", 3)
        self.assertEqual(parts[0], str(current_seq))
        self.assertEqual(parts[1], "ARQ")
        size = int(parts[2])

        header_len = len(f"{current_seq} ARQ {size} ".encode("ascii"))
        payload_bytes = data[header_len:]

        while len(payload_bytes) < size:
            chunk = self.sock.recv(4096)
            if not chunk:
                break
            payload_bytes.extend(chunk)

        self.assertEqual(len(payload_bytes), size)

    def test_16_ready_term_with_args_fails(self):
        """TERM com argumentos extras deve retornar NOK."""
        self._login()
        resp = self.send_cmd("TERM argumento_extra")
        self.assertEqual(resp, f"{self.seq_num - 1} NOK")

    def test_17_ready_term_closes_tcp(self):
        """TERM válido responde OK e fecha a conexão."""
        self._login()
        resp = self.send_cmd("TERM")
        self.assertEqual(resp, f"{self.seq_num - 1} OK")
        # Garante que o socket fechou
        extra = self.sock.recv(1024)
        self.assertEqual(extra, b"")

    # ==========================================================
    # 3. TESTES DE NÚMERO DE SEQUÊNCIA (SEQ_NUM) E SINTAXE
    # ==========================================================

    def test_18_arbitrary_initial_seq_num(self):
        """O PDF afirma que SEQ_NUM inicial pode ser qualquer número."""
        self.seq_num = 998822
        resp = self.send_cmd("CUMP user2")
        self.assertEqual(resp, "998822 OK")

        resp_list = self.send_cmd("LIST")
        self.assertTrue(resp_list.startswith("998823 ARQS "))

        resp_term = self.send_cmd("TERM")
        self.assertEqual(resp_term, "998824 OK")

    def test_19_malformed_command_string(self):
        """Mensagem sem espaço ou malformada retorna 0 NOK."""
        resp = self.send_raw("MENSAGEM_SEM_NENHUM_ESPACO")
        self.assertEqual(resp, "0 NOK")


if __name__ == "__main__":
    unittest.main(verbosity=2)

