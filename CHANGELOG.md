# CHANGELOG — PAPERWORLDS

## 1.3.9 (2026-11-27)

### Ressurreicao
- Regra fixa `RESPAWN_CLEAR_RADIUS_CELLS = 4`: so renasce se houver um disco de celulas jogaveis e sem tinta com esse raio.
- `RESPAWN_SEED_RADIUS_CELLS = 4` define o territorio inicial apos renascer.
- Sem espaco livre suficiente, o personagem nao renasce ate abrir area vazia (ou ate a partida terminar em 100%).

### Preenchimento de territorio
- Preenchimento tipo tinta para qualquer forma plana (curva, circular, irregular).
- Trilha mais grossa, flood local e passagem extra para fechar buracos internos.

### Performance
- Removidas superficies do mapa inteiro no desenho da borda (principal causa de travadas).
- Territorio e void desenhados em faixas horizontais.
- Movimento em um unico passo por frame; simulacao com timestep fixo a 60 Hz.

### Movimento
- Player e bots podem virar 180 e voltar pelo mesmo caminho.
- Deslize na barreira solta quando a direcao deixa a parede.

### Limpeza
- Imports nao usados removidos.
- Comentarios padronizados no estilo simples `# Comentario` (sem barras ASCII).
- Codigo morto de `update_position` removido.

### Identidade
- Nome do jogo: PAPERWORLDS em titulo, menus e HUD.

---

## 1.3.8 (2026-11-27)

- Mapa com 4x a area (480x480 celulas, 2880x2880 px).
- Timestep fixo a 60 FPS.
- Desgrudar da barreira facilitado.

## 1.3.7 (2026-11-27)

- Deslize na barreira mais estavel (menos inversao de lado).

## 1.3.6 (2026-11-27)

- Roubo de territorio ao eliminar adversario.
- Deslize na barreira real do mapa.
- Marcador visual do jogador (circulo + seta, 2 s).
- Cap de 60 FPS e renomeacao para PAPERWORLDS.

## 1.3.5

- Mapa dos estados em escala maxima.
- Ressurreicao em celulas nao pintadas ate 100% de dominio.

## 1.3.4

- Correcao da camera Visao de Aguia (segue o player e mostra trilhas).
- Contornos dos estados brasileiros alinhados ao geojson.

## 1.3.3

- Nickname flutuante sobre player e bots.
- Evolucao de dificuldade dos bots por fase.
- Correcao do preenchimento de area conquistada.

## 1.3.2

- Base TerritórIO Edição Brasil (refactor modular).
