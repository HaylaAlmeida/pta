FROM python:3.12-slim

# Instala watchdog com versão fixada para suportar live reload com watchmedo
RUN pip install --no-cache-dir watchdog==6.0.0

WORKDIR /app

COPY pta-server/ /app/

EXPOSE 11550

# Executa main.py com watchmedo monitorando alterações nos arquivos .py para live reload automático
CMD ["watchmedo", "auto-restart", "--directory=/app", "--pattern=*.py", "--recursive", "--", "python", "-u", "main.py"]
