# gaia_logic.py (VERSÃO COM LINK DE AJUDA)

import requests
import json
import re

class GaiaLogic:
    def __init__(self, ollama_url="http://localhost:11434/api/generate", model_name="gaia-ifsp"):
        self.ollama_url = ollama_url
        self.model_name = model_name
        
        # <<< MUDANÇA AQUI >>>
        # Mensagem padrão com o link para ser reutilizada
        self.fallback_link_message = (
            "Para informações oficiais e completas, por favor, acesse o "
            "<a href='https://portal.cmp.ifsp.edu.br/' target='_blank' style='color: #007bff; text-decoration: none;'>portal do IFSP Campinas</a>."
        )

        self.db_schema = """
        CREATE TABLE dados_ifsp (
            id INT AUTO_INCREMENT PRIMARY KEY,
            disciplina VARCHAR(255),
            curso VARCHAR(255),
            semestre INT,
            professor VARCHAR(255),
            horario VARCHAR(255),
            turno VARCHAR(20)
        );
        """

        self.example_sql_instructions = """
        -- Pergunta: "quantas disciplinas o curso de ads tem?"
        -- SQL: SELECT COUNT(DISTINCT disciplina) as 'Número de Disciplinas de ADS' FROM dados_ifsp WHERE curso LIKE '%TADS%';

        -- Pergunta: "quantos alunos tem em ads?"
        -- SQL: FORA_DO_ESCOPO_ALUNOS

        -- Pergunta: "que aulas o 5° semestre de ads tem na quarta e na sexta feira?"
        -- SQL: SELECT disciplina, professor, horario FROM dados_ifsp WHERE semestre = 5 AND curso LIKE '%TADS%' AND (horario LIKE '%Qua%' OR horario LIKE '%Sex%');

        -- Pergunta: "ola"
        -- SQL: SAUDACAO
        """

    def prompt(self, user_message):
        full_prompt = f"""
        Você é a Gaia, uma assistente virtual especialista em traduzir perguntas para consultas SQL precisas para a tabela `dados_ifsp`.

        ## Estrutura da Tabela:
        {self.db_schema}

        ## Exemplos de Tradução PERFEITOS:
        {self.example_sql_instructions}

        ## REGRAS INQUEBRÁVEIS:
        1. **NÃO CONTE ALUNOS**: A tabela `dados_ifsp` NÃO contém informações sobre o número de alunos. Se o usuário perguntar "quantos alunos", sua única resposta DEVE SER a palavra-chave `FORA_DO_ESCOPO_ALUNOS`.
        2. Se o usuário perguntar para contar qualquer outra coisa (disciplinas, professores), use `COUNT()` e dê um nome claro à coluna com `AS 'Nome da Coluna'`.
        3. **NUNCA USE UMA COLUNA CHAMADA 'dia'**. Para filtrar por dias da semana, você **OBRIGATORIAMENTE** deve usar a coluna `horario` com `LIKE`. Exemplo: `horario LIKE '%Qua%'`.
        4. **REGRA DE PARÊNTESES**: Se a pergunta filtrar a coluna `horario` por múltiplos dias (ex: 'quarta E sexta'), a estrutura **DEVE** ser `... AND (horario LIKE '%valor1%' OR horario LIKE '%valor2%')`.
        5. Responda APENAS com a consulta SQL ou uma das palavras-chave.

        ## Pergunta do Usuário:
        "{user_message}"

        ## Resposta (SQL ou Palavra-chave):
        """

        try:
            response = requests.post(
                self.ollama_url,
                headers={'Content-Type': 'application/json'},
                data=json.dumps({
                    "model": self.model_name,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": { "temperature": 0.0, "num_ctx": 4096 }
                }),
                timeout=180
            )
            response.raise_for_status()
            result = response.json()
            ai_response = result.get("response", "").strip()

            # <<< MUDANÇA AQUI >>>
            # As mensagens de erro agora incluem o link de ajuda.
            if "FORA_DO_ESCOPO_ALUNOS" in ai_response:
                message = f"Desculpe, eu não tenho acesso a informações sobre o número de alunos. Minha especialidade são os horários e disciplinas. <br><br>{self.fallback_link_message}"
                return {"message": message, "sql": None}
            
            if "FORA_DO_ESCOPO" in ai_response: # Uma recusa genérica
                message = f"Essa pergunta está fora do meu escopo de conhecimento. <br><br>{self.fallback_link_message}"
                return {"message": message, "sql": None}

            if "SAUDACAO" in ai_response:
                return {"message": "Olá! Sou a Gaia, a IA do IFSP. Em que posso ajudar?", "sql": None}

            sql_query = self._validate_and_extract_sql(ai_response)
            if sql_query:
                return {"message": f"Entendi! Buscando informações sobre '{user_message}'...", "sql": sql_query}
            else:
                message = f"Não consegui formular uma resposta para essa pergunta. <br><br>{self.fallback_link_message}"
                return {"message": message, "sql": None}

        except requests.exceptions.RequestException as e:
            return {"message": f"Erro na comunicação com a IA. Verifique se o Ollama está rodando. <br><br>Detalhes: {e}", "sql": None}

    def _validate_and_extract_sql(self, text):
        match = re.search(r"SELECT\s+.*?;", text, re.IGNORECASE | re.DOTALL)
        if match:
            sql_candidate = match.group(0).strip()
            return sql_candidate
        return None