# Discord Community Bot (Python)

Un bot Discord en Python structuré avec plusieurs cogs pour la gestion d'une communauté francophone.
Ce projet est fourni à titre d'exemple et nécessite des personnalisations (IDs, permissions, token).

## Prérequis
- Python 3.10+ recommandé
- Installer les dépendances :
```
pip install -r requirements.txt
```

## Installation rapide
1. Copier `config.example.json` en `config.json` et renseigner `token`, `guild_id`, `mod_log_channel_id`, etc.
2. Lancer :
```
python bot.py
```

## Structure
- `bot.py` : entrée principale
- `cogs/` : cogs (moderation, welcome, reaction_roles, info, utils)
- `data/` : stockage basique (json) pour settings et data persistantes
- `requirements.txt` : dépendances
- `README.md` : ce fichier

## Notes
- Les temporisations (ex : unmute automatique) sont gérées en mémoire — si le bot redémarre, les timers sont perdus. Pour production, utilisez une DB ou une persistance plus robuste.
- Vérifiez les permissions du bot (Intents, Manage Roles, Kick/Ban, Send Messages, Manage Messages...)