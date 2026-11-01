# barra-autoclicker

Autoclicker pra minigame de barra que sobe e vai trocando de cor. Você marca uma linha perto do topo da barra e, quando a barra passa por ela e a linha deixa de ser branca, o app dá um clique.

Ele só olha uns pixels da tela e simula o clique. Não lê memória do jogo nem injeta nada.

## Como funciona

Você marca um ponto no meio da barra, perto do topo. O app captura uma faixa fina de pixels ali com [mss](https://github.com/BoboTiG/python-mss) e classifica cada pixel:

- branco (inclui o cinza claro das marcações): a barra ainda não chegou
- preto ou bem escuro (divisórias e contorno): ignora
- qualquer outra cor: a barra passou

Se a porcentagem de pixels coloridos passa do limite (a sensibilidade), ele clica uma vez. Dá pra configurar pra ele desligar sozinho depois do clique, aí você aperta F6 pra armar a próxima rodada.

Não guardo cor de referência nenhuma. Só pergunto "é branco ou não?". No começo eu procurava laranja e quebrou na hora que a barra mudou de cor.

## Instalando

Precisa de Windows 10 ou 11, Python 3.10+ e rodar como administrador. Sem isso o jogo costuma ignorar o clique e o atalho de teclado.

```
git clone https://github.com/Goiabatriste06/barra-autoclicker.git
cd barra-autoclicker
python -m pip install -r requirements.txt
python autoclick_app.py
```

Ou abre o `iniciar.bat` com botão direito > Executar como administrador. Ele instala as dependências e abre o app. Se o `python` não for reconhecido, usa `py`. Depende de como o Python foi instalado.

## Usando

1. Abre o jogo e deixa a barra visível.
2. No app, clica em "Capturar posição" (ou aperta F7) e leva o mouse pro meio da barra, perto do topo. Você tem 3 segundos. Uma linha vermelha aparece ali.
3. Ajusta a altura com F8 (sobe) e F9 (desce). Quanto mais alta a linha, mais tarde ele clica.
4. F6 liga. A linha fica verde. Quando a barra cruzar, ele clica.

Atalhos: F6 liga/desliga, F7 captura a posição do mouse, F8 e F9 sobem e descem a linha.

## Ajustes

- Sensibilidade (% da linha): quanto da linha precisa mudar de cor pra disparar. Clicando sem querer, aumenta. Não dispara, diminui.
- Limite do branco: até onde um pixel ainda conta como branco. O cinza claro das marcações da barra tem que cair aqui.
- Intervalo entre cliques: mínimo de segundos entre um clique e outro.
- Desligar sozinho depois do clique: um clique por rodada.
- Botão do mouse: esquerdo ou direito.

O painel mostra ao vivo quanto da linha está colorido. Com a barra embaixo isso tem que ficar perto de zero.

## Se não funcionar

- Não clica nada: abre como administrador.
- Dispara com a barra ainda baixa: a linha deve estar pegando o fundo do jogo. Diminui a largura da linha pra ficar mais estreita que a barra, ou aumenta a sensibilidade.
- Nunca dispara: diminui a sensibilidade ou sobe a linha com F8.
- O Windows bloqueou o `.exe` que eu gerei: o Smart App Control barra executável sem assinatura, e todo `.exe` do PyInstaller cai nisso. Roda direto pelo Python que funciona igual.
- Coordenadas deslocadas: o app já avisa o Windows que lida com DPI, então 125% e 150% de escala não deveriam atrapalhar. Se ainda ficar torto, testa em 100%.

## Arquivos

- `autoclick_app.py`: o app todo, interface (Tkinter), captura e clique.
- `iniciar.bat`: atalho pra Windows.
- `requirements.txt`

As configurações (posição da linha etc.) vão pra um `config.json` que é criado quando você fecha o app. Está no `.gitignore` porque a posição só vale pra sua tela.

## Aviso

Isso automatiza clique em jogo, e muitos jogos (Roblox incluso) proíbem. Como ele só lê a tela e clica, costuma ser menos arriscado que exploit, mas ainda dá pra tomar ban. Use numa conta que você não se importe de perder.
