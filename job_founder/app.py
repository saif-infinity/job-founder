from __future__ import annotations

import json
import re
import shutil
import sys
from datetime import date, datetime
from pathlib import Path

from PySide6.QtCore import Qt, QThread, QTimer, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QFont
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog,
    QFormLayout, QFrame, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox,
    QPushButton, QSpinBox, QSplitter, QTableWidget,
    QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget,
)


JOBS = [
    {"title": "Développeur·euse Backend Python", "company": "Nova Tech", "city": "Lyon", "distance": "8 km", "contract": "CDI", "salary": "45–55 k€", "source": "Carrières", "date": "Il y a 2 j", "score": 89, "state": "Dossier prêt", "remote": "Hybride", "skills": ["Python", "PostgreSQL", "Docker"], "missing": ["Kubernetes"], "summary": "Rejoignez une équipe produit qui construit des services backend fiables. Vous contribuerez à la conception d’API, à l’observabilité et à l’amélioration continue de la plateforme.", "issues": ["Connexion requise avant l’accès au formulaire"], "link": "https://careers.example.org/nova/backend-python"},
    {"title": "Data Analyst", "company": "Gamma Conseil", "city": "Lyon", "distance": "12 km", "contract": "CDI", "salary": "40–48 k€", "source": "Welcome to the Jungle", "date": "Il y a 1 j", "score": 82, "state": "À analyser", "remote": "Télétravail", "skills": ["SQL", "Python", "Power BI"], "missing": ["Looker"], "summary": "Analysez des données opérationnelles et transformez les résultats en recommandations concrètes pour les équipes métier.", "issues": [], "link": "https://jobs.example.org/gamma/data-analyst"},
    {"title": "Ingénieur logiciel Python", "company": "Acme Digital", "city": "Villeurbanne", "distance": "5 km", "contract": "CDI", "salary": "50–60 k€", "source": "Site entreprise", "date": "Il y a 3 j", "score": 78, "state": "Bloqué", "remote": "Hybride", "skills": ["Python", "AWS", "CI/CD"], "missing": ["Terraform"], "summary": "Développement d’outils internes et de services cloud au sein d’une équipe plateforme.", "issues": ["Protection anti-robot détectée — intervention humaine requise"], "link": "https://jobs.example.org/acme/engineer"},
    {"title": "Développeur·euse Python junior", "company": "Atelier Numérique", "city": "Lyon", "distance": "3 km", "contract": "CDD", "salary": "33–38 k€", "source": "France Travail", "date": "Il y a 5 j", "score": 71, "state": "À vérifier", "remote": "Sur site", "skills": ["Python", "Django", "Git"], "missing": ["Django"], "summary": "Participez à la maintenance et à l’évolution d’applications métier avec une équipe à taille humaine.", "issues": ["Salaire affiché à confirmer"], "link": "https://jobs.example.org/atelier/python-junior"},
    {"title": "Chef·fe de projet digital", "company": "Beta Studio", "city": "Paris", "distance": "393 km", "contract": "CDI", "salary": "—", "source": "Agrégateur", "date": "Il y a 4 j", "score": 54, "state": "Ignoré", "remote": "Hybride", "skills": ["Agile", "Gestion de projet"], "missing": ["Jira"], "summary": "Pilotage de projets digitaux de la conception à la mise en production.", "issues": ["Hors du rayon de recherche"], "link": "https://jobs.example.org/beta/project"},
    {"title": "Développeur full-stack", "company": "Pixel & Co", "city": "Lyon", "distance": "9 km", "contract": "Freelance", "salary": "TJM 450 €", "source": "Site entreprise", "date": "Il y a 8 j", "score": 67, "state": "Expirée", "remote": "Télétravail", "skills": ["JavaScript", "Python", "API"], "missing": ["React"], "summary": "Mission de modernisation d’une application de gestion de contenu.", "issues": ["L’offre semble expirée"], "link": "https://jobs.example.org/pixel/fullstack"},
]

NAV_ITEMS = ["Accueil", "Offres", "Blocages", "Dossiers prêts", "Candidatures envoyées", "Sources", "Historique", "Paramètres"]

STYLE = """
QWidget { color: #172b4d; font-family: 'Inter', 'Segoe UI', sans-serif; font-size: 13px; }
QMainWindow, QWidget#root { background: #f4f7fb; }
QFrame#topbar, QFrame#panel, QFrame#sidebar, QFrame#activity, QFrame#filterbox { background: #ffffff; border: 1px solid #e5eaf1; border-radius: 12px; }
QFrame#sidebar { border-radius: 0px; border-width: 0px 1px 0px 0px; }
QLabel#brand { font-size: 18px; font-weight: 750; color: #12233e; }
QLabel#eyebrow { color: #8090a7; font-size: 10px; font-weight: 700; letter-spacing: 1px; }
QLabel#pageTitle { font-size: 22px; font-weight: 750; color: #152845; }
QLabel#muted { color: #74839a; }
QPushButton { background: #f4f6fa; border: 1px solid #e3e8f0; border-radius: 7px; padding: 8px 12px; color: #334663; font-weight: 600; }
QPushButton:hover { background: #eaf0f8; }
QPushButton#primary { background: #2769e8; color: white; border: 1px solid #2769e8; padding: 10px 18px; }
QPushButton#primary:hover { background: #1f59c9; }
QPushButton#nav { text-align: left; padding: 11px 12px; border: none; background: transparent; color: #63738d; font-weight: 600; }
QPushButton#nav:hover, QPushButton#nav[selected="true"] { background: #edf3ff; color: #2769e8; }
QLineEdit, QComboBox, QSpinBox, QTextEdit { border: 1px solid #dfe5ee; border-radius: 7px; padding: 7px 9px; background: white; selection-background-color: #cfe0ff; }
QTableWidget { border: none; background: white; gridline-color: #edf0f5; selection-background-color: #eef4ff; selection-color: #142b4e; alternate-background-color: #fbfcfe; }
QHeaderView::section { background: #f8fafc; color: #8290a4; padding: 9px 6px; border: none; border-bottom: 1px solid #e9edf3; font-size: 10px; font-weight: 750; }
QCheckBox { color: #53647d; spacing: 6px; }
"""


class PageAnalysisWorker(QThread):
    completed = Signal(object)
    failed = Signal(str)

    def __init__(self, url: str, parent=None):
        super().__init__(parent)
        self.url = url

    def run(self):
        try:
            from .navigation import analyze_with_playwright
            self.completed.emit(analyze_with_playwright(self.url))
        except Exception as exc:
            self.failed.emit(str(exc))


def label(text: str, name: str = "") -> QLabel:
    w = QLabel(text)
    if name:
        w.setObjectName(name)
    return w


def card() -> QFrame:
    frame = QFrame()
    frame.setObjectName("panel")
    return frame


class ResumeDialog(QDialog):
    def __init__(self, filepath: Path, extracted: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Vérifier le profil extrait")
        self.resize(560, 500)
        self.filepath = filepath
        layout = QVBoxLayout(self)
        layout.addWidget(label("Vérifiez les informations avant la recherche.", "pageTitle"))
        layout.addWidget(label("Le CV reste sur cet appareil. Les champs ci-dessous sont modifiables.", "muted"))
        form = QFormLayout()
        self.name = QLineEdit()
        self.email = QLineEdit()
        self.phone = QLineEdit()
        nonempty = [line.strip() for line in extracted.splitlines() if line.strip()]
        if nonempty and len(nonempty[0]) < 70 and not re.search(r"(?i)curriculum|\b(cv|resume)\b", nonempty[0]):
            self.name.setText(nonempty[0])
        email_match = re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", extracted)
        phone_match = re.search(r"(?:\+?\d[\d .()/-]{7,}\d)", extracted)
        if email_match: self.email.setText(email_match.group())
        if phone_match: self.phone.setText(phone_match.group().strip())
        self.city = QComboBox()
        self.city.setEditable(True)
        cities = re.findall(r"\b(?:Lyon|Paris|Marseille|Toulouse|Bordeaux|Lille|Nantes|Nice|Grenoble|Strasbourg)\b", extracted, re.I)
        unique = list(dict.fromkeys(c.title() for c in cities)) or ["Lyon"]
        self.city.addItems(unique)
        self.skills = QTextEdit()
        self.skills.setPlaceholderText("Ex. Python, SQL, gestion de projet…")
        self.skills.setMaximumHeight(72)
        self.experience = QLineEdit()
        self.experience.setPlaceholderText("Ex. 5 ans (à confirmer)")
        form.addRow("Nom et prénom", self.name)
        form.addRow("E-mail", self.email)
        form.addRow("Téléphone", self.phone)
        form.addRow("Ville détectée — à confirmer", self.city)
        form.addRow("Compétences", self.skills)
        form.addRow("Expérience", self.experience)
        layout.addLayout(form)
        self.radius = QSpinBox()
        self.radius.setRange(1, 250)
        self.radius.setValue(30)
        radius_row = QHBoxLayout()
        radius_row.addWidget(self.radius)
        radius_row.addWidget(label("km   ·   Télétravail et hybride acceptés", "muted"))
        radius_row.addStretch()
        layout.addWidget(label("Rayon de recherche", "eyebrow"))
        layout.addLayout(radius_row)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Save)
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("Enregistrer le profil")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.extracted = extracted

    def profile(self) -> dict:
        return {"file": str(self.filepath), "name": self.name.text(), "email": self.email.text(), "phone": self.phone.text(), "city": self.city.currentText(), "skills": self.skills.toPlainText(), "experience": self.experience.text(), "radius": self.radius.value()}


class JobFounderWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Job Founder — Centre de contrôle")
        self.resize(1460, 900)
        self.setMinimumSize(1120, 720)
        self.profile = {}
        self.analysis_worker = None
        self.statuses = {j["title"]: j["state"] for j in JOBS}
        self.active_filter = "Toutes les offres"
        self.selected_job = JOBS[0]
        self.activity_log = ["Espace de travail prêt · données de démonstration", "Les sources distantes ne sont pas encore connectées"]
        self.setAcceptDrops(True)
        self._build()
        self._populate_table()
        self._show_detail(self.selected_job)

    def _build(self):
        root = QWidget()
        root.setObjectName("root")
        outer = QVBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        top = QFrame()
        top.setObjectName("topbar")
        top.setMaximumHeight(84)
        row = QHBoxLayout(top)
        row.setContentsMargins(22, 12, 22, 12)
        brand = label("✦  Job Founder", "brand")
        row.addWidget(brand)
        row.addSpacing(18)
        self.cv_label = label("CV non importé", "muted")
        self.city_label = label("Ville : à confirmer", "muted")
        self.radius_label = label("Rayon : 30 km", "muted")
        self.offer_count = label("6 offres", "muted")
        self.issue_count = label("2 blocages", "muted")
        self.packet_count = label("1 dossier prêt", "muted")
        for item in (self.cv_label, self.city_label, self.radius_label, self.offer_count, self.issue_count, self.packet_count):
            row.addWidget(item)
            row.addSpacing(12)
        row.addStretch()
        self.search_button = QPushButton("⌕  Rechercher")
        self.search_button.setObjectName("primary")
        self.search_button.clicked.connect(self.search)
        row.addWidget(self.search_button)
        outer.addWidget(top)

        split = QSplitter(Qt.Orientation.Horizontal)
        split.setChildrenCollapsible(False)
        split.addWidget(self._sidebar())
        split.addWidget(self._center())
        split.addWidget(self._details())
        split.setSizes([190, 750, 390])
        outer.addWidget(split, 1)
        outer.addWidget(self._activity())
        self.setCentralWidget(root)
        self.setStyleSheet(STYLE)

    def _sidebar(self):
        box = QFrame()
        box.setObjectName("sidebar")
        box.setMinimumWidth(165)
        box.setMaximumWidth(205)
        layout = QVBoxLayout(box)
        layout.setContentsMargins(12, 20, 12, 16)
        layout.addWidget(label("ESPACE DE TRAVAIL", "eyebrow"))
        layout.addSpacing(10)
        self.nav_buttons = []
        for i, text in enumerate(NAV_ITEMS):
            b = QPushButton(("◉  " if i == 0 else "•  ") + text)
            b.setObjectName("nav")
            b.setProperty("selected", i == 0)
            b.clicked.connect(lambda checked=False, name=text: self.navigate(name))
            layout.addWidget(b)
            self.nav_buttons.append(b)
        layout.addStretch()
        mini = QFrame()
        mini.setStyleSheet("background:#f2f6ff;border-radius:9px;padding:7px")
        ml = QVBoxLayout(mini)
        ml.addWidget(label("Données locales", "eyebrow"))
        ml.addWidget(label("Votre CV ne quitte pas cet appareil.", "muted"))
        layout.addWidget(mini)
        return box

    def _center(self):
        box = QWidget()
        layout = QVBoxLayout(box)
        layout.setContentsMargins(18, 18, 12, 12)
        layout.setSpacing(12)
        head = QHBoxLayout()
        title_col = QVBoxLayout()
        title_col.addWidget(label("Offres d’emploi", "pageTitle"))
        title_col.addWidget(label("Données fictives pour la démonstration · aucune offre réelle chargée", "muted"))
        head.addLayout(title_col)
        head.addStretch()
        self.import_button = QPushButton("＋  Importer un CV")
        self.import_button.clicked.connect(self.import_cv)
        head.addWidget(self.import_button)
        layout.addLayout(head)

        filters = QFrame()
        filters.setObjectName("filterbox")
        fl = QVBoxLayout(filters)
        fl.setContentsMargins(12, 10, 12, 10)
        line1 = QHBoxLayout()
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("⌕  Poste, entreprise ou compétence")
        self.search_field.textChanged.connect(self._populate_table)
        self.score_filter = QComboBox()
        self.score_filter.addItems(["Score : tous", "≥ 60", "≥ 70", "≥ 80"])
        self.score_filter.currentIndexChanged.connect(self._populate_table)
        self.contract_filter = QComboBox()
        self.contract_filter.addItems(["Tous contrats", "CDI", "CDD", "Freelance", "Stage", "Alternance"])
        self.contract_filter.currentIndexChanged.connect(self._populate_table)
        line1.addWidget(self.search_field, 2)
        line1.addWidget(self.score_filter)
        line1.addWidget(self.contract_filter)
        fl.addLayout(line1)
        line2 = QHBoxLayout()
        self.remote_checks = []
        for text in ("Télétravail", "Hybride", "Sur site"):
            cb = QCheckBox(text)
            cb.setChecked(True)
            cb.stateChanged.connect(self._populate_table)
            line2.addWidget(cb)
            self.remote_checks.append(cb)
        line2.addSpacing(10)
        line2.addWidget(label("Ville :", "muted"))
        self.city_filter = QLineEdit()
        self.city_filter.setPlaceholderText("Lyon")
        self.city_filter.setMaximumWidth(125)
        self.city_filter.textChanged.connect(self._populate_table)
        line2.addWidget(self.city_filter)
        line2.addWidget(label("Rayon", "muted"))
        self.radius_filter = QSpinBox()
        self.radius_filter.setRange(1, 250)
        self.radius_filter.setValue(30)
        self.radius_filter.setSuffix(" km")
        self.radius_filter.valueChanged.connect(self._populate_table)
        line2.addWidget(self.radius_filter)
        line2.addStretch()
        fl.addLayout(line2)
        layout.addWidget(filters)

        table_card = card()
        tl = QVBoxLayout(table_card)
        tl.setContentsMargins(0, 0, 0, 0)
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(["SCORE", "POSTE / ENTREPRISE", "LIEU", "CONTRAT", "SALAIRE", "SOURCE", "PUBLIÉE", "ÉTAT"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(61)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setColumnWidth(0, 68)
        self.table.setColumnWidth(1, 230)
        self.table.setColumnWidth(2, 120)
        self.table.setColumnWidth(3, 84)
        self.table.setColumnWidth(4, 92)
        self.table.setColumnWidth(5, 115)
        self.table.setColumnWidth(6, 85)
        self.table.itemSelectionChanged.connect(self._selection_changed)
        tl.addWidget(self.table)
        layout.addWidget(table_card, 1)
        return box

    def _details(self):
        box = QFrame()
        box.setObjectName("panel")
        box.setMinimumWidth(330)
        box.setMaximumWidth(470)
        layout = QVBoxLayout(box)
        layout.setContentsMargins(18, 18, 18, 16)
        layout.setSpacing(10)
        top = QHBoxLayout()
        top.addWidget(label("ANALYSE DE L’OFFRE", "eyebrow"))
        top.addStretch()
        self.badge = label("Correspondance forte")
        self.badge.setStyleSheet("background:#e8f7ef;color:#18834c;padding:5px 8px;border-radius:9px;font-weight:700;font-size:10px")
        top.addWidget(self.badge)
        layout.addLayout(top)
        self.detail_title = label("", "pageTitle")
        self.detail_title.setWordWrap(True)
        layout.addWidget(self.detail_title)
        self.detail_company = label("", "muted")
        layout.addWidget(self.detail_company)
        self.detail_link = QPushButton("↗  Copier le lien exact")
        self.detail_link.clicked.connect(self.copy_link)
        layout.addWidget(self.detail_link)

        scorebox = QFrame()
        scorebox.setStyleSheet("background:#f3f7ff;border:1px solid #e3edff;border-radius:10px")
        sb = QHBoxLayout(scorebox)
        self.score_value = label("89", "pageTitle")
        self.score_value.setStyleSheet("font-size:29px;font-weight:800;color:#2769e8")
        sb.addWidget(self.score_value)
        sb.addWidget(label("/100  ·  score explicable\nCompétences, lieu, expérience, fraîcheur", "muted"))
        sb.addStretch()
        layout.addWidget(scorebox)
        layout.addWidget(label("RÉSUMÉ", "eyebrow"))
        self.summary = label("", "muted")
        self.summary.setWordWrap(True)
        layout.addWidget(self.summary)
        layout.addWidget(label("COMPÉTENCES", "eyebrow"))
        self.skills_label = label("")
        self.skills_label.setWordWrap(True)
        layout.addWidget(self.skills_label)
        layout.addWidget(label("POINT À VÉRIFIER", "eyebrow"))
        self.issue_label = label("")
        self.issue_label.setWordWrap(True)
        self.issue_label.setStyleSheet("color:#a35a12;background:#fff6e9;border-radius:7px;padding:8px")
        layout.addWidget(self.issue_label)
        self.status_label = label("État : Dossier prêt", "muted")
        layout.addWidget(self.status_label)
        layout.addWidget(label("Dossier : copie du CV source · lettre modèle · réponses · checklist", "muted"))
        layout.addStretch()
        self.analyze_btn = QPushButton("Analyser la page")
        self.analyze_btn.clicked.connect(self.analyze_page)
        self.packet_btn = QPushButton("Préparer le dossier")
        self.packet_btn.clicked.connect(self.prepare_packet)
        self.open_btn = QPushButton("Ouvrir l’offre")
        self.open_btn.clicked.connect(self.open_job)
        self.applied_btn = QPushButton("Marquer comme postulé")
        self.applied_btn.clicked.connect(self.mark_applied)
        self.ignore_btn = QPushButton("Ignorer cette offre")
        self.ignore_btn.clicked.connect(self.ignore_job)
        for button in (self.analyze_btn, self.packet_btn, self.open_btn, self.applied_btn, self.ignore_btn):
            layout.addWidget(button)
        return box

    def _activity(self):
        box = QFrame()
        box.setObjectName("activity")
        box.setMaximumHeight(94)
        layout = QVBoxLayout(box)
        layout.setContentsMargins(18, 8, 18, 8)
        head = QHBoxLayout()
        head.addWidget(label("JOURNAL D’ACTIVITÉ", "eyebrow"))
        head.addStretch()
        head.addWidget(label("●  Prêt", "muted"))
        layout.addLayout(head)
        self.log_text = label("  ·  ".join(self.activity_log[-2:]), "muted")
        layout.addWidget(self.log_text)
        return box

    def _populate_table(self, *_):
        current_row = self.table.currentRow() if hasattr(self, "table") else -1
        selected_title = None
        if current_row >= 0 and self.table.item(current_row, 1):
            selected_title = self.table.item(current_row, 1).data(Qt.ItemDataRole.UserRole)
        text = self.search_field.text().strip().lower() if hasattr(self, "search_field") else ""
        minimum = [0, 60, 70, 80][self.score_filter.currentIndex()] if hasattr(self, "score_filter") else 0
        contract = self.contract_filter.currentText() if hasattr(self, "contract_filter") else "Tous contrats"
        city = self.city_filter.text().strip().lower() if hasattr(self, "city_filter") else ""
        radius = self.radius_filter.value() if hasattr(self, "radius_filter") else 250
        remote_allowed = {cb.text(): cb.isChecked() for cb in self.remote_checks} if hasattr(self, "remote_checks") else {}
        visible = []
        for job in JOBS:
            searchable = " ".join([job["title"], job["company"], job["city"], *job["skills"]]).lower()
            if text and text not in searchable: continue
            if job["score"] < minimum: continue
            if contract != "Tous contrats" and job["contract"] != contract: continue
            if city and city not in job["city"].lower(): continue
            distance = int(re.search(r"\d+", job["distance"]).group())
            if distance > radius and job["remote"] != "Télétravail": continue
            if remote_allowed and not remote_allowed.get(job["remote"], True): continue
            if self.active_filter == "Blocages" and not job["issues"]: continue
            if self.active_filter == "Dossiers prêts" and self.statuses.get(job["title"], job["state"]) != "Dossier prêt": continue
            if self.active_filter == "Candidatures envoyées" and self.statuses.get(job["title"], job["state"]) != "Postulée": continue
            visible.append(job)
        self.table.setRowCount(len(visible))
        for r, job in enumerate(visible):
            score = QTableWidgetItem(f"{job['score']}  /100")
            score.setForeground(Qt.GlobalColor.darkGreen if job["score"] >= 80 else Qt.GlobalColor.darkBlue)
            vals = [score, QTableWidgetItem(f"{job['title']}\n{job['company']}"), QTableWidgetItem(f"{job['city']} · {job['distance']}"), QTableWidgetItem(job["contract"]), QTableWidgetItem(job["salary"]), QTableWidgetItem(job["source"]), QTableWidgetItem(job["date"]), QTableWidgetItem(self.statuses.get(job["title"], job["state"]))]
            for c, item in enumerate(vals):
                item.setData(Qt.ItemDataRole.UserRole, job["title"])
                if c == 1: item.setFont(QFont("", -1, QFont.Weight.DemiBold))
                self.table.setItem(r, c, item)
        if visible:
            restore = next((i for i, item in enumerate(visible) if item["title"] == selected_title), 0)
            self.table.selectRow(restore)
        else:
            self.table.clearSelection()
            self.detail_title.setText("Aucune offre pour ces filtres")
            self.detail_company.setText("Modifiez les critères ou relancez la recherche.")
        self.offer_count.setText(f"{len(visible)} offres")
        self.issue_count.setText(f"{sum(bool(j['issues']) for j in JOBS)} blocages")
        ready = sum(self.statuses.get(j["title"], j["state"]) == "Dossier prêt" for j in JOBS)
        self.packet_count.setText(f"{ready} dossier(s) prêt(s)")

    def _selection_changed(self):
        row = self.table.currentRow()
        if row < 0: return
        title = self.table.item(row, 1).data(Qt.ItemDataRole.UserRole)
        job = next((j for j in JOBS if j["title"] == title), None)
        if job:
            self.selected_job = job
            self._show_detail(job)

    def _show_detail(self, job):
        self.detail_title.setText(job["title"])
        self.detail_company.setText(f"{job['company']}  ·  {job['city']} · {job['distance']}  ·  {job['contract']} · {job['remote']}")
        self.score_value.setText(str(job["score"]))
        self.summary.setText(job["summary"])
        self.skills_label.setText("✓  " + "   ✓  ".join(job["skills"]) + "\n−  Manquante : " + (", ".join(job["missing"]) or "aucune signalée"))
        issues = job["issues"]
        self.issue_label.setText("⚑  " + (" · ".join(issues) if issues else "Aucun blocage détecté dans la fiche de démonstration."))
        self.status_label.setText("État : " + self.statuses.get(job["title"], job["state"]))
        self.badge.setText("Correspondance forte" if job["score"] >= 80 else "À vérifier" if job["score"] >= 60 else "Correspondance faible")
        self.detail_link.setToolTip(job["link"])

    def navigate(self, name):
        self.active_filter = name
        for b in self.nav_buttons:
            b.setProperty("selected", b.text().endswith(name))
            b.style().unpolish(b); b.style().polish(b)
        if name in ("Offres", "Accueil", "Historique"):
            self.search_field.setPlaceholderText("⌕  Poste, entreprise ou compétence" if name != "Accueil" else "Vue d’ensemble · filtrez les offres ci-dessous")
            self._populate_table()
        elif name in ("Blocages", "Dossiers prêts", "Candidatures envoyées"):
            self._populate_table()
        else:
            QMessageBox.information(self, name, f"L’écran « {name} » fait partie de la feuille de route du MVP graphique. Les actions sensibles restent sous validation humaine.")

    def _log(self, message):
        self.activity_log.append(f"{datetime.now().strftime('%H:%M')} · {message}")
        self.log_text.setText("  ·  ".join(self.activity_log[-2:]))

    def import_cv(self, path=None):
        if path is None:
            selected, _ = QFileDialog.getOpenFileName(self, "Importer un CV", str(Path.home()), "CV (*.pdf *.docx *.txt *.png *.jpg *.jpeg)")
            if not selected: return
            path = Path(selected)
        else:
            path = Path(path)
        suffix = path.suffix.lower()
        if suffix not in {".pdf", ".docx", ".txt", ".png", ".jpg", ".jpeg"}:
            QMessageBox.warning(self, "Format non pris en charge", "Choisissez un fichier PDF, DOCX, TXT, PNG ou JPG.")
            return
        if suffix in {".png", ".jpg", ".jpeg"}:
            QMessageBox.information(self, "OCR non activé", "L’import d’image est reconnu, mais l’extraction OCR n’est pas encore disponible. Vous pouvez continuer avec un CV PDF, DOCX ou TXT.")
            return
        try:
            if suffix == ".txt":
                extracted = path.read_text(encoding="utf-8", errors="replace")
            elif suffix == ".pdf":
                from pypdf import PdfReader
                extracted = "\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)
            else:
                from docx import Document
                extracted = "\n".join(p.text for p in Document(str(path)).paragraphs)
        except ImportError:
            QMessageBox.warning(self, "Module manquant", "L’extraction de ce format nécessite les dépendances PDF/DOCX de l’application.")
            return
        except Exception as exc:
            QMessageBox.warning(self, "Lecture impossible", f"Le CV n’a pas pu être lu : {exc}")
            return
        dialog = ResumeDialog(path, extracted, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.profile = dialog.profile()
            self.cv_label.setText(f"CV : {path.name}")
            self.city_label.setText(f"Ville : {self.profile['city']}")
            self.radius_label.setText(f"Rayon : {self.profile['radius']} km")
            self.city_filter.setText(self.profile["city"])
            self.radius_filter.setValue(self.profile["radius"])
            self._log(f"CV importé et profil confirmé : {path.name}")
            QMessageBox.information(self, "Profil enregistré", "Le profil est conservé dans cette session. Le fichier source n’a pas été envoyé à un service externe.")

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls(): event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls: self.import_cv(urls[0].toLocalFile())

    def search(self):
        if not self.profile:
            answer = QMessageBox.question(self, "Profil requis", "Importez et confirmez votre CV avant de lancer une recherche. Voulez-vous importer un CV maintenant ?")
            if answer == QMessageBox.StandardButton.Yes: self.import_cv()
            return
        self.search_button.setEnabled(False)
        self.search_button.setText("Recherche…")
        self._log("Préparation de la recherche · sources réelles non connectées dans ce prototype")
        QTimer.singleShot(1200, self._finish_search)

    def _finish_search(self):
        self.search_button.setEnabled(True)
        self.search_button.setText("⌕  Rechercher")
        self._log("Démonstration terminée · aucune requête externe n’a été envoyée")
        QMessageBox.information(self, "Recherche prête à configurer", "Le profil de recherche est confirmé. La connexion aux sources autorisées n’est pas encore implémentée ; les offres affichées restent des exemples fictifs.")

    def copy_link(self):
        QApplication.clipboard().setText(self.selected_job["link"])
        self._log("Lien exact copié dans le presse-papiers")

    def open_job(self):
        QMessageBox.information(self, "Offre de démonstration", f"Lien fictif :\n{self.selected_job['link']}\n\nLes données de démonstration ne renvoient pas vers une offre réelle.")

    def analyze_page(self):
        if self.analysis_worker and self.analysis_worker.isRunning():
            return
        url = self.selected_job["link"]
        self.analyze_btn.setEnabled(False)
        self.analyze_btn.setText("Analyse en cours…")
        self._log(f"Ouverture en lecture seule de la page : {self.selected_job['title']}")
        worker = PageAnalysisWorker(url, self)
        self.analysis_worker = worker
        worker.completed.connect(self._analysis_done)
        worker.failed.connect(self._analysis_failed)
        worker.finished.connect(worker.deleteLater)
        worker.start()

    def _analysis_done(self, report):
        self.analysis_worker = None
        self.analyze_btn.setEnabled(True)
        self.analyze_btn.setText("Analyser la page")
        platform_names = {
            "site_entreprise": "site entreprise",
            "site_carriere": "site carrière",
            "ats": "ATS de recrutement",
            "reseau_ou_agregateur": "réseau ou agrégateur",
            "institutionnel": "site institutionnel",
        }
        blocker_names = {
            "captcha_detecte": "CAPTCHA détecté — action humaine nécessaire",
            "login_requis": "Connexion requise",
            "offre_expiree": "Offre probablement expirée",
            "formulaire_multietapes": "Formulaire à plusieurs étapes",
            "lien_candidature_introuvable": "Lien de candidature introuvable",
        }
        blockers = [blocker_names.get(key, key) for key in (report.blockers or [])]
        self.issue_label.setText("⚑  " + (" · ".join(blockers) if blockers else "Aucun blocage évident détecté."))
        details = [
            f"Plateforme détectée : {platform_names.get(report.platform, report.platform)}",
            f"Page : {report.page_title or report.url}",
            f"Formulaire trouvé : {'oui' if report.form_found else 'non'}",
            f"Lien candidature : {report.application_url or 'non trouvé'}",
            f"Champs obligatoires : {', '.join(report.required_fields or []) or 'aucun détecté'}",
            f"Diagnostic : {'; '.join(blockers) if blockers else 'aucun blocage évident détecté'}",
            "L’analyse n’a ni soumis de formulaire ni tenté de contourner une protection.",
        ]
        self._log(f"Analyse terminée · {platform_names.get(report.platform, report.platform)} · {len(blockers)} point(s) à vérifier")
        QMessageBox.information(self, "Diagnostic de la page", "\n".join(details))

    def _analysis_failed(self, message):
        self.analysis_worker = None
        self.analyze_btn.setEnabled(True)
        self.analyze_btn.setText("Analyser la page")
        self._log(f"Analyse impossible : {message}")
        QMessageBox.warning(self, "Analyse impossible", f"La page n’a pas pu être analysée.\n\n{message}")

    def prepare_packet(self):
        job = self.selected_job
        safe = lambda value: re.sub(r"[^\w-]+", "_", value, flags=re.UNICODE).strip("_")
        folder_name = f"{date.today().isoformat()}_{safe(job['company'])}_{safe(job['title'])}_{safe(job['city'])}"
        target = Path.home() / "Candidatures" / folder_name
        try:
            target.mkdir(parents=True, exist_ok=True)
            if self.profile.get("file"):
                source = Path(self.profile["file"])
                if source.is_file(): shutil.copy2(source, target / f"cv_source{source.suffix.lower()}")
            facts = self.profile
            cover = f"Objet : Candidature — {job['title']}\n\nMadame, Monsieur,\n\nJe souhaite vous proposer ma candidature au poste de {job['title']} à {job['city']}. {('Mon expérience mentionnée dans mon profil (' + facts.get('experience', '') + ')') if facts.get('experience') else 'Mon parcours et les compétences que je peux confirmer dans mon CV'} motivent cette démarche.\n\nLes compétences demandées incluent : {', '.join(job['skills'])}. Cette lettre est un modèle à vérifier et personnaliser à partir de faits exacts avant tout envoi.\n\nCordialement,\n{facts.get('name', '[Votre nom]')}\n{facts.get('email', '')}\n{facts.get('phone', '')}\n"
            (target / "lettre_motivation.txt").write_text(cover, encoding="utf-8")
            (target / "reponses_formulaire.json").write_text(json.dumps({"pourquoi_ce_poste": "À personnaliser à partir d’éléments vérifiés.", "pretentions_salariales": "À compléter", "disponibilite": "À compléter", "competences": job["skills"]}, ensure_ascii=False, indent=2), encoding="utf-8")
            (target / "checklist.txt").write_text(f"Dossier de démonstration — {job['title']}\nLien : {job['link']}\n\n[ ] Vérifier l’offre et sa date\n[ ] Relire et personnaliser les documents\n[ ] Compléter les champs obligatoires\n[ ] Envoyer manuellement après validation\n\nAucune candidature n’a été envoyée.\n", encoding="utf-8")
            (target / "metadata.json").write_text(json.dumps({"offer": job, "created_at": datetime.now().isoformat(), "profile_city": facts.get("city"), "notice": "Offre de démonstration; documents à vérifier."}, ensure_ascii=False, indent=2), encoding="utf-8")
            self.statuses[job["title"]] = "Dossier prêt"
            self._populate_table()
            self._log(f"Dossier local créé : {target}")
            QMessageBox.information(self, "Dossier préparé", f"Dossier créé dans :\n{target}\n\nLe CV original est copié sans modification ; aucun CV adapté PDF ni document final n’est produit dans ce prototype. Vérifiez et personnalisez les fichiers avant envoi.")
        except OSError as exc:
            QMessageBox.warning(self, "Création impossible", f"Le dossier n’a pas pu être créé : {exc}")

    def mark_applied(self):
        title = self.selected_job["title"]
        self.statuses[title] = "Postulée"
        self.status_label.setText("État : Postulée")
        self._populate_table()
        self._log(f"Candidature marquée comme envoyée manuellement : {title}")

    def ignore_job(self):
        title = self.selected_job["title"]
        self.statuses[title] = "Ignoré"
        self.status_label.setText("État : Ignoré")
        self._populate_table()
        self._log(f"Offre ignorée : {title}")


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Job Founder")
    app.setOrganizationName("Job Founder")
    window = JobFounderWindow()
    window.show()
    return app.exec()
