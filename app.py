from flask import Flask, render_template, request, jsonify
import mysql.connector
from gaia_logic import GaiaLogic
import os  
from dotenv import load_dotenv 

app = Flask(__name__)
ai = GaiaLogic()

DB_CONFIG = {
    'host': os.getenv("DB_HOST"),
    'user': os.getenv("DB_USER"),
    'password': os.getenv("DB_PASSWORD"),
    'database': os.getenv("DB_DATABASE")
}

def conectar():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as err:
        print(f"Erro de conexão com o banco: {err}")
        return None

def formatar_resultados_sql(cursor):
    """Formata os resultados da consulta SQL de forma inteligente."""
    try:
        resultados = cursor.fetchall()
        
        # <<< MUDANÇA AQUI >>>
        if not resultados:
            # Mensagem de "não encontrado" agora inclui o link.
            return (
                "<p>Não encontrei nenhuma informação no meu banco de dados que corresponda à sua pesquisa. "
                "<br>Para garantir, você pode verificar as informações no "
                "<a href='https://portal.cmp.ifsp.edu.br/' target='_blank' style='color: #007bff; text-decoration: none;'>portal oficial do IFSP Campinas</a>.</p>"
            )

        colunas = [desc[0] for desc in cursor.description]

        if len(resultados) == 1 and len(colunas) == 1:
            valor = resultados[0][0]
            nome_coluna = colunas[0]
            return f"<p>O resultado para <b>'{nome_coluna}'</b> é: <b>{valor}</b>.</p>"

        style = "<style>table{width:100%;border-collapse:collapse;margin-top:10px;} th,td{padding:8px;text-align:left;border-bottom:1px solid #ddd;} th{background-color:#f2f2f2;font-weight:bold;} tr:hover{background-color:#f5f5f5;}</style>"
        html_table = f"{style}<table><thead><tr>"
        for col in colunas:
            html_table += f"<th>{col.capitalize().replace('_', ' ')}</th>"
        html_table += "</tr></thead><tbody>"

        for linha in resultados:
            html_table += "<tr>"
            for item in linha:
                html_table += f"<td>{item}</td>"
            html_table += "</tr>"

        html_table += "</tbody></table>"
        return html_table

    except Exception as e:
        print(f"Erro ao formatar resultados: {e}")
        return "<p>Ocorreu um erro ao processar os dados do banco.</p>"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')
    if not user_message:
        return jsonify({'error': 'A mensagem não pode ser vazia.'}), 400

    print(f"Mensagem recebida do usuário: {user_message}")

    response_data = ai.prompt(user_message)
    response_message = response_data.get("message")
    sql_query = response_data.get("sql")

    if sql_query:
        print(f"IA gerou SQL: {sql_query}")
        conn = conectar()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute(sql_query)
                resultado_db = formatar_resultados_sql(cursor)
                response_message += f"<br><br><b>Resultados Encontrados:</b><br>{resultado_db}"
            except mysql.connector.Error as err:
                print(f"Erro SQL: {err}")
                response_message = "Ocorreu um erro ao consultar o banco de dados. A consulta gerada pode estar incorreta."
            finally:
                if 'cursor' in locals() and cursor:
                    cursor.close()
                if conn.is_connected():
                    conn.close()
        else:
            response_message = "Não foi possível conectar ao banco de dados."

    print(f"Resposta final enviada ao usuário: {response_message}")
    return jsonify({'response': response_message})

if __name__ == '__main__':
    app.run(debug=True)