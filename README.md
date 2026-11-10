# Site do Centro de Ciências Forenses — UFPR

Site estático do CCF/UFPR. O conteúdo fica em arquivos JSON, um script Python gera o HTML e a
publicação é automática a cada `git push` na branch `main`.

Não há dependências: basta Python 3.8 ou mais recente.

## Rodar localmente

```bash
python3 build.py --serve     # gera dist/ e abre em http://localhost:8000
```

## Atualizar o conteúdo

Edite o arquivo correspondente em `content/` (pode ser pela própria interface do GitHub) e faça o commit.

| Arquivo | O que contém |
|---|---|
| `content/site.json` | Texto da página inicial, contato, pilares, missão, objetivos, linha do tempo, parceiros, documentos e notícias |
| `content/areas.json` | Áreas de atuação e laboratórios relacionados a cada uma |
| `content/laboratorios.json` | Laboratórios (sigla, nome, unidade, descrição, link) |
| `content/projetos.json` | Projetos e casos; `"destaque": true` leva o projeto à página inicial |
| `content/equipe.json` | Coordenação e Comitê Gestor |
| `content/numeros.json` | Indicadores exibidos na página inicial |

O build falha — e nada é publicado — se um JSON estiver inválido, se uma área citar um laboratório
inexistente ou se houver link interno quebrado.

Imagens, CSS e JavaScript ficam em `static/`. Os modelos das páginas estão em `build.py`.

## Publicação

### Opção A — GitHub Pages (padrão)

1. Crie o repositório no GitHub e envie este conteúdo para a branch `main`.
2. Em **Settings → Pages**, selecione **Source: GitHub Actions**.
3. A cada push, o workflow `.github/workflows/deploy.yml` gera e publica o site.

Para usar um domínio da UFPR (por exemplo, `ccf.ufpr.br`), informe-o em **Settings → Pages → Custom domain**
e peça à equipe de redes um registro DNS `CNAME` apontando para `<organização>.github.io`.

### Opção B — Jenkins + servidor próprio

O `Jenkinsfile` gera o site a partir do repositório no GitHub e o envia por `rsync` a um servidor web.
Crie um job *Multibranch Pipeline*, cadastre a credencial SSH `ccf-deploy-key`, ajuste `DEPLOY_USER`,
`DEPLOY_HOST` e `DEPLOY_PATH` no arquivo e configure o webhook do GitHub para o Jenkins.

Use apenas uma das opções. Se optar pelo Jenkins, apague `.github/workflows/deploy.yml`.

## Estrutura

```
build.py                    gerador (biblioteca padrão do Python)
content/                    conteúdo em JSON
static/css, js, img         arquivos copiados como estão
.github/workflows/          publicação no GitHub Pages
Jenkinsfile                 publicação via Jenkins
dist/                       saída gerada (não versionada)
```
