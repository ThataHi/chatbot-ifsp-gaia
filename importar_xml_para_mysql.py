import xml.etree.ElementTree as ET
import mysql.connector
import re
from tradutor_horarios import traduzir_horario_completo
import os 
from dotenv import load_dotenv

NAMESPACES = {'ss': 'urn:schemas-microsoft-com:office:spreadsheet'}
DB_CONFIG = {
    'host': os.getenv("DB_HOST"),
    'user': os.getenv("DB_USER"),
    'password': os.getenv("DB_PASSWORD"),
    'database': os.getenv("DB_DATABASE")
}

def extrair_semestre(texto_disciplina):
    """Extrai o número do semestre do nome da disciplina (ex: 'tads.1 - ...')."""
    match = re.search(r'\.(\d+)\s*-', texto_disciplina)
    if match:
        return int(match.group(1))
    return None 

def extrair_turno(texto_horario):
    """Extrai o turno principal do horário."""
    texto_horario = texto_horario.lower()
    if "noturno" in texto_horario:
        return "Noturno"
    if "vespertino" in texto_horario:
        return "Vespertino"
    if "matutino" in texto_horario:
        return "Matutino"
    return "Indefinido"

def carregar_dados(xml_path):
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        table = root.find('.//ss:Table', NAMESPACES)
        if table is None: return []
        
        linhas = table.findall('ss:Row', NAMESPACES)
        if not linhas: return []
        
        dados = []
        for row in linhas[1:]:
            celulas = row.findall('ss:Cell', NAMESPACES)
            linha_dados = {}
            for cell in celulas:
                index_attr = cell.get('{urn:schemas-microsoft-com:office:spreadsheet}Index')
                if index_attr:
                    idx = int(index_attr)
                    data_node = cell.find('ss:Data', NAMESPACES)
                    if data_node is not None and data_node.text:
                        linha_dados[idx] = data_node.text.strip()

            codigo_original = linha_dados.get(1)
            disciplina_raw = linha_dados.get(2, '')
            if not codigo_original or not disciplina_raw:
                continue

            # Extração inteligente dos novos dados
            semestre = extrair_semestre(disciplina_raw)
            horario_raw = linha_dados.get(6, 'A ser definido').strip()
            turno = extrair_turno(horario_raw)
            horario_traduzido = " | ".join(traduzir_horario_completo(horario_raw))

            # Limpa o nome da disciplina para não ter o código junto
            disciplina_limpa = disciplina_raw.split(' - ', 1)[-1]

            item = {
                'codigo_disciplina': codigo_original,
                'disciplina': disciplina_limpa,
                'curso': linha_dados.get(3, ''),
                'semestre': semestre,
                'professor': linha_dados.get(5, ''),
                'horario': horario_traduzido,
                'turno': turno,
                'sala': linha_dados.get(11, 'Não definida')
            }
            dados.append(item)
        return dados
    except Exception as e:
        print(f"Erro ao carregar dados do XML: {e}")
        return []

def importar_para_banco(dados):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("Conectado ao banco de dados.")
        
        # O script de criação da tabela já foi executado, então só inserimos.
        # TRUNCATE é opcional se você recriou a tabela com DROP/CREATE.
        cursor.execute("TRUNCATE TABLE dados_ifsp")
        print("Tabela 'dados_ifsp' limpa com sucesso.")

        sql = """
            INSERT INTO dados_ifsp 
            (codigo_disciplina, disciplina, curso, semestre, professor, horario, turno, sala)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        registros = [tuple(d.values()) for d in dados]

        cursor.executemany(sql, registros)
        conn.commit()
        print(f"{cursor.rowcount} registros importados com sucesso para a nova estrutura.")

    except mysql.connector.Error as err:
        print(f"Erro de banco de dados: {err}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
            print("Conexão com o banco de dados fechada.")

if __name__ == "__main__":
    xml_file = 'dados_ifsp.xml'
    print(f"Iniciando importação de dados do arquivo '{xml_file}'...")
    dados_carregados = carregar_dados(xml_file)
    if dados_carregados:
        importar_para_banco(dados_carregados)
    else:
        print("Nenhum dado válido foi carregado do XML.")
