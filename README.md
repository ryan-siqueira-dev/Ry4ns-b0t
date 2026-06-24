# Ry4ns Bot

Bot utilitario para Discord feito em Python com `discord.py`.

## Requisitos

- Python 3.12
- Uma aplicacao criada no Discord Developer Portal
- Um bot convidado para o servidor com os escopos `bot` e `applications.commands`

## Configuracao local

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e .
cp .env.example .env
```

Edite `.env`:

```env
DISCORD_TOKEN=token_do_bot
DISCORD_GUILD_ID=id_do_servidor_de_teste
```

O `DISCORD_GUILD_ID` faz os slash commands aparecerem rapidamente no servidor de teste. Se quiser registrar comandos globais depois, deixe esse campo vazio.

## Rodar

```bash
python -m ry4ns_bot
```

## Comandos

- `/ping`: mostra a latencia aproximada do bot.
- `/server`: mostra informacoes basicas do servidor.
- `/user`: mostra informacoes de um membro.
- `/avatar`: mostra o avatar de um membro.
- `/clear`: apaga de 1 a 100 mensagens no canal atual. Exige permissao de gerenciar mensagens.

## Testes

```bash
python -m unittest discover
python -m compileall ry4ns_bot tests
```
