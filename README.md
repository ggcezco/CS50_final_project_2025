# scrape do Gustavo

Pra ajudar na configuração

## Configurando um virtualenv

```bash
python -m venv .venv
```

Você vai ver que será criado um diretório .venv e o Git vai tentar subir isso pro repositório, o que não precisa.

Pra resolver isso, basta rodar um `ignr -p python > .gitignore` caso tenha o `ignr` instalado ou baixar um template de `.gitignore` do [GitHub para Python](https://github.com/github/gitignore/blob/main/Python.gitignore).

Caso opte por baixar o template, não esqueça de renomear o arquivo `Python.gitignore` para `.gitignore`.

O .venv é pra te ajudar a instalar pacotes de uma maneira isolada dos seus outros projetos, assim como controlar versões individualmente. Não vai demorar muito pra isso ser frustrante e causar problemas falsos, então já isola uma dor de cabeça no futuro.

### Executando coisas de dentro do virtualenv

```bash
source .venv/bin/activate
```

Agora isolado, podemos instalar as dependências do projeto com `pip`:

```bash
pip install requests bs4 
```

Com as dependências instaladas, vamos criar um arquivo `requirements.txt` pra "documentar" automaticamente essa ação e garantir que qualquer pessoa (incluindo você) que baixe esse código de novo possa ter as mesmas dependências nas mesmas versões.

```bash
pip freeze > requirements.txt
```

Sempre que você instalar ou atualizar qualquer pacote, lembre de executar o freeze novamente pra ter esse aquivo `requirements.txt` sempre atualizado.

Por fim, quando tiver executado o código, testado e modificado quantas vezes quiser, para sair do virtualenv execute:

```bash
deactivate
```

Precisando voltar, só chamar o comando `source .venv/bin/activate` novamente e as coisas estarão no ponto que você deixou do ponto de vista de instalação.

E para instalar/atualizar as dependências dentro de um virtualenv zerado depois de chamar o activate:

```bash
pip install -r requirements.txt  
```
