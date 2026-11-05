# =============================================================================
# LÓGICA DA ICM PARA OS ENSAIOS (biblioteca usada pelos ensaios 1 e 3/4)
#
# O que este arquivo faz:
#   - Não é um script para rodar. Ele só define classes e funções.
#   - Coloca todas as "lógicas de decisão" atrás da MESMA interface:
#       maquina.processar(atencao) -> letra do gesto ("A" a "E")
#       maquina.y                  -> valor filtrado atual
#     Assim o ensaio 1 roda qualquer lógica com o mesmo código, trocando só
#     o nome no dicionário LOGICAS.
#
# Lógicas disponíveis:
#   - real_v2: o código atual do projeto, IMPORTADO (não é cópia).
#   - real_v1: a versão antiga, importada de ensaios/legado/.
#   - faixas_sem_trava e histerese_3: lógicas de comparação, que não existem
#     no projeto. Servem de referência para medir se a lógica real é melhor.
#
# Também traz duas verificações automáticas (no fim do arquivo) que provam
# que a v2 só mudou o que se pretendia mudar em relação à v1.
#
# Entrada: valores de atenção (inteiros 0-100). Saída: letras de gesto.
# =============================================================================
"""
Lógica de decisão da ICM isolada para ensaios de bancada (sem hardware).

NADA aqui altera o código do projeto. Origem de cada trecho:

- `MaquinaRealV2` IMPORTA e usa, sem modificação, a classe atual
  `EEGStateMachine` de `src/services/eeg_state_machine.py` (lógica v2).
- `MaquinaRealV1` IMPORTA `ensaios/legado/eeg_state_machine_v1.py`, cópia
  literal do mesmo arquivo no commit 5fca7f5 (lógica v1, y inicial = 0,
  C→E com y ≥ 80, variáveis `bloqueado` e `piso`).
- `pacote_para_comando` reproduz o portão de `EEGSystem._on_eeg` em
  `src/services/eeg_state_sytem.py`, linhas 20-28:
      if data.attention == 0: return            # pacote ignorado
      novo_estado = self.maquina.processar(data.attention)
      self.arduino.enviar_estado(novo_estado.value)   # enviado A CADA pacote
- `V1SemBloqueado` é uma cópia de `_transicao` da v1 (linhas 16-60 do
  arquivo legado) sem as linhas de `bloqueado`; prova que essa variável não
  tinha efeito (`verificar_bloqueado_v1`).
- `FiltroIniciado` reproduz o filtro da v2 (`processar` e
  `_filtro_passa_baixa` de eeg_state_machine.py): y = primeira leitura não
  nula; depois y = α·x + (1−α)·y. Só é usado pelas lógicas de comparação,
  para que elas tenham exatamente o mesmo filtro da v2.
- `FaixasSemTrava` e `HistereseClassica` NÃO existem no projeto: são
  lógicas de COMPARAÇÃO criadas para o ensaio, com os limiares nominais
  20 / 65 / 75 / 85.
"""
# Coloca a raiz do repositório no caminho de import. Assim conseguimos
# importar o código REAL do projeto (src/, core/) sem copiar nada.
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from core.state_enum import State                                      # noqa: E402
from src.services.eeg_state_machine import EEGStateMachine              # noqa: E402  (v2)
from ensaios.legado.eeg_state_machine_v1 import EEGStateMachine as EEGStateMachineV1  # noqa: E402

# O alpha é LIDO do código do projeto. Se alguém mudar o alpha no projeto,
# os ensaios acompanham automaticamente, sem número digitado à mão.
ALPHA_DO_CODIGO = EEGStateMachine().alpha   # lido do código (0.50), não digitado
GESTOS = "ABCDE"
LIMIARES_NOMINAIS = (20, 65, 75, 85)          # fronteiras inferiores de B, C, D, E


# Diz em qual faixa nominal um valor está, sem olhar estado anterior.
# Truque: conta quantos limiares o valor já passou (0 a 4) e usa isso como
# índice em "ABCDE". Ex.: 70 passa 20 e 65 → 2 → "C".
# É usada para definir a "faixa real" do sinal limpo no ensaio 1.
def faixa_nominal(x: float) -> str:
    """Faixa 'sem memória': A <20 ≤ B <65 ≤ C <75 ≤ D <85 ≤ E."""
    i = sum(x >= l for l in LIMIARES_NOMINAIS)
    return GESTOS[i]


# Reproduz o "portão" do sistema real (EEGSystem._on_eeg):
# atenção = 0 significa pacote sem leitura válida (o headset manda 0 quando
# não está em contato com a cabeça). O sistema real descarta esse pacote e
# não envia nada ao Arduino. Aqui isso vira None ("nada enviado").
# Todo pacote não nulo gera um comando, mesmo que repita o anterior,
# exatamente como o sistema real faz.
def pacote_para_comando(maquina, attention):
    """Reproduz EEGSystem._on_eeg (linhas 20-28): None = nada é enviado."""
    if attention == 0:
        return None
    return maquina.processar(attention)


# --------------------------------------------------------------------------
# Adaptador fino em volta da classe REAL do projeto. Não reimplementa nada:
# só converte o State para letra e expõe o valor filtrado como .y.
# Com alpha=1.0 o filtro vira y = x, ou seja, "sinal bruto" (sem filtro).
class MaquinaRealV2:
    """Código atual do projeto, importado. alpha=1.0 equivale a 'sinal bruto'."""
    nome = "real_v2"

    def __init__(self, alpha=ALPHA_DO_CODIGO):
        self.sm = EEGStateMachine(alpha=alpha)

    def processar(self, att) -> str:
        return self.sm.processar(att).value

    @property
    def y(self):
        return self.sm.att_filtrado


# Mesmo adaptador, mas apontando para a versão antiga (v1).
# Herda processar() e y da v2, porque as duas classes têm a mesma interface.
class MaquinaRealV1(MaquinaRealV2):
    """Lógica antiga (commit 5fca7f5), importada da cópia em ensaios/legado/."""
    nome = "real_v1"

    def __init__(self, alpha=ALPHA_DO_CODIGO):
        self.sm = EEGStateMachineV1(alpha=alpha)


# Existe só para uma prova: a variável `bloqueado` da v1 não mudava nada.
# É a v1 copiada SEM as linhas de `bloqueado`. Se v1 e esta cópia derem a
# mesma saída em todos os pacotes testados, a variável era inútil, e a
# remoção dela na v2 não altera o comportamento.
class V1SemBloqueado:
    """Cópia de _transicao da v1 sem nenhuma linha de `bloqueado`."""
    nome = "v1_sem_bloqueado"

    def __init__(self, alpha=ALPHA_DO_CODIGO):
        self.alpha = alpha
        self.att_filtrado = 0
        self.estado_atual = State.B
        self.piso = State.B

    def _transicao(self, att):
        match self.estado_atual:
            case State.A:
                if att >= 30:
                    self.estado_atual = State.B
            case State.B:
                self.piso = State.B
                if att < 20:
                    self.estado_atual = State.A
                elif att >= 85:
                    self.estado_atual = State.E
                    self.piso = State.E
                elif att >= 75:
                    self.estado_atual = State.D
                    self.piso = State.D
                elif att >= 65:
                    self.estado_atual = State.C
                    self.piso = State.C
            case State.C:
                if att >= 80:
                    self.estado_atual = State.E
                    self.piso = State.E
                elif att >= 75:
                    self.estado_atual = State.D
                    self.piso = State.D
                elif att < 33:
                    self.estado_atual = State.B
            case State.D:
                if att >= 85:
                    self.estado_atual = State.E
                    self.piso = State.E
                elif att < 33:
                    if self.piso <= State.D:
                        self.estado_atual = State.B
            case State.E:
                if att < 33:
                    if self.piso <= State.E:
                        self.estado_atual = State.B

    def processar(self, att) -> str:
        self.att_filtrado = self.alpha * att + (1 - self.alpha) * self.att_filtrado
        self._transicao(self.att_filtrado)
        return self.estado_atual.value

    @property
    def y(self):
        return self.att_filtrado


# Filtro idêntico ao da v2, separado da máquina de estados.
# Por que existe: as lógicas de comparação precisam do MESMO filtro da v2.
# Assim, qualquer diferença nos resultados vem da regra de decisão, não do
# filtro. É uma comparação justa.
class FiltroIniciado:
    """Mesmo filtro da v2: inicia na primeira leitura não nula."""

    def __init__(self, alpha):
        self.alpha, self.y, self.ok = alpha, 0.0, False

    def filtrar(self, att):
        if not self.ok:
            if att == 0:
                return self.y
            self.y, self.ok = float(att), True
        else:
            self.y = self.alpha * att + (1 - self.alpha) * self.y
        return self.y


# Lógica de comparação 1: a mais simples possível.
# Gesto = faixa do valor filtrado, sem memória e sem histerese.
# Serve para mostrar quantos acionamentos espúrios aparecem quando o sinal
# oscila perto de um limiar e nada segura o estado.
class FaixasSemTrava:
    """Comparação: faixa nominal do valor filtrado, sem memória de estado."""
    nome = "faixas_sem_trava"

    def __init__(self, alpha=ALPHA_DO_CODIGO):
        self.f = FiltroIniciado(alpha)

    @property
    def y(self):
        return self.f.y

    def processar(self, att) -> str:
        return faixa_nominal(self.f.filtrar(att))


# Lógica de comparação 2: histerese "de livro", simétrica.
# Para subir de faixa, o valor precisa passar o limiar + d.
# Para descer, precisa ficar abaixo do limiar − d. Com d = 3, uma oscilação
# de ±3 em torno do limiar não troca o gesto.
# Diferença para a v2: aqui a descida é degrau por degrau (E→D→C→B),
# enquanto a v2 retém C/D/E até 33 e volta direto para B.
class HistereseClassica:
    """Comparação: limiares nominais deslocados ±d (sobe com L+d, desce com L-d)."""
    nome = "histerese_3"

    def __init__(self, alpha=ALPHA_DO_CODIGO, d=3.0):
        self.f, self.d = FiltroIniciado(alpha), d
        self.i = 1  # começa em B, como a máquina real

    @property
    def y(self):
        return self.f.y

    def processar(self, att) -> str:
        y = self.f.filtrar(att)
        L = LIMIARES_NOMINAIS
        # Laços "while": num salto grande o estado pode andar várias faixas
        # no mesmo pacote (diferente da v2, que anda no máximo uma por pacote).
        while self.i < 4 and y >= L[self.i] + self.d:
            self.i += 1
        while self.i > 0 and y < L[self.i - 1] - self.d:
            self.i -= 1
        return GESTOS[self.i]


# Catálogo nome → classe. O ensaio 1 percorre este dicionário, então todas
# as lógicas passam exatamente pelos mesmos sinais.
LOGICAS = {c.nome: c for c in (MaquinaRealV2, MaquinaRealV1, FaixasSemTrava, HistereseClassica)}


# Prova 1: roda a v1 e a cópia sem `bloqueado` lado a lado, pacote a pacote,
# e conta quantas vezes o comando OU o valor filtrado diferem.
# Resultado esperado (e obtido): 0 diferenças.
def verificar_bloqueado_v1(sequencias, alphas):
    """v1 x v1 sem `bloqueado`. Retorna (n_pacotes, n_diferenças)."""
    n = dif = 0
    for a in alphas:
        for seq in sequencias:
            m1, m2 = MaquinaRealV1(a), V1SemBloqueado(a)
            for x in seq:
                r1, r2 = pacote_para_comando(m1, x), pacote_para_comando(m2, x)
                n += 1
                dif += (r1 != r2) or (m1.y != m2.y)
    return n, dif


# Prova 2: a v2 só difere da v1 nas duas mudanças pretendidas:
#   (1) o filtro começa na 1ª leitura válida, não em 0;
#   (2) C → E passou a exigir y >= 85 (na v1 era 80).
# Para isolar a mudança (2), a v1 é rodada com o início de filtro da v2.
# Toda divergência que aparecer tem de ser do tipo "estava em C com
# 80 <= y < 85: v1 foi para E, v2 foi para D". Qualquer outra conta como
# "inexplicada". Resultado esperado: 0 inexplicadas.
def verificar_v1_v2(sequencias, alphas):
    """Confere que a v2 só difere da v1 pelas duas mudanças pretendidas.

    Na v1, o primeiro pacote é tratado como na v2 (att_filtrado = primeira
    leitura e _transicao direto, sem EMA). As duas rodam em paralelo; quando
    divergem, a divergência só é aceita se a v1 estava em C com 80 ≤ y < 85
    (único ponto em que C→E mudou). Nesse caso a v1 é ressincronizada.
    Retorna (n_pacotes, n_divergencias_explicadas, n_divergencias_inexplicadas).
    """
    n = expl = inexpl = 0
    for a in alphas:
        for seq in sequencias:
            v1, v2 = EEGStateMachineV1(alpha=a), EEGStateMachine(alpha=a)
            iniciado = False
            for x in seq:
                if x == 0:
                    continue                      # portão de _on_eeg
                antes = v1.estado_atual
                if not iniciado:                  # emula o novo início do filtro na v1
                    v1.att_filtrado = x
                    v1._transicao(x)
                    s1 = v1.estado_atual
                    iniciado = True
                else:
                    s1 = v1.processar(x)
                s2 = v2.processar(x)
                n += 1
                if v1.att_filtrado != v2.att_filtrado:
                    inexpl += 1
                if s1 != s2:
                    y = v2.att_filtrado
                    if antes == State.C and 80 <= y < 85 and s1 == State.E and s2 == State.D:
                        expl += 1
                    else:
                        inexpl += 1
                    # Ressincroniza a v1 com a v2 para que uma divergência
                    # explicada não gere divergências em cascata depois.
                    v1.estado_atual = s2
                    v1.piso = s2 if s2 in (State.C, State.D, State.E) else State.B
    return n, expl, inexpl
