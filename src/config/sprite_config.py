# Responsabilidade:
# Centralizar todas as configurações visuais dos sprites do jogo.
# Define caminho, escala, dimensões, opacidade e parâmetros de animação
# para cada recurso identificado por uma chave intuitiva.
# Não contém lógica; apenas dados de configuração.
# Para adicionar um novo sprite: registre sua chave e configuração abaixo.

# Estrutura de cada entrada:
# "chave.identificador": {
#     "path"    : caminho relativo à raiz do projeto (None = fallback procedural)
#     "scale"   : multiplicador de escala (1.0 = tamanho original)
#     "width"   : largura final em px (None = mantém proporção via scale)
#     "height"  : altura final em px  (None = mantém proporção via scale)
#     "opacity" : 0–255 (255 = totalmente opaco)
#     "frames"  : número de quadros para sprites animados (1 = estático)
#     "fps"     : velocidade da animação em quadros/segundo
#     "loop"    : True = animação em loop, False = reproduz uma vez
# }

SPRITE_CONFIG: dict = {

    # ── Jogador ───────────────────────────────────────────────────────────────
    "player.default": {
        "path":    None,          # fallback: círculo procedural colorido
        "scale":   1.0,
        "width":   None,
        "height":  None,
        "opacity": 255,
        "frames":  1,
        "fps":     0,
        "loop":    False,
    },
    "player.shield": {
        "path":    None,          # fallback: anel verde procedural
        "scale":   1.0,
        "width":   None,
        "height":  None,
        "opacity": 200,
        "frames":  1,
        "fps":     0,
        "loop":    True,
    },

    # ── Bots ──────────────────────────────────────────────────────────────────
    "bot.default": {
        "path":    None,          # fallback: círculo procedural colorido
        "scale":   1.0,
        "width":   None,
        "height":  None,
        "opacity": 255,
        "frames":  1,
        "fps":     0,
        "loop":    False,
    },

    # ── Power-ups ─────────────────────────────────────────────────────────────
    "powerup.size_up": {
        "path":    "assets/sprites/powerups/size_up.png",
        "scale":   1.0,
        "width":   32,
        "height":  32,
        "opacity": 255,
        "frames":  1,
        "fps":     0,
        "loop":    False,
    },
    "powerup.speed": {
        "path":    "assets/sprites/powerups/speed.png",
        "scale":   1.0,
        "width":   32,
        "height":  32,
        "opacity": 255,
        "frames":  1,
        "fps":     0,
        "loop":    False,
    },
    "powerup.bomb": {
        "path":    "assets/sprites/powerups/bomb.png",
        "scale":   1.0,
        "width":   32,
        "height":  32,
        "opacity": 255,
        "frames":  1,
        "fps":     0,
        "loop":    False,
    },
    "powerup.shield": {
        "path":    "assets/sprites/powerups/shield.png",
        "scale":   1.0,
        "width":   32,
        "height":  32,
        "opacity": 255,
        "frames":  1,
        "fps":     0,
        "loop":    False,
    },
    "powerup.eagle": {
        "path":    "assets/sprites/powerups/eagle.png",
        "scale":   1.0,
        "width":   32,
        "height":  32,
        "opacity": 255,
        "frames":  1,
        "fps":     0,
        "loop":    False,
    },

    # ── Efeitos ───────────────────────────────────────────────────────────────
    "effect.explosion": {
        "path":    None,          # fallback: círculo procedural animado
        "scale":   1.0,
        "width":   None,
        "height":  None,
        "opacity": 220,
        "frames":  1,
        "fps":     0,
        "loop":    False,
    },
    "effect.particle": {
        "path":    None,          # fallback: círculo procedural
        "scale":   1.0,
        "width":   None,
        "height":  None,
        "opacity": 255,
        "frames":  1,
        "fps":     0,
        "loop":    False,
    },

    # ── Interface ─────────────────────────────────────────────────────────────
    "ui.predator_badge": {
        "path":    None,          # fallback: texto renderizado
        "scale":   1.0,
        "width":   None,
        "height":  None,
        "opacity": 255,
        "frames":  1,
        "fps":     0,
        "loop":    False,
    },
    "ui.btn_blue": {
        "path":    "assets/sprites/ui_kenney/blue/button_rectangle_depth_gradient.png",
        "scale":   1.0,
        "width":   None,
        "height":  None,
        "opacity": 255,
        "frames":  1,
        "fps":     0,
        "loop":    False,
    },
    "ui.btn_green": {
        "path":    "assets/sprites/ui_kenney/green/button_rectangle_depth_gradient.png",
        "scale":   1.0,
        "width":   None,
        "height":  None,
        "opacity": 255,
        "frames":  1,
        "fps":     0,
        "loop":    False,
    },
    "ui.btn_red": {
        "path":    "assets/sprites/ui_kenney/red/button_rectangle_depth_gradient.png",
        "scale":   1.0,
        "width":   None,
        "height":  None,
        "opacity": 255,
        "frames":  1,
        "fps":     0,
        "loop":    False,
    },
    "ui.btn_yellow": {
        "path":    "assets/sprites/ui_kenney/yellow/button_rectangle_depth_gradient.png",
        "scale":   1.0,
        "width":   None,
        "height":  None,
        "opacity": 255,
        "frames":  1,
        "fps":     0,
        "loop":    False,
    },
    "ui.star": {
        "path":    "assets/sprites/ui_kenney/star.png",
        "scale":   1.0,
        "width":   32,
        "height":  32,
        "opacity": 255,
        "frames":  1,
        "fps":     0,
        "loop":    False,
    },

    # ── Fundos ────────────────────────────────────────────────────────────────
    "bg.menu": {
        "path":    None,          # fallback: gradiente procedural
        "scale":   1.0,
        "width":   None,
        "height":  None,
        "opacity": 255,
        "frames":  1,
        "fps":     0,
        "loop":    False,
    },
    "bg.game": {
        "path":    None,          # fallback: grade procedural
        "scale":   1.0,
        "width":   None,
        "height":  None,
        "opacity": 255,
        "frames":  1,
        "fps":     0,
        "loop":    False,
    },
}

# ── Mapeamento de animações ────────────────────────────────────────────────────
# Estrutura preparada para futuras animações por spritesheet ou sequência.
# Cada entrada define o conjunto de quadros de um estado de animação.
ANIMATION_CONFIG: dict = {
    "player.idle": {
        "sprite_key": "player.default",
        "frames":     1,
        "fps":        0,
        "loop":       True,
    },
    "bot.idle": {
        "sprite_key": "bot.default",
        "frames":     1,
        "fps":        0,
        "loop":       True,
    },
    # Futuras animações:
    # "player.death": { "sprite_key": "player.death", "frames": 8, "fps": 12, "loop": False },
    # "powerup.collect": { "sprite_key": "effect.explosion", "frames": 6, "fps": 15, "loop": False },
}
