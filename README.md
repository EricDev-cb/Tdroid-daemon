# Tdroid Daemon

Daemon Android desenvolvido em Python.

## Funcionalidades

- Detecta processo de aplicativo principal

- Aplica restrições automaticamente em processos secundarios

- Objetivo é otimizar e reduzir o uso da cpu por processos de aplicativos em segundo plano !

## Requisitos ⚠️
- ![Android](https://img.shields.io/badge/Android-11+-3DDC84?logo=android&logoColor=white)

- ![Termux](https://img.shields.io/badge/Termux-Terminal-black)

## Instalação

```bash
git clone https://github.com/EricDev-cb/Tdroid-daemon.git
cd Tdroid-daemon
pip install -r requirements.txt
```

## Roadmap

- [x] monitora aplicativos em primeiro e segundo plano
- [x] Aplica otimização em processos que esteja consumindo acima de 10% de cpu
- [ ] Suporte para linux (em breve)
- [ ] Interface gráfica (Apenas CLI GUI)

## Licença

MIT