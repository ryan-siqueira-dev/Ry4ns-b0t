# Ry4ns Bot

Bot utilitario para Discord feito em Python com `discord.py`.

## Requisitos

- Python 3.12, 3.13 ou 3.14
- Uma aplicacao criada no Discord Developer Portal
- Um bot convidado para o servidor com os escopos `bot` e `applications.commands`

## Configuracao local

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e .
```

Crie um arquivo `.env` na raiz do projeto:

```env
DISCORD_TOKEN=token_do_bot
DISCORD_GUILD_ID=id_do_servidor_de_teste
```

Se preferir, use `.env.example` como base:

```bash
cp .env.example .env
```

O `DISCORD_GUILD_ID` faz os slash commands aparecerem rapidamente no servidor de teste. Se quiser registrar comandos globais depois, deixe esse campo vazio.

## Rodar

```bash
python -m ry4ns_bot
```

## Comandos gerais

- `/ping`: mostra a latencia aproximada do bot.
- `/server`: mostra informacoes basicas do servidor.
- `/user`: mostra informacoes de um membro.
- `/avatar`: mostra o avatar de um membro.
- `/clear`: apaga de 1 a 100 mensagens no canal atual. Exige permissao de gerenciar mensagens.

## Comandos de moderacao

- `/timeout`: silencia temporariamente um membro. Exige permissao de moderar membros.
- `/untimeout`: remove o timeout de um membro. Exige permissao de moderar membros.
- `/kick`: expulsa um membro do servidor. Exige permissao de expulsar membros.
- `/ban`: bane um membro do servidor. Exige permissao de banir membros.
- `/slowmode`: define o modo lento do canal atual. Exige permissao de gerenciar canais.

Os comandos de moderacao tambem verificam hierarquia de cargos antes de agir. O bot precisa ter permissao e cargo acima do membro alvo.

## Comandos de entretenimento

- `/coinflip`: joga cara ou coroa.
- `/roll`: rola um dado com a quantidade de lados escolhida.
- `/choose`: escolhe uma opcao de uma lista separada por virgulas.
- `/8ball`: responde uma pergunta no estilo bola 8.

## Testes

Os testes verificam a configuracao, as regras de entretenimento e o registro dos comandos. Eles ajudam a perceber rapidamente se uma mudanca quebrou a inicializacao antes de rodar o bot no Discord.

```bash
python -m unittest discover
python -m compileall ry4ns_bot tests
```
