from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import os
from datetime import datetime
import csv

app = Flask(__name__, static_folder='static')
CORS(app)

# Arquivo para armazenar dados
DATA_FILE = os.path.join(os.path.dirname(__file__), 'dados_controle.csv')

def salvar_cadastro(dados):
    """Salva um cadastro no arquivo CSV"""
    try:
        # Criar arquivo se não existir
        if not os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Nome', 'Telefone', 'Email', 'Faturamento', 'Tipo_Empresa', 'Data_Cadastro', 'Status_Contato'])
        
        # Adicionar dados
        with open(DATA_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                dados.get('nome', ''),
                dados.get('telefone', ''),
                dados.get('email', ''),
                dados.get('faturamento', ''),
                dados.get('tipo_empresa', ''),
                datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
                'pendente'
            ])
        return True
    except Exception as e:
        print(f"Erro ao salvar: {e}")
        return False

def ler_cadastros():
    """Lê todos os cadastros do arquivo CSV"""
    try:
        if not os.path.exists(DATA_FILE):
            return []
        
        cadastros = []
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                cadastros.append(row)
        return cadastros
    except Exception as e:
        print(f"Erro ao ler: {e}")
        return []

# Função de cálculo do Livro Caixa (JavaScript no frontend)
def calcular_livro_caixa_js():
    return """
    function calcularLivroCaixa(faturamento) {
        const base = faturamento * 0.2; // 20% do faturamento
        
        // Faixas do IRPF
        let irpf = 0;
        if (base <= 2259.20) {
            irpf = 0;
        } else if (base <= 2826.65) {
            irpf = base * 0.075 - 169.44;
        } else if (base <= 3751.05) {
            irpf = base * 0.15 - 381.44;
        } else if (base <= 4664.68) {
            irpf = base * 0.225 - 662.77;
        } else {
            irpf = base * 0.275 - 896.00;
        }
        
        const iss = faturamento * 0.05; // 5%
        const inss = faturamento * 0.11; // 11%
        
        const total_mensal = Math.max(0, irpf) + iss + inss;
        
        return {
            mensal: total_mensal,
            anual: total_mensal * 12,
            aliquota: ((total_mensal / faturamento) * 100),
            base: base
        };
    }
    """

@app.route('/calcular', methods=['POST'])
def calcular():
    """Endpoint para cálculos dos regimes tributários"""
    try:
        dados = request.get_json()
        faturamento = float(dados.get('faturamento', 0))
        
        # Salvar cadastro
        salvar_cadastro({
            'nome': dados.get('nome', ''),
            'telefone': dados.get('telefone', ''),
            'email': dados.get('email', ''),
            'faturamento': faturamento,
            'tipo_empresa': dados.get('tipo_empresa', '')
        })
        
        # Cálculo Simples Nacional (Faixa 2, alíquota 16,75%)
        aliquota_simples = 16.75
        imposto_mensal_simples = faturamento * aliquota_simples / 100
        imposto_anual_simples = imposto_mensal_simples * 12
        
        # Cálculo Equiparação Hospitalar (Faixa 2, alíquota 5,93%)
        aliquota_equiparacao = 5.93
        imposto_mensal_equiparacao = faturamento * aliquota_equiparacao / 100
        imposto_anual_equiparacao = imposto_mensal_equiparacao * 12
        
        return jsonify({
            'success': True,
            'simples_nacional': {
                'mensal': round(imposto_mensal_simples, 2),
                'anual': round(imposto_anual_simples, 2),
                'aliquota': aliquota_simples
            },
            'equiparacao_hospitalar': {
                'mensal': round(imposto_mensal_equiparacao, 2),
                'anual': round(imposto_anual_equiparacao, 2),
                'aliquota': aliquota_equiparacao
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/login', methods=['POST'])
def admin_login():
    """Login da área administrativa"""
    dados = request.get_json()
    usuario = dados.get('usuario', '')
    senha = dados.get('senha', '')
    
    if usuario == 'Elfem/154' and senha == '5567E':
        return jsonify({'success': True})
    else:
        return jsonify({'success': False}), 401

@app.route('/admin/dados', methods=['GET'])
def admin_dados():
    """Retorna dados para área administrativa"""
    try:
        cadastros = ler_cadastros()
        
        # Converter para formato esperado pelo JavaScript
        dados_formatados = []
        for cadastro in cadastros:
            dados_formatados.append({
                'Data_Cadastro': cadastro.get('Data_Cadastro', ''),
                'Nome': cadastro.get('Nome', ''),
                'Telefone': cadastro.get('Telefone', ''),
                'Email': cadastro.get('Email', ''),
                'Faturamento': cadastro.get('Faturamento', '0'),
                'Tipo_Empresa': cadastro.get('Tipo_Empresa', ''),
                'Status_Contato': cadastro.get('Status_Contato', 'pendente')
            })
        
        return jsonify({
            'success': True,
            'dados': dados_formatados,
            'total': len(dados_formatados)
        })
    except Exception as e:
        print(f"Erro na API dados: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/estatisticas', methods=['GET'])
def admin_estatisticas():
    """Retorna estatísticas para área administrativa"""
    try:
        cadastros = ler_cadastros()
        hoje = datetime.now().strftime('%d/%m/%Y')
        
        # Contar cadastros de hoje
        cadastros_hoje = 0
        emails_unicos = set()
        
        for cadastro in cadastros:
            data_cadastro = cadastro.get('Data_Cadastro', '')
            if hoje in data_cadastro:
                cadastros_hoje += 1
            
            email = cadastro.get('Email', '')
            if email:
                emails_unicos.add(email)
        
        return jsonify({
            'success': True,
            'total_usuarios': len(emails_unicos),
            'total_simulacoes': len(cadastros),
            'cadastros_hoje': cadastros_hoje
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    """Serve arquivos estáticos"""
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

@app.route('/admin/marcar_contato', methods=['POST'])
def marcar_contato():
    try:
        dados = request.get_json()
        email = dados.get('email')
        status = dados.get('status')
        
        if not email:
            return jsonify({'success': False, 'error': 'Email não fornecido'})
        
        # Carregar dados existentes
        dados_existentes = []
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                dados_existentes = list(reader)
        
        # Atualizar status do contato
        for item in dados_existentes:
            if item.get('Email') == email:
                item['Status_Contato'] = status
                break
        
        # Salvar dados atualizados
        if dados_existentes:
            with open(DATA_FILE, 'w', newline='', encoding='utf-8') as f:
                fieldnames = ['Nome', 'Telefone', 'Email', 'Faturamento', 'Tipo_Empresa', 'Data_Cadastro', 'Status_Contato']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for item in dados_existentes:
                    if 'Status_Contato' not in item:
                        item['Status_Contato'] = 'pendente'
                    writer.writerow(item)
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    # Configuração para produção
    import os
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)

