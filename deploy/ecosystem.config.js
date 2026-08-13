module.exports = {
  apps: [
    {
      name: "forex-signal-bot",
      script: "main.py",
      interpreter: "/opt/forex_signal_bot/venv/bin/python",
      cwd: "/opt/forex_signal_bot",
      env: {
        PYTHONPATH: "/opt/forex_signal_bot",
      },
      // Redémarrage automatique
      autorestart: true,
      max_restarts: 10,
      restart_delay: 30000,
      min_uptime: "30s",
      watch: false,
      // Logs
      error_file: "./logs/pm2-error.log",
      out_file: "./logs/pm2-out.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss Z",
      merge_logs: true,
      // Ressources
      max_memory_restart: "512M",
      kill_timeout: 10000,
      listen_timeout: 15000,
    },
  ],
};
