# Docker-Überwachung über SSH

Seit DocOfHome 1.7.19 können mehrere Docker-Server über SSH überwacht werden. Jeder
Server wird einem eigenen Host-Asset zugeordnet. Die bisherige lokale Socket-Verbindung
bleibt verfügbar und wird beim Update automatisch übernommen.

## Sicherheitsmodell

DocOfHome erzeugt für jeden SSH-Host ein eigenes Ed25519-Schlüsselpaar. Der private
Schlüssel bleibt unter `/data/secrets/docker-ssh/`, wird nie von der API ausgeliefert
und ist Bestandteil des verschlüsselungsfreien DocOfHome-Backups. Backups müssen daher
wie Zugangsdaten behandelt werden. Der öffentliche Schlüssel wird in der Oberfläche
angezeigt.

Der SSH-Server wird nicht automatisch vertraut. DocOfHome zeigt den ermittelten
SHA256-Fingerabdruck an. Vergleiche ihn auf dem Zielserver mit:

```bash
sudo ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub
```

Erst danach den vorgemerkten Server-Schlüssel speichern. Ein später geänderter
Host-Schlüssel führt absichtlich zu einem Verbindungsfehler.

## Zielserver vorbereiten

Die folgenden Befehle werden auf jedem Docker-Server ausgeführt. Namen und Pfade können
an die Distribution angepasst werden.

1. Den mitgelieferten Helfer `scripts/docofhome-docker-snapshot` auf den Server kopieren
   und nur für root schreibbar installieren:

```bash
sudo install -o root -g root -m 0755 docofhome-docker-snapshot \
  /usr/local/bin/docofhome-docker-snapshot
```

2. Einen eigenen Benutzer erstellen und für den Docker-Socket berechtigen:

```bash
sudo useradd --create-home --shell /bin/sh docofhome-monitor
sudo usermod -aG docker docofhome-monitor
sudo install -d -o docofhome-monitor -g docofhome-monitor -m 0700 \
  /home/docofhome-monitor/.ssh
```

3. In DocOfHome unter **Dienste & Container → Docker-Host** den Server speichern.
   Anschließend den angezeigten Public Key kopieren.

4. Auf dem Docker-Server genau eine eingeschränkte Zeile in
   `/home/docofhome-monitor/.ssh/authorized_keys` eintragen:

```text
restrict,command="/usr/local/bin/docofhome-docker-snapshot" ssh-ed25519 AAAA... docofhome-docker-...
```

Danach Besitzer und Rechte setzen:

```bash
sudo chown docofhome-monitor:docofhome-monitor \
  /home/docofhome-monitor/.ssh/authorized_keys
sudo chmod 0600 /home/docofhome-monitor/.ssh/authorized_keys
```

Die Option `restrict` deaktiviert unter anderem Port-, Agent- und X11-Weiterleitung sowie
PTYs. `command=...` verhindert eine normale Shell und führt unabhängig vom angeforderten
Befehl ausschließlich den lesenden Snapshot-Helfer aus. Dieser fragt nur Docker
`/version` und `/containers/json?all=1` ab.

Mitgliedschaft in der Docker-Gruppe ist grundsätzlich eine weitreichende Berechtigung.
Die erzwungene SSH-Zeile begrenzt, was mit diesem Schlüssel möglich ist. Andere Schlüssel
des Benutzers sollten nicht ohne dieselben Einschränkungen zugelassen werden.

## DocOfHome einrichten

Für jeden NUC, Server oder jedes NAS:

1. Ein passendes Asset anlegen oder auswählen.
2. SSH-Hostname/IP, Port und Benutzer speichern.
3. Public Key auf dem Zielserver hinterlegen.
4. „Server-Schlüssel abrufen“ wählen und Fingerabdruck extern vergleichen.
5. Den vorgemerkten Schlüssel speichern.
6. „Testen“ und anschließend „Abgleichen“ ausführen.
7. Bei Bedarf automatische Aktualisierung aktivieren.

Container mit demselben Namen oder derselben Docker-ID auf unterschiedlichen Hosts
bleiben getrennt. Entfernen einer Docker-Verbindung löscht weder das Host-Asset noch
bereits erfasste Dienste.

## Lokaler Socket

Für eine lokale Verbindung bleibt `/var/run/docker.sock` möglich. Dafür muss der Socket
wie bisher in den DocOfHome-Container eingebunden sein. Sobald ausschließlich SSH-Hosts
verwendet werden, kann die Socket-Einbindung aus `compose.yaml` entfernt werden.
