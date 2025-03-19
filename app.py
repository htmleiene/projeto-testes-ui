from flask import Flask, request, render_template, jsonify
import json
import time
import os
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from urllib.parse import urlparse
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

app = Flask(__name__)

# Configuração de logs
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Arquivo para armazenar os dados dos testes
RESULTADOS_PATH = "data/resultados.json"



def inicializar_webdriver():
    try:
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')

        service = Service(ChromeDriverManager(driver_version="134.0.6998.89").install())  
        driver = webdriver.Chrome(service=service, options=options)

        logger.info("WebDriver inicializado com sucesso.")
        return driver
    except Exception as e:
        logger.error(f"Erro ao inicializar o WebDriver: {e}")
        raise

# Função para rodar o teste de usabilidade
def testar_usabilidade(url):
    try:
        driver = inicializar_webdriver()
        driver.get(url)
        logger.info(f"Acessando a URL: {url}")

        start_time = time.time()
        driver.get(url)
        WebDriverWait(driver, 10).until(lambda d: d.execute_script('return document.readyState') == 'complete')
        end_time = time.time()

        tempo_resposta = round(end_time - start_time, 2)
        resultado = {"url": url, "tempo_resposta": tempo_resposta, "status": "sucesso"}
        logger.info(f"Teste de usabilidade finalizado. Tempo de resposta: {tempo_resposta} segundos")


        # Salvar resultado no JSON
        salvar_resultado(resultado)
        return resultado
    except Exception as e:
        logger.error(f"Erro ao executar o teste de usabilidade: {e}")
        return {"url": url, "tempo_resposta": None, "status": "erro"}

# Função para salvar resultados em JSON (com tratamento de erros)
def salvar_resultado(dados):
    try:
        os.makedirs(os.path.dirname(RESULTADOS_PATH), exist_ok=True)
        logger.info(f"Diretório 'data' verificado/criado.")

        if not os.path.exists(RESULTADOS_PATH) or os.stat(RESULTADOS_PATH).st_size == 0:
            historico = []
        else:
            with open(RESULTADOS_PATH, "r", encoding="utf-8") as f:
                historico = json.load(f)

        historico.append(dados)

        with open(RESULTADOS_PATH, "w", encoding="utf-8") as f:
            json.dump(historico, f, indent=4, ensure_ascii=False)
        logger.info(f"Resultado salvo com sucesso: {dados}")
    except Exception as e:
        logger.error(f"Erro ao salvar resultado: {e}")

def validar_url(url):
    try:
        resultado = urlparse(url)
        return all([resultado.scheme, resultado.netloc])  # Verifica se tem esquema (http/https) e domínio
    except:
        return False

@app.route('/testar', methods=['POST'])
def testar():
    data = request.json
    url = data.get("url")
    
    if not url:
        return jsonify({"erro": "URL não informada"}), 400

    if not validar_url(url):
        return jsonify({"erro": "URL inválida"}), 400

    resultado = testar_usabilidade(url)
    return jsonify(resultado)

# Rota para o dashboard
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

# Rota para fornecer os dados para os gráficos
@app.route('/dados')
def get_dados():
    if not os.path.exists(RESULTADOS_PATH):
        return jsonify([])

    try:
        with open(RESULTADOS_PATH, "r") as f:
            historico = json.load(f)
        return jsonify(historico)
    except Exception as e:
        logger.error(f"Erro ao carregar dados: {e}")
        return jsonify([])

# Página inicial
@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)