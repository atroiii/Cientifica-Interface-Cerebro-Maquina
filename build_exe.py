"""Gera o executável do ICM com o PyInstaller.

Uso (na raiz do projeto, no Windows, com o mesmo Python 3.11 do projeto):

    pip install -r requirements.txt pyinstaller
    python build_exe.py              # pasta dist/ICM-Monitor/ (abre mais rápido)
    python build_exe.py --um-arquivo # um único dist/ICM-Monitor.exe

O SDK do BrainLink (deps/BrainLinkParser.pyd) precisa estar no lugar: ele é
copiado para dentro do executável.
"""
import argparse
import os
import shutil
import sys

NOME = "ICM-Monitor"
RAIZ = os.path.dirname(os.path.abspath(__file__))


def erro(msg):
    print(f"\n[ERRO] {msg}\n")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Gera o executável do ICM.")
    parser.add_argument("--um-arquivo", action="store_true",
                        help="gera um único .exe (mais fácil de copiar, mas demora "
                             "alguns segundos a mais para abrir)")
    args = parser.parse_args()

    os.chdir(RAIZ)

    try:
        import PyInstaller.__main__
    except ImportError:
        erro("PyInstaller não está instalado. Rode:  pip install pyinstaller")

    if os.name == "nt":
        sdk = os.path.join("deps", "BrainLinkParser.pyd")
    else:
        print("[aviso] Fora do Windows: o executável gerado só roda neste sistema.")
        sdk = next((os.path.join("deps", f) for f in os.listdir("deps")
                    if f.startswith("BrainLinkParser")
                    and f.endswith((".so", ".pyd", ".py"))), "")
    if not os.path.isfile(sdk):
        erro("SDK do BrainLink não encontrado em deps/BrainLinkParser.pyd.\n"
             "        Baixe em https://github.com/Macrotellect/BrainLinkParser-Python "
             "(veja o README).")
    if sys.version_info[:2] != (3, 11):
        print(f"[aviso] Python {sys.version_info[0]}.{sys.version_info[1]}: o SDK do "
              "BrainLink é compilado para o Python 3.11 e pode não funcionar.")

    sep = os.pathsep  # ";" no Windows, ":" no Linux/macOS
    destino_sdk = "deps"
    opcoes = [
        "main.py",
        f"--name={NOME}",
        "--windowed",              # sem janela de console
        "--noconfirm",
        "--clean",
        f"--icon={os.path.join('assets', 'icone.ico')}",
        f"--add-data={os.path.join('assets', 'icone.ico')}{sep}assets",
        "--collect-data=customtkinter",   # temas e fontes do CustomTkinter
        "--hidden-import=deps.BrainLinkParser",
        "--onefile" if args.um_arquivo else "--onedir",
    ]
    if sdk.endswith(".py"):
        opcoes.append(f"--add-data={sdk}{sep}{destino_sdk}")
    else:
        opcoes.append(f"--add-binary={sdk}{sep}{destino_sdk}")

    print("Gerando o executável (leva de 1 a 3 minutos)...\n")
    PyInstaller.__main__.run(opcoes)

    shutil.rmtree("build", ignore_errors=True)
    exe = NOME + (".exe" if os.name == "nt" else "")
    caminho = os.path.join("dist", exe) if args.um_arquivo else os.path.join("dist", NOME, exe)
    print("\nPronto! Executável em:", os.path.abspath(caminho))
    if not args.um_arquivo:
        print("Para levar para outro computador, copie a pasta inteira "
              f"dist/{NOME}/ (o .exe precisa dos arquivos que estão ao lado dele).")


if __name__ == "__main__":
    main()
