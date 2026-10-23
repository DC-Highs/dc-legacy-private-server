# Roadmap de comandos ainda não implementados

## Status do primeiro lote (2026-10-22)

Implementei **só `mistery_egg_hatch`** deste lote. Os outros quatro do "alta confiança"
(`get_rewarded_dragon`, `kompu_try`, `kompu_hurry_up`, `defensive_strategy_set`) ficaram de fora
de propósito: ao investigar a config em busca da mecânica de cada um, não achei uma fonte de
dados suficientemente sólida para implementá-los sem adivinhar preços, recompensas ou o estado
que os habilitaria — e um palpite errado aqui é exatamente a classe de bug que vira duplicação de
recursos (o mesmo risco discutido na análise do script malicioso).

- **`mistery_egg_hatch`** — implementado. Os itens 154-157 (`Small/Medium/Large/Super Mistery
  Egg`, `group_type: MISTERY_EGG`) já existem na config, e a tabela `mistery_egg` já tem as
  recompensas e os pesos por tier. O comando só precisava ler essa tabela e sortear no servidor,
  igual ao padrão já usado em `deus_cards_claim` e `kompu_boxes_claim_prize`. Ver
  `src/commands/mistery_egg_hatch.py` e `tests/test_mistery_egg.py`.
- **`defensive_strategy_set`** — ao reler `set_attack_team.py`, percebi que ele já guarda times
  por `team_type` livre (`privateState.teams`, até 8 tipos) — ou seja, um time de defesa já
  poderia ser só mais um `team_type` dentro do comando que já existe, sem precisar de um comando
  novo. É possível que a string que minerei seja um nome de campo de configuração de combate da
  IA do PvP, não um comando de cliente. Fica pendente até confirmar com os logs.
- **`get_rewarded_dragon`** — confirmei que é real (apareceu no script malicioso analisado nesta
  sessão), mas não achei no código nem na config quem produziria o "prêmio pendente" que esse
  comando reivindicaria. Implementar às pressas significaria aceitar o id do dragão que o próprio
  cliente manda como argumento — e dar o dragão de graça. Fica pendente até achar (ou logar) quem
  gera esse estado.
- **`kompu_try`, `kompu_hurry_up`** — não achei preço nem mecânica confirmados na config para
  essas variantes (o mais perto que achei foi `KOMPU_WIZZARD_COSTS` e `COST_HURRY_UP`, mas não dá
  para saber se são desses comandos ou de outra coisa sem ver o protocolo real em uso).

Nenhuma mudança no frontend (Vite) foi necessária: `mistery_egg_hatch` é só mais um comando de
`packet.php`, que já passa pela sessão, pelo CSRF e pelo rate limit existentes — a mesma
infraestrutura que protege todos os outros comandos.

## Status do segundo lote (2026-10-23)

Investigando os candidatos de confiança média, descobri que `message`, `gifts` e
`resourceAlliesMarket` já são campos reservados em `privateState`/`map` desde o template de save
(`web/srv/get_player_info.json`), e `collectGame` também — ou seja, são sistemas reais, só que
maiores do que "mais um comando", porque dois deles (`place_gift`, `create_message`) escrevem no
save de **outro** jogador, o mesmo tipo de operação sensível que hoje só existe em
`pending_assists`. Perguntei qual encarar primeiro; a escolha foi **Allies Market**
(`set_resource_allies`).

- **`set_resource_allies`** — implementado, com escopo deliberadamente reduzido. Confirmei: item
  79 (`ALLIES_MARKET` na config, `group_type: SOCIAL BUILDING`, sprite
  `0079_allies_market.swf`) tem 6 cargos de trabalhador (`social_items` id 79), e o nome do
  comando usa o verbo `set_`, não `collect_`, então implementei só a troca do time de
  trabalhadores — os amigos atribuídos a cada cargo — igual ao `set_attack_team`, sem pagar ouro
  ou comida. A config tem `RESOURCES_MARKET_PER_ALLY` (`{g: 500, f: 50}`), que sugere uma fórmula
  de produção por aliado, mas não achei o comando que a cobraria nem a cadência (por tempo? por
  clique?), então nenhum recurso é concedido até isso ser confirmado. Ver
  `src/commands/set_resource_allies.py` e `tests/test_set_resource_allies.py`.
  - **Ressalva honesta**: o campo `name` do item 79 nesta captura da config é "Dragon Market",
    não "Allies Market". Confiei no nome do arquivo do sprite e no global `ALLIES_MARKET=79`
    por serem mais específicos, mas é uma discrepância real que vale conferir nos logs.
  - Cada amigo atribuído é validado contra `friends.are_friends` (Postgres), igual ao
    `assist_neighbor` já existente — não dá para colocar um estranho para "trabalhar".
- **`place_gift`, `create_message`** — adiados por decisão do usuário. Ambos precisam de um
  desenho deliberado antes de qualquer código, porque envolvem escrever no save de outro
  jogador (limites de frequência, só-entre-amigos, e para `create_message` também sanitização de
  texto livre).
- **`collect_game_*`** — confirmado como sistema completo (`privateState.collectGame` + 5 tabelas
  de config), mas segue fora de escopo por ser do tamanho de uma feature nova.

> Arquivo temporário de trabalho, gerado a partir de mineração de strings dos clientes SWF em
> `flash/versions/`. **Não é uma confirmação**: extraí apenas as strings do SWF, sem decompilar o
> bytecode AS3. Os nomes abaixo são candidatos — alguns podem ser nomes de configuração, de assets
> ou de estados internos que coincidem com o padrão de nomenclatura dos comandos reais, não `cmd`
> de `packet.php` de fato.

## Como cheguei nisso

Comparei os 59 comandos já implementados (`src/enums.py` `Command`) contra os nomes extraídos do
`Base_sec_1.0.1.swf` que seguem o padrão de verbo de ação (`buy_`, `collect_`, `set_`, etc.). Achei
~98 candidatos novos.

## Lista de alta confiança (prioridade para implementar)

Esses batem com nomes de sistemas que o jogo realmente tem e para os quais já existe estado
parcial no save ou na config.

| Área | Comandos candidatos | Por quê é prioridade |
|---|---|---|
| Deus / recompensa de dragão | `get_rewarded_dragon` | Confirmado em uso real: apareceu no script malicioso analisado nesta sessão (`{"cmd":"get_rewarded_dragon","args":[1040]}`), então é real e já é explorado hoje. É irmão de `deus_cards_claim`/`deus_cards_generate`, que já existem. |
| Ovo místico / dragonário | `mistery_egg_hatch`, `dragonarium_hatch` | `mistery_egg` já é uma tabela da config (`config_for_player`), então falta só o comando que a consome. |
| Kompu boxes | `kompu_try`, `kompu_hurry_up` | Extensão natural de `kompu_boxes_new_list/open_box/claim_prize`, já implementados. |
| Loja / ofertas | `buy_offer`, `buy_special_offer`, `buy_all_special_offer`, `buy_level_up_offer` | `buy`, `buy_egg`, `buy_treasure_new/popup` já existem; essas são variantes de oferta que a config já carrega (`offer_packs`, `special_offers`, `payment_offers`). |
| PvP / combate | `speed_attack`, `defensive_strategy_set` | Complementam `attack_player`/`end_attack_f`, já implementados; `set_attack_team` já existe, então `defensive_strategy_set` é o par defensivo. |

## Lista de confiança média (prováveis, mas precisam validação)

- **Minigame de coleta** (`collect_game_begin_attack`, `collect_game_end_attack`,
  `collect_game_buy_all`, `collect_game_speed_up`, `collect_game_add_items_container`,
  `collect_game_update_timestamp`) — a config já tem `collect_game_quests`, `collect_game_items`,
  `collect_game_probabilities`. É um subsistema inteiro ainda não coberto, do tamanho de um recurso
  novo (tipo "caça ao tesouro").
- **Social**: `create_message`, `place_gift`, `set_resource_allies` — ligados ao sistema de
  vizinhos/allies, que já existe parcialmente (`assist_neighbor`, `friends.py`).
- `finish_si`, `buy_si_help` — "si" provavelmente é "speed-up item" ou similar; aparecem perto de
  `daily_item_cooldown_time`.

## Lista de baixa confiança / provável ruído

`island_1_c` até `island_6_c`, `habitat_pure`, `event_type`, `in_store`, `sell_price`,
`set_quality`, `upgrade_from`, `goal_breed`, `goal_collect`, `goal_expand_island` etc. — isso
cheira mais a nomes de assets, campos de config ou tipos de meta (valores, não comandos) do que a
comandos de `packet.php`.

## O que não é roadmap de verdade

`admin_*` (`admin_reset`, `admin_add_resources`, `admin_create_dragon`, `admin_fast_forward`,
`admin_set_dragon_level`, etc.) são comandos de cheat/debug que ficaram no cliente de produção.
Não implementá-los é a escolha certa; o dispatcher já os recusa como "não implementado" e isso é
bom, porque um deles (`admin_add_resources`) seria uma dádiva para duplicação de recursos se algum
dia fosse ligado.

## Método mais confiável do que mineração de string

O jeito confiável de montar o roadmap de verdade é observar os logs em produção: o dispatcher já
registra `"Command %s is not implemented, answering with a generic ok"` para cada comando
desconhecido (`src/commands/dispatcher.py:81`). Rodando:

```bash
docker compose logs -f app | grep "is not implemented"
```

enquanto o jogo roda em cada versão (principalmente 0.7.x a 1.0.1, que carregam com a config
atual), dá para conseguir uma lista real e ordenada por frequência de uso — exatamente os comandos
que o cliente tenta mandar na prática, sem ruído de assets ou config.

## Proposta de roadmap, em ordem

1. Rodar as versões 0.7.6 a 1.0.1 e coletar os `"is not implemented"` reais por uma sessão de jogo
   normal (build, colheita, venda, ataque, compra na loja).
2. Implementar primeiro `get_rewarded_dragon` (já confirmado em uso) e os pares óbvios de comandos
   existentes (`mistery_egg_hatch`, `kompu_try`/`kompu_hurry_up`, `defensive_strategy_set`).
3. Avaliar o subsistema `collect_game_*` como um recurso à parte, do tamanho de uma feature nova.
4. Deixar os candidatos de baixa confiança para depois, confirmando cada um só quando aparecer nos
   logs.
