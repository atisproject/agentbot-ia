"""
Fluxo de mensagens do WhatsApp para InFoccus
"""

MENSAGENS_BOASVINDAS = [
    """🎯💪🏼  *Agora você faz parte do time da inFocus!*

_[nome], é um prazer te dar as boas-vindas!_

A partir de agora, você não estará sozinha na sua jornada, nem vai mais perder tempo e dinheiro com estratégias que não funcionam.

Nos próximos meses, você será acompanhado por dois profissionais experientes, focados em criar a *melhor estratégia* para te aproximar dos seus objetivos… 

🔥 … Com dietas fáceis de seguir e treinos personalizados, tudo baseado em ciência — _sem achismos!_

Acredite, essa foi uma das melhores decisões que você poderia ter tomado por você.

⬇️  *Agora, vamos às informações importantes…*"""
]

ETAPAS_FLUXO = {
    'PRIMEIRO_CONTATO': 'Primeiro Contato [Boas-vindas]',
    'FOLLOW_UP_1': 'Follow Up 1 [após 24h]',
    'FOLLOW_UP_2': 'Follow Up 2 [12h após follow up 1]',
    'ENVIO_ACESSO': 'Envio de acesso Treino e Dieta',
    'CONFIRMACAO_ACESSO': 'Confirmação de acesso'
}

def get_mensagem_boas_vindas(nome):
    """Retorna a mensagem de boas vindas formatada com o nome do cliente"""
    return MENSAGENS_BOASVINDAS[0].replace('[nome]', nome)
