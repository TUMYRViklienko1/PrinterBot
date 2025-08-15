# PrinterBot

- A powerful and easy-to-use Discord bot for monitoring and controlling your Bambu Lab 3D printers directly from your Discord server.
- With real-time updates, interactive menus, and printer management features, PrinterBot keeps you connected to your prints.

## Installation:
```bash
docker run -d \
  --name discordbot \
  --env-file .env \
  -v printer_data:/app/data \
  timyrviklienko/discordbot:latest
```
