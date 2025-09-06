# StableDiffusion WebUI (SDWebUI) by Philipp Schott

![Python](https://img.shields.io/badge/python-3.13-blue?logo=python) 
![Django](https://img.shields.io/badge/django-5.2-green?logo=django)
![License](https://img.shields.io/badge/license-custom-red)

Ein modernes, nutzerfreundliches und neuartiges Web Interface für **Stable Diffusion**, entwickelt mit **Django**.  
Das Projekt legt Wert auf eine klare Bedienung, ein aufgeräumtes Design und ein performantes **Queue-System**.

---

## ✨ Features
- 🖼️ Web-UI für Stable Diffusion
- 📑 Eingebautes **Queue-System** zur Verwaltung mehrerer Jobs
- 🎨 Modernes & nutzerfreundliches Interface
- ⚡ Django-basiert (Python 3.13)

---

## 🚀 Installation (lokal)

### Voraussetzungen
- **Python** 3.13
- **Django** 5.2 oder aktueller
- Eine **GPU**, die Stable Diffusion unterstützt (CUDA oder ROCm, je nach Setup)
- Git + Pip

### Schritte
```bash
# Repository klonen
git clone https://github.com/vulpisnix/StableDiffusionWebUI.git
cd StableDiffusionWebUI

# Virtuelle Umgebung erstellen & aktivieren
python -m venv venv
source venv/bin/activate   # Linux/macOS
venv\Scripts\activate      # Windows

# Abhängigkeiten installieren
pip install -r requirements.txt

# Migrationen durchführen
python manage.py makemigrations
python manage.py migrate

# Server starten
python manage.py runserver
```

---

## 📸 Screenshots
*(Platzhalter – später Screenshots einfügen)*

---

## 🛠️ Entwicklung
Dieses Projekt wird derzeit allein entwickelt.  
Contributions sind aktuell nicht vorgesehen.

---

## 📜 Lizenz
Dieses Projekt darf **frei benutzt** werden,  
aber **Änderungen, Weiterverbreitung oder Forks sind nur mit meiner ausdrücklichen Einwilligung erlaubt**.

---

## 📬 Kontakt
- ✉️ philipp@busch-hub.de  
- ✉️ contact@crisestudios.com

---

## 📝 ToDo
- Screenshots für README hinzufügen
- Benutzersystem
- Queue-System erweitern (Prioritäten, Pausieren, Abbrechen)
- RESTful API
- Dokumentation erstellen
- Performance-Optimierungen für große Modelle
