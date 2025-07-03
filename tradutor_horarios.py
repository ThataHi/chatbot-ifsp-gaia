# tradutor_horarios.py

import re

def traduzir_horario_completo(expressao_horario):
    if not expressao_horario or "not placed" in expressao_horario.lower() or "definido" in expressao_horario.lower():
        return ["A ser definido"]

    dias_semana = { 'A': 'Seg', 'B': 'Ter', 'C': 'Qua', 'D': 'Qui', 'E': 'Sex', 'F': 'Sáb' }
    horarios_turnos = {
        'Matutino 1': '07:00-07:50', 'Matutino 2': '07:50-08:40', 'Matutino 3': '08:50-09:40',
        'Matutino 4': '09:40-10:30', 'Matutino 5': '10:40-11:30', 'Matutino 6': '11:30-12:20',
        'Vespertino 1': '12:50-13:40', 'Vespertino 2': '13:40-14:30', 'Vespertino 3': '14:40-15:30',
        'Vespertino 4': '15:30-16:20', 'Vespertino 5': '16:30-17:20', 'Vespertino 6': '17:20-18:10',
        'Noturno 1': '18:20-19:10', 'Noturno 2': '19:10-20:00', 'Noturno 3': '20:00-20:50',
        'Noturno 4': '21:00-21:50', 'Noturno 5': '21:50-22:40'
    }

    horarios_finais, temp_bloco = [], ""
    blocos = expressao_horario.split()
    agrupador = []
    for bloco in blocos:
        temp_bloco += " " + bloco
        if ')' in bloco:
            agrupador.append(temp_bloco.strip())
            temp_bloco = ""

    padrao = re.compile(r"([A-Za-z]+)\s*(\d)(?:-([A-Za-z]+)\s*(\d))?\(([A-F])\)")
    
    for bloco_horario in agrupador:
        match = padrao.search(bloco_horario)
        if not match: continue
        
        turno_inicio, p_inicio, turno_fim, p_fim, dia_letra = match.groups()
        chave_inicio = f"{turno_inicio.capitalize()} {p_inicio}"
        dia_traduzido = dias_semana.get(dia_letra, f"({dia_letra})")

        if p_fim:
            chave_fim = f"{turno_fim.capitalize()} {p_fim}"
            h_inicio = horarios_turnos.get(chave_inicio, "??:??").split('-')[0]
            h_fim = horarios_turnos.get(chave_fim, "??:??").split('-')[1]
            horarios_finais.append(f"{dia_traduzido} {h_inicio}-{h_fim}")
        else:
            horario_completo = horarios_turnos.get(chave_inicio, "Não encontrado")
            horarios_finais.append(f"{dia_traduzido} {horario_completo}")

    return horarios_finais if horarios_finais else ["Formato inválido"]