from domain.models import CommandType, RequestMessage


class MessageParser:
    """Parser responsável por deserializar strings de mensagens nos modelos de Domínio."""

    @staticmethod
    def parse(raw_text: str) -> RequestMessage:
        parts = raw_text.strip().split(" ", 2)
        if len(parts) < 2:
            return RequestMessage(
                seq_num="0",
                command=CommandType.UNKNOWN,
                raw_command="",
                args="",
                is_valid_format=False
            )

        raw_seq = parts[0]
        raw_command = parts[1]
        args = parts[2] if len(parts) == 3 else ""

        # Se SEQ_NUM for numérico, mantém; caso contrário, adota "0"
        is_seq_valid = raw_seq.isdigit()
        seq_num = raw_seq if is_seq_valid else "0"

        return RequestMessage(
            seq_num=seq_num,
            command=CommandType.from_string(raw_command),
            raw_command=raw_command,
            args=args,
            is_valid_format=is_seq_valid
        )
