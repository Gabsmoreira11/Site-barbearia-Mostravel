# Barbearia Prime — V3 Agenda

MVP educacional de site + sistema de agendamento com Flask, SQLAlchemy, SQLite e login de clientes.

## O que existe nesta V3
- Login/cadastro obrigatório para clientes.
- Calendário mensal visual do cliente.
- Rotina semanal por profissional.
- Vários períodos no mesmo dia (ex.: 09–12 e 13–19), permitindo intervalo de almoço.
- Serviços com duração diferente.
- Intervalo de geração de horários configurável.
- Antecedência mínima para agendamento.
- Limite de dias futuros.
- Folga por profissional.
- Bloqueio de horário específico.
- Feriados gerais.
- Agendamento manual pelo admin.
- Encaixe: permite agendamento fora da grade, desde que não haja conflito.
- Status: pendente, confirmado, concluído e cancelado.
- Cadastro e histórico de clientes.
- Links de WhatsApp para cliente/barbearia.
- Dashboard e agenda administrativa.

## Rodar
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

Abra http://127.0.0.1:5000

Admin de demonstração:
- e-mail: admin@prime.local
- senha: admin123

### Banco existente
A V3 possui uma pequena migração automática para novas colunas SQLite. Para uma instalação de teste limpa, apagar `instance/database.db` antes de executar é recomendado.

## WhatsApp
A integração usa links `wa.me` com mensagens pré-preenchidas. Isso não envia mensagens automaticamente. Para automação real sem clique, seria necessário integrar a WhatsApp Business Platform/API e configurar credenciais.

## Produção
Antes de vender como SaaS: trocar SECRET_KEY por variável de ambiente, PostgreSQL, migrations Alembic/Flask-Migrate, CSRF, autorização por recurso, logs, backups, HTTPS, rate limiting, testes, política de privacidade, termos, recuperação de senha e tratamento de concorrência para impedir dupla reserva.

### Acessos de demonstração
- Admin: `admin@prime.local` / `admin123`
- Barbeiro João: `joao@prime.local` / `joao123`
- Barbeiro Carlos: `carlos@prime.local` / `carlos123`
