# Guidelines de Arquitetura — MVC Alvo

Referência da **Fase 3**. Define a estrutura de destino e a responsabilidade de
cada camada, de forma independente de linguagem.

## Estrutura alvo

```
src/
├── config/          # configuração e segredos (só leitura de env)
├── models/          # acesso a dados + regra de domínio da entidade
├── services/        # regra de negócio que cruza entidades ou fala com o mundo externo
├── controllers/     # orquestração de um caso de uso por handler
├── views/ (routes/) # mapeamento rota → controller
├── middlewares/     # erro, validação, autenticação, CORS
└── app.<ext>        # composition root: monta dependências e sobe o servidor
```

Adapte a nomenclatura à convenção da linguagem — o que não muda é a **direção
das dependências**.

## Regra de dependência

```
routes → controllers → services → models → banco
              ↘ middlewares ↙
        todos → config (só leitura)
```

- A seta só aponta para a direita. **Model nunca importa controller.**
- Nenhuma camada importa `request`/`response` do framework além de controller e middleware.
- Config não importa ninguém.
- Import circular entre camadas é sinal de que a responsabilidade está no lugar errado.

## Responsabilidades por camada

### config/
**Faz**: ler variáveis de ambiente, aplicar defaults seguros, expor um objeto de
configuração tipado/validado, falhar no boot se faltar variável obrigatória.
**Não faz**: importar model, controller ou framework web; conter valor de segredo.

Regra: **zero literais de segredo**. Defaults só para valores não sensíveis
(porta, nível de log). Entregue junto um `.env.example` com todas as chaves.

### models/
**Faz**: CRUD da entidade com queries **parametrizadas**, serialização
(`to_dict`/`toJSON`), invariantes da própria entidade (status válido, item
atrasado), agregações via banco.
**Não faz**: ler `request`, devolver `response`/status HTTP, enviar e-mail,
conhecer outro model fora do seu agregado.

Um arquivo por entidade. É o único lugar do projeto onde SQL/ORM aparece.

### services/
**Faz**: caso de uso que cruza entidades (checkout: curso + matrícula +
pagamento + auditoria), integração externa (e-mail, gateway), transações que
envolvem vários models, relatórios que combinam fontes.
**Não faz**: conhecer HTTP; instanciar as próprias dependências (recebe por construtor).

Camada opcional: projeto CRUD simples pode ir de controller direto ao model. Crie
o service quando a regra cruzar entidades ou tocar serviço externo.

### controllers/
**Faz**: extrair dados do request, validar/delegar validação, chamar model ou
service, traduzir o resultado em status code + corpo, propagar erro ao middleware.
**Não faz**: SQL, cálculo de negócio, envio de notificação, `try/catch` repetido
por handler (isso é do error handler).

Alvo: **até ~25 linhas por handler**. Um handler por caso de uso.

### views/ (routes/)
**Faz**: declarar método HTTP + path → função do controller; aplicar middlewares
da rota; agrupar por recurso.
**Não faz**: qualquer lógica. Uma linha por rota.

Em API REST, a "View" do MVC é a camada de rota + serialização — sem template
engine. Manter o nome `views/` ou `routes/` é escolha do projeto; documente qual.

### middlewares/
**Faz**: error handler centralizado (uma resposta de erro padronizada e um log
estruturado por falha), autenticação/autorização, validação de schema, CORS,
`404` para rota desconhecida.
**Não faz**: regra de negócio.

O error handler é obrigatório: com ele os controllers deixam de repetir
`try/catch` e as respostas de erro ficam consistentes.

### app (composition root)
**Faz**: carregar config, instanciar dependências na ordem certa e injetá-las,
registrar middlewares e rotas, subir o servidor.
**Não faz**: declarar rota individual, conter regra, definir credencial.

É o **único** ponto do projeto onde acontece `new`/instanciação de infraestrutura.

## Preservação do contrato

A refatoração é **comportamento-preservante para o cliente da API**. Devem
permanecer idênticos: paths, métodos HTTP, nomes dos campos de request e
response, status codes, formato do corpo de erro.

Podem mudar: organização de arquivos, nomes internos, forma de acesso ao banco,
origem da configuração.

Exceção justificada: endpoint que executa SQL arbitrário ou reseta o banco deve
ser **removido** — a remoção é reportada explicitamente no relatório final.

## Checklist de aceite da Fase 3

- [ ] Diretórios da estrutura alvo criados
- [ ] Nenhum segredo no código; tudo em env + `.env.example` presente
- [ ] `debug` desligado por padrão, ligado só por variável de ambiente
- [ ] Todo acesso a dados dentro de `models/`, 100% parametrizado
- [ ] Nenhum handler de rota com SQL ou cálculo de negócio
- [ ] Rotas só mapeiam, sem lógica
- [ ] Error handler centralizado registrado, sem `try/catch` repetido nos controllers
- [ ] Entrypoint monta as dependências e nada mais
- [ ] Arquivos legados substituídos foram removidos
- [ ] Aplicação sobe sem erro
- [ ] Todas as rotas do baseline respondem com o mesmo status e formato
