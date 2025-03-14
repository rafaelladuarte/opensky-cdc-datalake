# Imagem base do Python
FROM python:3.9-slim

# Diretório de trabalho
WORKDIR /app

# Instala dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia os arquivos do projeto
COPY . .

# Comando de inicialização
CMD ["python", "app/main.py"]