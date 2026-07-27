export type HandbookCategoryId =
  | 'entry'
  | 'assets'
  | 'electrical'
  | 'network'
  | 'consumption'
  | 'home-assistant'
  | 'media'
  | 'operations'

export interface HandbookCategory {
  id: HandbookCategoryId
  title: string
  icon: string
  description: string
}

export interface HandbookEntry {
  id: string
  term: string
  aliases?: string[]
  category: HandbookCategoryId
  summary: string
  details: string
  example?: string
  related?: string[]
}

export interface HandbookSection {
  id: string
  title: string
  category: HandbookCategoryId
  introduction: string
  entries: HandbookEntry[]
}

export const handbookCategories: HandbookCategory[] = [
  {
    id: 'entry',
    title: 'Einstieg',
    icon: 'mdi-home-outline',
    description: 'Grundidee und zentrale Bausteine von DocOfHome.'
  },
  {
    id: 'assets',
    title: 'Assets & Produkte',
    icon: 'mdi-devices',
    description: 'Geräte, Produkte, Standorte und Kennzeichnungen.'
  },
  {
    id: 'electrical',
    title: 'Elektro',
    icon: 'mdi-flash',
    description: 'Verteilungen, Schutzgeräte, Leiter und Verbindungen.'
  },
  {
    id: 'network',
    title: 'Netzwerk',
    icon: 'mdi-lan',
    description: 'IP-Netze, Ports, VLANs und Verkabelung.'
  },
  {
    id: 'consumption',
    title: 'Verbrauch & Zähler',
    icon: 'mdi-chart-line',
    description: 'Zählerstände, Zeiträume und berechnete Verbräuche.'
  },
  {
    id: 'home-assistant',
    title: 'Home Assistant',
    icon: 'mdi-home-assistant',
    description: 'Geräte, Entitäten, Livewerte und Synchronisation.'
  },
  {
    id: 'media',
    title: 'Bilder & Dokumente',
    icon: 'mdi-folder-outline',
    description: 'Anhänge, Produktbilder, Immich und lokales Caching.'
  },
  {
    id: 'operations',
    title: 'Backup & Betrieb',
    icon: 'mdi-docker',
    description: 'Container, Datenverzeichnis, Updates und Wiederherstellung.'
  }
]

export const handbookSections: HandbookSection[] = [
  {
    id: 'einstieg',
    title: 'Einstieg',
    category: 'entry',
    introduction:
      'DocOfHome ist eine lokale Anwendung zur verständlichen Dokumentation eines privaten Hauses oder einer Wohnung. Die Bereiche greifen ineinander, bleiben aber fachlich getrennt.',
    entries: [
      {
        id: 'docofhome',
        term: 'DocOfHome',
        category: 'entry',
        summary: 'Lokaler digitaler Zwilling für die technische Hausdokumentation.',
        details:
          'DocOfHome bündelt Informationen zu Räumen, Geräten, Elektro, Netzwerk, Verbrauch, Smart Home, Bildern, Dokumenten und Wartungsaufgaben. Die Anwendung ist für den privaten Alltag gedacht und ersetzt keine Fachplanung.',
        example: 'Ein Wechselrichter wird als Asset angelegt, einem Standort zugeordnet und mit Dokumenten, Netzwerkdaten und Home-Assistant-Werten ergänzt.',
        related: ['Asset', 'Standort', 'Verbindung', 'Dokument']
      },
      {
        id: 'asset-produkt-standort-verbindung-dokument',
        term: 'Asset, Produkt, Standort, Verbindung und Dokument',
        aliases: ['Grundbausteine'],
        category: 'entry',
        summary: 'Fünf unterschiedliche Bausteine, die gemeinsam ein vollständiges Bild ergeben.',
        details:
          'Ein Asset ist das konkrete vorhandene Gerät. Ein Produkt beschreibt Hersteller und Modell. Der Standort sagt, wo sich das Asset befindet. Eine Verbindung beschreibt eine Beziehung oder Verkabelung. Ein Dokument enthält zum Beispiel Anleitung, Rechnung oder Prüfprotokoll.',
        example: 'Die konkrete Fritzbox ist das Asset; „FRITZ!Box 7590“ ist das Produkt; der Technikraum ist der Standort; das Netzwerkkabel ist die Verbindung; die PDF-Anleitung ist das Dokument.',
        related: ['Asset', 'Produkt', 'Standort', 'Verkabelung', 'Dokumentanhang']
      }
    ]
  },
  {
    id: 'assets-und-produkte',
    title: 'Assets und Produkte',
    category: 'assets',
    introduction:
      'Assets bilden die tatsächlich vorhandenen Gegenstände ab. Produkt- und Typdaten vermeiden doppelte Eingaben und sorgen für einheitliche Bezeichnungen.',
    entries: [
      {
        id: 'asset', term: 'Asset', category: 'assets',
        summary: 'Ein konkreter Gegenstand oder ein konkretes technisches Gerät im eigenen Bestand.',
        details: 'Ein Asset besitzt einen eigenen Namen, Status und Standort und kann Seriennummer, Inventarnummer, Bilder, Dokumente, Verbindungen und Integrationszuordnungen erhalten.',
        example: '„Waschmaschine Keller“ ist ein Asset. Eine zweite baugleiche Maschine wäre ein eigenes Asset.',
        related: ['Asset-Typ', 'Produkt', 'Standort', 'Status']
      },
      {
        id: 'asset-typ', term: 'Asset-Typ', category: 'assets',
        summary: 'Fachliche Gruppe für ähnliche Assets.',
        details: 'Der Asset-Typ beschreibt, um welche Art Gegenstand es sich handelt, etwa Wechselrichter, Sicherung, Switch oder Wasserzähler. Er kann gemeinsame Vorgaben wie eine DIN-Breite liefern.',
        example: 'Mehrere Leitungsschutzschalter können denselben Asset-Typ „Sicherung“ verwenden.',
        related: ['Asset', 'DIN-Breite', 'Produkt']
      },
      {
        id: 'produkt', term: 'Produkt', category: 'assets',
        summary: 'Hersteller- und Modellbeschreibung, die von mehreren Assets verwendet werden kann.',
        details: 'Ein Produkt enthält gemeinsame Daten wie Hersteller, Modell, Artikelnummer und Produktbild. Individuelle Daten wie Seriennummer oder Einbauort gehören dagegen zum Asset.',
        example: 'Das Produkt „Shelly Pro 3EM“ kann für das im Zählerschrank montierte konkrete Asset genutzt werden.',
        related: ['Asset', 'Produktbild', 'Seriennummer']
      },
      {
        id: 'seriennummer', term: 'Seriennummer', category: 'assets',
        summary: 'Vom Hersteller vergebene eindeutige Kennzeichnung eines konkreten Geräts.',
        details: 'Die Seriennummer unterscheidet baugleiche Geräte voneinander. Sie sollte so erfasst werden, wie sie auf Typenschild, Verpackung oder Rechnung steht.',
        related: ['Inventarnummer', 'Asset']
      },
      {
        id: 'inventarnummer', term: 'Inventarnummer', category: 'assets',
        summary: 'Eigene interne Kennzeichnung für ein Asset.',
        details: 'Die Inventarnummer wird selbst vergeben und bleibt unabhängig von Hersteller oder Seriennummer. Sie eignet sich für Etiketten und eine einheitliche Suche.',
        example: 'DOH-EL-0042 kann als eigene Inventarnummer für einen Smart Meter dienen.',
        related: ['Seriennummer', 'Label']
      },
      {
        id: 'standort', term: 'Standort', category: 'assets',
        summary: 'Der dokumentierte Platz eines Assets innerhalb der Gebäudestruktur.',
        details: 'Standorte können Gebäude, Etagen, Räume oder feinere Plätze abbilden. Eine nachvollziehbare Hierarchie ist meist hilfreicher als viele sehr kleine Sonderstandorte.',
        example: 'Haus → Erdgeschoss → Hauswirtschaftsraum → Zählerschrank.',
        related: ['Asset', 'Label']
      },
      {
        id: 'label', term: 'Label', category: 'assets',
        summary: 'Frei verwendbare Kennzeichnung zur zusätzlichen Gruppierung.',
        details: 'Labels ergänzen feste Felder und Standorte. Sie eignen sich zum Beispiel für Eigentümer, Gewerk, Wichtigkeit oder eine geplante Austauschgruppe.',
        example: 'Labels wie „kritisch“, „Außenbereich“ oder „Garantie bis 2029“.',
        related: ['Status', 'Standort']
      },
      {
        id: 'status', term: 'Status', category: 'assets',
        summary: 'Aktueller Lebenszykluszustand eines Assets.',
        details: 'Der Status zeigt, ob ein Asset aktiv, außer Betrieb, ersetzt oder archiviert ist. Historische Geräte sollten nicht gelöscht werden, wenn ihre Dokumentation weiterhin wichtig ist.',
        related: ['Asset', 'Archiv']
      },
      {
        id: 'duplizieren-serienanlage', term: 'Duplizieren / Serienanlage', aliases: ['Serienanlage'], category: 'assets',
        summary: 'Mehrere ähnliche Assets auf Basis einer Vorlage anlegen.',
        details: 'Beim Duplizieren werden gemeinsame Angaben übernommen. Individuelle Merkmale wie Seriennummer, Inventarnummer oder Position müssen anschließend korrekt zugeordnet werden.',
        example: 'Zwölf baugleiche Sicherungsautomaten werden aus einer Vorlage erzeugt und anschließend fortlaufend platziert.',
        related: ['Asset', 'Inventarnummer', 'DIN-Breite']
      },
      {
        id: 'din-breite', term: 'DIN-Breite', aliases: ['TE-Breite'], category: 'assets',
        summary: 'Platzbedarf eines DIN-Geräts in Teilungseinheiten.',
        details: 'Die DIN-Breite kann direkt am Asset oder als Standard am Asset-Typ hinterlegt werden. Sie wird für die Platzierung in einer Verteilung benötigt.',
        example: 'Ein einpoliger Leitungsschutzschalter benötigt meistens 1 TE, ein dreiphasiges Gerät häufig 3 oder 4 TE.',
        related: ['Teilungseinheit (TE)', 'DIN-Schiene / Hutschiene']
      }
    ]
  },
  {
    id: 'elektro',
    title: 'Elektro',
    category: 'electrical',
    introduction:
      'Die Elektroansicht dokumentiert den vorhandenen Aufbau vereinfacht und nachvollziehbar. Sie ist keine Elektroplanung und keine Anleitung für Arbeiten an spannungsführenden Anlagen.',
    entries: [
      { id: 'hauptverteilung', term: 'Hauptverteilung', category: 'electrical', summary: 'Zentrale elektrische Verteilung eines Gebäudes.', details: 'In der Hauptverteilung treffen üblicherweise Einspeisung, Zählerbereich und größere Abgänge zusammen. DocOfHome kann Reihen, Bereiche, Geräte, Schienen und Verbindungen dokumentieren.', example: 'Netzanschluss → Vorsicherung → Stromzähler → Hauptverteilung.', related: ['Unterverteilung', 'Einspeisung', 'Zählerplatz'] },
      { id: 'unterverteilung', term: 'Unterverteilung', category: 'electrical', summary: 'Nachgelagerte Verteilung für einen Gebäudebereich.', details: 'Eine Unterverteilung wird aus einer übergeordneten Verteilung versorgt und verteilt Stromkreise zum Beispiel auf Etage, Garage oder Werkstatt.', example: 'Die Hauptverteilung speist eine Unterverteilung in der Garage.', related: ['Hauptverteilung', 'Abgang', 'Einspeisung'] },
      { id: 'din-schiene', term: 'DIN-Schiene / Hutschiene', aliases: ['DIN-Schiene', 'Hutschiene'], category: 'electrical', summary: 'Normierte Metallschiene zur Montage von Reiheneinbaugeräten.', details: 'Auf der Hutschiene sitzen unter anderem Sicherungen, FI-Schalter, Smart Meter und Klemmen. In DocOfHome wird ihre Belegung über Reihen und Teilungseinheiten dargestellt.', related: ['Teilungseinheit (TE)', 'DIN-Breite'] },
      { id: 'teilungseinheit', term: 'Teilungseinheit (TE)', aliases: ['TE'], category: 'electrical', summary: 'Rastermaß für den Platzbedarf auf einer DIN-Schiene.', details: 'Ein Gerät belegt eine oder mehrere aufeinanderfolgende TE. Die Position hilft, einen Schrank später eindeutig nachzuvollziehen.', example: 'Eine Sicherung auf Reihe 2, TE 7 belegt bei 1 TE Breite genau diesen Platz.', related: ['DIN-Breite', 'DIN-Schiene / Hutschiene'] },
      { id: 'sicherung-lss', term: 'Sicherung / Leitungsschutzschalter', aliases: ['Sicherung', 'Leitungsschutzschalter', 'LS', 'LSS'], category: 'electrical', summary: 'Schutzgerät gegen Überlast und Kurzschluss eines Stromkreises.', details: 'In der privaten Dokumentation sind Bezeichnung, versorgter Bereich, Position, Phase und zugeordneter FI meist die wichtigsten Angaben.', example: '„Küche Steckdosen“ wird über einen Leitungsschutzschalter abgesichert.', related: ['Stromkreis', 'FI / RCD', 'Phase L1, L2, L3'] },
      { id: 'fi-rcd', term: 'FI / RCD', aliases: ['FI', 'RCD', 'Fehlerstromschutzschalter'], category: 'electrical', summary: 'Fehlerstrom-Schutzeinrichtung für eine Gruppe von Stromkreisen.', details: 'Ein FI/RCD überwacht, ob Strom unerwartet abfließt. In DocOfHome kann er einer Sammelschiene und einer N-Schiene zugeordnet werden, damit die zugehörige Gruppe verständlich bleibt.', example: 'FI „EG Allgemein“ → Sammelschiene → Sicherungen für Flur, Wohnzimmer und Küche.', related: ['FI-Gruppe', 'N-Schiene', 'Sammelschiene'] },
      { id: 'smart-meter', term: 'Smart Meter', category: 'electrical', summary: 'Digitales Messgerät mit Kommunikations- oder Integrationsmöglichkeit.', details: 'Ein Smart Meter kann als normales Asset im Schrank platziert und zusätzlich mit Home Assistant verbunden werden. Es ist nicht automatisch der abrechnungsrelevante Stromzähler des Netzbetreibers. Geräte mit externen Stromwandlerklemmen können mehrere Leitungen messen; jeder Messkanal wird in DocOfHome als nicht leitender Messpunkt an einer vorhandenen Verkabelung dokumentiert.', example: 'CT1, CT2 und CT3 messen die drei Phasen des Hausanschlusses und liefern Leistung und Strom an Home Assistant.', related: ['Stromzähler', 'Stromwandlerklemme / CT-Klemme', 'Livewert', 'Asset'] },
      { id: 'ct-klemme', term: 'Stromwandlerklemme / CT-Klemme', aliases: ['CT-Klemme', 'Messklemme', 'Stromwandler', 'Klappwandler'], category: 'electrical', summary: 'Messklemme, die um eine vorhandene Leitung gelegt wird und deren Stromfluss erfasst.', details: 'Eine CT-Klemme ist kein zusätzlicher stromführender Abgang. Sie misst berührungslos beziehungsweise über das magnetische Feld einer Leitung und gehört als Messbeziehung zu genau dieser Verkabelung. Ein Smart Meter kann mehrere Kanäle besitzen, zum Beispiel CT1 für L1, CT2 für L2 und CT3 für L3 oder getrennte Messpunkte für Netz, PV und Batterie. Einbaurichtung und Vorzeichen müssen dokumentiert werden, weil eine gedrehte Klemme Bezug und Einspeisung vertauschen kann. Jedem Kanal können eigene Home-Assistant-Entitäten für Leistung, Strom oder Energie zugeordnet werden.', example: 'Verkabelung Stromzähler → Hauptschalter trägt den Messpunkt CT1 „Hausanschluss L1“; dazu gehört sensor.smart_meter_l1_power.', related: ['Smart Meter', 'Verkabelung / Verbindungstypen', 'Entität', 'Phase L1, L2, L3'] },
      { id: 'stromzaehler', term: 'Stromzähler', category: 'electrical', summary: 'Zähler zur Erfassung elektrischer Energie.', details: 'Je nach Anlage gibt es Netzbezugs-, Einspeise-, Zwischen- oder Unterzähler. Der Zähler kann im Verbrauchsmodul erfasst und im Zählerfeld der Verteilung platziert werden.', related: ['Zähler', 'Zählerstand', 'Zählerplatz'] },
      { id: 'phasen', term: 'Phase L1, L2, L3', aliases: ['L1', 'L2', 'L3', 'Phasen'], category: 'electrical', summary: 'Drei aktive Leiter eines üblichen dreiphasigen Hausanschlusses.', details: 'Die Lasten werden möglichst sinnvoll auf L1, L2 und L3 verteilt. DocOfHome kann die Phase aus der Position unter einer Sammelschiene ableiten.', example: 'Eine dreiphasige Sammelschiene wiederholt das Muster L1 – L2 – L3.', related: ['Sammelschiene', 'Phasenverteilerblock', 'Neutralleiter N'] },
      { id: 'neutralleiter', term: 'Neutralleiter N', aliases: ['N', 'Neutralleiter'], category: 'electrical', summary: 'Leiter für den Rückstrom in vielen Wechselstromkreisen.', details: 'Bei FI-geschützten Gruppen muss der zugehörige Neutralleiter nachvollziehbar derselben FI-Gruppe zugeordnet sein. DocOfHome bildet dies über N-Schienen und Zuordnungen ab.', related: ['N-Schiene', 'FI / RCD', 'PEN'] },
      { id: 'schutzleiter', term: 'Schutzleiter PE', aliases: ['PE', 'Schutzleiter'], category: 'electrical', summary: 'Schutzleiter zur Verbindung berührbarer leitfähiger Teile mit dem Schutzsystem.', details: 'Der Schutzleiter wird in der Verteilung typischerweise auf einer PE-Schiene gesammelt. Er darf nicht mit einer normalen N-Zuordnung verwechselt werden.', related: ['PE-Schiene', 'PEN'] },
      { id: 'pen', term: 'PEN', category: 'electrical', summary: 'Kombinierter Schutz- und Neutralleiter in bestimmten Netzabschnitten.', details: 'PEN vereint PE- und N-Funktion bis zu seiner Aufteilung. Für die private Bestandsdokumentation genügt meist, Einspeisung und Aufteilung nachvollziehbar zu kennzeichnen.', related: ['Neutralleiter N', 'Schutzleiter PE', 'Potentialverteiler'] },
      { id: 'phasenverteilerblock', term: 'Phasenverteilerblock', category: 'electrical', summary: 'Passiver Verteilerpunkt für L1, L2 und L3.', details: 'Ein Phasenverteilerblock verteilt eine oder mehrere Einspeisungen auf mehrere Abgänge. In DocOfHome ist er eine passive Schrankkomponente und kein Asset.', example: 'Netzversorgung und PV-Abgang können dokumentiert an einem passenden Verteilerpunkt zusammenlaufen, sofern dies dem realen Bestand entspricht.', related: ['Potentialverteiler', 'mehrere Einspeisungen', 'Abgang'] },
      { id: 'potentialverteiler', term: 'Potentialverteiler', category: 'electrical', summary: 'Verteilerblock für ein gemeinsames elektrisches Potential.', details: 'Er wird eingesetzt, um einen Leiter auf mehrere Anschlüsse zu verteilen. Für die Hausdokumentation reichen Bezeichnung, Leiter, Position und Verbindungen.', related: ['Phasenverteilerblock', 'Sammelschiene'] },
      {
        id: 'sammelschiene', term: 'Sammelschiene', category: 'electrical',
        summary: 'Übergeordneter Begriff für einen gemeinsamen leitfähigen Verteiler mit einer Einspeisung und mehreren Abgängen.',
        details: 'Eine Sammelschiene verteilt ein gemeinsames elektrisches Potential auf mehrere Abgänge oder Gerätegruppen. Sie muss keine Kammform besitzen und nicht direkt in Sicherungsautomaten eingesteckt sein. Im Haus kann damit zum Beispiel die Versorgung nach Zähler oder Hauptschalter auf mehrere FI-Gruppen, eine Wallbox und eine Unterverteilung verteilt werden. Auch N- und PE-Schienen erfüllen funktional eine Sammelaufgabe, werden in DocOfHome wegen ihrer eindeutigen Leiterfunktion separat dokumentiert. Hersteller verwenden die Wörter Sammelschiene, Stromschiene, Phasenschiene und Kammschiene teilweise überlappend; DocOfHome trennt sie bewusst nach ihrer Aufgabe.',
        example: 'Stromzähler → Hauptschalter → Sammelschiene oder Verteilerblock → FI-Gruppe EG, FI-Gruppe OG und Unterverteilung Garage.',
        related: ['Phasenschiene / Kammschiene', 'Phasenverteilerblock', 'N-Schiene', 'PE-Schiene']
      },
      {
        id: 'phasenschiene', term: 'Phasenschiene / Kammschiene', aliases: ['Phasenschiene', 'Kammschiene'], category: 'electrical',
        summary: 'Spezielle vorkonfektionierte Sammelschiene mit regelmäßig angeordneten Stift- oder Gabelkontakten für benachbarte DIN-Geräte.',
        details: 'Die Kontakte sehen wie die Zähne eines Kamms aus und werden direkt in die Anschlussklemmen nebeneinanderliegender FI-, LS- oder FI/LS-Geräte eingesetzt. Dadurch ersetzt die Kammschiene viele einzelne Drahtbrücken innerhalb einer DIN-Reihe. Ein- und mehrphasige Ausführungen können ein festes Muster wie L1–L2–L3 wiederholen. Nicht jede Sammelschiene ist eine Kammschiene; eine Kammschiene verbindet direkt nebeneinanderliegende Reiheneinbaugeräte und übernimmt dort die Funktion einer kleinen Sammelschiene. In DocOfHome wird „Kammschiene / Phasenschiene“ für diese direkte Geräteverbindung verwendet und „Sammelschiene“ für den allgemeineren übergeordneten Verteilpunkt.',
        example: 'FI „EG Allgemein“ → dreiphasige Kammschiene → LS Licht, LS Steckdosen, LS Küche; die Positionen folgen dem dokumentierten L1–L2–L3-Muster.',
        related: ['Sammelschiene', 'FI / RCD', 'Sicherung / Leitungsschutzschalter', 'automatische Phasenzuordnung über eine Sammelschiene']
      },
      { id: 'n-schiene', term: 'N-Schiene', aliases: ['Neutralleiterschiene'], category: 'electrical', summary: 'Sammelpunkt für Neutralleiter einer eindeutig zugeordneten Gruppe.', details: 'Bei mehreren FI-Gruppen sollte jede N-Schiene verständlich dem passenden FI zugeordnet werden. DocOfHome warnt bei widersprüchlichen Zuordnungen.', example: 'FI „Bad/Waschen“ → N-Schiene „N Bad/Waschen“ → zugehörige Stromkreise.', related: ['Neutralleiter N', 'FI-Gruppe', 'Neutralleiterzuordnung'] },
      { id: 'pe-schiene', term: 'PE-Schiene', aliases: ['Schutzleiterschiene'], category: 'electrical', summary: 'Sammelpunkt für Schutzleiter.', details: 'Die PE-Schiene wird als passive Schrankkomponente dokumentiert. Sie gehört nicht zu einer einzelnen FI-Gruppe wie eine N-Schiene.', related: ['Schutzleiter PE', 'N-Schiene'] },
      { id: 'vorsicherung', term: 'Vorsicherung', category: 'electrical', summary: 'Vorgeschaltete Sicherung für nachgelagerte Leitungen oder Anlagenteile.', details: 'Die Vorsicherung begrenzt und schützt einen nachfolgenden Bereich. In einer vereinfachten Topologie wird sie zwischen Einspeisung und nachgelagertem Gerät dokumentiert.', example: 'Netzversorger → Vorsicherung → Zähler → Verteilerblock.', related: ['Einspeisung', 'Stromzähler', 'Hauptverteilung'] },
      { id: 'zaehlerplatz', term: 'Zählerplatz', category: 'electrical', summary: 'Vorgesehener Bereich einer Verteilung für Stromzähler.', details: 'Im strukturierten Schranklayout kann ein eigener Zählerbereich angelegt werden. Dort lassen sich Verbrauchszähler oder passende Zähler-Assets positionieren.', related: ['Stromzähler', 'Hauptverteilung'] },
      { id: 'stromkreis', term: 'Stromkreis', category: 'electrical', summary: 'Zusammengehöriger elektrischer Abgang zu Verbrauchern oder Steckdosen.', details: 'Ein Stromkreis sollte so benannt werden, dass sein versorgter Bereich verständlich ist. Optional können zugehörige Assets und Räume verknüpft werden.', example: '„Küche Arbeitssteckdosen“ oder „Außenlicht Terrasse“.', related: ['Sicherung / Leitungsschutzschalter', 'Abgang'] },
      { id: 'einspeisung', term: 'Einspeisung', category: 'electrical', summary: 'Quelle, aus der ein Gerät, Verteiler oder eine Schrankkomponente versorgt wird.', details: 'Eine Einspeisung kann vom Netz, einer übergeordneten Verteilung, einem Wechselrichter oder einer anderen realen Quelle stammen. Die Topologie dokumentiert die Richtung.', related: ['Abgang', 'mehrere Einspeisungen', 'Verkabelung / Verbindungstypen'] },
      { id: 'abgang', term: 'Abgang', category: 'electrical', summary: 'Weiterführende Verbindung von einer Verteilung oder Komponente zu einem Ziel.', details: 'Abgänge führen zum Beispiel zu Unterverteilungen, Sicherungen oder Verbrauchern. Eine klare Bezeichnung erleichtert spätere Fehlersuche und Umbauten.', related: ['Einspeisung', 'Stromkreis', 'Unterverteilung'] },
      { id: 'mehrere-einspeisungen', term: 'mehrere Einspeisungen', category: 'electrical', summary: 'Mehr als eine dokumentierte Quelle an einem geeigneten gemeinsamen Ziel.', details: 'DocOfHome kann mehrere Quellen an passiven Verteilpunkten abbilden. Dokumentiert werden darf nur der reale Bestand; die Funktion bewertet nicht, ob die elektrische Ausführung zulässig ist.', example: 'Zwei dokumentierte Quellen führen zu einem Phasenverteilerblock, von dem mehrere Abgänge weiterlaufen.', related: ['Einspeisung', 'Phasenverteilerblock', 'Potentialverteiler'] },
      { id: 'automatische-phasenzuordnung', term: 'automatische Phasenzuordnung über eine Sammelschiene', aliases: ['automatische Phasenzuordnung'], category: 'electrical', summary: 'Ableitung der Phase aus TE-Position und Phasenmuster.', details: 'Liegt ein Schutzgerät unter einer Sammelschiene, berechnet DocOfHome die Phase anhand von Startphase und wiederholtem L1/L2/L3-Muster. Manuelle Abweichungen bleiben dokumentierbar und erzeugen verständliche Hinweise.', related: ['Sammelschiene', 'Phase L1, L2, L3'] },
      { id: 'fi-gruppe', term: 'FI-Gruppe', category: 'electrical', summary: 'Zusammengehörige Geräte, Sammelschiene und Neutralleiter unter einem FI/RCD.', details: 'Die FI-Gruppe entsteht durch die Zuordnung einer Sammelschiene und N-Schiene zu einem FI. Schutzgeräte innerhalb des Bereichs übernehmen diese Gruppe automatisch.', example: 'FI → Sammelschiene → Sicherungen sowie FI → N-Schiene → Neutralleiter der gleichen Stromkreise.', related: ['FI / RCD', 'N-Schiene', 'Sammelschiene'] },
      { id: 'neutralleiterzuordnung', term: 'Neutralleiterzuordnung', category: 'electrical', summary: 'Verknüpfung eines Schutzgeräts oder einer Gruppe mit der passenden N-Schiene.', details: 'Die Zuordnung verhindert in der Dokumentation, dass Neutralleiter verschiedener FI-Gruppen versehentlich vermischt dargestellt werden. Abweichungen werden als Warnung gezeigt.', related: ['N-Schiene', 'FI-Gruppe', 'Neutralleiter N'] },
      { id: 'elektro-verbindungstypen', term: 'Verkabelung / Verbindungstypen', aliases: ['Elektro-Verkabelung'], category: 'electrical', summary: 'Dokumentierte gerichtete Beziehung zwischen elektrischen Endpunkten.', details: 'Verbindungen können Assets, Schutzgeräte, Verteilungen und passive Schrankkomponenten verbinden. Bezeichnung, Leiter und reale Richtung sollten nachvollziehbar bleiben.', example: 'Netzversorger → Vorsicherung → Zähler → Verteilerblock.', related: ['Einspeisung', 'Abgang', 'Verbindung'] }
    ]
  },
  {
    id: 'netzwerk',
    title: 'Netzwerk',
    category: 'network',
    introduction:
      'Das Netzwerkmodul beschreibt logische Netze, Geräteanschlüsse und die physische Verkabelung. Ziel ist eine verständliche Bestandsübersicht, nicht die Nachbildung jedes Herstellerdetails.',
    entries: [
      { id: 'netzwerk-begriff', term: 'Netzwerk', category: 'network', summary: 'Zusammengehöriger Kommunikationsbereich für Geräte und Dienste.', details: 'Ein Netzwerk kann einen privaten IP-Adressbereich, ein VLAN und gemeinsame Einstellungen wie Gateway, DNS oder DHCP besitzen.', related: ['IP-Adresse', 'Subnetz', 'VLAN'] },
      { id: 'ip-adresse', term: 'IP-Adresse', category: 'network', summary: 'Logische Adresse eines Geräts oder einer Schnittstelle im Netzwerk.', details: 'Die IP-Adresse muss innerhalb des jeweiligen Netzes eindeutig sein. Sie kann automatisch per DHCP oder manuell statisch vergeben werden.', example: '192.168.10.25 innerhalb des Netzes 192.168.10.0/24.', related: ['IPv4 / IPv6', 'DHCP', 'statische IP'] },
      { id: 'ipv4-ipv6', term: 'IPv4 / IPv6', aliases: ['IPv4', 'IPv6'], category: 'network', summary: 'Zwei Generationen des Internet-Protokolls mit unterschiedlichen Adressformaten.', details: 'IPv4 verwendet kurze Adressen wie 192.168.1.20. IPv6 verwendet längere hexadezimale Adressen. Beide können parallel dokumentiert werden.', related: ['IP-Adresse', 'Subnetz'] },
      { id: 'subnetz', term: 'Subnetz', category: 'network', summary: 'Logischer IP-Adressbereich, in dem Geräte direkt miteinander kommunizieren.', details: 'Das Subnetz wird meist mit Präfixlänge angegeben. Ein /24-Netz enthält bei IPv4 typischerweise 256 Adressen einschließlich Netz- und Broadcastadresse.', example: '192.168.10.0/24.', related: ['Netzmaske', 'Gateway', 'VLAN'] },
      { id: 'netzmaske', term: 'Netzmaske', category: 'network', summary: 'Kennzeichnet, welcher Teil einer IPv4-Adresse das Netz beschreibt.', details: 'Die Netzmaske 255.255.255.0 entspricht der Präfixlänge /24. Für die Dokumentation sollte eine einheitliche Schreibweise verwendet werden.', related: ['Subnetz', 'IP-Adresse'] },
      { id: 'gateway', term: 'Gateway', category: 'network', summary: 'Router-Adresse für Ziele außerhalb des eigenen Subnetzes.', details: 'Geräte senden Daten an das Gateway, wenn das Ziel nicht im lokalen Netz liegt. In Heimnetzen übernimmt diese Rolle oft Router oder Firewall.', example: 'Im Netz 192.168.10.0/24 ist 192.168.10.1 häufig das Gateway.', related: ['Router', 'Subnetz', 'DNS'] },
      { id: 'dns', term: 'DNS', aliases: ['Domain Name System'], category: 'network', summary: 'Übersetzt Namen in IP-Adressen.', details: 'DNS ermöglicht Zugriffe über Namen wie nas.home statt nur über IP-Adressen. Dokumentiert werden können interne oder externe DNS-Server.', related: ['IP-Adresse', 'Gateway'] },
      { id: 'dhcp', term: 'DHCP', aliases: ['Dynamic Host Configuration Protocol'], category: 'network', summary: 'Automatische Vergabe von IP-Einstellungen an Geräte.', details: 'Ein DHCP-Server verteilt IP-Adresse, Netzmaske, Gateway und häufig DNS. Reservierungen können dafür sorgen, dass ein bekanntes Gerät immer dieselbe Adresse erhält.', example: 'Der Router vergibt einem Fernseher automatisch 192.168.10.60.', related: ['statische IP', 'MAC-Adresse', 'IP-Adresse'] },
      { id: 'statische-ip', term: 'statische IP', aliases: ['feste IP'], category: 'network', summary: 'Dauerhaft festgelegte IP-Adresse.', details: 'Eine statische IP kann direkt am Gerät oder als DHCP-Reservierung gepflegt werden. Sie sollte nicht versehentlich im dynamischen Vergabebereich doppelt verwendet werden.', related: ['DHCP', 'IP-Adresse'] },
      { id: 'mac-adresse', term: 'MAC-Adresse', category: 'network', summary: 'Hardwarekennung einer Netzwerkschnittstelle.', details: 'Die MAC-Adresse hilft, eine konkrete Schnittstelle im lokalen Netz zu erkennen und DHCP-Reservierungen zuzuordnen. Virtuelle oder zufällige MAC-Adressen sind möglich.', related: ['Netzwerkschnittstelle', 'DHCP'] },
      { id: 'netzwerkschnittstelle', term: 'Netzwerkschnittstelle', category: 'network', summary: 'Anschluss oder logischer Adapter eines Netzwerkgeräts.', details: 'Ein Asset kann mehrere Schnittstellen besitzen, etwa LAN, WLAN, Management oder virtuelle Interfaces. Jede Schnittstelle kann eigene Adressen und Verbindungen haben.', related: ['physischer Port', 'logische Schnittstelle', 'MAC-Adresse'] },
      { id: 'physischer-port', term: 'physischer Port', category: 'network', summary: 'Tatsächlich vorhandener Anschluss am Gerät.', details: 'Physische Ports sind zum Beispiel RJ45-Buchsen, SFP-Steckplätze oder Glasfaseranschlüsse. Sie können mit Kabeln und Gegenstellen verbunden werden.', related: ['Switch-Port', 'logische Schnittstelle', 'Verkabelung'] },
      { id: 'logische-schnittstelle', term: 'logische Schnittstelle', category: 'network', summary: 'Softwareseitige Schnittstelle ohne zwingend eigenen physischen Anschluss.', details: 'Beispiele sind VLAN-Interfaces, Bridges, Bonding oder virtuelle Adapter. Sie können auf einem oder mehreren physischen Ports aufbauen.', related: ['physischer Port', 'VLAN', 'Netzwerkschnittstelle'] },
      { id: 'switch', term: 'Switch', category: 'network', summary: 'Gerät zur Verbindung mehrerer Teilnehmer innerhalb eines lokalen Netzes.', details: 'Ein Switch leitet Daten zwischen seinen Ports weiter. Managed Switches unterstützen zusätzliche Funktionen wie VLAN, PoE und Trunks.', related: ['Switch-Port', 'VLAN', 'Uplink'] },
      { id: 'switch-port', term: 'Switch-Port', category: 'network', summary: 'Ein einzelner Anschluss eines Switches.', details: 'Am Switch-Port werden Gegenstelle, Status, Geschwindigkeit, VLAN-Modus, PoE und Verkabelung dokumentiert. Ein ungenutzter Port bleibt neutral und wird nicht künstlich als Fehler markiert.', example: 'Port 8 → Patchpanel 12 → Netzwerkdose Büro → Arbeitsplatz-PC.', related: ['physischer Port', 'freie Ports', 'Patchpanel'] },
      { id: 'vlan', term: 'VLAN', aliases: ['Virtual LAN'], category: 'network', summary: 'Logische Trennung mehrerer Netze auf gemeinsamer Switch-Infrastruktur.', details: 'VLANs teilen ein physisches Netzwerk in getrennte Bereiche. Ein Port kann genau ein ungetaggtes VLAN oder mehrere getaggte VLANs transportieren, abhängig von seiner Aufgabe.', example: 'VLAN 10 für private Geräte, VLAN 20 für IoT und VLAN 30 für Gäste.', related: ['Tagged / Untagged', 'Access-Port', 'Trunk-Port'] },
      { id: 'tagged-untagged', term: 'Tagged / Untagged', aliases: ['Tagged', 'Untagged'], category: 'network', summary: 'Kennzeichnet, ob VLAN-Informationen in Ethernet-Frames mitgeführt werden.', details: 'Untagged bedeutet, dass das Endgerät normale Frames ohne VLAN-Markierung sendet. Tagged bedeutet, dass mehrere VLANs anhand ihrer Kennzeichnung über denselben Link transportiert werden können.', related: ['VLAN', 'Access-Port', 'Trunk-Port'] },
      { id: 'access-port', term: 'Access-Port', category: 'network', summary: 'Switch-Port für ein Endgerät in normalerweise genau einem ungetaggten VLAN.', details: 'Das Endgerät muss VLANs nicht kennen. Der Switch ordnet den Datenverkehr intern dem konfigurierten VLAN zu.', example: 'Ein Fernseher steckt an einem Access-Port im IoT-VLAN.', related: ['VLAN', 'Untagged', 'Trunk-Port'] },
      { id: 'trunk-port', term: 'Trunk-Port', category: 'network', summary: 'Verbindung, die mehrere VLANs transportiert.', details: 'Ein Trunk wird häufig zwischen Switches, Router, Firewall, Access Point oder Virtualisierungshost verwendet. Die erlaubten VLANs sollten auf beiden Seiten übereinstimmen.', example: 'Switch-Uplink zum Access Point mit privaten, IoT- und Gäste-VLANs.', related: ['Tagged / Untagged', 'Uplink', 'VLAN'] },
      { id: 'patchpanel', term: 'Patchpanel', category: 'network', summary: 'Passive Anschlussleiste für fest verlegte Gebäudekabel.', details: 'Ein Patchpanel verbindet die feste Hausverkabelung mit kurzen Patchkabeln zum Switch. Portnummer, Zielraum und Netzwerkdose sollten gemeinsam dokumentiert werden.', related: ['Netzwerkdose', 'Verkabelung', 'Switch-Port'] },
      { id: 'netzwerkdose', term: 'Netzwerkdose', category: 'network', summary: 'Fest installierter Netzwerkanschluss im Raum.', details: 'Eine Dose wird über die Gebäudeverkabelung mit einem Patchpanel verbunden. Eine klare Bezeichnung erleichtert die Zuordnung zum richtigen Switch-Port.', related: ['Patchpanel', 'Verkabelung'] },
      { id: 'netzwerk-verkabelung', term: 'Verkabelung', category: 'network', summary: 'Physische Verbindung zwischen zwei Netzwerkanschlüssen.', details: 'Die Dokumentation sollte beide Endpunkte und bei Bedarf Kabeltyp, Kennzeichnung und Verlauf enthalten. Passive Zwischenpunkte wie Patchpanel und Dose bleiben sichtbar.', related: ['Patchpanel', 'Netzwerkdose', 'Switch-Port'] },
      { id: 'uplink', term: 'Uplink', category: 'network', summary: 'Übergeordnete Verbindung eines Netzwerkgeräts zu einem weiteren Netzgerät.', details: 'Ein Uplink verbindet beispielsweise einen Etagen-Switch mit dem Haupt-Switch oder einen Switch mit der Firewall. Er ist häufig als Trunk konfiguriert.', related: ['Switch', 'Trunk-Port'] },
      { id: 'wlan', term: 'WLAN', aliases: ['Wi-Fi'], category: 'network', summary: 'Drahtloses lokales Netzwerk.', details: 'WLAN wird über Access Points bereitgestellt. Für die Dokumentation sind SSID, zugeordnetes Netz oder VLAN, Standort und gegebenenfalls Uplink relevant.', related: ['SSID', 'VLAN', 'PoE'] },
      { id: 'ssid', term: 'SSID', category: 'network', summary: 'Sichtbarer oder verborgener Name eines WLANs.', details: 'Mehrere Access Points können dieselbe SSID ausstrahlen. Eine SSID kann einem bestimmten VLAN oder Netz zugeordnet sein.', example: '„Home“, „Home-IoT“ und „Home-Gast“.', related: ['WLAN', 'VLAN'] },
      { id: 'poe', term: 'PoE', aliases: ['Power over Ethernet'], category: 'network', summary: 'Stromversorgung eines Geräts über das Netzwerkkabel.', details: 'PoE versorgt etwa Access Points, Kameras oder Telefone. Switch-Port und Leistungsbedarf sollten dokumentiert werden, wenn sie für Betrieb oder Fehlersuche wichtig sind.', related: ['Switch-Port', 'WLAN'] },
      { id: 'freie-ports', term: 'freie Ports', aliases: ['freier Port'], category: 'network', summary: 'Nicht belegte Anschlüsse ohne Fehlerstatus.', details: 'Ein freier Port ist ein normaler neutraler Zustand. Er kann als Reserve sichtbar bleiben, ohne eine Warnung oder künstliche Verbindung zu erhalten.', related: ['Switch-Port', 'Patchpanel'] },
      { id: 'router', term: 'Router', category: 'network', summary: 'Verbindet unterschiedliche IP-Netze miteinander.', details: 'Im Heimnetz übernimmt oft die Firewall oder Internetbox die Router- und Gateway-Funktion. Ein Router kann zusätzlich DHCP, DNS und VPN bereitstellen.', related: ['Gateway', 'Subnetz', 'VLAN'] }
    ]
  },
  {
    id: 'verbrauch-und-zaehler',
    title: 'Verbrauch und Zähler',
    category: 'consumption',
    introduction:
      'Das Verbrauchsmodul verwaltet Ablesungen und berechnet daraus nachvollziehbare Zeiträume. Messwerte sollten immer mit Datum und Einheit erfasst werden.',
    entries: [
      { id: 'zaehler', term: 'Zähler', category: 'consumption', summary: 'Messstelle für einen fortlaufenden oder periodischen Verbrauchswert.', details: 'Ein Zähler besitzt Typ, Einheit, Standort und Ablesungen. Er kann mit einem Asset verbunden sein, muss es aber nicht.', related: ['Zählerstand', 'Verbrauch', 'virtuelle / berechnete Zähler'] },
      { id: 'zaehlerstand', term: 'Zählerstand', category: 'consumption', summary: 'Zu einem Zeitpunkt abgelesener kumulierter Messwert.', details: 'Für eine korrekte Berechnung werden Wert, Einheit und Messzeitpunkt gespeichert. Der neue Stand sollte normalerweise nicht kleiner als der vorherige sein, außer bei Wechsel oder Korrektur.', example: '12.345,678 kWh am 26.07.2026.', related: ['Verbrauch', 'Korrektur und Plausibilitätsprüfung'] },
      { id: 'verbrauch', term: 'Verbrauch', category: 'consumption', summary: 'Differenz zwischen zwei passenden Zählerständen.', details: 'Verbrauch ist nicht dasselbe wie der absolute Zählerstand. DocOfHome berechnet die Differenz für den gewählten Zeitraum und kennzeichnet unvollständige Zeiträume.', related: ['Zählerstand', 'vollständiger und unvollständiger Zeitraum'] },
      { id: 'aktueller-monat', term: 'aktueller Monat / bis heute', aliases: ['bis heute'], category: 'consumption', summary: 'Auswertung des laufenden Monats nur bis zum aktuellen Tag.', details: 'Ein laufender Monat ist noch nicht abgeschlossen. Der Zeitraum endet deshalb heute und nicht künstlich am letzten Tag des Monats.', related: ['vollständiger und unvollständiger Zeitraum', 'Verbrauch'] },
      { id: 'vollstaendiger-zeitraum', term: 'vollständiger und unvollständiger Zeitraum', aliases: ['unvollständiger Zeitraum', 'vollständiger Zeitraum'], category: 'consumption', summary: 'Kennzeichnung, ob Ablesungen den gesamten gewünschten Zeitraum abdecken.', details: 'Ein vollständiger Zeitraum besitzt passende Start- und Endwerte. Fehlt eine Grenze oder läuft der Zeitraum noch, wird das Ergebnis als unvollständig gekennzeichnet statt zu genau vorgetäuscht.', related: ['aktueller Monat / bis heute', 'Plausibilitätsprüfung'] },
      { id: 'zaehlertypen', term: 'Wasser-, Strom-, Gas- und Wärmezähler', aliases: ['Wasserzähler', 'Gaszähler', 'Wärmezähler'], category: 'consumption', summary: 'Typische Verbrauchszähler eines Privathaushalts.', details: 'Die Zählertypen unterscheiden sich vor allem durch Einheit und Messgegenstand. Die Erfassungslogik mit Zeitstempel und fortlaufendem Stand bleibt ähnlich.', example: 'Wasser in m³, Strom in kWh, Gas häufig in m³ oder kWh, Wärme in kWh oder MWh.', related: ['Zähler', 'Zählerstand'] },
      { id: 'virtuelle-zaehler', term: 'virtuelle / berechnete Zähler', aliases: ['virtueller Zähler', 'berechneter Zähler'], category: 'consumption', summary: 'Aus mehreren realen Zählern oder Differenzen abgeleiteter Wert.', details: 'Virtuelle Zähler besitzen keine eigene physische Ablesestelle. Ihre Werte werden nachvollziehbar aus vorhandenen Monatsverbräuchen berechnet.', example: 'EG-Verbrauch = Dusche + Küche + Zählerraum; restliches Haus = Hauptzähler minus EG.', related: ['Zähler', 'Verbrauch'] },
      { id: 'zaehlerstandserfassung', term: 'Zählerstandserfassung', category: 'consumption', summary: 'Dialog zum Eintragen einer neuen Ablesung.', details: 'Die Erfassung sollte direkt am Zähler erfolgen. Datum, Wert und Einheit werden geprüft; Hinweise schützen vor Zahlendrehern oder falschem Zähler.', related: ['Dashboard-Schnellerfassung', 'Korrektur und Plausibilitätsprüfung'] },
      { id: 'korrektur-plausibilitaet', term: 'Korrektur und Plausibilitätsprüfung', aliases: ['Plausibilitätsprüfung'], category: 'consumption', summary: 'Prüfung und nachvollziehbare Berichtigung auffälliger Ablesungen.', details: 'DocOfHome prüft unter anderem Reihenfolge, Wertebereich und ungewöhnliche Sprünge. Eine Korrektur sollte bewusst erfolgen, statt einen auffälligen Wert kommentarlos zu überschreiben.', related: ['Zählerstand', 'vollständiger und unvollständiger Zeitraum'] },
      { id: 'dashboard-schnellerfassung', term: 'Dashboard-Schnellerfassung', category: 'consumption', summary: 'Direkter Einstieg vom Dashboard zur mobilen Ablesung.', details: 'Der Button „Zählerstände erfassen“ öffnet die Verbrauchsseite direkt im Erfassungsmodus. Dadurch sind regelmäßige Ablesungen mit wenigen Schritten möglich.', related: ['Zählerstandserfassung', 'Zählerstand'] }
    ]
  },
  {
    id: 'home-assistant',
    title: 'Home Assistant',
    category: 'home-assistant',
    introduction:
      'Die Integration ergänzt die statische Hausdokumentation um ausgewählte Livewerte. DocOfHome bleibt dabei das Dokumentationssystem und Home Assistant die Quelle der aktuellen Zustände.',
    entries: [
      { id: 'integration', term: 'Integration', category: 'home-assistant', summary: 'Konfigurierte Verbindung zwischen DocOfHome und einem externen System.', details: 'Eine Integration enthält technische Verbindungsdaten und stellt Geräte oder Werte bereit. Zugangsdaten gehören nicht in Wiki, Feedback oder Release-ZIP.', related: ['Synchronisation', 'Cache'] },
      { id: 'ha-geraet', term: 'Gerät', category: 'home-assistant', summary: 'In Home Assistant zusammengefasste technische Einheit.', details: 'Ein Gerät kann mehrere Entitäten besitzen, zum Beispiel Leistung, Energie, Temperatur und Schalter. Es kann einem DocOfHome-Asset zugeordnet werden.', related: ['Entität', 'Asset'] },
      { id: 'entitaet', term: 'Entität', category: 'home-assistant', summary: 'Ein einzelner Zustand oder steuerbarer Kanal in Home Assistant.', details: 'Entitäten haben eine ID wie sensor.stromzaehler_leistung. DocOfHome verwendet ausgewählte Entitäten für Livewerte und Rollen.', related: ['Sensor', 'Schalter', 'Rolle'] },
      { id: 'sensor', term: 'Sensor', category: 'home-assistant', summary: 'Lesende Entität für einen Mess- oder Zustandswert.', details: 'Sensoren liefern etwa Leistung, Energie, Temperatur oder Batteriestand. Einheit und Verfügbarkeit bestimmen die verständliche Anzeige.', related: ['Entität', 'Livewert'] },
      { id: 'schalter', term: 'Schalter', category: 'home-assistant', summary: 'Steuerbare Entität mit mindestens Ein- und Aus-Zustand.', details: 'DocOfHome dokumentiert Schalter und ihre Zuordnung, ist aber nicht als vollständige Bedienoberfläche für jede Automation gedacht.', related: ['Entität', 'Gerät'] },
      { id: 'rolle', term: 'Rolle', category: 'home-assistant', summary: 'Bedeutung einer ausgewählten Entität innerhalb von DocOfHome.', details: 'Eine Rolle legt fest, ob ein Wert zum Beispiel als primäre Liveanzeige, Energie, Leistung oder Zustand verwendet wird. Dadurch bleibt die Anzeige unabhängig vom technischen Entitätsnamen verständlich.', related: ['Entität', 'Livewert'] },
      { id: 'livewert', term: 'Livewert', category: 'home-assistant', summary: 'Zuletzt synchronisierter aktueller Zustand einer Entität.', details: 'Livewerte werden mit Verfügbarkeit, Einheit und Zeitstempel angezeigt. Ein Livewert ersetzt keine historische Zählerablesung.', example: 'Aktuelle Leistung 428 W im Schrank; Zählerstand weiterhin separat im Verbrauchsmodul.', related: ['Sensor', 'Zählerstand', 'Cache'] },
      { id: 'asset-zuordnung-ha', term: 'Zuordnung zu einem Asset', category: 'home-assistant', summary: 'Verknüpfung eines Home-Assistant-Geräts oder einer Entität mit dem realen DocOfHome-Asset.', details: 'Die Zuordnung verhindert doppelte Gerätewelten. Das Asset enthält Dokumentation und Standort; Home Assistant liefert ausgewählte Livewerte.', related: ['Asset', 'Gerät', 'Entität'] },
      { id: 'synchronisation', term: 'Synchronisation', category: 'home-assistant', summary: 'Aktualisierung von Geräten, Entitäten und Zuständen aus Home Assistant.', details: 'Die Synchronisation liest den aktuellen Stand ein und aktualisiert den lokalen Cache. Sie sollte bei vorübergehender Nichterreichbarkeit verständlich fehlschlagen, ohne bestehende Zuordnungen zu löschen.', related: ['Cache', 'Single-Flight-Sync'] },
      { id: 'cache', term: 'Cache', category: 'home-assistant', summary: 'Zwischengespeicherter letzter bekannter Integrationsstand.', details: 'Der Cache beschleunigt die Anzeige und hält bekannte Zuordnungen sichtbar, wenn Home Assistant kurzzeitig nicht erreichbar ist. Zeitstempel zeigen, wie aktuell die Daten sind.', related: ['Synchronisation', 'Livewert'] },
      { id: 'single-flight-sync', term: 'Single-Flight-Sync', category: 'home-assistant', summary: 'Verhindert mehrere gleichzeitig laufende identische Synchronisationen.', details: 'Wenn mehrere Ansichten gleichzeitig aktuelle Daten benötigen, wird nur eine gemeinsame Synchronisation ausgeführt. Das reduziert Last und widersprüchliche Ergebnisse.', related: ['Synchronisation', 'Cache'] }
    ]
  },
  {
    id: 'bilder-und-dokumente',
    title: 'Bilder und Dokumente',
    category: 'media',
    introduction:
      'Bilder und Dokumente ergänzen strukturierte Daten um Typenschilder, Einbauzustände, Rechnungen, Anleitungen und weitere Nachweise.',
    entries: [
      { id: 'upload', term: 'Upload', category: 'media', summary: 'Übertragung einer Datei in den von DocOfHome verwalteten oder angebundenen Speicher.', details: 'Vor dem Upload sollten Dateiname, Inhalt und mögliche Zugangsdaten geprüft werden. Dateien werden gezielt einem Asset, Produkt oder Dokumentbereich zugeordnet.', related: ['Dokumentanhang', 'Produktbild'] },
      { id: 'url', term: 'URL', category: 'media', summary: 'Adresse einer externen oder internen Ressource.', details: 'Eine URL kann auf ein Bild oder Dokument verweisen. Für dauerhaft wichtige Hausdokumentation ist eine lokale oder kontrollierte Kopie verlässlicher als ein flüchtiger externer Link.', related: ['lokales Caching', 'Online-Bildsuche'] },
      { id: 'immich', term: 'Immich', category: 'media', summary: 'Optional angebundene Fotoverwaltung für vorhandene Bilder.', details: 'Über Immich können passende Bilder ausgewählt und einem Asset oder einer Ablesung zugeordnet werden. DocOfHome speichert die Verknüpfung, nicht die komplette Immich-Bibliothek.', related: ['Assetbild', 'Upload'] },
      { id: 'online-bildsuche', term: 'Online-Bildsuche', category: 'media', summary: 'Optionale Suche nach einem passenden Produktbild im Internet.', details: 'Die Suche ist nicht zwingend erforderlich und kann deaktiviert werden. Ausgewählte Bilder sollten lokal gespeichert werden, damit die Darstellung offline erhalten bleibt.', related: ['lokales Caching', 'Produktbild'] },
      { id: 'lokales-caching', term: 'lokales Caching', aliases: ['lokaler Cache'], category: 'media', summary: 'Lokale Kopie eines extern gefundenen Bildes.', details: 'Durch lokales Caching bleibt ein Produktbild verfügbar, auch wenn die ursprüngliche Webseite oder Internetverbindung später nicht erreichbar ist.', related: ['Online-Bildsuche', 'URL'] },
      { id: 'dokumentanhang', term: 'Dokumentanhang', category: 'media', summary: 'Datei oder Verknüpfung, die einem dokumentierten Objekt zugeordnet ist.', details: 'Typische Anhänge sind Bedienungsanleitungen, Rechnungen, Schaltbilder, Prüfprotokolle oder Garantienachweise.', related: ['Upload', 'Asset'] },
      { id: 'produktbild', term: 'Produktbild', category: 'media', summary: 'Allgemeines Bild eines Herstellers oder Modells.', details: 'Das Produktbild wird von mehreren Assets desselben Produkts geteilt und zeigt typischerweise nicht den tatsächlichen Einbauzustand.', related: ['Produkt', 'Assetbild'] },
      { id: 'assetbild', term: 'Assetbild', category: 'media', summary: 'Foto des konkret vorhandenen Assets.', details: 'Ein Assetbild kann Typenschild, Einbauort, Anschlüsse oder aktuellen Zustand zeigen. Es ist individueller als ein allgemeines Produktbild.', related: ['Asset', 'Produktbild', 'Immich'] }
    ]
  },
  {
    id: 'backup-und-betrieb',
    title: 'Backup und Betrieb',
    category: 'operations',
    introduction:
      'DocOfHome wird typischerweise als Docker-Anwendung betrieben. Entscheidend sind ein persistentes Datenverzeichnis, überprüfte Backups und nachvollziehbare Updates.',
    entries: [
      { id: 'docker', term: 'Docker', category: 'operations', summary: 'Plattform zum Ausführen der Anwendung in Containern.', details: 'Docker stellt eine reproduzierbare Laufzeit bereit. Die dauerhaft wichtigen Daten müssen außerhalb des austauschbaren Containers in Volumes oder Bind-Mounts liegen.', related: ['Container', 'Compose', 'Volume'] },
      { id: 'container', term: 'Container', category: 'operations', summary: 'Laufende Instanz eines Docker-Images.', details: 'Ein Container enthält Anwendung und Laufzeit, sollte aber nicht als alleiniger dauerhafter Datenspeicher betrachtet werden. Er kann bei einem Update ersetzt werden.', related: ['Docker', 'Volume', 'Healthcheck'] },
      { id: 'compose', term: 'Compose', aliases: ['Docker Compose'], category: 'operations', summary: 'Deklarative Beschreibung mehrerer Container und ihrer Einstellungen.', details: 'Eine Compose-Datei definiert Images, Ports, Umgebungsvariablen, Volumes, Netzwerke und Healthchecks. Änderungen sollten versioniert und vor dem Update gesichert werden.', related: ['Docker', 'Container', 'Volume'] },
      { id: 'volume', term: 'Volume', category: 'operations', summary: 'Persistenter Speicher außerhalb des kurzlebigen Containers.', details: 'Volumes oder Bind-Mounts bewahren Datenbanken, Uploads und Konfigurationen beim Austausch des Containers. Ihr tatsächlicher Speicherort gehört in die Betriebsdokumentation.', related: ['Datenverzeichnis', 'Backup', 'Container'] },
      { id: 'datenverzeichnis', term: 'Datenverzeichnis', category: 'operations', summary: 'Persistenter Ordner mit Datenbank, Uploads und anwendungsbezogenen Dateien.', details: 'Das Datenverzeichnis ist der wichtigste Bestandteil eines Backups. Vor Updates sollte geprüft werden, dass es vollständig gesichert und nicht versehentlich in ein Release-ZIP aufgenommen wird.', related: ['Volume', 'Backup', 'Restore'] },
      { id: 'backup', term: 'Backup', category: 'operations', summary: 'Konsistente Sicherung der dauerhaft benötigten Daten.', details: 'Ein Backup sollte Datenverzeichnis, Datenbank und notwendige Betriebsdateien umfassen. Eine erfolgreiche Dateikopie allein beweist noch nicht, dass eine Wiederherstellung funktioniert.', related: ['Restore', 'Datenverzeichnis'] },
      { id: 'restore', term: 'Restore', category: 'operations', summary: 'Wiederherstellung einer Installation aus einem Backup.', details: 'Ein Restore sollte regelmäßig testweise geprüft werden. Version, Dateirechte, Datenbankmigrationen und Zielpfade müssen zum Sicherungsstand passen.', related: ['Backup', 'Migration', 'Version'] },
      { id: 'migration', term: 'Migration', category: 'operations', summary: 'Versionierter Umbau des Datenbankschemas bei einem Update.', details: 'Alembic-Migrationen ändern Tabellen und Felder kontrolliert. Sie dürfen nicht übersprungen oder manuell nachgebaut werden; vor ihrer Ausführung ist ein Backup erforderlich.', related: ['Version', 'Release', 'Backup'] },
      { id: 'version', term: 'Version', category: 'operations', summary: 'Eindeutige Kennzeichnung eines Anwendungsstands.', details: 'Die Version wird zentral gepflegt und muss in Frontend, Backend, Dokumentation und Release-Artefakten übereinstimmen. Sie hilft bei Support und Migration.', related: ['Release', 'Migration'] },
      { id: 'release', term: 'Release', category: 'operations', summary: 'Geprüfter, dokumentierter und verpackter Softwarestand.', details: 'Ein Release enthält Quellstand, Versionsinformationen, Release Notes, Prüfsumme, Manifest und einen ehrlichen Validierungsbericht. Nicht ausgeführte Tests dürfen nicht als bestanden gelten.', related: ['Version', 'Logs', 'Healthcheck'] },
      { id: 'logs', term: 'Logs', category: 'operations', summary: 'Zeitlich geordnete Laufzeitmeldungen von Anwendung und Containern.', details: 'Logs helfen bei Fehleranalyse und Healthchecks. Vor einer Weitergabe müssen Zugangsdaten, Tokens und private Inhalte ausgeschlossen werden.', related: ['Healthcheck', 'Container'] },
      { id: 'healthcheck', term: 'Healthcheck', category: 'operations', summary: 'Automatische Prüfung, ob der Dienst grundsätzlich betriebsbereit ist.', details: 'Ein Healthcheck bestätigt Erreichbarkeit und Basisfunktion, ersetzt aber keine fachliche Prüfung von Navigation, Suche, Datenzugriff und Backup.', related: ['Container', 'Logs', 'Release'] }
    ]
  }
]

export const handbookEntries: HandbookEntry[] = handbookSections.flatMap((section) => section.entries)

function normalize(value: string): string {
  return value
    .toLocaleLowerCase('de')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
}

export function categoryTitle(categoryId: HandbookCategoryId): string {
  return handbookCategories.find((category) => category.id === categoryId)?.title ?? categoryId
}

export function entrySearchText(entry: HandbookEntry): string {
  return normalize([
    entry.term,
    ...(entry.aliases ?? []),
    entry.summary,
    entry.details,
    entry.example ?? '',
    categoryTitle(entry.category),
    ...(entry.related ?? [])
  ].join(' '))
}

export function filterHandbookEntries(
  entries: HandbookEntry[],
  query: string,
  category: HandbookCategoryId | 'all'
): HandbookEntry[] {
  const normalizedQuery = normalize(query.trim())
  return entries.filter((entry) => {
    if (category !== 'all' && entry.category !== category) return false
    return !normalizedQuery || entrySearchText(entry).includes(normalizedQuery)
  })
}

export function sortGlossaryEntries(entries: HandbookEntry[]): HandbookEntry[] {
  return [...entries].sort((left, right) => left.term.localeCompare(right.term, 'de', {
    sensitivity: 'base',
    numeric: true
  }))
}

export function glossaryLetter(entry: HandbookEntry): string {
  const letter = entry.term.trim().charAt(0).toLocaleUpperCase('de')
  return /[A-ZÄÖÜ]/.test(letter) ? letter : '#'
}

export function glossaryLetters(entries: HandbookEntry[]): string[] {
  return [...new Set(sortGlossaryEntries(entries).map(glossaryLetter))]
}
