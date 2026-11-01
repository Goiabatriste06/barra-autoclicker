# Barra Autoclicker

Um clicador automático pra minigames com **barra que sobe e vai mudando de cor**.
Você coloca uma linha de detecção perto do topo da barra e, quando a barra passa
por ela (a linha deixa de ser branca), o app dá o clique no botão que você escolher.

Nada de ler memória do jogo nem injetar nada: ele só **olha uns pixels da tela**
e **simula um clique**, igual um dedo seu faria, só que no tempo certo.

## Como funciona (resumão)

1. Você marca um ponto no meio da barra, perto do topo. O app captura uma faixa fininha de pixels ali (com [`mss`](https://github.com/BoboTiG/python-mss), que é bem rápido).
2. A cada ciclo ele classifica os pixels da faixa:
   - **branco** (inclui o cinza claro das marcações): a barra ainda não chegou;
   - **preto/escuro** (divisórias e contorno): ignorado;
   - **qualquer outra cor**: a barra passou por ali.
3. Se a porcentagem de pixels coloridos passar do limite (**Sensibilidade**), ele clica uma vez.
4. Opcionalmente ele se desliga sozinho depois do clique. Aí você aperta `F6` pra armar a próxima rodada.

Ele não guarda cor nenhuma de referência. Só olha "branco ou não branco". Por isso funciona com qualquer cor que a barra assumir.

## Requisitos

- Windows 10 ou 11
- Python 3.10 ou mais novo
- Rodar **como administrador** (senão o jogo costuma ignorar clique e atalho de teclado)

## Rodando

```bash
git clone https://github.com/Goiabatriste06/barra-autoclicker.git
cd barra-autoclicker
python -m pip install -r requirements.txt
python autoclick_app.py
```

Se preferir clicar: abra o **`iniciar.bat`** com *botão direito → Executar como administrador*.
Ele instala as dependências e abre o app.

> Se o `python` não for reconhecido, tente `py` no lugar. Dependendo de como o Python foi instalado, é um ou outro.

## Usando

1. Abra o jogo e deixe a barra visível.
2. No app, clique em **Capturar posição** (ou aperte `F7`) e leve o mouse pro **meio da barra, perto do topo**. Você tem 3 segundos. A linha vermelha aparece ali.
3. Ajuste a altura com `F8` (sobe) e `F9` (desce). Quanto mais alto a linha, mais tarde ele clica.
4. Aperte `F6` pra ligar. A linha fica verde. Quando a barra cruzar, ele clica.

| Atalho | O que faz |
|--------|-----------|
| `F6` | liga / desliga |
| `F7` | captura a posição do mouse |
| `F8` / `F9` | sobe / desce a linha |

## Ajustes que importam

| Opção | Pra que serve |
|-------|---------------|
| **Sensibilidade (% da linha)** | quanto da linha precisa mudar de cor pra disparar. Clicando sem querer? Aumenta. Não dispara? Diminui. |
| **Limite do branco** | até que ponto um pixel ainda conta como "branco". O cinza claro das marcações da barra deve cair aqui. |
| **Intervalo entre cliques** | segundos mínimos entre um clique e outro. |
| **Desligar sozinho depois do clique** | faz um clique por rodada e volta a ficar desligado. |
| **Botão do mouse** | direito ou esquerdo. |

O painel mostra, ao vivo, a porcentagem da linha que está colorida. Com a barra baixa, isso tem que ficar perto de zero.

## Problemas comuns

- **Não clica nada:** abra como administrador.
- **Dispara com a barra ainda baixa:** a linha provavelmente está pegando o fundo do jogo. Diminua a **Largura** da linha pra ficar mais estreita que a barra, ou aumente a sensibilidade.
- **Não dispara nunca:** diminua a sensibilidade ou suba a linha com `F8`.
- **O Windows bloqueou o `.exe` que eu gerei:** o Smart App Control barra executáveis sem assinatura (todo `.exe` do PyInstaller cai nisso). Rode direto pelo Python, que funciona igual.
- **As coordenadas estão deslocadas:** o app já se declara "DPI aware", então escala de 125% e 150% não deve atrapalhar. Se ainda assim estiver torto, teste em 100%.

## Estrutura

```
barra-autoclicker/
├── autoclick_app.py   # o app inteiro (interface Tkinter + captura + clique)
├── iniciar.bat        # atalho pra Windows
├── requirements.txt
└── .gitignore
```

As configurações (posição da linha etc.) ficam num `config.json` criado ao fechar o app. Ele está no `.gitignore` porque a posição vale só pra sua tela.

## Aviso

Isso automatiza input em jogos. Muitos jogos (Roblox incluso) têm regras contra automação e podem punir a conta.
O app não mexe no jogo, só lê a tela e clica, o que costuma ser menos arriscado que exploits, mas o risco existe.
**Use por sua conta e risco** e, de preferência, em conta que você não se importe de perder.
