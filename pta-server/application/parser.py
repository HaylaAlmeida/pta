from domain.models import CommandType, RequestMessage


class MessageParser:
    """Parser responsável por deserializar strings de mensagens nos modelos de Domínio."""

    @staticmethod
    def parse(raw_text: str) -> RequestMessage:
        parts = raw_text.strip().split(" ", 2)
        if len(parts) < 2:
            return RequestMessage(
                seq_num="-1",
                command=CommandType.UNKNOWN,
                raw_command="",
                args="",
                is_valid_format=False
            )

        seq_num = parts[0]
        raw_command = parts[1]
        args = parts[2] if len(parts) == 3 else ""
        is_valid = seq_num.isdigit()

        return RequestMessage(
            seq_num=seq_num,
            command=CommandType.from_string(raw_command),
            raw_command=raw_command,
            args=args,
            is_valid_format=is_valid
        )

