# Dependencias de Runtime

O jogo deve iniciar com o minimo possivel de dependencias obrigatorias para preservar compatibilidade entre Windows e Linux.

## Obrigatoria

- `pygame-ce` ou `pygame`: base da janela, input, audio e renderizacao.

## Recomendadas e leves

- `pygame_gui`: janelas e controles de UI mais ricos. Sem ela, o jogo usa menus manuais.
- `pygame-menu`: menus de inicio e pausa mais polidos. Sem ela, entra um menu nativo simples em Pygame.
- `pytweening`: curvas de animacao. Sem ela, o projeto usa easing quadratico nativo.
- `loguru`: logs mais legiveis. Sem ela, o projeto usa `logging`.

## Opcionais

- `numpy`: particulas vetorizadas. Sem ela, o sistema usa listas Python.
- `pymunk`: fisica 2D para entidades e obstaculos. Sem ela, o jogo usa colisao do `World`.
- `pytmx`: carregamento futuro de mapas TMX. Sem ela, o mundo procedural continua funcionando.

## Experimentais

- `moderngl`: apresentacao via GPU/shaders. Sem ela, o render CPU do Pygame e usado.
- `numba`: aceleracao de funcoes matematicas. Sem ela, as mesmas funcoes rodam em Python puro.

Use `requirements-minimal.txt` para maquinas de teste limpas e `requirements.txt` para desenvolvimento completo.
