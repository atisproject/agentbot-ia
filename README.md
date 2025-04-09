# AgentBot-IA: Sistema de Coaching Nutricional com IA

## Visão Geral
AgentBot-IA é uma aplicação web baseada em Flask que integra inteligência artificial para fornecer coaching nutricional automatizado. O sistema utiliza a API OpenAI para processamento de linguagem natural e a API Twilio para comunicação via WhatsApp.

## Requisitos
```
apscheduler==3.10.1
email-validator==2.0.0
flask==2.3.3
flask-login==0.6.2
flask-sqlalchemy==3.0.5
gunicorn==23.0.0
openai==1.3.7
psycopg2-binary==2.9.7
sqlalchemy==2.0.20
twilio==8.5.0
werkzeug==2.3.7
```

## Guia de Implantação no Render

Este guia detalhado explica como implantar a aplicação AgentBot-IA na plataforma Render com um domínio personalizado.

### Passo 1: Preparar o Projeto para Implantação

#### 1.1 Arquivos Necessários

Certifique-se de que seu projeto contenha estes arquivos importantes:
- `requirements.txt` - Lista todas as dependências do projeto
- `Procfile` (opcional) - Especifica como iniciar a aplicação
- `.gitignore` - Exclui arquivos desnecessários do repositório

Conteúdo do Procfile (opcional mas recomendado):
```
web: gunicorn --bind 0.0.0.0:$PORT --workers=2 --reuse-port main:app
```

### Passo 2: Configurar Repositório Git

Se seu projeto ainda não estiver em um repositório Git:

1. Inicialize um repositório Git no diretório do projeto
2. Adicione e faça o commit de todos os arquivos
3. Crie um repositório no GitHub/GitLab
4. Conecte e envie seu código para o repositório remoto

### Passo 3: Configurar Banco de Dados PostgreSQL no Render

1. Acesse o dashboard do Render: https://dashboard.render.com
2. Clique em "Novo" → "PostgreSQL"
3. Preencha os detalhes do banco de dados:
   - **Nome**: agentbot-ia-db
   - **Banco de Dados**: agentbot_ia
   - **Usuário**: agentbot_user
   - **Região**: Escolha a mais próxima dos seus usuários
   - **Versão do PostgreSQL**: 15 (mais recente estável)
   - **Tipo de Instância**: "Starter" ($7/mês) para produção ou "Free" para testes
4. Clique em "Criar Banco de Dados"
5. **IMPORTANTE**: Anote as informações de conexão fornecidas:
   - URL de Banco de Dados Interno (para conectar de serviços Render)
   - URL de Banco de Dados Externo (para conectar de fora do Render)
   - Comando PSQL (para acesso via linha de comando)

### Passo 4: Criar Serviço Web no Render

1. No dashboard do Render, clique em "Novo" → "Serviço Web"
2. Conecte seu repositório:
   - Se estiver usando GitHub/GitLab: Clique em "Conectar conta"
   - Siga as instruções para autorizar o Render
   - Selecione seu repositório da lista
   - Caso esteja usando outro provedor Git: Selecione "Repositório Git público" e cole a URL

3. Configure as definições do serviço web:
   - **Nome**: AgentBot-IA
   - **Região**: Escolha a mesma região do seu banco de dados
   - **Branch**: main (ou sua branch padrão)
   - **Runtime**: Python 3
   - **Comando de Build**: `pip install -r requirements.txt`
   - **Comando de Início**: `gunicorn --bind 0.0.0.0:$PORT main:app`
   - **Tipo de Instância**: "Starter" ($7/mês) para produção ou "Free" para testes
   - **Auto-Deploy**: Sim (para implantação automática quando você enviar alterações de código)

4. Defina as variáveis de ambiente:
   - **DATABASE_URL**: URL de Banco de Dados Interno do Passo 3
   - **OPENAI_API_KEY**: Sua chave de API da OpenAI
   - **TWILIO_ACCOUNT_SID**: Seu SID de conta da Twilio
   - **TWILIO_AUTH_TOKEN**: Seu token de autenticação da Twilio
   - **TWILIO_PHONE_NUMBER**: Seu número de telefone Twilio com WhatsApp (formato: +1234567890)
   - **SESSION_SECRET**: String aleatória para segurança da sessão

5. Clique em "Criar Serviço Web"

### Passo 3: Configurar Banco de Dados PostgreSQL no Render

1. Acesse o dashboard do Render: https://dashboard.render.com
2. Clique em "Novo" → "PostgreSQL"
3. Preencha os detalhes do banco de dados:
   - **Nome**: agentbot-ia-db
   - **Banco de Dados**: agentbot_ia
   - **Usuário**: agentbot_user
   - **Região**: Escolha a mais próxima dos seus usuários
   - **Versão do PostgreSQL**: 15 (mais recente estável)
   - **Tipo de Instância**: "Starter" ($7/mês) para produção ou "Free" para testes
4. Clique em "Criar Banco de Dados"
5. **IMPORTANTE**: Anote as informações de conexão fornecidas:
   - URL de Banco de Dados Interno (para conectar de serviços Render)
   - URL de Banco de Dados Externo (para conectar de fora do Render)
   - Comando PSQL (para acesso via linha de comando)

### Passo 4: Criar Serviço Web no Render

1. No dashboard do Render, clique em "Novo" → "Serviço Web"
2. Conecte seu repositório:
   - Se estiver usando GitHub/GitLab: Clique em "Conectar conta"
   - Siga as instruções para autorizar o Render
   - Selecione seu repositório da lista
   - Caso esteja usando outro provedor Git: Selecione "Repositório Git público" e cole a URL

3. Configure as definições do serviço web:
   - **Nome**: AgentBot-IA
   - **Região**: Escolha a mesma região do seu banco de dados
   - **Branch**: main (ou sua branch padrão)
   - **Runtime**: Python 3
   - **Comando de Build**: (Comando para instalar requisitos)
   - **Comando de Início**: `gunicorn --bind 0.0.0.0:$PORT main:app`
   - **Tipo de Instância**: "Starter" ($7/mês) para produção ou "Free" para testes
   - **Auto-Deploy**: Sim (para implantação automática quando você enviar alterações de código)

4. Defina as variáveis de ambiente:
   - **DATABASE_URL**: URL de Banco de Dados Interno do Passo 3
   - **OPENAI_API_KEY**: Sua chave de API da OpenAI
   - **TWILIO_ACCOUNT_SID**: Seu SID de conta da Twilio
   - **TWILIO_AUTH_TOKEN**: Seu token de autenticação da Twilio
   - **TWILIO_PHONE_NUMBER**: Seu número de telefone Twilio com WhatsApp (formato: +1234567890)
   - **SESSION_SECRET**: String aleatória para segurança da sessão

5. Clique em "Criar Serviço Web"

### Passo 5: Inicializar Tabelas do Banco de Dados

Após a implantação do serviço, você precisa inicializar as tabelas do banco de dados:

1. Acesse a aba "Shell" do seu serviço web no dashboard do Render
2. Aguarde a conexão do shell
3. Execute o Python e inicialize o banco de dados:

```bash
python
```

Em seguida, no prompt do Python:

```python
from app import app, init_db
with app.app_context():
    init_db()
exit()
```

Isso criará todas as tabelas necessárias no seu banco de dados PostgreSQL.

### Passo 6: Configurar Seu Domínio Personalizado

1. No dashboard do seu serviço web, clique na aba "Configurações"
2. Role até "Domínio Personalizado"
3. Clique em "Adicionar Domínio Personalizado"
4. Digite seu domínio: `agentbot-ia.shop`
5. Clique em "Salvar"
6. O Render mostrará instruções de configuração DNS

#### Configurar DNS com seu Provedor de Domínio

1. Faça login no seu registrador de domínio (onde você comprou `agentbot-ia.shop`)
2. Navegue até as configurações DNS ou gerenciamento de DNS
3. Adicione os seguintes registros conforme instruído pelo Render:

Para domínio raiz (agentbot-ia.shop):
- **Tipo**: A
- **Nome**: @ (ou deixe em branco)
- **Valor**: Endereços IP do Render (fornecidos nas instruções)
- **TTL**: 3600 (ou padrão/automático)

Para subdomínio www:
- **Tipo**: CNAME
- **Nome**: www
- **Valor**: Sua URL do Render (ex: `agentbot-ia.onrender.com`)
- **TTL**: 3600 (ou padrão/automático)

4. Aguarde a propagação do DNS (pode levar 24-48 horas, mas geralmente é mais rápido)
5. O Render verificará automaticamente seu domínio
6. Uma vez verificado, você verá um status "Verificado" na seção Domínio Personalizado
7. O Render provisionará automaticamente um certificado SSL via Let's Encrypt

### Passo 7: Configurar Integração com WhatsApp

1. Faça login no console da Twilio: https://console.twilio.com
2. Navegue até "Messaging" → "Settings" → "WhatsApp Sandbox"
3. Localize o campo "When a message comes in"
4. Atualize a URL do webhook para seu domínio personalizado:
   ```
   https://agentbot-ia.shop/webhook/whatsapp
   ```
5. Certifique-se de que o método HTTP esteja definido como "HTTP Post"
6. Clique em "Salvar"

#### Testar Integração com WhatsApp

1. Use seu telefone para enviar uma mensagem para o número WhatsApp da Twilio
2. Verifique se você recebe uma resposta automatizada do seu bot
3. Verifique os logs no seu dashboard do Render para garantir que o webhook esteja sendo acionado

### Passo 8: Tarefas Adicionais Pós-Implantação

#### Configurar Backups Automáticos de Banco de Dados

1. No dashboard do seu serviço PostgreSQL no Render, vá para "Backups"
2. Ative os backups automáticos
3. Configure o cronograma de backup desejado (diário é recomendado)

#### Monitorar Desempenho da Aplicação

1. No dashboard do seu serviço web, clique na aba "Métricas"
2. Revise métricas de CPU, memória e requisições
3. Configure alertas de métricas, se necessário (na aba "Alertas")

#### Configurar Registro de Logs

1. No dashboard do seu serviço web, clique na aba "Logs"
2. Revise os logs da aplicação para quaisquer erros ou problemas
3. Considere configurar drenos de log para serviços externos para armazenamento de log de longo prazo

### Passo 9: Manutenção Contínua e Atualizações

#### Atualizar Sua Aplicação

Para atualizar sua aplicação:
1. Faça alterações em seu código localmente
2. Faça o commit e envie para seu repositório Git
3. O Render implantará automaticamente as alterações se o auto-deploy estiver ativado
4. Monitore a implantação na aba "Eventos" do dashboard do seu serviço

#### Migrações de Banco de Dados

Para alterações no esquema do banco de dados:
1. Crie um script de migração (ou use as ferramentas de migração do seu ORM)
2. Teste as migrações localmente
3. Implante alterações de código com migrações
4. Use o shell do Render para executar comandos de migração, se necessário

## Estrutura do Projeto

```
├── app.py                  # Configuração do aplicativo Flask e banco de dados
├── main.py                 # Ponto de entrada para o servidor web
├── models.py               # Modelos de banco de dados SQLAlchemy
├── routes.py               # Rotas principais da aplicação web
├── ai_agent.py             # Integração com OpenAI para assistente de IA
├── whatsapp_integration.py # Integração com a API Twilio para WhatsApp
├── whatsapp_routes.py      # Rotas para webhooks do WhatsApp
├── whatsapp_flows.py       # Fluxos de mensagens para comunicação WhatsApp
├── notification.py         # Sistema de notificação por SMS/WhatsApp
├── static/                 # Arquivos estáticos (CSS, JS, imagens)
│   ├── css/                # Folhas de estilo
│   ├── js/                 # Scripts JavaScript
│   └── img/                # Imagens e ícones
└── templates/              # Templates HTML (Jinja2)
    ├── layout.html         # Template base
    ├── index.html          # Página inicial
    ├── dashboard.html      # Painel de controle
    ├── leads.html          # Gerenciamento de leads
    └── configuracoes.html  # Configurações do sistema
```

## Variáveis de Ambiente Necessárias

```
DATABASE_URL=postgres://usuario:senha@host:porta/nome_do_banco
OPENAI_API_KEY=sua-chave-api-openai
TWILIO_ACCOUNT_SID=seu-account-sid-twilio
TWILIO_AUTH_TOKEN=seu-auth-token-twilio
TWILIO_PHONE_NUMBER=+1234567890
SESSION_SECRET=string-aleatoria-para-seguranca
```

## Usuários e Funções

O sistema suporta os seguintes tipos de usuários:
- **Administrador**: Acesso completo ao sistema e configurações
- **Usuário**: Acesso ao painel e gerenciamento de leads

## Recursos Principais

1. **Assistente de IA**: Processamento automático de mensagens de clientes
2. **Integração WhatsApp**: Comunicação direta com clientes via WhatsApp
3. **Dashboard**: Visualização de estatísticas e dados importantes
4. **Gerenciamento de Leads**: Acompanhamento de potenciais clientes
5. **Base de Conhecimento**: Armazenamento de informações para treinamento da IA
6. **Agendamento**: Sistema de lembretes e acompanhamento automático

## Suporte e Manutenção

Para questões relacionadas à implantação ou funcionamento da aplicação:
- **Problemas de Render**: Consulte a [documentação oficial do Render](https://render.com/docs)
- **Integração Twilio**: Verifique o [guia de integração WhatsApp da Twilio](https://www.twilio.com/docs/whatsapp)
- **API OpenAI**: Consulte a [documentação da OpenAI](https://platform.openai.com/docs/introduction)

## Licença

Este projeto é proprietário e confidencial. Todos os direitos reservados.
